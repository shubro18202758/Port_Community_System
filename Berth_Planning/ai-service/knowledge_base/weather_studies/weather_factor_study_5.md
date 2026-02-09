# Weather Factor Study 5 - Impact Analysis

**Data Source**: WEATHER_DATA table
**Category**: Weather Studies

## Weather Impact Factor: 50% Severity

### Conditions
- Wind Speed: 45 knots
- Wave Height: 4.5 meters
- Visibility: 1000 meters

### Query Example
```sql
SELECT WindSpeed, WaveHeight, Visibility, WeatherCondition
FROM WEATHER_DATA
WHERE RecordedAt >= DATEADD(HOUR, -24, GETDATE())
    AND (WindSpeed BETWEEN 40 AND 50)
ORDER BY RecordedAt DESC;
```

**Historical Impact** (2024 data):
- Vessels affected: 125
- Average delay: 3.5 hours
- Operations suspended: 0

**AI Prediction Model**: Delay factor = 0.75 × (wind_speed / 25) + 0.5 × (wave_height / 3)

**Keywords**: WEATHER_DATA, weather impact, wind speed, wave height, delay prediction, weather factors
