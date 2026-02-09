# Seasonal Weather Patterns - Annual Climate Analysis

**Document Type**: Weather Impact Study
**Data Source**: WEATHER_DATA table (2024 full year)
**Category**: Weather Studies

---

## Monthly Weather Summary

```sql
SELECT
    MONTH(RecordedAt) AS Month,
    AVG(WindSpeed) AS AvgWindKnots,
    MAX(WindSpeed) AS MaxWindKnots,
    AVG(WaveHeight) AS AvgWaveMeters,
    MAX(WaveHeight) AS MaxWaveMeters,
    AVG(Visibility) AS AvgVisibilityMeters,
    COUNT(CASE WHEN WindSpeed > 25 THEN 1 END) AS StormHours
FROM WEATHER_DATA
WHERE YEAR(RecordedAt) = 2024
GROUP BY MONTH(RecordedAt)
ORDER BY Month;
```

**Storm Season**: July-September (summer storms, tropical systems)
**Fog Season**: October-November (autumn, temperature inversions)
**Calm Season**: April-June (spring, stable conditions)

**AI Agent Recommendation**: Factor seasonal weather patterns into ETA predictions for vessels arriving 7+ days out.

**Keywords**: WEATHER_DATA, seasonal patterns, monthly weather, storm season, fog season, climate analysis
