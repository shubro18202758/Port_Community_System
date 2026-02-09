# Port Operations Manual: Priority & Commercial Constraints

**Document Type**: Port Operations Manual - Soft Constraints (Optimizable)
**Category**: Layer 5 - Policy, Priority & Commercial Constraints
**Classification**: SOFT (weight-based optimization), some HARD (government vessels)
**Applies To**: Vessel prioritization, commercial negotiations, berth assignments

---

## Overview

Priority and commercial constraints govern how vessels are ranked when competing for limited berth capacity. These are primarily SOFT constraints that can be optimized based on priority weights, commercial terms, and strategic considerations. However, government/military vessels have near-HARD priority status.

## Vessel Priority System

### Priority Weight Hierarchy

| Priority Level | Weight | Vessel Type | Can Be Overridden? |
|---------------|--------|-------------|-------------------|
| **P-PRIO-001: Government/Navy** | 100 | Military vessels, Coast Guard, Government | Rarely (national security) |
| **P-PRIO-002: Emergency/Distress** | 95 | Medical emergency, vessel in distress | Never (safety of life) |
| **P-PRIO-003: Window Vessels** | 90 | Scheduled liner services | High cost to override |
| **P-PRIO-004: Perishable Cargo** | 80 | Reefers, live animals, time-sensitive | Moderate cost |
| **P-PRIO-005: Transshipment Hubs** | 75 | Feeder vessels feeding main lines | Moderate |
| **P-PRIO-006: Strategic Customers** | 70 | Long-term contract holders | Negotiable |
| **P-PRIO-007: FCFS (Default)** | 50 | Standard tramp vessels | Standard queue |
| **P-PRIO-008: Low Priority** | 30 | Vessels with no urgency | Can wait |

---

## Priority Rule Examples

### 1. Government/Navy Vessel Priority Override - P-PRIO-001

**Rule**: `IF vessel.type = 'GOVERNMENT' OR 'NAVY' THEN priority_weight = 100`

**Description**: Military and government vessels have near-absolute priority, typically for national security, humanitarian missions, or official state visits.

**Example Scenario**:

**Current Berth M1 Status**:
- **MV Commercial Trader**: Confirmed for 1400 arrival, pilot assigned (Priority: 50)

**Incoming Request**:
- **INS Vikrant** (Indian Navy Aircraft Carrier)
- ETA: 1400, requires Berth M1 specifically (only berth with required depth/length)
- Priority: 100 (Government vessel)

**AI Decision**:
```
Priority Comparison: 100 (Navy) >> 50 (Commercial)
Action: Override commercial booking
```

**Resolution**:
1. INS Vikrant assigned Berth M1 at 1400
2. MV Commercial Trader reassigned to Berth M2 (similar capacity berth)
3. No demurrage charged to Commercial Trader (port directive - force majeure)
4. Commercial Trader agent notified 6 hours in advance

**Commercial Impact**:
- Port Authority absorbs reassignment cost (~$5,000 pilot/tug re-routing)
- Commercial Trader NOT penalized (government priority is non-commercial)

**Rationale**: National security and government operations take absolute precedence. This is effectively a HARD constraint in practice.

---

### 2. Emergency/Distress Vessels - P-PRIO-002

**Rule**: `IF vessel.status = 'DISTRESS' OR 'MEDICAL_EMERGENCY' THEN priority = ABSOLUTE`

**Description**: Vessels with medical emergencies, engine failure, or distress situations receive immediate priority under SOLAS (Safety of Life at Sea) conventions.

**Example**:
- **MV Ocean Star**: Crew member with heart attack, requires immediate medical evacuation
- **Current Port Status**: 3 vessels in queue, estimated wait 8 hours
- **Decision**: MV Ocean Star given immediate berth access, bypassing queue
- **Medical evacuation**: Helicopter landing arranged, patient transferred to hospital within 2 hours

**SOLAS Requirement**: This is an international maritime law obligation - ports MUST provide emergency access. No commercial considerations apply.

---

### 3. Window Vessel Priority (Scheduled Liners) - P-PRIO-003

**Rule**: `IF vessel.liner_service = TRUE AND vessel.has_contract_window = TRUE THEN priority_weight = 90`

**Description**: Container liner services operating on fixed weekly schedules have contracted berthing windows. Missing these windows disrupts entire network schedules.

**Window Vessel Characteristics**:
- Weekly fixed schedule (e.g., every Monday 0800-2000)
- Contracted berth allocation
- Feeder vessels depend on main liner timing
- High penalty for window violations ($50,000-200,000 per missed window)

**Example**:
- **MV Maersk Eindhoven**: Weekly liner, contracted window Wednesday 0800-2000 at Berth P1
- **Current Berth P1 occupant**: MV Coastal Runner (tramp vessel, no fixed schedule)
- **Problem**: MV Coastal Runner needs 16 more hours, but window vessel arrives in 14 hours

**AI Priority Comparison**:
```
Maersk (Window): Weight 90, SLA penalty if delayed: $50,000
Coastal Runner (Tramp): Weight 50, demurrage if shifted: $8,000/day

Decision: Window vessel takes priority
```

**Options Generated**:
1. **Expedite Coastal Runner** - Add 2 extra cranes, finish in 10 hours (Cost: $8,000)
2. **Shift Coastal Runner** to Berth P2 mid-operation (Cost: $12,000)
3. **Delay window vessel** - Pay $50,000 SLA penalty + network disruption

**AI Recommendation**: Option 1 (expedite current vessel) - lowest total cost, no SLA breach.

---

### 4. Perishable Cargo Priority - P-PRIO-004

**Rule**: `IF vessel.cargo_type = 'PERISHABLE' THEN priority_weight = 80`

**Description**: Vessels carrying time-sensitive perishable cargo (food, pharmaceuticals, live animals) get elevated priority due to cargo degradation risk.

**Perishable Cargo Categories**:
| Cargo Type | Shelf Life at Port Temp | Priority Justification |
|-----------|------------------------|----------------------|
| **Bananas/Fruits** | 24-48 hours | Ripening continues, quality degrades |
| **Pharmaceuticals** | 12-24 hours (temperature-sensitive) | Regulatory temperature compliance |
| **Live Animals** | Immediate (welfare concern) | Animal welfare regulations |
| **Fresh Seafood** | 12-24 hours | Spoilage risk, health hazard |
| **Frozen Goods** | 48-72 hours (if reefers functioning) | Quality degradation if temp rises |

**Example Scenario**:
**Two vessels arrive simultaneously at 0800**:
- **MV Fruit Express**: 5,000 MT Bananas (Priority: 80)
- **MV General Star**: 5,000 MT Steel Coils (Priority: 50)

**Single Berth Available**: Berth N1

**AI Decision**:
```
Perishable Priority: 80 > General Cargo: 50
Decision: MV Fruit Express → Berth N1 (immediate berthing)
         MV General Star → Anchorage (wait 8-12 hours)
```

**Economic Rationale**:
- Bananas have 48-hour port shelf life at 28°C ambient temperature
- Delay of 8 hours = acceptable
- Delay of 24+ hours = significant quality loss ($200-500 per ton)
- Steel can wait indefinitely without quality impact

**Commercial Negotiation**: MV General Star agent can pay premium ($15,000) to override priority, but typically not economic.

---

### 5. First-Come-First-Served (FCFS) - P-PRIO-007

**Rule**: `IF no_special_priority THEN priority = ETA_timestamp (earliest gets priority)`

**Description**: Default priority system for standard tramp vessels with no special status. Queue is based purely on arrival time.

**FCFS Queue Example**:
```
Position | Vessel Name      | ETA  | Priority Weight | Status
---------|-----------------|------|----------------|--------
1        | MV Atlantic 1   | 0600 | 50 (FCFS)      | Berthing
2        | MV Pacific 2    | 0630 | 50 (FCFS)      | Waiting (30 min)
3        | MV Indian 3     | 0700 | 50 (FCFS)      | Waiting (1 hour)
4        | MV Mediterranean| 0730 | 50 (FCFS)      | Waiting (1.5 hours)
```

**Queue Jumping Scenarios**:
- **Window vessel (Priority 90)** arrives at 0745 → Jumps to position 1 or 2
- **Perishable cargo (Priority 80)** arrives at 0715 → Jumps ahead of Mediterranean
- **Government vessel (Priority 100)** → Immediate berth access

---

## Commercial Optimization

### 6. Demurrage Minimization - P-COMM-001

**Description**: Demurrage is penalty cost charged to vessel operator for exceeding agreed laytime (free cargo handling period).

**Demurrage Rate Structure**:
- **Container vessels**: $15,000-50,000 per day
- **Bulk carriers**: $8,000-25,000 per day
- **Tankers**: $20,000-80,000 per day
- **ULCV/VLCC**: $80,000-150,000 per day

**AI Optimization Example**:

**Vessel**: MV Bulk Trader
- Current queue position: 3rd in line
- Estimated wait: 18 hours
- Demurrage rate: $15,000/day = $11,250 for 18 hours

**Premium Berth Option**:
- Berth T1 available in 2 hours (for premium payment)
- Premium charge: $8,000
- Demurrage saved: $10,000 (16 hours)

**Cost-Benefit**:
```
Net Savings = Demurrage Saved - Premium Cost
            = $10,000 - $8,000
            = $2,000 benefit
```

**AI Recommendation**: Offer premium berthing option to vessel agent. If accepted, port earns $8,000 revenue and vessel saves $2,000 vs. waiting.

---

### 7. Berth Productivity Targets - P-COMM-003

**Description**: Ports have contractual berth productivity commitments (container moves per hour, tons per day for bulk).

**Productivity KPIs**:
- **Container terminals**: 25-35 moves per hour (MPH) per crane
- **Bulk terminals**: 3,000-10,000 tons per day
- **Liquid terminals**: 500-2,000 m³ per hour

**Penalty Structure**:
- **Below 80% target**: Warning
- **Below 70% target**: $5,000-15,000 penalty per vessel
- **Below 60% target**: SLA breach, contract renegotiation

**AI Scheduling to Meet Productivity**:
- **Allocate faster berths** to vessels with tight laytime
- **Assign more cranes/gangs** to vessels approaching demurrage
- **Avoid berth/crane maintenance** during peak periods

---

### 8. Strategic Customer Relationships - P-PRIO-006

**Rule**: `IF vessel.operator IN strategic_partners THEN priority_weight = 70`

**Description**: Long-term contract holders (annual agreements, volume commitments) receive preferential treatment.

**Strategic Partner Benefits**:
- Priority weight: 70 (vs. 50 standard)
- Guaranteed berth windows for regular calls
- Discounted port dues (5-15% reduction)
- Dedicated account management
- Preferred crane allocation

**Example**:
- **Maersk Line**: 20-year port partnership, 52 vessel calls/year
- **Priority**: 70 (strategic partner)
- **Benefit**: Jumps ahead of FCFS queue (priority 50), second only to window vessels (90) and perishables (80)

**Commercial Rationale**: Long-term partners provide stable revenue, justify preferential treatment to maintain business relationship.

---

## Integration with AI Priority Module

### Query Example:
**Question**: "Why did INS Vikrant (Navy ship) override MV Commercial Trader's berth booking?"

**Expected RAG Response**:
"Based on priority rules (P-PRIO-001), government and military vessels have priority weight of 100, which is the highest in the priority hierarchy (except life-threatening emergencies). MV Commercial Trader has standard FCFS priority of 50. The priority difference (100 vs. 50) triggered an automatic override where INS Vikrant was assigned the originally confirmed berth.

Per port policy, MV Commercial Trader was reassigned to an equivalent berth (M2) without demurrage penalty, as government vessel priority is considered force majeure. This override is justified by national security considerations and is effectively a HARD constraint in practice, though technically classified as SOFT (high-weight priority)."

---

## Related Documents

- Commercial Contract Terms & Conditions
- SLA Performance Standards
- Window Vessel Operating Agreements
- Port Tariff Schedule

---

**Keywords**: vessel priority, government vessels, emergency vessels, window vessels, liner services, perishable cargo, FCFS, demurrage, commercial optimization, strategic customers, berth productivity, priority weights
