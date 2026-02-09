using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class TerminalRepository : ITerminalRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public TerminalRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<Terminal>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        // Simple query without multi-mapping to ensure PortId is correctly populated
        const string sql = @"
            SELECT t.TerminalId, t.PortId, t.TerminalName, t.TerminalCode, t.TerminalType,
                   t.OperatorName, t.Latitude, t.Longitude, t.IsActive, t.CreatedAt, t.UpdatedAt,
                   p.PortName, p.PortCode
            FROM TERMINALS t
            LEFT JOIN PORTS p ON t.PortId = p.PortId
            ORDER BY p.PortName, t.TerminalName";

        return await connection.QueryAsync<Terminal>(sql);
    }

    public async Task<IEnumerable<Terminal>> GetByPortIdAsync(int portId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT t.TerminalId, t.PortId, t.TerminalName, t.TerminalCode, t.TerminalType,
                   t.OperatorName, t.Latitude, t.Longitude, t.IsActive, t.CreatedAt, t.UpdatedAt
            FROM TERMINALS t
            WHERE t.PortId = @PortId
            ORDER BY t.TerminalName";
        return await connection.QueryAsync<Terminal>(sql, new { PortId = portId });
    }

    public async Task<Terminal?> GetByIdAsync(int terminalId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT t.TerminalId, t.PortId, t.TerminalName, t.TerminalCode, t.TerminalType,
                   t.OperatorName, t.Latitude, t.Longitude, t.IsActive, t.CreatedAt, t.UpdatedAt
            FROM TERMINALS t
            WHERE t.TerminalId = @TerminalId";
        return await connection.QueryFirstOrDefaultAsync<Terminal>(sql, new { TerminalId = terminalId });
    }

    public async Task<Terminal?> GetByCodeAsync(string terminalCode)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT t.TerminalId, t.PortId, t.TerminalName, t.TerminalCode, t.TerminalType,
                   t.OperatorName, t.Latitude, t.Longitude, t.IsActive, t.CreatedAt, t.UpdatedAt
            FROM TERMINALS t
            WHERE t.TerminalCode = @TerminalCode";
        return await connection.QueryFirstOrDefaultAsync<Terminal>(sql, new { TerminalCode = terminalCode });
    }

    public async Task<int> CreateAsync(Terminal terminal)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType,
                                   OperatorName, Latitude, Longitude, IsActive)
            VALUES (@PortId, @TerminalName, @TerminalCode, @TerminalType,
                    @OperatorName, @Latitude, @Longitude, @IsActive);
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.QuerySingleAsync<int>(sql, terminal);
    }

    public async Task<bool> UpdateAsync(Terminal terminal)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE TERMINALS SET
                PortId = @PortId,
                TerminalName = @TerminalName,
                TerminalCode = @TerminalCode,
                TerminalType = @TerminalType,
                OperatorName = @OperatorName,
                Latitude = @Latitude,
                Longitude = @Longitude,
                IsActive = @IsActive,
                UpdatedAt = GETUTCDATE()
            WHERE TerminalId = @TerminalId";
        int rowsAffected = await connection.ExecuteAsync(sql, terminal);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(int terminalId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM TERMINALS WHERE TerminalId = @TerminalId";
        int rowsAffected = await connection.ExecuteAsync(sql, new { TerminalId = terminalId });
        return rowsAffected > 0;
    }
}
