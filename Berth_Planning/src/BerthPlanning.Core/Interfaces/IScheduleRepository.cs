using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IScheduleRepository
{
    Task<IEnumerable<VesselSchedule>> GetAllAsync();
    Task<IEnumerable<VesselSchedule>> GetActiveAsync();
    Task<IEnumerable<VesselSchedule>> GetByStatusAsync(string status);
    Task<IEnumerable<VesselSchedule>> GetByBerthAsync(int berthId);
    Task<IEnumerable<VesselSchedule>> GetByDateRangeAsync(DateTime startDate, DateTime endDate);
    Task<VesselSchedule?> GetByIdAsync(int scheduleId);
    Task<VesselSchedule?> GetByVesselIdAsync(int vesselId);

    // SP calls
    Task<AllocationResultDto> AllocateVesselToBerthAsync(int vesselId, int berthId, DateTime eta, DateTime etd, int? dwellTime);
    Task<bool> UpdateVesselETAAsync(int scheduleId, DateTime newETA, DateTime? newPredictedETA);
    Task<bool> RecordVesselArrivalAsync(int scheduleId, DateTime ata);
    Task<bool> RecordVesselBerthingAsync(int scheduleId, DateTime atb);
    Task<bool> RecordVesselDepartureAsync(int scheduleId, DateTime atd);

    Task<int> CreateAsync(VesselSchedule schedule);
    Task<bool> UpdateAsync(VesselSchedule schedule);
    Task<bool> DeleteAsync(int scheduleId);
}
