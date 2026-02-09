# Historical Berth Allocation Patterns - 2024 Annual Analysis

**Document Type**: Historical Analysis - Berth Assignment Patterns
**Data Source**: VESSEL_SCHEDULE, BERTHS, VESSELS tables (Jan-Dec 2024)
**Analysis Period**: 12 months (8,760 vessel movements)
**Category**: Historical Logs

---

## Executive Summary

Analysis of 2024 berth allocation patterns reveals clear preferences and efficiency metrics across different vessel types and berth configurations. This document provides AI agents with historical context for berth assignment decisions.

**Key Findings**:
- Container vessels show 78% preference for Berths A1-A3 (4-crane configuration)
- Bulk carriers achieve 15% faster turnaround at Berths E1-E2 (specialized equipment)
- RoRo vessels require Berths D1-D2 (dedicated ramp access)
- Peak utilization: Berths A1 (87%), A2 (85%), E1 (82%)

---

## Container Vessel Allocation Patterns

### Preferred Berths (from BERTHS table)
**Query**: `SELECT BerthName, BerthType, NumberOfCranes FROM BERTHS WHERE BerthType = 'Container'`

| Berth | Crane Count | 2024 Usage | Avg Dwell Time | Utilization % |
|-------|-------------|------------|----------------|---------------|
| **A1** | 4 cranes | 1,247 vessels | 18.2 hours | 87% |
| **A2** | 4 cranes | 1,189 vessels | 18.5 hours | 85% |
| **A3** | 3 cranes | 892 vessels | 21.3 hours | 72% |
| **A4** | 3 cranes | 734 vessels | 22.1 hours | 68% |

### Vessel Size Distribution (from VESSELS table)
```sql
SELECT
    CASE
        WHEN LOA < 200 THEN 'Small (LOA < 200m)'
        WHEN LOA BETWEEN 200 AND 300 THEN 'Medium (200-300m)'
        ELSE 'Large (LOA > 300m)'
    END AS SizeCategory,
    COUNT(*) AS Vessels,
    AVG(DwellTime) AS AvgDwellHours
FROM VESSEL_SCHEDULE vs
JOIN VESSELS v ON vs.VesselId = v.VesselId
WHERE v.VesselType = 'Container' AND YEAR(vs.ETD) = 2024
GROUP BY CASE WHEN LOA < 200 THEN 'Small' WHEN LOA BETWEEN 200 AND 300 THEN 'Medium' ELSE 'Large' END;
```

**Results**:
- Small (LOA < 200m): 1,234 vessels, avg 14.2 hours dwell
- Medium (200-300m): 2,847 vessels, avg 18.7 hours dwell
- Large (LOA > 300m): 981 vessels, avg 26.3 hours dwell

### Assignment Logic Insights
**Historical Pattern**: 94% of container vessels with LOA > 280m were assigned to Berth A1 or A2 (longest berths: 320m and 310m respectively).

**Reasoning**: Large vessels require:
- Longer berth length (A1: 320m, A2: 310m accommodate up to 300m LOA safely)
- 4-crane configuration for faster turnaround (target: <20 hours for 2,000+ TEU)
- Deeper draft capability (A1/A2: 15m vs A3/A4: 12m)

**AI Agent Recommendation**: When `vessel.loa > 280 AND vessel.type = 'Container'`, prioritize Berth A1 or A2 for assignment.

---

## Bulk Carrier Allocation Patterns

### Preferred Berths (from BERTHS table)
**Query**: `SELECT * FROM BERTHS WHERE BerthType = 'Bulk'`

| Berth | Specialization | 2024 Usage | Avg Dwell Time | Utilization % |
|-------|----------------|------------|----------------|---------------|
| **E1** | Dry bulk (grain) | 423 vessels | 32.5 hours | 82% |
| **E2** | Ore/coal | 398 vessels | 36.7 hours | 78% |
| **E3** | General bulk | 267 vessels | 28.9 hours | 64% |

### Cargo Type Matching (from VESSEL_SCHEDULE)
**Historical Data**: Mismatched berth assignments resulted in 12% longer dwell times.

**Example**:
- Grain vessels at E1 (specialized grain conveyor): 32.5 hours avg
- Grain vessels at E2 (ore-focused berth): 38.2 hours avg (+17.5% longer)

**AI Agent Recommendation**: Query `BERTHS.BerthSpecialization` and match with `VESSELS.PrimaryCargo` for optimal assignment.

---

## RoRo Vessel Allocation Patterns

### Dedicated Berths (from BERTHS table)
**Query**: `SELECT * FROM BERTHS WHERE HasRoRoRamp = 1`

| Berth | Ramp Type | 2024 Usage | Avg Dwell Time | Utilization % |
|-------|-----------|------------|----------------|---------------|
| **D1** | 50-ton capacity | 234 vessels | 12.3 hours | 58% |
| **D2** | 80-ton capacity | 198 vessels | 14.7 hours | 52% |

**Critical Constraint**: RoRo vessels CANNOT berth at non-RoRo berths (100% hard constraint).

**AI Agent Recommendation**: `IF vessel.type = 'RoRo' THEN berth.has_roro_ramp = TRUE` (mandatory filter).

---

## Tanker Allocation Patterns

### Preferred Berths (from BERTHS table)
**Query**: `SELECT * FROM BERTHS WHERE BerthType = 'Liquid'`

| Berth | Pipeline Type | 2024 Usage | Avg Dwell Time | Utilization % |
|-------|---------------|------------|----------------|---------------|
| **C1** | Crude oil | 156 vessels | 28.4 hours | 69% |
| **C2** | Chemical | 142 vessels | 24.8 hours | 61% |
| **C3** | LNG | 87 vessels | 31.2 hours | 54% |

**Dangerous Goods Segregation** (from VESSEL_SCHEDULE):
- Chemical tankers at C2: 100% success rate (no incidents)
- Chemical tankers at C1: 3 incidents (pipeline contamination risk)

**AI Agent Recommendation**: Strict cargo type matching for tanker berths (safety-critical).

---

## Peak Hour Analysis

### Hourly Arrival Distribution (from VESSEL_SCHEDULE)
```sql
SELECT
    DATEPART(HOUR, ETA) AS Hour,
    COUNT(*) AS Arrivals,
    AVG(WaitingTime) AS AvgWaitMinutes
FROM VESSEL_SCHEDULE
WHERE YEAR(ETA) = 2024
GROUP BY DATEPART(HOUR, ETA)
ORDER BY Hour;
```

**Peak Hours** (highest waiting times):
- **08:00-10:00**: 847 arrivals, avg 42 min wait (berth congestion)
- **14:00-16:00**: 782 arrivals, avg 38 min wait (shift change overlap)
- **20:00-22:00**: 623 arrivals, avg 28 min wait (tidal window preference)

**Off-Peak Hours** (lowest waiting times):
- **02:00-04:00**: 234 arrivals, avg 8 min wait
- **10:00-12:00**: 512 arrivals, avg 15 min wait

**AI Agent Recommendation**: For low-priority vessels, suggest off-peak arrival times (02:00-04:00) to minimize waiting.

---

## Seasonal Patterns

### Monthly Berth Demand (from VESSEL_SCHEDULE)
| Month | Total Vessels | Peak Berths | Avg Utilization % | Notes |
|-------|---------------|-------------|-------------------|-------|
| **January** | 642 | A1, A2, E1 | 78% | Post-holiday surge |
| **February** | 598 | A1, E1 | 74% | Lunar New Year slowdown |
| **March** | 721 | A1, A2, A3 | 81% | Spring container peak |
| **April** | 698 | A1, E1, E2 | 79% | Bulk grain exports |
| **May** | 712 | A1, A2, D1 | 80% | RoRo vehicle surge |
| **June** | 734 | A1, A2, A3 | 82% | Summer peak begins |
| **July** | 798 | All container | 85% | Peak season (highest) |
| **August** | 812 | All container | 87% | Peak season continues |
| **September** | 745 | A1, A2, E1 | 83% | Post-peak normalization |
| **October** | 689 | A1, A2, E2 | 78% | Bulk commodity season |
| **November** | 701 | A1, A2, A3 | 79% | Pre-holiday buildup |
| **December** | 610 | A1, E1 | 72% | Holiday slowdown |

**AI Agent Recommendation**: July-August require aggressive optimization (87% avg utilization = near capacity).

---

## Berth Assignment Success Metrics

### First-Choice Assignment Rate (from OPTIMIZATION_RUNS)
```sql
SELECT
    BerthId,
    COUNT(*) AS TotalAssignments,
    SUM(CASE WHEN IsFirstChoice = 1 THEN 1 ELSE 0 END) AS FirstChoiceCount,
    (SUM(CASE WHEN IsFirstChoice = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) AS FirstChoiceRate
FROM OPTIMIZATION_RUNS
WHERE YEAR(OptimizationDate) = 2024
GROUP BY BerthId;
```

**Results**:
- Berth A1: 78% first-choice assignments (most preferred)
- Berth A2: 74% first-choice assignments
- Berth E1: 68% first-choice assignments
- Berth C3: 45% first-choice assignments (least utilized, LNG specialization)

**Insight**: High first-choice rates correlate with:
1. Multi-crane configuration (A1: 4 cranes)
2. Longest berth length (A1: 320m)
3. Versatile cargo handling (A1: container + general cargo capable)

---

## Query Patterns for AI Agents

### Example 1: Find Historical Berth Preference for Similar Vessels
```sql
-- Query VESSEL_HISTORY to find berth preferences for similar vessels
SELECT TOP 5
    vh.BerthId,
    b.BerthName,
    COUNT(*) AS HistoricalVisits,
    AVG(vh.DwellTime) AS AvgDwellHours,
    AVG(vh.WaitingTime) AS AvgWaitMinutes
FROM VESSEL_HISTORY vh
JOIN BERTHS b ON vh.BerthId = b.BerthId
JOIN VESSELS v ON vh.VesselId = v.VesselId
WHERE v.VesselType = @TargetVesselType
    AND v.LOA BETWEEN @TargetLOA - 20 AND @TargetLOA + 20
    AND vh.VisitDate >= DATEADD(YEAR, -1, GETDATE())
GROUP BY vh.BerthId, b.BerthName
ORDER BY HistoricalVisits DESC;
```

**Use Case**: "What berth has historically served Container vessels with LOA ~280m most frequently?"

### Example 2: Calculate Berth Turnaround Efficiency
```sql
-- Query VESSEL_SCHEDULE for berth-specific performance
SELECT
    b.BerthName,
    b.NumberOfCranes,
    COUNT(vs.ScheduleId) AS VesselsServed,
    AVG(vs.DwellTime) / 60.0 AS AvgDwellHours,
    AVG(vs.WaitingTime) AS AvgWaitMinutes,
    (COUNT(vs.ScheduleId) * 1.0 / 365) AS VesselsPerDay
FROM VESSEL_SCHEDULE vs
JOIN BERTHS b ON vs.BerthId = b.BerthId
WHERE YEAR(vs.ETD) = 2024
    AND vs.Status = 'Departed'
GROUP BY b.BerthId, b.BerthName, b.NumberOfCranes
ORDER BY AvgDwellHours ASC;
```

**Use Case**: "Which berth has the fastest average turnaround time for Container vessels?"

---

## AI Agent Integration Recommendations

### When ETA Predictor Agent queries this document:
- Use peak hour data to adjust waiting time predictions
- Reference seasonal patterns for July-August congestion warnings

### When Berth Optimizer Agent queries this document:
- Prioritize historical first-choice berths (A1, A2, E1)
- Match vessel type to berth specialization (RoRo → D1/D2, Tanker → C1/C2/C3)
- Consider dwell time patterns for turnaround estimates

### When Conflict Resolver Agent queries this document:
- Reference off-peak hours (02:00-04:00) for delay suggestions
- Use berth utilization rates to identify alternative berths (C3: 54% underutilized)

---

**Keywords**: berth allocation, historical patterns, container berths, bulk carriers, RoRo, tanker berths, utilization rates, dwell time analysis, seasonal patterns, vessel history, berth preferences, turnaround efficiency, VESSEL_SCHEDULE, BERTHS, VESSELS, VESSEL_HISTORY
