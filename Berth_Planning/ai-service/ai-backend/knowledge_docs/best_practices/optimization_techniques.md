# Berth Allocation Optimization Techniques - Best Practices

**Document Type**: Best Practices - Optimization Methods
**Source**: Operations Research, Port Management Literature
**Category**: Best Practices

---

## Berth Allocation Problem (BAP) Overview

The Berth Allocation Problem is a combinatorial optimization problem with O(N⁴) complexity (source: Cornell ORIE research). Given N vessels, find optimal berth assignments minimizing:
- Total waiting time (minimize ATA-to-ATB gaps)
- Total port stay time (minimize ATA-to-ATD)
- Berth idle time (maximize utilization)
- Priority violations (respect vessel priorities)

**Constraints**:
- Physical: LOA ≤ berth length, draft ≤ berth depth
- Temporal: No berth double-booking
- Resource: Crane/pilot/tugboat availability

---

## Optimization Strategies

### 1. First-Come-First-Served (FCFS)
**Simple baseline approach**

```sql
-- FCFS allocation
SELECT
    vs.ScheduleId,
    vs.VesselId,
    vs.ETA,
    b.BerthId,
    b.BerthName
FROM VESSEL_SCHEDULE vs
CROSS APPLY (
    SELECT TOP 1 *
    FROM BERTHS b
    WHERE b.BerthType = (SELECT VesselType FROM VESSELS WHERE VesselId = vs.VesselId)
        AND NOT EXISTS (
            SELECT 1 FROM VESSEL_SCHEDULE vs2
            WHERE vs2.BerthId = b.BerthId
                AND vs.ETA < vs2.ETD
                AND vs2.ETA < vs.ETD
        )
    ORDER BY b.BerthId
) b
WHERE vs.Status = 'Scheduled'
ORDER BY vs.ETA;
```

**Advantages**: Simple, fair
**Disadvantages**: Ignores priority, suboptimal utilization

---

### 2. Priority-Based Assignment
**Respect vessel priorities**

```sql
-- Priority-based allocation
SELECT
    vs.ScheduleId,
    vs.VesselId,
    vs.Priority,
    vs.ETA,
    best_berth.BerthId
FROM VESSEL_SCHEDULE vs
CROSS APPLY (
    SELECT TOP 1 b.BerthId, b.BerthName
    FROM BERTHS b
    WHERE /* compatibility checks */
    ORDER BY
        b.NumberOfCranes DESC,  -- Prefer more cranes
        b.Length ASC            -- Prefer smaller berth (save capacity)
) best_berth
WHERE vs.Status = 'Scheduled'
ORDER BY vs.Priority ASC, vs.ETA ASC;  -- High priority first (Priority 1 = highest)
```

**Used in**: Emergency vessels, government vessels, window vessels

---

### 3. Multi-Factor Scoring
**Comprehensive berth fitness calculation**

```python
def calculate_berth_score(vessel, berth, current_time):
    """
    Score berth suitability (0-100 scale)
    """
    score = 0

    # Physical fit (25 points)
    if berth.length >= vessel.loa * 1.05:  # 5% buffer
        score += 25
    elif berth.length >= vessel.loa:
        score += 20
    else:
        return 0  # Not compatible

    # Equipment match (20 points)
    if berth.number_of_cranes >= vessel.required_cranes:
        score += 20
    elif berth.number_of_cranes >= vessel.required_cranes - 1:
        score += 15

    # Location convenience (15 points)
    # Closer to port entrance = higher score
    score += (15 * (1 - berth.distance_from_entrance / max_distance))

    # Historical performance (10 points)
    # Query VESSEL_HISTORY for past performance at this berth
    avg_dwell = get_avg_dwell_time(vessel.type, berth.id)
    if avg_dwell < target_dwell_time:
        score += 10

    # Resource availability (10 points)
    resources_ready = check_resource_availability(berth, current_time)
    if resources_ready:
        score += 10

    # Waiting time reduction (10 points)
    next_available = get_next_available_time(berth)
    if next_available <= vessel.eta:
        score += 10

    # Commercial terms (10 points)
    if berth.has_premium_service:
        score += 5

    return score
```

**Implement in**: Berth Optimizer Agent

---

### 4. Time Window Optimization
**Schedule vessels to minimize gaps**

**Technique**: Use OR-Tools Constraint Programming Solver (already implemented in .NET backend)

```python
# Pseudo-code (actual implementation in C# OR-Tools)
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Decision variables
berth_assignments = {}
start_times = {}
end_times = {}

for vessel in vessels:
    for berth in compatible_berths:
        berth_assignments[(vessel, berth)] = model.NewBoolVar(f'assign_{vessel}_{berth}')
        start_times[(vessel, berth)] = model.NewIntVar(0, max_time, f'start_{vessel}_{berth}')
        end_times[(vessel, berth)] = model.NewIntVar(0, max_time, f'end_{vessel}_{berth}')

# Constraints
# 1. Each vessel assigned to exactly one berth
for vessel in vessels:
    model.Add(sum(berth_assignments[(vessel, b)] for b in compatible_berths) == 1)

# 2. No berth overlap (no double-booking)
for berth in berths:
    intervals = []
    for vessel in vessels:
        interval = model.NewOptionalIntervalVar(
            start_times[(vessel, berth)],
            dwell_times[vessel],
            end_times[(vessel, berth)],
            berth_assignments[(vessel, berth)],
            f'interval_{vessel}_{berth}'
        )
        intervals.append(interval)
    model.AddNoOverlap(intervals)

# Objective: Minimize total waiting time + maximize utilization
model.Minimize(total_waiting_time - utilization_bonus)
```

**AI Agent Integration**: Call existing .NET OR-Tools API via HTTP

---

## Query Patterns for Optimization

### Find Best Available Berth
```sql
WITH CompatibleBerths AS (
    SELECT
        b.BerthId,
        b.BerthName,
        b.Length,
        b.NumberOfCranes,
        -- Check availability
        (SELECT MIN(vs2.ETD)
         FROM VESSEL_SCHEDULE vs2
         WHERE vs2.BerthId = b.BerthId
             AND vs2.Status IN ('Berthed', 'Scheduled')
             AND vs2.ETD > GETDATE()
        ) AS NextAvailableTime
    FROM BERTHS b
    WHERE b.IsActive = 1
        AND b.Length >= @VesselLOA
        AND b.MaxDraft >= @VesselDraft
        AND b.BerthType = @VesselType
)
SELECT TOP 1 *
FROM CompatibleBerths
WHERE NextAvailableTime IS NULL OR NextAvailableTime <= @VesselETA
ORDER BY NumberOfCranes DESC, Length ASC;
```

---

## Best Practices for AI Agents

### ETA Predictor Best Practices
1. Update predictions every 2-4 hours as vessel approaches
2. Incorporate multiple data sources: AIS, weather, historical patterns
3. Confidence scoring: Decrease confidence for predictions >48 hours out
4. Log predictions in OPTIMIZATION_RUNS for performance tracking

### Berth Optimizer Best Practices
1. Multi-factor scoring over simple FCFS
2. Respect hard constraints (physical, safety) first
3. Optimize soft constraints (commercial, efficiency) second
4. Consider resource availability (cranes, pilots, tugs)
5. Minimize waiting time as primary objective

### Conflict Resolver Best Practices
1. Detect conflicts early (48+ hours advance warning)
2. Generate multiple resolution options (typically 3 alternatives)
3. Calculate cost impact of each option
4. Prefer shifting lower-priority vessels
5. Minimize cascade effects (avoid shifting too many vessels)

---

**Keywords**: berth allocation optimization, OR-Tools, constraint programming, priority-based assignment, multi-factor scoring, FCFS, BAP, combinatorial optimization, VESSEL_SCHEDULE, BERTHS, best practices
