using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IResourceRepository
{
    Task<IEnumerable<Resource>> GetAllAsync();
    Task<Resource?> GetByIdAsync(int resourceId);
    Task<IEnumerable<Resource>> GetByTypeAsync(string resourceType);
    Task<int> CreateAsync(Resource resource);
    Task<bool> UpdateAsync(Resource resource);
    Task<bool> DeleteAsync(int resourceId);
    Task<IEnumerable<ResourceAllocation>> GetAllocationsAsync(int resourceId);
}
