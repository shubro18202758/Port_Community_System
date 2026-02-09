using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class WhatIfController : ControllerBase
{
    private readonly IWhatIfService _whatIfService;
    private readonly ILogger<WhatIfController> _logger;

    public WhatIfController(IWhatIfService whatIfService, ILogger<WhatIfController> logger)
    {
        _whatIfService = whatIfService;
        _logger = logger;
    }

    /// <summary>
    /// Simulate vessel delay scenario
    /// </summary>
    [HttpGet("vessel-delay")]
    public async Task<ActionResult<WhatIfScenarioResultDto>> SimulateVesselDelay(
        [FromQuery] int scheduleId,
        [FromQuery] int delayMinutes)
    {
        try
        {
            if (delayMinutes <= 0)
            {
                return BadRequest("Delay minutes must be positive");
            }

            WhatIfScenarioResultDto result = await _whatIfService.SimulateVesselDelayAsync(scheduleId, delayMinutes);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error simulating vessel delay for schedule {ScheduleId}", scheduleId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Simulate berth closure scenario
    /// </summary>
    [HttpGet("berth-closure")]
    public async Task<ActionResult<WhatIfScenarioResultDto>> SimulateBerthClosure(
        [FromQuery] int berthId,
        [FromQuery] DateTime closureStart,
        [FromQuery] DateTime closureEnd)
    {
        try
        {
            if (closureEnd <= closureStart)
            {
                return BadRequest("Closure end must be after closure start");
            }

            WhatIfScenarioResultDto result = await _whatIfService.SimulateBerthClosureAsync(berthId, closureStart, closureEnd);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error simulating berth closure for berth {BerthId}", berthId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Simulate weather alert scenario
    /// </summary>
    [HttpGet("weather-alert")]
    public async Task<ActionResult<WhatIfScenarioResultDto>> SimulateWeatherAlert(
        [FromQuery] string weatherCondition,
        [FromQuery] DateTime? until = null)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(weatherCondition))
            {
                return BadRequest("Weather condition is required");
            }

            DateTime alertEnd = until ?? DateTime.UtcNow.AddHours(6);
            WhatIfScenarioResultDto result = await _whatIfService.SimulateWeatherAlertAsync(weatherCondition, alertEnd);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error simulating weather alert: {WeatherCondition}", weatherCondition);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Simulate new vessel arrival scenario
    /// </summary>
    [HttpGet("new-vessel")]
    public async Task<ActionResult<WhatIfScenarioResultDto>> SimulateNewVessel(
        [FromQuery] int vesselId,
        [FromQuery] DateTime proposedETA)
    {
        try
        {
            if (proposedETA < DateTime.UtcNow)
            {
                return BadRequest("Proposed ETA must be in the future");
            }

            WhatIfScenarioResultDto result = await _whatIfService.SimulateNewVesselAsync(vesselId, proposedETA);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error simulating new vessel arrival for vessel {VesselId}", vesselId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Run custom what-if scenario
    /// </summary>
    [HttpPost("custom")]
    public async Task<ActionResult<WhatIfScenarioResultDto>> RunCustomScenario(
        [FromBody] WhatIfScenarioRequestDto request)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(request.ScenarioType))
            {
                return BadRequest("Scenario type is required");
            }

            WhatIfScenarioResultDto result = await _whatIfService.RunCustomScenarioAsync(request);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error running custom scenario: {ScenarioType}", request.ScenarioType);
            return StatusCode(500, "Internal server error");
        }
    }
}
