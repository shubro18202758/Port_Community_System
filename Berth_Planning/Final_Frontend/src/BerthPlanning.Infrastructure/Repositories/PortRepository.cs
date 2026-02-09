using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class PortRepository : IPortRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public PortRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<Port>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT PortId, PortName, PortCode, Country, City, TimeZone,
                   Latitude, Longitude, ContactEmail, ContactPhone, IsActive, CreatedAt, UpdatedAt
            FROM PORTS
            ORDER BY PortName";
        return await connection.QueryAsync<Port>(sql);
    }

    public async Task<Port?> GetByIdAsync(int portId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT PortId, PortName, PortCode, Country, City, TimeZone,
                   Latitude, Longitude, ContactEmail, ContactPhone, IsActive, CreatedAt, UpdatedAt
            FROM PORTS
            WHERE PortId = @PortId";
        return await connection.QueryFirstOrDefaultAsync<Port>(sql, new { PortId = portId });
    }

    public async Task<Port?> GetByCodeAsync(string portCode)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT PortId, PortName, PortCode, Country, City, TimeZone,
                   Latitude, Longitude, ContactEmail, ContactPhone, IsActive, CreatedAt, UpdatedAt
            FROM PORTS
            WHERE PortCode = @PortCode";
        return await connection.QueryFirstOrDefaultAsync<Port>(sql, new { PortCode = portCode });
    }

    public async Task<int> CreateAsync(Port port)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO PORTS (PortName, PortCode, Country, City, TimeZone,
                               Latitude, Longitude, ContactEmail, ContactPhone, IsActive)
            VALUES (@PortName, @PortCode, @Country, @City, @TimeZone,
                    @Latitude, @Longitude, @ContactEmail, @ContactPhone, @IsActive);
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.QuerySingleAsync<int>(sql, port);
    }

    public async Task<bool> UpdateAsync(Port port)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE PORTS SET
                PortName = @PortName,
                PortCode = @PortCode,
                Country = @Country,
                City = @City,
                TimeZone = @TimeZone,
                Latitude = @Latitude,
                Longitude = @Longitude,
                ContactEmail = @ContactEmail,
                ContactPhone = @ContactPhone,
                IsActive = @IsActive,
                UpdatedAt = GETUTCDATE()
            WHERE PortId = @PortId";
        int rowsAffected = await connection.ExecuteAsync(sql, port);
        return rowsAffected > 0;
    }

    public async Task<bool> DeleteAsync(int portId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM PORTS WHERE PortId = @PortId";
        int rowsAffected = await connection.ExecuteAsync(sql, new { PortId = portId });
        return rowsAffected > 0;
    }
}
