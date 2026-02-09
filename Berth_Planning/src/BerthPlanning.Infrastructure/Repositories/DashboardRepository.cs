using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class DashboardRepository : IDashboardRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public DashboardRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<DashboardMetricsDto> GetDashboardMetricsAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        // Call sp_GetDashboardStats or use view
        const string sql = @"
            SELECT
                (SELECT COUNT(*) FROM VESSELS) AS TotalVessels,
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE WHERE Status IN ('Scheduled', 'Approaching')) AS VesselsInQueue,
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE WHERE Status = 'Berthed') AS VesselsBerthed,
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE WHERE Status = 'Approaching') AS VesselsApproaching,
                (SELECT COUNT(*) FROM BERTHS WHERE IsActive = 1) AS TotalBerths,
                (SELECT COUNT(*) FROM BERTHS b WHERE b.IsActive = 1 AND NOT EXISTS (
                    SELECT 1 FROM VESSEL_SCHEDULE vs
                    WHERE vs.BerthId = b.BerthId AND vs.Status = 'Berthed'
                )) AS AvailableBerths,
                (SELECT COUNT(*) FROM BERTHS b WHERE b.IsActive = 1 AND EXISTS (
                    SELECT 1 FROM VESSEL_SCHEDULE vs
                    WHERE vs.BerthId = b.BerthId AND vs.Status = 'Berthed'
                )) AS OccupiedBerths,
                (SELECT COUNT(*) FROM CONFLICTS WHERE Status = 'Detected') AS ActiveConflicts,
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE WHERE CAST(ETA AS DATE) = CAST(GETUTCDATE() AS DATE)) AS TodayArrivals,
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE WHERE CAST(ETD AS DATE) = CAST(GETUTCDATE() AS DATE)) AS TodayDepartures,
                ISNULL((SELECT AVG(CAST(WaitingTime AS DECIMAL)) FROM VESSEL_SCHEDULE WHERE WaitingTime IS NOT NULL), 0) AS AverageWaitingTime";

        DashboardMetricsDto? metrics = await connection.QueryFirstOrDefaultAsync<DashboardMetricsDto>(sql);

        if (metrics != null && metrics.TotalBerths > 0)
        {
            metrics.BerthUtilization = Math.Round((decimal)metrics.OccupiedBerths / metrics.TotalBerths * 100, 1);
        }

        return metrics ?? new DashboardMetricsDto();
    }

    public async Task<IEnumerable<BerthStatusDto>> GetCurrentBerthStatusAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        // Use view vw_CurrentBerthStatus if available, otherwise inline query
        const string sql = @"
            SELECT
                b.BerthId,
                b.BerthName,
                b.BerthCode,
                CASE
                    WHEN EXISTS (SELECT 1 FROM BERTH_MAINTENANCE bm
                                 WHERE bm.BerthId = b.BerthId
                                 AND bm.Status IN ('Scheduled', 'InProgress')
                                 AND GETUTCDATE() BETWEEN bm.StartTime AND bm.EndTime) THEN 'Maintenance'
                    WHEN vs.Status = 'Berthed' THEN 'Occupied'
                    WHEN vs.Status IN ('Scheduled', 'Approaching') THEN 'Reserved'
                    ELSE 'Available'
                END AS Status,
                v.VesselName AS CurrentVessel,
                vs.ETA AS VesselETA,
                vs.ETD AS VesselETD,
                b.NumberOfCranes,
                b.BerthType
            FROM BERTHS b
            LEFT JOIN VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId
                AND vs.Status IN ('Berthed', 'Scheduled', 'Approaching')
            LEFT JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE b.IsActive = 1
            ORDER BY b.BerthCode";

        return await connection.QueryAsync<BerthStatusDto>(sql);
    }

    public async Task<IEnumerable<VesselQueueDto>> GetVesselQueueAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        // Use view vw_VesselQueueDashboard
        const string sql = @"
            SELECT
                v.VesselId,
                vs.ScheduleId,
                v.VesselName,
                v.VesselType,
                vs.ETA,
                vs.PredictedETA,
                vs.Status,
                v.Priority,
                b.BerthName AS AssignedBerth,
                v.LOA,
                v.Draft
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.Status IN ('Scheduled', 'Approaching')
            ORDER BY v.Priority ASC, vs.ETA ASC";

        return await connection.QueryAsync<VesselQueueDto>(sql);
    }

    public async Task<IEnumerable<TimelineEventDto>> GetBerthTimelineAsync(DateTime startDate, DateTime endDate)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT
                vs.ScheduleId,
                vs.BerthId,
                b.BerthName,
                vs.VesselId,
                v.VesselName,
                ISNULL(vs.ATA, vs.ETA) AS StartTime,
                ISNULL(vs.ATD, vs.ETD) AS EndTime,
                vs.Status,
                v.VesselType
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            INNER JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.Status NOT IN ('Cancelled')
              AND ((vs.ETA BETWEEN @StartDate AND @EndDate)
                   OR (vs.ETD BETWEEN @StartDate AND @EndDate)
                   OR (vs.ETA <= @StartDate AND vs.ETD >= @EndDate))
            ORDER BY b.BerthCode, vs.ETA";

        return await connection.QueryAsync<TimelineEventDto>(sql, new { StartDate = startDate, EndDate = endDate });
    }

    public async Task<IEnumerable<AlertNotification>> GetActiveAlertsAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT TOP 20 AlertId, AlertType, RelatedEntityId, EntityType, Severity,
                   Message, IsRead, CreatedAt, ReadAt
            FROM ALERTS_NOTIFICATIONS
            WHERE IsRead = 0
            ORDER BY
                CASE Severity
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    ELSE 4
                END,
                CreatedAt DESC";

        return await connection.QueryAsync<AlertNotification>(sql);
    }

    public async Task<WeatherData?> GetCurrentWeatherAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT TOP 1 WeatherId, RecordedAt, WindSpeed, WindDirection, Visibility,
                   WaveHeight, Temperature, Precipitation, WeatherCondition, IsAlert, FetchedAt
            FROM WEATHER_DATA
            ORDER BY RecordedAt DESC";

        return await connection.QueryFirstOrDefaultAsync<WeatherData>(sql);
    }

    public async Task<IEnumerable<Conflict>> GetActiveConflictsAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT c.ConflictId, c.ConflictType, c.ScheduleId1, c.ScheduleId2, c.Description,
                   c.Severity, c.Status, c.DetectedAt, c.ResolvedAt, c.Resolution,
                   v1.VesselName AS Vessel1Name,
                   v2.VesselName AS Vessel2Name,
                   b.BerthName
            FROM CONFLICTS c
            INNER JOIN VESSEL_SCHEDULE vs1 ON c.ScheduleId1 = vs1.ScheduleId
            INNER JOIN VESSELS v1 ON vs1.VesselId = v1.VesselId
            LEFT JOIN VESSEL_SCHEDULE vs2 ON c.ScheduleId2 = vs2.ScheduleId
            LEFT JOIN VESSELS v2 ON vs2.VesselId = v2.VesselId
            LEFT JOIN BERTHS b ON vs1.BerthId = b.BerthId
            WHERE c.Status = 'Detected'
            ORDER BY c.Severity ASC, c.DetectedAt DESC";

        return await connection.QueryAsync<Conflict>(sql);
    }
}
