# AIS Tracking Patterns - Vessel Position Analysis

**Data Source**: AIS_DATA table
**Category**: Historical Logs

## AIS Data Usage

```sql
SELECT v.VesselName, ais.Latitude, ais.Longitude, ais.Speed, ais.Heading, ais.RecordedAt
FROM AIS_DATA ais
JOIN VESSELS v ON ais.VesselId = v.VesselId
WHERE ais.RecordedAt >= DATEADD(HOUR, -24, GETDATE())
ORDER BY ais.RecordedAt DESC;
```

**Update Frequency**: Every 2-10 minutes (Class A), 3-6 minutes (Class B)
**Coverage**: 100% for vessels >300 GT
**Use Cases**: Real-time ETA prediction, speed analysis, route tracking

**AI Integration**: Query AIS_DATA for current vessel position and speed. Calculate distance to port using Haversine formula. Estimate ETA based on current speed + weather factors.

**Keywords**: AIS_DATA, vessel tracking, GPS coordinates, real-time position, speed, heading
