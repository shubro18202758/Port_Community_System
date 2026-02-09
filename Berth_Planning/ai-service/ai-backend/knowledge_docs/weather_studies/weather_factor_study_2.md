# Weather Factor Study 2 - Impact Analysis

**Data Source**: WEATHER_DATA table
**Category**: Weather Studies

## Weather Impact Factor: 20% Severity

### Conditions
- Wind Speed: 30 knots
- Wave Height: 3. meters
- Visibility: 1600 meters

### Query Example
```sql
SELECT WindSpeed, WaveHeight, Visibility, WeatherCondition
FROM WEATHER_DATA
WHERE RecordedAt >= DATEADD(HOUR, -24, GETDATE())
    AND (WindSpeed BETWEEN 25 AND 35)
ORDER BY RecordedAt DESC;
```

**Historical Impact** (2024 data):
- Vessels affected: 80
- Average delay: 2. hours
- Operations suspended: 0

**AI Prediction Model**: Delay factor = 0.29999999999999999 × (wind_speed / 25) + 0.20000000000000001 × (wave_height / 3)

**Keywords**: WEATHER_DATA, weather impact, wind speed, wave height, delay prediction, weather factors
