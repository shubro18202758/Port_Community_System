# Berth Maintenance Patterns - Scheduled Downtime Analysis

**Document Type**: Historical Analysis
**Data Source**: BERTH_MAINTENANCE table
**Category**: Historical Logs

---

## Maintenance Schedule Patterns

```sql
SELECT
    b.BerthName,
    bm.MaintenanceType,
    bm.ScheduledStart,
    bm.ScheduledEnd,
    DATEDIFF(HOUR, bm.ScheduledStart, bm.ScheduledEnd) AS MaintenanceHours,
    bm.Status
FROM BERTH_MAINTENANCE bm
JOIN BERTHS b ON bm.BerthId = b.BerthId
WHERE YEAR(bm.ScheduledStart) = 2024
ORDER BY bm.ScheduledStart;
```

**Typical Maintenance Types**:
- Crane overhaul: 10-14 days (annual)
- Fender replacement: 5-7 days (every 5-10 years)
- Bollard inspection: 4-8 hours (quarterly)
- Dredging: 7-14 days (annual)

**Impact on Scheduling**: Plan vessel assignments around maintenance windows (HARD constraint).

**Keywords**: BERTH_MAINTENANCE, maintenance windows, crane overhaul, berth downtime, scheduled maintenance
