using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;

namespace BerthPlanning.Infrastructure.Services;

/// <summary>
/// HTTP client for communicating with the Python AI service
/// </summary>
public class AIServiceClient : IAIServiceClient
{
    private readonly HttpClient _httpClient;
    private readonly ILogger<AIServiceClient> _logger;
    private readonly string _baseUrl;
    private readonly JsonSerializerOptions _jsonOptions;

    public AIServiceClient(
        HttpClient httpClient,
        IConfiguration configuration,
        ILogger<AIServiceClient> logger)
    {
        _httpClient = httpClient;
        _logger = logger;
        _baseUrl = configuration["AIService:BaseUrl"] ?? "http://localhost:8000";
        
        _httpClient.BaseAddress = new Uri(_baseUrl);
        _httpClient.Timeout = TimeSpan.FromSeconds(60);

        _jsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
            PropertyNameCaseInsensitive = true
        };
    }

    // ==================== HEALTH & STATUS ====================

    public async Task<AIServiceHealthDto> GetHealthAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/health");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<AIServiceHealthDto>(_jsonOptions)
                ?? new AIServiceHealthDto { Status = "error" };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get AI service health");
            return new AIServiceHealthDto { Status = "unreachable" };
        }
    }

    public async Task<AIModelInfoDto> GetModelInfoAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/model/info");
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<AIModelInfoDto>(_jsonOptions)
                ?? new AIModelInfoDto { Status = "error" };
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get AI model info");
            return new AIModelInfoDto { Status = "error" };
        }
    }

    public async Task<bool> LoadModelAsync()
    {
        try
        {
            var response = await _httpClient.PostAsync("/model/load", null);
            return response.IsSuccessStatusCode;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to load AI model");
            return false;
        }
    }

    // ==================== ETA PREDICTIONS ====================

    public async Task<AIETAPredictionDto?> PredictETAAsync(int vesselId, int? scheduleId = null)
    {
        try
        {
            var url = $"/predictions/eta/{vesselId}";
            if (scheduleId.HasValue)
            {
                url += $"?schedule_id={scheduleId}";
            }

            var response = await _httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<AIETAPredictionDto>(_jsonOptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to predict ETA for vessel {VesselId}", vesselId);
            return null;
        }
    }

    public async Task<List<AIETAPredictionDto>> PredictETABatchAsync(IEnumerable<int> vesselIds)
    {
        try
        {
            var ids = string.Join(",", vesselIds);
            var response = await _httpClient.GetAsync($"/predictions/eta/batch?vessel_ids={ids}");
            response.EnsureSuccessStatusCode();
            
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, List<AIETAPredictionDto>>>(_jsonOptions);
            return result?.GetValueOrDefault("predictions") ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to predict ETA batch");
            return [];
        }
    }

    public async Task<Dictionary<string, object>> GetClaudeETAPredictionAsync(int vesselId, bool includeRagContext = true)
    {
        try
        {
            var request = new { vessel_id = vesselId, include_rag_context = includeRagContext };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/agents/claude/eta", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>(_jsonOptions) ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get Claude ETA prediction for vessel {VesselId}", vesselId);
            return new Dictionary<string, object> { ["error"] = ex.Message };
        }
    }

    // ==================== BERTH SUGGESTIONS ====================

    public async Task<List<AIBerthSuggestionDto>> GetBerthSuggestionsAsync(int vesselId, DateTime? preferredEta = null, int topN = 5)
    {
        try
        {
            var url = $"/suggestions/berth/{vesselId}?top_n={topN}";
            if (preferredEta.HasValue)
            {
                url += $"&preferred_eta={preferredEta.Value:o}";
            }

            var response = await _httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();
            return await response.Content.ReadFromJsonAsync<List<AIBerthSuggestionDto>>(_jsonOptions) ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get berth suggestions for vessel {VesselId}", vesselId);
            return [];
        }
    }

    public async Task<Dictionary<string, object>> GetClaudeBerthOptimizationAsync(int vesselId, bool includeRagContext = true, int timeHorizonHours = 48)
    {
        try
        {
            var request = new { vessel_id = vesselId, include_rag_context = includeRagContext, time_horizon_hours = timeHorizonHours };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/agents/claude/berth", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>(_jsonOptions) ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get Claude berth optimization for vessel {VesselId}", vesselId);
            return new Dictionary<string, object> { ["error"] = ex.Message };
        }
    }

    // ==================== CHATBOT ====================

    public async Task<AIChatResponseDto?> ChatAsync(string message, string? sessionId = null)
    {
        try
        {
            var request = new { message, session_id = sessionId };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/chat", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<AIChatResponseDto>(_jsonOptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to send chat message");
            return null;
        }
    }

    public async Task<List<Dictionary<string, object>>> GetChatHistoryAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/chat/history");
            response.EnsureSuccessStatusCode();
            
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, List<Dictionary<string, object>>>>(_jsonOptions);
            return result?.GetValueOrDefault("history") ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get chat history");
            return [];
        }
    }

    public async Task ClearChatHistoryAsync()
    {
        try
        {
            await _httpClient.PostAsync("/chat/clear", null);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to clear chat history");
        }
    }

    // ==================== RAG KNOWLEDGE BASE ====================

    public async Task<AIExplanationResponseDto?> GenerateExplanationAsync(string query, string? contextCategory = null, string? additionalContext = null)
    {
        try
        {
            var request = new { query, context_category = contextCategory, additional_context = additionalContext };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/rag/explain", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<AIExplanationResponseDto>(_jsonOptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to generate explanation for query: {Query}", query);
            return null;
        }
    }

    public async Task<List<AISearchResultDto>> SearchKnowledgeBaseAsync(string query, int k = 5, string? category = null)
    {
        try
        {
            var url = $"/rag/search?query={Uri.EscapeDataString(query)}&k={k}";
            if (!string.IsNullOrEmpty(category))
            {
                url += $"&category={category}";
            }

            var response = await _httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();
            
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, List<AISearchResultDto>>>(_jsonOptions);
            return result?.GetValueOrDefault("results") ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to search knowledge base");
            return [];
        }
    }

    public async Task<List<AISearchResultDto>> HybridSearchAsync(string query, int topK = 5, string method = "hybrid")
    {
        try
        {
            var request = new { query, top_k = topK, method };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/rag/hybrid-search", content);
            response.EnsureSuccessStatusCode();
            
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>(_jsonOptions);
            
            if (result?.ContainsKey("results") == true && result["results"] is JsonElement element)
            {
                return JsonSerializer.Deserialize<List<AISearchResultDto>>(element.GetRawText(), _jsonOptions) ?? [];
            }
            return [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to perform hybrid search");
            return [];
        }
    }

    // ==================== CONFLICT DETECTION ====================

    public async Task<List<AIConflictDto>> DetectConflictsAsync(int timeWindowHours = 48)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/agents/conflicts?hours={timeWindowHours}");
            response.EnsureSuccessStatusCode();
            
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, object>>(_jsonOptions);
            
            if (result?.ContainsKey("conflicts") == true && result["conflicts"] is JsonElement element)
            {
                return JsonSerializer.Deserialize<List<AIConflictDto>>(element.GetRawText(), _jsonOptions) ?? [];
            }
            return [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to detect conflicts");
            return [];
        }
    }

    public async Task<Dictionary<string, object>> ResolveConflictAsync(int conflictId, string resolutionAction)
    {
        try
        {
            var request = new { conflict_id = conflictId, resolution_action = resolutionAction };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/agents/resolve-conflict", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>(_jsonOptions) ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to resolve conflict {ConflictId}", conflictId);
            return new Dictionary<string, object> { ["error"] = ex.Message };
        }
    }

    public async Task<Dictionary<string, object>> GetClaudeConflictResolutionAsync(string? timeStart = null, string? timeEnd = null, bool includeRagContext = true)
    {
        try
        {
            var request = new { time_start = timeStart, time_end = timeEnd, include_rag_context = includeRagContext };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/agents/claude/conflicts", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>(_jsonOptions) ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get Claude conflict resolution");
            return new Dictionary<string, object> { ["error"] = ex.Message };
        }
    }

    // ==================== MULTI-AGENT SYSTEM ====================

    public async Task<AIVesselArrivalProcessingDto?> ProcessVesselArrivalAsync(int vesselId)
    {
        try
        {
            var request = new { vessel_id = vesselId };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/agents/process-arrival", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<AIVesselArrivalProcessingDto>(_jsonOptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to process vessel arrival for vessel {VesselId}", vesselId);
            return null;
        }
    }

    public async Task<Dictionary<string, object>> OptimizeScheduleAsync(string algorithm = "greedy", int timeHorizonHours = 48)
    {
        try
        {
            var request = new { algorithm, time_horizon_hours = timeHorizonHours };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/agents/optimize-schedule", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>(_jsonOptions) ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to optimize schedule");
            return new Dictionary<string, object> { ["error"] = ex.Message };
        }
    }

    // ==================== WHAT-IF SIMULATION ====================

    public async Task<AIWhatIfResultDto?> RunWhatIfSimulationAsync(AIWhatIfRequestDto request)
    {
        try
        {
            var payload = new
            {
                scenario_type = request.ScenarioType,
                vessel_id = request.VesselId,
                berth_id = request.BerthId,
                delay_hours = request.DelayHours,
                duration_hours = request.DurationHours,
                additional_vessels = request.AdditionalVessels
            };
            var content = new StringContent(JsonSerializer.Serialize(payload, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/simulation/what-if", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<AIWhatIfResultDto>(_jsonOptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to run what-if simulation");
            return null;
        }
    }

    public async Task<AIWhatIfResultDto?> SimulateDelayImpactAsync(int vesselId, int delayHours = 4)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/simulation/delay-impact/{vesselId}?delay_hours={delayHours}");
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<AIWhatIfResultDto>(_jsonOptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to simulate delay impact for vessel {VesselId}", vesselId);
            return null;
        }
    }

    public async Task<AIWhatIfResultDto?> SimulateBerthClosureAsync(int berthId, int durationHours = 24)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/simulation/berth-closure/{berthId}?duration_hours={durationHours}");
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<AIWhatIfResultDto>(_jsonOptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to simulate berth closure for berth {BerthId}", berthId);
            return null;
        }
    }

    public async Task<AIWhatIfResultDto?> SimulateCapacitySurgeAsync(int additionalVessels = 5)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/simulation/capacity-surge?additional_vessels={additionalVessels}");
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<AIWhatIfResultDto>(_jsonOptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to simulate capacity surge");
            return null;
        }
    }

    // ==================== DASHBOARD & ANALYTICS ====================

    public async Task<AIDashboardOverviewDto?> GetDashboardOverviewAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/dashboard/overview");
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<AIDashboardOverviewDto>(_jsonOptions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get AI dashboard overview");
            return null;
        }
    }

    public async Task<Dictionary<string, object>> GetBerthTimelineAsync(int hours = 48)
    {
        try
        {
            var response = await _httpClient.GetAsync($"/dashboard/timeline?hours={hours}");
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>(_jsonOptions) ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get berth timeline");
            return new Dictionary<string, object> { ["error"] = ex.Message };
        }
    }

    // ==================== REAL-TIME ALERTS ====================

    public async Task<List<AIAlertDto>> GetActiveAlertsAsync()
    {
        try
        {
            var response = await _httpClient.GetAsync("/alerts/active");
            response.EnsureSuccessStatusCode();
            
            var result = await response.Content.ReadFromJsonAsync<Dictionary<string, List<AIAlertDto>>>(_jsonOptions);
            return result?.GetValueOrDefault("alerts") ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get active alerts");
            return [];
        }
    }

    // ==================== CONSTRAINT VALIDATION ====================

    public async Task<Dictionary<string, object>> ValidateConstraintsAsync(int vesselId, int berthId, DateTime? eta = null)
    {
        try
        {
            var request = new { vessel_id = vesselId, berth_id = berthId, eta = eta?.ToString("o") };
            var content = new StringContent(JsonSerializer.Serialize(request, _jsonOptions), Encoding.UTF8, "application/json");
            
            var response = await _httpClient.PostAsync("/validate/constraints", content);
            response.EnsureSuccessStatusCode();
            
            return await response.Content.ReadFromJsonAsync<Dictionary<string, object>>(_jsonOptions) ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to validate constraints for vessel {VesselId} at berth {BerthId}", vesselId, berthId);
            return new Dictionary<string, object> { ["error"] = ex.Message };
        }
    }
}
