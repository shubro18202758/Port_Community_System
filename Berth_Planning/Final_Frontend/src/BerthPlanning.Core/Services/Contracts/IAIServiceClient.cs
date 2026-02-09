using BerthPlanning.Core.DTOs;

namespace BerthPlanning.Core.Services.Contracts;

/// <summary>
/// Interface for AI Service Client - connects .NET backend to Python AI service
/// </summary>
public interface IAIServiceClient
{
    // ==================== HEALTH & STATUS ====================
    
    /// <summary>
    /// Check AI service health status
    /// </summary>
    Task<AIServiceHealthDto> GetHealthAsync();
    
    /// <summary>
    /// Get AI model information
    /// </summary>
    Task<AIModelInfoDto> GetModelInfoAsync();

    /// <summary>
    /// Load AI model into GPU memory
    /// </summary>
    Task<bool> LoadModelAsync();

    // ==================== ETA PREDICTIONS ====================
    
    /// <summary>
    /// Get AI-powered ETA prediction for a vessel
    /// </summary>
    Task<AIETAPredictionDto?> PredictETAAsync(int vesselId, int? scheduleId = null);

    /// <summary>
    /// Get ETA predictions for multiple vessels
    /// </summary>
    Task<List<AIETAPredictionDto>> PredictETABatchAsync(IEnumerable<int> vesselIds);

    /// <summary>
    /// Get Claude-powered ETA prediction with RAG context
    /// </summary>
    Task<Dictionary<string, object>> GetClaudeETAPredictionAsync(int vesselId, bool includeRagContext = true);

    // ==================== BERTH SUGGESTIONS ====================
    
    /// <summary>
    /// Get AI-powered berth suggestions for a vessel
    /// </summary>
    Task<List<AIBerthSuggestionDto>> GetBerthSuggestionsAsync(int vesselId, DateTime? preferredEta = null, int topN = 5);

    /// <summary>
    /// Get Claude-powered berth optimization
    /// </summary>
    Task<Dictionary<string, object>> GetClaudeBerthOptimizationAsync(int vesselId, bool includeRagContext = true, int timeHorizonHours = 48);

    // ==================== CHATBOT ====================
    
    /// <summary>
    /// Send message to AI chatbot
    /// </summary>
    Task<AIChatResponseDto?> ChatAsync(string message, string? sessionId = null);

    /// <summary>
    /// Get chat history
    /// </summary>
    Task<List<Dictionary<string, object>>> GetChatHistoryAsync();

    /// <summary>
    /// Clear chat history
    /// </summary>
    Task ClearChatHistoryAsync();

    // ==================== RAG KNOWLEDGE BASE ====================
    
    /// <summary>
    /// Generate AI explanation using RAG
    /// </summary>
    Task<AIExplanationResponseDto?> GenerateExplanationAsync(string query, string? contextCategory = null, string? additionalContext = null);

    /// <summary>
    /// Search knowledge base
    /// </summary>
    Task<List<AISearchResultDto>> SearchKnowledgeBaseAsync(string query, int k = 5, string? category = null);

    /// <summary>
    /// Hybrid search (vector + BM25)
    /// </summary>
    Task<List<AISearchResultDto>> HybridSearchAsync(string query, int topK = 5, string method = "hybrid");

    // ==================== CONFLICT DETECTION ====================
    
    /// <summary>
    /// Detect scheduling conflicts
    /// </summary>
    Task<List<AIConflictDto>> DetectConflictsAsync(int timeWindowHours = 48);

    /// <summary>
    /// Resolve a conflict
    /// </summary>
    Task<Dictionary<string, object>> ResolveConflictAsync(int conflictId, string resolutionAction);

    /// <summary>
    /// Claude-powered conflict detection and resolution
    /// </summary>
    Task<Dictionary<string, object>> GetClaudeConflictResolutionAsync(string? timeStart = null, string? timeEnd = null, bool includeRagContext = true);

    // ==================== MULTI-AGENT SYSTEM ====================
    
    /// <summary>
    /// Complete vessel arrival processing using multi-agent orchestration
    /// </summary>
    Task<AIVesselArrivalProcessingDto?> ProcessVesselArrivalAsync(int vesselId);

    /// <summary>
    /// Optimize schedule using AI agents
    /// </summary>
    Task<Dictionary<string, object>> OptimizeScheduleAsync(string algorithm = "greedy", int timeHorizonHours = 48);

    // ==================== WHAT-IF SIMULATION ====================
    
    /// <summary>
    /// Run what-if simulation
    /// </summary>
    Task<AIWhatIfResultDto?> RunWhatIfSimulationAsync(AIWhatIfRequestDto request);

    /// <summary>
    /// Simulate delay impact
    /// </summary>
    Task<AIWhatIfResultDto?> SimulateDelayImpactAsync(int vesselId, int delayHours = 4);

    /// <summary>
    /// Simulate berth closure
    /// </summary>
    Task<AIWhatIfResultDto?> SimulateBerthClosureAsync(int berthId, int durationHours = 24);

    /// <summary>
    /// Simulate capacity surge
    /// </summary>
    Task<AIWhatIfResultDto?> SimulateCapacitySurgeAsync(int additionalVessels = 5);

    // ==================== DASHBOARD & ANALYTICS ====================
    
    /// <summary>
    /// Get AI dashboard overview
    /// </summary>
    Task<AIDashboardOverviewDto?> GetDashboardOverviewAsync();

    /// <summary>
    /// Get berth timeline
    /// </summary>
    Task<Dictionary<string, object>> GetBerthTimelineAsync(int hours = 48);

    // ==================== REAL-TIME ALERTS ====================
    
    /// <summary>
    /// Get active alerts from AI service
    /// </summary>
    Task<List<AIAlertDto>> GetActiveAlertsAsync();

    // ==================== CONSTRAINT VALIDATION ====================
    
    /// <summary>
    /// Validate berth allocation constraints
    /// </summary>
    Task<Dictionary<string, object>> ValidateConstraintsAsync(int vesselId, int berthId, DateTime? eta = null);
}
