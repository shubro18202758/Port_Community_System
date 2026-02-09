# Weather Factor Study 6 - Impact Analysis

**Data Source**: WEATHER_DATA table
**Category**: Weather Studies

## Weather Impact Factor: 60% Severity

### Conditions
- Wind Speed: 50 knots
- Wave Height: 5. meters
- Visibility: 800 meters

### Query Example
```sql
SELECT WindSpeed, WaveHeight, Visibility, WeatherCondition
FROM WEATHER_DATA
WHERE RecordedAt >= DATEADD(HOUR, -24, GETDATE())
    AND (WindSpeed BETWEEN 45 AND 55)
ORDER BY RecordedAt DESC;
```

**Historical Impact** (2024 data):
- Vessels affected: 140
- Average delay: 4. hours
- Operations suspended: 0

**AI Prediction Model**: Delay factor = 0.89999999999999991 × (wind_speed / 25) + 0.60000000000000009 × (wave_height / 3)

**Keywords**: WEATHER_DATA, weather impact, wind speed, wave height, delay prediction, weather factors
