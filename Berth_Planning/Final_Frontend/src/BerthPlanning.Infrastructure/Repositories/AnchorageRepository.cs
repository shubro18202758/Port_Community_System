using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class AnchorageRepository : IAnchorageRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public AnchorageRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<Anchorage>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT a.*, p.PortName, p.PortCode
            FROM ANCHORAGES a
            LEFT JOIN PORTS p ON a.PortId = p.PortId
            ORDER BY a.AnchorageName";
        return await connection.QueryAsync<Anchorage>(sql);
    }

    public async Task<Anchorage?> GetByIdAsync(int anchorageId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT a.*, p.PortName, p.PortCode
            FROM ANCHORAGES a
            LEFT JOIN PORTS p ON a.PortId = p.PortId
            WHERE a.AnchorageId = @AnchorageId";
        return await connection.QueryFirstOrDefaultAsync<Anchorage>(sql, new { AnchorageId = anchorageId });
    }

    public async Task<IEnumerable<Anchorage>> GetByPortIdAsync(int portId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT a.*, p.PortName, p.PortCode
            FROM ANCHORAGES a
            LEFT JOIN PORTS p ON a.PortId = p.PortId
            WHERE a.PortId = @PortId
            ORDER BY a.AnchorageName";
        return await connection.QueryAsync<Anchorage>(sql, new { PortId = portId });
    }

    public async Task<IEnumerable<Anchorage>> GetByTypeAsync(string anchorageType)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT a.*, p.PortName, p.PortCode
            FROM ANCHORAGES a
            LEFT JOIN PORTS p ON a.PortId = p.PortId
            WHERE a.AnchorageType = @AnchorageType
            ORDER BY a.AnchorageName";
        return await connection.QueryAsync<Anchorage>(sql, new { AnchorageType = anchorageType });
    }

    public async Task<int> CreateAsync(Anchorage anchorage)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO ANCHORAGES (PortId, AnchorageName, AnchorageType, Latitude, Longitude,
                Depth, MaxVessels, CurrentOccupancy, MaxVesselLOA, MaxVesselDraft,
                AverageWaitingTime, STSCargoOpsPermitted, QuarantineAnchorage)
            VALUES (@PortId, @AnchorageName, @AnchorageType, @Latitude, @Longitude,
                @Depth, @MaxVessels, @CurrentOccupancy, @MaxVesselLOA, @MaxVesselDraft,
                @AverageWaitingTime, @STSCargoOpsPermitted, @QuarantineAnchorage);
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.QuerySingleAsync<int>(sql, anchorage);
    }

    public async Task<bool> UpdateAsync(Anchorage anchorage)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE ANCHORAGES SET
                PortId = @PortId, AnchorageName = @AnchorageName, AnchorageType = @AnchorageType,
                Latitude = @Latitude, Longitude = @Longitude, Depth = @Depth,
                MaxVessels = @MaxVessels, CurrentOccupancy = @CurrentOccupancy,
                MaxVesselLOA = @MaxVesselLOA, MaxVesselDraft = @MaxVesselDraft,
                AverageWaitingTime = @AverageWaitingTime, STSCargoOpsPermitted = @STSCargoOpsPermitted,
                QuarantineAnchorage = @QuarantineAnchorage, IsActive = @IsActive
            WHERE AnchorageId = @AnchorageId";
        int rowsAffected = await connection.ExecuteAsync(sql, anchorage);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(int anchorageId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM ANCHORAGES WHERE AnchorageId = @AnchorageId";
        int rowsAffected = await connection.ExecuteAsync(sql, new { AnchorageId = anchorageId });
        return rowsAffected > 0;
    }
}
