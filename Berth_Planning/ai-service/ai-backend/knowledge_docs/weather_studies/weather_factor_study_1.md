# Weather Factor Study 1 - Impact Analysis

**Data Source**: WEATHER_DATA table
**Category**: Weather Studies

## Weather Impact Factor: 10% Severity

### Conditions
- Wind Speed: 25 knots
- Wave Height: 2.5 meters
- Visibility: 1800 meters

### Query Example
```sql
SELECT WindSpeed, WaveHeight, Visibility, WeatherCondition
FROM WEATHER_DATA
WHERE RecordedAt >= DATEADD(HOUR, -24, GETDATE())
    AND (WindSpeed BETWEEN 20 AND 30)
ORDER BY RecordedAt DESC;
```

**Historical Impact** (2024 data):
- Vessels affected: 65
- Average delay: 1.5 hours
- Operations suspended: 0

**AI Prediction Model**: Delay factor = 0.14999999999999999 × (wind_speed / 25) + 0.10000000000000001 × (wave_height / 3)

**Keywords**: WEATHER_DATA, weather impact, wind speed, wave height, delay prediction, weather factors
