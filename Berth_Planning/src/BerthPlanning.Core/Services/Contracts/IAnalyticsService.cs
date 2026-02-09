using BerthPlanning.Core.DTOs;

namespace BerthPlanning.Core.Services.Contracts;

public interface IAnalyticsService
{
    // Historical Analytics
    Task<HistoricalAnalyticsDto> GetHistoricalAnalyticsAsync(AnalyticsPeriodRequestDto request);
    Task<IEnumerable<BerthUtilizationDto>> GetBerthUtilizationAsync(DateTime startDate, DateTime endDate);
    Task<IEnumerable<VesselTypeStatsDto>> GetVesselTypeStatsAsync(DateTime startDate, DateTime endDate);
    Task<IEnumerable<DailyTrendDto>> GetDailyTrendsAsync(DateTime startDate, DateTime endDate);

    // Performance metrics
    Task<decimal> GetAverageWaitingTimeAsync(DateTime startDate, DateTime endDate, int? berthId = null);
    Task<decimal> GetETAAccuracyRateAsync(DateTime startDate, DateTime endDate);
    Task<decimal> GetAverageTurnaroundTimeAsync(DateTime startDate, DateTime endDate);
}
