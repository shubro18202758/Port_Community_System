# Vessel Performance History - Repeat Customer Analysis

**Document Type**: Historical Analysis
**Data Source**: VESSEL_HISTORY table
**Category**: Historical Logs

---

## Repeat Vessel Analysis

```sql
SELECT
    v.VesselName,
    v.VesselType,
    COUNT(vh.VisitId) AS TotalVisits,
    AVG(vh.DwellTime) / 60.0 AS AvgDwellHours,
    AVG(vh.WaitingTime) AS AvgWaitMinutes
FROM VESSEL_HISTORY vh
JOIN VESSELS v ON vh.VesselId = v.VesselId
GROUP BY v.VesselId, v.VesselName, v.VesselType
HAVING COUNT(vh.VisitId) > 5
ORDER BY TotalVisits DESC;
```

**Top Repeat Customers** (2023-2024):
- MSC Aurora: 42 visits, 18.2h avg dwell, 15min avg wait
- Maersk Edinburgh: 38 visits, 19.4h avg dwell, 18min avg wait
- OOCL Harmony: 34 visits, 17.8h avg dwell, 22min avg wait

**Insight**: Frequent visitors show 20% faster turnaround due to operational familiarity.

**Keywords**: VESSEL_HISTORY, repeat customers, vessel performance, historical visits
