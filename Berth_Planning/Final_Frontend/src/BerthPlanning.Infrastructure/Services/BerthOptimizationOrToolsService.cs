using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Models;
using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using Dapper;
using Google.OrTools.Sat;
using Microsoft.Extensions.Logging;
using System.Diagnostics;

namespace BerthPlanning.Infrastructure.Services;

/// <summary>
/// Google OR-Tools based berth optimization service using CP-SAT solver
/// Implements global schedule optimization with constraint programming
/// </summary>
public class BerthOptimizationOrToolsService : IBerthOptimizationOrToolsService
{
    private readonly IDbConnectionFactory _connectionFactory;
    private readonly IVesselRepository _vesselRepository;
    private readonly IBerthRepository _berthRepository;
    private readonly IScheduleRepository _scheduleRepository;
    private readonly IScoringEngine _scoringEngine;
    private readonly IConstraintValidator _constraintValidator;
    private readonly ILogger<BerthOptimizationOrToolsService> _logger;

    // Time discretization: 15-minute slots
    private const int TimeSlotMinutes = 15;
    private const int MaxDwellTimeSlots = 96; // 24 hours max
    private const int BufferSlots = 2; // 30 minutes buffer between vessels

    public BerthOptimizationOrToolsService(
        IDbConnectionFactory connectionFactory,
        IVesselRepository vesselRepository,
        IBerthRepository berthRepository,
        IScheduleRepository scheduleRepository,
        IScoringEngine scoringEngine,
        IConstraintValidator constraintValidator,
        ILogger<BerthOptimizationOrToolsService> logger)
    {
        _connectionFactory = connectionFactory;
        _vesselRepository = vesselRepository;
        _berthRepository = berthRepository;
        _scheduleRepository = scheduleRepository;
        _scoringEngine = scoringEngine;
        _constraintValidator = constraintValidator;
        _logger = logger;
    }

    public async Task<OrToolsOptimizationResultDto> OptimizeGlobalScheduleAsync(OrToolsOptimizationRequestDto request)
    {
        var stopwatch = Stopwatch.StartNew();
        var result = new OrToolsOptimizationResultDto();

        try
        {
            _logger.LogInformation("Starting OR-Tools global schedule optimization");

            // 1. Load data
            var vessels = await LoadVesselsAsync(request.VesselIds, request.StartTime, request.EndTime);
            var berths = await LoadActiveBerthsAsync();
            var existingSchedules = await LoadExistingSchedulesAsync(request.StartTime, request.EndTime);

            if (!vessels.Any())
            {
                result.Status = "NoVessels";
                result.Messages.Add("No vessels to optimize in the given time window");
                return result;
            }

            // 2. Calculate metrics before optimization
            result.Before = await CalculateMetricsAsync(existingSchedules, berths);

            // 3. Build and solve the CP-SAT model
            var (solverResult, assignments) = await SolveWithCpSatAsync(
                vessels, berths, existingSchedules, request);

            // 4. Process results
            result.SolverStatus = solverResult.Status.ToString();
            result.IsFeasible = solverResult.Status == CpSolverStatus.Feasible ||
                               solverResult.Status == CpSolverStatus.Optimal;
            result.IsOptimal = solverResult.Status == CpSolverStatus.Optimal;
            result.ObjectiveValue = solverResult.ObjectiveValue;
            result.ObjectiveBound = solverResult.BestObjectiveBound;
            result.OptimalityGap = result.ObjectiveValue > 0
                ? (result.ObjectiveValue - result.ObjectiveBound) / result.ObjectiveValue * 100
                : 0;

            // 5. Generate assignments
            result.Assignments = assignments;

            // 6. Calculate changes from existing schedules
            result.Changes = GenerateScheduleChanges(existingSchedules, assignments);

            // 7. Calculate metrics after optimization
            result.After = CalculateOptimizedMetrics(assignments, berths);

            // 8. Calculate improvement
            result.Improvement = CalculateImprovement(result.Before, result.After, result.Changes.Count);

            // 9. Apply changes if requested
            if (request.AutoApply && result.IsFeasible && result.Changes.Any())
            {
                await ApplyChangesAsync(result.Changes);
                result.Messages.Add($"Applied {result.Changes.Count} schedule changes");
            }

            // 10. Solver statistics
            result.SolverStats = new OrToolsSolverStatsDto
            {
                SolverName = "CP-SAT",
                NumVariables = solverResult.NumVariables,
                NumConstraints = solverResult.NumConstraints,
                NumBranches = (int)solverResult.NumBranches,
                NumConflicts = (int)solverResult.NumConflicts,
                WallTime = solverResult.WallTime,
                UserTime = solverResult.UserTime,
                StatusMessage = GetStatusMessage(solverResult.Status)
            };

            result.Status = result.IsFeasible ? "Success" : "Infeasible";
            result.Messages.Add($"Optimization completed with status: {result.SolverStatus}");

            _logger.LogInformation("OR-Tools optimization completed: {Status}, Objective: {Objective}",
                result.SolverStatus, result.ObjectiveValue);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error during OR-Tools optimization");
            result.Status = "Error";
            result.Messages.Add($"Optimization failed: {ex.Message}");
        }

        stopwatch.Stop();
        result.ExecutionTimeMs = stopwatch.ElapsedMilliseconds;
        return result;
    }

    private async Task<(CpSolverResult, List<OrToolsBerthAssignmentDto>)> SolveWithCpSatAsync(
        List<VesselScheduleInput> vessels,
        List<Berth> berths,
        List<VesselSchedule> existingSchedules,
        OrToolsOptimizationRequestDto request)
    {
        var model = new CpModel();
        var assignments = new List<OrToolsBerthAssignmentDto>();

        int numVessels = vessels.Count;
        int numBerths = berths.Count;
        int horizonStart = 0;
        int horizonEnd = (int)(request.EndTime - request.StartTime).TotalMinutes / TimeSlotMinutes;

        _logger.LogDebug("Building CP model: {NumVessels} vessels, {NumBerths} berths, {HorizonSlots} time slots",
            numVessels, numBerths, horizonEnd);

        // === Decision Variables ===

        // x[v,b] = 1 if vessel v is assigned to berth b
        var vesselBerthAssignment = new IntVar[numVessels, numBerths];

        // start[v] = start time slot for vessel v
        var vesselStartTime = new IntVar[numVessels];

        // end[v] = end time slot for vessel v
        var vesselEndTime = new IntVar[numVessels];

        // duration[v] = duration for vessel v (based on estimated dwell time)
        var vesselDuration = new IntVar[numVessels];

        // interval[v,b] = optional interval if vessel v assigned to berth b
        var intervals = new IntervalVar[numVessels, numBerths];

        // Pre-calculate compatibility scores
        var compatibilityScores = new long[numVessels, numBerths];
        var physicalFitValid = new bool[numVessels, numBerths];

        for (int v = 0; v < numVessels; v++)
        {
            var vessel = vessels[v];

            for (int b = 0; b < numBerths; b++)
            {
                var berth = berths[b];

                // Check physical fit
                physicalFitValid[v, b] = _constraintValidator.ValidatePhysicalFit(vessel.Vessel, berth);

                // Calculate compatibility score (scaled to integer)
                if (physicalFitValid[v, b])
                {
                    var score = await _scoringEngine.CalculateScoreAsync(vessel.Vessel, berth, vessel.ETA);
                    compatibilityScores[v, b] = (long)(score * 100);
                }
                else
                {
                    compatibilityScores[v, b] = 0;
                }
            }
        }

        // === Create Variables ===

        for (int v = 0; v < numVessels; v++)
        {
            var vessel = vessels[v];

            // Earliest start based on vessel ETA
            int earliestStart = Math.Max(0, (int)(vessel.ETA - request.StartTime).TotalMinutes / TimeSlotMinutes);
            int estimatedDuration = vessel.EstimatedDwellMinutes / TimeSlotMinutes;
            estimatedDuration = Math.Max(4, Math.Min(estimatedDuration, MaxDwellTimeSlots)); // Min 1 hour

            // Start time variable
            vesselStartTime[v] = model.NewIntVar(earliestStart, horizonEnd - estimatedDuration, $"start_v{v}");

            // Duration variable (fixed based on estimated dwell time)
            vesselDuration[v] = model.NewIntVar(estimatedDuration, estimatedDuration, $"duration_v{v}");

            // End time variable
            vesselEndTime[v] = model.NewIntVar(earliestStart + estimatedDuration, horizonEnd, $"end_v{v}");

            // Link start + duration = end
            model.Add(vesselStartTime[v] + vesselDuration[v] == vesselEndTime[v]);

            // Assignment variables for each berth
            for (int b = 0; b < numBerths; b++)
            {
                // Assignment binary variable
                vesselBerthAssignment[v, b] = model.NewBoolVar($"assign_v{v}_b{b}");

                // Create optional interval for no-overlap constraint
                // BoolVar is used as ILiteral for the presence/absence of the interval
                intervals[v, b] = model.NewOptionalIntervalVar(
                    vesselStartTime[v],
                    vesselDuration[v],
                    vesselEndTime[v],
                    (BoolVar)vesselBerthAssignment[v, b],
                    $"interval_v{v}_b{b}");

                // If physical fit is invalid, force assignment to 0
                if (!physicalFitValid[v, b])
                {
                    model.Add(vesselBerthAssignment[v, b] == 0);
                }
            }
        }

        // === Constraints ===

        // C1: Each vessel must be assigned to exactly one berth
        for (int v = 0; v < numVessels; v++)
        {
            var assignmentVars = new IntVar[numBerths];
            for (int b = 0; b < numBerths; b++)
            {
                assignmentVars[b] = vesselBerthAssignment[v, b];
            }
            model.Add(LinearExpr.Sum(assignmentVars) == 1);
        }

        // C2: No overlap on each berth (vessels cannot occupy same berth at same time)
        for (int b = 0; b < numBerths; b++)
        {
            var berthIntervals = new List<IntervalVar>();
            for (int v = 0; v < numVessels; v++)
            {
                berthIntervals.Add(intervals[v, b]);
            }

            // Add existing schedules as fixed intervals
            foreach (var existing in existingSchedules.Where(s => s.BerthId == berths[b].BerthId))
            {
                if (existing.ETA.HasValue && existing.ETD.HasValue)
                {
                    int existingStart = Math.Max(0, (int)(existing.ETA.Value - request.StartTime).TotalMinutes / TimeSlotMinutes);
                    int existingEnd = Math.Min(horizonEnd, (int)(existing.ETD.Value - request.StartTime).TotalMinutes / TimeSlotMinutes);
                    int existingDuration = existingEnd - existingStart;

                    if (existingDuration > 0 && existingStart < horizonEnd)
                    {
                        var fixedInterval = model.NewFixedSizeIntervalVar(existingStart, existingDuration, $"existing_b{b}_{existing.ScheduleId}");
                        berthIntervals.Add(fixedInterval);
                    }
                }
            }

            if (berthIntervals.Count > 1)
            {
                model.AddNoOverlap(berthIntervals);
            }
        }

        // C3: Buffer time between consecutive vessels on same berth
        // (This is implicitly handled by durations, but we can add explicit buffers)

        // === Objective Function ===
        // Minimize: weighted sum of (waiting time - compatibility score)

        var objectiveTerms = new List<LinearExpr>();

        for (int v = 0; v < numVessels; v++)
        {
            var vessel = vessels[v];
            int earliestStart = Math.Max(0, (int)(vessel.ETA - request.StartTime).TotalMinutes / TimeSlotMinutes);

            // Waiting time cost (start - earliest possible start)
            // Weight by vessel priority (higher priority = higher penalty for waiting)
            int priorityMultiplier = 4 - Math.Min(3, vessel.Vessel.Priority); // Priority 1 -> 3x, Priority 3 -> 1x
            var waitingCost = (vesselStartTime[v] - earliestStart) * request.Weights.WaitingTimeWeight * priorityMultiplier;

            // Compatibility bonus (subtract from objective to maximize)
            for (int b = 0; b < numBerths; b++)
            {
                // Scale compatibility score for integer arithmetic
                long scaledBonus = compatibilityScores[v, b] *
                    (request.Weights.TypeMatchWeight + request.Weights.UtilizationWeight) / 100;

                var compatibilityBonus = vesselBerthAssignment[v, b] * scaledBonus;

                objectiveTerms.Add(waitingCost - compatibilityBonus);
            }
        }

        model.Minimize(LinearExpr.Sum(objectiveTerms));

        // === Solve ===

        var solver = new CpSolver();
        solver.StringParameters = $"max_time_in_seconds:{request.MaxSolverTimeSeconds}";

        var status = solver.Solve(model);

        var solverResult = new CpSolverResult
        {
            Status = status,
            ObjectiveValue = status == CpSolverStatus.Feasible || status == CpSolverStatus.Optimal
                ? (long)solver.ObjectiveValue : 0,
            BestObjectiveBound = solver.BestObjectiveBound,
            NumVariables = model.Model.Variables.Count,
            NumConstraints = model.Model.Constraints.Count,
            NumBranches = solver.NumBranches(),
            NumConflicts = solver.NumConflicts(),
            WallTime = solver.WallTime(),
            UserTime = solver.WallTime() // UserTime not available, use WallTime
        };

        // === Extract Solution ===

        if (status == CpSolverStatus.Feasible || status == CpSolverStatus.Optimal)
        {
            for (int v = 0; v < numVessels; v++)
            {
                var vessel = vessels[v];

                for (int b = 0; b < numBerths; b++)
                {
                    if (solver.Value(vesselBerthAssignment[v, b]) == 1)
                    {
                        var berth = berths[b];
                        long startSlot = solver.Value(vesselStartTime[v]);
                        long endSlot = solver.Value(vesselEndTime[v]);

                        var scheduledETA = request.StartTime.AddMinutes(startSlot * TimeSlotMinutes);
                        var scheduledETD = request.StartTime.AddMinutes(endSlot * TimeSlotMinutes);
                        int earliestStart = Math.Max(0, (int)(vessel.ETA - request.StartTime).TotalMinutes / TimeSlotMinutes);
                        int waitingMinutes = (int)(startSlot - earliestStart) * TimeSlotMinutes;

                        assignments.Add(new OrToolsBerthAssignmentDto
                        {
                            VesselId = vessel.Vessel.VesselId,
                            VesselName = vessel.Vessel.VesselName,
                            VesselType = vessel.Vessel.VesselType ?? "Unknown",
                            Priority = vessel.Vessel.Priority,
                            BerthId = berth.BerthId,
                            BerthName = berth.BerthName,
                            BerthType = berth.BerthType ?? "General",
                            TerminalName = berth.TerminalName ?? "",
                            ScheduledETA = scheduledETA,
                            ScheduledETD = scheduledETD,
                            EstimatedDwellTimeMinutes = vessel.EstimatedDwellMinutes,
                            WaitingTimeMinutes = Math.Max(0, waitingMinutes),
                            CompatibilityScore = compatibilityScores[v, b] / 100.0,
                            PhysicalFitScore = physicalFitValid[v, b] ? 100 : 0,
                            TypeMatchScore = GetTypeMatchScore(vessel.Vessel.VesselType, berth.BerthType),
                            TotalScore = compatibilityScores[v, b] / 100.0,
                            AssignmentReason = GenerateAssignmentReason(vessel.Vessel, berth, waitingMinutes),
                            ConstraintsSatisfied = GetSatisfiedConstraints(vessel.Vessel, berth, scheduledETA, scheduledETD)
                        });

                        break;
                    }
                }
            }
        }

        return (solverResult, assignments);
    }

    public async Task<List<OrToolsBerthAssignmentDto>> OptimizeSingleVesselAsync(int vesselId, DateTime preferredETA)
    {
        var vessel = await _vesselRepository.GetByIdAsync(vesselId);
        if (vessel == null)
        {
            return [];
        }

        var berths = await LoadActiveBerthsAsync();
        var assignments = new List<OrToolsBerthAssignmentDto>();

        foreach (var berth in berths)
        {
            if (!_constraintValidator.ValidatePhysicalFit(vessel, berth))
            {
                continue;
            }

            var score = await _scoringEngine.CalculateScoreAsync(vessel, berth, preferredETA);
            var availableSlot = await FindNextAvailableSlotAsync(berth.BerthId, preferredETA);

            if (availableSlot.HasValue)
            {
                int waitingMinutes = (int)(availableSlot.Value - preferredETA).TotalMinutes;
                int dwellMinutes = EstimateDwellTime(vessel);

                assignments.Add(new OrToolsBerthAssignmentDto
                {
                    VesselId = vessel.VesselId,
                    VesselName = vessel.VesselName,
                    VesselType = vessel.VesselType ?? "Unknown",
                    Priority = vessel.Priority,
                    BerthId = berth.BerthId,
                    BerthName = berth.BerthName,
                    BerthType = berth.BerthType ?? "General",
                    TerminalName = berth.TerminalName ?? "",
                    ScheduledETA = availableSlot.Value,
                    ScheduledETD = availableSlot.Value.AddMinutes(dwellMinutes),
                    EstimatedDwellTimeMinutes = dwellMinutes,
                    WaitingTimeMinutes = Math.Max(0, waitingMinutes),
                    CompatibilityScore = (double)score,
                    PhysicalFitScore = 100,
                    TypeMatchScore = GetTypeMatchScore(vessel.VesselType, berth.BerthType),
                    TotalScore = (double)score,
                    AssignmentReason = GenerateAssignmentReason(vessel, berth, waitingMinutes)
                });
            }
        }

        return assignments.OrderByDescending(a => a.TotalScore).Take(5).ToList();
    }

    public async Task<OrToolsOptimizationResultDto> ReoptimizeOnDeviationAsync(int scheduleId, int deviationMinutes)
    {
        var schedule = await _scheduleRepository.GetByIdAsync(scheduleId);
        if (schedule == null)
        {
            return new OrToolsOptimizationResultDto
            {
                Status = "Error",
                Messages = ["Schedule not found"]
            };
        }

        var request = new OrToolsOptimizationRequestDto
        {
            StartTime = DateTime.UtcNow,
            EndTime = DateTime.UtcNow.AddDays(3),
            MaxSolverTimeSeconds = 30,
            AutoApply = false
        };

        return await OptimizeGlobalScheduleAsync(request);
    }

    public async Task<OrToolsFeasibilityResultDto> CheckFeasibilityAsync(int vesselId, int berthId, DateTime eta, DateTime etd)
    {
        var vessel = await _vesselRepository.GetByIdAsync(vesselId);
        var berth = await _berthRepository.GetByIdAsync(berthId);

        if (vessel == null || berth == null)
        {
            return new OrToolsFeasibilityResultDto
            {
                IsFeasible = false,
                Status = "NotFound",
                Violations = [new ConstraintViolationDto { Message = "Vessel or berth not found" }]
            };
        }

        var constraintCheck = await _constraintValidator.ValidateAssignmentAsync(vessel, berth, eta, etd);

        var result = new OrToolsFeasibilityResultDto
        {
            IsFeasible = constraintCheck.Violations.Count == 0,
            Status = constraintCheck.Violations.Count == 0 ? "Feasible" : "Infeasible",
            Violations = constraintCheck.Violations
        };

        if (!result.IsFeasible)
        {
            // Find alternatives
            var alternatives = await OptimizeSingleVesselAsync(vesselId, eta);
            if (alternatives.Any())
            {
                var best = alternatives.First();
                result.AlternativeBerthId = best.BerthId;
                result.AlternativeBerthName = best.BerthName;
                result.NearestFeasibleETA = best.ScheduledETA;
                result.AlternativeSuggestions.Add($"Consider berth {best.BerthName} starting at {best.ScheduledETA:g}");
            }
        }

        return result;
    }

    public Task<OrToolsSolverStatsDto> GetSolverStatisticsAsync()
    {
        return Task.FromResult(new OrToolsSolverStatsDto
        {
            SolverName = "Google OR-Tools CP-SAT",
            StatusMessage = "Ready"
        });
    }

    // === Helper Methods ===

    private async Task<List<VesselScheduleInput>> LoadVesselsAsync(List<int>? vesselIds, DateTime startTime, DateTime endTime)
    {
        using var connection = _connectionFactory.CreateConnection();

        string sql = @"
            SELECT v.*, vs.ETA, vs.ETD, vs.Status, vs.ScheduleId
            FROM VESSELS v
            LEFT JOIN VESSEL_SCHEDULE vs ON v.VesselId = vs.VesselId
            WHERE (vs.Status IS NULL OR vs.Status IN ('Scheduled', 'Approaching'))
              AND (vs.ETA IS NULL OR vs.ETA BETWEEN @StartTime AND @EndTime)";

        if (vesselIds != null && vesselIds.Any())
        {
            sql += " AND v.VesselId IN @VesselIds";
        }

        var vessels = await connection.QueryAsync<dynamic>(sql, new { StartTime = startTime, EndTime = endTime, VesselIds = vesselIds });

        return vessels.Select(v => new VesselScheduleInput
        {
            Vessel = new Vessel
            {
                VesselId = v.VesselId,
                VesselName = v.VesselName,
                VesselType = v.VesselType,
                LOA = v.LOA,
                Beam = v.Beam,
                Draft = v.Draft,
                GrossTonnage = v.GrossTonnage,
                CargoType = v.CargoType,
                CargoVolume = v.CargoVolume,
                Priority = v.Priority ?? 2
            },
            ETA = v.ETA ?? DateTime.UtcNow.AddHours(6),
            ETD = v.ETD,
            ScheduleId = v.ScheduleId,
            EstimatedDwellMinutes = EstimateDwellTimeFromDynamic(v)
        }).ToList();
    }

    private async Task<List<Berth>> LoadActiveBerthsAsync()
    {
        var berths = await _berthRepository.GetAllAsync();
        return berths.Where(b => b.IsActive).ToList();
    }

    private async Task<List<VesselSchedule>> LoadExistingSchedulesAsync(DateTime startTime, DateTime endTime)
    {
        using var connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT *
            FROM VESSEL_SCHEDULE
            WHERE Status NOT IN ('Departed', 'Cancelled')
              AND ((ETA <= @EndTime AND ETD >= @StartTime) OR (ETA BETWEEN @StartTime AND @EndTime))";

        var schedules = await connection.QueryAsync<VesselSchedule>(sql, new { StartTime = startTime, EndTime = endTime });
        return schedules.ToList();
    }

    private async Task<DateTime?> FindNextAvailableSlotAsync(int berthId, DateTime preferredETA)
    {
        using var connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT TOP 1 ETD
            FROM VESSEL_SCHEDULE
            WHERE BerthId = @BerthId
              AND Status NOT IN ('Departed', 'Cancelled')
              AND ETD > @PreferredETA
            ORDER BY ETD ASC";

        var nextETD = await connection.QueryFirstOrDefaultAsync<DateTime?>(sql, new { BerthId = berthId, PreferredETA = preferredETA });

        if (!nextETD.HasValue)
        {
            return preferredETA;
        }

        // Check if preferred ETA conflicts with any existing schedule
        const string conflictSql = @"
            SELECT COUNT(*)
            FROM VESSEL_SCHEDULE
            WHERE BerthId = @BerthId
              AND Status NOT IN ('Departed', 'Cancelled')
              AND ETA <= @PreferredETA AND ETD > @PreferredETA";

        var conflicts = await connection.ExecuteScalarAsync<int>(conflictSql, new { BerthId = berthId, PreferredETA = preferredETA });

        return conflicts > 0 ? nextETD.Value.AddMinutes(30) : preferredETA;
    }

    private async Task<OrToolsMetricsDto> CalculateMetricsAsync(List<VesselSchedule> schedules, List<Berth> berths)
    {
        var metrics = new OrToolsMetricsDto
        {
            AssignedVessels = schedules.Count(s => s.BerthId.HasValue),
            UnassignedVessels = schedules.Count(s => !s.BerthId.HasValue),
            TotalConflicts = schedules.Sum(s => s.ConflictCount)
        };

        if (schedules.Any(s => s.WaitingTime.HasValue))
        {
            metrics.TotalWaitingTimeMinutes = schedules.Where(s => s.WaitingTime.HasValue).Sum(s => s.WaitingTime!.Value);
            metrics.AverageWaitingTimeMinutes = schedules.Where(s => s.WaitingTime.HasValue).Average(s => s.WaitingTime!.Value);
        }

        // Calculate utilization
        var assignedBerthIds = schedules.Where(s => s.BerthId.HasValue).Select(s => s.BerthId!.Value).Distinct();
        metrics.BerthUtilizationPercent = berths.Count > 0 ? (double)assignedBerthIds.Count() / berths.Count * 100 : 0;

        if (schedules.Any(s => s.OptimizationScore.HasValue))
        {
            metrics.AverageCompatibilityScore = (double)schedules.Where(s => s.OptimizationScore.HasValue).Average(s => s.OptimizationScore!.Value);
        }

        return metrics;
    }

    private OrToolsMetricsDto CalculateOptimizedMetrics(List<OrToolsBerthAssignmentDto> assignments, List<Berth> berths)
    {
        return new OrToolsMetricsDto
        {
            AssignedVessels = assignments.Count,
            UnassignedVessels = 0,
            TotalWaitingTimeMinutes = assignments.Sum(a => a.WaitingTimeMinutes),
            AverageWaitingTimeMinutes = assignments.Any() ? assignments.Average(a => a.WaitingTimeMinutes) : 0,
            BerthUtilizationPercent = berths.Count > 0 ? (double)assignments.Select(a => a.BerthId).Distinct().Count() / berths.Count * 100 : 0,
            TotalConflicts = 0,
            AverageCompatibilityScore = assignments.Any() ? assignments.Average(a => a.CompatibilityScore) : 0
        };
    }

    private OrToolsImprovementDto CalculateImprovement(OrToolsMetricsDto before, OrToolsMetricsDto after, int changesCount)
    {
        return new OrToolsImprovementDto
        {
            WaitingTimeReductionPercent = before.TotalWaitingTimeMinutes > 0
                ? (before.TotalWaitingTimeMinutes - after.TotalWaitingTimeMinutes) / before.TotalWaitingTimeMinutes * 100
                : 0,
            UtilizationImprovementPercent = after.BerthUtilizationPercent - before.BerthUtilizationPercent,
            ConflictsResolved = before.TotalConflicts - after.TotalConflicts,
            SchedulesChanged = changesCount,
            OverallImprovementScore = CalculateOverallImprovement(before, after)
        };
    }

    private double CalculateOverallImprovement(OrToolsMetricsDto before, OrToolsMetricsDto after)
    {
        double waitingImprovement = before.TotalWaitingTimeMinutes > 0
            ? (before.TotalWaitingTimeMinutes - after.TotalWaitingTimeMinutes) / before.TotalWaitingTimeMinutes
            : 0;
        double utilizationImprovement = (after.BerthUtilizationPercent - before.BerthUtilizationPercent) / 100;
        double scoreImprovement = before.AverageCompatibilityScore > 0
            ? (after.AverageCompatibilityScore - before.AverageCompatibilityScore) / before.AverageCompatibilityScore
            : 0;

        return (waitingImprovement * 0.4 + utilizationImprovement * 0.3 + scoreImprovement * 0.3) * 100;
    }

    private List<ScheduleChangeDto> GenerateScheduleChanges(List<VesselSchedule> existing, List<OrToolsBerthAssignmentDto> optimized)
    {
        var changes = new List<ScheduleChangeDto>();

        foreach (var assignment in optimized)
        {
            var existingSchedule = existing.FirstOrDefault(e => e.VesselId == assignment.VesselId);

            if (existingSchedule == null)
            {
                changes.Add(new ScheduleChangeDto
                {
                    VesselId = assignment.VesselId,
                    VesselName = assignment.VesselName,
                    NewBerthId = assignment.BerthId,
                    NewBerthName = assignment.BerthName,
                    NewETA = assignment.ScheduledETA,
                    ChangeReason = "New assignment by OR-Tools optimizer"
                });
            }
            else if (existingSchedule.BerthId != assignment.BerthId ||
                    (existingSchedule.ETA.HasValue && Math.Abs((existingSchedule.ETA.Value - assignment.ScheduledETA).TotalMinutes) > 30))
            {
                changes.Add(new ScheduleChangeDto
                {
                    ScheduleId = existingSchedule.ScheduleId,
                    VesselId = assignment.VesselId,
                    VesselName = assignment.VesselName,
                    OldBerthId = existingSchedule.BerthId,
                    OldBerthName = existingSchedule.BerthName,
                    NewBerthId = assignment.BerthId,
                    NewBerthName = assignment.BerthName,
                    OldETA = existingSchedule.ETA,
                    NewETA = assignment.ScheduledETA,
                    ChangeReason = GenerateChangeReason(existingSchedule, assignment)
                });
            }
        }

        return changes;
    }

    private async Task ApplyChangesAsync(List<ScheduleChangeDto> changes)
    {
        using var connection = _connectionFactory.CreateConnection();

        foreach (var change in changes)
        {
            if (change.ScheduleId > 0)
            {
                const string sql = @"
                    UPDATE VESSEL_SCHEDULE
                    SET BerthId = @NewBerthId,
                        ETA = @NewETA,
                        IsOptimized = 1,
                        UpdatedAt = @UpdatedAt
                    WHERE ScheduleId = @ScheduleId";

                await connection.ExecuteAsync(sql, new
                {
                    change.NewBerthId,
                    change.NewETA,
                    UpdatedAt = DateTime.UtcNow,
                    change.ScheduleId
                });
            }
        }
    }

    private int EstimateDwellTime(Vessel vessel)
    {
        // Estimate based on cargo type and volume
        int baseDwell = vessel.VesselType switch
        {
            "Container" => 720, // 12 hours
            "Bulk" => 1440, // 24 hours
            "Tanker" => 960, // 16 hours
            "RoRo" => 480, // 8 hours
            _ => 720 // 12 hours default
        };

        if (vessel.CargoVolume.HasValue)
        {
            baseDwell = (int)(baseDwell * Math.Min(2.0m, vessel.CargoVolume.Value / 10000m));
        }

        return Math.Max(240, Math.Min(2880, baseDwell)); // Min 4 hours, Max 48 hours
    }

    private int EstimateDwellTimeFromDynamic(dynamic vessel)
    {
        string? vesselType = vessel.VesselType;
        decimal? cargoVolume = vessel.CargoVolume;

        int baseDwell = vesselType switch
        {
            "Container" => 720,
            "Bulk" => 1440,
            "Tanker" => 960,
            "RoRo" => 480,
            _ => 720
        };

        if (cargoVolume.HasValue)
        {
            baseDwell = (int)(baseDwell * Math.Min(2.0m, cargoVolume.Value / 10000m));
        }

        return Math.Max(240, Math.Min(2880, baseDwell));
    }

    private double GetTypeMatchScore(string? vesselType, string? berthType)
    {
        if (string.IsNullOrEmpty(vesselType) || string.IsNullOrEmpty(berthType))
            return 50;

        if (vesselType.Equals(berthType, StringComparison.OrdinalIgnoreCase))
            return 100;

        var compatibility = new Dictionary<(string, string), double>
        {
            { ("Container", "General"), 60 },
            { ("Bulk", "General"), 70 },
            { ("RoRo", "General"), 70 },
            { ("General", "Container"), 60 },
            { ("General", "Bulk"), 60 }
        };

        return compatibility.GetValueOrDefault((vesselType, berthType), 40);
    }

    private string GenerateAssignmentReason(Vessel vessel, Berth berth, int waitingMinutes)
    {
        var reasons = new List<string>();

        if (vessel.VesselType?.Equals(berth.BerthType, StringComparison.OrdinalIgnoreCase) == true)
        {
            reasons.Add("Perfect vessel-berth type match");
        }

        if (vessel.LOA.HasValue)
        {
            decimal margin = (berth.Length - vessel.LOA.Value) / berth.Length * 100;
            if (margin >= 10 && margin <= 25)
            {
                reasons.Add("Optimal berth length utilization");
            }
        }

        if (waitingMinutes <= 30)
        {
            reasons.Add("Minimal waiting time");
        }
        else if (waitingMinutes > 120)
        {
            reasons.Add($"Note: {waitingMinutes} minutes waiting time");
        }

        return reasons.Any() ? string.Join("; ", reasons) : "Best available option";
    }

    private string GenerateChangeReason(VesselSchedule existing, OrToolsBerthAssignmentDto optimized)
    {
        var reasons = new List<string>();

        if (existing.BerthId != optimized.BerthId)
        {
            reasons.Add($"Berth changed for better utilization");
        }

        if (existing.ETA.HasValue)
        {
            var timeDiff = (optimized.ScheduledETA - existing.ETA.Value).TotalMinutes;
            if (Math.Abs(timeDiff) > 30)
            {
                reasons.Add($"Time adjusted by {Math.Abs(timeDiff):F0} minutes");
            }
        }

        return reasons.Any() ? string.Join("; ", reasons) : "Optimized assignment";
    }

    private List<string> GetSatisfiedConstraints(Vessel vessel, Berth berth, DateTime eta, DateTime etd)
    {
        var constraints = new List<string>();

        if (vessel.LOA.HasValue && vessel.LOA.Value <= berth.Length)
            constraints.Add("HC-01: Physical Fit - Length");

        if (vessel.Draft.HasValue && vessel.Draft.Value <= berth.MaxDraft)
            constraints.Add("HC-02: Physical Fit - Draft");

        if (berth.IsActive)
            constraints.Add("HC-04: Berth Active");

        return constraints;
    }

    private string GetStatusMessage(CpSolverStatus status)
    {
        return status switch
        {
            CpSolverStatus.Optimal => "Optimal solution found",
            CpSolverStatus.Feasible => "Feasible solution found (may not be optimal)",
            CpSolverStatus.Infeasible => "No feasible solution exists",
            CpSolverStatus.ModelInvalid => "Model is invalid",
            CpSolverStatus.Unknown => "Solver status unknown",
            _ => status.ToString()
        };
    }

    // Helper classes
    private class VesselScheduleInput
    {
        public Vessel Vessel { get; set; } = new();
        public DateTime ETA { get; set; }
        public DateTime? ETD { get; set; }
        public int? ScheduleId { get; set; }
        public int EstimatedDwellMinutes { get; set; }
    }

    private class CpSolverResult
    {
        public CpSolverStatus Status { get; set; }
        public long ObjectiveValue { get; set; }
        public double BestObjectiveBound { get; set; }
        public int NumVariables { get; set; }
        public int NumConstraints { get; set; }
        public long NumBranches { get; set; }
        public long NumConflicts { get; set; }
        public double WallTime { get; set; }
        public double UserTime { get; set; }
    }
}
