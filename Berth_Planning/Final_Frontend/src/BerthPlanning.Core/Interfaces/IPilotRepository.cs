using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IPilotRepository
{
    Task<IEnumerable<Pilot>> GetAllAsync();
    Task<Pilot?> GetByIdAsync(int pilotId);
    Task<IEnumerable<Pilot>> GetByPortCodeAsync(string portCode);
    Task<IEnumerable<Pilot>> GetByTypeAsync(string pilotType);
    Task<IEnumerable<Pilot>> GetByStatusAsync(string status);
    Task<int> CreateAsync(Pilot pilot);
    Task<bool> UpdateAsync(Pilot pilot);
    Task<bool> DeleteAsync(int pilotId);
}
