namespace BerthPlanning.Core.Interfaces;

/// <summary>
/// AISStream.io Integration Service - FREE AIS data via WebSocket
/// Register at https://aisstream.io to get your free API key
/// </summary>
public interface IAISStreamService
{
    Task<bool> ConnectAsync(CancellationToken cancellationToken = default);
    Task DisconnectAsync();
    Task SubscribeToAreaAsync(double minLat, double minLon, double maxLat, double maxLon);
    Task SubscribeToVesselsAsync(List<string> mmsiList);
    bool IsConnected { get; }
    event EventHandler<AISPositionUpdate>? OnPositionUpdate;
    event EventHandler<AISVesselData>? OnVesselDataUpdate;
}

public class AISPositionUpdate
{
    public string MMSI { get; set; } = string.Empty;
    public string VesselName { get; set; } = string.Empty;
    public double Latitude { get; set; }
    public double Longitude { get; set; }
    public double SpeedOverGround { get; set; } // knots
    public double CourseOverGround { get; set; } // degrees
    public double TrueHeading { get; set; }
    public int NavigationStatus { get; set; }
    public DateTime Timestamp { get; set; }
    public string Destination { get; set; } = string.Empty;
    public DateTime? ETA { get; set; }
}

public class AISVesselData
{
    public string MMSI { get; set; } = string.Empty;
    public string IMO { get; set; } = string.Empty;
    public string VesselName { get; set; } = string.Empty;
    public string CallSign { get; set; } = string.Empty;
    public int ShipType { get; set; }
    public string ShipTypeName { get; set; } = string.Empty;
    public double Length { get; set; }
    public double Beam { get; set; }
    public double Draft { get; set; }
    public string Destination { get; set; } = string.Empty;
    public DateTime? ETA { get; set; }
}

public class AISSubscriptionRequest
{
    public string APIKey { get; set; } = string.Empty;
    public List<List<List<double>>> BoundingBoxes { get; set; } = [];
    public List<string>? FiltersShipMMSI { get; set; }
    public List<string>? FilterMessageTypes { get; set; }
}
