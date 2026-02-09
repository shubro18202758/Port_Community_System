using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface ITerminalRepository
{
    Task<IEnumerable<Terminal>> GetAllAsync();
    Task<IEnumerable<Terminal>> GetByPortIdAsync(int portId);
    Task<Terminal?> GetByIdAsync(int terminalId);
    Task<Terminal?> GetByCodeAsync(string terminalCode);
    Task<int> CreateAsync(Terminal terminal);
    Task<bool> UpdateAsync(Terminal terminal);
    Task<bool> DeleteAsync(int terminalId);
}
