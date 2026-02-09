using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class SuggestionsController : ControllerBase
{
    private readonly ISuggestionService _suggestionService;
    private readonly ILogger<SuggestionsController> _logger;

    public SuggestionsController(ISuggestionService suggestionService, ILogger<SuggestionsController> logger)
    {
        _suggestionService = suggestionService;
        _logger = logger;
    }

    [HttpGet("berth/{vesselId}")]
    public async Task<ActionResult<SuggestionResponseDto>> GetBerthSuggestions(
        int vesselId,
        [FromQuery] DateTime? preferredETA = null)
    {
        try
        {
            _logger.LogInformation("Getting berth suggestions for vessel {VesselId}", vesselId);

            SuggestionResponseDto suggestions = await _suggestionService.GetBerthSuggestionsAsync(vesselId, preferredETA);

            return suggestions.Suggestions.Count == 0
                ? (ActionResult<SuggestionResponseDto>)Ok(new SuggestionResponseDto
                {
                    VesselId = vesselId,
                    RequestedAt = DateTime.UtcNow,
                    Message = "No compatible berths found. Please check vessel dimensions or try a different time window."
                })
                : (ActionResult<SuggestionResponseDto>)Ok(suggestions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error getting berth suggestions for vessel {VesselId}", vesselId);
            return StatusCode(500, "Internal server error");
        }
    }
}
