using BerthPlanning.Core.DTOs;

namespace BerthPlanning.Core.Services.Contracts;

/// <summary>
/// Interface for Google OR-Tools based berth optimization service
/// Provides global optimal scheduling using Constraint Programming (CP-SAT solver)
/// </summary>
public interface IBerthOptimizationOrToolsService
{
    /// <summary>
    /// Performs global optimization of berth assignments for all pending vessels
    /// Uses CP-SAT solver to find optimal allocation minimizing total weighted cost
    /// </summary>
    Task<OrToolsOptimizationResultDto> OptimizeGlobalScheduleAsync(OrToolsOptimizationRequestDto request);

    /// <summary>
    /// Optimizes assignment for a single vessel considering all constraints
    /// Returns top N best berth assignments with scores
    /// </summary>
    Task<List<OrToolsBerthAssignmentDto>> OptimizeSingleVesselAsync(int vesselId, DateTime preferredETA);

    /// <summary>
    /// Re-optimizes schedules when a deviation or conflict is detected
    /// Attempts to find better assignments while minimizing disruption
    /// </summary>
    Task<OrToolsOptimizationResultDto> ReoptimizeOnDeviationAsync(int scheduleId, int deviationMinutes);

    /// <summary>
    /// Validates if a proposed schedule is feasible using constraint satisfaction
    /// </summary>
    Task<OrToolsFeasibilityResultDto> CheckFeasibilityAsync(int vesselId, int berthId, DateTime eta, DateTime etd);

    /// <summary>
    /// Gets optimization statistics and solver metrics
    /// </summary>
    Task<OrToolsSolverStatsDto> GetSolverStatisticsAsync();
}
