using BerthPlanning.Core.DTOs;

namespace BerthPlanning.Core.Services.Contracts;

public interface ISuggestionService
{
    Task<SuggestionResponseDto> GetBerthSuggestionsAsync(int vesselId, DateTime? preferredETA = null);
    Task<ConflictResolutionDto> GetConflictResolutionSuggestionsAsync(int conflictId);
    Task<List<string>> GenerateExplanationAsync(int vesselId, int berthId, decimal score);
}
