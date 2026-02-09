using BerthPlanning.Core.Interfaces;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System.Net.WebSockets;
using System.Text;
using System.Text.Json;

namespace BerthPlanning.Infrastructure.Services;

/// <summary>
/// AISStream.io WebSocket Service - FREE AIS data
/// Register at https://aisstream.io to get your free API key
/// </summary>
public class AISStreamService : IAISStreamService, IDisposable
{
    private readonly ILogger<AISStreamService> _logger;
    private readonly string _apiKey;
    private ClientWebSocket? _webSocket;
    private CancellationTokenSource? _cts;
    private Task? _receiveTask;

    private const string WS_URL = "wss://stream.aisstream.io/v0/stream";

    public bool IsConnected => _webSocket?.State == WebSocketState.Open;
    public event EventHandler<AISPositionUpdate>? OnPositionUpdate;
    public event EventHandler<AISVesselData>? OnVesselDataUpdate;

    public AISStreamService(IConfiguration configuration, ILogger<AISStreamService> logger)
    {
        _logger = logger;
        _apiKey = configuration["AISStream:ApiKey"] ?? string.Empty;
    }

    public async Task<bool> ConnectAsync(CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(_apiKey))
        {
            _logger.LogWarning("AISStream API key not configured. Register at https://aisstream.io for free.");
            return false;
        }

        try
        {
            _webSocket = new ClientWebSocket();
            _cts = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);

            await _webSocket.ConnectAsync(new Uri(WS_URL), _cts.Token);
            _logger.LogInformation("Connected to AISStream.io WebSocket");

            // Start receiving messages
            _receiveTask = ReceiveMessagesAsync(_cts.Token);

            return true;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to connect to AISStream.io");
            return false;
        }
    }

    public async Task DisconnectAsync()
    {
        _cts?.Cancel();

        if (_webSocket?.State == WebSocketState.Open)
        {
            await _webSocket.CloseAsync(WebSocketCloseStatus.NormalClosure, "Closing", CancellationToken.None);
        }

        _webSocket?.Dispose();
        _webSocket = null;
        _logger.LogInformation("Disconnected from AISStream.io");
    }

    public async Task SubscribeToAreaAsync(double minLat, double minLon, double maxLat, double maxLon)
    {
        if (!IsConnected)
        {
            _logger.LogWarning("Not connected to AISStream. Call ConnectAsync first.");
            return;
        }

        var subscription = new
        {
            APIKey = _apiKey,
            BoundingBoxes = new[] {
                new[] {
                    new[] { minLat, minLon },
                    new[] { maxLat, maxLon }
                }
            },
            FilterMessageTypes = new[] { "PositionReport", "ShipStaticData" }
        };

        string json = JsonSerializer.Serialize(subscription);
        byte[] bytes = Encoding.UTF8.GetBytes(json);

        await _webSocket!.SendAsync(bytes, WebSocketMessageType.Text, true, _cts!.Token);
        _logger.LogInformation("Subscribed to AIS data for area: ({MinLat},{MinLon}) to ({MaxLat},{MaxLon})",
            minLat, minLon, maxLat, maxLon);
    }

    public async Task SubscribeToVesselsAsync(List<string> mmsiList)
    {
        if (!IsConnected)
        {
            _logger.LogWarning("Not connected to AISStream. Call ConnectAsync first.");
            return;
        }

        var subscription = new
        {
            APIKey = _apiKey,
            BoundingBoxes = new[] {
                new[] {
                    new[] { -90.0, -180.0 },
                    new[] { 90.0, 180.0 }
                }
            },
            FiltersShipMMSI = mmsiList,
            FilterMessageTypes = new[] { "PositionReport", "ShipStaticData" }
        };

        string json = JsonSerializer.Serialize(subscription);
        byte[] bytes = Encoding.UTF8.GetBytes(json);

        await _webSocket!.SendAsync(bytes, WebSocketMessageType.Text, true, _cts!.Token);
        _logger.LogInformation("Subscribed to AIS data for {Count} vessels", mmsiList.Count);
    }

    private async Task ReceiveMessagesAsync(CancellationToken cancellationToken)
    {
        byte[] buffer = new byte[8192];

        while (!cancellationToken.IsCancellationRequested && IsConnected)
        {
            try
            {
                WebSocketReceiveResult result = await _webSocket!.ReceiveAsync(buffer, cancellationToken);

                if (result.MessageType == WebSocketMessageType.Close)
                {
                    _logger.LogInformation("WebSocket closed by server");
                    break;
                }

                string json = Encoding.UTF8.GetString(buffer, 0, result.Count);
                ProcessMessage(json);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error receiving AIS message");
            }
        }
    }

    private void ProcessMessage(string json)
    {
        try
        {
            using var doc = JsonDocument.Parse(json);
            JsonElement root = doc.RootElement;

            if (!root.TryGetProperty("MessageType", out JsonElement msgType))
            {
                return;
            }

            string? messageType = msgType.GetString();

            if (messageType == "PositionReport" && root.TryGetProperty("Message", out JsonElement posMsg))
            {
                AISPositionUpdate? position = ParsePositionReport(posMsg, root);
                if (position != null)
                {
                    OnPositionUpdate?.Invoke(this, position);
                }
            }
            else if (messageType == "ShipStaticData" && root.TryGetProperty("Message", out JsonElement staticMsg))
            {
                AISVesselData? vesselData = ParseStaticData(staticMsg, root);
                if (vesselData != null)
                {
                    OnVesselDataUpdate?.Invoke(this, vesselData);
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogDebug(ex, "Error parsing AIS message");
        }
    }

    private AISPositionUpdate? ParsePositionReport(JsonElement message, JsonElement root)
    {
        try
        {
            if (!message.TryGetProperty("PositionReport", out JsonElement report))
            {
                return null;
            }

            JsonElement metaData = root.TryGetProperty("MetaData", out JsonElement meta) ? meta : default;

            return new AISPositionUpdate
            {
                MMSI = metaData.TryGetProperty("MMSI", out JsonElement mmsi) ? mmsi.GetInt64().ToString() : "",
                VesselName = metaData.TryGetProperty("ShipName", out JsonElement name) ? name.GetString() ?? "" : "",
                Latitude = report.TryGetProperty("Latitude", out JsonElement lat) ? lat.GetDouble() : 0,
                Longitude = report.TryGetProperty("Longitude", out JsonElement lon) ? lon.GetDouble() : 0,
                SpeedOverGround = report.TryGetProperty("Sog", out JsonElement sog) ? sog.GetDouble() : 0,
                CourseOverGround = report.TryGetProperty("Cog", out JsonElement cog) ? cog.GetDouble() : 0,
                TrueHeading = report.TryGetProperty("TrueHeading", out JsonElement hdg) ? hdg.GetDouble() : 0,
                NavigationStatus = report.TryGetProperty("NavigationalStatus", out JsonElement navStat) ? navStat.GetInt32() : 0,
                Timestamp = DateTime.UtcNow
            };
        }
        catch
        {
            return null;
        }
    }

    private AISVesselData? ParseStaticData(JsonElement message, JsonElement root)
    {
        try
        {
            if (!message.TryGetProperty("ShipStaticData", out JsonElement data))
            {
                return null;
            }

            JsonElement metaData = root.TryGetProperty("MetaData", out JsonElement meta) ? meta : default;

            var vesselData = new AISVesselData
            {
                MMSI = metaData.TryGetProperty("MMSI", out JsonElement mmsi) ? mmsi.GetInt64().ToString() : "",
                VesselName = data.TryGetProperty("Name", out JsonElement name) ? name.GetString() ?? "" : "",
                CallSign = data.TryGetProperty("CallSign", out JsonElement cs) ? cs.GetString() ?? "" : "",
                ShipType = data.TryGetProperty("Type", out JsonElement type) ? type.GetInt32() : 0,
                Destination = data.TryGetProperty("Destination", out JsonElement dest) ? dest.GetString() ?? "" : ""
            };

            // Parse IMO
            if (data.TryGetProperty("ImoNumber", out JsonElement imo))
            {
                vesselData.IMO = imo.GetInt64().ToString();
            }

            // Parse dimensions
            if (data.TryGetProperty("Dimension", out JsonElement dim))
            {
                double a = dim.TryGetProperty("A", out JsonElement dimA) ? dimA.GetDouble() : 0;
                double b = dim.TryGetProperty("B", out JsonElement dimB) ? dimB.GetDouble() : 0;
                double c = dim.TryGetProperty("C", out JsonElement dimC) ? dimC.GetDouble() : 0;
                double d = dim.TryGetProperty("D", out JsonElement dimD) ? dimD.GetDouble() : 0;

                vesselData.Length = a + b;
                vesselData.Beam = c + d;
            }

            // Parse draft
            if (data.TryGetProperty("MaximumStaticDraught", out JsonElement draft))
            {
                vesselData.Draft = draft.GetDouble() / 10.0; // Convert from decimeters
            }

            // Parse ETA
            if (data.TryGetProperty("Eta", out JsonElement eta))
            {
                int month = eta.TryGetProperty("Month", out JsonElement m) ? m.GetInt32() : 0;
                int day = eta.TryGetProperty("Day", out JsonElement d) ? d.GetInt32() : 0;
                int hour = eta.TryGetProperty("Hour", out JsonElement h) ? h.GetInt32() : 0;
                int minute = eta.TryGetProperty("Minute", out JsonElement min) ? min.GetInt32() : 0;

                if (month > 0 && day > 0)
                {
                    int year = DateTime.UtcNow.Year;
                    if (month < DateTime.UtcNow.Month)
                    {
                        year++;
                    }

                    vesselData.ETA = new DateTime(year, month, day, hour, minute, 0);
                }
            }

            vesselData.ShipTypeName = GetShipTypeName(vesselData.ShipType);

            return vesselData;
        }
        catch
        {
            return null;
        }
    }

    private static string GetShipTypeName(int shipType)
    {
        return shipType switch
        {
            >= 70 and <= 79 => "Cargo",
            >= 80 and <= 89 => "Tanker",
            >= 60 and <= 69 => "Passenger",
            >= 40 and <= 49 => "High Speed",
            >= 30 and <= 39 => "Fishing",
            >= 50 and <= 59 => "Tug/Pilot",
            >= 20 and <= 29 => "WIG",
            _ => "Other"
        };
    }

    public void Dispose()
    {
        _cts?.Cancel();
        _webSocket?.Dispose();
        _cts?.Dispose();
    }
}
