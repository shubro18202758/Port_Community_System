using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

/// <summary>
/// AI Service Controller - Exposes AI-powered features from the Python backend
/// </summary>
[ApiController]
[Route("[controller]")]
public class AIController : ControllerBase
{
    private readonly IAIServiceClient _aiService;
    private readonly ILogger<AIController> _logger;

    public AIController(IAIServiceClient aiService, ILogger<AIController> logger)
    {
        _aiService = aiService;
        _logger = logger;
    }

    // ==================== HEALTH & STATUS ====================

    /// <summary>
    /// Check AI service health status
    /// </summary>
    [HttpGet("health")]
    public async Task<ActionResult<AIServiceHealthDto>> GetHealth()
    {
        var health = await _aiService.GetHealthAsync();
        return Ok(health);
    }

    /// <summary>
    /// Get AI model information
    /// </summary>
    [HttpGet("model/info")]
    public async Task<ActionResult<AIModelInfoDto>> GetModelInfo()
    {
        var info = await _aiService.GetModelInfoAsync();
        return Ok(info);
    }

    /// <summary>
    /// Load AI model into GPU memory
    /// </summary>
    [HttpPost("model/load")]
    public async Task<ActionResult> LoadModel()
    {
        var success = await _aiService.LoadModelAsync();
        return success 
            ? Ok(new { status = "loading", message = "Model loading started in background" })
            : StatusCode(503, new { status = "error", message = "Failed to start model loading" });
    }

    // ==================== ETA PREDICTIONS ====================

    /// <summary>
    /// Get AI-powered ETA prediction for a vessel
    /// </summary>
    [HttpGet("predictions/eta/{vesselId}")]
    public async Task<ActionResult<AIETAPredictionDto>> PredictETA(int vesselId, [FromQuery] int? scheduleId = null)
    {
        var prediction = await _aiService.PredictETAAsync(vesselId, scheduleId);
        
        if (prediction == null)
            return NotFound(new { message = $"No prediction available for vessel {vesselId}" });
        
        return Ok(prediction);
    }

    /// <summary>
    /// Get ETA predictions for multiple vessels
    /// </summary>
    [HttpGet("predictions/eta/batch")]
    public async Task<ActionResult<List<AIETAPredictionDto>>> PredictETABatch([FromQuery] string vesselIds)
    {
        var ids = vesselIds.Split(',').Select(int.Parse);
        var predictions = await _aiService.PredictETABatchAsync(ids);
        return Ok(predictions);
    }

    /// <summary>
    /// Get Claude-powered ETA prediction with RAG context
    /// </summary>
    [HttpPost("predictions/eta/claude")]
    public async Task<ActionResult> GetClaudeETAPrediction([FromBody] ClaudeETARequestDto request)
    {
        var result = await _aiService.GetClaudeETAPredictionAsync(request.VesselId, request.IncludeRagContext);
        return Ok(result);
    }

    // ==================== BERTH SUGGESTIONS ====================

    /// <summary>
    /// Get AI-powered berth suggestions for a vessel
    /// </summary>
    [HttpGet("suggestions/berth/{vesselId}")]
    public async Task<ActionResult<List<AIBerthSuggestionDto>>> GetBerthSuggestions(
        int vesselId, 
        [FromQuery] DateTime? preferredEta = null,
        [FromQuery] int topN = 5)
    {
        var suggestions = await _aiService.GetBerthSuggestionsAsync(vesselId, preferredEta, topN);
        
        if (suggestions.Count == 0)
            return NotFound(new { message = $"No berth suggestions available for vessel {vesselId}" });
        
        return Ok(suggestions);
    }

    /// <summary>
    /// Get Claude-powered berth optimization
    /// </summary>
    [HttpPost("suggestions/berth/claude")]
    public async Task<ActionResult> GetClaudeBerthOptimization([FromBody] ClaudeBerthRequestDto request)
    {
        var result = await _aiService.GetClaudeBerthOptimizationAsync(
            request.VesselId, 
            request.IncludeRagContext, 
            request.TimeHorizonHours);
        return Ok(result);
    }

    // ==================== CHATBOT ====================

    /// <summary>
    /// Send message to AI chatbot
    /// </summary>
    [HttpPost("chat")]
    public async Task<ActionResult<AIChatResponseDto>> Chat([FromBody] AIChatRequestDto request)
    {
        var response = await _aiService.ChatAsync(request.Message, request.SessionId);
        
        if (response == null)
            return StatusCode(503, new { message = "AI chatbot unavailable" });
        
        return Ok(response);
    }

    /// <summary>
    /// Get chat history
    /// </summary>
    [HttpGet("chat/history")]
    public async Task<ActionResult> GetChatHistory()
    {
        var history = await _aiService.GetChatHistoryAsync();
        return Ok(new { history });
    }

    /// <summary>
    /// Clear chat history
    /// </summary>
    [HttpPost("chat/clear")]
    public async Task<ActionResult> ClearChatHistory()
    {
        await _aiService.ClearChatHistoryAsync();
        return Ok(new { status = "cleared" });
    }

    // ==================== RAG KNOWLEDGE BASE ====================

    /// <summary>
    /// Generate AI explanation using RAG
    /// </summary>
    [HttpPost("rag/explain")]
    public async Task<ActionResult<AIExplanationResponseDto>> GenerateExplanation([FromBody] AIExplanationRequestDto request)
    {
        var response = await _aiService.GenerateExplanationAsync(
            request.Query, 
            request.ContextCategory, 
            request.AdditionalContext);
        
        if (response == null)
            return StatusCode(503, new { message = "RAG service unavailable" });
        
        return Ok(response);
    }

    /// <summary>
    /// Search knowledge base
    /// </summary>
    [HttpGet("rag/search")]
    public async Task<ActionResult> SearchKnowledgeBase(
        [FromQuery] string query, 
        [FromQuery] int k = 5,
        [FromQuery] string? category = null)
    {
        var results = await _aiService.SearchKnowledgeBaseAsync(query, k, category);
        return Ok(new { results });
    }

    /// <summary>
    /// Hybrid search (vector + BM25)
    /// </summary>
    [HttpPost("rag/hybrid-search")]
    public async Task<ActionResult> HybridSearch([FromBody] HybridSearchRequestDto request)
    {
        var results = await _aiService.HybridSearchAsync(request.Query, request.TopK, request.Method);
        return Ok(new { results, method = request.Method, total_results = results.Count });
    }

    // ==================== CONFLICT DETECTION ====================

    /// <summary>
    /// Detect scheduling conflicts
    /// </summary>
    [HttpGet("conflicts")]
    public async Task<ActionResult> DetectConflicts([FromQuery] int hours = 48)
    {
        var conflicts = await _aiService.DetectConflictsAsync(hours);
        return Ok(new { time_window_hours = hours, conflicts_found = conflicts.Count, conflicts });
    }

    /// <summary>
    /// Resolve a conflict
    /// </summary>
    [HttpPost("conflicts/resolve")]
    public async Task<ActionResult> ResolveConflict([FromBody] AIConflictResolutionRequestDto request)
    {
        var result = await _aiService.ResolveConflictAsync(request.ConflictId, request.ResolutionAction);
        return Ok(result);
    }

    /// <summary>
    /// Claude-powered conflict detection and resolution
    /// </summary>
    [HttpPost("conflicts/claude")]
    public async Task<ActionResult> GetClaudeConflictResolution([FromBody] ClaudeConflictRequestDto request)
    {
        var result = await _aiService.GetClaudeConflictResolutionAsync(
            request.TimeStart, 
            request.TimeEnd, 
            request.IncludeRagContext);
        return Ok(result);
    }

    // ==================== MULTI-AGENT SYSTEM ====================

    /// <summary>
    /// Complete vessel arrival processing using multi-agent orchestration
    /// </summary>
    [HttpPost("agents/process-arrival")]
    public async Task<ActionResult<AIVesselArrivalProcessingDto>> ProcessVesselArrival([FromBody] VesselArrivalRequestDto request)
    {
        var result = await _aiService.ProcessVesselArrivalAsync(request.VesselId);
        
        if (result == null)
            return StatusCode(503, new { message = "Multi-agent system unavailable" });
        
        if (!result.Success)
            return BadRequest(result);
        
        return Ok(result);
    }

    /// <summary>
    /// Optimize schedule using AI agents
    /// </summary>
    [HttpPost("agents/optimize-schedule")]
    public async Task<ActionResult> OptimizeSchedule([FromBody] OptimizeScheduleRequestDto request)
    {
        var result = await _aiService.OptimizeScheduleAsync(request.Algorithm, request.TimeHorizonHours);
        return Ok(result);
    }

    // ==================== WHAT-IF SIMULATION ====================

    /// <summary>
    /// Run what-if simulation
    /// </summary>
    [HttpPost("simulation/what-if")]
    public async Task<ActionResult<AIWhatIfResultDto>> RunWhatIfSimulation([FromBody] AIWhatIfRequestDto request)
    {
        var result = await _aiService.RunWhatIfSimulationAsync(request);
        
        if (result == null)
            return StatusCode(503, new { message = "Simulation service unavailable" });
        
        return Ok(result);
    }

    /// <summary>
    /// Simulate delay impact
    /// </summary>
    [HttpGet("simulation/delay-impact/{vesselId}")]
    public async Task<ActionResult<AIWhatIfResultDto>> SimulateDelayImpact(int vesselId, [FromQuery] int delayHours = 4)
    {
        var result = await _aiService.SimulateDelayImpactAsync(vesselId, delayHours);
        
        if (result == null)
            return StatusCode(503, new { message = "Simulation service unavailable" });
        
        return Ok(result);
    }

    /// <summary>
    /// Simulate berth closure
    /// </summary>
    [HttpGet("simulation/berth-closure/{berthId}")]
    public async Task<ActionResult<AIWhatIfResultDto>> SimulateBerthClosure(int berthId, [FromQuery] int durationHours = 24)
    {
        var result = await _aiService.SimulateBerthClosureAsync(berthId, durationHours);
        
        if (result == null)
            return StatusCode(503, new { message = "Simulation service unavailable" });
        
        return Ok(result);
    }

    /// <summary>
    /// Simulate capacity surge
    /// </summary>
    [HttpGet("simulation/capacity-surge")]
    public async Task<ActionResult<AIWhatIfResultDto>> SimulateCapacitySurge([FromQuery] int additionalVessels = 5)
    {
        var result = await _aiService.SimulateCapacitySurgeAsync(additionalVessels);
        
        if (result == null)
            return StatusCode(503, new { message = "Simulation service unavailable" });
        
        return Ok(result);
    }

    // ==================== DASHBOARD & ANALYTICS ====================

    /// <summary>
    /// Get AI dashboard overview
    /// </summary>
    [HttpGet("dashboard/overview")]
    public async Task<ActionResult<AIDashboardOverviewDto>> GetDashboardOverview()
    {
        var overview = await _aiService.GetDashboardOverviewAsync();
        
        if (overview == null)
            return StatusCode(503, new { message = "AI dashboard unavailable" });
        
        return Ok(overview);
    }

    /// <summary>
    /// Get berth timeline
    /// </summary>
    [HttpGet("dashboard/timeline")]
    public async Task<ActionResult> GetBerthTimeline([FromQuery] int hours = 48)
    {
        var timeline = await _aiService.GetBerthTimelineAsync(hours);
        return Ok(timeline);
    }

    // ==================== REAL-TIME ALERTS ====================

    /// <summary>
    /// Get active alerts from AI service
    /// </summary>
    [HttpGet("alerts/active")]
    public async Task<ActionResult<List<AIAlertDto>>> GetActiveAlerts()
    {
        var alerts = await _aiService.GetActiveAlertsAsync();
        return Ok(alerts);
    }

    // ==================== CONSTRAINT VALIDATION ====================

    /// <summary>
    /// Validate berth allocation constraints using AI
    /// </summary>
    [HttpPost("validate/constraints")]
    public async Task<ActionResult> ValidateConstraints([FromBody] ConstraintValidationRequestDto request)
    {
        var result = await _aiService.ValidateConstraintsAsync(request.VesselId, request.BerthId, request.Eta);
        return Ok(result);
    }
}

// ==================== REQUEST DTOs ====================

public class HybridSearchRequestDto
{
    public string Query { get; set; } = string.Empty;
    public int TopK { get; set; } = 5;
    public string Method { get; set; } = "hybrid";
}

public class VesselArrivalRequestDto
{
    public int VesselId { get; set; }
}

public class OptimizeScheduleRequestDto
{
    public string Algorithm { get; set; } = "greedy";
    public int TimeHorizonHours { get; set; } = 48;
}

public class ConstraintValidationRequestDto
{
    public int VesselId { get; set; }
    public int BerthId { get; set; }
    public DateTime? Eta { get; set; }
}
