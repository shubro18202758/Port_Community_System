namespace BerthPlanning.Core.DTOs;

// ============================================
// AI SERVICE INTEGRATION DTOs
// ============================================

/// <summary>
/// AI Service health status
/// </summary>
public class AIServiceHealthDto
{
    public string Status { get; set; } = "unknown";
    public string Timestamp { get; set; } = string.Empty;
    public string ModelStatus { get; set; } = "not_loaded";
    public string DatabaseStatus { get; set; } = "disconnected";
    public string RagStatus { get; set; } = "not_initialized";
}

/// <summary>
/// AI Model information
/// </summary>
public class AIModelInfoDto
{
    public string Status { get; set; } = string.Empty;
    public string ModelName { get; set; } = string.Empty;
    public string? ModelType { get; set; }
    public string? Provider { get; set; }
    public int? ContextWindow { get; set; }
    public int? MaxOutputTokens { get; set; }
}

// ============================================
// AI-POWERED ETA PREDICTION DTOs
// ============================================

public class AIETAPredictionRequestDto
{
    public int VesselId { get; set; }
    public int? ScheduleId { get; set; }
}

public class AIETAPredictionDto
{
    public int VesselId { get; set; }
    public string VesselName { get; set; } = string.Empty;
    public string? OriginalEta { get; set; }
    public string? PredictedEta { get; set; }
    public int DeviationMinutes { get; set; }
    public double ConfidenceScore { get; set; }
    public string Status { get; set; } = "Unknown";
    public Dictionary<string, object> Factors { get; set; } = [];
    public string AiExplanation { get; set; } = string.Empty;
}

// ============================================
// AI-POWERED BERTH SUGGESTIONS DTOs
// ============================================

public class AIBerthSuggestionDto
{
    public int BerthId { get; set; }
    public string BerthName { get; set; } = string.Empty;
    public string TerminalName { get; set; } = string.Empty;
    public double TotalScore { get; set; }
    public double ConstraintScore { get; set; }
    public double UtilizationScore { get; set; }
    public double WaitingTimeScore { get; set; }
    public double PriorityScore { get; set; }
    public List<Dictionary<string, object>> Violations { get; set; } = [];
    public bool IsFeasible { get; set; }
    public string Explanation { get; set; } = string.Empty;
}

// ============================================
// CHATBOT DTOs
// ============================================

public class AIChatRequestDto
{
    public string Message { get; set; } = string.Empty;
    public string? SessionId { get; set; }
}

public class AIChatResponseDto
{
    public string Text { get; set; } = string.Empty;
    public string Intent { get; set; } = string.Empty;
    public Dictionary<string, object> Entities { get; set; } = [];
    public Dictionary<string, object>? StructuredData { get; set; }
    public List<Dictionary<string, object>> Actions { get; set; } = [];
    public double Confidence { get; set; }
}

// ============================================
// RAG (Retrieval Augmented Generation) DTOs
// ============================================

public class AIExplanationRequestDto
{
    public string Query { get; set; } = string.Empty;
    public string? ContextCategory { get; set; }
    public string? AdditionalContext { get; set; }
}

public class AIExplanationResponseDto
{
    public bool Success { get; set; }
    public string Explanation { get; set; } = string.Empty;
    public List<string> ContextUsed { get; set; } = [];
    public string Model { get; set; } = string.Empty;
}

public class AISearchResultDto
{
    public string Content { get; set; } = string.Empty;
    public string Source { get; set; } = string.Empty;
    public string Category { get; set; } = string.Empty;
    public double Score { get; set; }
    public string RetrievalMethod { get; set; } = string.Empty;
}

// ============================================
// CONFLICT DETECTION DTOs
// ============================================

public class AIConflictDto
{
    public int ConflictId { get; set; }
    public string ConflictType { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;
    public string Severity { get; set; } = "Medium";
    public int? VesselId { get; set; }
    public string? VesselName { get; set; }
    public int? BerthId { get; set; }
    public string? BerthName { get; set; }
    public DateTime DetectedAt { get; set; }
    public List<ConflictResolutionOptionDto>? ResolutionOptions { get; set; }
}

public class AIConflictResolutionRequestDto
{
    public int ConflictId { get; set; }
    public string ResolutionAction { get; set; } = string.Empty;
}

// ============================================
// WHAT-IF SIMULATION DTOs
// ============================================

public class AIWhatIfRequestDto
{
    public string ScenarioType { get; set; } = string.Empty; // delay, berth_closure, surge
    public int? VesselId { get; set; }
    public int? BerthId { get; set; }
    public int? DelayHours { get; set; } = 4;
    public int? DurationHours { get; set; } = 24;
    public int? AdditionalVessels { get; set; } = 5;
}

public class AIWhatIfResultDto
{
    public string ScenarioType { get; set; } = string.Empty;
    public bool Success { get; set; }
    public string Summary { get; set; } = string.Empty;
    public List<ImpactedScheduleDto> ImpactedSchedules { get; set; } = [];
    public Dictionary<string, object> Metrics { get; set; } = [];
    public List<string> Recommendations { get; set; } = [];
}

// ============================================
// MULTI-AGENT SYSTEM DTOs
// ============================================

public class AIVesselArrivalProcessingDto
{
    public int VesselId { get; set; }
    public bool Success { get; set; }
    public string Status { get; set; } = string.Empty;
    public AIETAPredictionDto? EtaPrediction { get; set; }
    public List<AIBerthSuggestionDto> BerthSuggestions { get; set; } = [];
    public List<AIConflictDto> DetectedConflicts { get; set; } = [];
    public Dictionary<string, object> ResourceAllocations { get; set; } = [];
    public string? Error { get; set; }
}

// ============================================
// DASHBOARD DTOs
// ============================================

public class AIDashboardOverviewDto
{
    public string Timestamp { get; set; } = string.Empty;
    public AIDashboardMetricsDto Metrics { get; set; } = new();
    public List<Dictionary<string, object>> VesselsScheduled { get; set; } = [];
    public List<Dictionary<string, object>> VesselsAtBerth { get; set; } = [];
}

public class AIDashboardMetricsDto
{
    public int VesselsInQueue { get; set; }
    public int VesselsAtBerth { get; set; }
    public int TotalBerths { get; set; }
    public double BerthUtilizationPercent { get; set; }
    public int ActiveConflicts { get; set; }
}

// ============================================
// REAL-TIME ALERTS DTOs
// ============================================

public class AIAlertDto
{
    public int AlertId { get; set; }
    public string AlertType { get; set; } = string.Empty;
    public string Title { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public string Severity { get; set; } = "INFO";  // DEBUG, INFO, WARNING, HIGH, CRITICAL
    public int? VesselId { get; set; }
    public int? BerthId { get; set; }
    public int? ScheduleId { get; set; }
    public Dictionary<string, object>? Metadata { get; set; }
    public DateTime CreatedAt { get; set; }
    public bool IsAcknowledged { get; set; }
}

// ============================================
// CLAUDE AGENT DTOs
// ============================================

public class ClaudeETARequestDto
{
    public int VesselId { get; set; }
    public bool IncludeRagContext { get; set; } = true;
}

public class ClaudeBerthRequestDto
{
    public int VesselId { get; set; }
    public bool IncludeRagContext { get; set; } = true;
    public int TimeHorizonHours { get; set; } = 48;
}

public class ClaudeConflictRequestDto
{
    public string? TimeStart { get; set; }
    public string? TimeEnd { get; set; }
    public bool IncludeRagContext { get; set; } = true;
}

// NOTE: ConflictResolutionOptionDto is defined in SuggestionDto.cs
// NOTE: ImpactedScheduleDto is defined in PredictionDto.cs
