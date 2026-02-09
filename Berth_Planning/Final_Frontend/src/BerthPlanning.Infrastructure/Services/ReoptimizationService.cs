using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using Dapper;

namespace BerthPlanning.Infrastructure.Services;

public class ReoptimizationService : IReoptimizationService
{
    private readonly IDbConnectionFactory _connectionFactory;
    private readonly ISuggestionService _suggestionService;
    private readonly IScoringEngine _scoringEngine;

    // Thresholds for auto-trigger
    private const int MinDeviationForReopt = 60; // 1 hour minimum deviation to trigger
    private const int MaxSchedulesToOptimize = 20; // Limit optimization scope

    public ReoptimizationService(
        IDbConnectionFactory connectionFactory,
        ISuggestionService suggestionService,
        IScoringEngine scoringEngine)
    {
        _connectionFactory = connectionFactory;
        _suggestionService = suggestionService;
        _scoringEngine = scoringEngine;
    }

    public async Task<ReoptimizationResultDto> TriggerReoptimizationAsync(ReoptimizationRequestDto request)
    {
        ReoptimizationResultDto result = new()
        {
            TriggerType = request.TriggerType,
            CalculatedAt = DateTime.UtcNow
        };

        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        try
        {
            // Get schedules to optimize
            IEnumerable<dynamic> schedules = await GetSchedulesToOptimizeAsync(connection, request);
            result.SchedulesAnalyzed = schedules.Count();

            if (!schedules.Any())
            {
                result.Status = "NoChangesNeeded";
                result.Messages.Add("No schedules found that need optimization");
                return result;
            }

            // Analyze each schedule and find better assignments
            foreach (dynamic schedule in schedules)
            {
                dynamic improvement = await AnalyzeScheduleImprovementAsync(connection, schedule);
                if (improvement != null)
                {
                    result.ProposedChanges.Add(improvement);
                }
            }

            // Detect and resolve conflicts
            IEnumerable<dynamic> conflicts = await DetectConflictsAsync(connection, schedules);
            foreach (dynamic conflict in conflicts)
            {
                dynamic resolution = await GenerateConflictResolutionAsync(connection, conflict);
                if (resolution != null)
                {
                    result.ProposedChanges.Add(resolution);
                    result.ConflictsResolved++;
                }
            }

            result.SchedulesModified = result.ProposedChanges.Count;

            // Calculate improvements
            if (result.ProposedChanges.Any())
            {
                result.Status = "Success";
                result.WaitingTimeReduction = CalculateWaitingTimeReduction(result.ProposedChanges);
                result.UtilizationImprovement = CalculateUtilizationImprovement(result.ProposedChanges);
                result.Messages.Add($"Found {result.ProposedChanges.Count} potential improvements");
            }
            else
            {
                result.Status = "NoChangesNeeded";
                result.Messages.Add("Current schedule is optimal");
            }

            // Auto-apply if requested
            if (request.AutoApply && result.ProposedChanges.Any())
            {
                var applied = await ApplyOptimizationAsync(result.OptimizationId, result.ProposedChanges);
                result.Applied = applied;
                result.Messages.Add(applied ? "Changes applied successfully" : "Failed to apply some changes");
            }
        }
        catch (Exception ex)
        {
            result.Status = "Failed";
            result.Messages.Add($"Optimization failed: {ex.Message}");
        }

        return result;
    }

    public async Task<ReoptimizationResultDto> OptimizeForDeviationAsync(int scheduleId, int deviationMinutes)
    {
        ReoptimizationRequestDto request = new()
        {
            TriggerType = "Deviation",
            TriggeredByScheduleId = scheduleId
        };

        return await TriggerReoptimizationAsync(request);
    }

    public async Task<ReoptimizationResultDto> OptimizeForConflictsAsync(List<int> conflictIds)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        // Get affected schedule IDs from conflicts
        const string sql = @"
            SELECT DISTINCT ScheduleId1 AS ScheduleId FROM CONFLICTS WHERE ConflictId IN @ConflictIds
            UNION
            SELECT DISTINCT ScheduleId2 FROM CONFLICTS WHERE ConflictId IN @ConflictIds AND ScheduleId2 IS NOT NULL";

        List<int> scheduleIds = (await connection.QueryAsync<int>(sql, new { ConflictIds = conflictIds })).ToList();

        ReoptimizationRequestDto request = new()
        {
            TriggerType = "Conflict",
            AffectedScheduleIds = scheduleIds
        };

        return await TriggerReoptimizationAsync(request);
    }

    public async Task<bool> ApplyOptimizationAsync(string optimizationId, List<ScheduleChangeDto> changes)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        int successCount = 0;

        foreach (ScheduleChangeDto change in changes)
        {
            try
            {
                if (change.NewBerthId.HasValue && change.NewBerthId != change.OldBerthId)
                {
                    // Update berth assignment
                    const string sql = @"
                        UPDATE VESSEL_SCHEDULE
                        SET BerthId = @NewBerthId,
                            IsOptimized = 1,
                            UpdatedAt = GETUTCDATE()
                        WHERE ScheduleId = @ScheduleId";

                    _ = await connection.ExecuteAsync(sql, new
                    {
                        change.NewBerthId,
                        change.ScheduleId
                    });
                }

                if (change.NewETA.HasValue && change.NewETA != change.OldETA)
                {
                    // Update ETA
                    const string sql = @"
                        UPDATE VESSEL_SCHEDULE
                        SET ETA = @NewETA,
                            IsOptimized = 1,
                            UpdatedAt = GETUTCDATE()
                        WHERE ScheduleId = @ScheduleId";

                    _ = await connection.ExecuteAsync(sql, new
                    {
                        change.NewETA,
                        change.ScheduleId
                    });
                }

                successCount++;
            }
            catch
            {
                // Log error but continue with other changes
            }
        }

        return successCount == changes.Count;
    }

    public async Task<bool> ShouldTriggerReoptimizationAsync(int scheduleId, int deviationMinutes)
    {
        if (Math.Abs(deviationMinutes) < MinDeviationForReopt)
        {
            return false;
        }

        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        // Check if this deviation causes conflicts
        const string sql = @"
            SELECT COUNT(*)
            FROM VESSEL_SCHEDULE vs1
            INNER JOIN VESSEL_SCHEDULE vs2 ON vs1.BerthId = vs2.BerthId
            WHERE vs1.ScheduleId = @ScheduleId
              AND vs2.ScheduleId != @ScheduleId
              AND vs2.Status IN ('Scheduled', 'Approaching', 'Berthed')
              AND (
                  (DATEADD(MINUTE, @DeviationMinutes, vs1.ETA) < vs2.ETD AND DATEADD(MINUTE, @DeviationMinutes, vs1.ETD) > vs2.ETA)
              )";

        var conflictCount = await connection.QueryFirstAsync<int>(sql, new
        {
            ScheduleId = scheduleId,
            DeviationMinutes = deviationMinutes
        });

        return conflictCount > 0;
    }

    #region Private Methods

    private async Task<IEnumerable<dynamic>> GetSchedulesToOptimizeAsync(
        System.Data.IDbConnection connection,
        ReoptimizationRequestDto request)
    {
        var sql = @"
            SELECT TOP (@MaxSchedules)
                vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.ETD, vs.Status,
                vs.OptimizationScore, vs.ConflictCount, vs.DwellTime,
                v.VesselName, v.VesselType, v.LOA, v.Draft, v.Priority,
                b.BerthName, b.BerthCode
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.Status IN ('Scheduled', 'Approaching')";

        DynamicParameters parameters = new();
        parameters.Add("MaxSchedules", MaxSchedulesToOptimize);

        if (request.AffectedScheduleIds?.Any() == true)
        {
            sql += " AND vs.ScheduleId IN @AffectedScheduleIds";
            parameters.Add("AffectedScheduleIds", request.AffectedScheduleIds);
        }
        else if (request.TriggeredByScheduleId.HasValue)
        {
            // Get the triggered schedule and nearby schedules
            sql += @" AND (vs.ScheduleId = @TriggeredScheduleId
                     OR (vs.BerthId = (SELECT BerthId FROM VESSEL_SCHEDULE WHERE ScheduleId = @TriggeredScheduleId)
                         AND vs.ETA BETWEEN DATEADD(HOUR, -24, (SELECT ETA FROM VESSEL_SCHEDULE WHERE ScheduleId = @TriggeredScheduleId))
                                         AND DATEADD(HOUR, 48, (SELECT ETA FROM VESSEL_SCHEDULE WHERE ScheduleId = @TriggeredScheduleId))))";
            parameters.Add("TriggeredScheduleId", request.TriggeredByScheduleId);
        }

        if (request.OptimizationWindow.HasValue)
        {
            sql += " AND vs.ETA <= @OptimizationWindow";
            parameters.Add("OptimizationWindow", request.OptimizationWindow);
        }

        sql += " ORDER BY vs.ETA";

        return await connection.QueryAsync(sql, parameters);
    }

    private async Task<ScheduleChangeDto?> AnalyzeScheduleImprovementAsync(
        System.Data.IDbConnection connection,
        dynamic schedule)
    {
        // Get current score
        decimal currentScore = schedule.OptimizationScore ?? 0;

        // Get alternative berths with better scores
        const string alternativesSql = @"
            SELECT b.BerthId, b.BerthName, b.BerthCode, b.Length, b.MaxDraft, b.BerthType, b.NumberOfCranes
            FROM BERTHS b
            WHERE b.IsActive = 1
              AND b.Length >= @VesselLOA
              AND b.MaxDraft >= @VesselDraft
              AND b.BerthId != @CurrentBerthId
              AND NOT EXISTS (
                  SELECT 1 FROM VESSEL_SCHEDULE vs
                  WHERE vs.BerthId = b.BerthId
                    AND vs.ScheduleId != @ScheduleId
                    AND vs.Status IN ('Berthed', 'Scheduled', 'Approaching')
                    AND vs.ETA < @ETD AND vs.ETD > @ETA
              )
              AND NOT EXISTS (
                  SELECT 1 FROM BERTH_MAINTENANCE bm
                  WHERE bm.BerthId = b.BerthId
                    AND bm.Status IN ('Scheduled', 'InProgress')
                    AND @ETA BETWEEN bm.StartTime AND bm.EndTime
              )";

        IEnumerable<dynamic> alternatives = await connection.QueryAsync<dynamic>(alternativesSql, new
        {
            VesselLOA = schedule.LOA ?? 100,
            VesselDraft = schedule.Draft ?? 8,
            CurrentBerthId = schedule.BerthId ?? 0,
            schedule.ScheduleId,
            schedule.ETA,
            ETD = schedule.ETD ?? ((DateTime)schedule.ETA).AddHours(schedule.DwellTime ?? 24)
        });

        // Find best alternative
        BerthPlanning.Core.Models.Vessel vessel = new()
        {
            VesselId = schedule.VesselId,
            VesselName = schedule.VesselName,
            VesselType = schedule.VesselType,
            LOA = schedule.LOA,
            Draft = schedule.Draft
        };

        decimal bestScore = currentScore;
        dynamic? bestBerth = null;

        foreach (dynamic alt in alternatives)
        {
            BerthPlanning.Core.Models.Berth berth = new()
            {
                BerthId = alt.BerthId,
                BerthName = alt.BerthName,
                Length = alt.Length,
                MaxDraft = alt.MaxDraft,
                BerthType = alt.BerthType,
                NumberOfCranes = alt.NumberOfCranes
            };

            dynamic score = await _scoringEngine.CalculateScoreAsync(vessel, berth, schedule.ETA);

            if (score > bestScore + 5) // Only suggest if meaningfully better (5+ points)
            {
                bestScore = score;
                bestBerth = alt;
            }
        }

        return bestBerth != null
            ? new ScheduleChangeDto
            {
                ScheduleId = schedule.ScheduleId,
                VesselId = schedule.VesselId,
                VesselName = schedule.VesselName,
                OldBerthId = schedule.BerthId,
                NewBerthId = bestBerth.BerthId,
                OldBerthName = schedule.BerthName,
                NewBerthName = bestBerth.BerthName,
                OldETA = schedule.ETA,
                NewETA = schedule.ETA,
                ChangeReason = $"Better berth match found (score: {currentScore:F1} → {bestScore:F1})"
            }
            : null;
    }

    private async Task<IEnumerable<dynamic>> DetectConflictsAsync(
        System.Data.IDbConnection connection,
        IEnumerable<dynamic> schedules)
    {
        List<int> scheduleIds = schedules.Select(s => (int)s.ScheduleId).ToList();

        if (!scheduleIds.Any())
        {
            return Enumerable.Empty<dynamic>();
        }

        const string sql = @"
            SELECT
                vs1.ScheduleId AS Schedule1Id,
                vs2.ScheduleId AS Schedule2Id,
                v1.VesselName AS Vessel1Name,
                v2.VesselName AS Vessel2Name,
                vs1.BerthId,
                b.BerthName,
                vs1.ETA AS ETA1, vs1.ETD AS ETD1,
                vs2.ETA AS ETA2, vs2.ETD AS ETD2
            FROM VESSEL_SCHEDULE vs1
            INNER JOIN VESSEL_SCHEDULE vs2 ON vs1.BerthId = vs2.BerthId AND vs1.ScheduleId < vs2.ScheduleId
            INNER JOIN VESSELS v1 ON vs1.VesselId = v1.VesselId
            INNER JOIN VESSELS v2 ON vs2.VesselId = v2.VesselId
            LEFT JOIN BERTHS b ON vs1.BerthId = b.BerthId
            WHERE vs1.ScheduleId IN @ScheduleIds
              AND vs1.Status IN ('Scheduled', 'Approaching')
              AND vs2.Status IN ('Scheduled', 'Approaching')
              AND vs1.ETA < vs2.ETD AND vs1.ETD > vs2.ETA";

        return await connection.QueryAsync(sql, new { ScheduleIds = scheduleIds });
    }

    private async Task<ScheduleChangeDto?> GenerateConflictResolutionAsync(
        System.Data.IDbConnection connection,
        dynamic conflict)
    {
        // Try to find alternative berth for the lower priority vessel
        const string prioritySql = @"
            SELECT vs.ScheduleId, v.Priority, v.VesselName, vs.VesselId, vs.ETA, vs.ETD, v.LOA, v.Draft, v.VesselType
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE vs.ScheduleId IN (@Schedule1Id, @Schedule2Id)
            ORDER BY v.Priority DESC"; // Higher priority number = lower priority

        List<dynamic> schedules = (await connection.QueryAsync<dynamic>(prioritySql, new
        {
            conflict.Schedule1Id,
            conflict.Schedule2Id
        })).ToList();

        dynamic vesselToMove = schedules.First(); // Lower priority vessel

        // Find alternative berth
        const string altSql = @"
            SELECT TOP 1 b.BerthId, b.BerthName
            FROM BERTHS b
            WHERE b.IsActive = 1
              AND b.BerthId != @CurrentBerthId
              AND b.Length >= @VesselLOA
              AND b.MaxDraft >= @VesselDraft
              AND NOT EXISTS (
                  SELECT 1 FROM VESSEL_SCHEDULE vs
                  WHERE vs.BerthId = b.BerthId
                    AND vs.Status IN ('Berthed', 'Scheduled', 'Approaching')
                    AND vs.ETA < @ETD AND vs.ETD > @ETA
              )
            ORDER BY CASE WHEN b.BerthType = @VesselType THEN 0 ELSE 1 END";

        dynamic? altBerth = await connection.QueryFirstOrDefaultAsync<dynamic>(altSql, new
        {
            CurrentBerthId = conflict.BerthId,
            VesselLOA = vesselToMove.LOA ?? 100,
            VesselDraft = vesselToMove.Draft ?? 8,
            VesselType = vesselToMove.VesselType ?? "General",
            vesselToMove.ETA,
            ETD = vesselToMove.ETD ?? ((DateTime)vesselToMove.ETA).AddHours(24)
        });

        return altBerth != null
            ? new ScheduleChangeDto
            {
                ScheduleId = vesselToMove.ScheduleId,
                VesselId = vesselToMove.VesselId,
                VesselName = vesselToMove.VesselName,
                OldBerthId = conflict.BerthId,
                NewBerthId = altBerth.BerthId,
                OldBerthName = conflict.BerthName,
                NewBerthName = altBerth.BerthName,
                OldETA = vesselToMove.ETA,
                NewETA = vesselToMove.ETA,
                ChangeReason = $"Conflict resolution: moved to avoid overlap with higher-priority vessel"
            }
            : null;
    }

    private decimal CalculateWaitingTimeReduction(List<ScheduleChangeDto> changes)
    {
        // Estimate waiting time reduction based on berth reassignments
        return changes.Count * 15m; // Assume average 15 min reduction per change
    }

    private decimal CalculateUtilizationImprovement(List<ScheduleChangeDto> changes)
    {
        // Estimate utilization improvement
        return changes.Count * 2m; // Assume 2% improvement per optimized schedule
    }

    #endregion
}
