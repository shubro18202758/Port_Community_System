using BerthPlanning.Core.Models;

namespace BerthPlanning.Core.Interfaces;

public interface IChannelRepository
{
    Task<IEnumerable<Channel>> GetAllAsync();
    Task<Channel?> GetByIdAsync(int channelId);
    Task<IEnumerable<Channel>> GetByPortIdAsync(int portId);
    Task<int> CreateAsync(Channel channel);
    Task<bool> UpdateAsync(Channel channel);
    Task<bool> DeleteAsync(int channelId);
}
