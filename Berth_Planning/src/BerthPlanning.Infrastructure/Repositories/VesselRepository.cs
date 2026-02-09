using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class VesselRepository : IVesselRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public VesselRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<Vessel>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT VesselId, VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft,
                   GrossTonnage, CargoType, CargoVolume, Priority, CreatedAt, UpdatedAt
            FROM VESSELS
            ORDER BY VesselName";
        return await connection.QueryAsync<Vessel>(sql);
    }

    public async Task<Vessel?> GetByIdAsync(int vesselId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT VesselId, VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft,
                   GrossTonnage, CargoType, CargoVolume, Priority, CreatedAt, UpdatedAt
            FROM VESSELS
            WHERE VesselId = @VesselId";
        return await connection.QueryFirstOrDefaultAsync<Vessel>(sql, new { VesselId = vesselId });
    }

    public async Task<Vessel?> GetByIMOAsync(string imo)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT VesselId, VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft,
                   GrossTonnage, CargoType, CargoVolume, Priority, CreatedAt, UpdatedAt
            FROM VESSELS
            WHERE IMO = @IMO";
        return await connection.QueryFirstOrDefaultAsync<Vessel>(sql, new { IMO = imo });
    }

    public async Task<IEnumerable<Vessel>> GetByTypeAsync(string vesselType)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT VesselId, VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft,
                   GrossTonnage, CargoType, CargoVolume, Priority, CreatedAt, UpdatedAt
            FROM VESSELS
            WHERE VesselType = @VesselType
            ORDER BY VesselName";
        return await connection.QueryAsync<Vessel>(sql, new { VesselType = vesselType });
    }

    public async Task<int> CreateAsync(Vessel vessel)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO VESSELS (VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft,
                                 GrossTonnage, CargoType, CargoVolume, Priority)
            VALUES (@VesselName, @IMO, @MMSI, @VesselType, @LOA, @Beam, @Draft,
                    @GrossTonnage, @CargoType, @CargoVolume, @Priority);
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.QuerySingleAsync<int>(sql, vessel);
    }

    public async Task<bool> UpdateAsync(Vessel vessel)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE VESSELS SET
                VesselName = @VesselName,
                IMO = @IMO,
                MMSI = @MMSI,
                VesselType = @VesselType,
                LOA = @LOA,
                Beam = @Beam,
                Draft = @Draft,
                GrossTonnage = @GrossTonnage,
                CargoType = @CargoType,
                CargoVolume = @CargoVolume,
                Priority = @Priority,
                UpdatedAt = GETUTCDATE()
            WHERE VesselId = @VesselId";
        int rowsAffected = await connection.ExecuteAsync(sql, vessel);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(int vesselId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM VESSELS WHERE VesselId = @VesselId";
        int rowsAffected = await connection.ExecuteAsync(sql, new { VesselId = vesselId });
        return rowsAffected > 0;
    }
}
