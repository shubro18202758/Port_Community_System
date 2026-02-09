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
        // Use CTE to assign each vessel exactly one status (Berthed > Approaching > Scheduled > Departed)
        const string sql = @"
            ;WITH VesselStatus AS (
                SELECT v.VesselId,
                    COALESCE(
                        (SELECT TOP 1 vs.Status FROM VESSEL_SCHEDULE vs WHERE vs.VesselId = v.VesselId AND vs.Status = 'Berthed'),
                        (SELECT TOP 1 vs.Status FROM VESSEL_SCHEDULE vs WHERE vs.VesselId = v.VesselId AND vs.Status = 'Approaching'),
                        (SELECT TOP 1 vs.Status FROM VESSEL_SCHEDULE vs WHERE vs.VesselId = v.VesselId AND vs.Status = 'Scheduled'),
                        (SELECT TOP 1 vs.Status FROM VESSEL_SCHEDULE vs WHERE vs.VesselId = v.VesselId AND vs.Status = 'Departed'),
                        'Idle'
                    ) AS CurrentStatus
                FROM VESSELS v
            )
            SELECT
                (SELECT COUNT(*) FROM VESSELS) AS TotalVessels,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus = 'Scheduled') AS VesselsScheduled,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus = 'Approaching') AS VesselsApproaching,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus = 'Berthed') AS VesselsBerthed,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus = 'Departed') AS VesselsDeparted,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus IN ('Scheduled', 'Approaching')) AS VesselsInQueue,
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

    public async Task<DashboardMetricsDto> GetDashboardMetricsByTerminalAsync(int terminalId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            ;WITH TerminalBerths AS (
                SELECT BerthId FROM BERTHS WHERE TerminalId = @TerminalId AND IsActive = 1
            ),
            VesselStatus AS (
                SELECT v.VesselId,
                    COALESCE(
                        (SELECT TOP 1 vs.Status FROM VESSEL_SCHEDULE vs INNER JOIN TerminalBerths tb ON vs.BerthId = tb.BerthId WHERE vs.VesselId = v.VesselId AND vs.Status = 'Berthed'),
                        (SELECT TOP 1 vs.Status FROM VESSEL_SCHEDULE vs INNER JOIN TerminalBerths tb ON vs.BerthId = tb.BerthId WHERE vs.VesselId = v.VesselId AND vs.Status = 'Approaching'),
                        (SELECT TOP 1 vs.Status FROM VESSEL_SCHEDULE vs INNER JOIN TerminalBerths tb ON vs.BerthId = tb.BerthId WHERE vs.VesselId = v.VesselId AND vs.Status = 'Scheduled'),
                        (SELECT TOP 1 vs.Status FROM VESSEL_SCHEDULE vs INNER JOIN TerminalBerths tb ON vs.BerthId = tb.BerthId WHERE vs.VesselId = v.VesselId AND vs.Status = 'Departed'),
                        'Idle'
                    ) AS CurrentStatus
                FROM VESSELS v
                WHERE EXISTS (SELECT 1 FROM VESSEL_SCHEDULE vs2 INNER JOIN TerminalBerths tb2 ON vs2.BerthId = tb2.BerthId WHERE vs2.VesselId = v.VesselId)
            )
            SELECT
                (SELECT COUNT(*) FROM VesselStatus) AS TotalVessels,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus = 'Scheduled') AS VesselsScheduled,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus = 'Approaching') AS VesselsApproaching,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus = 'Berthed') AS VesselsBerthed,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus = 'Departed') AS VesselsDeparted,
                (SELECT COUNT(*) FROM VesselStatus WHERE CurrentStatus IN ('Scheduled', 'Approaching')) AS VesselsInQueue,
                (SELECT COUNT(*) FROM TerminalBerths) AS TotalBerths,
                (SELECT COUNT(*) FROM TerminalBerths tb WHERE NOT EXISTS (
                    SELECT 1 FROM VESSEL_SCHEDULE vs WHERE vs.BerthId = tb.BerthId AND vs.Status = 'Berthed'
                )) AS AvailableBerths,
                (SELECT COUNT(*) FROM TerminalBerths tb WHERE EXISTS (
                    SELECT 1 FROM VESSEL_SCHEDULE vs WHERE vs.BerthId = tb.BerthId AND vs.Status = 'Berthed'
                )) AS OccupiedBerths,
                (SELECT COUNT(*) FROM CONFLICTS c
                    INNER JOIN VESSEL_SCHEDULE vs1 ON c.ScheduleId1 = vs1.ScheduleId
                    INNER JOIN TerminalBerths tb ON vs1.BerthId = tb.BerthId
                    WHERE c.Status = 'Detected') AS ActiveConflicts,
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE vs INNER JOIN TerminalBerths tb ON vs.BerthId = tb.BerthId WHERE CAST(vs.ETA AS DATE) = CAST(GETUTCDATE() AS DATE)) AS TodayArrivals,
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE vs INNER JOIN TerminalBerths tb ON vs.BerthId = tb.BerthId WHERE CAST(vs.ETD AS DATE) = CAST(GETUTCDATE() AS DATE)) AS TodayDepartures,
                ISNULL((SELECT AVG(CAST(vs.WaitingTime AS DECIMAL)) FROM VESSEL_SCHEDULE vs INNER JOIN TerminalBerths tb ON vs.BerthId = tb.BerthId WHERE vs.WaitingTime IS NOT NULL), 0) AS AverageWaitingTime";

        DashboardMetricsDto? metrics = await connection.QueryFirstOrDefaultAsync<DashboardMetricsDto>(sql, new { TerminalId = terminalId });

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
        // Use ROW_NUMBER to pick only one schedule per berth (Berthed > Approaching > Scheduled)
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
                    WHEN ranked.Status = 'Berthed' THEN 'Occupied'
                    WHEN ranked.Status IN ('Scheduled', 'Approaching') THEN 'Reserved'
                    ELSE 'Available'
                END AS Status,
                v.VesselName AS CurrentVessel,
                ranked.ETA AS VesselETA,
                ranked.ETD AS VesselETD,
                b.NumberOfCranes,
                b.BerthType
            FROM BERTHS b
            LEFT JOIN (
                SELECT vs.BerthId, vs.VesselId, vs.Status, vs.ETA, vs.ETD,
                    ROW_NUMBER() OVER (PARTITION BY vs.BerthId ORDER BY
                        CASE vs.Status
                            WHEN 'Berthed' THEN 1
                            WHEN 'Approaching' THEN 2
                            WHEN 'Scheduled' THEN 3
                        END
                    ) AS rn
                FROM VESSEL_SCHEDULE vs
                WHERE vs.Status IN ('Berthed', 'Scheduled', 'Approaching')
            ) ranked ON b.BerthId = ranked.BerthId AND ranked.rn = 1
            LEFT JOIN VESSELS v ON ranked.VesselId = v.VesselId
            WHERE b.IsActive = 1
            ORDER BY b.BerthCode";

        return await connection.QueryAsync<BerthStatusDto>(sql);
    }

    public async Task<IEnumerable<BerthStatusDto>> GetCurrentBerthStatusByTerminalAsync(int terminalId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

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
                    WHEN ranked.Status = 'Berthed' THEN 'Occupied'
                    WHEN ranked.Status IN ('Scheduled', 'Approaching') THEN 'Reserved'
                    ELSE 'Available'
                END AS Status,
                v.VesselName AS CurrentVessel,
                ranked.ETA AS VesselETA,
                ranked.ETD AS VesselETD,
                b.NumberOfCranes,
                b.BerthType
            FROM BERTHS b
            LEFT JOIN (
                SELECT vs.BerthId, vs.VesselId, vs.Status, vs.ETA, vs.ETD,
                    ROW_NUMBER() OVER (PARTITION BY vs.BerthId ORDER BY
                        CASE vs.Status
                            WHEN 'Berthed' THEN 1
                            WHEN 'Approaching' THEN 2
                            WHEN 'Scheduled' THEN 3
                        END
                    ) AS rn
                FROM VESSEL_SCHEDULE vs
                WHERE vs.Status IN ('Berthed', 'Scheduled', 'Approaching')
            ) ranked ON b.BerthId = ranked.BerthId AND ranked.rn = 1
            LEFT JOIN VESSELS v ON ranked.VesselId = v.VesselId
            WHERE b.IsActive = 1 AND b.TerminalId = @TerminalId
            ORDER BY b.BerthCode";

        return await connection.QueryAsync<BerthStatusDto>(sql, new { TerminalId = terminalId });
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
