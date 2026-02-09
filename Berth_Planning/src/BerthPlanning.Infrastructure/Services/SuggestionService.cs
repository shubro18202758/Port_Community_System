using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using Dapper;

namespace BerthPlanning.Infrastructure.Services;

public class SuggestionService : ISuggestionService
{
    private readonly IDbConnectionFactory _connectionFactory;
    private readonly IVesselRepository _vesselRepository;
    private readonly IBerthRepository _berthRepository;
    private readonly IConstraintValidator _constraintValidator;
    private readonly IScoringEngine _scoringEngine;

    public SuggestionService(
        IDbConnectionFactory connectionFactory,
        IVesselRepository vesselRepository,
        IBerthRepository berthRepository,
        IConstraintValidator constraintValidator,
        IScoringEngine scoringEngine)
    {
        _connectionFactory = connectionFactory;
        _vesselRepository = vesselRepository;
        _berthRepository = berthRepository;
        _constraintValidator = constraintValidator;
        _scoringEngine = scoringEngine;
    }

    public async Task<SuggestionResponseDto> GetBerthSuggestionsAsync(int vesselId, DateTime? preferredETA = null)
    {
        Vessel? vessel = await _vesselRepository.GetByIdAsync(vesselId);
        if (vessel == null)
        {
            return new SuggestionResponseDto
            {
                VesselId = vesselId,
                RequestedAt = DateTime.UtcNow,
                Message = "Vessel not found"
            };
        }

        DateTime eta = preferredETA ?? DateTime.UtcNow.AddHours(4);
        int estimatedDwellHours = EstimateDwellTime(vessel);
        DateTime etd = eta.AddHours(estimatedDwellHours);

        // Get all active berths
        IEnumerable<Berth> berths = await _berthRepository.GetActiveAsync();
        var suggestions = new List<BerthSuggestionDto>();

        foreach (Berth berth in berths)
        {
            // Basic physical fit check first
            if (!_constraintValidator.ValidatePhysicalFit(vessel, berth))
            {
                continue;
            }

            // Find next available slot for this berth
            (DateTime availableETA, DateTime availableETD) = await FindNextAvailableSlotAsync(berth.BerthId, eta, estimatedDwellHours);

            // Validate all constraints
            ConstraintCheckDto constraintCheck = await _constraintValidator.ValidateAssignmentAsync(vessel, berth, availableETA, availableETD);

            // Skip if hard constraints violated
            if (constraintCheck.Violations.Any(v => v.Severity == "Critical"))
            {
                continue;
            }

            // Calculate score
            decimal score = await _scoringEngine.CalculateScoreAsync(vessel, berth, availableETA);
            constraintCheck.SoftConstraintScore = score;

            // Generate explanation
            List<string> reasoning = await GenerateExplanationAsync(vessel.VesselId, berth.BerthId, score);

            // Calculate waiting time
            int waitMinutes = (int)(availableETA - eta).TotalMinutes;

            suggestions.Add(new BerthSuggestionDto
            {
                BerthId = berth.BerthId,
                BerthName = berth.BerthName,
                BerthCode = berth.BerthCode,
                Score = score,
                Confidence = DetermineConfidence(score, constraintCheck),
                ProposedETA = availableETA,
                ProposedETD = availableETD,
                EstimatedWaitMinutes = Math.Max(0, waitMinutes),
                Reasoning = reasoning,
                Constraints = constraintCheck
            });
        }

        // Rank suggestions by score
        var rankedSuggestions = suggestions
            .OrderByDescending(s => s.Score)
            .Select((s, i) => { s.Rank = i + 1; return s; })
            .Take(5)
            .ToList();

        return new SuggestionResponseDto
        {
            VesselId = vesselId,
            VesselName = vessel.VesselName,
            RequestedAt = DateTime.UtcNow,
            Suggestions = rankedSuggestions,
            Message = rankedSuggestions.Any() ? null : "No compatible berths found"
        };
    }

    private async Task<(DateTime, DateTime)> FindNextAvailableSlotAsync(int berthId, DateTime preferredETA, int dwellHours)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        // Find conflicting schedules
        const string sql = @"
            SELECT ETA, ETD
            FROM VESSEL_SCHEDULE
            WHERE BerthId = @BerthId
              AND Status NOT IN ('Departed', 'Cancelled')
              AND ETD > @PreferredETA
            ORDER BY ETA";

        IEnumerable<(DateTime ETA, DateTime ETD)> schedules = await connection.QueryAsync<(DateTime ETA, DateTime ETD)>(sql,
            new { BerthId = berthId, PreferredETA = preferredETA });

        DateTime proposedETA = preferredETA;
        DateTime proposedETD = preferredETA.AddHours(dwellHours);

        foreach ((DateTime ETA, DateTime ETD) in schedules)
        {
            // Check for overlap
            if (proposedETA < ETD && proposedETD > ETA)
            {
                // Conflict - move to after this schedule
                proposedETA = ETD.AddMinutes(30); // 30 min buffer
                proposedETD = proposedETA.AddHours(dwellHours);
            }
        }

        return (proposedETA, proposedETD);
    }

    private string DetermineConfidence(decimal score, ConstraintCheckDto constraints)
    {
        if (constraints.HardConstraintsMet < constraints.HardConstraintsTotal)
        {
            return "LOW";
        }

        return score >= 85 ? "HIGH" : score >= 70 ? "MEDIUM" : "LOW";
    }

    private int EstimateDwellTime(Vessel vessel)
    {
        // Estimate dwell time in hours based on vessel type and cargo
        return vessel.VesselType switch
        {
            "Container" => vessel.CargoVolume.HasValue && vessel.CargoVolume > 5000 ? 24 : 16,
            "Bulk" => vessel.CargoVolume.HasValue && vessel.CargoVolume > 50000 ? 48 : 24,
            "Tanker" => 24,
            "RoRo" => 8,
            _ => 12
        };
    }

    public async Task<List<string>> GenerateExplanationAsync(int vesselId, int berthId, decimal score)
    {
        var explanations = new List<string>();
        Vessel? vessel = await _vesselRepository.GetByIdAsync(vesselId);
        Berth? berth = await _berthRepository.GetByIdAsync(berthId);

        if (vessel == null || berth == null)
        {
            return explanations;
        }

        // Physical fit explanation
        if (vessel.LOA.HasValue)
        {
            decimal lengthMargin = berth.Length - vessel.LOA.Value;
            decimal marginPercent = lengthMargin / berth.Length * 100;
            explanations.Add($"Physical fit: {vessel.LOA}m vessel in {berth.Length}m berth ({marginPercent:F1}% margin)");
        }

        if (vessel.Draft.HasValue)
        {
            decimal draftMargin = berth.MaxDraft - vessel.Draft.Value;
            explanations.Add($"Draft clearance: {draftMargin:F1}m safety margin");
        }

        // Type match
        if (!string.IsNullOrEmpty(vessel.VesselType) && !string.IsNullOrEmpty(berth.BerthType))
        {
            if (vessel.VesselType == berth.BerthType)
            {
                explanations.Add($"Perfect type match: {vessel.VesselType} berth");
            }
            else
            {
                explanations.Add($"Compatible: {vessel.VesselType} vessel at {berth.BerthType} berth");
            }
        }

        // Crane availability
        if (berth.NumberOfCranes > 0)
        {
            explanations.Add($"{berth.NumberOfCranes} crane(s) available at this berth");
        }

        // Score summary
        if (score >= 85)
        {
            explanations.Add("Excellent match - highly recommended");
        }
        else if (score >= 70)
        {
            explanations.Add("Good match - recommended with minor considerations");
        }
        else if (score >= 50)
        {
            explanations.Add("Acceptable match - some constraints to consider");
        }

        return explanations;
    }

    public async Task<ConflictResolutionDto> GetConflictResolutionSuggestionsAsync(int conflictId)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT c.*, v1.VesselName as Vessel1Name, v2.VesselName as Vessel2Name
            FROM CONFLICTS c
            INNER JOIN VESSEL_SCHEDULE vs1 ON c.ScheduleId1 = vs1.ScheduleId
            INNER JOIN VESSELS v1 ON vs1.VesselId = v1.VesselId
            LEFT JOIN VESSEL_SCHEDULE vs2 ON c.ScheduleId2 = vs2.ScheduleId
            LEFT JOIN VESSELS v2 ON vs2.VesselId = v2.VesselId
            WHERE c.ConflictId = @ConflictId";

        dynamic? conflict = await connection.QueryFirstOrDefaultAsync<dynamic>(sql, new { ConflictId = conflictId });

        if (conflict == null)
        {
            return new ConflictResolutionDto { ConflictId = conflictId };
        }

        var options = new List<ConflictResolutionOptionDto>();

        // Generate resolution options based on conflict type
        switch ((string)conflict.ConflictType)
        {
            case "BerthOverlap":
                options.Add(new ConflictResolutionOptionDto
                {
                    Option = "A",
                    Action = "DELAY_SECOND_VESSEL",
                    Description = $"Delay {conflict.Vessel2Name} until first vessel departs",
                    ImpactScore = 15,
                    Reasoning = "Minimal disruption, maintains priority order"
                });
                options.Add(new ConflictResolutionOptionDto
                {
                    Option = "B",
                    Action = "RELOCATE_FIRST_VESSEL",
                    Description = $"Move {conflict.Vessel1Name} to alternative berth",
                    ImpactScore = 25,
                    Reasoning = "May require resource reallocation"
                });
                options.Add(new ConflictResolutionOptionDto
                {
                    Option = "C",
                    Action = "SWAP_SCHEDULES",
                    Description = "Swap berth assignments between vessels",
                    ImpactScore = 30,
                    Reasoning = "Requires coordination with both vessels"
                });
                break;

            case "ResourceUnavailable":
                options.Add(new ConflictResolutionOptionDto
                {
                    Option = "A",
                    Action = "DELAY_UNTIL_AVAILABLE",
                    Description = "Wait for resource to become available",
                    ImpactScore = 20,
                    Reasoning = "Safe option, ensures proper resource allocation"
                });
                options.Add(new ConflictResolutionOptionDto
                {
                    Option = "B",
                    Action = "USE_ALTERNATIVE_RESOURCE",
                    Description = "Assign alternative resource if available",
                    ImpactScore = 10,
                    Reasoning = "Faster resolution if alternatives exist"
                });
                break;

            case "TidalConstraint":
                options.Add(new ConflictResolutionOptionDto
                {
                    Option = "A",
                    Action = "RESCHEDULE_TO_HIGH_TIDE",
                    Description = "Move arrival to next high tide window",
                    ImpactScore = 15,
                    Reasoning = "Ensures safe navigation for deep-draft vessel"
                });
                break;

            default:
                options.Add(new ConflictResolutionOptionDto
                {
                    Option = "A",
                    Action = "MANUAL_REVIEW",
                    Description = "Requires manual review by operator",
                    ImpactScore = 50,
                    Reasoning = "Complex conflict requiring human decision"
                });
                break;
        }

        return new ConflictResolutionDto
        {
            ConflictId = conflictId,
            ConflictType = conflict.ConflictType,
            AffectedVessels = new List<int> { (int)conflict.ScheduleId1, conflict.ScheduleId2 ?? 0 }.Where(x => x > 0).ToList(),
            Options = options.OrderBy(o => o.ImpactScore).ToList(),
            AIRecommendation = options.OrderBy(o => o.ImpactScore).First().Option,
            Confidence = "HIGH"
        };
    }
}
