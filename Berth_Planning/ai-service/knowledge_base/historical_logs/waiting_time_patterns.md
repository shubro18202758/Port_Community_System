# Waiting Time Patterns - Port Congestion Analysis

**Document Type**: Historical Analysis - Pre-Berthing Delays
**Data Source**: VESSEL_SCHEDULE table (WaitingTime column)
**Analysis Period**: 2024 full year
**Category**: Historical Logs

---

## Executive Summary

Analysis of 8,760 vessel arrivals in 2024 reveals waiting time patterns correlated with:
- Time of day (peak: 08:00-10:00, avg 42 min wait)
- Day of week (Monday/Friday peaks: +23% vs midweek)
- Seasonal demand (July-August: +35% waiting time)
- Weather events (storm delays create 2-4 day cascades)

**Overall Metrics**:
- Average waiting time: 28 minutes
- Median waiting time: 18 minutes
- 90th percentile: 67 minutes
- Maximum recorded: 284 minutes (storm event, Aug 2024)

---

## Hourly Waiting Time Distribution

```sql
SELECT
    DATEPART(HOUR, vs.ATA) AS ArrivalHour,
    AVG(vs.WaitingTime) AS AvgWaitMinutes,
    MAX(vs.WaitingTime) AS MaxWaitMinutes,
    COUNT(*) AS VesselCount
FROM VESSEL_SCHEDULE vs
WHERE YEAR(vs.ATA) = 2024 AND vs.WaitingTime > 0
GROUP BY DATEPART(HOUR, vs.ATA)
ORDER BY AvgWaitMinutes DESC;
```

**Peak Congestion Hours**:
- **08:00-10:00**: 42 min avg (berth turnover delays)
- **14:00-16:00**: 38 min avg (shift change impact)
- **20:00-22:00**: 28 min avg (tidal window clustering)

**Low Congestion Hours**:
- **02:00-04:00**: 8 min avg (optimal arrival time)
- **10:00-12:00**: 15 min avg (post-morning rush)

---

## Vessel Priority Impact on Waiting Time

```sql
SELECT
    vs.Priority,
    AVG(vs.WaitingTime) AS AvgWaitMinutes,
    COUNT(*) AS VesselCount
FROM VESSEL_SCHEDULE vs
WHERE YEAR(vs.ATA) = 2024 AND vs.Status = 'Departed'
GROUP BY vs.Priority
ORDER BY vs.Priority;
```

**Results**:
- Priority 1 (High): 12 min avg, 1,847 vessels
- Priority 2 (Medium): 28 min avg, 5,234 vessels
- Priority 3 (Low): 45 min avg, 1,679 vessels

**Insight**: High-priority vessels wait 58% less than medium priority, 73% less than low priority.

---

## AI Agent Recommendations

**For ETA Predictor Agent**:
- Add waiting time estimates based on arrival hour
- Query: `SELECT AVG(WaitingTime) FROM VESSEL_SCHEDULE WHERE DATEPART(HOUR, ATA) = @PredictedArrivalHour`

**For Berth Optimizer Agent**:
- Suggest off-peak arrivals (02:00-04:00) for low-priority vessels
- Consider priority when resolving berth conflicts

---

**Keywords**: waiting time, port congestion, vessel queue, WaitingTime column, VESSEL_SCHEDULE, arrival delays, priority impact, hourly patterns
