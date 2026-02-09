using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using Dapper;

namespace BerthPlanning.Infrastructure.Services;

public class WhatIfService : IWhatIfService
{
    private readonly IDbConnectionFactory _connectionFactory;
    private readonly ISuggestionService _suggestionService;

    public WhatIfService(IDbConnectionFactory connectionFactory, ISuggestionService suggestionService)
    {
        _connectionFactory = connectionFactory;
        _suggestionService = suggestionService;
    }

    public async Task<WhatIfScenarioResultDto> SimulateVesselDelayAsync(int scheduleId, int delayMinutes)
    {
        WhatIfScenarioRequestDto request = new()
        {
            ScenarioType = "VesselDelay",
            ScheduleId = scheduleId,
            DelayMinutes = delayMinutes
        };

        return await RunCustomScenarioAsync(request);
    }

    public async Task<WhatIfScenarioResultDto> SimulateBerthClosureAsync(int berthId, DateTime closureStart, DateTime closureEnd)
    {
        WhatIfScenarioRequestDto request = new()
        {
            ScenarioType = "BerthClosure",
            BerthId = berthId,
            ClosureStart = closureStart,
            ClosureEnd = closureEnd
        };

        return await RunCustomScenarioAsync(request);
    }

    public async Task<WhatIfScenarioResultDto> SimulateWeatherAlertAsync(string weatherCondition, DateTime duration)
    {
        WhatIfScenarioRequestDto request = new()
        {
            ScenarioType = "WeatherAlert",
            WeatherCondition = weatherCondition,
            ClosureEnd = duration
        };

        return await RunCustomScenarioAsync(request);
    }

    public async Task<WhatIfScenarioResultDto> SimulateNewVesselAsync(int vesselId, DateTime proposedETA)
    {
        WhatIfScenarioRequestDto request = new()
        {
            ScenarioType = "NewVessel",
            VesselId = vesselId,
            NewETA = proposedETA
        };

        return await RunCustomScenarioAsync(request);
    }

    public async Task<WhatIfScenarioResultDto> RunCustomScenarioAsync(WhatIfScenarioRequestDto request)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        WhatIfScenarioResultDto result = new()
        {
            ScenarioType = request.ScenarioType,
            CalculatedAt = DateTime.UtcNow,
            // Get current state
            CurrentState = await GetCurrentMetricsAsync(connection)
        };

        switch (request.ScenarioType)
        {
            case "VesselDelay":
                await SimulateVesselDelayInternalAsync(connection, request, result);
                break;

            case "BerthClosure":
                await SimulateBerthClosureInternalAsync(connection, request, result);
                break;

            case "WeatherAlert":
                await SimulateWeatherAlertInternalAsync(connection, request, result);
                break;

            case "NewVessel":
                await SimulateNewVesselInternalAsync(connection, request, result);
                break;

            default:
                result.Description = "Unknown scenario type";
                break;
        }

        return result;
    }

    private async Task SimulateVesselDelayInternalAsync(
        System.Data.IDbConnection connection,
        WhatIfScenarioRequestDto request,
        WhatIfScenarioResultDto result)
    {
        if (!request.ScheduleId.HasValue || !request.DelayMinutes.HasValue)
        {
            result.Description = "Invalid request: ScheduleId and DelayMinutes required";
            return;
        }

        // Get the schedule being delayed
        const string scheduleSql = @"
            SELECT vs.ScheduleId, vs.VesselId, v.VesselName, vs.BerthId, b.BerthName,
                   vs.ETA, vs.ETD, vs.Status, vs.DwellTime, v.LOA, v.Draft, v.VesselType
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.ScheduleId = @ScheduleId";

        dynamic? schedule = await connection.QueryFirstOrDefaultAsync<dynamic>(scheduleSql, new { request.ScheduleId });

        if (schedule == null)
        {
            result.Description = "Schedule not found";
            return;
        }

        int delayMinutes = request.DelayMinutes.Value;
        DateTime newETA = ((DateTime)schedule.ETA).AddMinutes(delayMinutes);
        DateTime newETD = schedule.ETD != null
            ? ((DateTime)schedule.ETD).AddMinutes(delayMinutes)
            : newETA.AddHours(schedule.DwellTime ?? 24);

        result.Description = $"Simulating {delayMinutes} minute delay for vessel '{schedule.VesselName}'";

        // Add the primary affected schedule
        result.AffectedSchedules.Add(new ScheduleImpactDto
        {
            ScheduleId = schedule.ScheduleId,
            VesselId = schedule.VesselId,
            VesselName = schedule.VesselName,
            BerthId = schedule.BerthId,
            BerthName = schedule.BerthName,
            OriginalETA = schedule.ETA,
            OriginalETD = schedule.ETD,
            ProjectedETA = newETA,
            ProjectedETD = newETD,
            DelayMinutes = delayMinutes,
            ImpactSeverity = GetImpactSeverity(delayMinutes),
            ChangeDescription = $"Primary delay of {delayMinutes} minutes"
        });

        // Find cascading impacts
        if (schedule.BerthId != null)
        {
            const string cascadeSql = @"
                SELECT vs.ScheduleId, vs.VesselId, v.VesselName, vs.BerthId, b.BerthName,
                       vs.ETA, vs.ETD, vs.Status, vs.DwellTime
                FROM VESSEL_SCHEDULE vs
                INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
                LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
                WHERE vs.BerthId = @BerthId
                  AND vs.ScheduleId != @ScheduleId
                  AND vs.Status IN ('Scheduled', 'Approaching')
                  AND vs.ETA >= @OriginalETA
                  AND vs.ETA < @NewETD
                ORDER BY vs.ETA";

            IEnumerable<dynamic> cascading = await connection.QueryAsync<dynamic>(cascadeSql, new
            {
                schedule.BerthId,
                request.ScheduleId,
                OriginalETA = schedule.ETA,
                NewETD = newETD
            });

            int cascadeDelay = 0;
            DateTime previousETD = newETD;

            foreach (dynamic cascade in cascading)
            {
                // Calculate cascade delay
                if (cascade.ETA < previousETD)
                {
                    int overlap = (int)(previousETD - (DateTime)cascade.ETA).TotalMinutes;
                    cascadeDelay += overlap;

                    DateTime cascadeNewETA = ((DateTime)cascade.ETA).AddMinutes(overlap);
                    dynamic cascadeNewETD = cascade.ETD != null
                        ? ((DateTime)cascade.ETD).AddMinutes(overlap)
                        : cascadeNewETA.AddHours(cascade.DwellTime ?? 24);

                    result.AffectedSchedules.Add(new ScheduleImpactDto
                    {
                        ScheduleId = cascade.ScheduleId,
                        VesselId = cascade.VesselId,
                        VesselName = cascade.VesselName,
                        BerthId = cascade.BerthId,
                        BerthName = cascade.BerthName,
                        OriginalETA = cascade.ETA,
                        OriginalETD = cascade.ETD,
                        ProjectedETA = cascadeNewETA,
                        ProjectedETD = cascadeNewETD,
                        DelayMinutes = overlap,
                        ImpactSeverity = GetImpactSeverity(overlap),
                        ChangeDescription = $"Cascade delay of {overlap} minutes"
                    });

                    // Add to projected conflicts
                    result.ProjectedConflicts.Add(new ConflictProjectionDto
                    {
                        Schedule1Id = (int)request.ScheduleId,
                        Schedule2Id = cascade.ScheduleId,
                        Vessel1Name = schedule.VesselName,
                        Vessel2Name = cascade.VesselName,
                        BerthId = schedule.BerthId,
                        BerthName = schedule.BerthName,
                        ConflictType = "TimeOverlap",
                        OverlapMinutes = overlap
                    });

                    previousETD = cascadeNewETD;
                }
            }
        }

        // Calculate projected state
        result.ProjectedState = new ScenarioMetricsDto
        {
            TotalSchedules = result.CurrentState.TotalSchedules,
            ConflictCount = result.CurrentState.ConflictCount + result.ProjectedConflicts.Count,
            AverageWaitingTime = result.CurrentState.AverageWaitingTime +
                (result.AffectedSchedules.Sum(a => a.DelayMinutes) / Math.Max(1, result.AffectedSchedules.Count)),
            BerthUtilization = result.CurrentState.BerthUtilization,
            OnTimeArrivals = result.CurrentState.OnTimeArrivals - result.AffectedSchedules.Count(a => a.ImpactSeverity != "None"),
            DelayedArrivals = result.CurrentState.DelayedArrivals + result.AffectedSchedules.Count(a => a.ImpactSeverity != "None")
        };

        // Generate recommendations
        await GenerateDelayRecommendationsAsync(connection, schedule, delayMinutes, result);
    }

    private async Task SimulateBerthClosureInternalAsync(
        System.Data.IDbConnection connection,
        WhatIfScenarioRequestDto request,
        WhatIfScenarioResultDto result)
    {
        if (!request.BerthId.HasValue || !request.ClosureStart.HasValue || !request.ClosureEnd.HasValue)
        {
            result.Description = "Invalid request: BerthId, ClosureStart, and ClosureEnd required";
            return;
        }

        // Get berth info
        const string berthSql = "SELECT BerthId, BerthName, BerthCode FROM BERTHS WHERE BerthId = @BerthId";
        dynamic? berth = await connection.QueryFirstOrDefaultAsync<dynamic>(berthSql, new { request.BerthId });

        if (berth == null)
        {
            result.Description = "Berth not found";
            return;
        }

        result.Description = $"Simulating closure of berth '{berth.BerthName}' from {request.ClosureStart:g} to {request.ClosureEnd:g}";

        // Find affected schedules
        const string affectedSql = @"
            SELECT vs.ScheduleId, vs.VesselId, v.VesselName, vs.BerthId, b.BerthName,
                   vs.ETA, vs.ETD, vs.Status, v.LOA, v.Draft, v.VesselType
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.BerthId = @BerthId
              AND vs.Status IN ('Scheduled', 'Approaching')
              AND ((vs.ETA BETWEEN @ClosureStart AND @ClosureEnd)
                   OR (vs.ETD BETWEEN @ClosureStart AND @ClosureEnd)
                   OR (vs.ETA <= @ClosureStart AND vs.ETD >= @ClosureEnd))
            ORDER BY vs.ETA";

        IEnumerable<dynamic> affected = await connection.QueryAsync<dynamic>(affectedSql, new
        {
            request.BerthId,
            request.ClosureStart,
            request.ClosureEnd
        });

        foreach (dynamic schedule in affected)
        {
            result.AffectedSchedules.Add(new ScheduleImpactDto
            {
                ScheduleId = schedule.ScheduleId,
                VesselId = schedule.VesselId,
                VesselName = schedule.VesselName,
                BerthId = schedule.BerthId,
                BerthName = schedule.BerthName,
                OriginalETA = schedule.ETA,
                OriginalETD = schedule.ETD,
                ProjectedETA = schedule.ETA, // Will need reassignment
                ProjectedETD = schedule.ETD,
                DelayMinutes = 0,
                ImpactSeverity = "High",
                ChangeDescription = "Requires berth reassignment due to closure"
            });

            // Get alternative berth suggestions
            dynamic alternatives = await GetAlternativeBerthsAsync(connection, schedule);

            if (alternatives.Any())
            {
                dynamic best = alternatives.First();
                result.Recommendations.Add(new ScenarioRecommendationDto
                {
                    Priority = result.Recommendations.Count + 1,
                    Action = "Reassign",
                    Description = $"Move vessel '{schedule.VesselName}' to berth '{best.BerthName}'",
                    TargetScheduleId = schedule.ScheduleId,
                    TargetBerthId = best.BerthId,
                    NewBerthName = best.BerthName,
                    SuggestedTime = schedule.ETA,
                    ImprovementScore = best.Score
                });
            }
            else
            {
                result.Recommendations.Add(new ScenarioRecommendationDto
                {
                    Priority = result.Recommendations.Count + 1,
                    Action = "Delay",
                    Description = $"Delay vessel '{schedule.VesselName}' until after closure ends",
                    TargetScheduleId = schedule.ScheduleId,
                    SuggestedTime = request.ClosureEnd,
                    ImprovementScore = 50
                });
            }
        }

        // Update projected state
        result.ProjectedState = new ScenarioMetricsDto
        {
            TotalSchedules = result.CurrentState.TotalSchedules,
            ConflictCount = result.CurrentState.ConflictCount + result.AffectedSchedules.Count,
            AverageWaitingTime = result.CurrentState.AverageWaitingTime,
            BerthUtilization = result.CurrentState.BerthUtilization * 0.9m, // Reduced due to closure
            OnTimeArrivals = result.CurrentState.OnTimeArrivals - result.AffectedSchedules.Count,
            DelayedArrivals = result.CurrentState.DelayedArrivals + result.AffectedSchedules.Count
        };
    }

    private async Task SimulateWeatherAlertInternalAsync(
        System.Data.IDbConnection connection,
        WhatIfScenarioRequestDto request,
        WhatIfScenarioResultDto result)
    {
        if (string.IsNullOrEmpty(request.WeatherCondition))
        {
            result.Description = "Invalid request: WeatherCondition required";
            return;
        }

        DateTime alertEnd = request.ClosureEnd ?? DateTime.UtcNow.AddHours(6);

        result.Description = $"Simulating weather alert '{request.WeatherCondition}' until {alertEnd:g}";

        // Find all scheduled arrivals during weather event
        const string affectedSql = @"
            SELECT vs.ScheduleId, vs.VesselId, v.VesselName, vs.BerthId, b.BerthName,
                   vs.ETA, vs.ETD, vs.Status, v.LOA, v.Draft, v.VesselType
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.Status IN ('Scheduled', 'Approaching')
              AND vs.ETA BETWEEN GETUTCDATE() AND @AlertEnd
            ORDER BY vs.ETA";

        IEnumerable<dynamic> affected = await connection.QueryAsync<dynamic>(affectedSql, new { AlertEnd = alertEnd });

        // Determine delay based on weather severity
        int weatherDelay = request.WeatherCondition?.ToLower() switch
        {
            "storm" => 240,
            "heavy rain" => 60,
            "fog" => 120,
            "high wind" => 90,
            _ => 60
        };

        foreach (dynamic schedule in affected)
        {
            DateTime projectedETA = ((DateTime)schedule.ETA).AddMinutes(weatherDelay);

            result.AffectedSchedules.Add(new ScheduleImpactDto
            {
                ScheduleId = schedule.ScheduleId,
                VesselId = schedule.VesselId,
                VesselName = schedule.VesselName,
                BerthId = schedule.BerthId,
                BerthName = schedule.BerthName,
                OriginalETA = schedule.ETA,
                OriginalETD = schedule.ETD,
                ProjectedETA = projectedETA > alertEnd ? projectedETA : alertEnd,
                ProjectedETD = schedule.ETD != null ? ((DateTime)schedule.ETD).AddMinutes(weatherDelay) : null,
                DelayMinutes = weatherDelay,
                ImpactSeverity = GetImpactSeverity(weatherDelay),
                ChangeDescription = $"Weather delay: {request.WeatherCondition}"
            });
        }

        // Update projected state
        result.ProjectedState = new ScenarioMetricsDto
        {
            TotalSchedules = result.CurrentState.TotalSchedules,
            ConflictCount = result.CurrentState.ConflictCount,
            AverageWaitingTime = result.CurrentState.AverageWaitingTime + weatherDelay,
            BerthUtilization = result.CurrentState.BerthUtilization * 0.7m,
            OnTimeArrivals = 0,
            DelayedArrivals = result.AffectedSchedules.Count
        };

        // Add weather recommendation
        result.Recommendations.Add(new ScenarioRecommendationDto
        {
            Priority = 1,
            Action = "HoldAll",
            Description = $"Hold all vessel movements until weather clears (estimated {alertEnd:g})",
            ImprovementScore = 100
        });
    }

    private async Task SimulateNewVesselInternalAsync(
        System.Data.IDbConnection connection,
        WhatIfScenarioRequestDto request,
        WhatIfScenarioResultDto result)
    {
        if (!request.VesselId.HasValue || !request.NewETA.HasValue)
        {
            result.Description = "Invalid request: VesselId and NewETA required";
            return;
        }

        // Get vessel info
        const string vesselSql = @"
            SELECT VesselId, VesselName, VesselType, LOA, Draft, Beam
            FROM VESSELS WHERE VesselId = @VesselId";

        dynamic? vessel = await connection.QueryFirstOrDefaultAsync<dynamic>(vesselSql, new { request.VesselId });

        if (vessel == null)
        {
            result.Description = "Vessel not found";
            return;
        }

        result.Description = $"Simulating new arrival of vessel '{vessel.VesselName}' at {request.NewETA:g}";

        // Get berth suggestions using existing service
        dynamic suggestions = await _suggestionService.GetBerthSuggestionsAsync(vessel.VesselId, request.NewETA.Value);

        if (suggestions.Suggestions.Any())
        {
            foreach (var suggestion in suggestions.Suggestions.Take(3))
            {
                result.Recommendations.Add(new ScenarioRecommendationDto
                {
                    Priority = result.Recommendations.Count + 1,
                    Action = "AssignBerth",
                    Description = suggestion.Explanation ?? $"Assign to berth '{suggestion.BerthName}'",
                    TargetBerthId = suggestion.BerthId,
                    NewBerthName = suggestion.BerthName,
                    SuggestedTime = request.NewETA,
                    ImprovementScore = suggestion.Score
                });

                // Check for conflicts with this assignment
                dynamic conflicts = await CheckBerthConflictsAsync(connection, suggestion.BerthId, request.NewETA.Value, 24);

                foreach (var conflict in conflicts)
                {
                    result.ProjectedConflicts.Add(new ConflictProjectionDto
                    {
                        Schedule1Id = 0, // New vessel
                        Schedule2Id = conflict.ScheduleId,
                        Vessel1Name = vessel.VesselName,
                        Vessel2Name = conflict.VesselName,
                        BerthId = suggestion.BerthId,
                        BerthName = suggestion.BerthName,
                        ConflictType = "TimeOverlap",
                        OverlapMinutes = conflict.OverlapMinutes
                    });
                }
            }
        }
        else
        {
            result.Recommendations.Add(new ScenarioRecommendationDto
            {
                Priority = 1,
                Action = "Queue",
                Description = "No suitable berths available at requested time. Vessel will need to wait in queue.",
                ImprovementScore = 30
            });
        }

        // Update projected state
        result.ProjectedState = new ScenarioMetricsDto
        {
            TotalSchedules = result.CurrentState.TotalSchedules + 1,
            ConflictCount = result.CurrentState.ConflictCount + result.ProjectedConflicts.Count,
            AverageWaitingTime = result.CurrentState.AverageWaitingTime,
            BerthUtilization = Math.Min(100, result.CurrentState.BerthUtilization + 5),
            OnTimeArrivals = result.CurrentState.OnTimeArrivals,
            DelayedArrivals = result.CurrentState.DelayedArrivals
        };
    }

    #region Helper Methods

    private async Task<ScenarioMetricsDto> GetCurrentMetricsAsync(System.Data.IDbConnection connection)
    {
        const string sql = @"
            SELECT
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE WHERE Status IN ('Scheduled', 'Approaching', 'Berthed')) AS TotalSchedules,
                (SELECT COUNT(*) FROM CONFLICTS WHERE Status = 'Detected') AS ConflictCount,
                ISNULL((SELECT AVG(CAST(WaitingTime AS DECIMAL)) FROM VESSEL_SCHEDULE WHERE WaitingTime IS NOT NULL), 0) AS AverageWaitingTime,
                (SELECT COUNT(*) FROM BERTHS b WHERE b.IsActive = 1 AND EXISTS (
                    SELECT 1 FROM VESSEL_SCHEDULE vs WHERE vs.BerthId = b.BerthId AND vs.Status = 'Berthed'
                )) * 100.0 / NULLIF((SELECT COUNT(*) FROM BERTHS WHERE IsActive = 1), 0) AS BerthUtilization,
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE WHERE Status = 'Berthed' AND ATA <= ETA) AS OnTimeArrivals,
                (SELECT COUNT(*) FROM VESSEL_SCHEDULE WHERE Status IN ('Scheduled', 'Approaching') AND PredictedETA > ETA) AS DelayedArrivals";

        dynamic? metrics = await connection.QueryFirstOrDefaultAsync<dynamic>(sql);

        return new ScenarioMetricsDto
        {
            TotalSchedules = metrics?.TotalSchedules ?? 0,
            ConflictCount = metrics?.ConflictCount ?? 0,
            AverageWaitingTime = metrics?.AverageWaitingTime ?? 0,
            BerthUtilization = metrics?.BerthUtilization ?? 0,
            OnTimeArrivals = metrics?.OnTimeArrivals ?? 0,
            DelayedArrivals = metrics?.DelayedArrivals ?? 0
        };
    }

    private async Task GenerateDelayRecommendationsAsync(
        System.Data.IDbConnection connection,
        dynamic schedule,
        int delayMinutes,
        WhatIfScenarioResultDto result)
    {
        // Option 1: Accept delay
        result.Recommendations.Add(new ScenarioRecommendationDto
        {
            Priority = 1,
            Action = "AcceptDelay",
            Description = $"Accept the {delayMinutes} minute delay for vessel '{schedule.VesselName}'",
            TargetScheduleId = schedule.ScheduleId,
            ImprovementScore = 50
        });

        // Option 2: Find alternative berth if conflicts exist
        if (result.ProjectedConflicts.Any())
        {
            dynamic alternatives = await GetAlternativeBerthsAsync(connection, schedule);

            if (alternatives.Any())
            {
                dynamic best = alternatives.First();
                result.Recommendations.Add(new ScenarioRecommendationDto
                {
                    Priority = 2,
                    Action = "Reassign",
                    Description = $"Move vessel '{schedule.VesselName}' to berth '{best.BerthName}' to avoid conflicts",
                    TargetScheduleId = schedule.ScheduleId,
                    TargetBerthId = best.BerthId,
                    NewBerthName = best.BerthName,
                    SuggestedTime = ((DateTime)schedule.ETA).AddMinutes(delayMinutes),
                    ImprovementScore = best.Score
                });
            }
        }

        // Option 3: Reschedule conflicting vessels
        if (result.AffectedSchedules.Count > 1)
        {
            result.Recommendations.Add(new ScenarioRecommendationDto
            {
                Priority = 3,
                Action = "RescheduleOthers",
                Description = $"Reschedule {result.AffectedSchedules.Count - 1} other vessels to accommodate delay",
                ImprovementScore = 40
            });
        }
    }

    private async Task<List<(int BerthId, string BerthName, decimal Score)>> GetAlternativeBerthsAsync(
        System.Data.IDbConnection connection, dynamic schedule)
    {
        const string sql = @"
            SELECT b.BerthId, b.BerthName, b.Length, b.MaxDraft, b.BerthType
            FROM BERTHS b
            WHERE b.IsActive = 1
              AND b.BerthId != @CurrentBerthId
              AND b.Length >= @VesselLOA
              AND b.MaxDraft >= @VesselDraft
              AND NOT EXISTS (
                  SELECT 1 FROM VESSEL_SCHEDULE vs
                  WHERE vs.BerthId = b.BerthId
                    AND vs.Status IN ('Berthed', 'Scheduled', 'Approaching')
                    AND ((vs.ETA < @ETD AND vs.ETD > @ETA) OR (vs.ETA BETWEEN @ETA AND @ETD))
              )
            ORDER BY
                CASE WHEN b.BerthType = @VesselType THEN 0 ELSE 1 END,
                b.Length";

        IEnumerable<dynamic> berths = await connection.QueryAsync<dynamic>(sql, new
        {
            CurrentBerthId = schedule.BerthId ?? 0,
            VesselLOA = schedule.LOA ?? 100,
            VesselDraft = schedule.Draft ?? 8,
            VesselType = schedule.VesselType ?? "General",
            schedule.ETA,
            ETD = schedule.ETD ?? ((DateTime)schedule.ETA).AddHours(24)
        });

        return berths.Select(b => (
            BerthId: (int)b.BerthId,
            BerthName: (string)b.BerthName,
            Score: b.BerthType == schedule.VesselType ? 90m : 70m
        )).ToList();
    }

    private async Task<List<(int ScheduleId, string VesselName, int OverlapMinutes)>> CheckBerthConflictsAsync(
        System.Data.IDbConnection connection, int berthId, DateTime eta, int dwellHours)
    {
        DateTime etd = eta.AddHours(dwellHours);

        const string sql = @"
            SELECT vs.ScheduleId, v.VesselName, vs.ETA, vs.ETD
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE vs.BerthId = @BerthId
              AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
              AND ((vs.ETA < @ETD AND vs.ETD > @ETA) OR (vs.ETA BETWEEN @ETA AND @ETD))";

        IEnumerable<dynamic> conflicts = await connection.QueryAsync<dynamic>(sql, new { BerthId = berthId, ETA = eta, ETD = etd });

        return conflicts.Select(c =>
        {
            dynamic overlapStart = c.ETA > eta ? c.ETA : eta;
            dynamic overlapEnd = (c.ETD ?? c.ETA.AddHours(24)) < etd ? (c.ETD ?? c.ETA.AddHours(24)) : etd;
            var overlapMinutes = (int)(overlapEnd - overlapStart).TotalMinutes;

            return (
                ScheduleId: (int)c.ScheduleId,
                VesselName: (string)c.VesselName,
                OverlapMinutes: Math.Max(0, overlapMinutes)
            );
        }).Where(c => c.OverlapMinutes > 0).ToList();
    }

    private string GetImpactSeverity(int delayMinutes)
    {
        if (delayMinutes < 30)
        {
            return "Low";
        }

        return delayMinutes < 60 ? "Medium" : delayMinutes < 120 ? "High" : "Critical";
    }

    #endregion
}
