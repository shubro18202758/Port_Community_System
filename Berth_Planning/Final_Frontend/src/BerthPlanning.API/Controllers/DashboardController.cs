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
    public async Task<ActionResult<DashboardMetricsDto>> GetMetrics([FromQuery] int? terminalId = null)
    {
        try
        {
            DashboardMetricsDto metrics;
            if (terminalId.HasValue)
            {
                metrics = await _dashboardRepository.GetDashboardMetricsByTerminalAsync(terminalId.Value);
            }
            else
            {
                metrics = await _dashboardRepository.GetDashboardMetricsAsync();
            }
            return Ok(metrics);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting dashboard metrics");
            return StatusCode(500, "Internal server error");
        }
    }

    [HttpGet("berth-status")]
    public async Task<ActionResult<IEnumerable<BerthStatusDto>>> GetBerthStatus([FromQuery] int? terminalId = null)
    {
        try
        {
            IEnumerable<BerthStatusDto> status;
            if (terminalId.HasValue)
            {
                status = await _dashboardRepository.GetCurrentBerthStatusByTerminalAsync(terminalId.Value);
            }
            else
            {
                status = await _dashboardRepository.GetCurrentBerthStatusAsync();
            }
            return Ok(status);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting berth status");
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
}
