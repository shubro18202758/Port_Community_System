using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Services.Contracts;

public interface IScoringEngine
{
    Task<decimal> CalculateScoreAsync(Vessel vessel, Berth berth, DateTime proposedETA);
    decimal CalculatePhysicalFitScore(Vessel vessel, Berth berth);
    decimal CalculateTypeMatchScore(Vessel vessel, Berth berth);
    Task<decimal> CalculateWaitingTimeScoreAsync(int berthId, DateTime vesselETA, DateTime proposedETA);
    decimal CalculateCraneAvailabilityScore(Vessel vessel, Berth berth);
    Task<decimal> CalculateHistoricalPerformanceScoreAsync(int vesselId, int berthId);
    Task<decimal> CalculateTidalCompatibilityScoreAsync(decimal vesselDraft, DateTime proposedETA);
}
