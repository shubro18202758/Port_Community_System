# Weather Factor Study 4 - Impact Analysis

**Data Source**: WEATHER_DATA table
**Category**: Weather Studies

## Weather Impact Factor: 40% Severity

### Conditions
- Wind Speed: 40 knots
- Wave Height: 4. meters
- Visibility: 1200 meters

### Query Example
```sql
SELECT WindSpeed, WaveHeight, Visibility, WeatherCondition
FROM WEATHER_DATA
WHERE RecordedAt >= DATEADD(HOUR, -24, GETDATE())
    AND (WindSpeed BETWEEN 35 AND 45)
ORDER BY RecordedAt DESC;
```

**Historical Impact** (2024 data):
- Vessels affected: 110
- Average delay: 3. hours
- Operations suspended: 0

**AI Prediction Model**: Delay factor = 0.59999999999999998 × (wind_speed / 25) + 0.40000000000000002 × (wave_height / 3)

**Keywords**: WEATHER_DATA, weather impact, wind speed, wave height, delay prediction, weather factors
