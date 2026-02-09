# SmartBerth AI - Berth Allocation Constraint Framework
## Consolidated Constraints with Practical Examples

---

## EXECUTIVE SUMMARY

This document defines the complete constraint framework for the SmartBerth AI Berth Planning & Optimization Module. The constraints are organized into **6 layers** with clear classification as **HARD** (must satisfy) or **SOFT** (optimizable with penalty/weight).

### Target Terminal Profile
| Parameter | Requirement |
|-----------|-------------|
| Minimum Berths | 5+ berths |
| Berth Occupancy | 50-70%+ |
| Terminal Types | Container, Bulk, Multi-purpose |

---

## CONSTRAINT CLASSIFICATION OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SMARTBERTH CONSTRAINT HIERARCHY                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  LAYER 1: VESSEL-LEVEL CONSTRAINTS                          [Mostly HARD]  │
│  ├── 1.1 Physical Dimensions (LOA, Beam, Draft, Air Draft)                 │
│  ├── 1.2 Vessel Type & Cargo Compatibility                                 │
│  └── 1.3 Vessel Readiness (Pilot, Tug, Documentation)                      │
│                                                                             │
│  LAYER 2: BERTH / TERMINAL-LEVEL CONSTRAINTS                [Mostly HARD]  │
│  ├── 2.1 Berth Physical Constraints                                        │
│  ├── 2.2 Berth Specialization & Equipment                                  │
│  └── 2.3 Berth Availability & Maintenance                                  │
│                                                                             │
│  LAYER 3: OPERATIONAL RESOURCE CONSTRAINTS                  [HARD + SOFT]  │
│  ├── 3.1 Pilotage Resources                                                │
│  ├── 3.2 Towage Resources                                                  │
│  └── 3.3 Terminal Labor & Equipment                                        │
│                                                                             │
│  LAYER 4: TEMPORAL & ENVIRONMENTAL CONSTRAINTS              [HARD + SOFT]  │
│  ├── 4.1 Tidal Windows                                                     │
│  ├── 4.2 Weather Conditions                                                │
│  └── 4.3 Time-of-Day Restrictions                                          │
│                                                                             │
│  LAYER 5: POLICY, PRIORITY & COMMERCIAL CONSTRAINTS         [Mostly SOFT]  │
│  ├── 5.1 Vessel Priority Rules                                             │
│  ├── 5.2 Window Vessel Contracts (NEW)                                     │
│  ├── 5.3 Contractual Berth Agreements                                      │
│  └── 5.4 Commercial Penalty Optimization                                   │
│                                                                             │
│  LAYER 6: UKC & NAVIGATION SAFETY CONSTRAINTS               [ALL HARD]     │
│  ├── 6.1 Under Keel Clearance (UKC)                                        │
│  ├── 6.2 Channel Navigation                                                │
│  └── 6.3 Anchorage Management                                              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# LAYER 1: VESSEL-LEVEL CONSTRAINTS

## 1.1 Physical Dimensions (HARD)

These constraints are **non-negotiable** - physical incompatibility means NO allocation possible.

| Constraint ID | Constraint | Formula | Type |
|---------------|------------|---------|------|
| V-DIM-001 | Length Overall (LOA) | `vessel.loa ≤ berth.max_loa` | HARD |
| V-DIM-002 | Beam | `vessel.beam ≤ berth.max_beam` | HARD |
| V-DIM-003 | Static Draft | `vessel.draft ≤ berth.max_draft` | HARD |
| V-DIM-004 | Air Draft | `vessel.air_draft ≤ terminal.max_air_draft` | HARD |
| V-DIM-005 | Gross Tonnage Limit | `vessel.gt ≤ berth.max_gt` | HARD |

### Practical Examples

#### Example 1.1.1: LOA Constraint Violation
```
SCENARIO: MV Pacific Fortune (Container Vessel)
─────────────────────────────────────────────────
Vessel LOA: 366 meters (Post-Panamax)
Available Berths at Terminal:
  • Berth A1: Max LOA = 350m  ❌ REJECTED (366 > 350)
  • Berth A2: Max LOA = 400m  ✓ ELIGIBLE
  • Berth A3: Max LOA = 320m  ❌ REJECTED (366 > 320)

AI Decision: Only Berth A2 is physically compatible.
Berth A1 and A3 are removed from candidate list immediately.
```

#### Example 1.1.2: Draft Constraint with Tidal Dependency
```
SCENARIO: MV Iron Carrier (Bulk Carrier, Fully Loaded)
─────────────────────────────────────────────────
Vessel Arrival Draft: 14.5 meters
Berth B3 Specifications:
  • Charted Depth: 14.0 meters
  • High Tide Addition: +1.2 meters
  • Available Depth at High Tide: 15.2 meters

AI Decision: 
  • At Low Tide: ❌ REJECTED (14.5 > 14.0)
  • At High Tide: ✓ ELIGIBLE (14.5 < 15.2)
  
Constraint: HARD, but time-dependent.
AI schedules berthing within tidal window (HW ± 2 hours).
```

#### Example 1.1.3: Air Draft Constraint (Bridge/Gantry)
```
SCENARIO: MV Coastal Pride at River Terminal
─────────────────────────────────────────────────
Vessel Air Draft (keel to highest point): 52 meters
Route to Berth requires passing under:
  • Highway Bridge: Clearance = 55 meters  ✓ OK
  • Gantry Crane: Clearance = 48 meters    ❌ BLOCKED

AI Decision: Vessel cannot reach Berth C1.
Alternative: Assign to outer berth (Berth C5) with no air draft restriction.
```

---

## 1.2 Vessel Type & Cargo Compatibility (HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| V-CARGO-001 | Cargo Type Match | Berth must handle vessel's cargo type | HARD |
| V-CARGO-002 | Hazardous Cargo (DG) | DG-certified berth required | HARD |
| V-CARGO-003 | Reefer Capability | Power points for refrigerated containers | HARD |
| V-CARGO-004 | Tank/Liquid Handling | Pipeline & manifold compatibility | HARD |
| V-CARGO-005 | RoRo Ramp | Stern/bow ramp compatibility | HARD |

### Practical Examples

#### Example 1.2.1: Cargo Type Mismatch
```
SCENARIO: MV Grain Master (Bulk Carrier with Wheat)
─────────────────────────────────────────────────
Cargo: 45,000 MT of Wheat (Dry Bulk)
Terminal Available Berths:
  • Berth T1: Container Terminal    ❌ REJECTED (no grain handling)
  • Berth T2: Liquid Bulk Terminal  ❌ REJECTED (liquids only)
  • Berth T3: Dry Bulk Terminal     ✓ ELIGIBLE (has grain suckers)

AI Decision: Only Berth T3 can handle this vessel.
Constraint is HARD - no optimization possible.
```

#### Example 1.2.2: Dangerous Goods (IMDG) Segregation
```
SCENARIO: MV Chemical Express (Chemical Tanker)
─────────────────────────────────────────────────
Cargo: Methanol (IMDG Class 3 - Flammable Liquid)
Regulatory Requirement: 
  • Minimum 100m from passenger terminals
  • No concurrent berthing with Class 1 (Explosives)
  
Current Berth Status:
  • Berth D1: Passenger ferry at adjacent berth  ❌ REJECTED
  • Berth D2: Empty, 150m from nearest vessel    ✓ ELIGIBLE
  • Berth D3: Ammonium Nitrate vessel nearby     ❌ REJECTED (Class 1 conflict)

AI Decision: Berth D2 is the only safe option.
Segregation rules are HARD constraints with legal implications.
```

#### Example 1.2.3: Reefer Container Power Requirement
```
SCENARIO: MV Fresh Atlantic (Reefer Container Vessel)
─────────────────────────────────────────────────
Vessel Requirement: 400 reefer plugs (refrigerated containers)
Berth Power Availability:
  • Berth E1: 200 reefer plugs  ❌ REJECTED (insufficient)
  • Berth E2: 500 reefer plugs  ✓ ELIGIBLE
  • Berth E3: 450 reefer plugs  ✓ ELIGIBLE

AI Decision: Berths E2 and E3 are eligible.
If Berth E2 is occupied, E3 is assigned.
Reefer power is HARD constraint - cargo will spoil without power.
```

---

## 1.3 Vessel Readiness Constraints (HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| V-READY-001 | Pilot Availability | Certified pilot must be available | HARD |
| V-READY-002 | Tug Requirement Met | Required tugs available | HARD |
| V-READY-003 | Documentation Complete | Clearances obtained | HARD |
| V-READY-004 | Crew Compliance | ISPS, health clearances | HARD |

### Practical Examples

#### Example 1.3.1: No Pilot Available
```
SCENARIO: MV Eastern Star arriving at 0200 hours
─────────────────────────────────────────────────
Vessel LOA: 280 meters (requires Class A pilot)
Pilot Roster at 0200:
  • Pilot Kumar: Off duty (rest period)
  • Pilot Singh: On another vessel (MV Cosco Fortune)
  • Pilot Rao: Class B only (not certified for 280m)

AI Decision: 
  ❌ Cannot berth at 0200 - no qualified pilot available
  ✓ Earliest berthing: 0600 (Pilot Kumar back on duty)
  
Action: Vessel anchors at designated anchorage.
Waiting time: 4 hours (recorded for KPI tracking).
```

#### Example 1.3.2: Insufficient Tugs
```
SCENARIO: MV Cape Titan (VLCC Tanker)
─────────────────────────────────────────────────
Vessel GT: 180,000 GT
Port Requirement: 4 tugs (minimum 60T bollard pull each)
Tug Fleet Status at ETA:
  • Tug Neptune: 65T BP - Available     ✓
  • Tug Triton: 70T BP - Available      ✓
  • Tug Poseidon: 55T BP - Available    ❌ (below 60T)
  • Tug Oceanus: 68T BP - Under repair  ❌

AI Decision:
  Only 2 qualifying tugs available (need 4)
  ❌ Cannot berth until additional tugs available
  
Action: 
  • Alert tug operator to expedite Oceanus repair
  • Or request tug from neighboring port (3-hour transit)
  • Vessel waits at anchorage
```

---

# LAYER 2: BERTH / TERMINAL-LEVEL CONSTRAINTS

## 2.1 Berth Physical Constraints (HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| B-PHYS-001 | Berth Length | Total quay length available | HARD |
| B-PHYS-002 | Water Depth at Berth | Charted depth + tide | HARD |
| B-PHYS-003 | Fender Capacity | Vessel displacement limits | HARD |
| B-PHYS-004 | Mooring Bollard Capacity | SWL of bollards | HARD |
| B-PHYS-005 | Quay Load Bearing | Tons per square meter | HARD |

### Practical Examples

#### Example 2.1.1: Fender Rating Exceeded
```
SCENARIO: MV Mega Container (18,000 TEU vessel)
─────────────────────────────────────────────────
Vessel Displacement: 220,000 tons
Berth F1 Fender Rating: 180,000 tons maximum

AI Calculation:
  220,000 tons > 180,000 tons fender capacity
  
AI Decision: ❌ REJECTED
  Fender damage risk - structural constraint violated.
  
Alternative: Berth F3 with 250,000 ton fender rating ✓
```

#### Example 2.1.2: Bollard Capacity Check
```
SCENARIO: Storm Warning - High Winds Expected
─────────────────────────────────────────────────
Vessel: MV Nordic Giant (Panamax Bulk Carrier)
Expected Wind: 45 knots
Mooring Line Tension Calculated: 85 tons per bollard

Berth G2 Bollard SWL: 100 tons  ✓ SAFE
Berth G4 Bollard SWL: 60 tons   ❌ UNSAFE (85 > 60)

AI Decision: 
  If storm expected, only Berth G2 is safe.
  Berth G4 removed from options during weather alert.
```

---

## 2.2 Berth Specialization & Equipment (HARD/SOFT)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| B-SPEC-001 | Terminal Type | Container/Bulk/Liquid/RoRo | HARD |
| B-SPEC-002 | Crane Availability | STS cranes, mobile cranes | SOFT |
| B-SPEC-003 | Shore Crane Outreach | Vessel beam compatibility | HARD |
| B-SPEC-004 | Conveyor/Pipeline | Bulk/liquid transfer | HARD |
| B-SPEC-005 | Shore Ramp | RoRo operations | HARD |

### Practical Examples

#### Example 2.2.1: Crane Outreach Limitation
```
SCENARIO: MV MSC Gülsün (23,756 TEU - World's Largest)
─────────────────────────────────────────────────
Vessel Beam: 61.5 meters (24 containers wide)
Berth Crane Specifications:
  • Berth H1: STS Crane Outreach = 22 containers  ❌ REJECTED
  • Berth H2: STS Crane Outreach = 24 containers  ✓ ELIGIBLE
  • Berth H3: STS Crane Outreach = 25 containers  ✓ ELIGIBLE

AI Decision:
  Berth H1 cranes cannot reach outer containers.
  Only H2 and H3 can serve this mega-vessel.
```

#### Example 2.2.2: Bulk Berth Specialization
```
SCENARIO: Coal vs Grain Segregation
─────────────────────────────────────────────────
Incoming Vessels:
  • MV Coal Runner: 50,000 MT Coal
  • MV Wheat Harvest: 35,000 MT Food-Grade Wheat

Bulk Terminal Berths:
  • Berth J1: Coal-dedicated (contaminated)    → Coal Runner ✓
  • Berth J2: Clean grain berth                → Wheat Harvest ✓
  • Berth J3: General bulk                     → Either possible

AI Decision:
  ❌ Cannot assign Wheat Harvest to J1 (contamination risk)
  ✓ Coal Runner → J1, Wheat Harvest → J2
  
Constraint: HARD for food safety compliance.
```

---

## 2.3 Berth Availability & Maintenance (HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| B-AVAIL-001 | Current Occupancy | No double-booking | HARD |
| B-AVAIL-002 | Maintenance Window | Planned closures | HARD |
| B-AVAIL-003 | Buffer Time | Min time between vessels | SOFT |
| B-AVAIL-004 | Shift Handover | Operational gaps | SOFT |

### Practical Examples

#### Example 2.3.1: Berth Overlap Conflict
```
SCENARIO: Two Vessels Requesting Same Berth
─────────────────────────────────────────────────
Berth K1 Status:
  Current Vessel: MV Evergreen Unity
  ETD: 14:00 (2 hours cargo remaining)
  
Incoming Request:
  MV OOCL Pacific
  ETA: 13:00 (wants immediate berthing)

AI Analysis:
  Overlap Period: 13:00 - 14:00 (1 hour conflict)
  
AI Decision:
  ❌ Cannot double-book Berth K1
  
Options Generated:
  1. Delay MV OOCL Pacific ETA to 14:30 (buffer time)
  2. Assign MV OOCL Pacific to alternative Berth K2
  3. Expedite MV Evergreen Unity operations (crane priority)
  
AI Recommendation: Option 2 (Berth K2 available immediately)
```

#### Example 2.3.2: Maintenance Window Conflict
```
SCENARIO: Scheduled Crane Maintenance
─────────────────────────────────────────────────
Berth L1 Maintenance Schedule:
  Date: Monday 0600-1800 (12-hour crane overhaul)
  
Vessel Request:
  MV Atlantic Trader
  ETA: Monday 0800
  Cargo Ops Duration: 10 hours

AI Decision:
  ❌ Cannot use Berth L1 on Monday (maintenance)
  
Alternative Assignment:
  ✓ Berth L2 available Monday 0800
  Or delay to Tuesday 0600 at Berth L1
```

---

# LAYER 3: OPERATIONAL RESOURCE CONSTRAINTS

## 3.1 Pilotage Resources (HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| R-PILOT-001 | Pilot Certification Match | Vessel class vs pilot class | HARD |
| R-PILOT-002 | Pilot Availability | Duty roster check | HARD |
| R-PILOT-003 | Pilot Rest Hours | Fatigue regulations | HARD |
| R-PILOT-004 | Pilot Transit Time | From station to vessel | SOFT |

### Practical Examples

#### Example 3.1.1: Pilot Certification Mismatch
```
SCENARIO: LNG Carrier Arriving
─────────────────────────────────────────────────
Vessel: MV LNG Pioneer (Q-Max LNG Carrier)
Requirement: LNG-certified pilot (special training)

Pilot Roster:
  • Pilot Ahmed: Container/General - Not LNG certified  ❌
  • Pilot Chen: LNG Certified - On duty                 ✓
  • Pilot Rodriguez: LNG Certified - Off duty (rest)   ❌

AI Decision:
  Only Pilot Chen can handle this vessel.
  If Pilot Chen unavailable, vessel must wait.
  
LNG pilotage is HARD constraint - safety critical.
```

#### Example 3.1.2: Pilot Rest Hour Violation Prevention
```
SCENARIO: Back-to-Back Pilot Assignments
─────────────────────────────────────────────────
Pilot Kumar's Log:
  • 0200-0400: Piloted MV Eastern Star (inbound)
  • 0400-0600: Rest required (minimum 2 hours)
  
New Request:
  MV Pacific Venture ETA: 0430
  Requires immediate pilotage

AI Decision:
  ❌ Cannot assign Pilot Kumar (rest violation)
  ✓ Assign Pilot Singh (fresh duty shift)
  
Fatigue management is HARD - regulatory requirement.
```

---

## 3.2 Towage Resources (HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| R-TUG-001 | Tug Number Requirement | Based on vessel GT/LOA | HARD |
| R-TUG-002 | Bollard Pull Requirement | Total BP needed | HARD |
| R-TUG-003 | Tug Availability | Fleet status | HARD |
| R-TUG-004 | Tug Positioning Time | Transit to vessel | SOFT |

### Practical Examples

#### Example 3.2.1: Bollard Pull Calculation
```
SCENARIO: VLCC Tanker Berthing
─────────────────────────────────────────────────
Vessel: MV Crude Champion (VLCC, 300,000 DWT)
Port Tug Requirement Formula:
  GT > 200,000 = 4 tugs, minimum 250T total BP

Available Tug Fleet:
  • Tug Alpha: 70T BP    ✓
  • Tug Beta: 65T BP     ✓
  • Tug Gamma: 60T BP    ✓
  • Tug Delta: 55T BP    ✓
  Total: 250T BP         ✓ MEETS REQUIREMENT

AI Decision: All 4 tugs assigned to MV Crude Champion
Any tug breakdown = operation delayed (HARD constraint)
```

---

## 3.3 Terminal Labor & Equipment (SOFT/HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| R-LABOR-001 | Gang Availability | Stevedore shifts | SOFT |
| R-LABOR-002 | Crane Operator | Certified operators | HARD |
| R-LABOR-003 | Equipment Availability | RTG, reach stackers | SOFT |
| R-LABOR-004 | Shift Timing | Labor shift windows | SOFT |

### Practical Examples

#### Example 3.3.1: Labor Shift Optimization
```
SCENARIO: Night Shift Premium Avoidance
─────────────────────────────────────────────────
Vessel: MV Coastal Express
ETA Options: 2200 (tonight) or 0600 (tomorrow)
Cargo Volume: 500 TEU (estimated 8 hours)

Cost Analysis:
  • Night Shift (2200-0600): +40% labor premium
  • Day Shift (0600-1400): Standard rate

AI Recommendation (SOFT optimization):
  If vessel can delay to 0600, save $15,000 in labor costs.
  If demurrage > $15,000, berth at 2200.
  
  Demurrage Rate: $8,000/day = $2,667 for 8-hour delay
  Labor Savings: $15,000
  Net Benefit of Delay: $12,333 ✓
  
AI Decision: Recommend 0600 berthing (cost optimized)
```

---

# LAYER 4: TEMPORAL & ENVIRONMENTAL CONSTRAINTS

## 4.1 Tidal Constraints (HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| T-TIDE-001 | High-Draft Window | Tide-dependent transit | HARD |
| T-TIDE-002 | Tidal Gate | One-way channel timing | HARD |
| T-TIDE-003 | UKC at Berth | Depth at berth position | HARD |

### Practical Examples

#### Example 4.1.1: Tidal Window Calculation
```
SCENARIO: Deep-Draft Bulk Carrier
─────────────────────────────────────────────────
Vessel: MV Cape Ore (Capesize Bulk Carrier)
Arrival Draft: 17.5 meters

Channel Specifications:
  • Charted Depth: 16.0 meters
  • Required UKC: 1.5 meters
  • Minimum Depth Needed: 17.5 + 1.5 = 19.0 meters

Tide Forecast (Today):
  • Low Water: 0600 (+0.2m) → Total: 16.2m  ❌
  • High Water: 1200 (+3.5m) → Total: 19.5m ✓
  • Low Water: 1800 (+0.3m) → Total: 16.3m  ❌
  • High Water: 0000 (+3.2m) → Total: 19.2m ✓

AI Decision:
  Tidal Windows Available:
  • Window 1: 1030-1330 (around HW 1200) ✓
  • Window 2: 2200-0200 (around HW 0000) ✓
  
  Vessel must transit within these windows only.
  HARD constraint - grounding risk otherwise.
```

#### Example 4.1.2: One-Way Channel Traffic
```
SCENARIO: Narrow Channel with Tidal Gate
─────────────────────────────────────────────────
Channel: Approach Channel Alpha (one-way traffic)
Tidal Gate: Inbound 0800-1100, Outbound 1400-1700

Vessels Scheduled:
  • MV Inbound-1: ETA 0830 → Inbound window ✓
  • MV Inbound-2: ETA 1000 → Inbound window ✓
  • MV Outbound-1: ETD 0900 → ❌ CONFLICT (outbound during inbound window)

AI Decision:
  MV Outbound-1 must delay departure to 1400.
  Or expedite to depart by 0800 before inbound window.
  
Channel direction is HARD constraint (collision risk).
```

---

## 4.2 Weather Constraints (HARD/SOFT)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| T-WX-001 | Wind Speed Limit | Crane operations | HARD |
| T-WX-002 | Visibility Minimum | Pilotage safety | HARD |
| T-WX-003 | Wave Height Limit | Pilot boarding | HARD |
| T-WX-004 | Storm Alert | Port suspension | HARD |
| T-WX-005 | Rain Impact | Cargo sensitivity | SOFT |

### Practical Examples

#### Example 4.2.1: Wind Speed Crane Shutdown
```
SCENARIO: High Winds Approaching
─────────────────────────────────────────────────
Weather Forecast:
  • Current: 25 knots (operations normal)
  • 1400 hrs: 35 knots (caution)
  • 1600 hrs: 45 knots (crane shutdown)
  • 2000 hrs: 55 knots (port closure)

Vessel: MV Container King
  • Current berth time: 1200
  • Remaining work: 400 TEU (6 hours at normal speed)
  • Completion at normal pace: 1800 ❌ (after crane shutdown)

AI Decision:
  Deploy additional cranes to finish by 1530.
  Or suspend operations 1600-2200, resume after storm.
  
  Cost Analysis:
  • Extra crane cost: $5,000
  • Delay cost (demurrage + berth): $20,000
  
  AI Recommendation: Deploy extra crane ✓
```

#### Example 4.2.2: Fog - Visibility Below Minimum
```
SCENARIO: Dense Fog at Port Entrance
─────────────────────────────────────────────────
Visibility: 200 meters
Pilotage Requirement: Minimum 500 meters visibility

Vessels Waiting:
  • MV Atlantic Voyager: ETA 0600, waiting at anchorage
  • MV Pacific Trader: ETA 0630, waiting at anchorage
  • MV Indian Ocean: ETA 0700, waiting at anchorage

AI Decision:
  ❌ All pilotage suspended until visibility > 500m
  
  Forecast: Fog clearing by 0900
  New Schedule:
  • MV Atlantic Voyager: Berthing 0930
  • MV Pacific Trader: Berthing 1030
  • MV Indian Ocean: Berthing 1130
  
  Priority maintained, but all delayed uniformly.
```

---

## 4.3 Time-of-Day Restrictions (HARD/SOFT)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| T-TIME-001 | Daylight-Only Operations | For certain vessel types | HARD |
| T-TIME-002 | Night Navigation Ban | Channel restrictions | HARD |
| T-TIME-003 | Noise Restrictions | Urban port limits | SOFT |
| T-TIME-004 | Hazmat Daylight Rule | DG cargo handling | HARD |

### Practical Examples

#### Example 4.3.1: Daylight-Only for LNG Operations
```
SCENARIO: LNG Carrier Night Arrival
─────────────────────────────────────────────────
Vessel: MV LNG Freedom
ETA: 2100 hours (after sunset)
Port Rule: LNG vessels - daylight berthing only

AI Decision:
  ❌ Cannot berth at 2100 (night)
  ✓ Vessel anchors, berths at sunrise (0600)
  
  Waiting Time: 9 hours
  Reason: Safety regulation (HARD constraint)
```

---

# LAYER 5: POLICY, PRIORITY & COMMERCIAL CONSTRAINTS

## 5.1 Vessel Priority Rules (SOFT with Weights)

| Constraint ID | Constraint | Priority Weight | Type |
|---------------|------------|-----------------|------|
| P-PRIO-001 | Government/Navy Vessels | Weight: 100 (Absolute) | SOFT* |
| P-PRIO-002 | Emergency/Distress | Weight: 95 | SOFT* |
| P-PRIO-003 | Liner Services (Window Vessels) | Weight: 90 | SOFT |
| P-PRIO-004 | Perishable Cargo | Weight: 80 | SOFT |
| P-PRIO-005 | Transshipment Vessels | Weight: 75 | SOFT |
| P-PRIO-006 | Strategic Customers | Weight: 70 | SOFT |
| P-PRIO-007 | First-Come-First-Served | Weight: 50 (default) | SOFT |

*Note: Government and Emergency can override other constraints.

### Practical Examples

#### Example 5.1.1: Navy Vessel Priority Override
```
SCENARIO: Indian Navy Ship Arriving
─────────────────────────────────────────────────
Current Berth M1 Status:
  MV Commercial Trader (ETA: 1400)
  Already confirmed, pilot assigned

Incoming Request:
  INS Vikrant (Aircraft Carrier)
  ETA: 1400, requires Berth M1 specifically
  Priority: Government Vessel (Weight: 100)

AI Decision:
  ✓ INS Vikrant assigned Berth M1
  ✓ MV Commercial Trader reassigned to Berth M2
  ✓ No demurrage charged to Commercial Trader (port directive)
  
Government vessel priority is effectively HARD in practice.
```

#### Example 5.1.2: Perishable Cargo Priority
```
SCENARIO: Banana Carrier vs General Cargo
─────────────────────────────────────────────────
Both vessels arrive simultaneously at 0800:
  • MV Fruit Express: 5,000 MT Bananas (perishable)
  • MV General Star: 5,000 MT Steel Coils (non-perishable)

Single Berth Available: Berth N1

Priority Weights:
  • Perishable Cargo: 80
  • General Cargo (FCFS): 50

AI Decision:
  ✓ MV Fruit Express → Berth N1 (higher priority)
  ✓ MV General Star → Anchorage (wait for next berth)
  
Rationale: Bananas have 48-hour shelf life at port temperature.
Steel can wait indefinitely without quality loss.
```

---

## 5.2 Window Vessel Contracts (NEW - CRITICAL FEATURE)

This is a **key SmartBerth differentiator** - handling scheduled liner services with contracted berth windows.

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| P-WINDOW-001 | Window Vessel ETA | Contracted arrival time | SOFT (high weight) |
| P-WINDOW-002 | Berth Vacation Priority | Current vessel must vacate | HARD |
| P-WINDOW-003 | Limited Berth Time Contract | Max time for non-window | HARD |
| P-WINDOW-004 | Berth Premium Payment | Commercial incentive | SOFT |
| P-WINDOW-005 | Penalty for Window Miss | SLA breach cost | SOFT |

### Practical Examples

#### Example 5.2.1: Window Vessel Approaching - Berth Vacation Required
```
SCENARIO: Maersk Liner with Contracted Window
─────────────────────────────────────────────────
WINDOW VESSEL:
  • MV Maersk Eindhoven (Weekly liner service)
  • Contracted Window: Wednesday 0800-2000
  • Berth: P1 (dedicated by contract)

CURRENT SITUATION (Tuesday 1800):
  • Berth P1 occupied by MV Coastal Runner
  • MV Coastal Runner ETD: Originally Thursday 0600
  • Remaining Cargo: 800 TEU (16 hours work)

CONFLICT:
  Window vessel arrives in 14 hours
  Current vessel needs 16 hours
  Gap: -2 hours

AI DECISION PROCESS:

Step 1: Calculate Options
┌─────────────────────────────────────────────────────────────┐
│ Option A: Expedite MV Coastal Runner                        │
│   • Add 2 extra cranes                                      │
│   • Complete in 10 hours (by Wednesday 0400)                │
│   • Cost: $8,000 (crane premium)                            │
├─────────────────────────────────────────────────────────────┤
│ Option B: Shift MV Coastal Runner to Berth P2               │
│   • Unberthing time: 2 hours                                │
│   • Re-berthing at P2: 1 hour                               │
│   • Continue operations at P2                               │
│   • Cost: $12,000 (extra pilot + tugs + delay)              │
├─────────────────────────────────────────────────────────────┤
│ Option C: Limited Time Contract                             │
│   • MV Coastal Runner agreed to LIMITED BERTH TIME          │
│   • Must vacate by Wednesday 0600                           │
│   • Remaining cargo: Discharged at next port                │
│   • Payment: Port compensates $5,000 for short-berthing     │
├─────────────────────────────────────────────────────────────┤
│ Option D: Window Vessel Delay (LAST RESORT)                 │
│   • Delay MV Maersk Eindhoven to Thursday                   │
│   • SLA Penalty: $50,000                                    │
│   • Reputation damage: Severe                               │
└─────────────────────────────────────────────────────────────┘

AI RECOMMENDATION:
  ✓ Option A (Expedite) - Lowest cost, no SLA breach
  
NOTIFICATION GENERATED:
  → Terminal Ops: Deploy cranes 3 & 4 to Berth P1
  → MV Coastal Runner Agent: Operations expedited
  → MV Maersk Eindhoven Agent: Window confirmed
```

#### Example 5.2.2: Limited Time Contract Execution
```
SCENARIO: Tramp Vessel Accepts Limited Berth Time
─────────────────────────────────────────────────
SETUP:
  • MV Bulk Trader (Tramp vessel, no fixed schedule)
  • Requests berth for 48-hour cargo operation
  • Only berth available: Berth Q1

CONSTRAINT:
  • Berth Q1 has window vessel arriving in 36 hours
  • MV CMA CGM Marco Polo (Window Vessel)
  • Contracted window: Cannot be missed

LIMITED TIME CONTRACT OFFERED:

┌─────────────────────────────────────────────────────────────┐
│           LIMITED BERTH TIME AGREEMENT                      │
├─────────────────────────────────────────────────────────────┤
│ Vessel: MV Bulk Trader                                      │
│ Berth: Q1                                                   │
│ Berthing Time: 1200 Tuesday                                 │
│ MAXIMUM BERTH TIME: 34 hours (must vacate by 2200 Wed)     │
│                                                             │
│ Terms:                                                      │
│ • Vessel agrees to vacate 2 hours before window vessel     │
│ • If cargo incomplete, vessel shifts to anchorage          │
│ • Remaining cargo handled at Berth Q3 (when available)     │
│                                                             │
│ Compensation:                                               │
│ • 15% discount on port dues for accepting limited time     │
│ • Priority for next available berth for remaining cargo    │
│                                                             │
│ Penalty for Non-Compliance:                                 │
│ • $25,000 per hour if berth not vacated on time           │
└─────────────────────────────────────────────────────────────┘

AI EXECUTION:
  • Contract generated and sent to agent
  • Agent accepts via PCS portal
  • Countdown timer activated in system
  • Alerts at T-6 hours, T-2 hours, T-30 minutes
```

#### Example 5.2.3: Window Vessel Payment Settlement
```
SCENARIO: Commercial Settlement for Berth Displacement
─────────────────────────────────────────────────
SITUATION:
  MV Independent Spirit (tramp) at Berth R1
  MV Hapag Express (window) arriving in 6 hours
  MV Independent Spirit needs 8 more hours

NEGOTIATION VIA SMARTBERTH:

Option 1: MV Independent Spirit Leaves Early
  • Remaining cargo: 1,200 TEU
  • To be completed at: Next port (Singapore)
  • Additional freight: $15,000
  • Port compensation to vessel: $10,000
  • Net cost to port: $10,000

Option 2: MV Hapag Express Waits 2 Hours
  • SLA penalty: $20,000
  • Network delay impact: 4 connecting feeders affected
  • Total estimated cost: $45,000

AI RECOMMENDATION: Option 1
  → Commercial settlement initiated
  → Payment order generated: Port pays $10,000 to MV Independent Spirit
  → Berth R1 vacated at required time
  → Window vessel SLA maintained

AUDIT TRAIL:
  All decisions logged with:
  • Timestamp
  • Decision rationale
  • Cost comparison
  • Approving authority
  • Contract reference
```

---

## 5.3 Contractual Berth Agreements (HARD/SOFT)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| P-CONTRACT-001 | Dedicated Berth | Exclusive use agreement | HARD |
| P-CONTRACT-002 | Preferred Berth | Priority but not exclusive | SOFT |
| P-CONTRACT-003 | Volume Commitment | Minimum annual TEU/MT | SOFT |
| P-CONTRACT-004 | Terminal Handling Agreement | THA terms | SOFT |

### Practical Examples

#### Example 5.3.1: Dedicated Berth Violation Attempt
```
SCENARIO: MSC Dedicated Berth
─────────────────────────────────────────────────
Contract: Berth S1 dedicated to MSC vessels
Duration: 2024-2028
Terms: Berth S1 exclusively for MSC, 24/7

Incoming Request:
  MV Cosco Shipping Star (Cosco vessel)
  Requests Berth S1 (only berth with deep draft)
  
AI Decision:
  ❌ REJECTED - Berth S1 is MSC-dedicated
  
Alternative Offered:
  ✓ Berth S2 (if vessel draft compatible)
  ✓ Wait for Berth S3 (deeper draft, available in 6 hours)
  
Dedicated berth contracts are HARD constraints.
```

---

## 5.4 Commercial Penalty Optimization (SOFT)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| P-COMM-001 | Demurrage Minimization | Waiting cost optimization | SOFT |
| P-COMM-002 | SLA Compliance | TAT commitments | SOFT |
| P-COMM-003 | Berth Productivity Target | Moves per hour | SOFT |
| P-COMM-004 | Revenue Maximization | Port income optimization | SOFT |

### Practical Examples

#### Example 5.4.1: Demurrage vs Berth Premium Trade-off
```
SCENARIO: Vessel Willing to Pay Premium for Earlier Berth
─────────────────────────────────────────────────
MV Urgent Cargo:
  • Current queue position: 3rd in line
  • Estimated wait: 18 hours
  • Demurrage rate: $15,000/day
  • Demurrage exposure: $11,250 (18 hours)

Premium Berth Option:
  • Berth T1 available in 2 hours (for premium)
  • Premium charge: $8,000
  • Demurrage saved: $10,000 (16 hours)

AI Calculation:
  Net benefit to vessel: $10,000 - $8,000 = $2,000 savings
  Revenue to port: $8,000 (premium)
  
AI Recommendation:
  Offer premium berthing to MV Urgent Cargo
  Vessel agent can accept/decline via portal
```

---

# LAYER 6: UKC & NAVIGATION SAFETY CONSTRAINTS

## 6.1 Under Keel Clearance (HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| N-UKC-001 | Static UKC | Min clearance at rest | HARD |
| N-UKC-002 | Dynamic UKC (Squat) | Speed-dependent sinkage | HARD |
| N-UKC-003 | Heel Allowance | Turning allowance | HARD |
| N-UKC-004 | Wave Response | Swell allowance | HARD |

### Practical Examples

#### Example 6.1.1: Complete UKC Calculation
```
SCENARIO: Capesize Bulk Carrier Transit
─────────────────────────────────────────────────
Vessel: MV Iron Duke
Static Draft: 17.8 meters

Channel Specifications:
  • Charted Depth: 18.5 meters
  • Tide at Transit Time: +2.0 meters
  • Available Depth: 20.5 meters

UKC Calculation:
┌─────────────────────────────────────────────────────────────┐
│ Component               │ Value    │ Calculation           │
├─────────────────────────────────────────────────────────────┤
│ Static Draft            │ 17.80 m  │ Given                 │
│ Squat (at 8 knots)      │ +0.45 m  │ 0.02 × V² × Cb        │
│ Heel (15° turn)         │ +0.30 m  │ Beam/2 × sin(15°)     │
│ Wave Response           │ +0.25 m  │ Sea state 3           │
├─────────────────────────────────────────────────────────────┤
│ TOTAL DYNAMIC DRAFT     │ 18.80 m  │                       │
│ Available Depth         │ 20.50 m  │ Chart + Tide          │
│ CALCULATED UKC          │ 1.70 m   │ 20.50 - 18.80         │
│ REQUIRED UKC            │ 1.50 m   │ Port policy           │
├─────────────────────────────────────────────────────────────┤
│ STATUS                  │ ✓ SAFE   │ 1.70 > 1.50           │
└─────────────────────────────────────────────────────────────┘

AI Decision: Transit APPROVED for current tidal window.
```

---

## 6.2 Channel Navigation (HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| N-CHAN-001 | Channel Width | Vessel beam clearance | HARD |
| N-CHAN-002 | Bend Radius | Turning limitations | HARD |
| N-CHAN-003 | Traffic Separation | One-way rules | HARD |
| N-CHAN-004 | Speed Limits | Channel-specific | HARD |

---

## 6.3 Anchorage Management (SOFT/HARD)

| Constraint ID | Constraint | Description | Type |
|---------------|------------|-------------|------|
| N-ANCH-001 | Anchorage Capacity | Number of vessels | HARD |
| N-ANCH-002 | Anchorage Depth | Vessel draft compatibility | HARD |
| N-ANCH-003 | Swing Circle | Vessel LOA clearance | HARD |
| N-ANCH-004 | Anchorage Assignment | Waiting queue management | SOFT |

### Practical Examples

#### Example 6.3.1: Anchorage Congestion Management
```
SCENARIO: Multiple Vessels Waiting, Limited Anchorage
─────────────────────────────────────────────────
Anchorage Capacity:
  • Deep Water Anchorage (>15m): 8 vessels max
  • Shallow Anchorage (<15m): 12 vessels max
  • Current Occupancy: 7 deep, 11 shallow

Incoming Vessels:
  • MV Deep Drafter (Draft: 16m) → Needs deep anchorage
  • MV Coastal Small (Draft: 8m) → Can use shallow

Deep Anchorage Status:
  7 occupied + 1 incoming = 8 (at capacity)
  
AI Decision:
  ✓ MV Deep Drafter → Deep Anchorage Position A8
  ✓ MV Coastal Small → Shallow Anchorage Position B12
  
  Alert: Deep anchorage now at capacity.
  Next deep-draft arrival must either:
  • Wait at sea (drifting)
  • Proceed to alternate port
  • Accept shallow anchorage (if draft permits - check tide)
```

---

# SUMMARY: CONSTRAINT PRIORITY MATRIX

## Quick Reference: Which Constraints Can Be Violated?

| Layer | Constraint Type | Can Override? | Override Condition |
|-------|-----------------|---------------|-------------------|
| 1 | Vessel Physical Dimensions | ❌ NEVER | Impossible - laws of physics |
| 1 | Cargo Compatibility | ❌ NEVER | Safety critical |
| 2 | Berth Physical Limits | ❌ NEVER | Infrastructure fixed |
| 2 | Berth Specialization | ❌ NEVER | Equipment mismatch |
| 3 | Pilot/Tug Availability | ⚠️ RARELY | Emergency only |
| 4 | Tidal Windows | ❌ NEVER | Grounding risk |
| 4 | Weather (Critical) | ❌ NEVER | Safety critical |
| 4 | Weather (Moderate) | ✓ SOFT | With risk acceptance |
| 5 | Priority Rules | ✓ SOFT | Commercial negotiation |
| 5 | Window Vessels | ⚠️ HIGH COST | Heavy penalty |
| 5 | Commercial Terms | ✓ SOFT | Payment can override |
| 6 | UKC Requirements | ❌ NEVER | Grounding risk |

---

## AI Decision Flowchart

```
INCOMING BERTH REQUEST
         │
         ▼
┌─────────────────────────────────────────┐
│ LAYER 1: PHYSICAL FEASIBILITY CHECK     │
│ (LOA, Beam, Draft, Cargo Type)          │
│                                         │
│ Pass? ──No──► REJECT (No alternatives)  │
│   │                                     │
│  Yes                                    │
│   ▼                                     │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ LAYER 2: BERTH COMPATIBILITY CHECK      │
│ (Specialization, Equipment, Depth)      │
│                                         │
│ Pass? ──No──► Filter to compatible only │
│   │                                     │
│  Yes                                    │
│   ▼                                     │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ LAYER 3: RESOURCE AVAILABILITY CHECK    │
│ (Pilots, Tugs, Labor)                   │
│                                         │
│ Pass? ──No──► Delay until available     │
│   │                                     │
│  Yes                                    │
│   ▼                                     │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ LAYER 4: TEMPORAL WINDOW CHECK          │
│ (Tide, Weather, Time-of-Day)            │
│                                         │
│ Pass? ──No──► Schedule for valid window │
│   │                                     │
│  Yes                                    │
│   ▼                                     │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ LAYER 5: PRIORITY & COMMERCIAL CHECK    │
│ (Window Vessels, Contracts, Priority)   │
│                                         │
│ Conflict? ──Yes──► Optimize/Negotiate   │
│   │                                     │
│  No                                     │
│   ▼                                     │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ LAYER 6: NAVIGATION SAFETY CHECK        │
│ (UKC, Channel, Anchorage)               │
│                                         │
│ Pass? ──No──► Adjust timing/route       │
│   │                                     │
│  Yes                                    │
│   ▼                                     │
└─────────────────────────────────────────┘
         │
         ▼
    ┌─────────┐
    │ ALLOCATE│
    │  BERTH  │
    └─────────┘
```

---

*Document Version: 1.0*
*Created for: SmartBerth AI Module*
*Date: February 2026*
