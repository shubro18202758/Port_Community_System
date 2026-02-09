# Port Operations Manual: Master Constraint Decision Framework

**Document Type**: Port Operations Manual - Decision Framework & Summary
**Category**: All Layers - Integrated Constraint System
**Classification**: Framework for constraint hierarchy and decision logic
**Applies To**: AI berth allocation system, conflict resolution, priority management

---

## Executive Summary

This document provides the **MASTER DECISION FRAMEWORK** for the SmartBerth AI Berth Allocation System, integrating all 6 constraint layers into a unified decision-making process.

**Key Principle**: Constraints are evaluated in order of **rigidity** (HARD before SOFT) and **safety criticality** (safety before commercial).

---

## Constraint Hierarchy Overview

### Constraint Classification

| Layer | Constraint Category | Type | Override? | Typical Examples |
|-------|-------------------|------|-----------|-----------------|
| **6** | Navigation Safety (UKC) | HARD | ❌ NEVER | Under keel clearance, grounding prevention |
| **1** | Vessel Physical Dimensions | HARD | ❌ NEVER | LOA, beam, draft, air draft |
| **2** | Berth Physical Limits | HARD | ❌ NEVER | Fender capacity, bollard SWL, quay load |
| **1** | Cargo Compatibility | HARD | ❌ NEVER | Cargo type match, DG segregation |
| **2** | Berth Specialization | HARD | ❌ NEVER | Container/bulk/liquid terminals |
| **3** | Pilot/Tug Availability | HARD | ⚠️ RARELY | Pilot certification, tug bollard pull |
| **4** | Tidal Windows | HARD | ❌ NEVER | High tide required for deep draft |
| **4** | Critical Weather | HARD | ❌ NEVER | Crane shutdown winds (>40 knots), fog |
| **2** | Maintenance Windows | HARD | ⚠️ RARELY | Scheduled crane overhauls |
| **2** | Berth Occupancy | HARD | ❌ NEVER | No double-booking |
| **4** | Moderate Weather | SOFT | ✓ YES | Rain delay, wind 25-35 knots |
| **5** | Priority Rules | SOFT | ✓ YES | Window vessels, perishable cargo |
| **5** | Commercial Terms | SOFT | ✓ YES | Demurrage optimization, premiums |
| **3** | Labor Optimization | SOFT | ✓ YES | Shift timing, gang availability |

---

## AI Decision Flowchart

### Sequential Constraint Evaluation Process

```
┌─────────────────────────────────────────────────────────────┐
│                 INCOMING BERTH REQUEST                      │
│        (Vessel ID, ETA, Cargo Type, Specifications)         │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: PHYSICAL FEASIBILITY (Layer 1 + 6)                │
│ ─────────────────────────────────────────────────────────── │
│ ✓ LOA ≤ Berth Max LOA?                                      │
│ ✓ Beam ≤ Berth Max Beam?                                    │
│ ✓ Draft ≤ Available Depth (with UKC)?                       │
│ ✓ Air Draft ≤ Terminal Height Clearance?                    │
│ ✓ GT ≤ Berth Max GT?                                        │
│                                                             │
│ IF ANY = NO → ❌ REJECT (Physical Incompatibility)          │
│ IF ALL = YES → ✓ Proceed to Stage 2                        │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: CARGO & BERTH COMPATIBILITY (Layer 1 + 2)         │
│ ─────────────────────────────────────────────────────────── │
│ ✓ Cargo Type matches Berth Specialization?                  │
│ ✓ DG Segregation requirements met?                          │
│ ✓ Reefer plugs sufficient (if needed)?                      │
│ ✓ Pipeline type compatible (if liquid cargo)?               │
│ ✓ RoRo ramp available (if RoRo vessel)?                     │
│ ✓ Crane outreach adequate?                                  │
│ ✓ Fender/Bollard capacity adequate?                         │
│                                                             │
│ IF ANY = NO → Filter to compatible berths only             │
│ IF NONE COMPATIBLE → ❌ REJECT                              │
│ IF ≥1 COMPATIBLE → ✓ Proceed to Stage 3                    │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 3: RESOURCE AVAILABILITY (Layer 3)                   │
│ ─────────────────────────────────────────────────────────── │
│ ✓ Qualified pilot available at ETA?                         │
│ ✓ Sufficient tugs available (number + bollard pull)?        │
│ ✓ Crane operators certified?                                │
│ ✓ Stevedore gangs available (if needed)?                    │
│                                                             │
│ IF RESOURCES UNAVAILABLE →                                  │
│   Calculate earliest available time                         │
│   Delay vessel ETA to match resource availability           │
│                                                             │
│ ✓ Proceed to Stage 4                                       │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 4: TEMPORAL & ENVIRONMENTAL WINDOWS (Layer 4)        │
│ ─────────────────────────────────────────────────────────── │
│ ✓ Tidal window adequate (if deep draft)?                    │
│ ✓ Weather acceptable (wind, visibility, waves)?             │
│ ✓ Time-of-day restrictions met (if applicable)?             │
│ ✓ Channel traffic window available (if one-way)?            │
│                                                             │
│ IF WINDOW UNAVAILABLE →                                     │
│   Schedule for next valid window                            │
│   (e.g., next high tide, after fog clears)                  │
│                                                             │
│ IF CRITICAL WEATHER UNSAFE → ❌ DELAY (Hard constraint)     │
│ IF MODERATE WEATHER → Evaluate with Stage 5 (Soft)         │
│                                                             │
│ ✓ Proceed to Stage 5                                       │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 5: PRIORITY & COMMERCIAL OPTIMIZATION (Layer 5)      │
│ ─────────────────────────────────────────────────────────── │
│ • Assign priority weight to vessel                          │
│ • Check for window vessel conflicts                         │
│ • Evaluate commercial terms (demurrage, premium)            │
│ • Check berth availability (including maintenance)          │
│                                                             │
│ IF BERTH OCCUPIED BY LOWER PRIORITY VESSEL →               │
│   Generate conflict resolution options:                     │
│   1. Expedite current vessel                                │
│   2. Shift current vessel to alternative berth              │
│   3. Offer limited berth time contract                      │
│   4. Delay incoming vessel (if lower priority)              │
│                                                             │
│ IF WINDOW VESSEL + CONFLICT →                              │
│   High-priority resolution required                         │
│   (Avoid SLA penalty $50K-200K)                            │
│                                                             │
│ ✓ Select optimal berth from compatible options             │
└───────────────────────┬─────────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ STAGE 6: FINAL BERTH ALLOCATION                            │
│ ─────────────────────────────────────────────────────────── │
│ • Assign specific berth                                     │
│ • Schedule pilot, tugs, resources                           │
│ • Reserve berth in system                                   │
│ • Generate notifications to stakeholders                    │
│ • Log decision rationale in audit trail                     │
│                                                             │
│ ✓ BERTH ALLOCATED                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Constraint Override Rules

### When Can HARD Constraints Be Overridden?

| Constraint Type | Override Permitted? | Conditions | Authority Level |
|----------------|-------------------|------------|----------------|
| **Physical Dimensions** | ❌ NEVER | Laws of physics cannot be overridden | N/A |
| **UKC/Navigation Safety** | ❌ NEVER | Grounding risk unacceptable | N/A |
| **Cargo Compatibility** | ❌ NEVER | Safety/contamination risk | N/A |
| **Fender/Bollard Capacity** | ❌ NEVER | Structural damage risk | N/A |
| **Pilot Certification** | ⚠️ EXCEPTIONAL | Life-threatening emergency only | Port Authority Director |
| **Tidal Windows** | ❌ NEVER | Grounding risk | N/A |
| **Critical Weather (>40 knots)** | ❌ NEVER | Safety of life at sea | N/A |
| **Maintenance Windows** | ⚠️ EXCEPTIONAL | Emergency vessel (distress) | Harbor Master |
| **Window Vessel SLA** | ✓ YES | Commercial negotiation, penalty payment | Commercial Manager |

**Key Principle**: Safety-critical HARD constraints (marked ❌ NEVER) are **ABSOLUTE** and cannot be overridden under any circumstances. Economic, political, or operational pressures do not apply.

---

## Conflict Resolution Priority Matrix

### Multi-Vessel Conflict Resolution

**Scenario**: Two vessels request same berth, same time window

**Priority Comparison Logic**:

| Vessel A | Vessel B | Decision | Rationale |
|---------|---------|----------|-----------|
| Government (100) | Commercial (50) | **A wins** | National security priority |
| Emergency (95) | Window (90) | **A wins** | Safety of life at sea |
| Window (90) | Perishable (80) | **A wins** | SLA penalty avoidance |
| Perishable (80) | Strategic (70) | **A wins** | Cargo degradation risk |
| Strategic (70) | FCFS (50) | **A wins** | Long-term contract holder |
| FCFS (50) | FCFS (50) | **Earlier ETA wins** | First-come-first-served tie-breaker |

**Commercial Override Conditions**:
```
IF vessel_B.priority_weight < vessel_A.priority_weight:
    IF vessel_B.willing_to_pay_premium > (priority_difference × base_rate):
        vessel_B MAY override vessel_A
    ELSE:
        vessel_A retains priority
```

**Example Commercial Override**:
- Vessel A (Strategic, Priority 70): Confirmed for Berth X at 1400
- Vessel B (FCFS, Priority 50): Willing to pay $20,000 premium for 1400 slot
- Priority Gap: 70 - 50 = 20 points
- Base Rate: $500/point
- Required Premium: 20 × $500 = $10,000
- **Vessel B Offer**: $20,000 (exceeds requirement)
- **Decision**: Vessel B may override if Vessel A willing to reschedule for compensation

---

## Scoring & Ranking System

### Multi-Factor Berth Scoring (When Multiple Compatible Berths)

**Scoring Formula** (100-point scale):
```
Total Score = (Physical_Fit × 0.25)
            + (Equipment_Match × 0.20)
            + (Location_Convenience × 0.15)
            + (Historical_Performance × 0.10)
            + (Resource_Availability × 0.10)
            + (Waiting_Time_Reduction × 0.10)
            + (Commercial_Terms × 0.10)

Where each component scored 0-100
```

**Example Calculation**:

**Vessel**: Container vessel (280m LOA, 2,000 TEU)

| Berth | Physical Fit | Equipment | Location | Historical | Resources | Waiting Time | Commercial | **Total Score** |
|-------|-------------|-----------|----------|-----------|----------|--------------|-----------|-----------------|
| **A1** | 90 (perfect) | 95 (4 cranes) | 100 (closest) | 85 (good record) | 90 (all available) | 100 (immediate) | 80 (standard) | **90.5** ⭐ |
| **A2** | 85 (good) | 90 (4 cranes) | 70 (farther) | 80 (decent) | 85 (pilot delay 30m) | 70 (1h wait) | 90 (premium berth) | **82.0** |
| **A3** | 100 (oversized) | 60 (3 cranes) | 60 (far) | 90 (excellent) | 95 (all ready) | 50 (2h wait) | 75 (older berth) | **76.0** |

**AI Recommendation**: **Berth A1** (highest score: 90.5) - Best overall fit considering all factors.

---

## Real-Time Constraint Monitoring

### Dynamic Constraint Re-Evaluation

**Trigger Events for Re-Evaluation**:
1. **Weather changes**: Wind speed increases, fog rolls in
2. **Resource failures**: Crane breakdown, pilot illness, tug unavailable
3. **Schedule changes**: Vessel ETA updates, delays
4. **Emergency insertions**: Government vessel, medical emergency
5. **Tidal changes**: Tide lower than forecast
6. **Berth issues**: Damage, maintenance needed

**Re-Evaluation Algorithm**:
```
ON trigger_event:
    FOR each affected_vessel IN scheduled_vessels:
        RE_RUN constraint_evaluation_stages_1_through_6
        IF new_constraints_violated:
            GENERATE updated_berth_assignment
            NOTIFY stakeholders
            LOG change_rationale
```

**Example Dynamic Re-Assignment**:
```
T-0:00: MV Container King assigned to Berth H1, ETA 1400
T+0:30: Weather update - Wind increasing to 38 knots by 1400
T+0:35: AI re-evaluates - Berth H1 exposed, wind-sensitive
T+0:40: AI generates alternatives:
        Option 1: Shift to Berth H2 (sheltered)
        Option 2: Delay ETA to 1800 (after wind decreases)
T+0:45: AI recommends Option 1 (Berth H2)
T+0:50: Vessel agent notified, accepts H2
T+1:00: Updated berth assignment confirmed
```

---

## Integration with AI Decision Engine

### Query Example 1:
**Question**: "Why was my vessel assigned to Berth B2 instead of the requested Berth B1?"

**Expected RAG Response**:
"Based on the master constraint decision framework, your vessel underwent 6-stage evaluation:

**Stage 1-2 (Physical/Cargo)**: Both B1 and B2 were compatible.

**Stage 3 (Resources)**: Berth B1 requires 4 crane operators, but only 3 were available at your ETA. Berth B2 has 3 cranes (matching available operators).

**Stage 4 (Temporal)**: No tidal/weather constraints.

**Stage 5 (Priority)**: Your vessel (FCFS priority 50) and another vessel assigned to B1 had similar priority, but B1 was already confirmed to a window vessel (priority 90) with overlapping time.

**Stage 6 (Final Selection)**: Berth B2 scored 85/100 vs B1's theoretical 90/100. The AI prioritized immediate berthing with available resources (B2) over waiting for optimal berth (B1 with 2-hour delay for crane operators).

**Decision Rationale**: Avoiding 2-hour delay saves ~$600 demurrage, outweighing slight productivity reduction from 3 vs 4 cranes (10-15 minute extension on 8-hour cargo operation)."

### Query Example 2:
**Question**: "Can this constraint be overridden for my high-priority cargo?"

**Expected RAG Response**:
"Based on constraint classification, the specific constraint preventing your berth assignment is: [Constraint ID and Description].

**Constraint Type**: [HARD / SOFT]

**Override Possibility**:
- If HARD (safety-critical): ❌ **Cannot be overridden** - Physical/safety constraints are absolute. Options are: [Alternative berths / Wait for valid window / Alternative port].
- If SOFT (commercial/operational): ✓ **May be optimized** through: [Premium payment / Priority upgrade / Commercial negotiation / Window vessel coordination].

**Your specific case**: [Detailed analysis of the constraint, why it exists, what alternatives are available, and commercial options if applicable]."

---

## Summary: Constraint Evaluation Checklist

**For AI System (Sequential Evaluation)**:
```
☐ Stage 1: Physical dimensions compatible?
☐ Stage 2: Cargo and berth specialization match?
☐ Stage 3: Resources (pilot, tugs, labor) available?
☐ Stage 4: Tidal/weather windows valid?
☐ Stage 5: Priority conflicts resolved?
☐ Stage 6: Final berth selected and scheduled?
```

**For Human Operators (Override Verification)**:
```
☐ Is constraint classification HARD or SOFT?
☐ If HARD: Is this safety-critical (never override)?
☐ If SOFT: What is commercial cost of override?
☐ Are all stakeholders notified of deviation?
☐ Is override authority level sufficient?
☐ Is audit trail documented?
```

---

## Related Documents

- All Layer 1-6 Constraint Documents (01-09)
- Commercial Contract Terms
- Safety Management System
- Audit & Compliance Procedures

---

**Keywords**: constraint framework, decision hierarchy, hard constraints, soft constraints, priority matrix, conflict resolution, berth scoring, constraint override, master decision logic, AI allocation system, sequential evaluation, real-time monitoring
