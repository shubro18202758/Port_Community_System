namespace BerthPlanning.Core.DTOs;

public class OptimizationRequestDto
{
    public DateTime? StartTime { get; set; }
    public DateTime? EndTime { get; set; }
    public List<int>? VesselIds { get; set; }
    public string Algorithm { get; set; } = "Genetic";
    public int MaxIterations { get; set; } = 100;
}

public class OptimizationResultDto
{
    public int RunId { get; set; }
    public string Status { get; set; } = string.Empty;
    public string Algorithm { get; set; } = string.Empty;
    public int ExecutionTimeMs { get; set; }
    public decimal ImprovementScore { get; set; }
    public OptimizationMetricsDto Before { get; set; } = new();
    public OptimizationMetricsDto After { get; set; } = new();
    public List<ScheduleChangeDto> Changes { get; set; } = [];
    public List<string> Messages { get; set; } = [];
}

public class OptimizationMetricsDto
{
    public decimal TotalWaitingTime { get; set; }
    public decimal BerthUtilization { get; set; }
    public int ConflictCount { get; set; }
    public decimal AverageScore { get; set; }
}

public class ScheduleChangeDto
{
    public int ScheduleId { get; set; }
    public int VesselId { get; set; }
    public string VesselName { get; set; } = string.Empty;
    public int? OldBerthId { get; set; }
    public int? NewBerthId { get; set; }
    public string? OldBerthName { get; set; }
    public string? NewBerthName { get; set; }
    public DateTime? OldETA { get; set; }
    public DateTime? NewETA { get; set; }
    public string ChangeReason { get; set; } = string.Empty;
}
