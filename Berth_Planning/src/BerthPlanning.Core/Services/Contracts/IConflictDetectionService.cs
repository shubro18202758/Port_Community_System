using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Services.Contracts;

public interface IConflictDetectionService
{
    Task<List<Conflict>> DetectAllConflictsAsync();
    Task<List<Conflict>> DetectBerthOverlapsAsync();
    Task<List<Conflict>> DetectResourceConflictsAsync();
    Task<List<Conflict>> DetectTidalConflictsAsync();
    Task<List<Conflict>> DetectPriorityViolationsAsync();
    Task<int> SaveConflictAsync(Conflict conflict);
    Task<bool> ResolveConflictAsync(int conflictId, string resolution);
}
