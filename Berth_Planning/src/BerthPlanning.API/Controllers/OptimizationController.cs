using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class OptimizationController : ControllerBase
{
    private readonly IReoptimizationService _reoptimizationService;
    private readonly ILogger<OptimizationController> _logger;

    public OptimizationController(IReoptimizationService reoptimizationService, ILogger<OptimizationController> logger)
    {
        _reoptimizationService = reoptimizationService;
        _logger = logger;
    }

    /// <summary>
    /// Trigger schedule re-optimization
    /// </summary>
    [HttpPost("trigger")]
    public async Task<ActionResult<ReoptimizationResultDto>> TriggerReoptimization(
        [FromBody] ReoptimizationRequestDto request)
    {
        try
        {
            ReoptimizationResultDto result = await _reoptimizationService.TriggerReoptimizationAsync(request);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error triggering re-optimization");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Optimize for a specific deviation
    /// </summary>
    [HttpPost("deviation/{scheduleId}")]
    public async Task<ActionResult<ReoptimizationResultDto>> OptimizeForDeviation(
        int scheduleId,
        [FromQuery] int deviationMinutes)
    {
        try
        {
            ReoptimizationResultDto result = await _reoptimizationService.OptimizeForDeviationAsync(scheduleId, deviationMinutes);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error optimizing for deviation on schedule {ScheduleId}", scheduleId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Optimize to resolve specific conflicts
    /// </summary>
    [HttpPost("conflicts")]
    public async Task<ActionResult<ReoptimizationResultDto>> OptimizeForConflicts(
        [FromBody] List<int> conflictIds)
    {
        try
        {
            if (conflictIds == null || !conflictIds.Any())
            {
                return BadRequest("At least one conflict ID is required");
            }

            ReoptimizationResultDto result = await _reoptimizationService.OptimizeForConflictsAsync(conflictIds);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error optimizing for conflicts");
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Apply optimization changes
    /// </summary>
    [HttpPost("apply/{optimizationId}")]
    public async Task<ActionResult<object>> ApplyOptimization(
        string optimizationId,
        [FromBody] List<ScheduleChangeDto> changes)
    {
        try
        {
            if (changes == null || !changes.Any())
            {
                return BadRequest("Changes are required");
            }

            bool success = await _reoptimizationService.ApplyOptimizationAsync(optimizationId, changes);

            return Ok(new
            {
                OptimizationId = optimizationId,
                Applied = success,
                ChangesCount = changes.Count,
                Message = success ? "All changes applied successfully" : "Some changes failed to apply"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error applying optimization {OptimizationId}", optimizationId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Check if re-optimization should be triggered for a schedule deviation
    /// </summary>
    [HttpGet("should-reoptimize/{scheduleId}")]
    public async Task<ActionResult<object>> ShouldTriggerReoptimization(
        int scheduleId,
        [FromQuery] int deviationMinutes)
    {
        try
        {
            bool shouldTrigger = await _reoptimizationService.ShouldTriggerReoptimizationAsync(
                scheduleId, deviationMinutes);

            return Ok(new
            {
                ScheduleId = scheduleId,
                DeviationMinutes = deviationMinutes,
                ShouldTriggerReoptimization = shouldTrigger,
                Recommendation = shouldTrigger
                    ? "Re-optimization recommended due to potential conflicts"
                    : "Current schedule remains optimal"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error checking re-optimization need for schedule {ScheduleId}", scheduleId);
            return StatusCode(500, "Internal server error");
        }
    }
}
