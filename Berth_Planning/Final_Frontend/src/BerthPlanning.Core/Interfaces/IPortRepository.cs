using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IPortRepository
{
    Task<IEnumerable<Port>> GetAllAsync();
    Task<Port?> GetByIdAsync(int portId);
    Task<Port?> GetByCodeAsync(string portCode);
    Task<int> CreateAsync(Port port);
    Task<bool> UpdateAsync(Port port);
    Task<bool> DeleteAsync(int portId);
}
