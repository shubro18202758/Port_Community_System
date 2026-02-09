using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface ITugboatRepository
{
    Task<IEnumerable<Tugboat>> GetAllAsync();
    Task<Tugboat?> GetByIdAsync(int tugId);
    Task<IEnumerable<Tugboat>> GetByPortCodeAsync(string portCode);
    Task<IEnumerable<Tugboat>> GetByTypeAsync(string tugType);
    Task<IEnumerable<Tugboat>> GetByStatusAsync(string status);
    Task<int> CreateAsync(Tugboat tugboat);
    Task<bool> UpdateAsync(Tugboat tugboat);
    Task<bool> DeleteAsync(int tugId);
}
