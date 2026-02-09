using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IDashboardRepository
{
    Task<DashboardMetricsDto> GetDashboardMetricsAsync();
    Task<IEnumerable<BerthStatusDto>> GetCurrentBerthStatusAsync();
    Task<IEnumerable<VesselQueueDto>> GetVesselQueueAsync();
    Task<IEnumerable<TimelineEventDto>> GetBerthTimelineAsync(DateTime startDate, DateTime endDate);
    Task<IEnumerable<AlertNotification>> GetActiveAlertsAsync();
    Task<WeatherData?> GetCurrentWeatherAsync();
    Task<IEnumerable<Conflict>> GetActiveConflictsAsync();
}
