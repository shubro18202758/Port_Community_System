# Port Operations Manual: Window Vessel Operations & Contract Management

**Document Type**: Port Operations Manual - Critical Commercial Feature
**Category**: Layer 5 - Policy & Commercial Constraints (Window Vessels)
**Classification**: SOFT (high-weight), with HARD berth vacation requirements
**Applies To**: Scheduled liner services, berth window management, SLA compliance

---

## Overview

Window Vessel Operations are a **CRITICAL SMARTBERTH DIFFERENTIATOR** for managing scheduled liner services with contracted berthing windows. This feature handles the complexity of:
- Guaranteed berth availability at specific time windows
- Preemption of non-window vessels
- SLA penalty management
- Limited-time berth contracts
- Commercial settlements

Window vessels represent 30-50% of container port traffic and carry severe financial penalties ($50,000-200,000 per missed window) for schedule violations.

## Window Vessel Concept

### Definition

**Window Vessel**: A vessel operating on a fixed, published schedule (weekly, bi-weekly) with a contracted berthing window at specific berths.

**Characteristics**:
- **Fixed schedule**: Same day/time each week (e.g., every Wednesday 0800-2000)
- **Contracted berth**: Specific berth guaranteed (e.g., Berth P1)
- **Network dependencies**: Feeder vessels, cargo trains, trucks synchronized to schedule
- **High penalties**: $50,000-200,000 per missed/delayed window
- **Strategic importance**: Major shipping lines (Maersk, MSC, CMA CGM, Hapag-Lloyd)

---

## Constraint Definitions

### 1. Window Vessel ETA Priority - P-WINDOW-001

**Rule**: `IF vessel.has_contract_window = TRUE THEN priority_weight = 90 AND berth_must_be_available_at_window_start`

**Description**: Window vessels have near-HARD priority. Berths must be vacant at window start time.

**Window Contract Example**:
```
Vessel: MV Maersk Eindhoven
Service: Asia-Europe Express (AE7)
Schedule: Every Wednesday
Window: 0800-2000 (12-hour window)
Contracted Berth: P1 (dedicated container berth)
SLA Penalty: $50,000 if berth not available at 0800
```

---

### 2. Berth Vacation Priority - P-WINDOW-002

**Rule**: `IF window_vessel_approaching THEN current_occupant_must_vacate_or_expedite`

**Type**: **HARD** constraint (contractually enforceable)

**Description**: When a window vessel is approaching, the AI system must ensure the contracted berth is vacant by window start time, requiring:
1. Current occupant completes operations before window
2. Current occupant shifts to another berth
3. Current occupant accepts limited berth time contract
4. (Last resort) Window vessel delayed with SLA penalty payment

**Critical Scenario: Berth Vacation Required**

**Setup**:
- **Window Vessel**: MV Maersk Eindhoven, contracted window Wednesday 0800-2000
- **Current Situation** (Tuesday 1800):
  - Berth P1 occupied by MV Coastal Runner (tramp vessel)
  - Original ETD: Thursday 0600 (16 more hours of cargo work)
  - **Problem**: Window vessel arrives in 14 hours, but current vessel needs 16 hours
  - **Gap**: -2 hours conflict

**AI Decision Matrix**:

| Option | Description | Cost | Risk | Recommendation |
|--------|-------------|------|------|---------------|
| **A: Expedite** | Add 2 extra cranes, finish in 10 hours | $8,000 | Low | ⭐ **BEST** |
| **B: Shift** | Move to Berth P2 mid-operation | $12,000 | Medium | Backup |
| **C: Limited Time** | Vessel accepts partial discharge | $5,000 | Low | Alternative |
| **D: Delay Window** | Miss window, pay SLA penalty | $50,000 | High | ❌ Avoid |

**AI Recommendation**: **Option A (Expedite)**
- Lowest cost: $8,000
- No SLA breach
- Window vessel on time
- Current vessel completes all cargo

**Implementation**:
```
T-14 hours: AI detects potential conflict
T-12 hours: Generate options, calculate costs
T-10 hours: Notify terminal operations + vessel agent
T-8 hours: Deploy Cranes 3 & 4 to Berth P1
Wednesday 0400: MV Coastal Runner completes, departs
Wednesday 0600: Berth P1 vacant, prepared for window vessel
Wednesday 0800: MV Maersk Eindhoven berths (on-time) ✓
```

---

### 3. Limited Berth Time Contracts - P-WINDOW-003

**Rule**: `IF berth_required_for_window_vessel THEN current_vessel_may_accept_limited_time_contract`

**Type**: **HARD** (contractually binding once accepted)

**Description**: Tramp vessels can accept "Limited Berth Time" agreements where they berth with strict vacation deadlines to accommodate incoming window vessels.

**Limited Time Contract Template**:

```
┌─────────────────────────────────────────────────────────┐
│         LIMITED BERTH TIME AGREEMENT                    │
├─────────────────────────────────────────────────────────┤
│ Vessel: MV Bulk Trader                                  │
│ Berth: Q1                                               │
│ Berthing Time: 1200 Tuesday                             │
│ MAXIMUM BERTH TIME: 34 hours (must vacate by 2200 Wed) │
│                                                         │
│ Reason: Berth Q1 has window vessel arriving Thursday   │
│         MV CMA CGM Marco Polo (contracted window)      │
│                                                         │
│ Terms:                                                  │
│ • Vessel agrees to vacate 2 hours before window vessel │
│ • If cargo incomplete, shift to anchorage/Berth Q3     │
│ • Remaining cargo handled when alternative berth free  │
│                                                         │
│ Vessel Benefits:                                        │
│ • Immediate berthing (vs. 12-hour wait)                │
│ • 15% discount on port dues                            │
│ • Priority for next available berth (if cargo remains) │
│                                                         │
│ Penalties for Non-Compliance:                           │
│ • $25,000 per hour if berth not vacated on time       │
│ • Forced unberthing with tug costs charged to vessel  │
│                                                         │
│ Countdown Alerts:                                       │
│ • T-6 hours: First warning                             │
│ • T-2 hours: Final warning                             │
│ • T-30 minutes: Prepare for unberthing                 │
└─────────────────────────────────────────────────────────┘
```

**Acceptance Workflow**:
1. AI detects window vessel conflict 24-48 hours in advance
2. Generate limited-time contract offer
3. Send to vessel agent via Port Community System (PCS)
4. Agent accepts/rejects within 2 hours
5. If accepted: Contract activated, countdown timer starts
6. If rejected: Vessel waits for full berth time availability

**Example Execution**:
- **MV Bulk Trader** needs 48 hours for full cargo discharge
- **Limited-time offer**: 34 hours at Berth Q1
- **Agent decision**: **ACCEPTS** (better than 18-hour anchorage wait)
- **Result**:
  - 70% of cargo discharged in 34 hours
  - Vessel shifts to anchorage at T=34 hours
  - Remaining 30% discharged at Berth Q3 next day (8 hours)
  - Total time: 34 + 24 (anchorage) + 8 = 66 hours (vs. 48+18 wait = 66 hours FCFS)
  - **Benefit**: 15% port dues discount = $6,000 saved

---

### 4. Window Vessel Premium Payment - P-WINDOW-004

**Rule**: `IF non_window_vessel_willing_to_pay_premium THEN window_berth_may_be_available_at_premium_rate`

**Type**: **SOFT** (commercial negotiation)

**Description**: Non-window vessels can pay premium rates to access window berths during non-window periods.

**Premium Rate Structure**:
- **Off-peak hours** (non-window periods): 20-30% premium
- **Adjacent to window** (within 4 hours): 50% premium
- **Emergency requests**: 100% premium

**Example**:
- **Berth P1**: Window berth for Maersk (Wednesday 0800-2000 only)
- **Available**: Thursday-Tuesday (6 days per week)
- **MV Independent Trader** requests Berth P1 on Friday
- **Options**:
  1. Standard berth (Q1): Free, available immediately
  2. Premium berth (P1): +25% fee, better crane productivity
- **Calculation**:
  - Standard berth: $30,000 port dues, 16-hour turnaround
  - Premium berth: $37,500 port dues, 12-hour turnaround (better cranes)
  - Demurrage savings: 4 hours × $300/hour = $1,200
  - **Net cost**: $7,500 - $1,200 = $6,300 extra
- **Agent Decision**: Depends on demurrage rate and schedule pressure

---

### 5. SLA Penalty for Window Miss - P-WINDOW-005

**Rule**: `IF window_vessel_delayed THEN port_pays_SLA_penalty`

**Type**: **SOFT** (commercial penalty)

**Description**: If the port fails to provide the contracted window (berth unavailable, technical issues), the port authority pays SLA penalties to the shipping line.

**Penalty Structure**:
```
Delay Duration | Penalty Amount | Additional Consequences
---------------|----------------|----------------------
0-30 minutes   | $0             | Warning, documented
30-120 minutes | $15,000        | Formal complaint
2-6 hours      | $50,000        | Contract review
6-12 hours     | $100,000       | Executive escalation
>12 hours      | $200,000       | Contract termination risk
```

**Example: Missed Window Cost Analysis**

**Scenario**: Crane breakdown at Berth P1, repair needs 8 hours
- **Window Vessel**: MV Hapag Express, window 0800-2000
- **Crane Failure**: 0730 (30 min before window)
- **Repair Time**: 8 hours (ready by 1530)

**Impact**:
1. **SLA Penalty**: $50,000 (2-6 hour delay category)
2. **Network Disruption**: 4 feeder vessels delayed (cascade effect)
3. **Reputation Damage**: Shipping line trust degraded
4. **Future Contracts**: Risk of rate renegotiation

**Alternative Options** (AI evaluates):
| Option | Cost | Time | Decision |
|--------|------|------|----------|
| Repair crane (8 hrs) | $5,000 | 8 hrs | $50,000 SLA penalty |
| Shift to Berth P2 | $15,000 | 3 hrs | $15,000 penalty + shift cost = $30,000 |
| Emergency crane rental | $40,000 | 2 hrs | $15,000 penalty + rental = $55,000 |

**AI Recommendation**: **Shift to Berth P2** (lowest total cost: $30,000)

---

## Commercial Settlement Examples

### Scenario 1: Berth Displacement Negotiation

**Situation**:
- **MV Independent Spirit** (tramp) at Berth R1, needs 8 more hours
- **MV Hapag Express** (window) arriving in 6 hours

**AI-Generated Options**:

**Option 1: Independent Spirit Leaves Early**
- Remaining cargo: 1,200 TEU (30% of total)
- Complete at next port: Singapore (+5 days transit)
- Additional freight cost: $15,000
- Port compensation: $10,000 (goodwill payment)
- **Net cost to vessel**: $5,000
- **Benefit**: Window vessel on-time, no SLA penalty

**Option 2: Hapag Express Waits 2 Hours**
- SLA penalty: $20,000
- Network delay: 4 feeder vessels affected
- Estimated network cost: $25,000
- **Total cost**: $45,000

**AI Recommendation**: **Option 1** (port pays $10,000 to vessel, saves $35,000 vs. delaying window vessel)

**Settlement Agreement**:
```
Port Authority agrees to pay $10,000 to MV Independent Spirit
Vessel agrees to vacate Berth R1 by 1600
Remaining cargo completed at Singapore
Payment processed within 48 hours
```

**Audit Trail**:
- Timestamp: All communications logged
- Decision rationale: Cost-benefit analysis attached
- Contract reference: Window vessel SLA agreement cited
- Approving authority: Harbor Master signature
- Payment order: Finance department authorization

---

### Scenario 2: Window Vessel Delay Compensation (Reverse)

**Situation**: Window vessel (MV Maersk) delayed 4 hours due to storm, arrives at 1200 instead of 0800

**Port Response**:
- **No SLA penalty** charged to port (force majeure - weather)
- Berth held vacant from 0800-1200 (4-hour idle time)
- Port absorbs opportunity cost (~$8,000 lost revenue)
- Next window vessel schedule maintained (no cascade)

**Contractual Clause**: "Acts of God (weather, natural disasters) exempt from SLA penalties for both parties."

---

## AI Window Management Algorithms

### Predictive Window Conflict Detection

**Algorithm**: Scan schedule 48-72 hours ahead, identify potential window conflicts

**Detection Logic**:
```python
FOR each window_vessel in next_72_hours:
    window_start_time = vessel.window_start
    contracted_berth = vessel.berth_id

    # Check current occupant
    current_vessel = get_vessel_at_berth(contracted_berth, window_start_time)

    IF current_vessel EXISTS:
        estimated_ETD = current_vessel.ETD

        IF estimated_ETD > window_start_time:
            conflict_gap = estimated_ETD - window_start_time
            GENERATE conflict_resolution_options()
            NOTIFY stakeholders(48_hours_advance)
```

**Notification Recipients**:
- Harbor Master
- Berth Operations Manager
- Current vessel agent
- Window vessel agent
- Terminal operators

---

## Integration with AI Berth Allocator

### Query Example:
**Question**: "What happens if MV Coastal Runner can't finish before the window vessel arrives?"

**Expected RAG Response**:
"Based on window vessel operations (P-WINDOW-002), if MV Coastal Runner cannot complete cargo operations before MV Maersk Eindhoven's contracted window starts (Wednesday 0800), the AI system will generate berth vacation options:

1. **Expedite operations**: Add extra cranes to finish before 0800 (typical cost: $5,000-10,000)
2. **Shift to alternative berth**: Move vessel to Berth P2 mid-operation (cost: $10,000-15,000)
3. **Limited berth time contract**: Vessel accepts partial discharge with 15% port dues discount
4. **Window vessel delay**: Port pays $50,000 SLA penalty (LAST RESORT)

The AI prioritizes options in cost-ascending order. Window vessels have priority weight of 90 (vs. 50 for tramp vessels), and contractual SLA penalties create strong incentive to maintain window schedules. This is effectively a HARD constraint due to severe financial penalties for violations."

---

## Related Documents

- Commercial Contract Templates
- SLA Performance Standards
- Window Vessel Master Agreements
- Settlement & Dispute Resolution Procedures

---

**Keywords**: window vessels, liner services, scheduled services, berth windows, SLA penalties, limited berth time, berth vacation, commercial settlement, contract management, Maersk, MSC, CMA CGM, network scheduling
