using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class ResourcesController : ControllerBase
{
    private readonly IResourceOptimizationService _resourceService;
    private readonly ILogger<ResourcesController> _logger;

    public ResourcesController(IResourceOptimizationService resourceService, ILogger<ResourcesController> logger)
    {
        _resourceService = resourceService;
        _logger = logger;
    }

    /// <summary>
    /// Get resource availability for a specific type and time window
    /// </summary>
    [HttpGet("availability")]
    public async Task<ActionResult<IEnumerable<ResourceAvailabilityDto>>> GetResourceAvailability(
        [FromQuery] string resourceType,
        [FromQuery] DateTime from,
        [FromQuery] DateTime until)
    {
        try
        {
            if (string.IsNullOrWhiteSpace(resourceType))
            {
                return BadRequest("Resource type is required (Crane, Tug, Pilot)");
            }

            IEnumerable<ResourceAvailabilityDto> availability = await _resourceService.GetResourceAvailabilityAsync(resourceType, from, until);
            return Ok(availability);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting resource availability for {ResourceType}", resourceType);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Get all resources required for a schedule
    /// </summary>
    [HttpGet("schedule/{scheduleId}")]
    public async Task<ActionResult<IEnumerable<ResourceAvailabilityDto>>> GetResourcesForSchedule(int scheduleId)
    {
        try
        {
            IEnumerable<ResourceAvailabilityDto> resources = await _resourceService.GetAllResourcesForScheduleAsync(scheduleId);
            return Ok(resources);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting resources for schedule {ScheduleId}", scheduleId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Optimize resource allocation for a schedule
    /// </summary>
    [HttpPost("optimize/{scheduleId}")]
    public async Task<ActionResult<ResourceOptimizationResultDto>> OptimizeResourcesForSchedule(int scheduleId)
    {
        try
        {
            ResourceOptimizationResultDto result = await _resourceService.OptimizeResourcesForScheduleAsync(scheduleId);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error optimizing resources for schedule {ScheduleId}", scheduleId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Allocate specific resources
    /// </summary>
    [HttpPost("allocate")]
    public async Task<ActionResult<ResourceOptimizationResultDto>> AllocateResources(
        [FromBody] ResourceAllocationRequestDto request)
    {
        try
        {
            if (request.ScheduleId <= 0)
            {
                return BadRequest("Valid schedule ID is required");
            }

            if (string.IsNullOrWhiteSpace(request.ResourceType))
            {
                return BadRequest("Resource type is required");
            }

            ResourceOptimizationResultDto result = await _resourceService.AllocateResourcesAsync(request);
            return Ok(result);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error allocating resources for schedule {ScheduleId}", request.ScheduleId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Release resources for a schedule
    /// </summary>
    [HttpPost("release/{scheduleId}")]
    public async Task<ActionResult<object>> ReleaseResources(int scheduleId)
    {
        try
        {
            bool success = await _resourceService.ReleaseResourcesAsync(scheduleId);

            return Ok(new
            {
                ScheduleId = scheduleId,
                Released = success,
                Message = success ? "Resources released successfully" : "No active resources found to release"
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error releasing resources for schedule {ScheduleId}", scheduleId);
            return StatusCode(500, "Internal server error");
        }
    }

    /// <summary>
    /// Detect resource conflicts in a time window
    /// </summary>
    [HttpGet("conflicts")]
    public async Task<ActionResult<IEnumerable<ResourceConflictDto>>> DetectResourceConflicts(
        [FromQuery] DateTime from,
        [FromQuery] DateTime until)
    {
        try
        {
            IEnumerable<ResourceConflictDto> conflicts = await _resourceService.DetectResourceConflictsAsync(from, until);
            return Ok(conflicts);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error detecting resource conflicts");
            return StatusCode(500, "Internal server error");
        }
    }
}
