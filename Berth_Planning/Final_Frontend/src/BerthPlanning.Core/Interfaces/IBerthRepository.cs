using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IBerthRepository
{
    Task<IEnumerable<Berth>> GetAllAsync();
    Task<IEnumerable<Berth>> GetActiveAsync();
    Task<Berth?> GetByIdAsync(int berthId);
    Task<Berth?> GetByCodeAsync(string berthCode);
    Task<IEnumerable<Berth>> GetByTerminalIdAsync(int terminalId);
    Task<IEnumerable<Berth>> GetCompatibleBerthsAsync(decimal vesselLOA, decimal vesselDraft);
    Task<int> CreateAsync(Berth berth);
    Task<bool> UpdateAsync(Berth berth);
    Task<bool> DeleteAsync(int berthId);
    Task<bool> CheckAvailabilityAsync(int berthId, DateTime startTime, DateTime endTime);
}
