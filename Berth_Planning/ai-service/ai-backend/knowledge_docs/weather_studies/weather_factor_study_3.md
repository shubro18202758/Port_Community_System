# Weather Factor Study 3 - Impact Analysis

**Data Source**: WEATHER_DATA table
**Category**: Weather Studies

## Weather Impact Factor: 30% Severity

### Conditions
- Wind Speed: 35 knots
- Wave Height: 3.5 meters
- Visibility: 1400 meters

### Query Example
```sql
SELECT WindSpeed, WaveHeight, Visibility, WeatherCondition
FROM WEATHER_DATA
WHERE RecordedAt >= DATEADD(HOUR, -24, GETDATE())
    AND (WindSpeed BETWEEN 30 AND 40)
ORDER BY RecordedAt DESC;
```

**Historical Impact** (2024 data):
- Vessels affected: 95
- Average delay: 2.5 hours
- Operations suspended: 0

**AI Prediction Model**: Delay factor = 0.44999999999999996 × (wind_speed / 25) + 0.30000000000000004 × (wave_height / 3)

**Keywords**: WEATHER_DATA, weather impact, wind speed, wave height, delay prediction, weather factors
