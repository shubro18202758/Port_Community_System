using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Services.Contracts;

public interface IConstraintValidator
{
    Task<ConstraintCheckDto> ValidateAssignmentAsync(Vessel vessel, Berth berth, DateTime proposedETA, DateTime proposedETD);
    bool ValidatePhysicalFit(Vessel vessel, Berth berth);
    Task<bool> ValidateNoOverlapAsync(int berthId, DateTime eta, DateTime etd, int? excludeScheduleId = null);
    Task<bool> ValidateMaintenanceWindowAsync(int berthId, DateTime eta, DateTime etd);
    Task<bool> ValidateTidalWindowAsync(decimal vesselDraft, DateTime eta);
    Task<bool> ValidateWeatherSafetyAsync(DateTime eta);
    Task<bool> ValidateResourceAvailabilityAsync(int berthId, DateTime eta, DateTime etd);
}
