using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Repositories;

public class ResourceRepository : IResourceRepository
{
    private readonly IDbConnectionFactory _connectionFactory;

    public ResourceRepository(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<Resource>> GetAllAsync()
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT ResourceId, ResourceType, ResourceName, Capacity, IsAvailable,
                   MaintenanceSchedule, CreatedAt
            FROM RESOURCES
            ORDER BY ResourceType, ResourceName";
        return await connection.QueryAsync<Resource>(sql);
    }

    public async Task<Resource?> GetByIdAsync(int resourceId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT ResourceId, ResourceType, ResourceName, Capacity, IsAvailable,
                   MaintenanceSchedule, CreatedAt
            FROM RESOURCES
            WHERE ResourceId = @ResourceId";
        return await connection.QueryFirstOrDefaultAsync<Resource>(sql, new { ResourceId = resourceId });
    }

    public async Task<IEnumerable<Resource>> GetByTypeAsync(string resourceType)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT ResourceId, ResourceType, ResourceName, Capacity, IsAvailable,
                   MaintenanceSchedule, CreatedAt
            FROM RESOURCES
            WHERE ResourceType = @ResourceType
            ORDER BY ResourceName";
        return await connection.QueryAsync<Resource>(sql, new { ResourceType = resourceType });
    }

    public async Task<int> CreateAsync(Resource resource)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            INSERT INTO RESOURCES (ResourceType, ResourceName, Capacity, IsAvailable, MaintenanceSchedule, CreatedAt)
            VALUES (@ResourceType, @ResourceName, @Capacity, @IsAvailable, @MaintenanceSchedule, GETUTCDATE());
            SELECT CAST(SCOPE_IDENTITY() AS INT);";
        return await connection.ExecuteScalarAsync<int>(sql, resource);
    }

    public async Task<bool> UpdateAsync(Resource resource)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            UPDATE RESOURCES
            SET ResourceType = @ResourceType,
                ResourceName = @ResourceName,
                Capacity = @Capacity,
                IsAvailable = @IsAvailable,
                MaintenanceSchedule = @MaintenanceSchedule
            WHERE ResourceId = @ResourceId";
        int rows = await connection.ExecuteAsync(sql, resource);
        return rows > 0;
    }

    public async Task<bool> DeleteAsync(int resourceId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = "DELETE FROM RESOURCES WHERE ResourceId = @ResourceId";
        int rows = await connection.ExecuteAsync(sql, new { ResourceId = resourceId });
        return rows > 0;
    }

    public async Task<IEnumerable<ResourceAllocation>> GetAllocationsAsync(int resourceId)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();
        const string sql = @"
            SELECT ra.AllocationId, ra.ScheduleId, ra.ResourceId,
                   ra.AllocatedFrom, ra.AllocatedTo, ra.Quantity, ra.Status, ra.CreatedAt,
                   r.ResourceName, r.ResourceType,
                   v.VesselName
            FROM RESOURCE_ALLOCATION ra
            INNER JOIN RESOURCES r ON ra.ResourceId = r.ResourceId
            LEFT JOIN VESSEL_SCHEDULE vs ON ra.ScheduleId = vs.ScheduleId
            LEFT JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE ra.ResourceId = @ResourceId
              AND ra.Status != 'Released'
            ORDER BY ra.AllocatedFrom DESC";
        return await connection.QueryAsync<ResourceAllocation>(sql, new { ResourceId = resourceId });
    }
}
