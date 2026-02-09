using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class BerthRepository : IBerthRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public BerthRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<Berth>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT b.BerthId, b.TerminalId, b.BerthName, b.BerthCode, b.Length, b.Depth, b.MaxDraft, b.BerthType,
                   b.NumberOfCranes, b.BollardCount, b.IsActive, b.Latitude, b.Longitude, b.CreatedAt, b.UpdatedAt,
                   t.TerminalName, t.TerminalCode, p.PortName, p.PortCode
            FROM BERTHS b
            LEFT JOIN TERMINALS t ON b.TerminalId = t.TerminalId
            LEFT JOIN PORTS p ON t.PortId = p.PortId
            ORDER BY p.PortName, t.TerminalName, b.BerthCode";
        return await connection.QueryAsync<Berth>(sql);
    }

    public async Task<IEnumerable<Berth>> GetActiveAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT b.BerthId, b.TerminalId, b.BerthName, b.BerthCode, b.Length, b.Depth, b.MaxDraft, b.BerthType,
                   b.NumberOfCranes, b.BollardCount, b.IsActive, b.Latitude, b.Longitude, b.CreatedAt, b.UpdatedAt,
                   t.TerminalName, t.TerminalCode, p.PortName, p.PortCode
            FROM BERTHS b
            LEFT JOIN TERMINALS t ON b.TerminalId = t.TerminalId
            LEFT JOIN PORTS p ON t.PortId = p.PortId
            WHERE b.IsActive = 1
            ORDER BY p.PortName, t.TerminalName, b.BerthCode";
        return await connection.QueryAsync<Berth>(sql);
    }

    public async Task<Berth?> GetByIdAsync(int berthId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT b.BerthId, b.TerminalId, b.BerthName, b.BerthCode, b.Length, b.Depth, b.MaxDraft, b.BerthType,
                   b.NumberOfCranes, b.BollardCount, b.IsActive, b.Latitude, b.Longitude, b.CreatedAt, b.UpdatedAt,
                   t.TerminalName, t.TerminalCode, p.PortName, p.PortCode
            FROM BERTHS b
            LEFT JOIN TERMINALS t ON b.TerminalId = t.TerminalId
            LEFT JOIN PORTS p ON t.PortId = p.PortId
            WHERE b.BerthId = @BerthId";
        return await connection.QueryFirstOrDefaultAsync<Berth>(sql, new { BerthId = berthId });
    }

    public async Task<Berth?> GetByCodeAsync(string berthCode)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT b.BerthId, b.TerminalId, b.BerthName, b.BerthCode, b.Length, b.Depth, b.MaxDraft, b.BerthType,
                   b.NumberOfCranes, b.BollardCount, b.IsActive, b.Latitude, b.Longitude, b.CreatedAt, b.UpdatedAt,
                   t.TerminalName, t.TerminalCode, p.PortName, p.PortCode
            FROM BERTHS b
            LEFT JOIN TERMINALS t ON b.TerminalId = t.TerminalId
            LEFT JOIN PORTS p ON t.PortId = p.PortId
            WHERE b.BerthCode = @BerthCode";
        return await connection.QueryFirstOrDefaultAsync<Berth>(sql, new { BerthCode = berthCode });
    }

    public async Task<IEnumerable<Berth>> GetByTerminalIdAsync(int terminalId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT b.BerthId, b.TerminalId, b.BerthName, b.BerthCode, b.Length, b.Depth, b.MaxDraft, b.BerthType,
                   b.NumberOfCranes, b.BollardCount, b.IsActive, b.Latitude, b.Longitude, b.CreatedAt, b.UpdatedAt,
                   t.TerminalName, t.TerminalCode, p.PortName, p.PortCode
            FROM BERTHS b
            LEFT JOIN TERMINALS t ON b.TerminalId = t.TerminalId
            LEFT JOIN PORTS p ON t.PortId = p.PortId
            WHERE b.TerminalId = @TerminalId
            ORDER BY b.BerthCode";
        return await connection.QueryAsync<Berth>(sql, new { TerminalId = terminalId });
    }

    public async Task<IEnumerable<Berth>> GetCompatibleBerthsAsync(decimal vesselLOA, decimal vesselDraft)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        // Call stored procedure sp_FindCompatibleBerths
        return await connection.QueryAsync<Berth>(
            "sp_FindCompatibleBerths",
            new { VesselLOA = vesselLOA, VesselDraft = vesselDraft },
            commandType: CommandType.StoredProcedure);
    }

    public async Task<bool> CheckAvailabilityAsync(int berthId, DateTime startTime, DateTime endTime)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        // Call stored procedure sp_CheckBerthAvailability
        // The SP returns multiple result sets, we need the last one with BerthAvailability
        using SqlMapper.GridReader multi = await connection.QueryMultipleAsync(
            "sp_CheckBerthAvailability",
            new { BerthId = berthId, StartTime = startTime, EndTime = endTime },
            commandType: CommandType.StoredProcedure);

        // Skip conflict result sets and get the summary
        _ = await multi.ReadAsync(); // Skip schedule conflicts
        _ = await multi.ReadAsync(); // Skip maintenance conflicts
        dynamic? summary = await multi.ReadFirstOrDefaultAsync<dynamic>(); // Get availability summary

        // SP returns BerthAvailability = 'AVAILABLE' or 'UNAVAILABLE'
        return summary?.BerthAvailability == "AVAILABLE";
    }

    public async Task<int> CreateAsync(Berth berth)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO BERTHS (TerminalId, BerthName, BerthCode, Length, Depth, MaxDraft, BerthType,
                               NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
            VALUES (@TerminalId, @BerthName, @BerthCode, @Length, @Depth, @MaxDraft, @BerthType,
                    @NumberOfCranes, @BollardCount, @IsActive, @Latitude, @Longitude);
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.QuerySingleAsync<int>(sql, berth);
    }

    public async Task<bool> UpdateAsync(Berth berth)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE BERTHS SET
                TerminalId = @TerminalId,
                BerthName = @BerthName,
                BerthCode = @BerthCode,
                Length = @Length,
                Depth = @Depth,
                MaxDraft = @MaxDraft,
                BerthType = @BerthType,
                NumberOfCranes = @NumberOfCranes,
                BollardCount = @BollardCount,
                IsActive = @IsActive,
                Latitude = @Latitude,
                Longitude = @Longitude,
                UpdatedAt = GETUTCDATE()
            WHERE BerthId = @BerthId";
        int rowsAffected = await connection.ExecuteAsync(sql, berth);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(int berthId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM BERTHS WHERE BerthId = @BerthId";
        int rowsAffected = await connection.ExecuteAsync(sql, new { BerthId = berthId });
        return rowsAffected > 0;
    }
}
