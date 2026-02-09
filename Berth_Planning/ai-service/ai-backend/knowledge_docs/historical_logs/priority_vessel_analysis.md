# Priority Vessel Analysis - High-Priority Operations

**Data Source**: VESSEL_SCHEDULE table (Priority column)
**Category**: Historical Logs

## Priority System (from VESSEL_SCHEDULE)

**Priority Levels**:
- **1 (High)**: Government vessels, emergency, window vessels
- **2 (Medium)**: Regular scheduled services, perishable cargo
- **3 (Low)**: Tramp vessels, general cargo

```sql
SELECT
    vs.Priority,
    COUNT(*) AS VesselCount,
    AVG(vs.WaitingTime) AS AvgWaitMinutes,
    AVG(vs.DwellTime) / 60.0 AS AvgDwellHours
FROM VESSEL_SCHEDULE vs
WHERE vs.Status = 'Departed' AND YEAR(vs.ETD) = 2024
GROUP BY vs.Priority
ORDER BY vs.Priority;
```

**Impact**: Priority 1 vessels wait 58% less than Priority 2, receive preferential berth assignments.

**AI Agent Rule**: Always check VESSEL_SCHEDULE.Priority when resolving berth conflicts. Priority 1 overrides Priority 2/3.

**Keywords**: priority vessels, VESSEL_SCHEDULE, Priority column, high-priority operations, window vessels
