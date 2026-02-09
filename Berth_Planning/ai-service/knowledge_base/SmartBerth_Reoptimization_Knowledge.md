# SmartBerth AI - Real-Time Re-Optimization Engine Knowledge

**Document Version:** 2.0  
**Last Updated:** February 2026  
**Purpose:** Comprehensive domain knowledge for real-time schedule re-optimization and what-if simulation  
**Priority:** HIGH — Central orchestrator for schedule changes

---

## 1. Re-Optimization Triggers

### 1.1 Trigger Types and Sources
| Trigger Type | Source Service | Description | Expected Frequency |
|---|---|---|---|
| ETA_CHANGE | Vessel Tracking / ETA Prediction | Predicted ETA deviates from scheduled window | Multiple times per hour |
| CONFLICT_DETECTED | Conflict Detection | Schedule conflict identified that needs resolution | 2-5 per day |
| RESOURCE_UNAVAILABLE | Resource Planning | Pilot/tug/crane becomes unavailable | 1-3 per day |
| VESSEL_DELAY | Vessel Tracking | Vessel significantly behind schedule | 3-8 per day |
| WEATHER_CHANGE | Weather Service | Weather conditions affect operations | 1-2 per day |
| PRIORITY_OVERRIDE | Manual / System | High-priority vessel needs immediate attention | Rare (0-1 per day) |
| BERTH_UNAVAILABLE | Terminal Ops | Berth taken offline (maintenance, incident) | Rare (0-1 per week) |
| MANUAL_ADJUSTMENT | Port Operator | Operator drags schedule on Gantt chart | 5-15 per day |

### 1.2 Trigger Significance Assessment
Not all triggers require full re-optimization. Assessment criteria:
- **Impact Magnitude:** How much does the schedule change (minutes vs. hours)?
- **Cascade Potential:** How many downstream vessels are affected?
- **Resource Impact:** Are critical resources (pilots, tugs) affected?
- **Schedule Buffer:** Is there enough slack to absorb the change?

Significance Levels:
- **MINOR:** < 15 min deviation, no cascade, sufficient buffer → Log only
- **MODERATE:** 15-60 min deviation, 1-2 affected, tight buffer → Local adjustment
- **MAJOR:** 60+ min deviation, 3+ affected, insufficient buffer → Full re-optimization
- **CRITICAL:** Safety concern, berth closure, or 5+ vessels affected → Emergency re-optimization

---

## 2. Re-Optimization Decision Engine (7-Step Process)

### Step 1: Evaluate Trigger Significance
- Parse trigger event details
- Calculate deviation magnitude
- Check if deviation exceeds threshold for re-optimization

### Step 2: Assess Schedule Stability
- Count number of active berth assignments
- Calculate overall schedule slack (buffer time between consecutive vessels)
- Identify already-stressed assignments (low buffer, near-constraint)

### Step 3: Generate Candidate Adjustments
For each affected assignment:
- **Option A:** Keep current assignment, shift time window
- **Option B:** Reassign to alternative berth
- **Option C:** Change priority ordering
- **Option D:** Request vessel speed adjustment

### Step 4: Score Candidates
Multi-objective scoring:
- **Minimize Disruption:** Number of schedule changes (weight: 0.40)
- **Maximize Throughput:** Total vessels processed per day (weight: 0.30)
- **Minimize Waiting:** Average vessel waiting time (weight: 0.20)
- **Risk Minimization:** Constraint violation probability (weight: 0.10)

### Step 5: Select Optimal Schedule
Apply constraints and select highest-scoring feasible schedule.

### Step 6: Generate LLM Explanation
Claude generates natural language explanation of:
- What changed and why
- Who is affected (list of vessels)
- What actions are required
- What risks remain

### Step 7: Execute and Emit Alerts
- Apply schedule changes
- Notify affected parties via alert service
- Update digital twin visualization

---

## 3. Schedule Change Types

### 3.1 BERTH_REASSIGN
Move a vessel from one berth to another.
- **Pre-conditions:** Target berth compatible (LOA, draft, cargo type), time window available
- **Side effects:** Resource reassignment (different cranes, possibly different pilots/tugs)
- **Notification:** Both origin and target terminal operators

### 3.2 TIME_SHIFT
Adjust the scheduled time window for a vessel at the same berth.
- **Pre-conditions:** Shifted window doesn't overlap with adjacent assignments
- **Side effects:** May require resource rescheduling (pilot/tug timing)
- **Notification:** Shipping agent, terminal operator, pilot service, tug service

### 3.3 PRIORITY_CHANGE
Change the processing priority of a vessel.
- **Pre-conditions:** Justification required (cargo type, contractual, safety)
- **Side effects:** Lower-priority vessels may be delayed
- **Notification:** All affected shipping agents

### 3.4 RESOURCE_REALLOC
Reassign resources (cranes, pilots, tugs) between operations.
- **Pre-conditions:** Resource compatible with new assignment, operator certified
- **Side effects:** Original operation may be slower
- **Notification:** Resource operators, affected terminal operators

---

## 4. Cascade Impact Analysis

### 4.1 Direct Impact
Vessels whose schedule is directly changed by the re-optimization.
- Berth changes, time shifts, resource changes

### 4.2 Indirect Impact
Vessels affected because a directly-impacted vessel occupies their previously scheduled berth.
- Chain reaction: Vessel A delayed → Berth occupied → Vessel B cannot dock → Vessel C delayed...
- Typically extends 2-4 levels deep

### 4.3 Impact Metrics
- **Total Delay (vessel-hours):** Sum of all delays across all affected vessels
- **Max Single Delay:** Worst-case delay for any single vessel
- **Resources Affected:** Count of pilots, tugs, cranes requiring rescheduling
- **Cost Estimate:** Berth charges, overtime, demurrage costs
- **Alerts Generated:** Count and severity of alerts triggered

---

## 5. Gantt Chart Schedule Management

### 5.1 Gantt Display Elements
- **X-axis:** Time (24-hour view, scrollable)
- **Y-axis:** Berths (grouped by terminal)
- **Bars:** Vessel assignments showing:
  - Vessel name and type
  - Scheduled time window (arrival → departure)
  - Color-coded by status (Green=confirmed, Yellow=provisional, Red=conflict)
  - ETA confidence indicator

### 5.2 Drag-and-Drop Rules
When an operator drags a vessel bar to a new position:
1. **Validate target berth compatibility** (LOA, draft, cargo)
2. **Check time window availability** (no overlap with other vessels)
3. **Verify resource availability** (pilots, tugs, cranes at new time)
4. **Assess cascade impact** (effect on subsequent vessels)
5. **Generate LLM explanation** of the move's implications
6. **Request confirmation** before applying

Rejected moves show explanation of why the move is infeasible.

### 5.3 Before/After State Snapshots
Every re-optimization event records:
- **Before State:** Complete schedule snapshot at time of trigger
- **After State:** Complete schedule snapshot after optimization
- **Changes Array:** List of individual changes with before/after values
- **Explanation:** LLM-generated explanation of all changes
- **Audit Trail:** Timestamp, trigger source, operator (if manual)

---

## 6. Auto-Adjustment vs. Operator-Confirmed Mode

### 6.1 Auto-Adjustment Mode
- System automatically applies MINOR and MODERATE re-optimizations
- Operator notified after the fact
- Suitable for: routine ETA updates, small time shifts (< 30 min)

### 6.2 Operator-Confirmed Mode
- System proposes changes, waits for operator approval
- Required for: MAJOR and CRITICAL changes, priority overrides, berth reassignments
- Timeout: If no response in 15 minutes, system applies recommended action

### 6.3 Configuration
Port operators can configure:
- Threshold for auto vs. confirmed mode (minutes of delay)
- Which trigger types always require confirmation
- Quiet hours (night operations may default to auto)
- Escalation contacts for different severity levels
