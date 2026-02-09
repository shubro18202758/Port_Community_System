using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using Dapper;

namespace BerthPlanning.Infrastructure.Services;

public class ResourceOptimizationService : IResourceOptimizationService
{
    private readonly IDbConnectionFactory _connectionFactory;

    public ResourceOptimizationService(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<IEnumerable<ResourceAvailabilityDto>> GetResourceAvailabilityAsync(
        string resourceType, DateTime from, DateTime until)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT
                r.ResourceId,
                r.ResourceType,
                r.ResourceName,
                r.IsAvailable,
                ra.ScheduleId,
                ra.AllocatedFrom,
                ra.AllocatedTo AS AllocatedUntil,
                v.VesselName AS CurrentAssignment
            FROM RESOURCES r
            LEFT JOIN RESOURCE_ALLOCATION ra ON r.ResourceId = ra.ResourceId
                AND ra.Status IN ('Allocated', 'InUse')
                AND ((ra.AllocatedFrom <= @Until AND ra.AllocatedTo >= @From))
            LEFT JOIN VESSEL_SCHEDULE vs ON ra.ScheduleId = vs.ScheduleId
            LEFT JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE r.ResourceType = @ResourceType
              AND r.IsAvailable = 1
            ORDER BY r.ResourceName";

        IEnumerable<dynamic> resources = await connection.QueryAsync<dynamic>(sql, new
        {
            ResourceType = resourceType,
            From = from,
            Until = until
        });

        return resources.Select(r => new ResourceAvailabilityDto
        {
            ResourceId = r.ResourceId,
            ResourceType = r.ResourceType,
            ResourceName = r.ResourceName,
            IsAvailable = r.AllocatedFrom == null,
            AvailableFrom = r.AllocatedUntil != null ? (DateTime?)r.AllocatedUntil : from,
            AvailableUntil = r.AllocatedFrom != null ? (DateTime?)r.AllocatedFrom : until,
            CurrentAssignment = r.CurrentAssignment
        });
    }

    public async Task<IEnumerable<ResourceAvailabilityDto>> GetAllResourcesForScheduleAsync(int scheduleId)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        // Get schedule timing
        const string scheduleSql = @"
            SELECT vs.ETA, vs.ETD, vs.DwellTime, v.VesselType, v.CargoVolume
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE vs.ScheduleId = @ScheduleId";

        dynamic? schedule = await connection.QueryFirstOrDefaultAsync<dynamic>(scheduleSql, new { ScheduleId = scheduleId });

        if (schedule == null)
        {
            return Enumerable.Empty<ResourceAvailabilityDto>();
        }

        DateTime from = schedule.ETA;
        DateTime until = schedule.ETD ?? ((DateTime)schedule.ETA).AddHours(schedule.DwellTime ?? 24);

        // Get all resource types
        List<ResourceAvailabilityDto> results = new();

        IEnumerable<ResourceAvailabilityDto> cranes = await GetResourceAvailabilityAsync("Crane", from, until);
        results.AddRange(cranes);

        IEnumerable<ResourceAvailabilityDto> tugs = await GetResourceAvailabilityAsync("Tugboat", from, until);
        results.AddRange(tugs);

        IEnumerable<ResourceAvailabilityDto> pilots = await GetResourceAvailabilityAsync("Pilot", from, until);
        results.AddRange(pilots);

        return results;
    }

    public async Task<ResourceOptimizationResultDto> OptimizeResourcesForScheduleAsync(int scheduleId)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        // Get schedule and vessel info
        const string scheduleSql = @"
            SELECT vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.ETD, vs.DwellTime,
                   v.VesselName, v.VesselType, v.LOA, v.GrossTonnage, v.CargoVolume,
                   b.BerthName, b.NumberOfCranes
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.ScheduleId = @ScheduleId";

        dynamic? schedule = await connection.QueryFirstOrDefaultAsync<dynamic>(scheduleSql, new { ScheduleId = scheduleId });

        if (schedule == null)
        {
            return new ResourceOptimizationResultDto
            {
                ScheduleId = scheduleId,
                AllResourcesAvailable = false,
                AlternativeRecommendation = "Schedule not found"
            };
        }

        ResourceOptimizationResultDto result = new()
        {
            ScheduleId = scheduleId,
            VesselName = schedule.VesselName
        };

        DateTime from = schedule.ETA;
        DateTime until = schedule.ETD ?? ((DateTime)schedule.ETA).AddHours(schedule.DwellTime ?? 24);

        // Calculate required resources based on vessel type and size
        dynamic requirements = CalculateResourceRequirements(schedule);

        // Check and allocate each resource type
        foreach (var req in requirements)
        {
            dynamic available = await GetAvailableResourcesAsync(connection, req.ResourceType, from, until, req.Quantity);

            if (available.Count >= req.Quantity)
            {
                // Allocate resources
                foreach (var resource in available.Take(req.Quantity))
                {
                    result.Assignments.Add(new ResourceAssignmentDto
                    {
                        ResourceId = resource.ResourceId,
                        ResourceType = req.ResourceType,
                        ResourceName = resource.ResourceName,
                        AssignedFrom = from,
                        AssignedUntil = until
                    });
                }
            }
            else
            {
                // Record conflict
                result.Conflicts.Add(new ResourceConflictDto
                {
                    ResourceType = req.ResourceType,
                    RequiredQuantity = req.Quantity,
                    AvailableQuantity = available.Count,
                    ConflictDescription = $"Need {req.Quantity} {req.ResourceType}(s), only {available.Count} available"
                });
            }
        }

        result.AllResourcesAvailable = !result.Conflicts.Any();

        if (!result.AllResourcesAvailable)
        {
            result.AlternativeRecommendation = await GenerateAlternativeRecommendationAsync(
                connection, schedule, requirements, from, until);
        }

        return result;
    }

    public async Task<ResourceOptimizationResultDto> AllocateResourcesAsync(ResourceAllocationRequestDto request)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        ResourceOptimizationResultDto result = new()
        {
            ScheduleId = request.ScheduleId
        };

        // Get vessel name
        const string vesselSql = @"
            SELECT v.VesselName FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE vs.ScheduleId = @ScheduleId";

        result.VesselName = await connection.QueryFirstOrDefaultAsync<string>(vesselSql,
            new { request.ScheduleId }) ?? "Unknown";

        // Find available resources
        List<(int ResourceId, string ResourceName)> available = await GetAvailableResourcesAsync(
            connection, request.ResourceType, request.RequiredFrom, request.RequiredUntil, request.QuantityRequired);

        if (available.Count >= request.QuantityRequired)
        {
            // Create allocations
            foreach ((int ResourceId, string ResourceName) in available.Take(request.QuantityRequired))
            {
                const string insertSql = @"
                    INSERT INTO RESOURCE_ALLOCATION (ResourceId, ScheduleId, AllocatedFrom, AllocatedTo, Status)
                    VALUES (@ResourceId, @ScheduleId, @AllocatedFrom, @AllocatedTo, 'Allocated')";

                _ = await connection.ExecuteAsync(insertSql, new
                {
                    ResourceId,
                    request.ScheduleId,
                    AllocatedFrom = request.RequiredFrom,
                    AllocatedTo = request.RequiredUntil
                });

                result.Assignments.Add(new ResourceAssignmentDto
                {
                    ResourceId = ResourceId,
                    ResourceType = request.ResourceType,
                    ResourceName = ResourceName,
                    AssignedFrom = request.RequiredFrom,
                    AssignedUntil = request.RequiredUntil
                });
            }

            result.AllResourcesAvailable = true;
        }
        else
        {
            result.AllResourcesAvailable = false;
            result.Conflicts.Add(new ResourceConflictDto
            {
                ResourceType = request.ResourceType,
                RequiredQuantity = request.QuantityRequired,
                AvailableQuantity = available.Count,
                ConflictDescription = $"Insufficient {request.ResourceType} resources available"
            });
        }

        return result;
    }

    public async Task<bool> ReleaseResourcesAsync(int scheduleId)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            UPDATE RESOURCE_ALLOCATION
            SET Status = 'Released', AllocatedTo = GETUTCDATE()
            WHERE ScheduleId = @ScheduleId AND Status IN ('Allocated', 'InUse')";

        var rowsAffected = await connection.ExecuteAsync(sql, new { ScheduleId = scheduleId });
        return rowsAffected > 0;
    }

    public async Task<IEnumerable<ResourceConflictDto>> DetectResourceConflictsAsync(DateTime from, DateTime until)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        // Find schedules in the time window
        const string schedulesSql = @"
            SELECT vs.ScheduleId, vs.VesselId, vs.ETA, vs.ETD, vs.DwellTime,
                   v.VesselType, v.GrossTonnage, v.CargoVolume
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE vs.Status IN ('Scheduled', 'Approaching')
              AND vs.ETA BETWEEN @From AND @Until
            ORDER BY vs.ETA";

        IEnumerable<dynamic> schedules = await connection.QueryAsync<dynamic>(schedulesSql, new { From = from, Until = until });

        List<ResourceConflictDto> conflicts = new();
        Dictionary<string, Dictionary<DateTime, int>> resourceDemand = new(); // Type -> Hour -> Count

        foreach (dynamic schedule in schedules)
        {
            dynamic requirements = CalculateResourceRequirements(schedule);
            DateTime scheduleStart = schedule.ETA;
            DateTime scheduleEnd = schedule.ETD ?? ((DateTime)schedule.ETA).AddHours(schedule.DwellTime ?? 24);

            foreach (var req in requirements)
            {
                if (!resourceDemand.ContainsKey(req.ResourceType))
                {
                    resourceDemand[req.ResourceType] = new Dictionary<DateTime, int>();
                }

                // Aggregate demand by hour
                for (DateTime hour = scheduleStart; hour < scheduleEnd; hour = hour.AddHours(1))
                {
                    DateTime hourKey = new(hour.Year, hour.Month, hour.Day, hour.Hour, 0, 0);
                    if (!resourceDemand[req.ResourceType].ContainsKey(hourKey))
                    {
                        resourceDemand[req.ResourceType][hourKey] = 0;
                    }

                    resourceDemand[req.ResourceType][hourKey] += req.Quantity;
                }
            }
        }

        // Check against available resources
        foreach (var resourceType in resourceDemand.Keys)
        {
            var totalAvailable = await GetTotalResourceCountAsync(connection, resourceType);

            foreach ((DateTime hour, int demand) in resourceDemand[resourceType])
            {
                if (demand > totalAvailable)
                {
                    conflicts.Add(new ResourceConflictDto
                    {
                        ResourceType = resourceType,
                        RequiredQuantity = demand,
                        AvailableQuantity = totalAvailable,
                        ConflictDescription = $"At {hour:g}: Need {demand} {resourceType}(s), only {totalAvailable} available"
                    });
                }
            }
        }

        return conflicts;
    }

    #region Private Helper Methods

    private List<(string ResourceType, int Quantity)> CalculateResourceRequirements(dynamic schedule)
    {
        List<(string ResourceType, int Quantity)> requirements = new();

        string vesselType = schedule.VesselType ?? "General";
        decimal? grossTonnage = schedule.GrossTonnage;
        decimal? cargoVolume = schedule.CargoVolume;

        // Pilot requirements (always 1 for arrival and departure)
        requirements.Add(("Pilot", 1));

        // Tug requirements based on vessel size
        int tugs = 1;
        if (grossTonnage.HasValue)
        {
            if (grossTonnage > 50000)
            {
                tugs = 3;
            }
            else if (grossTonnage > 20000)
            {
                tugs = 2;
            }
        }
        requirements.Add(("Tugboat", tugs));

        // Crane requirements based on vessel type and cargo
        int cranes = vesselType switch
        {
            "Container" => cargoVolume > 5000 ? 3 : cargoVolume > 2000 ? 2 : 1,
            "Bulk" => cargoVolume > 50000 ? 2 : 1,
            "General" => 1,
            _ => 0
        };

        if (cranes > 0)
        {
            requirements.Add(("Crane", cranes));
        }

        return requirements;
    }

    private async Task<List<(int ResourceId, string ResourceName)>> GetAvailableResourcesAsync(
        System.Data.IDbConnection connection,
        string resourceType,
        DateTime from,
        DateTime until,
        int quantityNeeded)
    {
        const string sql = @"
            SELECT r.ResourceId, r.ResourceName
            FROM RESOURCES r
            WHERE r.ResourceType = @ResourceType
              AND r.IsAvailable = 1
              AND NOT EXISTS (
                  SELECT 1 FROM RESOURCE_ALLOCATION ra
                  WHERE ra.ResourceId = r.ResourceId
                    AND ra.Status IN ('Allocated', 'InUse')
                    AND ra.AllocatedFrom < @Until
                    AND ra.AllocatedTo > @From
              )
            ORDER BY r.ResourceName";

        IEnumerable<dynamic> resources = await connection.QueryAsync<dynamic>(sql, new
        {
            ResourceType = resourceType,
            From = from,
            Until = until
        });

        return resources
            .Select(r => (ResourceId: (int)r.ResourceId, ResourceName: (string)r.ResourceName))
            .ToList();
    }

    private async Task<int> GetTotalResourceCountAsync(System.Data.IDbConnection connection, string resourceType)
    {
        const string sql = "SELECT COUNT(*) FROM RESOURCES WHERE ResourceType = @ResourceType AND IsAvailable = 1";
        return await connection.QueryFirstAsync<int>(sql, new { ResourceType = resourceType });
    }

    private async Task<string> GenerateAlternativeRecommendationAsync(
        System.Data.IDbConnection connection,
        dynamic schedule,
        List<(string ResourceType, int Quantity)> requirements,
        DateTime from,
        DateTime until)
    {
        List<string> recommendations = new();
        foreach ((string ResourceType, _) in requirements)
        {
            // Find next available slot
            const string sql = @"
                SELECT MIN(ra.AllocatedTo) AS NextAvailable
                FROM RESOURCE_ALLOCATION ra
                INNER JOIN RESOURCES r ON ra.ResourceId = r.ResourceId
                WHERE r.ResourceType = @ResourceType
                  AND ra.Status IN ('Allocated', 'InUse')
                  AND ra.AllocatedTo > @From";

            DateTime? nextAvailable = await connection.QueryFirstOrDefaultAsync<DateTime?>(sql, new
            {
                ResourceType,
                From = from
            });

            if (nextAvailable.HasValue && nextAvailable > from)
            {
                recommendations.Add($"Delay arrival by {(int)(nextAvailable.Value - from).TotalMinutes} minutes for {ResourceType} availability");
            }
        }

        return recommendations.Any()
            ? string.Join("; ", recommendations)
            : "Consider adjusting schedule timing or requesting additional resources";
    }

    #endregion
}
