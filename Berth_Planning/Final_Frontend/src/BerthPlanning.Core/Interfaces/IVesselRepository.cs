using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IVesselRepository
{
    Task<IEnumerable<Vessel>> GetAllAsync();
    Task<Vessel?> GetByIdAsync(int vesselId);
    Task<Vessel?> GetByIMOAsync(string imo);
    Task<IEnumerable<Vessel>> GetByTypeAsync(string vesselType);
    Task<int> CreateAsync(Vessel vessel);
    Task<bool> UpdateAsync(Vessel vessel);
    Task<bool> DeleteAsync(int vesselId);
}
