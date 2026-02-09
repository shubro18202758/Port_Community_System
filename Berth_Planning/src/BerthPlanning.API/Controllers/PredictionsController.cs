using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class PredictionsController : ControllerBase
{
    private readonly IPredictionService _predictionService;
    private readonly ILogger<PredictionsController> _logger;

    public PredictionsController(IPredictionService predictionService, ILogger<PredictionsController> logger)
    {
        _predictionService = predictionService;
        _logger = logger;
    }

    /// <summary>
    /// Get ETA prediction for a specific vessel
    /// </summary>
    [HttpGet("eta/{vesselId}")]
    public async Task<ActionResult<ETAPredictionDto>> GetETAPrediction(int vesselId, [FromQuery] int? scheduleId = null)
    {
        try
        {
            ETAPredictionDto prediction = await _predictionService.PredictETAAsync(vesselId, scheduleId);
            return Ok(prediction);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error predicting ETA for vessel {VesselId}", vesselId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get ETA predictions for all active vessels
    /// </summary>
    [HttpGet("eta/active")]
    public async Task<ActionResult<IEnumerable<ETAPredictionDto>>> GetAllActiveETAPredictions()
    {
        try
        {
            IEnumerable<ETAPredictionDto> predictions = await _predictionService.PredictAllActiveETAsAsync();
            return Ok(predictions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error predicting ETAs for active vessels");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Detect all current deviations
    /// </summary>
    [HttpGet("deviations")]
    public async Task<ActionResult<IEnumerable<DeviationAlertDto>>> GetDeviations()
    {
        try
        {
            IEnumerable<DeviationAlertDto> deviations = await _predictionService.DetectDeviationsAsync();
            return Ok(deviations);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error detecting deviations");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Check deviation for a specific schedule
    /// </summary>
    [HttpGet("deviations/schedule/{scheduleId}")]
    public async Task<ActionResult<DeviationAlertDto>> CheckScheduleDeviation(int scheduleId)
    {
        try
        {
            DeviationAlertDto? deviation = await _predictionService.CheckScheduleDeviationAsync(scheduleId);

            return deviation == null ? (ActionResult<DeviationAlertDto>)Ok(new { Message = "No significant deviation detected", ScheduleId = scheduleId }) : (ActionResult<DeviationAlertDto>)Ok(deviation);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking deviation for schedule {ScheduleId}", scheduleId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Analyze impact of a potential deviation
    /// </summary>
    [HttpGet("deviations/impact/{scheduleId}")]
    public async Task<ActionResult<IEnumerable<ImpactedScheduleDto>>> AnalyzeDeviationImpact(
        int scheduleId,
        [FromQuery] int deviationMinutes)
    {
        try
        {
            IEnumerable<ImpactedScheduleDto> impact = await _predictionService.AnalyzeDeviationImpactAsync(scheduleId, deviationMinutes);
            return Ok(impact);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error analyzing deviation impact for schedule {ScheduleId}", scheduleId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Calculate distance from vessel to port
    /// </summary>
    [HttpGet("distance/{vesselId}")]
    public async Task<ActionResult<object>> GetDistanceToPort(
        int vesselId,
        [FromQuery] decimal portLat = 18.9388m,
        [FromQuery] decimal portLon = 72.8354m)
    {
        try
        {
            decimal distance = await _predictionService.CalculateDistanceToPortAsync(vesselId, portLat, portLon);

            return Ok(new
            {
                VesselId = vesselId,
                DistanceNauticalMiles = Math.Round(distance, 2),
                PortLatitude = portLat,
                PortLongitude = portLon
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error calculating distance for vessel {VesselId}", vesselId);
            return StatusCode(500, "Internal server error");
        }
    }
}
