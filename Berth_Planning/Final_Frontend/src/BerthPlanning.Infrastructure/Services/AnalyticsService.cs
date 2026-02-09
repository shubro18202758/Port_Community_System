using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using Dapper;

namespace BerthPlanning.Infrastructure.Services;

public class AnalyticsService : IAnalyticsService
{
    private readonly IDbConnectionFactory _connectionFactory;

    public AnalyticsService(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<HistoricalAnalyticsDto> GetHistoricalAnalyticsAsync(AnalyticsPeriodRequestDto request)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        HistoricalAnalyticsDto result = new()
        {
            PeriodStart = request.StartDate,
            PeriodEnd = request.EndDate
        };

        // Get summary metrics
        DynamicParameters summaryParams = new();
        summaryParams.Add("StartDate", request.StartDate);
        summaryParams.Add("EndDate", request.EndDate);

        var summarySql = @"
            SELECT
                COUNT(*) AS TotalVesselCalls,
                SUM(CASE WHEN Status = 'Departed' THEN 1 ELSE 0 END) AS CompletedCalls,
                SUM(CASE WHEN Status = 'Cancelled' THEN 1 ELSE 0 END) AS CancelledCalls,
                AVG(CAST(WaitingTime AS DECIMAL)) AS AverageWaitingTime,
                AVG(CAST(DwellTime AS DECIMAL)) AS AverageDwellTime,
                AVG(CASE WHEN ATA IS NOT NULL AND ATD IS NOT NULL
                    THEN DATEDIFF(MINUTE, ATA, ATD) / 60.0 ELSE NULL END) AS AverageTurnaroundTime
            FROM VESSEL_SCHEDULE
            WHERE ETA BETWEEN @StartDate AND @EndDate";

        if (request.BerthId.HasValue)
        {
            summarySql += " AND BerthId = @BerthId";
            summaryParams.Add("BerthId", request.BerthId);
        }

        dynamic? summary = await connection.QueryFirstOrDefaultAsync<dynamic>(summarySql, summaryParams);

        if (summary != null)
        {
            result.TotalVesselCalls = summary.TotalVesselCalls ?? 0;
            result.CompletedCalls = summary.CompletedCalls ?? 0;
            result.CancelledCalls = summary.CancelledCalls ?? 0;
            result.AverageWaitingTime = summary.AverageWaitingTime ?? 0;
            result.AverageDwellTime = summary.AverageDwellTime ?? 0;
            result.AverageTurnaroundTime = summary.AverageTurnaroundTime ?? 0;
        }

        // Get ETA accuracy
        var accuracySql = @"
            SELECT
                COUNT(CASE WHEN ABS(DATEDIFF(MINUTE, ETA, ATA)) <= 60 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) AS ETAAccuracyRate,
                AVG(ABS(DATEDIFF(MINUTE, ETA, ATA))) AS AverageETADeviation
            FROM VESSEL_SCHEDULE
            WHERE ETA BETWEEN @StartDate AND @EndDate
              AND ATA IS NOT NULL";

        dynamic? accuracy = await connection.QueryFirstOrDefaultAsync<dynamic>(accuracySql, summaryParams);

        if (accuracy != null)
        {
            result.ETAAccuracyRate = accuracy.ETAAccuracyRate ?? 0;
            result.AverageETADeviation = accuracy.AverageETADeviation ?? 0;
        }

        // Get berth utilization
        result.AverageBerthUtilization = await CalculateAverageUtilizationAsync(
            connection, request.StartDate, request.EndDate, request.BerthId);

        // Get conflict stats
        var conflictSql = @"
            SELECT
                COUNT(*) AS TotalConflicts,
                SUM(CASE WHEN Status = 'Resolved' THEN 1 ELSE 0 END) AS ResolvedConflicts
            FROM CONFLICTS
            WHERE DetectedAt BETWEEN @StartDate AND @EndDate";

        dynamic? conflicts = await connection.QueryFirstOrDefaultAsync<dynamic>(conflictSql, summaryParams);

        if (conflicts != null)
        {
            result.TotalConflicts = conflicts.TotalConflicts ?? 0;
            result.ResolvedConflicts = conflicts.ResolvedConflicts ?? 0;
        }

        // Get detailed breakdowns
        result.BerthUtilization = (await GetBerthUtilizationAsync(request.StartDate, request.EndDate)).ToList();
        result.VesselTypeStats = (await GetVesselTypeStatsAsync(request.StartDate, request.EndDate)).ToList();
        result.DailyTrends = (await GetDailyTrendsAsync(request.StartDate, request.EndDate)).ToList();

        return result;
    }

    public async Task<IEnumerable<BerthUtilizationDto>> GetBerthUtilizationAsync(DateTime startDate, DateTime endDate)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        var totalHours = (endDate - startDate).TotalHours;

        const string sql = @"
            SELECT
                b.BerthId,
                b.BerthName,
                COUNT(vs.ScheduleId) AS VesselCount,
                SUM(CASE
                    WHEN vs.ATA IS NOT NULL AND vs.ATD IS NOT NULL
                    THEN DATEDIFF(MINUTE, vs.ATA, vs.ATD) / 60.0
                    WHEN vs.ETA IS NOT NULL AND vs.ETD IS NOT NULL
                    THEN DATEDIFF(MINUTE, vs.ETA, vs.ETD) / 60.0
                    ELSE vs.DwellTime
                END) AS TotalOccupiedHours,
                AVG(CAST(vs.WaitingTime AS DECIMAL)) AS AverageWaitingTime
            FROM BERTHS b
            LEFT JOIN VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId
                AND vs.ETA BETWEEN @StartDate AND @EndDate
                AND vs.Status NOT IN ('Cancelled')
            WHERE b.IsActive = 1
            GROUP BY b.BerthId, b.BerthName
            ORDER BY b.BerthName";

        IEnumerable<dynamic> results = await connection.QueryAsync<dynamic>(sql, new { StartDate = startDate, EndDate = endDate });

        return results.Select(r => new BerthUtilizationDto
        {
            BerthId = r.BerthId,
            BerthName = r.BerthName,
            VesselCount = r.VesselCount ?? 0,
            TotalOccupiedHours = r.TotalOccupiedHours ?? 0,
            UtilizationPercent = totalHours > 0 ? Math.Round((r.TotalOccupiedHours ?? 0) / (decimal)totalHours * 100, 1) : 0,
            AverageWaitingTime = r.AverageWaitingTime ?? 0
        });
    }

    public async Task<IEnumerable<VesselTypeStatsDto>> GetVesselTypeStatsAsync(DateTime startDate, DateTime endDate)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT
                v.VesselType,
                COUNT(*) AS Count,
                AVG(CAST(vs.WaitingTime AS DECIMAL)) AS AverageWaitingTime,
                AVG(CAST(vs.DwellTime AS DECIMAL)) AS AverageDwellTime,
                AVG(CASE
                    WHEN vs.ATA IS NOT NULL AND vs.ATD IS NOT NULL
                    THEN DATEDIFF(MINUTE, vs.ATA, vs.ATD) / 60.0
                    ELSE NULL
                END) AS AverageTurnaroundTime
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE vs.ETA BETWEEN @StartDate AND @EndDate
              AND vs.Status NOT IN ('Cancelled')
            GROUP BY v.VesselType
            ORDER BY COUNT(*) DESC";

        IEnumerable<dynamic> results = await connection.QueryAsync<dynamic>(sql, new { StartDate = startDate, EndDate = endDate });

        return results.Select(r => new VesselTypeStatsDto
        {
            VesselType = r.VesselType ?? "Unknown",
            Count = r.Count,
            AverageWaitingTime = r.AverageWaitingTime ?? 0,
            AverageDwellTime = r.AverageDwellTime ?? 0,
            AverageTurnaroundTime = r.AverageTurnaroundTime ?? 0
        });
    }

    public async Task<IEnumerable<DailyTrendDto>> GetDailyTrendsAsync(DateTime startDate, DateTime endDate)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            WITH DateRange AS (
                SELECT CAST(@StartDate AS DATE) AS Date
                UNION ALL
                SELECT DATEADD(DAY, 1, Date)
                FROM DateRange
                WHERE Date < @EndDate
            )
            SELECT
                dr.Date,
                ISNULL(arrivals.VesselArrivals, 0) AS VesselArrivals,
                ISNULL(departures.VesselDepartures, 0) AS VesselDepartures,
                ISNULL(conflicts.ConflictCount, 0) AS ConflictCount,
                ISNULL(waittime.AverageWaitingTime, 0) AS AverageWaitingTime
            FROM DateRange dr
            LEFT JOIN (
                SELECT CAST(ISNULL(ATA, ETA) AS DATE) AS ArrivalDate, COUNT(*) AS VesselArrivals
                FROM VESSEL_SCHEDULE
                WHERE Status NOT IN ('Cancelled')
                GROUP BY CAST(ISNULL(ATA, ETA) AS DATE)
            ) arrivals ON dr.Date = arrivals.ArrivalDate
            LEFT JOIN (
                SELECT CAST(ISNULL(ATD, ETD) AS DATE) AS DepartureDate, COUNT(*) AS VesselDepartures
                FROM VESSEL_SCHEDULE
                WHERE Status = 'Departed'
                GROUP BY CAST(ISNULL(ATD, ETD) AS DATE)
            ) departures ON dr.Date = departures.DepartureDate
            LEFT JOIN (
                SELECT CAST(DetectedAt AS DATE) AS ConflictDate, COUNT(*) AS ConflictCount
                FROM CONFLICTS
                GROUP BY CAST(DetectedAt AS DATE)
            ) conflicts ON dr.Date = conflicts.ConflictDate
            LEFT JOIN (
                SELECT CAST(ETA AS DATE) AS WaitDate, AVG(CAST(WaitingTime AS DECIMAL)) AS AverageWaitingTime
                FROM VESSEL_SCHEDULE
                WHERE WaitingTime IS NOT NULL
                GROUP BY CAST(ETA AS DATE)
            ) waittime ON dr.Date = waittime.WaitDate
            ORDER BY dr.Date
            OPTION (MAXRECURSION 366)";

        IEnumerable<dynamic> results = await connection.QueryAsync<dynamic>(sql, new { StartDate = startDate, EndDate = endDate });

        // Calculate berth utilization per day
        Dictionary<DateTime, decimal> utilizationByDay = await GetDailyUtilizationAsync(connection, startDate, endDate);

        return results.Select(r => new DailyTrendDto
        {
            Date = r.Date,
            VesselArrivals = r.VesselArrivals,
            VesselDepartures = r.VesselDepartures,
            ConflictCount = r.ConflictCount,
            AverageWaitingTime = r.AverageWaitingTime,
            BerthUtilization = utilizationByDay.TryGetValue((DateTime)r.Date, out var util) ? util : 0
        });
    }

    public async Task<decimal> GetAverageWaitingTimeAsync(DateTime startDate, DateTime endDate, int? berthId = null)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        var sql = @"
            SELECT AVG(CAST(WaitingTime AS DECIMAL))
            FROM VESSEL_SCHEDULE
            WHERE ETA BETWEEN @StartDate AND @EndDate
              AND WaitingTime IS NOT NULL
              AND Status NOT IN ('Cancelled')";

        DynamicParameters parameters = new();
        parameters.Add("StartDate", startDate);
        parameters.Add("EndDate", endDate);

        if (berthId.HasValue)
        {
            sql += " AND BerthId = @BerthId";
            parameters.Add("BerthId", berthId);
        }

        return await connection.QueryFirstOrDefaultAsync<decimal?>(sql, parameters) ?? 0;
    }

    public async Task<decimal> GetETAAccuracyRateAsync(DateTime startDate, DateTime endDate)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT
                COUNT(CASE WHEN ABS(DATEDIFF(MINUTE, ETA, ATA)) <= 60 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)
            FROM VESSEL_SCHEDULE
            WHERE ETA BETWEEN @StartDate AND @EndDate
              AND ATA IS NOT NULL
              AND Status = 'Departed'";

        return await connection.QueryFirstOrDefaultAsync<decimal?>(sql,
            new { StartDate = startDate, EndDate = endDate }) ?? 0;
    }

    public async Task<decimal> GetAverageTurnaroundTimeAsync(DateTime startDate, DateTime endDate)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT AVG(DATEDIFF(MINUTE, ATA, ATD) / 60.0)
            FROM VESSEL_SCHEDULE
            WHERE ETA BETWEEN @StartDate AND @EndDate
              AND ATA IS NOT NULL AND ATD IS NOT NULL
              AND Status = 'Departed'";

        return await connection.QueryFirstOrDefaultAsync<decimal?>(sql,
            new { StartDate = startDate, EndDate = endDate }) ?? 0;
    }

    #region Private Helper Methods

    private async Task<decimal> CalculateAverageUtilizationAsync(
        System.Data.IDbConnection connection,
        DateTime startDate,
        DateTime endDate,
        int? berthId)
    {
        var totalHours = (endDate - startDate).TotalHours;
        if (totalHours <= 0)
        {
            return 0;
        }

        var sql = @"
            SELECT
                COUNT(DISTINCT b.BerthId) AS TotalBerths,
                SUM(CASE
                    WHEN vs.ATA IS NOT NULL AND vs.ATD IS NOT NULL
                    THEN DATEDIFF(MINUTE, vs.ATA, vs.ATD) / 60.0
                    WHEN vs.ETA IS NOT NULL AND vs.ETD IS NOT NULL
                    THEN DATEDIFF(MINUTE, vs.ETA, vs.ETD) / 60.0
                    ELSE ISNULL(vs.DwellTime, 0)
                END) AS TotalOccupiedHours
            FROM BERTHS b
            LEFT JOIN VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId
                AND vs.ETA BETWEEN @StartDate AND @EndDate
                AND vs.Status NOT IN ('Cancelled')
            WHERE b.IsActive = 1";

        DynamicParameters parameters = new();
        parameters.Add("StartDate", startDate);
        parameters.Add("EndDate", endDate);

        if (berthId.HasValue)
        {
            sql += " AND b.BerthId = @BerthId";
            parameters.Add("BerthId", berthId);
        }

        dynamic? result = await connection.QueryFirstOrDefaultAsync<dynamic>(sql, parameters);

        if (result == null || result.TotalBerths == 0)
        {
            return 0;
        }

        var maxCapacity = (decimal)result.TotalBerths * (decimal)totalHours;
        dynamic utilized = result.TotalOccupiedHours ?? 0m;

        return Math.Round(utilized / maxCapacity * 100, 1);
    }

    private async Task<Dictionary<DateTime, decimal>> GetDailyUtilizationAsync(
        System.Data.IDbConnection connection,
        DateTime startDate,
        DateTime endDate)
    {
        const string sql = @"
            SELECT
                CAST(vs.ETA AS DATE) AS Date,
                COUNT(DISTINCT b.BerthId) AS TotalBerths,
                SUM(CASE
                    WHEN DATEDIFF(HOUR, vs.ETA, ISNULL(vs.ETD, DATEADD(HOUR, ISNULL(vs.DwellTime, 24), vs.ETA))) > 24
                    THEN 24
                    ELSE DATEDIFF(HOUR, vs.ETA, ISNULL(vs.ETD, DATEADD(HOUR, ISNULL(vs.DwellTime, 24), vs.ETA)))
                END) AS OccupiedHours
            FROM BERTHS b
            LEFT JOIN VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId
                AND vs.ETA BETWEEN @StartDate AND @EndDate
                AND vs.Status NOT IN ('Cancelled')
            WHERE b.IsActive = 1
            GROUP BY CAST(vs.ETA AS DATE)";

        IEnumerable<dynamic> results = await connection.QueryAsync<dynamic>(sql, new { StartDate = startDate, EndDate = endDate });

        var totalBerths = await connection.QueryFirstAsync<int>(
            "SELECT COUNT(*) FROM BERTHS WHERE IsActive = 1");

        return results.ToDictionary(
            r => (DateTime)r.Date,
            r => totalBerths > 0
                ? Math.Round((decimal)(r.OccupiedHours ?? 0) / (totalBerths * 24) * 100, 1)
                : 0m
        );
    }

    #endregion
}
