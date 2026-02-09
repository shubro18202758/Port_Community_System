using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IDashboardRepository
{
    Task<DashboardMetricsDto> GetDashboardMetricsAsync();
    Task<DashboardMetricsDto> GetDashboardMetricsByTerminalAsync(int terminalId);
    Task<IEnumerable<BerthStatusDto>> GetCurrentBerthStatusAsync();
    Task<IEnumerable<BerthStatusDto>> GetCurrentBerthStatusByTerminalAsync(int terminalId);
    Task<IEnumerable<VesselQueueDto>> GetVesselQueueAsync();
    Task<IEnumerable<TimelineEventDto>> GetBerthTimelineAsync(DateTime startDate, DateTime endDate);
    Task<IEnumerable<AlertNotification>> GetActiveAlertsAsync();
    Task<WeatherData?> GetCurrentWeatherAsync();
    Task<IEnumerable<Conflict>> GetActiveConflictsAsync();
}
