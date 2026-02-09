namespace BerthPlanning.Core.DTOs;

// ============================================
// PREDICTIVE ETA CALCULATION DTOs
// ============================================

public class ETAPredictionRequestDto
{
    public int VesselId { get; set; }
    public int? ScheduleId { get; set; }
}

public class ETAPredictionDto
{
    public int VesselId { get; set; }
    public int? ScheduleId { get; set; }
    public string VesselName { get; set; } = string.Empty;

    // Original ETA from schedule
    public DateTime? OriginalETA { get; set; }

    // AI-Predicted ETA based on AIS data
    public DateTime? PredictedETA { get; set; }

    // Deviation in minutes (positive = delayed, negative = early)
    public int DeviationMinutes { get; set; }

    // Confidence score (0-100)
    public decimal ConfidenceScore { get; set; }

    // Prediction factors
    public PredictionFactorsDto Factors { get; set; } = new();

    // Current vessel position
    public PredictedVesselPositionDto? CurrentPosition { get; set; }

    // Status: OnTime, Early, Delayed, Critical
    public string Status { get; set; } = "Unknown";

    public DateTime CalculatedAt { get; set; }
}

public class PredictionFactorsDto
{
    public decimal DistanceToPort { get; set; }  // Nautical miles
    public decimal CurrentSpeed { get; set; }     // Knots
    public decimal AverageSpeed { get; set; }     // Historical average
    public decimal WeatherImpact { get; set; }    // Factor (1.0 = no impact)
    public decimal TidalImpact { get; set; }      // Factor
    public decimal HistoricalAccuracy { get; set; } // Past prediction accuracy
    public string PredictionMethod { get; set; } = string.Empty;
}

public class PredictedVesselPositionDto
{
    public decimal Latitude { get; set; }
    public decimal Longitude { get; set; }
    public decimal? Speed { get; set; }
    public decimal? Course { get; set; }
    public decimal? Heading { get; set; }
    public string? NavigationStatus { get; set; }
    public DateTime RecordedAt { get; set; }
}

// ============================================
// ARRIVAL DEVIATION DETECTION DTOs
// ============================================

public class DeviationAlertDto
{
    public int AlertId { get; set; }
    public int ScheduleId { get; set; }
    public int VesselId { get; set; }
    public string VesselName { get; set; } = string.Empty;
    public int? BerthId { get; set; }
    public string? BerthName { get; set; }

    // Deviation details
    public DateTime OriginalETA { get; set; }
    public DateTime PredictedETA { get; set; }
    public int DeviationMinutes { get; set; }

    // Severity: Low (<30min), Medium (30-60min), High (1-2hr), Critical (>2hr)
    public string Severity { get; set; } = "Low";

    // Type: Early, Delayed
    public string DeviationType { get; set; } = "Delayed";

    // Impact assessment
    public List<ImpactedScheduleDto> ImpactedSchedules { get; set; } = [];

    public bool RequiresReoptimization { get; set; }
    public DateTime DetectedAt { get; set; }
}

public class ImpactedScheduleDto
{
    public int ScheduleId { get; set; }
    public int VesselId { get; set; }
    public string VesselName { get; set; } = string.Empty;
    public int? BerthId { get; set; }
    public string? BerthName { get; set; }
    public string ImpactType { get; set; } = string.Empty; // Overlap, Delayed, Cascade
    public int ImpactMinutes { get; set; }
}

// ============================================
// WHAT-IF SIMULATION DTOs
// ============================================

public class WhatIfScenarioRequestDto
{
    public string ScenarioType { get; set; } = string.Empty; // VesselDelay, BerthClosure, WeatherAlert, NewVessel
    public int? VesselId { get; set; }
    public int? ScheduleId { get; set; }
    public int? BerthId { get; set; }
    public int? DelayMinutes { get; set; }
    public DateTime? NewETA { get; set; }
    public DateTime? ClosureStart { get; set; }
    public DateTime? ClosureEnd { get; set; }
    public string? WeatherCondition { get; set; }
}

public class WhatIfScenarioResultDto
{
    public string ScenarioId { get; set; } = Guid.NewGuid().ToString();
    public string ScenarioType { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;

    // Current state
    public ScenarioMetricsDto CurrentState { get; set; } = new();

    // Projected state after scenario
    public ScenarioMetricsDto ProjectedState { get; set; } = new();

    // Impact analysis
    public List<ScheduleImpactDto> AffectedSchedules { get; set; } = [];
    public List<ConflictProjectionDto> ProjectedConflicts { get; set; } = [];

    // Recommendations
    public List<ScenarioRecommendationDto> Recommendations { get; set; } = [];

    public DateTime CalculatedAt { get; set; }
}

public class ScenarioMetricsDto
{
    public int TotalSchedules { get; set; }
    public int ConflictCount { get; set; }
    public decimal AverageWaitingTime { get; set; }
    public decimal BerthUtilization { get; set; }
    public int OnTimeArrivals { get; set; }
    public int DelayedArrivals { get; set; }
}

public class ScheduleImpactDto
{
    public int ScheduleId { get; set; }
    public int VesselId { get; set; }
    public string VesselName { get; set; } = string.Empty;
    public int? BerthId { get; set; }
    public string? BerthName { get; set; }

    public DateTime OriginalETA { get; set; }
    public DateTime? OriginalETD { get; set; }
    public DateTime ProjectedETA { get; set; }
    public DateTime? ProjectedETD { get; set; }

    public int DelayMinutes { get; set; }
    public string ImpactSeverity { get; set; } = "None"; // None, Low, Medium, High, Critical
    public string ChangeDescription { get; set; } = string.Empty;
}

public class ConflictProjectionDto
{
    public int Schedule1Id { get; set; }
    public int Schedule2Id { get; set; }
    public string Vessel1Name { get; set; } = string.Empty;
    public string Vessel2Name { get; set; } = string.Empty;
    public int? BerthId { get; set; }
    public string? BerthName { get; set; }
    public string ConflictType { get; set; } = string.Empty;
    public int OverlapMinutes { get; set; }
}

public class ScenarioRecommendationDto
{
    public int Priority { get; set; }
    public string Action { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public int? TargetScheduleId { get; set; }
    public int? TargetBerthId { get; set; }
    public string? NewBerthName { get; set; }
    public DateTime? SuggestedTime { get; set; }
    public decimal ImprovementScore { get; set; }
}

// ============================================
// RE-OPTIMIZATION DTOs
// ============================================

public class ReoptimizationRequestDto
{
    public string TriggerType { get; set; } = string.Empty; // Deviation, Conflict, Manual, Weather
    public int? TriggeredByScheduleId { get; set; }
    public List<int>? AffectedScheduleIds { get; set; }
    public DateTime? OptimizationWindow { get; set; }
    public bool AutoApply { get; set; } = false;
}

public class ReoptimizationResultDto
{
    public string OptimizationId { get; set; } = Guid.NewGuid().ToString();
    public string TriggerType { get; set; } = string.Empty;
    public string Status { get; set; } = string.Empty; // Success, PartialSuccess, NoChangesNeeded, Failed

    public int SchedulesAnalyzed { get; set; }
    public int SchedulesModified { get; set; }
    public int ConflictsResolved { get; set; }
    public int NewConflictsCreated { get; set; }

    public decimal WaitingTimeReduction { get; set; }
    public decimal UtilizationImprovement { get; set; }

    public List<ScheduleChangeDto> ProposedChanges { get; set; } = [];
    public List<string> Messages { get; set; } = [];

    public DateTime CalculatedAt { get; set; }
    public bool Applied { get; set; }
}

// ============================================
// RESOURCE OPTIMIZATION DTOs
// ============================================

public class ResourceAllocationRequestDto
{
    public int ScheduleId { get; set; }
    public string ResourceType { get; set; } = string.Empty; // Crane, Tug, Pilot
    public int QuantityRequired { get; set; }
    public DateTime RequiredFrom { get; set; }
    public DateTime RequiredUntil { get; set; }
}

public class ResourceAvailabilityDto
{
    public int ResourceId { get; set; }
    public string ResourceType { get; set; } = string.Empty;
    public string ResourceName { get; set; } = string.Empty;
    public bool IsAvailable { get; set; }
    public DateTime? AvailableFrom { get; set; }
    public DateTime? AvailableUntil { get; set; }
    public string? CurrentAssignment { get; set; }
}

public class ResourceOptimizationResultDto
{
    public int ScheduleId { get; set; }
    public string VesselName { get; set; } = string.Empty;

    public List<ResourceAssignmentDto> Assignments { get; set; } = [];
    public List<ResourceConflictDto> Conflicts { get; set; } = [];

    public bool AllResourcesAvailable { get; set; }
    public string? AlternativeRecommendation { get; set; }
}

public class ResourceAssignmentDto
{
    public int ResourceId { get; set; }
    public string ResourceType { get; set; } = string.Empty;
    public string ResourceName { get; set; } = string.Empty;
    public DateTime AssignedFrom { get; set; }
    public DateTime AssignedUntil { get; set; }
}

public class ResourceConflictDto
{
    public string ResourceType { get; set; } = string.Empty;
    public int RequiredQuantity { get; set; }
    public int AvailableQuantity { get; set; }
    public string ConflictDescription { get; set; } = string.Empty;
}

// ============================================
// HISTORICAL ANALYTICS DTOs
// ============================================

public class AnalyticsPeriodRequestDto
{
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public string? GroupBy { get; set; } // Day, Week, Month
    public int? BerthId { get; set; }
    public string? VesselType { get; set; }
}

public class HistoricalAnalyticsDto
{
    public DateTime PeriodStart { get; set; }
    public DateTime PeriodEnd { get; set; }

    // Summary metrics
    public int TotalVesselCalls { get; set; }
    public int CompletedCalls { get; set; }
    public int CancelledCalls { get; set; }

    // Performance metrics
    public decimal AverageBerthUtilization { get; set; }
    public decimal AverageWaitingTime { get; set; }
    public decimal AverageTurnaroundTime { get; set; }
    public decimal AverageDwellTime { get; set; }

    // ETA accuracy
    public decimal ETAAccuracyRate { get; set; }  // % within 1 hour
    public decimal AverageETADeviation { get; set; }  // Minutes

    // Conflict stats
    public int TotalConflicts { get; set; }
    public int ResolvedConflicts { get; set; }

    // Breakdown data
    public List<BerthUtilizationDto> BerthUtilization { get; set; } = [];
    public List<VesselTypeStatsDto> VesselTypeStats { get; set; } = [];
    public List<DailyTrendDto> DailyTrends { get; set; } = [];
}

public class BerthUtilizationDto
{
    public int BerthId { get; set; }
    public string BerthName { get; set; } = string.Empty;
    public decimal UtilizationPercent { get; set; }
    public int VesselCount { get; set; }
    public decimal TotalOccupiedHours { get; set; }
    public decimal AverageWaitingTime { get; set; }
}

public class VesselTypeStatsDto
{
    public string VesselType { get; set; } = string.Empty;
    public int Count { get; set; }
    public decimal AverageWaitingTime { get; set; }
    public decimal AverageDwellTime { get; set; }
    public decimal AverageTurnaroundTime { get; set; }
}

public class DailyTrendDto
{
    public DateTime Date { get; set; }
    public int VesselArrivals { get; set; }
    public int VesselDepartures { get; set; }
    public decimal BerthUtilization { get; set; }
    public decimal AverageWaitingTime { get; set; }
    public int ConflictCount { get; set; }
}
