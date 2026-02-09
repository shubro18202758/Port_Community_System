# Fog and Visibility Impact - Navigation Safety Analysis

**Document Type**: Weather Impact Study
**Data Source**: WEATHER_DATA, VESSEL_SCHEDULE tables
**Category**: Weather Studies

---

## Visibility Constraints

**WEATHER_DATA Schema**:
- Visibility column: meters (numeric)
- Critical threshold: <500m (navigation hazard)
- Warning threshold: <1000m (reduced speed required)

**From WEATHER_DATA (2024)**:
```sql
SELECT
    CASE
        WHEN Visibility < 500 THEN 'Critical (<500m)'
        WHEN Visibility < 1000 THEN 'Warning (500-1000m)'
        ELSE 'Normal (>1000m)'
    END AS VisibilityCategory,
    COUNT(*) AS HourCount,
    AVG(DATEDIFF(MINUTE, vs.ETA, vs.ATA)) AS AvgDelay Minutes
FROM WEATHER_DATA wd
LEFT JOIN VESSEL_SCHEDULE vs ON CAST(wd.RecordedAt AS DATE) = CAST(vs.ETA AS DATE)
GROUP BY CASE WHEN Visibility < 500 THEN 'Critical' WHEN Visibility < 1000 THEN 'Warning' ELSE 'Normal' END;
```

**Fog Events (2024)**: 23 events, avg duration 4.7 hours
**Impact**: 142 vessels delayed, avg 2.3 hours per vessel

**Seasonal Pattern**: Most fog events in October-November (autumn, 65% of annual fog)

**AI Agent Recommendation**: Query WEATHER_DATA.Visibility and add delay factor if <1000m.

**Keywords**: WEATHER_DATA, visibility, fog, navigation safety, weather delays
