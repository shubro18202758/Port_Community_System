using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class AnalyticsController : ControllerBase
{
    private readonly IAnalyticsService _analyticsService;
    private readonly ILogger<AnalyticsController> _logger;

    public AnalyticsController(IAnalyticsService analyticsService, ILogger<AnalyticsController> logger)
    {
        _analyticsService = analyticsService;
        _logger = logger;
    }

    /// <summary>
    /// Get comprehensive historical analytics
    /// </summary>
    [HttpGet("historical")]
    public async Task<ActionResult<HistoricalAnalyticsDto>> GetHistoricalAnalytics(
        [FromQuery] DateTime startDate,
        [FromQuery] DateTime endDate,
        [FromQuery] string? groupBy = null,
        [FromQuery] int? berthId = null,
        [FromQuery] string? vesselType = null)
    {
        try
        {
            if (endDate <= startDate)
            {
                return BadRequest("End date must be after start date");
            }

            AnalyticsPeriodRequestDto request = new()
            {
                StartDate = startDate,
                EndDate = endDate,
                GroupBy = groupBy,
                BerthId = berthId,
                VesselType = vesselType
            };

            HistoricalAnalyticsDto analytics = await _analyticsService.GetHistoricalAnalyticsAsync(request);
            return Ok(analytics);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting historical analytics");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get berth utilization breakdown
    /// </summary>
    [HttpGet("berth-utilization")]
    public async Task<ActionResult<IEnumerable<BerthUtilizationDto>>> GetBerthUtilization(
        [FromQuery] DateTime startDate,
        [FromQuery] DateTime endDate)
    {
        try
        {
            IEnumerable<BerthUtilizationDto> utilization = await _analyticsService.GetBerthUtilizationAsync(startDate, endDate);
            return Ok(utilization);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting berth utilization");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get vessel type statistics
    /// </summary>
    [HttpGet("vessel-stats")]
    public async Task<ActionResult<IEnumerable<VesselTypeStatsDto>>> GetVesselTypeStats(
        [FromQuery] DateTime startDate,
        [FromQuery] DateTime endDate)
    {
        try
        {
            IEnumerable<VesselTypeStatsDto> stats = await _analyticsService.GetVesselTypeStatsAsync(startDate, endDate);
            return Ok(stats);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting vessel type stats");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get daily trends
    /// </summary>
    [HttpGet("daily-trends")]
    public async Task<ActionResult<IEnumerable<DailyTrendDto>>> GetDailyTrends(
        [FromQuery] DateTime startDate,
        [FromQuery] DateTime endDate)
    {
        try
        {
            IEnumerable<DailyTrendDto> trends = await _analyticsService.GetDailyTrendsAsync(startDate, endDate);
            return Ok(trends);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting daily trends");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get average waiting time
    /// </summary>
    [HttpGet("waiting-time")]
    public async Task<ActionResult<object>> GetAverageWaitingTime(
        [FromQuery] DateTime startDate,
        [FromQuery] DateTime endDate,
        [FromQuery] int? berthId = null)
    {
        try
        {
            var avgWaitingTime = await _analyticsService.GetAverageWaitingTimeAsync(startDate, endDate, berthId);

            return Ok(new
            {
                StartDate = startDate,
                EndDate = endDate,
                BerthId = berthId,
                AverageWaitingTimeMinutes = Math.Round(avgWaitingTime, 1)
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting average waiting time");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get ETA accuracy rate
    /// </summary>
    [HttpGet("eta-accuracy")]
    public async Task<ActionResult<object>> GetETAAccuracy(
        [FromQuery] DateTime startDate,
        [FromQuery] DateTime endDate)
    {
        try
        {
            var accuracyRate = await _analyticsService.GetETAAccuracyRateAsync(startDate, endDate);

            return Ok(new
            {
                StartDate = startDate,
                EndDate = endDate,
                ETAAccuracyPercentage = Math.Round(accuracyRate, 1),
                Description = "Percentage of arrivals within 1 hour of predicted ETA"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting ETA accuracy");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get average turnaround time
    /// </summary>
    [HttpGet("turnaround-time")]
    public async Task<ActionResult<object>> GetAverageTurnaroundTime(
        [FromQuery] DateTime startDate,
        [FromQuery] DateTime endDate)
    {
        try
        {
            var avgTurnaround = await _analyticsService.GetAverageTurnaroundTimeAsync(startDate, endDate);

            return Ok(new
            {
                StartDate = startDate,
                EndDate = endDate,
                AverageTurnaroundTimeHours = Math.Round(avgTurnaround, 1),
                Description = "Average time from arrival to departure"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting average turnaround time");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get quick summary for last 7/30/90 days
    /// </summary>
    [HttpGet("summary/{period}")]
    public async Task<ActionResult<HistoricalAnalyticsDto>> GetQuickSummary(string period)
    {
        try
        {
            DateTime endDate = DateTime.UtcNow;
            DateTime startDate = period.ToLower() switch
            {
                "7d" or "week" => endDate.AddDays(-7),
                "30d" or "month" => endDate.AddDays(-30),
                "90d" or "quarter" => endDate.AddDays(-90),
                "365d" or "year" => endDate.AddDays(-365),
                _ => endDate.AddDays(-30) // Default to 30 days
            };

            AnalyticsPeriodRequestDto request = new()
            {
                StartDate = startDate,
                EndDate = endDate
            };

            HistoricalAnalyticsDto analytics = await _analyticsService.GetHistoricalAnalyticsAsync(request);
            return Ok(analytics);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting summary for period {Period}", period);
            return StatusCode(500, "Internal server error");
        }
    }
}
