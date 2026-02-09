using BerthPlanning.Core.DTOs;

namespace BerthPlanning.Core.Services.Contracts;

public interface IPredictionService
{
    // Predictive ETA Calculation
    Task<ETAPredictionDto> PredictETAAsync(int vesselId, int? scheduleId = null);
    Task<IEnumerable<ETAPredictionDto>> PredictAllActiveETAsAsync();
    Task<decimal> CalculateDistanceToPortAsync(int vesselId, decimal portLat, decimal portLon);

    // Arrival Deviation Detection
    Task<IEnumerable<DeviationAlertDto>> DetectDeviationsAsync();
    Task<DeviationAlertDto?> CheckScheduleDeviationAsync(int scheduleId);
    Task<IEnumerable<ImpactedScheduleDto>> AnalyzeDeviationImpactAsync(int scheduleId, int deviationMinutes);
}
