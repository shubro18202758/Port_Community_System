using BerthPlanning.Core.DTOs;

namespace BerthPlanning.Core.Services.Contracts;

public interface IResourceOptimizationService
{
    // Resource Availability
    Task<IEnumerable<ResourceAvailabilityDto>> GetResourceAvailabilityAsync(string resourceType, DateTime from, DateTime until);
    Task<IEnumerable<ResourceAvailabilityDto>> GetAllResourcesForScheduleAsync(int scheduleId);

    // Resource Allocation
    Task<ResourceOptimizationResultDto> OptimizeResourcesForScheduleAsync(int scheduleId);
    Task<ResourceOptimizationResultDto> AllocateResourcesAsync(ResourceAllocationRequestDto request);
    Task<bool> ReleaseResourcesAsync(int scheduleId);

    // Resource Planning
    Task<IEnumerable<ResourceConflictDto>> DetectResourceConflictsAsync(DateTime from, DateTime until);
}
