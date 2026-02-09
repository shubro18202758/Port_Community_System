using BerthPlanning.Core.DTOs;
using BerthPlanning.Core.Services.Contracts;
using BerthPlanning.Infrastructure.Data;
using Dapper;

namespace BerthPlanning.Infrastructure.Services;

public class PredictionService : IPredictionService
{
    private readonly IDbConnectionFactory _connectionFactory;

    // Mumbai Port coordinates (default)
    private const decimal PortLatitude = 18.9388m;
    private const decimal PortLongitude = 72.8354m;

    // Thresholds
    private const int DeviationLowMinutes = 30;
    private const int DeviationMediumMinutes = 60;
    private const int DeviationHighMinutes = 120;

    public PredictionService(IDbConnectionFactory connectionFactory)
    {
        _connectionFactory = connectionFactory;
    }

    public async Task<ETAPredictionDto> PredictETAAsync(int vesselId, int? scheduleId = null)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        // Get vessel and schedule info
        const string vesselSql = @"
            SELECT v.VesselId, v.VesselName, v.MMSI, v.VesselType,
                   vs.ScheduleId, vs.ETA, vs.PredictedETA, vs.Status
            FROM VESSELS v
            LEFT JOIN VESSEL_SCHEDULE vs ON v.VesselId = vs.VesselId
                AND vs.Status IN ('Scheduled', 'Approaching')
            WHERE v.VesselId = @VesselId
            ORDER BY vs.ETA DESC";

        dynamic? vesselInfo = await connection.QueryFirstOrDefaultAsync<dynamic>(vesselSql, new { VesselId = vesselId });

        if (vesselInfo == null)
        {
            return new ETAPredictionDto
            {
                VesselId = vesselId,
                Status = "Unknown",
                CalculatedAt = DateTime.UtcNow
            };
        }

        // Get latest AIS position
        const string aisSql = @"
            SELECT TOP 5 AISId, VesselId, MMSI, Latitude, Longitude, Speed, Course, Heading,
                   NavigationStatus, RecordedAt
            FROM AIS_DATA
            WHERE VesselId = @VesselId
            ORDER BY RecordedAt DESC";

        List<dynamic> aisData = (await connection.QueryAsync<dynamic>(aisSql, new { VesselId = vesselId })).ToList();

        ETAPredictionDto prediction = new()
        {
            VesselId = vesselId,
            ScheduleId = scheduleId ?? (int?)vesselInfo.ScheduleId,
            VesselName = vesselInfo.VesselName,
            OriginalETA = vesselInfo.ETA,
            CalculatedAt = DateTime.UtcNow
        };

        if (aisData.Any())
        {
            dynamic latestAis = aisData.First();

            prediction.CurrentPosition = new PredictedVesselPositionDto
            {
                Latitude = (decimal)latestAis.Latitude,
                Longitude = (decimal)latestAis.Longitude,
                Speed = latestAis.Speed != null ? (decimal?)latestAis.Speed : null,
                Course = latestAis.Course != null ? (decimal?)latestAis.Course : null,
                Heading = latestAis.Heading != null ? (decimal?)latestAis.Heading : null,
                NavigationStatus = latestAis.NavigationStatus,
                RecordedAt = latestAis.RecordedAt
            };

            // Calculate distance to port
            var distance = CalculateHaversineDistance(
                (decimal)latestAis.Latitude, (decimal)latestAis.Longitude,
                PortLatitude, PortLongitude);

            // Calculate average speed from recent AIS data
            decimal avgSpeed = CalculateAverageSpeed(aisData);
            decimal currentSpeed = latestAis.Speed ?? avgSpeed;

            // Get weather impact factor
            var weatherFactor = await GetWeatherImpactFactorAsync(connection);

            // Get historical accuracy for this vessel
            var historicalAccuracy = await GetHistoricalAccuracyAsync(connection, vesselId);

            prediction.Factors = new PredictionFactorsDto
            {
                DistanceToPort = Math.Round(distance, 2),
                CurrentSpeed = currentSpeed,
                AverageSpeed = avgSpeed,
                WeatherImpact = weatherFactor,
                TidalImpact = 1.0m, // TODO: Calculate based on tidal data
                HistoricalAccuracy = historicalAccuracy,
                PredictionMethod = currentSpeed > 0 ? "AIS-Based" : "Historical"
            };

            // Predict ETA based on current position and speed
            if (currentSpeed > 0.5m)
            {
                var adjustedSpeed = currentSpeed * weatherFactor;
                var hoursToArrival = distance / adjustedSpeed;
                DateTime predictedETA = DateTime.UtcNow.AddHours((double)hoursToArrival);

                // Apply confidence adjustments based on data freshness
                var dataAge = (DateTime.UtcNow - (DateTime)latestAis.RecordedAt).TotalMinutes;
                var freshnessConfidence = dataAge < 30 ? 95 : dataAge < 60 ? 85 : dataAge < 120 ? 70 : 50;

                prediction.PredictedETA = predictedETA;
                prediction.ConfidenceScore = freshnessConfidence * historicalAccuracy / 100;
            }
            else
            {
                // Vessel stationary - use original ETA with low confidence
                prediction.PredictedETA = prediction.OriginalETA;
                prediction.ConfidenceScore = 40m;
                prediction.Factors.PredictionMethod = "Stationary-Fallback";
            }
        }
        else
        {
            // No AIS data - use original ETA
            prediction.PredictedETA = prediction.OriginalETA;
            prediction.ConfidenceScore = 30m;
            prediction.Factors.PredictionMethod = "NoAIS-Fallback";
        }

        // Calculate deviation
        if (prediction.OriginalETA.HasValue && prediction.PredictedETA.HasValue)
        {
            prediction.DeviationMinutes = (int)(prediction.PredictedETA.Value - prediction.OriginalETA.Value).TotalMinutes;
            prediction.Status = GetDeviationStatus(prediction.DeviationMinutes);
        }
        else
        {
            prediction.Status = "Unknown";
        }

        // Update predicted ETA in database
        if (prediction.ScheduleId.HasValue && prediction.PredictedETA.HasValue)
        {
            const string updateSql = @"
                UPDATE VESSEL_SCHEDULE
                SET PredictedETA = @PredictedETA, UpdatedAt = GETUTCDATE()
                WHERE ScheduleId = @ScheduleId";

            _ = await connection.ExecuteAsync(updateSql, new
            {
                prediction.PredictedETA,
                prediction.ScheduleId
            });
        }

        return prediction;
    }

    public async Task<IEnumerable<ETAPredictionDto>> PredictAllActiveETAsAsync()
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT DISTINCT v.VesselId
            FROM VESSELS v
            INNER JOIN VESSEL_SCHEDULE vs ON v.VesselId = vs.VesselId
            WHERE vs.Status IN ('Scheduled', 'Approaching')";

        IEnumerable<int> vesselIds = await connection.QueryAsync<int>(sql);
        List<ETAPredictionDto> predictions = new();

        foreach (var vesselId in vesselIds)
        {
            ETAPredictionDto prediction = await PredictETAAsync(vesselId);
            predictions.Add(prediction);
        }

        return predictions.OrderBy(p => p.PredictedETA);
    }

    public async Task<decimal> CalculateDistanceToPortAsync(int vesselId, decimal portLat, decimal portLon)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT TOP 1 Latitude, Longitude
            FROM AIS_DATA
            WHERE VesselId = @VesselId
            ORDER BY RecordedAt DESC";

        dynamic? position = await connection.QueryFirstOrDefaultAsync<dynamic>(sql, new { VesselId = vesselId });

        return position == null
            ? 0
            : CalculateHaversineDistance(
            (decimal)position.Latitude, (decimal)position.Longitude,
            portLat, portLon);
    }

    public async Task<IEnumerable<DeviationAlertDto>> DetectDeviationsAsync()
    {
        IEnumerable<ETAPredictionDto> predictions = await PredictAllActiveETAsAsync();
        List<DeviationAlertDto> alerts = new();

        foreach (ETAPredictionDto? prediction in predictions.Where(p => Math.Abs(p.DeviationMinutes) >= DeviationLowMinutes))
        {
            if (!prediction.ScheduleId.HasValue)
            {
                continue;
            }

            IEnumerable<ImpactedScheduleDto> impact = await AnalyzeDeviationImpactAsync(prediction.ScheduleId.Value, prediction.DeviationMinutes);

            DeviationAlertDto alert = new()
            {
                ScheduleId = prediction.ScheduleId.Value,
                VesselId = prediction.VesselId,
                VesselName = prediction.VesselName,
                OriginalETA = prediction.OriginalETA ?? DateTime.UtcNow,
                PredictedETA = prediction.PredictedETA ?? DateTime.UtcNow,
                DeviationMinutes = prediction.DeviationMinutes,
                Severity = GetDeviationSeverity(prediction.DeviationMinutes),
                DeviationType = prediction.DeviationMinutes > 0 ? "Delayed" : "Early",
                ImpactedSchedules = impact.ToList(),
                RequiresReoptimization = Math.Abs(prediction.DeviationMinutes) >= DeviationHighMinutes || impact.Any(),
                DetectedAt = DateTime.UtcNow
            };

            alerts.Add(alert);
        }

        return alerts.OrderByDescending(a => a.Severity).ThenBy(a => a.PredictedETA);
    }

    public async Task<DeviationAlertDto?> CheckScheduleDeviationAsync(int scheduleId)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        const string sql = @"
            SELECT vs.ScheduleId, vs.VesselId, v.VesselName, vs.BerthId, b.BerthName,
                   vs.ETA, vs.PredictedETA, vs.Status
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.ScheduleId = @ScheduleId";

        dynamic? schedule = await connection.QueryFirstOrDefaultAsync<dynamic>(sql, new { ScheduleId = scheduleId });

        if (schedule == null)
        {
            return null;
        }

        // Get fresh prediction
        dynamic prediction = await PredictETAAsync(schedule.VesselId, scheduleId);

        if (Math.Abs(prediction.DeviationMinutes) < DeviationLowMinutes)
        {
            return null;
        }

        dynamic impact = await AnalyzeDeviationImpactAsync(scheduleId, prediction.DeviationMinutes);

        return new DeviationAlertDto
        {
            ScheduleId = scheduleId,
            VesselId = schedule.VesselId,
            VesselName = schedule.VesselName,
            BerthId = schedule.BerthId,
            BerthName = schedule.BerthName,
            OriginalETA = schedule.ETA,
            PredictedETA = prediction.PredictedETA ?? schedule.ETA,
            DeviationMinutes = prediction.DeviationMinutes,
            Severity = GetDeviationSeverity(prediction.DeviationMinutes),
            DeviationType = prediction.DeviationMinutes > 0 ? "Delayed" : "Early",
            ImpactedSchedules = impact.ToList(),
            RequiresReoptimization = Math.Abs(prediction.DeviationMinutes) >= DeviationHighMinutes || impact.Any(),
            DetectedAt = DateTime.UtcNow
        };
    }

    public async Task<IEnumerable<ImpactedScheduleDto>> AnalyzeDeviationImpactAsync(int scheduleId, int deviationMinutes)
    {
        using System.Data.IDbConnection connection = _connectionFactory.CreateConnection();

        // Get the affected schedule
        const string scheduleSql = @"
            SELECT vs.ScheduleId, vs.VesselId, vs.BerthId, vs.ETA, vs.ETD, vs.DwellTime
            FROM VESSEL_SCHEDULE vs
            WHERE vs.ScheduleId = @ScheduleId";

        dynamic? schedule = await connection.QueryFirstOrDefaultAsync<dynamic>(scheduleSql, new { ScheduleId = scheduleId });

        if (schedule == null || schedule.BerthId == null)
        {
            return Enumerable.Empty<ImpactedScheduleDto>();
        }

        DateTime newETA = ((DateTime)schedule.ETA).AddMinutes(deviationMinutes);
        DateTime newETD = schedule.ETD != null
            ? ((DateTime)schedule.ETD).AddMinutes(deviationMinutes)
            : newETA.AddHours(schedule.DwellTime ?? 24);

        // Find schedules that would be impacted by the new timing
        const string impactSql = @"
            SELECT vs.ScheduleId, vs.VesselId, v.VesselName, vs.BerthId, b.BerthName,
                   vs.ETA, vs.ETD, vs.Status
            FROM VESSEL_SCHEDULE vs
            INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE vs.BerthId = @BerthId
              AND vs.ScheduleId != @ScheduleId
              AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
              AND (
                  (vs.ETA < @NewETD AND vs.ETD > @NewETA) -- Overlap
                  OR (vs.ETA BETWEEN @NewETA AND @NewETD) -- Starts during
              )
            ORDER BY vs.ETA";

        IEnumerable<dynamic> impacted = await connection.QueryAsync<dynamic>(impactSql, new
        {
            schedule.BerthId,
            ScheduleId = scheduleId,
            NewETA = newETA,
            NewETD = newETD
        });

        List<ImpactedScheduleDto> result = new();

        foreach (dynamic imp in impacted)
        {
            var impactMinutes = 0;
            var impactType = "Overlap";

            if (imp.ETA < newETD && imp.ETD > newETA)
            {
                // Time overlap - calculate overlap duration
                dynamic overlapStart = imp.ETA > newETA ? imp.ETA : newETA;
                dynamic overlapEnd = imp.ETD < newETD ? imp.ETD : newETD;
                impactMinutes = (int)(overlapEnd - overlapStart).TotalMinutes;
                impactType = "Overlap";
            }
            else if (imp.ETA >= newETA && imp.ETA <= newETD)
            {
                // Would need to be delayed
                impactMinutes = (int)(newETD - imp.ETA).TotalMinutes;
                impactType = "Delayed";
            }

            result.Add(new ImpactedScheduleDto
            {
                ScheduleId = imp.ScheduleId,
                VesselId = imp.VesselId,
                VesselName = imp.VesselName,
                BerthId = imp.BerthId,
                BerthName = imp.BerthName,
                ImpactType = impactType,
                ImpactMinutes = impactMinutes
            });
        }

        return result;
    }

    #region Helper Methods

    private decimal CalculateHaversineDistance(decimal lat1, decimal lon1, decimal lat2, decimal lon2)
    {
        const decimal R = 3440.065m; // Earth radius in nautical miles

        var dLat = ToRadians(lat2 - lat1);
        var dLon = ToRadians(lon2 - lon1);

        var a = (decimal)((Math.Sin((double)dLat / 2) * Math.Sin((double)dLat / 2)) +
                (Math.Cos((double)ToRadians(lat1)) * Math.Cos((double)ToRadians(lat2)) *
                Math.Sin((double)dLon / 2) * Math.Sin((double)dLon / 2)));

        var c = (decimal)(2 * Math.Atan2(Math.Sqrt((double)a), Math.Sqrt(1 - (double)a)));

        return R * c;
    }

    private decimal ToRadians(decimal degrees)
    {
        return degrees * (decimal)Math.PI / 180;
    }

    private decimal CalculateAverageSpeed(List<dynamic> aisData)
    {
        List<decimal> speeds = aisData
            .Where(a => a.Speed is not null and > (dynamic)0)
            .Select(a => (decimal)a.Speed)
            .ToList();

        return speeds.Any() ? speeds.Average() : 10m; // Default 10 knots
    }

    private async Task<decimal> GetWeatherImpactFactorAsync(System.Data.IDbConnection connection)
    {
        const string sql = @"
            SELECT TOP 1 WindSpeed, WaveHeight, Visibility, WeatherCondition, IsAlert
            FROM WEATHER_DATA
            ORDER BY RecordedAt DESC";

        dynamic? weather = await connection.QueryFirstOrDefaultAsync<dynamic>(sql);

        if (weather == null)
        {
            return 1.0m;
        }

        decimal factor = 1.0m;

        // Wind impact
        if (weather.WindSpeed != null)
        {
            var windSpeed = (decimal)weather.WindSpeed;
            if (windSpeed > 30)
            {
                factor *= 0.7m;
            }
            else if (windSpeed > 20)
            {
                factor *= 0.85m;
            }
            else if (windSpeed > 15)
            {
                factor *= 0.95m;
            }
        }

        // Wave impact
        if (weather.WaveHeight != null)
        {
            var waveHeight = (decimal)weather.WaveHeight;
            if (waveHeight > 3)
            {
                factor *= 0.75m;
            }
            else if (waveHeight > 2)
            {
                factor *= 0.9m;
            }
        }

        // Visibility impact
        if (weather.Visibility is not null and < (dynamic)1000)
        {
            factor *= 0.8m;
        }

        // Alert flag
        if (weather.IsAlert)
        {
            factor *= 0.6m;
        }

        return factor;
    }

    private async Task<decimal> GetHistoricalAccuracyAsync(System.Data.IDbConnection connection, int vesselId)
    {
        const string sql = @"
            SELECT
                CASE
                    WHEN COUNT(*) = 0 THEN 75
                    ELSE 100 - AVG(ABS(DATEDIFF(MINUTE, ETA, ATA))) / 10.0
                END AS Accuracy
            FROM VESSEL_SCHEDULE
            WHERE VesselId = @VesselId
              AND ATA IS NOT NULL
              AND ETA IS NOT NULL
              AND Status = 'Departed'";

        var accuracy = await connection.QueryFirstOrDefaultAsync<decimal?>(sql, new { VesselId = vesselId });

        return Math.Max(50, Math.Min(100, accuracy ?? 75));
    }

    private string GetDeviationStatus(int deviationMinutes)
    {
        var absDeviation = Math.Abs(deviationMinutes);

        return absDeviation < DeviationLowMinutes
            ? "OnTime"
            : deviationMinutes < 0
            ? absDeviation >= DeviationHighMinutes ? "VeryEarly" : "Early"
            : absDeviation >= DeviationHighMinutes ? "Critical" : "Delayed";
    }

    private string GetDeviationSeverity(int deviationMinutes)
    {
        var absDeviation = Math.Abs(deviationMinutes);

        if (absDeviation < DeviationLowMinutes)
        {
            return "Low";
        }

        return absDeviation < DeviationMediumMinutes ? "Medium" : absDeviation < DeviationHighMinutes ? "High" : "Critical";
    }

    #endregion
}
