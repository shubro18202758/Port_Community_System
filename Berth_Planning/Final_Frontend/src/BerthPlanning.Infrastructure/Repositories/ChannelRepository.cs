using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class ChannelRepository : IChannelRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public ChannelRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<Channel>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT c.*, p.PortName, p.PortCode
            FROM CHANNELS c
            LEFT JOIN PORTS p ON c.PortId = p.PortId
            ORDER BY c.ChannelName";
        return await connection.QueryAsync<Channel>(sql);
    }

    public async Task<Channel?> GetByIdAsync(int channelId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT c.*, p.PortName, p.PortCode
            FROM CHANNELS c
            LEFT JOIN PORTS p ON c.PortId = p.PortId
            WHERE c.ChannelId = @ChannelId";
        return await connection.QueryFirstOrDefaultAsync<Channel>(sql, new { ChannelId = channelId });
    }

    public async Task<IEnumerable<Channel>> GetByPortIdAsync(int portId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT c.*, p.PortName, p.PortCode
            FROM CHANNELS c
            LEFT JOIN PORTS p ON c.PortId = p.PortId
            WHERE c.PortId = @PortId
            ORDER BY c.ChannelName";
        return await connection.QueryAsync<Channel>(sql, new { PortId = portId });
    }

    public async Task<int> CreateAsync(Channel channel)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO CHANNELS (PortId, ChannelName, ChannelLength, ChannelWidth, ChannelDepth,
                ChannelDepthAtChartDatum, OneWayOrTwoWay, MaxVesselLOA, MaxVesselBeam, MaxVesselDraft,
                TrafficSeparationScheme, SpeedLimit, TidalWindowRequired, PilotageCompulsory,
                TugEscortRequired, DayNightRestrictions, VisibilityMinimum, WindSpeedLimit,
                CurrentSpeedLimit, ChannelSegments, AnchorageAreaId)
            VALUES (@PortId, @ChannelName, @ChannelLength, @ChannelWidth, @ChannelDepth,
                @ChannelDepthAtChartDatum, @OneWayOrTwoWay, @MaxVesselLOA, @MaxVesselBeam, @MaxVesselDraft,
                @TrafficSeparationScheme, @SpeedLimit, @TidalWindowRequired, @PilotageCompulsory,
                @TugEscortRequired, @DayNightRestrictions, @VisibilityMinimum, @WindSpeedLimit,
                @CurrentSpeedLimit, @ChannelSegments, @AnchorageAreaId);
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.QuerySingleAsync<int>(sql, channel);
    }

    public async Task<bool> UpdateAsync(Channel channel)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE CHANNELS SET
                PortId = @PortId, ChannelName = @ChannelName, ChannelLength = @ChannelLength,
                ChannelWidth = @ChannelWidth, ChannelDepth = @ChannelDepth,
                ChannelDepthAtChartDatum = @ChannelDepthAtChartDatum, OneWayOrTwoWay = @OneWayOrTwoWay,
                MaxVesselLOA = @MaxVesselLOA, MaxVesselBeam = @MaxVesselBeam, MaxVesselDraft = @MaxVesselDraft,
                TrafficSeparationScheme = @TrafficSeparationScheme, SpeedLimit = @SpeedLimit,
                TidalWindowRequired = @TidalWindowRequired, PilotageCompulsory = @PilotageCompulsory,
                TugEscortRequired = @TugEscortRequired, DayNightRestrictions = @DayNightRestrictions,
                VisibilityMinimum = @VisibilityMinimum, WindSpeedLimit = @WindSpeedLimit,
                CurrentSpeedLimit = @CurrentSpeedLimit, ChannelSegments = @ChannelSegments,
                AnchorageAreaId = @AnchorageAreaId, IsActive = @IsActive
            WHERE ChannelId = @ChannelId";
        int rowsAffected = await connection.ExecuteAsync(sql, channel);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(int channelId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM CHANNELS WHERE ChannelId = @ChannelId";
        int rowsAffected = await connection.ExecuteAsync(sql, new { ChannelId = channelId });
        return rowsAffected > 0;
    }
}
