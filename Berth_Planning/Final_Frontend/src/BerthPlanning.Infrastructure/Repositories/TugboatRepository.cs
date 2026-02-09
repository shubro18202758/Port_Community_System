using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class TugboatRepository : ITugboatRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public TugboatRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<Tugboat>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT * FROM TUGBOATS
            ORDER BY TugName";
        return await connection.QueryAsync<Tugboat>(sql);
    }

    public async Task<Tugboat?> GetByIdAsync(int tugId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "SELECT * FROM TUGBOATS WHERE TugId = @TugId";
        return await connection.QueryFirstOrDefaultAsync<Tugboat>(sql, new { TugId = tugId });
    }

    public async Task<IEnumerable<Tugboat>> GetByPortCodeAsync(string portCode)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT * FROM TUGBOATS
            WHERE PortCode = @PortCode
            ORDER BY TugName";
        return await connection.QueryAsync<Tugboat>(sql, new { PortCode = portCode });
    }

    public async Task<IEnumerable<Tugboat>> GetByTypeAsync(string tugType)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT * FROM TUGBOATS
            WHERE TugType = @TugType
            ORDER BY TugName";
        return await connection.QueryAsync<Tugboat>(sql, new { TugType = tugType });
    }

    public async Task<IEnumerable<Tugboat>> GetByStatusAsync(string status)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT * FROM TUGBOATS
            WHERE Status = @Status
            ORDER BY TugName";
        return await connection.QueryAsync<Tugboat>(sql, new { Status = status });
    }

    public async Task<int> CreateAsync(Tugboat tugboat)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO TUGBOATS (PortCode, TugName, TugCode, IMONumber, MMSI, CallSign,
                FlagState, PortOfRegistry, TugType, TugTypeFullName, TugClass,
                Operator, BollardPull, Length, Beam, Draft,
                EnginePower, MaxSpeed, YearBuilt, FiFiClass, WinchCapacity, CrewSize, Status)
            VALUES (@PortCode, @TugName, @TugCode, @IMONumber, @MMSI, @CallSign,
                @FlagState, @PortOfRegistry, @TugType, @TugTypeFullName, @TugClass,
                @Operator, @BollardPull, @Length, @Beam, @Draft,
                @EnginePower, @MaxSpeed, @YearBuilt, @FiFiClass, @WinchCapacity, @CrewSize, @Status);
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.QuerySingleAsync<int>(sql, tugboat);
    }

    public async Task<bool> UpdateAsync(Tugboat tugboat)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE TUGBOATS SET
                PortCode = @PortCode, TugName = @TugName, TugCode = @TugCode,
                IMONumber = @IMONumber, MMSI = @MMSI, CallSign = @CallSign,
                FlagState = @FlagState, PortOfRegistry = @PortOfRegistry,
                TugType = @TugType, TugTypeFullName = @TugTypeFullName, TugClass = @TugClass,
                Operator = @Operator, BollardPull = @BollardPull, Length = @Length,
                Beam = @Beam, Draft = @Draft, EnginePower = @EnginePower,
                MaxSpeed = @MaxSpeed, YearBuilt = @YearBuilt, FiFiClass = @FiFiClass,
                WinchCapacity = @WinchCapacity, CrewSize = @CrewSize, Status = @Status
            WHERE TugId = @TugId";
        int rowsAffected = await connection.ExecuteAsync(sql, tugboat);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(int tugId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM TUGBOATS WHERE TugId = @TugId";
        int rowsAffected = await connection.ExecuteAsync(sql, new { TugId = tugId });
        return rowsAffected > 0;
    }
}
