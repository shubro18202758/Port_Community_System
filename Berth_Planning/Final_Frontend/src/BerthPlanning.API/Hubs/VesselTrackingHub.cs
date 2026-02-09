using Microsoft.AspNetCore.SignalR;

namespace BerthPlanning.API.Hubs;

public class VesselTrackingHub : Hub
{
    private readonly ILogger<VesselTrackingHub> _logger;

    public VesselTrackingHub(ILogger<VesselTrackingHub> logger)
    {
        _logger = logger;
    }

    public async Task SubscribeToPortArea(string portCode, double minLat, double minLon, double maxLat, double maxLon)
    {
        await Groups.AddToGroupAsync(Context.ConnectionId, $"port_{portCode}");
        _logger.LogInformation("Client {ConnectionId} subscribed to port {PortCode} area", Context.ConnectionId, portCode);
    }

    public async Task SubscribeToVessels(int[] vesselIds)
    {
        foreach (var vesselId in vesselIds)
        {
            await Groups.AddToGroupAsync(Context.ConnectionId, $"vessel_{vesselId}");
        }
        _logger.LogInformation("Client {ConnectionId} subscribed to {Count} vessels", Context.ConnectionId, vesselIds.Length);
    }

    public async Task UnsubscribeFromPortArea(string portCode)
    {
        await Groups.RemoveFromGroupAsync(Context.ConnectionId, $"port_{portCode}");
        _logger.LogInformation("Client {ConnectionId} unsubscribed from port {PortCode}", Context.ConnectionId, portCode);
    }

    public override async Task OnConnectedAsync()
    {
        _logger.LogInformation("Client connected: {ConnectionId}", Context.ConnectionId);
        await base.OnConnectedAsync();
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        _logger.LogInformation("Client disconnected: {ConnectionId}", Context.ConnectionId);
        await base.OnDisconnectedAsync(exception);
    }
}

// DTO for vessel position updates
public class VesselPositionUpdate
{
    public int? VesselId { get; set; }
    public string Mmsi { get; set; } = string.Empty;
    public string VesselName { get; set; } = string.Empty;
    public string? Imo { get; set; }
    public string? VesselType { get; set; }
    public double Latitude { get; set; }
    public double Longitude { get; set; }
    public double Speed { get; set; }
    public double Course { get; set; }
    public double? Heading { get; set; }
    public string? Destination { get; set; }
    public DateTime? DeclaredETA { get; set; }
    public DateTime? PredictedETA { get; set; }
    public double? DistanceToPort { get; set; }
    public string? Phase { get; set; }
    public DateTime Timestamp { get; set; }
}
