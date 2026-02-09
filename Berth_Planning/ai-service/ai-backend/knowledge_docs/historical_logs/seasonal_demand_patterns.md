# Seasonal Demand Patterns - Annual Port Activity Analysis

**Document Type**: Historical Analysis - Seasonal Trends
**Data Source**: VESSEL_SCHEDULE, VESSELS tables (2024)
**Category**: Historical Logs

---

## Monthly Vessel Arrivals

```sql
SELECT
    MONTH(vs.ETA) AS Month,
    COUNT(*) AS TotalVessels,
    AVG(vs.WaitingTime) AS AvgWaitMinutes,
    SUM(vs.DwellTime) / 60.0 AS TotalBerthHours
FROM VESSEL_SCHEDULE vs
WHERE YEAR(vs.ETA) = 2024
GROUP BY MONTH(vs.ETA)
ORDER BY Month;
```

**Peak Season** (July-August):
- 1,610 vessels total (15% above annual average)
- 35 min avg waiting time (+25% vs annual)
- Berth utilization: 87% (near capacity)

**Low Season** (February, December):
- 1,208 vessels total (10% below average)
- 22 min avg waiting time (-21% vs annual)
- Berth utilization: 73%

---

## Vessel Type Seasonality

**Container Vessels**:
- Peak: July-August (back-to-school, holiday inventory buildup)
- Low: January-February (post-holiday slowdown)

**Bulk Carriers**:
- Peak: April-May (spring grain harvest), October (autumn harvest)
- Low: December-January (winter shipping pause)

**Tankers**:
- Stable year-round (petroleum demand consistent)
- Slight peak: June-July (summer driving season)

---

**Keywords**: seasonal patterns, monthly trends, peak season, vessel demand, VESSEL_SCHEDULE, annual analysis, port utilization
