using BerthPlanning.Core.DTOs;

namespace BerthPlanning.Core.Services.Contracts;

public interface IOptimizationService
{
    Task<OptimizationResultDto> OptimizeScheduleAsync(OptimizationRequestDto request);
    Task<OptimizationMetricsDto> CalculateCurrentMetricsAsync();
}
