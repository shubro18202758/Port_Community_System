using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IAnchorageRepository
{
    Task<IEnumerable<Anchorage>> GetAllAsync();
    Task<Anchorage?> GetByIdAsync(int anchorageId);
    Task<IEnumerable<Anchorage>> GetByPortIdAsync(int portId);
    Task<IEnumerable<Anchorage>> GetByTypeAsync(string anchorageType);
    Task<int> CreateAsync(Anchorage anchorage);
    Task<bool> UpdateAsync(Anchorage anchorage);
    Task<bool> DeleteAsync(int anchorageId);
}
