# Storm Impact Analysis - Weather Delay Patterns

**Document Type**: Weather Impact Study
**Data Source**: WEATHER_DATA, VESSEL_SCHEDULE, AIS_DATA tables
**Analysis Period**: 2023-2024 (24 months, 18 storm events)
**Category**: Weather Studies

---

## Executive Summary

Storm events cause significant disruptions to port operations. Analysis of 18 major storms (wind >25 knots, wave height >3m) in 2023-2024 reveals:
- **Average delay per storm**: 3.5 hours per vessel
- **Total delays**: 2,847 vessel-hours lost
- **Cascade effects**: Storms create 2-4 day backlog
- **Economic impact**: ~$850K in demurrage costs per storm event

---

## Storm Classification and Impact

### Query Pattern
```sql
SELECT
    wd.WindSpeed,
    wd.WaveHeight,
    wd.Visibility,
    COUNT(vs.ScheduleId) AS VesselsAffected,
    AVG(DATEDIFF(MINUTE, vs.ETA, vs.ATA)) AS AvgDelayMinutes
FROM WEATHER_DATA wd
JOIN VESSEL_SCHEDULE vs ON CAST(wd.RecordedAt AS DATE) = CAST(vs.ETA AS DATE)
WHERE wd.WindSpeed > 25 OR wd.WaveHeight > 3
GROUP BY wd.WindSpeed, wd.WaveHeight, wd.Visibility;
```

**Storm Severity Categories**:

| Severity | Wind (knots) | Wave Height (m) | Avg Delay | Operations |
|----------|--------------|-----------------|-----------|------------|
| **Moderate** | 25-35 | 3-4 | 2.5 hours | Partial suspension |
| **Severe** | 35-45 | 4-6 | 4.2 hours | Most ops suspended |
| **Extreme** | >45 | >6 | 8+ hours | Complete shutdown |

---

## Historical Storm Events (2024)

### Storm Event: August 15-17, 2024
```sql
SELECT * FROM WEATHER_DATA
WHERE RecordedAt BETWEEN '2024-08-15' AND '2024-08-17'
    AND (WindSpeed > 35 OR WaveHeight > 4);
```

**Conditions**:
- Peak wind: 42 knots (Aug 16, 14:00)
- Peak wave: 5.2 meters
- Visibility: <500m (fog + rain)
- Duration: 36 hours

**Impact** (from VESSEL_SCHEDULE):
- 47 vessels delayed (avg 4.8 hours each)
- 12 vessels diverted to anchorage
- 3 vessels rerouted to alternate port
- Backlog cleared: 72 hours post-storm

**AI Agent Insight**: When `WEATHER_DATA.WindSpeed > 35`, expect 4-5 hour delays + 2-3 day recovery period.

---

## Weather-ETA Correlation

### Predictive Model (from historical data)
```python
# ETA delay calculation based on weather
def calculate_weather_delay(wind_speed, wave_height, visibility):
    delay_hours = 0

    # Wind impact
    if wind_speed > 45:
        delay_hours += 8.0  # Extreme - full shutdown
    elif wind_speed > 35:
        delay_hours += 4.2  # Severe
    elif wind_speed > 25:
        delay_hours += 2.5  # Moderate

    # Wave impact (additional)
    if wave_height > 6:
        delay_hours += 3.0
    elif wave_height > 4:
        delay_hours += 1.5
    elif wave_height > 3:
        delay_hours += 0.8

    # Visibility impact (fog)
    if visibility < 500:
        delay_hours += 2.0
    elif visibility < 1000:
        delay_hours += 0.5

    return delay_hours
```

**AI Agent Recommendation**: Query WEATHER_DATA forecast and apply delay model to PredictedETA.

---

## Crane Operation Suspension Rules

**From ALERTS_NOTIFICATIONS and BERTH_MAINTENANCE**:

| Weather Condition | Crane Operation | Historical Events |
|-------------------|-----------------|-------------------|
| Wind <25 knots | Normal operations | 8,590 vessel-days |
| Wind 25-35 knots | Reduced speed (50%) | 142 vessel-days |
| Wind 35-40 knots | Suspended (safety) | 28 vessel-days |
| Wind >40 knots | Full shutdown | 8 vessel-days |

**Query Example**:
```sql
-- Check if crane operations possible
SELECT
    wd.WindSpeed,
    CASE
        WHEN wd.WindSpeed < 25 THEN 'Normal'
        WHEN wd.WindSpeed < 35 THEN 'Reduced'
        WHEN wd.WindSpeed < 40 THEN 'Suspended'
        ELSE 'Shutdown'
    END AS CraneStatus
FROM WEATHER_DATA wd
WHERE wd.RecordedAt >= DATEADD(HOUR, -1, GETDATE())
ORDER BY wd.RecordedAt DESC;
```

---

## Berth-Specific Weather Vulnerability

**From BERTHS table + WEATHER_DATA correlation**:

| Berth | Exposure | Critical Wind Dir | Threshold (knots) | 2024 Suspensions |
|-------|----------|-------------------|-------------------|------------------|
| **A1** | Moderate | Northwest | 35 | 3 events |
| **A2** | Moderate | Northwest | 35 | 3 events |
| **C1** (Tanker) | High | West | 30 | 7 events (more cautious) |
| **D1** (RoRo) | Low | Protected | 40 | 1 event |
| **E1** (Bulk) | High | Southwest | 30 | 6 events |

**AI Agent Recommendation**: When wind >30 knots from vulnerable direction, consider sheltered berths (D1/D2) for assignments.

---

## Integration with AIS_DATA

### Vessel Position Tracking During Storms
```sql
SELECT
    v.VesselName,
    ais.Latitude,
    ais.Longitude,
    ais.Speed,
    ais.Heading,
    wd.WindSpeed,
    wd.WaveHeight
FROM AIS_DATA ais
JOIN VESSELS v ON ais.VesselId = v.VesselId
JOIN WEATHER_DATA wd ON ABS(DATEDIFF(MINUTE, ais.RecordedAt, wd.RecordedAt)) < 30
WHERE wd.WindSpeed > 35
ORDER BY ais.RecordedAt;
```

**Observed Patterns**:
- Vessels reduce speed by 30-50% in storm conditions
- Some vessels anchor offshore, waiting for weather improvement
- Deep-draft vessels more cautious (grounding risk with high waves)

---

## AI Agent Query Patterns

### For ETA Predictor Agent
```sql
-- Get current weather conditions
SELECT TOP 1
    WindSpeed,
    WaveHeight,
    Visibility,
    WeatherCondition
FROM WEATHER_DATA
WHERE RecordedAt >= DATEADD(HOUR, -1, GETDATE())
ORDER BY RecordedAt DESC;

-- Get forecast (if available)
SELECT * FROM WEATHER_DATA
WHERE RecordedAt BETWEEN GETDATE() AND DATEADD(HOUR, 24, GETDATE())
    AND WeatherCondition LIKE '%forecast%';
```

### For Berth Optimizer Agent
```sql
-- Check if berth exposed to current wind direction
SELECT
    b.BerthName,
    b.Exposure,
    wd.WindSpeed,
    wd.WindDirection,
    CASE
        WHEN wd.WindSpeed > 35 AND b.Exposure = 'High' THEN 'Avoid'
        WHEN wd.WindSpeed > 30 AND b.Exposure = 'Moderate' THEN 'Caution'
        ELSE 'OK'
    END AS RecommendedAction
FROM BERTHS b
CROSS JOIN (
    SELECT TOP 1 * FROM WEATHER_DATA
    ORDER BY RecordedAt DESC
) wd;
```

---

**Keywords**: storm impact, weather delays, wind speed, wave height, WEATHER_DATA table, crane suspension, vessel delays, storm events, ETA prediction, weather forecasting, berth exposure
