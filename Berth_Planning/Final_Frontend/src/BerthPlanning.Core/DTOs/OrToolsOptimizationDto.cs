namespace BerthPlanning.Core.DTOs;

/// <summary>
/// Request DTO for OR-Tools global optimization
/// </summary>
public class OrToolsOptimizationRequestDto
{
    /// <summary>
    /// Start of the planning horizon
    /// </summary>
    public DateTime StartTime { get; set; } = DateTime.UtcNow;

    /// <summary>
    /// End of the planning horizon (default 7 days)
    /// </summary>
    public DateTime EndTime { get; set; } = DateTime.UtcNow.AddDays(7);

    /// <summary>
    /// Specific vessel IDs to optimize (null = all pending vessels)
    /// </summary>
    public List<int>? VesselIds { get; set; }

    /// <summary>
    /// Maximum time allowed for solver in seconds
    /// </summary>
    public int MaxSolverTimeSeconds { get; set; } = 60;

    /// <summary>
    /// Whether to auto-apply changes or just preview
    /// </summary>
    public bool AutoApply { get; set; } = false;

    /// <summary>
    /// Optimization objective weights
    /// </summary>
    public OptimizationWeightsDto Weights { get; set; } = new();
}

/// <summary>
/// Weights for multi-objective optimization
/// </summary>
public class OptimizationWeightsDto
{
    /// <summary>
    /// Weight for minimizing total waiting time (0-100)
    /// </summary>
    public int WaitingTimeWeight { get; set; } = 40;

    /// <summary>
    /// Weight for maximizing berth utilization (0-100)
    /// </summary>
    public int UtilizationWeight { get; set; } = 25;

    /// <summary>
    /// Weight for vessel-berth type compatibility (0-100)
    /// </summary>
    public int TypeMatchWeight { get; set; } = 20;

    /// <summary>
    /// Weight for respecting vessel priority (0-100)
    /// </summary>
    public int PriorityWeight { get; set; } = 15;
}

/// <summary>
/// Result DTO for OR-Tools optimization
/// </summary>
public class OrToolsOptimizationResultDto
{
    public string OptimizationId { get; set; } = Guid.NewGuid().ToString();
    public string Status { get; set; } = string.Empty;
    public string SolverStatus { get; set; } = string.Empty;
    public bool IsFeasible { get; set; }
    public bool IsOptimal { get; set; }
    public long ExecutionTimeMs { get; set; }
    public long ObjectiveValue { get; set; }
    public double ObjectiveBound { get; set; }
    public double OptimalityGap { get; set; }

    // Metrics comparison
    public OrToolsMetricsDto Before { get; set; } = new();
    public OrToolsMetricsDto After { get; set; } = new();
    public OrToolsImprovementDto Improvement { get; set; } = new();

    // Detailed assignments
    public List<OrToolsBerthAssignmentDto> Assignments { get; set; } = [];
    public List<ScheduleChangeDto> Changes { get; set; } = [];
    public List<string> Messages { get; set; } = [];

    // Solver statistics
    public OrToolsSolverStatsDto SolverStats { get; set; } = new();
}

/// <summary>
/// Metrics before/after optimization
/// </summary>
public class OrToolsMetricsDto
{
    public double TotalWaitingTimeMinutes { get; set; }
    public double AverageWaitingTimeMinutes { get; set; }
    public double BerthUtilizationPercent { get; set; }
    public int TotalConflicts { get; set; }
    public int AssignedVessels { get; set; }
    public int UnassignedVessels { get; set; }
    public double AverageCompatibilityScore { get; set; }
}

/// <summary>
/// Improvement metrics
/// </summary>
public class OrToolsImprovementDto
{
    public double WaitingTimeReductionPercent { get; set; }
    public double UtilizationImprovementPercent { get; set; }
    public int ConflictsResolved { get; set; }
    public int SchedulesChanged { get; set; }
    public double OverallImprovementScore { get; set; }
}

/// <summary>
/// Single berth assignment result
/// </summary>
public class OrToolsBerthAssignmentDto
{
    public int VesselId { get; set; }
    public string VesselName { get; set; } = string.Empty;
    public string VesselType { get; set; } = string.Empty;
    public int Priority { get; set; }

    public int BerthId { get; set; }
    public string BerthName { get; set; } = string.Empty;
    public string BerthType { get; set; } = string.Empty;
    public string TerminalName { get; set; } = string.Empty;

    public DateTime ScheduledETA { get; set; }
    public DateTime ScheduledETD { get; set; }
    public int EstimatedDwellTimeMinutes { get; set; }
    public int WaitingTimeMinutes { get; set; }

    public double CompatibilityScore { get; set; }
    public double PhysicalFitScore { get; set; }
    public double TypeMatchScore { get; set; }
    public double TotalScore { get; set; }

    public string AssignmentReason { get; set; } = string.Empty;
    public List<string> ConstraintsSatisfied { get; set; } = [];
    public List<string> Warnings { get; set; } = [];
}

/// <summary>
/// Feasibility check result
/// </summary>
public class OrToolsFeasibilityResultDto
{
    public bool IsFeasible { get; set; }
    public string Status { get; set; } = string.Empty;
    public List<ConstraintViolationDto> Violations { get; set; } = [];
    public List<string> AlternativeSuggestions { get; set; } = [];
    public DateTime? NearestFeasibleETA { get; set; }
    public int? AlternativeBerthId { get; set; }
    public string? AlternativeBerthName { get; set; }
}

/// <summary>
/// OR-Tools solver statistics
/// </summary>
public class OrToolsSolverStatsDto
{
    public string SolverName { get; set; } = "CP-SAT";
    public int NumVariables { get; set; }
    public int NumConstraints { get; set; }
    public int NumBranches { get; set; }
    public int NumConflicts { get; set; }
    public double WallTime { get; set; }
    public double UserTime { get; set; }
    public string StatusMessage { get; set; } = string.Empty;
}
