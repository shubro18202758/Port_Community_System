using BerthPlanning.Core.Interfaces;
using BerthPlanning.Core.Models;
using Microsoft.AspNetCore.Mvc;

namespace BerthPlanning.API.Controllers;

[ApiController]
[Route("[controller]")]
public class AISController : ControllerBase
{
    private readonly IVesselRepository _vesselRepository;
    private readonly ILogger<AISController> _logger;

    public AISController(
        IVesselRepository vesselRepository,
        ILogger<AISController> logger)
    {
        _vesselRepository = vesselRepository;
        _logger = logger;
    }

    /// <summary>
    /// Get simulated AIS positions for vessels in database (Demo mode)
    /// In production, connect to AISStream.io WebSocket for real data
    /// </summary>
    [HttpGet("vessels/positions")]
    public async Task<ActionResult<List<VesselPositionDto>>> GetVesselPositions(
        [FromQuery] double? minLat = null,
        [FromQuery] double? minLon = null,
        [FromQuery] double? maxLat = null,
        [FromQuery] double? maxLon = null)
    {
        try
        {
            IEnumerable<Vessel> vessels = await _vesselRepository.GetAllAsync();

            // Default to Mumbai/JNPT area if no bounds specified
            double centerLat = minLat.HasValue && maxLat.HasValue ? (minLat.Value + maxLat.Value) / 2 : 18.95;
            double centerLon = minLon.HasValue && maxLon.HasValue ? (minLon.Value + maxLon.Value) / 2 : 72.95;

            var random = new Random();
            var positions = vessels.Take(30).Select(v => new VesselPositionDto
            {
                MMSI = v.MMSI ?? $"9{v.VesselId:D8}",
                IMO = v.IMO ?? "",
                VesselName = v.VesselName,
                VesselType = v.VesselType,
                Latitude = centerLat + ((random.NextDouble() - 0.5) * 0.5),
                Longitude = centerLon + ((random.NextDouble() - 0.5) * 0.5),
                SpeedOverGround = Math.Round(random.NextDouble() * 15, 1),
                CourseOverGround = Math.Round(random.NextDouble() * 360, 0),
                NavigationStatus = GetRandomNavStatus(random),
                Destination = "JNPT Mumbai",
                ETA = DateTime.UtcNow.AddHours(random.Next(1, 48)),
                Timestamp = DateTime.UtcNow
            }).ToList();

            return Ok(positions);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error fetching vessel positions");
            return StatusCode(500, "Failed to fetch vessel positions");
        }
    }

    /// <summary>
    /// Get simulated position for a specific vessel by MMSI
    /// </summary>
    [HttpGet("vessel/{mmsi}/position")]
    public async Task<ActionResult<VesselPositionDto>> GetVesselPosition(string mmsi)
    {
        try
        {
            IEnumerable<Vessel> vessels = await _vesselRepository.GetAllAsync();
            Vessel? vessel = vessels.FirstOrDefault(v => v.MMSI == mmsi);

            if (vessel == null)
            {
                // Create a simulated position for unknown vessel
                var random = new Random();
                return Ok(new VesselPositionDto
                {
                    MMSI = mmsi,
                    VesselName = $"Vessel {mmsi}",
                    VesselType = "Unknown",
                    Latitude = 18.95 + ((random.NextDouble() - 0.5) * 0.3),
                    Longitude = 72.95 + ((random.NextDouble() - 0.5) * 0.3),
                    SpeedOverGround = Math.Round(random.NextDouble() * 12, 1),
                    CourseOverGround = Math.Round(random.NextDouble() * 360, 0),
                    NavigationStatus = "Under way using engine",
                    Timestamp = DateTime.UtcNow
                });
            }

            var rnd = new Random();
            return Ok(new VesselPositionDto
            {
                MMSI = vessel.MMSI ?? mmsi,
                IMO = vessel.IMO ?? "",
                VesselName = vessel.VesselName,
                VesselType = vessel.VesselType,
                Latitude = 18.95 + ((rnd.NextDouble() - 0.5) * 0.3),
                Longitude = 72.95 + ((rnd.NextDouble() - 0.5) * 0.3),
                SpeedOverGround = Math.Round(rnd.NextDouble() * 12, 1),
                CourseOverGround = Math.Round(rnd.NextDouble() * 360, 0),
                NavigationStatus = GetRandomNavStatus(rnd),
                Destination = "JNPT Mumbai",
                ETA = DateTime.UtcNow.AddHours(rnd.Next(1, 24)),
                Timestamp = DateTime.UtcNow
            });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error fetching vessel position for MMSI {MMSI}", mmsi);
            return StatusCode(500, "Failed to fetch vessel position");
        }
    }

    /// <summary>
    /// Get vessel details by MMSI
    /// </summary>
    [HttpGet("vessel/{mmsi}/details")]
    public async Task<ActionResult<VesselDetailsDto>> GetVesselDetails(string mmsi)
    {
        try
        {
            IEnumerable<Vessel> vessels = await _vesselRepository.GetAllAsync();
            Vessel? vessel = vessels.FirstOrDefault(v => v.MMSI == mmsi);

            return vessel == null
                ? (ActionResult<VesselDetailsDto>)NotFound($"Vessel with MMSI {mmsi} not found")
                : (ActionResult<VesselDetailsDto>)Ok(new VesselDetailsDto
                {
                    MMSI = vessel.MMSI ?? mmsi,
                    IMO = vessel.IMO ?? "",
                    VesselName = vessel.VesselName,
                    CallSign = "", // Not in current model
                    VesselType = vessel.VesselType ?? "Unknown",
                    Flag = "Unknown", // Not in current model
                    LOA = (double)(vessel.LOA ?? 0),
                    Beam = (double)(vessel.Beam ?? 0),
                    Draft = (double)(vessel.Draft ?? 0),
                    GrossTonnage = vessel.GrossTonnage ?? (int)((vessel.LOA ?? 100) * (vessel.Beam ?? 20) * 2.5m),
                    DeadWeight = (int)((vessel.LOA ?? 100) * (vessel.Beam ?? 20) * 3.5m)
                });
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error fetching vessel details for MMSI {MMSI}", mmsi);
            return StatusCode(500, "Failed to fetch vessel details");
        }
    }

    /// <summary>
    /// Get simulated port congestion data
    /// </summary>
    [HttpGet("port/{portCode}/congestion")]
    public ActionResult<PortCongestionDto> GetPortCongestion(string portCode)
    {
        var random = new Random();
        string portName = portCode switch
        {
            "INMUN" => "JNPT Mumbai",
            "INBOM" => "Mumbai Port Trust",
            "INKOC" => "Kochi Port",
            "INCHE" => "Chennai Port",
            "INVTZ" => "Visakhapatnam Port",
            _ => portCode
        };

        return Ok(new PortCongestionDto
        {
            PortCode = portCode,
            PortName = portName,
            VesselsAtPort = random.Next(15, 35),
            VesselsAtAnchorage = random.Next(5, 20),
            ExpectedArrivals24h = random.Next(8, 18),
            ExpectedDepartures24h = random.Next(6, 15),
            AverageWaitTimeHours = Math.Round((random.NextDouble() * 24) + 4, 1),
            CongestionLevel = new[] { "Low", "Medium", "High" }[random.Next(3)],
            LastUpdated = DateTime.UtcNow
        });
    }

    /// <summary>
    /// Get expected arrivals for a port (simulated)
    /// </summary>
    [HttpGet("port/{portCode}/arrivals")]
    public async Task<ActionResult<List<ExpectedArrivalDto>>> GetExpectedArrivals(
        string portCode,
        [FromQuery] int hours = 48)
    {
        try
        {
            IEnumerable<Vessel> vessels = await _vesselRepository.GetAllAsync();
            var random = new Random();

            var arrivals = vessels.Take(15).Select(v => new ExpectedArrivalDto
            {
                MMSI = v.MMSI ?? $"9{v.VesselId:D8}",
                IMO = v.IMO ?? "",
                VesselName = v.VesselName,
                VesselType = v.VesselType ?? "Unknown",
                LOA = (double)(v.LOA ?? 0),
                Draft = (double)(v.Draft ?? 0),
                ExpectedArrival = DateTime.UtcNow.AddHours(random.Next(1, hours)),
                Origin = new[] { "Singapore", "Dubai", "Colombo", "Shanghai", "Rotterdam" }[random.Next(5)],
                DistanceToGo = Math.Round((random.NextDouble() * 500) + 10, 1)
            }).OrderBy(a => a.ExpectedArrival).ToList();

            return Ok(arrivals);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Error fetching expected arrivals for port {PortCode}", portCode);
            return StatusCode(500, "Failed to fetch expected arrivals");
        }
    }

    /// <summary>
    /// Get AIS service status and info
    /// </summary>
    [HttpGet("status")]
    public ActionResult GetAISStatus()
    {
        return Ok(new
        {
            Mode = "Demo/Simulation",
            Message = "Using simulated AIS data based on database vessels",
            ProductionSetup = new
            {
                Provider = "AISStream.io",
                Website = "https://aisstream.io",
                Type = "WebSocket (FREE)",
                Instructions = "1. Register at aisstream.io for free API key, 2. Add key to appsettings.json under AISStream:ApiKey, 3. Connect via WebSocket for real-time data"
            },
            AlternativeProviders = new[]
            {
                new { Name = "AISHub", Url = "https://www.aishub.net", Type = "Free (requires AIS feed contribution)" },
                new { Name = "MarineTraffic", Url = "https://www.marinetraffic.com", Type = "Paid API" }
            }
        });
    }

    private static string GetRandomNavStatus(Random random)
    {
        string[] statuses = new[]
        {
            "Under way using engine",
            "At anchor",
            "Moored",
            "Restricted maneuverability",
            "Constrained by draught"
        };
        return statuses[random.Next(statuses.Length)];
    }
}

// DTOs for AIS Controller
public class VesselPositionDto
{
    public string MMSI { get; set; } = string.Empty;
    public string IMO { get; set; } = string.Empty;
    public string VesselName { get; set; } = string.Empty;
    public string VesselType { get; set; } = string.Empty;
    public double Latitude { get; set; }
    public double Longitude { get; set; }
    public double SpeedOverGround { get; set; }
    public double CourseOverGround { get; set; }
    public string NavigationStatus { get; set; } = string.Empty;
    public string Destination { get; set; } = string.Empty;
    public DateTime? ETA { get; set; }
    public DateTime Timestamp { get; set; }
}

public class VesselDetailsDto
{
    public string MMSI { get; set; } = string.Empty;
    public string IMO { get; set; } = string.Empty;
    public string VesselName { get; set; } = string.Empty;
    public string CallSign { get; set; } = string.Empty;
    public string VesselType { get; set; } = string.Empty;
    public string Flag { get; set; } = string.Empty;
    public double LOA { get; set; }
    public double Beam { get; set; }
    public double Draft { get; set; }
    public int GrossTonnage { get; set; }
    public int DeadWeight { get; set; }
}

public class PortCongestionDto
{
    public string PortCode { get; set; } = string.Empty;
    public string PortName { get; set; } = string.Empty;
    public int VesselsAtPort { get; set; }
    public int VesselsAtAnchorage { get; set; }
    public int ExpectedArrivals24h { get; set; }
    public int ExpectedDepartures24h { get; set; }
    public double AverageWaitTimeHours { get; set; }
    public string CongestionLevel { get; set; } = string.Empty;
    public DateTime LastUpdated { get; set; }
}

public class ExpectedArrivalDto
{
    public string MMSI { get; set; } = string.Empty;
    public string IMO { get; set; } = string.Empty;
    public string VesselName { get; set; } = string.Empty;
    public string VesselType { get; set; } = string.Empty;
    public double LOA { get; set; }
    public double Draft { get; set; }
    public DateTime ExpectedArrival { get; set; }
    public string Origin { get; set; } = string.Empty;
    public double DistanceToGo { get; set; }
}
