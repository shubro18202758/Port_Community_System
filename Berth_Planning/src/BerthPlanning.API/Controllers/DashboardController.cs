using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class DashboardController : ControllerBase
{
    private readonly IDashboardRepository _dashboardRepository;
    private readonly ILogger<DashboardController> _logger;

    public DashboardController(IDashboardRepository dashboardRepository, ILogger<DashboardController> logger)
    {
        _dashboardRepository = dashboardRepository;
        _logger = logger;
    }

    [HttpGet("metrics")]
    public async Task<ActionResult<DashboardMetricsDto>> GetMetrics()
    {
        try
        {
            DashboardMetricsDto metrics = await _dashboardRepository.GetDashboardMetricsAsync();
            return Ok(metrics);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting dashboard metrics");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("berth-status")]
    public async Task<ActionResult<IEnumerable<BerthStatusDto>>> GetBerthStatus()
    {
        try
        {
            IEnumerable<BerthStatusDto> status = await _dashboardRepository.GetCurrentBerthStatusAsync();
            return Ok(status);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting berth status");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("vessel-queue")]
    public async Task<ActionResult<IEnumerable<VesselQueueDto>>> GetVesselQueue()
    {
        try
        {
            IEnumerable<VesselQueueDto> queue = await _dashboardRepository.GetVesselQueueAsync();
            return Ok(queue);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting vessel queue");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("timeline")]
    public async Task<ActionResult<IEnumerable<TimelineEventDto>>> GetTimeline(
        [FromQuery] DateTime? startDate = null,
        [FromQuery] DateTime? endDate = null)
    {
        try
        {
            DateTime start = startDate ?? DateTime.UtcNow.AddDays(-1);
            DateTime end = endDate ?? DateTime.UtcNow.AddDays(7);

            IEnumerable<TimelineEventDto> timeline = await _dashboardRepository.GetBerthTimelineAsync(start, end);
            return Ok(timeline);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting timeline");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("alerts")]
    public async Task<ActionResult<IEnumerable<object>>> GetAlerts()
    {
        try
        {
            IEnumerable<AlertNotification> alerts = await _dashboardRepository.GetActiveAlertsAsync();
            return Ok(alerts);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting alerts");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("weather")]
    public async Task<ActionResult<object>> GetCurrentWeather()
    {
        try
        {
            WeatherData? weather = await _dashboardRepository.GetCurrentWeatherAsync();
            return weather == null ? (ActionResult<object>)Ok(new { Message = "No weather data available" }) : (ActionResult<object>)Ok(weather);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting weather");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("conflicts")]
    public async Task<ActionResult<IEnumerable<object>>> GetConflicts()
    {
        try
        {
            IEnumerable<Conflict> conflicts = await _dashboardRepository.GetActiveConflictsAsync();
            return Ok(conflicts);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting conflicts");
            return StatusCode(500, "Internal server error");
        }
    }
}
