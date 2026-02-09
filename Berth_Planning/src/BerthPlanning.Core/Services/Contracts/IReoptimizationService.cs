using BerthPlanning.Core.DTOs;

namespace BerthPlanning.Core.Services.Contracts;

public interface IReoptimizationService
{
    // Real-Time Re-Optimization
    Task<ReoptimizationResultDto> TriggerReoptimizationAsync(ReoptimizationRequestDto request);
    Task<ReoptimizationResultDto> OptimizeForDeviationAsync(int scheduleId, int deviationMinutes);
    Task<ReoptimizationResultDto> OptimizeForConflictsAsync(List<int> conflictIds);
    Task<bool> ApplyOptimizationAsync(string optimizationId, List<ScheduleChangeDto> changes);

    // Automatic triggers
    Task<bool> ShouldTriggerReoptimizationAsync(int scheduleId, int deviationMinutes);
}
