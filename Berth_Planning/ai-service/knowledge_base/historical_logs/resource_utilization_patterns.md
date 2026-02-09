# Resource Utilization Patterns - Historical Analysis

**Document Type**: Historical Analysis - Resource Usage
**Data Source**: RESOURCES, RESOURCE_ALLOCATION tables (2024 data)
**Analysis Period**: 12 months
**Category**: Historical Logs

---

## Executive Summary

Resource allocation efficiency directly impacts berth turnaround times. Analysis of RESOURCES and RESOURCE_ALLOCATION tables reveals optimal resource scheduling patterns, peak demand periods, and equipment bottlenecks.

**Key Metrics (2024)**:
- Crane utilization: 78% average (target: 75-85%)
- Pilot availability: 99.2% (24/7 coverage maintained)
- Tugboat utilization: 64% average (peaks at 89% during high tide windows)
- Labor gang efficiency: 82% (shift optimization opportunity)

---

## Crane Resource Analysis

### Crane Inventory (from RESOURCES table)
```sql
SELECT
    ResourceId,
    ResourceName,
    ResourceType,
    Capacity,
    IsAvailable,
    MaintenanceSchedule
FROM RESOURCES
WHERE ResourceType = 'Crane'
ORDER BY Capacity DESC;
```

| Crane ID | Name | Capacity (tons) | Location | 2024 Usage Hours | Utilization % | Status |
|----------|------|-----------------|----------|------------------|---------------|--------|
| **R-CR-001** | STS Crane 1 | 65 | Berth A1 | 6,847 | 78% | Active |
| **R-CR-002** | STS Crane 2 | 65 | Berth A1 | 6,752 | 77% | Active |
| **R-CR-003** | STS Crane 3 | 50 | Berth A2 | 6,489 | 74% | Active |
| **R-CR-004** | STS Crane 4 | 50 | Berth A2 | 6,512 | 74% | Active |
| **R-CR-005** | MHC Crane 5 | 45 | Berth A3 | 5,834 | 67% | Active |
| **R-CR-006** | MHC Crane 6 | 45 | Berth A3 | 5,921 | 68% | Active |

**Insight**: High-capacity cranes (65-ton) at Berth A1 show highest utilization (78%) due to:
- Large container vessel preference for A1 (see berth_allocation_patterns_2024.md)
- Faster loading rates (35 containers/hour vs 28 containers/hour for 50-ton cranes)

### Crane Allocation Patterns (from RESOURCE_ALLOCATION)
```sql
SELECT
    r.ResourceName,
    COUNT(ra.AllocationId) AS TotalAllocations,
    AVG(DATEDIFF(MINUTE, ra.AllocatedFrom, ra.AllocatedTo)) AS AvgAllocationMinutes,
    SUM(DATEDIFF(MINUTE, ra.AllocatedFrom, ra.AllocatedTo)) / 60.0 AS TotalHoursAllocated
FROM RESOURCE_ALLOCATION ra
JOIN RESOURCES r ON ra.ResourceId = r.ResourceId
WHERE r.ResourceType = 'Crane'
    AND YEAR(ra.AllocatedFrom) = 2024
GROUP BY r.ResourceId, r.ResourceName
ORDER BY TotalHoursAllocated DESC;
```

**Results**:
- Crane 1: 1,247 allocations, avg 5.5 hours per vessel, 6,847 total hours
- Crane 2: 1,189 allocations, avg 5.7 hours per vessel, 6,752 total hours
- Crane 3: 892 allocations, avg 7.3 hours per vessel, 6,489 total hours

**Pattern**: Multi-crane allocations reduce turnaround time by 35-40%:
- 1 crane: avg 18.2 hours dwell time
- 2 cranes: avg 11.8 hours dwell time (35% reduction)
- 4 cranes: avg 7.3 hours dwell time (60% reduction from 1-crane baseline)

### Crane Failure Impact Analysis (from BERTH_MAINTENANCE, ALERTS_NOTIFICATIONS)
**2024 Unplanned Downtime Events**: 14 incidents

| Date | Crane | Failure Type | Downtime Hours | Vessels Affected | Impact |
|------|-------|--------------|----------------|------------------|--------|
| 2024-03-15 | Crane 2 | Hydraulic leak | 8 hours | 4 vessels | +12 hours total delay |
| 2024-06-22 | Crane 5 | Motor failure | 18 hours | 7 vessels | +28 hours total delay |
| 2024-09-08 | Crane 1 | Electrical fault | 6 hours | 3 vessels | +8 hours total delay |

**AI Agent Recommendation**: When crane unavailable, query RESOURCE_ALLOCATION for alternative crane assignments:
```sql
-- Find alternative cranes at adjacent berths
SELECT r.ResourceId, r.ResourceName, b.BerthName, r.IsAvailable
FROM RESOURCES r
JOIN BERTHS b ON r.BerthId = b.BerthId
WHERE r.ResourceType = 'Crane'
    AND r.IsAvailable = 1
    AND b.BerthType = @RequiredBerthType
    AND NOT EXISTS (
        SELECT 1 FROM RESOURCE_ALLOCATION ra
        WHERE ra.ResourceId = r.ResourceId
            AND @RequestedTime BETWEEN ra.AllocatedFrom AND ra.AllocatedTo
    );
```

---

## Pilot Resource Analysis

### Pilot Inventory (from RESOURCES table)
```sql
SELECT
    ResourceId,
    ResourceName,
    ResourceType,
    Certifications,
    IsAvailable
FROM RESOURCES
WHERE ResourceType = 'Pilot'
ORDER BY ResourceName;
```

| Pilot ID | Name | Certifications | 2024 Jobs | Availability % | Shift Pattern |
|----------|------|----------------|-----------|----------------|---------------|
| **R-PIL-001** | Pilot A | Class 1, Deep Draft | 847 | 99.8% | Rotating 24/7 |
| **R-PIL-002** | Pilot B | Class 1, Tanker | 798 | 99.5% | Rotating 24/7 |
| **R-PIL-003** | Pilot C | Class 2, Container | 812 | 99.2% | Rotating 24/7 |
| **R-PIL-004** | Pilot D | Class 2, Bulk | 734 | 98.9% | Rotating 24/7 |

**Pilot Assignment Logic** (from RESOURCE_ALLOCATION):
```sql
-- Match pilot certification to vessel requirements
SELECT
    v.VesselName,
    v.VesselType,
    v.Draft,
    r.ResourceName AS AssignedPilot,
    r.Certifications
FROM VESSEL_SCHEDULE vs
JOIN VESSELS v ON vs.VesselId = v.VesselId
JOIN RESOURCE_ALLOCATION ra ON vs.ScheduleId = ra.ScheduleId
JOIN RESOURCES r ON ra.ResourceId = r.ResourceId
WHERE r.ResourceType = 'Pilot'
    AND YEAR(vs.ETA) = 2024
ORDER BY vs.ETA;
```

**Certification Requirements**:
- Deep Draft vessels (draft > 12m): Class 1 pilot only (Pilot A or B)
- Tanker vessels (all): Pilot B (specialized tanker certification)
- Container vessels: Class 1 or 2 (any pilot)
- Bulk carriers: Class 2 sufficient (Pilot C or D)

**AI Agent Recommendation**: Query `RESOURCES.Certifications` to match with `VESSELS.VesselType` and `VESSELS.Draft`:
```
IF vessel.draft > 12 THEN pilot.certification MUST INCLUDE 'Deep Draft'
IF vessel.type = 'Tanker' THEN pilot.certification MUST INCLUDE 'Tanker'
```

### Pilot Availability Gaps (from ALERTS_NOTIFICATIONS)
**2024 Incidents**: 7 cases where no pilot available

| Date | Time | Reason | Vessels Delayed | Avg Delay (min) |
|------|------|--------|-----------------|-----------------|
| 2024-02-14 | 03:30 | All pilots on active jobs | 2 vessels | 45 min |
| 2024-07-19 | 18:45 | Pilot illness (Pilot C) | 3 vessels | 62 min |
| 2024-10-03 | 22:15 | Weather delay cascaded | 1 vessel | 38 min |

**Mitigation**: Maintain 4 pilots with staggered shifts ensures 99.2% availability (acceptable for port operations).

---

## Tugboat Resource Analysis

### Tugboat Fleet (from RESOURCES table)
```sql
SELECT
    ResourceId,
    ResourceName,
    ResourceType,
    BollardPull,
    IsAvailable
FROM RESOURCES
WHERE ResourceType = 'Tugboat'
ORDER BY BollardPull DESC;
```

| Tugboat ID | Name | Bollard Pull (tons) | 2024 Jobs | Utilization % | Status |
|------------|------|---------------------|-----------|---------------|--------|
| **R-TUG-001** | Tug Alpha | 65 | 1,234 | 71% | Active |
| **R-TUG-002** | Tug Beta | 60 | 1,189 | 68% | Active |
| **R-TUG-003** | Tug Gamma | 55 | 892 | 64% | Active |
| **R-TUG-004** | Tug Delta | 50 | 734 | 58% | Active |

### Tugboat Allocation Rules (from RESOURCE_ALLOCATION)
**Historical Pattern Analysis**:

```sql
-- Analyze tugboat requirements by vessel size
SELECT
    CASE
        WHEN v.LOA < 150 THEN 'Small (<150m)'
        WHEN v.LOA BETWEEN 150 AND 250 THEN 'Medium (150-250m)'
        ELSE 'Large (>250m)'
    END AS VesselSizeCategory,
    AVG(tugboat_count.TugCount) AS AvgTugsRequired,
    MAX(tugboat_count.TugCount) AS MaxTugsRequired
FROM VESSEL_SCHEDULE vs
JOIN VESSELS v ON vs.VesselId = v.VesselId
JOIN (
    SELECT ra.ScheduleId, COUNT(*) AS TugCount
    FROM RESOURCE_ALLOCATION ra
    JOIN RESOURCES r ON ra.ResourceId = r.ResourceId
    WHERE r.ResourceType = 'Tugboat'
    GROUP BY ra.ScheduleId
) tugboat_count ON vs.ScheduleId = tugboat_count.ScheduleId
WHERE YEAR(vs.ETA) = 2024
GROUP BY CASE WHEN v.LOA < 150 THEN 'Small' WHEN v.LOA BETWEEN 150 AND 250 THEN 'Medium' ELSE 'Large' END;
```

**Results**:
- Small vessels (<150m LOA): 1.2 tugs average, 2 tugs max
- Medium vessels (150-250m LOA): 2.0 tugs average, 3 tugs max
- Large vessels (>250m LOA): 3.0 tugs average, 4 tugs max

**Bollard Pull Requirements** (from historical data):
```
Vessel GT < 50,000: Minimum 50-ton bollard pull (1-2 tugs)
Vessel GT 50,000-100,000: Minimum 60-ton bollard pull (2-3 tugs)
Vessel GT > 100,000: Minimum 65-ton bollard pull (3-4 tugs)
```

**AI Agent Recommendation**:
```python
def calculate_tugboat_requirement(vessel):
    if vessel.gt < 50000:
        return {"count": 1, "min_bollard_pull": 50}
    elif vessel.gt < 100000:
        return {"count": 2, "min_bollard_pull": 60}
    else:
        return {"count": 3, "min_bollard_pull": 65}
```

### Tugboat Peak Demand Periods (from RESOURCE_ALLOCATION)
**Tidal Window Correlation**:

| Tide Phase | Tugboat Allocations | Avg Concurrent Jobs | Peak Demand Time |
|------------|---------------------|---------------------|------------------|
| **High Tide ±2h** | 3,847 jobs | 3.2 concurrent | 10:00-12:00, 22:00-00:00 |
| **Mid Tide** | 2,189 jobs | 1.8 concurrent | 04:00-06:00, 16:00-18:00 |
| **Low Tide** | 892 jobs | 0.6 concurrent | 01:00-03:00, 13:00-15:00 |

**Insight**: High tide windows (±2 hours) see 4-5× tugboat demand due to:
- Deep draft vessels requiring high tide for navigation (see UKC constraints)
- Simultaneous arrivals scheduled for optimal tidal depth

**AI Agent Recommendation**: Check TIDAL_DATA for high tide periods when scheduling tugboat resources:
```sql
SELECT TideDateTime, TideHeight, TideType
FROM TIDAL_DATA
WHERE TideType = 'High'
    AND TideDateTime BETWEEN @StartDate AND @EndDate
ORDER BY TideDateTime;
```

---

## Labor Gang Resource Analysis

### Stevedore Gang Inventory (from RESOURCES table)
```sql
SELECT
    ResourceId,
    ResourceName,
    ResourceType,
    ShiftPattern,
    Capacity
FROM RESOURCES
WHERE ResourceType = 'StevedoreGang'
ORDER BY ResourceName;
```

| Gang ID | Name | Capacity (workers) | Shift | 2024 Allocations | Utilization % |
|---------|------|-------------------|-------|------------------|---------------|
| **R-STD-001** | Gang A | 12 workers | Day (06:00-14:00) | 1,247 | 86% |
| **R-STD-002** | Gang B | 12 workers | Day (06:00-14:00) | 1,189 | 82% |
| **R-STD-003** | Gang C | 10 workers | Evening (14:00-22:00) | 892 | 78% |
| **R-STD-004** | Gang D | 10 workers | Evening (14:00-22:00) | 834 | 73% |
| **R-STD-005** | Gang E | 8 workers | Night (22:00-06:00) | 623 | 64% |
| **R-STD-006** | Gang F | 8 workers | Night (22:00-06:00) | 598 | 61% |

### Shift Handover Impact (from RESOURCE_ALLOCATION, VESSEL_SCHEDULE)
**Query**: Analyze waiting time increase during shift handover periods
```sql
SELECT
    DATEPART(HOUR, vs.ATB) AS BerthingHour,
    AVG(vs.WaitingTime) AS AvgWaitMinutes,
    COUNT(*) AS VesselCount
FROM VESSEL_SCHEDULE vs
WHERE YEAR(vs.ATB) = 2024
    AND vs.WaitingTime > 0
GROUP BY DATEPART(HOUR, vs.ATB)
ORDER BY AvgWaitMinutes DESC;
```

**Peak Waiting Times** (shift handover correlation):
- **06:00** (night→day shift): 42 min avg wait (734 vessels affected)
- **14:00** (day→evening shift): 38 min avg wait (612 vessels affected)
- **22:00** (evening→night shift): 28 min avg wait (487 vessels affected)

**AI Agent Recommendation**: Avoid scheduling vessel berthing within ±30 minutes of shift change (05:30-06:30, 13:30-14:30, 21:30-22:30) unless high priority.

---

## Resource Contention Analysis

### Multi-Resource Conflict Detection (from RESOURCE_ALLOCATION, CONFLICTS)
**Query**: Find schedules requiring same resources simultaneously
```sql
SELECT
    c.ConflictId,
    c.ConflictType,
    c.Severity,
    c.Description,
    c.DetectedAt
FROM CONFLICTS c
WHERE c.ConflictType = 'ResourceContention'
    AND YEAR(c.DetectedAt) = 2024
ORDER BY c.Severity DESC, c.DetectedAt DESC;
```

**2024 Resource Conflicts**: 142 incidents

| Resource Type | Conflict Count | Avg Resolution Time (min) | Impact Level |
|---------------|----------------|---------------------------|--------------|
| **Crane** | 87 conflicts | 62 min | High (delays cargo ops) |
| **Tugboat** | 34 conflicts | 28 min | Medium (delays berthing) |
| **Pilot** | 14 conflicts | 45 min | High (delays arrival) |
| **Gang** | 7 conflicts | 18 min | Low (minor shift delay) |

**Example Conflict Scenario** (from CONFLICTS table):
```
ConflictId: C-2024-0428
Type: ResourceContention
Severity: High
Description: "Crane 2 allocated to Vessel A (Schedule S-1234) 14:00-18:00,
              but also requested for Vessel B (Schedule S-1235) 15:00-19:00.
              1-hour overlap detected."
Resolution: "Reassigned Crane 3 to Vessel B, 22-minute delay incurred."
DetectedAt: 2024-07-15 13:45:00
ResolvedAt: 2024-07-15 14:07:00
```

**AI Agent Recommendation**: Query RESOURCE_ALLOCATION before assigning to detect conflicts:
```sql
SELECT r.ResourceId, r.ResourceName, ra.AllocatedFrom, ra.AllocatedTo
FROM RESOURCE_ALLOCATION ra
JOIN RESOURCES r ON ra.ResourceId = r.ResourceId
WHERE r.ResourceType = @RequestedResourceType
    AND ra.Status = 'Allocated'
    AND (
        (@RequestedStart BETWEEN ra.AllocatedFrom AND ra.AllocatedTo)
        OR (@RequestedEnd BETWEEN ra.AllocatedFrom AND ra.AllocatedTo)
        OR (ra.AllocatedFrom BETWEEN @RequestedStart AND @RequestedEnd)
    );
```

---

## Query Patterns for AI Agents

### Example 1: Find Available Cranes for Time Window
```sql
SELECT r.ResourceId, r.ResourceName, r.Capacity, b.BerthName
FROM RESOURCES r
JOIN BERTHS b ON r.BerthId = b.BerthId
WHERE r.ResourceType = 'Crane'
    AND r.IsAvailable = 1
    AND NOT EXISTS (
        SELECT 1 FROM RESOURCE_ALLOCATION ra
        WHERE ra.ResourceId = r.ResourceId
            AND ra.Status = 'Allocated'
            AND (
                (@RequestedStart BETWEEN ra.AllocatedFrom AND ra.AllocatedTo)
                OR (@RequestedEnd BETWEEN ra.AllocatedFrom AND ra.AllocatedTo)
            )
    )
ORDER BY r.Capacity DESC;
```

### Example 2: Calculate Required Resources for Vessel
```sql
-- Based on historical patterns for similar vessels
SELECT
    AVG(crane_count.CraneCount) AS AvgCranesNeeded,
    AVG(tug_count.TugCount) AS AvgTugsNeeded,
    AVG(vs.DwellTime) AS AvgDwellMinutes
FROM VESSEL_SCHEDULE vs
JOIN VESSELS v ON vs.VesselId = v.VesselId
JOIN (
    SELECT ra.ScheduleId, COUNT(*) AS CraneCount
    FROM RESOURCE_ALLOCATION ra
    JOIN RESOURCES r ON ra.ResourceId = r.ResourceId
    WHERE r.ResourceType = 'Crane'
    GROUP BY ra.ScheduleId
) crane_count ON vs.ScheduleId = crane_count.ScheduleId
JOIN (
    SELECT ra.ScheduleId, COUNT(*) AS TugCount
    FROM RESOURCE_ALLOCATION ra
    JOIN RESOURCES r ON ra.ResourceId = r.ResourceId
    WHERE r.ResourceType = 'Tugboat'
    GROUP BY ra.ScheduleId
) tug_count ON vs.ScheduleId = tug_count.ScheduleId
WHERE v.VesselType = @TargetVesselType
    AND v.LOA BETWEEN @TargetLOA - 20 AND @TargetLOA + 20
    AND YEAR(vs.ETD) = 2024;
```

---

**Keywords**: resource utilization, crane allocation, pilot availability, tugboat requirements, labor gangs, shift handover, resource contention, RESOURCES table, RESOURCE_ALLOCATION table, bollard pull, stevedore gangs, resource conflicts, utilization metrics
