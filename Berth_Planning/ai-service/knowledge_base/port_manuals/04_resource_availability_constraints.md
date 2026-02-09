# Port Operations Manual: Resource Availability Constraints

**Document Type**: Port Operations Manual - Hard + Soft Constraints
**Category**: Layer 3 - Operational Resource Constraints
**Classification**: HARD (pilot/tug), SOFT (labor optimization)
**Applies To**: Pilotage, towage, terminal labor operations

---

## Overview

Resource availability constraints ensure adequate pilotage, towage, and terminal labor resources are available for safe and efficient vessel operations. Pilot and tug requirements are HARD constraints (safety-critical), while labor optimization is typically SOFT.

## Pilotage Resources

### 1. Pilot Certification Requirements - Constraint ID: R-PILOT-001

**Rule**: `pilot.certification_class ≥ vessel.required_pilot_class`

**Description**: Pilots must hold certifications matching vessel size and type. This is a HARD safety constraint enforced by maritime regulations.

**Pilot Classification System**:

| Pilot Class | Vessel Size Range | Special Certifications |
|-------------|-------------------|----------------------|
| **Class A** | Up to 150m LOA, <20,000 GT | General cargo, containers |
| **Class B** | 150-250m LOA, 20,000-80,000 GT | Container, bulk carriers |
| **Class C** | 250-350m LOA, 80,000-150,000 GT | Large containers, VLCC |
| **Class S** | >350m LOA, >150,000 GT | ULCV, mega-tankers |
| **LNG-Certified** | Any LNG/LPG carrier | Gas handling training |
| **Tanker-Certified** | Chemical/oil tankers | Hazmat procedures |

**Example Scenario: LNG Carrier Arrival**
- **Vessel**: MV LNG Pioneer (Q-Max LNG Carrier, 345m LOA)
- **Requirement**: LNG-certified pilot + Class C general certification

**Pilot Roster Check**:
- **Pilot Ahmed**: Class B, Container certified ❌ **DISQUALIFIED** (no LNG cert)
- **Pilot Chen**: Class C, LNG-certified ✓ **QUALIFIED**
- **Pilot Rodriguez**: Class A, LNG-certified ❌ **DISQUALIFIED** (insufficient class)

**Decision**: Only Pilot Chen can handle this vessel. If unavailable, vessel must wait at anchorage.

**Safety Rationale**: LNG carriers have specialized gas handling systems, ballasting procedures, and emergency protocols. Uncertified pilots create catastrophic risk (explosion, environmental disaster).

---

### 2. Pilot Availability & Rest Hours - Constraint ID: R-PILOT-002, R-PILOT-003

**Rule**: `pilot.status = 'AVAILABLE' AND pilot.rest_hours_since_last_job ≥ minimum_rest`

**Description**: Pilots must be available and adequately rested per fatigue management regulations.

**Mandatory Rest Periods** (International standards):
- **Between jobs**: Minimum 6 hours rest after 8-hour shift
- **Daily maximum**: 12 hours duty in any 24-hour period
- **Weekly maximum**: 72 hours duty in any 7-day period
- **After night shift (0000-0600)**: Minimum 8 hours rest before next assignment

**Example: Pilot Fatigue Prevention**
- **Pilot Kumar's Log**:
  - 0200-0400: Piloted MV Eastern Star (inbound) - 2 hours duty
  - 0400-1000: Mandatory rest period (6 hours minimum)

- **New Request**: MV Pacific Venture ETA 0430
  - Requires immediate pilotage

**Decision Logic**:
- **Pilot Kumar**: ❌ **UNAVAILABLE** (only 30 min rest, needs 6 hours)
- **Pilot Singh**: ✓ **AVAILABLE** (fresh duty shift, well-rested)

**Consequence of Violation**:
- Regulatory penalties: $10,000-50,000 per violation
- Safety risk: Fatigue-related accidents (collision, grounding)
- Pilot license suspension: 30-90 days

**Hard Constraint Justification**: Maritime law prohibits fatigued pilotage operations. No commercial pressure can override this.

---

### 3. Pilot Positioning Time - Constraint ID: R-PILOT-004

**Rule**: `pilot_travel_time + boarding_time ≤ (vessel_ETA - pilot_dispatch_time)`

**Type**: **SOFT** constraint (affects scheduling efficiency)

**Description**: Pilots must physically reach pilot boarding grounds (PBG) before vessel arrival.

**Timing Calculation**:
```
Total Pilot Response Time =
  Alert Time (15 min)
  + Travel to pilot station (20-60 min depending on location)
  + Pilot boat launch prep (10 min)
  + Transit to PBG (15-45 min)
  + Boarding operation (10-20 min)

Typical Range: 70-150 minutes advance notice required
```

**Example**:
- **Vessel**: MV Container King ETA at Pilot Boarding Ground: 0600
- **Pilot Kumar**: Currently at home, 45 min from pilot station
- **Dispatch Calculation**:
  - Alert: 0400 (15 min prep)
  - Drive to station: 0415-0500 (45 min)
  - Pilot boat launch: 0500-0510 (10 min)
  - Transit to PBG: 0510-0545 (35 min)
  - Boarding: 0545-0555 (10 min)
  - **Ready for pilotage**: 0555 ✓ **5 minutes buffer**

**Optimization**: AI system dispatches pilots with sufficient lead time to avoid vessel delays.

---

## Towage Resources

### 4. Tug Number Requirements - Constraint ID: R-TUG-001

**Rule**: Based on vessel size and port-specific regulations

**Standard Tug Requirements**:

| Vessel Gross Tonnage | Minimum Tugs | Conditions |
|---------------------|--------------|-----------|
| <10,000 GT | 0-1 tugs | Optional for small vessels, depends on maneuverability |
| 10,000-50,000 GT | 2 tugs | Standard for most cargo vessels |
| 50,000-150,000 GT | 3 tugs | Large bulk carriers, Panamax containers |
| 150,000-250,000 GT | 4 tugs | Post-Panamax containers, Suezmax tankers |
| >250,000 GT | 5+ tugs | ULCV containers, VLCC tankers |

**Special Conditions Requiring Additional Tugs**:
- **High winds (>25 knots)**: +1 tug
- **Strong currents (>2 knots)**: +1 tug
- **Narrow channel**: +1 tug
- **Vessel with limited maneuverability** (engine issues): +1 tug

**Example Calculation**:
- **Vessel**: MV Cape Titan (VLCC Tanker, 320,000 GT)
- **Base requirement**: 5 tugs (per GT category)
- **Weather conditions**: 30-knot winds
- **Final requirement**: 6 tugs (5 base + 1 weather)

---

### 5. Bollard Pull Requirements - Constraint ID: R-TUG-002

**Rule**: `SUM(tug_bollard_pulls) ≥ required_total_BP`

**Description**: Tugs are rated by Bollard Pull (BP) - the maximum pulling force measured in metric tons.

**Bollard Pull Calculation Formula**:
```
Required BP = (Vessel GT / 1000) × Wind Factor × Current Factor

Where:
- Wind Factor: 1.0 (calm), 1.3 (25-35 knots), 1.5 (>35 knots)
- Current Factor: 1.0 (<1 knot), 1.2 (1-2 knots), 1.4 (>2 knots)

Example:
Vessel: 200,000 GT
Wind: 30 knots (Factor 1.3)
Current: 0.5 knots (Factor 1.0)
Required BP = (200,000/1000) × 1.3 × 1.0 = 260 tons BP
```

**Tug Fleet Assignment Example**:
- **Required Total BP**: 260 tons
- **Available Tugs**:
  - Tug Alpha: 70T BP ✓
  - Tug Beta: 65T BP ✓
  - Tug Gamma: 60T BP ✓
  - Tug Delta: 55T BP ✓
  - **Total**: 250T BP ❌ **INSUFFICIENT** (10T short)

**Options**:
1. Wait for higher-capacity tug (Tug Epsilon: 75T BP) to become available
2. Request tug from neighboring port (3-hour transit)
3. Delay vessel until weather improves (reduce wind factor)

**Decision**: Hard constraint - cannot proceed with insufficient tug capacity. Risk of loss of control, collision, or grounding.

---

## Terminal Labor & Equipment

### 6. Stevedore Gang Availability - Constraint ID: R-LABOR-001

**Rule**: `required_gangs ≤ available_gangs`

**Type**: **SOFT** constraint (scheduling optimization)

**Description**: Stevedore gangs are teams of workers for cargo handling. Each gang typically consists of:
- 1 foreman
- 2 crane operators (for twin-crane operations)
- 8-12 lashing/unlashing crew
- 4-6 tally clerks/checkers

**Gang Productivity**:
- Container operations: 25-35 moves per hour per gang
- Break bulk: 50-100 tons per hour per gang
- Bulk cargo: 200-500 tons per hour per gang

**Labor Shift Structure**:
- **Day shift**: 0600-1400 (8 hours) - Standard rate
- **Evening shift**: 1400-2200 (8 hours) - Standard rate
- **Night shift**: 2200-0600 (8 hours) - 40% premium rate
- **Overtime**: Beyond 8 hours - 50-100% premium rate

**Example: Shift Optimization**
- **Vessel**: MV Coastal Express
- **Cargo**: 500 TEU (8 hours work for 1 gang)
- **ETA Options**:
  - Option A: 2200 (night shift start) - $60,000 labor cost (40% premium)
  - Option B: 0600 (day shift start) - $42,000 labor cost (standard)

**Cost-Benefit Analysis**:
- **Night arrival (Option A)**:
  - Labor cost: $60,000
  - Vessel finishes: 0600 next day
  - Demurrage saved: $0 (no waiting)

- **Delay to day shift (Option B)**:
  - Labor cost: $42,000
  - Vessel waits 8 hours
  - Demurrage cost: 8 hours @ $300/hour = $2,400
  - **Net savings**: $60,000 - $42,000 - $2,400 = **$15,600**

**AI Recommendation**: Delay to day shift if demurrage rate is low. This is a SOFT optimization that balances labor cost vs. vessel waiting cost.

---

### 7. Crane Operator Certification - Constraint ID: R-LABOR-002

**Rule**: `operator.crane_certification = TRUE`

**Type**: **HARD** constraint

**Description**: Crane operators must be certified for the specific crane type (STS gantry, mobile harbor crane, reach stacker).

**Certification Levels**:
- **Basic STS**: Panamax-size gantry cranes (up to 50-ton lift)
- **Super-Post-Panamax**: Ultra-large gantry cranes (65-ton lift, 24-row outreach)
- **Mobile harbor crane**: Liebherr LHM cranes (104-208 ton capacity)
- **Heavy-lift specialist**: Project cargo cranes (400+ ton capacity)

**Shortage Scenario**:
- **Vessel**: ULCV requiring 4 Super-Post-Panamax crane operators
- **Available Operators**:
  - 6 Basic STS certified ❌ **CANNOT** operate Super-Post-Panamax cranes
  - 3 Super-Post-Panamax certified ✓ Only 3 available (need 4)

**Decision**:
- Deploy only 3 cranes (instead of 4)
- Extends vessel turnaround time by 33%
- Or delay vessel until 4th certified operator available (shift change, typically 6-8 hours)

---

## Integration with AI Resource Scheduler

### Query Example:
**Question**: "Can MV LNG Pioneer berth immediately at 0200 hours?"

**Expected RAG Response**:
"No. Based on pilot certification requirements (R-PILOT-001), MV LNG Pioneer is an LNG carrier requiring an LNG-certified pilot. Current pilot roster check at 0200 shows:
- Pilot Kumar: Off duty, rest period
- Pilot Singh: Currently piloting another vessel
- Pilot Rao: Not LNG-certified

The only LNG-certified pilot (Pilot Chen) is available at 0600 (4-hour wait). Additionally, R-PILOT-003 (rest hour requirements) mandates adequate rest between shifts. Recommendation: Vessel anchors at designated anchorage, berths at 0600 when qualified pilot available. This is a HARD safety constraint that cannot be overridden."

---

## Related Documents

- Layer 1: Vessel Readiness Requirements
- Layer 4: Weather Constraints (affect tug requirements)
- Safety Manual: Pilot Boarding Procedures, Tug Operations

---

**Keywords**: pilotage, towage, pilot certification, tug bollard pull, stevedore gangs, crane operators, labor shifts, resource availability, fatigue management, tug requirements
