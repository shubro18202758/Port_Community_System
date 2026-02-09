using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Models;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using System.Data;

namespace BerthPlanning.Infrastructure.Services;

public class ConstraintValidator : IConstraintValidator
{
    private readonly IDbConnectionFactory _connectionFactory;

    public ConstraintValidator(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<ConstraintCheckDto> ValidateAssignmentAsync(Vessel vessel, Berth berth, DateTime proposedETA, DateTime proposedETD)
    {
        List<ConstraintViolationDto> violations = [];
        int hardConstraintsMet = 0;
        const int totalHardConstraints = 8;

        // HC-01: Physical Fit - Length
        if (vessel.LOA.HasValue && vessel.LOA.Value <= berth.Length)
        {
            hardConstraintsMet++;
        }
        else
        {
            violations.Add(new ConstraintViolationDto
            {
                ConstraintId = "HC-01",
                ConstraintName = "Physical Fit - Length",
                Severity = "Critical",
                Message = $"Vessel LOA ({vessel.LOA}m) exceeds berth length ({berth.Length}m)"
            });
        }

        // HC-02: Physical Fit - Draft
        if (vessel.Draft.HasValue && vessel.Draft.Value <= berth.MaxDraft)
        {
            hardConstraintsMet++;
        }
        else
        {
            violations.Add(new ConstraintViolationDto
            {
                ConstraintId = "HC-02",
                ConstraintName = "Physical Fit - Draft",
                Severity = "Critical",
                Message = $"Vessel draft ({vessel.Draft}m) exceeds berth max draft ({berth.MaxDraft}m)"
            });
        }

        // HC-03: No Time Overlap
        if (await ValidateNoOverlapAsync(berth.BerthId, proposedETA, proposedETD))
        {
            hardConstraintsMet++;
        }
        else
        {
            violations.Add(new ConstraintViolationDto
            {
                ConstraintId = "HC-03",
                ConstraintName = "No Time Overlap",
                Severity = "Critical",
                Message = "Time slot conflicts with existing schedule"
            });
        }

        // HC-04: Berth Active
        if (berth.IsActive)
        {
            hardConstraintsMet++;
        }
        else
        {
            violations.Add(new ConstraintViolationDto
            {
                ConstraintId = "HC-04",
                ConstraintName = "Berth Active",
                Severity = "Critical",
                Message = "Berth is not currently active"
            });
        }

        // HC-05: No Maintenance Conflict
        if (await ValidateMaintenanceWindowAsync(berth.BerthId, proposedETA, proposedETD))
        {
            hardConstraintsMet++;
        }
        else
        {
            violations.Add(new ConstraintViolationDto
            {
                ConstraintId = "HC-05",
                ConstraintName = "No Maintenance Conflict",
                Severity = "Critical",
                Message = "Berth has scheduled maintenance during this period"
            });
        }

        // HC-06: Tidal Window (for deep-draft vessels)
        if (!vessel.Draft.HasValue || vessel.Draft.Value <= 12 || await ValidateTidalWindowAsync(vessel.Draft.Value, proposedETA))
        {
            hardConstraintsMet++;
        }
        else
        {
            violations.Add(new ConstraintViolationDto
            {
                ConstraintId = "HC-06",
                ConstraintName = "Tidal Window",
                Severity = "Critical",
                Message = "Deep-draft vessel requires high tide window"
            });
        }

        // HC-07: Weather Safety
        if (await ValidateWeatherSafetyAsync(proposedETA))
        {
            hardConstraintsMet++;
        }
        else
        {
            violations.Add(new ConstraintViolationDto
            {
                ConstraintId = "HC-07",
                ConstraintName = "Weather Safety",
                Severity = "Critical",
                Message = "Weather alert active during proposed arrival"
            });
        }

        // HC-08: Resource Availability
        if (await ValidateResourceAvailabilityAsync(berth.BerthId, proposedETA, proposedETD))
        {
            hardConstraintsMet++;
        }
        else
        {
            violations.Add(new ConstraintViolationDto
            {
                ConstraintId = "HC-08",
                ConstraintName = "Resource Availability",
                Severity = "High",
                Message = "Required resources (pilot/tugboat) may not be available"
            });
        }

        return new ConstraintCheckDto
        {
            HardConstraintsMet = hardConstraintsMet,
            HardConstraintsTotal = totalHardConstraints,
            SoftConstraintScore = 0, // Calculated separately by ScoringEngine
            Violations = violations
        };
    }

    public bool ValidatePhysicalFit(Vessel vessel, Berth berth)
    {
        return vessel.LOA.HasValue && vessel.Draft.HasValue && vessel.LOA.Value <= berth.Length && vessel.Draft.Value <= berth.MaxDraft;
    }

    public async Task<bool> ValidateNoOverlapAsync(int berthId, DateTime eta, DateTime etd, int? excludeScheduleId = null)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        var sql = @"
            SELECT COUNT(*)
            FROM VESSEL_SCHEDULE
            WHERE BerthId = @BerthId
              AND Status NOT IN ('Departed', 'Cancelled')
              AND ((ETA < @ETD AND ETD > @ETA))";

        if (excludeScheduleId.HasValue)
        {
            sql += " AND ScheduleId != @ExcludeScheduleId";
        }

        var count = await connection.ExecuteScalarAsync<int>(sql, new
        {
            BerthId = berthId,
            ETA = eta,
            ETD = etd,
            ExcludeScheduleId = excludeScheduleId
        });

        return count == 0;
    }

    public async Task<bool> ValidateMaintenanceWindowAsync(int berthId, DateTime eta, DateTime etd)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT COUNT(*)
            FROM BERTH_MAINTENANCE
            WHERE BerthId = @BerthId
              AND Status IN ('Scheduled', 'InProgress')
              AND ((StartTime < @ETD AND EndTime > @ETA))";

        var count = await connection.ExecuteScalarAsync<int>(sql, new { BerthId = berthId, ETA = eta, ETD = etd });
        return count == 0;
    }

    public async Task<bool> ValidateTidalWindowAsync(decimal vesselDraft, DateTime eta)
    {
        // Deep draft vessels (>12m) need high tide
        if (vesselDraft <= 12)
        {
            return true;
        }

        using IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT TOP 1 Height
            FROM TIDAL_DATA
            WHERE TideType = 'HighTide'
              AND TideTime BETWEEN DATEADD(HOUR, -2, @ETA) AND DATEADD(HOUR, 2, @ETA)
            ORDER BY ABS(DATEDIFF(MINUTE, TideTime, @ETA))";

        var tidalHeight = await connection.ExecuteScalarAsync<decimal?>(sql, new { ETA = eta });

        // Require tidal height to accommodate vessel draft + 1m safety margin
        return tidalHeight.HasValue && tidalHeight.Value >= vesselDraft + 1;
    }

    public async Task<bool> ValidateWeatherSafetyAsync(DateTime eta)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT TOP 1 IsAlert
            FROM WEATHER_DATA
            WHERE RecordedAt BETWEEN DATEADD(HOUR, -3, @ETA) AND DATEADD(HOUR, 3, @ETA)
            ORDER BY ABS(DATEDIFF(MINUTE, RecordedAt, @ETA))";

        var isAlert = await connection.ExecuteScalarAsync<bool?>(sql, new { ETA = eta });
        return !isAlert.GetValueOrDefault(false);
    }

    public async Task<bool> ValidateResourceAvailabilityAsync(int berthId, DateTime eta, DateTime etd)
    {
        using IDbConnection connection = _connectionFactory.CreateConnection();

        // Check if pilot and tugboat are available
        const string sql = @"
            SELECT COUNT(*)
            FROM RESOURCES r
            WHERE r.ResourceType IN ('Pilot', 'Tugboat')
              AND r.IsAvailable = 1
              AND NOT EXISTS (
                  SELECT 1 FROM RESOURCE_ALLOCATION ra
                  WHERE ra.ResourceId = r.ResourceId
                    AND ra.Status != 'Released'
                    AND ((ra.AllocatedFrom < @ETD AND ra.AllocatedTo > @ETA))
              )";

        var availableCount = await connection.ExecuteScalarAsync<int>(sql, new { ETA = eta, ETD = etd });

        // Need at least 1 pilot and 1 tugboat
        return availableCount >= 2;
    }
}
