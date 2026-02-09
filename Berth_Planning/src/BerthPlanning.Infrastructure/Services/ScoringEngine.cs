using BerthPlanning.Core.Models;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using Dapper;

namespace BerthPlanning.Infrastructure.Services;

public class ScoringEngine : IScoringEngine
{
    private readonly IDbConnectionFactory _connectionFactory;

    // Scoring weights
    private const decimal PhysicalFitWeight = 25m;
    private const decimal TypeMatchWeight = 20m;
    private const decimal WaitingTimeWeight = 20m;
    private const decimal CraneAvailabilityWeight = 15m;
    private const decimal HistoricalPerformanceWeight = 10m;
    private const decimal TidalCompatibilityWeight = 10m;

    public ScoringEngine(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<decimal> CalculateScoreAsync(Vessel vessel, Berth berth, DateTime proposedETA)
    {
        decimal totalScore = 0;

        // Physical Fit Score (0-25 points)
        totalScore += CalculatePhysicalFitScore(vessel, berth);

        // Type Match Score (0-20 points)
        totalScore += CalculateTypeMatchScore(vessel, berth);

        // Waiting Time Score (0-20 points)
        totalScore += await CalculateWaitingTimeScoreAsync(berth.BerthId, vessel.CreatedAt, proposedETA);

        // Crane Availability Score (0-15 points)
        totalScore += CalculateCraneAvailabilityScore(vessel, berth);

        // Historical Performance Score (0-10 points)
        totalScore += await CalculateHistoricalPerformanceScoreAsync(vessel.VesselId, berth.BerthId);

        // Tidal Compatibility Score (0-10 points)
        if (vessel.Draft.HasValue)
        {
            totalScore += await CalculateTidalCompatibilityScoreAsync(vessel.Draft.Value, proposedETA);
        }
        else
        {
            totalScore += TidalCompatibilityWeight; // Full score if no draft constraint
        }

        return Math.Round(totalScore, 2);
    }

    public decimal CalculatePhysicalFitScore(Vessel vessel, Berth berth)
    {
        if (!vessel.LOA.HasValue || !vessel.Draft.HasValue)
        {
            return 0;
        }

        // Calculate margin percentages
        decimal lengthMargin = (berth.Length - vessel.LOA.Value) / berth.Length;
        decimal draftMargin = (berth.MaxDraft - vessel.Draft.Value) / berth.MaxDraft;

        // Ideal margin is 10-20%, too tight or too loose reduces score
        decimal lengthScore = CalculateMarginScore(lengthMargin) * (PhysicalFitWeight / 2);
        decimal draftScore = CalculateMarginScore(draftMargin) * (PhysicalFitWeight / 2);

        return lengthScore + draftScore;
    }

    private decimal CalculateMarginScore(decimal margin)
    {
        if (margin < 0)
        {
            return 0; // Doesn't fit
        }

        if (margin < 0.05m)
        {
            return 0.7m; // Too tight
        }

        if (margin < 0.10m)
        {
            return 0.85m; // Slightly tight
        }

        if (margin <= 0.25m)
        {
            return 1.0m; // Ideal
        }

        if (margin <= 0.40m)
        {
            return 0.9m; // Slightly loose
        }

        return 0.8m; // Too loose (wasted capacity)
    }

    public decimal CalculateTypeMatchScore(Vessel vessel, Berth berth)
    {
        if (string.IsNullOrEmpty(vessel.VesselType) || string.IsNullOrEmpty(berth.BerthType))
        {
            return TypeMatchWeight * 0.5m; // Neutral score
        }

        if (vessel.VesselType.Equals(berth.BerthType, StringComparison.OrdinalIgnoreCase))
        {
            return TypeMatchWeight; // Perfect match
        }

        // Partial compatibility matrix
        decimal compatibility = GetTypeCompatibility(vessel.VesselType, berth.BerthType);
        return TypeMatchWeight * compatibility;
    }

    private decimal GetTypeCompatibility(string vesselType, string berthType)
    {
        // Compatibility matrix (1.0 = perfect, 0.5 = acceptable, 0.2 = poor)
        Dictionary<(string, string), decimal> matrix = new()
        {
            { ("Container", "Container"), 1.0m },
            { ("Container", "General"), 0.6m },
            { ("Bulk", "Bulk"), 1.0m },
            { ("Bulk", "General"), 0.7m },
            { ("Tanker", "Tanker"), 1.0m },
            { ("Tanker", "Bulk"), 0.3m },
            { ("RoRo", "RoRo"), 1.0m },
            { ("RoRo", "General"), 0.7m },
            { ("General", "General"), 1.0m },
            { ("General", "Container"), 0.6m },
            { ("General", "Bulk"), 0.6m },
        };

        return matrix.GetValueOrDefault((vesselType, berthType), 0.4m);
    }

    public async Task<decimal> CalculateWaitingTimeScoreAsync(int berthId, DateTime vesselETA, DateTime proposedETA)
    {
        // Calculate waiting time in minutes
        double waitingMinutes = (proposedETA - vesselETA).TotalMinutes;

        if (waitingMinutes <= 0)
        {
            return WaitingTimeWeight; // No waiting - full score
        }

        if (waitingMinutes <= 30)
        {
            return WaitingTimeWeight * 0.95m;
        }

        if (waitingMinutes <= 60)
        {
            return WaitingTimeWeight * 0.85m;
        }

        if (waitingMinutes <= 120)
        {
            return WaitingTimeWeight * 0.70m;
        }

        if (waitingMinutes <= 240)
        {
            return WaitingTimeWeight * 0.50m;
        }

        if (waitingMinutes <= 480)
        {
            return WaitingTimeWeight * 0.30m;
        }

        return WaitingTimeWeight * 0.10m; // Long wait - low score
    }

    public decimal CalculateCraneAvailabilityScore(Vessel vessel, Berth berth)
    {
        if (berth.NumberOfCranes == 0)
        {
            return CraneAvailabilityWeight * 0.3m; // No cranes
        }

        // Estimate required cranes based on cargo volume
        int estimatedRequired = EstimateCranesRequired(vessel);

        if (berth.NumberOfCranes >= estimatedRequired)
        {
            return CraneAvailabilityWeight; // Sufficient cranes
        }

        // Partial score based on crane ratio
        decimal ratio = (decimal)berth.NumberOfCranes / estimatedRequired;
        return CraneAvailabilityWeight * Math.Min(1.0m, ratio);
    }

    private int EstimateCranesRequired(Vessel vessel)
    {
        if (!vessel.CargoVolume.HasValue)
        {
            return 1;
        }

        // Rough estimation based on cargo volume and vessel type
        return vessel.VesselType switch
        {
            "Container" => vessel.CargoVolume.Value > 5000 ? 3 : vessel.CargoVolume.Value > 2000 ? 2 : 1,
            "Bulk" => vessel.CargoVolume.Value > 50000 ? 2 : 1,
            _ => 1
        };
    }

    public async Task<decimal> CalculateHistoricalPerformanceScoreAsync(int vesselId, int berthId)
    {
        using var connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT
                COUNT(*) as VisitCount,
                AVG(CAST(ETAAccuracy AS DECIMAL)) as AvgETAAccuracy,
                AVG(CAST(ActualDwellTime AS DECIMAL)) as AvgDwellTime
            FROM VESSEL_HISTORY
            WHERE VesselId = @VesselId AND BerthId = @BerthId";

        var history = await connection.QueryFirstOrDefaultAsync<dynamic>(sql, new { VesselId = vesselId, BerthId = berthId });

        if (history == null || history.VisitCount == 0)
        {
            return HistoricalPerformanceWeight * 0.5m; // Neutral - no history
        }

        // Score based on visit count and accuracy
        decimal visitBonus = Math.Min(1.0m, (decimal)history.VisitCount / 10); // Max bonus at 10 visits
        decimal accuracyBonus = history.AvgETAAccuracy != null ? (decimal)history.AvgETAAccuracy / 100 : 0.5m;

        return HistoricalPerformanceWeight * ((visitBonus * 0.4m) + (accuracyBonus * 0.6m));
    }

    public async Task<decimal> CalculateTidalCompatibilityScoreAsync(decimal vesselDraft, DateTime proposedETA)
    {
        // Shallow draft vessels get full score
        if (vesselDraft <= 10)
        {
            return TidalCompatibilityWeight;
        }

        using var connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT TOP 1 Height, TideType
            FROM TIDAL_DATA
            WHERE TideTime BETWEEN DATEADD(HOUR, -3, @ProposedETA) AND DATEADD(HOUR, 3, @ProposedETA)
            ORDER BY ABS(DATEDIFF(MINUTE, TideTime, @ProposedETA))";

        var tidal = await connection.QueryFirstOrDefaultAsync<dynamic>(sql, new { ProposedETA = proposedETA });

        if (tidal == null)
        {
            return TidalCompatibilityWeight * 0.5m; // No tidal data - neutral
        }

        decimal tidalHeight = (decimal)tidal.Height;
        decimal requiredDepth = vesselDraft + 1; // 1m safety margin

        if (tidalHeight >= requiredDepth)
        {
            return TidalCompatibilityWeight; // Safe
        }

        // Reduced score if tight
        decimal margin = tidalHeight - vesselDraft;
        if (margin > 0)
        {
            return TidalCompatibilityWeight * (0.5m + (margin / 2));
        }

        return 0; // Cannot accommodate
    }
}
