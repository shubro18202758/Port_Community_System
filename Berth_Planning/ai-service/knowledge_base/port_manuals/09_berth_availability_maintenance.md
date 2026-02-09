# Port Operations Manual: Berth Availability & Maintenance Management

**Document Type**: Port Operations Manual - Hard + Soft Constraints
**Category**: Layer 2 - Berth/Terminal-Level Availability Constraints
**Classification**: HARD (maintenance windows), SOFT (buffer times, shift handover)
**Applies To**: Berth scheduling, maintenance planning, operational gaps

---

## Overview

Berth availability and maintenance constraints manage temporal access to berths, ensuring:
1. No double-booking (HARD constraint - physical impossibility)
2. Planned maintenance windows are respected (HARD constraint - safety/regulatory)
3. Operational buffer times for berth preparation (SOFT constraint - efficiency)
4. Shift handover coordination (SOFT constraint - labor management)

---

## Berth Occupancy Constraints

### 1. No Double-Booking - Constraint ID: B-AVAIL-001

**Rule**: `FOR ANY berth: MAX(concurrent_vessels) = 1`

**Type**: **ABSOLUTE HARD** constraint

**Description**: A berth can physically accommodate only ONE vessel at a time. This is the most fundamental berth allocation constraint.

**Overlap Detection Algorithm**:
```
FOR vessel_A IN berth_X:
    FOR vessel_B IN berth_X WHERE vessel_B ≠ vessel_A:
        IF (vessel_A.ETB < vessel_B.ETD) AND (vessel_B.ETB < vessel_A.ETD):
            CONFLICT DETECTED
```

**Example Conflict Scenario**:

**Berth K1 Status**:
- **Current Vessel**: MV Evergreen Unity
  - ETB (Estimated Time Berthing): 1000
  - ETD (Estimated Time Departure): 1400 (2 hours cargo ops remaining at 1200)

**Incoming Request**:
- **MV OOCL Pacific**
  - Requested ETB: 1300 (wants immediate berthing)

**Overlap Analysis**:
```
Evergreen Unity: 1000────────────1400
OOCL Pacific:           1300──────────1700
                         ▼
                      CONFLICT
                      (1300-1400 = 1-hour overlap)
```

**Decision**: ❌ **REJECTED** - Cannot double-book Berth K1

**AI-Generated Resolution Options**:
1. **Delay OOCL Pacific to 1430** (30-minute buffer after Evergreen departs)
   - Cost: 1.5 hours demurrage
   - Benefit: Uses same berth, no complexity

2. **Assign OOCL Pacific to alternative Berth K2**
   - Cost: K2 may be less optimal (fewer cranes, longer distance)
   - Benefit: Immediate berthing, no waiting

3. **Expedite Evergreen Unity operations**
   - Deploy extra crane to finish by 1230
   - Cost: $3,000 crane premium
   - Benefit: OOCL Pacific berths closer to requested time (1300)

**AI Recommendation**: **Option 2** (Berth K2 available immediately, least disruption)

---

### 2. Buffer Time Between Vessels - Constraint ID: B-AVAIL-003

**Rule**: `next_vessel_ETB ≥ previous_vessel_ETD + buffer_time`

**Type**: **SOFT** constraint (operational best practice)

**Description**: Buffer time allows for:
- Berth inspection after vessel departure
- Mooring line retrieval and stowage
- Debris/cargo residue cleanup
- Fender damage assessment
- Pilot boat repositioning

**Standard Buffer Times**:

| Berth Type | Normal Buffer | After Large Vessel | After Maintenance |
|-----------|--------------|-------------------|------------------|
| **Container** | 30-60 minutes | 60-90 minutes | 120 minutes |
| **Bulk** | 60-120 minutes | 120-180 minutes | 180 minutes |
| **Liquid** | 30-45 minutes | 45-60 minutes | 90 minutes |
| **RoRo** | 20-30 minutes | 30-45 minutes | 60 minutes |

**Example Optimization**:
```
Vessel A (Container): ETD 1400
Vessel B (Container): Requested ETB 1415
Standard Buffer: 60 minutes
Optimal ETB for Vessel B: 1500 (1400 + 60 min)

Actual Request: 1415 (45 minutes short of optimal)
```

**AI Decision Options**:
1. **Accept 1415 berthing** - Tighter schedule, rush berth prep
   - Risk: 10% chance of 15-minute delay due to incomplete prep
   - Benefit: Vessel B saves 45 minutes waiting

2. **Recommend 1500 berthing** - Full buffer, standard operations
   - Benefit: Safe, predictable operations
   - Cost: Vessel B waits 45 extra minutes

**Decision Factors**:
- Vessel B demurrage rate: If high (>$500/hour), accept 1415
- Port congestion: If high, accept 1415 to maximize throughput
- Weather: If good, accept 1415; if marginal, maintain 1500 buffer

**Typical Decision**: SOFT constraint allows flexibility based on commercial/operational context.

---

## Planned Maintenance Constraints

### 3. Maintenance Window Scheduling - Constraint ID: B-AVAIL-002

**Rule**: `IF berth.maintenance_scheduled THEN berth.available = FALSE DURING maintenance_window`

**Type**: **HARD** constraint

**Description**: Berths require periodic maintenance for:
- Crane overhauls (annual, 7-14 days)
- Fender replacement (every 5-10 years, 3-7 days)
- Quay wall repairs (as-needed, 1-30 days)
- Mooring bollard inspections (quarterly, 1 day)
- Dredging operations (annual, 3-14 days)
- Electrical system upgrades (periodic, 2-7 days)

**Maintenance Types & Durations**:

| Maintenance Type | Frequency | Duration | Advance Notice |
|-----------------|-----------|----------|---------------|
| **Crane Major Overhaul** | Annual | 10-14 days | 90 days |
| **Crane Minor Service** | Quarterly | 12-24 hours | 30 days |
| **Fender Replacement** | 5-10 years | 5-7 days | 180 days |
| **Bollard Inspection** | Quarterly | 4-8 hours | 14 days |
| **Quay Repairs** | As-needed | 1-30 days | Emergency: 24 hours |
| **Dredging** | Annual | 7-14 days | 90 days |

**Example Maintenance Conflict**:

**Berth L1 Maintenance Schedule**:
- **Type**: Crane overhaul (STS Crane #1)
- **Date**: Monday 0600-1800 (12-hour shutdown)
- **Reason**: Annual mandatory inspection

**Vessel Request**:
- **MV Atlantic Trader**
- **ETA**: Monday 0800
- **Cargo Operations**: 10 hours (needs cranes)

**Conflict Analysis**:
```
Maintenance Window: 0600────────────1800
Vessel Request:           0800──────────1800
                           ▼
                        OVERLAP: 0800-1800
                        Cannot operate cranes during maintenance
```

**Decision**: ❌ **REJECTED** for Monday berthing at Berth L1

**AI-Generated Alternatives**:
1. **Assign to Berth L2** (adjacent berth, operational)
   - Available Monday 0800
   - Cost: Berth L2 slightly less efficient (3 cranes vs 4 at L1)

2. **Delay to Tuesday 0600** (after maintenance completion)
   - Wait time: 22 hours
   - Demurrage cost: 22 hours @ $300/hour = $6,600

3. **Partial operation Sunday + completion Tuesday**
   - Berth at L1 Sunday evening, discharge 40% before maintenance
   - Complete remaining 60% Tuesday after maintenance
   - Complex scheduling, potential for cargo re-stow errors

**AI Recommendation**: **Option 1** (Berth L2 on Monday) - Immediate berthing, minimal operational impact, avoids demurrage.

---

### 4. Emergency Maintenance (Unplanned) - Constraint ID: B-AVAIL-002-EMERGENCY

**Description**: Equipment failures require immediate maintenance, forcing berth closures with minimal advance notice.

**Emergency Scenarios**:
- **Crane breakdown**: Motor failure, hydraulic leak, structural crack
- **Fender damage**: Impact from vessel berthing error
- **Bollard failure**: Mooring line overload
- **Fire/electrical fault**: Safety shutdown
- **Quay structural damage**: Crack, settlement, corrosion

**Example Emergency Closure**:

**Incident**: Crane hydraulic failure at Berth M1
- **Time**: Tuesday 1430
- **Diagnosis**: Hydraulic pump failure, 8-hour repair
- **Estimated Ready**: Wednesday 2230

**Impacted Vessels**:
1. **MV Current Vessel** (at Berth M1):
   - 60% cargo completed, 4 hours remaining
   - **Decision**: Shift to Berth M2 to complete operations (2-hour delay, $5,000 cost)

2. **MV Scheduled Arrival** (ETB M1 Wednesday 0600):
   - **Original Plan**: Berth M1 at 0600
   - **Revised Plan**: Delay to Thursday 0600 (24-hour delay) OR assign to M3

**AI Priority Logic**:
```
IF window_vessel OR high_priority:
    ASSIGN to best_alternative_berth
ELSE IF standard_priority:
    IF demurrage_rate > threshold:
        ASSIGN to alternative_berth (accept suboptimal)
    ELSE:
        DELAY until primary_berth_ready
```

**Communication Protocol**:
1. **Immediate notification** (within 15 minutes of failure):
   - Harbor Master
   - Vessel agents (current + scheduled)
   - Terminal operators
   - Pilot station

2. **Status updates every 2 hours**:
   - Repair progress
   - Revised ETA for berth availability
   - Alternative berth options

---

## Operational Gap Management

### 5. Shift Handover Gaps - Constraint ID: B-AVAIL-004

**Rule**: `avoid_berth_operations_during_shift_handover ± 15_minutes`

**Type**: **SOFT** constraint (operational best practice)

**Description**: Labor shift changes create brief operational gaps as crews hand over equipment, brief next shift, and perform equipment checks.

**Shift Handover Times**:
- **0600 ± 15 min** (night → day shift)
- **1400 ± 15 min** (day → evening shift)
- **2200 ± 15 min** (evening → night shift)

**Impact on Berthing Operations**:
```
Shift Handover Activities:
- Crane operator handover: 10-15 minutes
- Stevedore gang briefing: 10-20 minutes
- Equipment inspection: 5-10 minutes
- Safety briefing: 5-10 minutes

Total Gap: 30-55 minutes reduced productivity
```

**Optimization Strategy**:
- **Avoid scheduling**:
  - Vessel berthing during handover (pilot/tug coordination affected)
  - Critical cargo operations during handover (reduced crane productivity)

- **Prefer scheduling**:
  - Berth preparation during handover (cleaning, inspection - non-critical)
  - Administrative tasks (documentation, tally)

**Example**:
**Vessel ETB**: Options are 1345 or 1445

**Analysis**:
- **1345 berthing**: Vessel secured by 1400, operations start immediately after shift handover (1430)
  - Slight delay waiting for new shift
  - Benefit: Full shift availability (1430-2200 = 7.5 hours)

- **1445 berthing**: Operations start immediately with new shift already on duty
  - Benefit: No handover gap, immediate productivity
  - Less total shift time available (1445-2200 = 7.25 hours)

**AI Recommendation**: **1445 berthing** (avoids shift handover complexity, immediate productivity)

---

### 6. Weather Window Optimization - Constraint ID: B-AVAIL-005

**Description**: Berthing operations should avoid known weather interruptions when possible.

**Weather Interruption Windows** (predictable patterns):
- **Storm approach**: Operations suspended 2-4 hours before arrival
- **Fog periods**: 0400-0800 visibility < 500m (seasonal)
- **High tide periods**: Brief operational pauses during tide peak (current effects)
- **Seasonal patterns**: Monsoon seasons, winter storms

**AI Weather-Aware Scheduling**:
```
IF forecast_storm_arrival < vessel_cargo_duration + 4_hours:
    RECOMMEND: Delay berthing until post-storm
ELSE IF forecast_fog_window_overlaps_berthing:
    RECOMMEND: Early berthing (before fog) or late berthing (after fog clears)
```

**Example**:
**Vessel**: 18-hour cargo operation
**Weather Forecast**: Storm in 24 hours

**Analysis**:
- **Immediate berthing**: Start 0800, planned completion 0200 next day
- **Storm arrival**: 0800 next day (30 hours from now)
- **Buffer**: 30 - 18 = 12 hours ✓ **SAFE**

**Decision**: Proceed with berthing - sufficient buffer before storm.

---

## Berth Utilization Optimization

### 7. Berth Idle Time Minimization - Constraint ID: B-UTIL-001

**Type**: **SOFT** constraint (commercial optimization)

**Description**: Maximize berth occupancy to increase port revenue and efficiency.

**Utilization Calculation**:
```
Berth Utilization % = (Occupied Hours / Total Available Hours) × 100

Target Benchmarks:
- High-efficiency ports: 70-85% utilization
- Medium-efficiency: 55-70% utilization
- Low-efficiency: <55% utilization

Optimal Range: 70-75%
(above 80% creates scheduling inflexibility, below 60% indicates underutilization)
```

**Idle Time Causes**:
1. **No vessel scheduled**: Demand gap
2. **Buffer time**: Between vessels (intentional)
3. **Maintenance**: Planned or emergency
4. **Weather**: Suspended operations
5. **Tide**: Waiting for tidal window
6. **Pilot/tug unavailability**: Resource constraints

**AI Idle Time Reduction Strategies**:
1. **Tight scheduling**: Reduce buffer times (within safe limits)
2. **Opportunistic berthing**: Assign lower-priority vessels to fill gaps
3. **Maintenance coordination**: Schedule during low-demand periods
4. **Tidal window optimization**: Maximize vessels per tidal cycle

**Example Optimization**:
```
Current Schedule:
Vessel A: 0800-1600 (8 hours)
Vessel B: 1800-0200 (8 hours) [2-hour gap]

Utilization: 16 occupied / 18 hours = 89% (high but inflexible)

Alternative Schedule:
Vessel A: 0800-1600 (8 hours)
Vessel C: 1630-1830 (2 hours) [opportunistic small vessel]
Vessel B: 1900-0300 (8 hours)

Utilization: 18 occupied / 19 hours = 95% (excellent)
```

---

## Integration with AI Berth Scheduler

### Query Example:
**Question**: "Can MV Atlantic Trader berth at L1 on Monday 0800?"

**Expected RAG Response**:
"No. Based on maintenance window constraints (B-AVAIL-002), Berth L1 has scheduled crane maintenance on Monday from 0600-1800 (12-hour shutdown for annual STS Crane #1 overhaul). MV Atlantic Trader requires 10 hours of cargo operations using cranes, which cannot be performed during the maintenance window.

Alternative options:
1. **Berth L2 on Monday 0800**: Adjacent berth, fully operational, 3 cranes available (vs 4 at L1). Slight productivity reduction but immediate berthing with no delay.
2. **Berth L1 on Tuesday 0600**: After maintenance completion, full 4-crane capacity, but requires 22-hour wait (demurrage: ~$6,600 at $300/hour).

Recommendation: Berth L2 on Monday (Option 1) - avoids demurrage cost and provides immediate berthing. The 1-crane difference has minimal impact on 10-hour cargo operation (extends to ~11 hours).

This is a HARD constraint - berths under maintenance cannot be used for cargo operations due to safety regulations and equipment unavailability."

---

## Related Documents

- Maintenance Schedule (Annual Calendar)
- Emergency Response Procedures
- Labor Shift Rosters
- Berth Utilization Reports (Monthly KPIs)

---

**Keywords**: berth availability, double-booking, maintenance windows, crane overhaul, shift handover, buffer time, berth utilization, idle time, emergency maintenance, operational gaps, berth scheduling, conflictresolution
