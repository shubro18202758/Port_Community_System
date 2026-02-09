# Port Operations Manual: Tidal & Weather Constraints

**Document Type**: Port Operations Manual - Hard Constraints
**Category**: Layer 4 - Temporal & Environmental Constraints
**Classification**: HARD (safety-critical), SOFT (operational efficiency)
**Applies To**: Vessel transit timing, berth operations, cargo handling

---

## Overview

Tidal and weather constraints are time-dependent factors that affect vessel navigation safety and operational efficiency. Tidal windows are HARD constraints (grounding risk), while some weather conditions allow SOFT optimization (operational delays vs. safety).

## Tidal Constraints

### 1. Tidal Window Calculations - Constraint ID: T-TIDE-001

**Rule**: `available_depth = charted_depth + tidal_height ≥ vessel_draft + required_UKC`

**Description**: Deep-draft vessels can only transit channels and berth during high tide windows when water depth is sufficient.

**Required Under Keel Clearance (UKC)**:
- **Standard vessels**: 1.5 meters minimum
- **Large vessels (>100,000 GT)**: 2.0 meters minimum
- **VLCC/ULCV**: 2.5-3.0 meters minimum
- **Dynamic UKC** (moving vessel): +0.5-1.0 meters additional

**Tidal Window Calculation Example**:

**Vessel**: MV Cape Ore (Capesize Bulk Carrier)
- Arrival Draft: 17.5 meters
- Required UKC: 1.5 meters
- **Minimum Depth Needed**: 17.5 + 1.5 = **19.0 meters**

**Channel Specifications**:
- Charted Depth: 16.0 meters

**Today's Tide Forecast**:
```
Time    | Tide Height | Total Depth | Status
--------|-------------|-------------|--------
0600 LW | +0.2m      | 16.2m       | ❌ UNSAFE (16.2 < 19.0)
1200 HW | +3.5m      | 19.5m       | ✓ SAFE (19.5 > 19.0)
1800 LW | +0.3m      | 16.3m       | ❌ UNSAFE
0000 HW | +3.2m      | 19.2m       | ✓ SAFE
```

**Tidal Windows Available**:
- **Window 1**: 1030-1330 (3 hours centered on HW 1200)
- **Window 2**: 2200-0200 (4 hours centered on HW 0000)

**AI Decision**: Vessel must schedule transit/berthing within these windows only. **This is a HARD constraint** - attempting transit outside window risks grounding.

**Consequences of Grounding**:
- Vessel damage: $5-50 million repairs
- Cargo loss: $10-100 million
- Environmental damage: $50-500 million (for oil spills)
- Channel blockage: Port closure, $5-10 million daily economic impact

---

### 2. One-Way Channel Tidal Gates - Constraint ID: T-TIDE-002

**Rule**: `channel.traffic_direction = 'INBOUND' OR 'OUTBOUND'` (time-dependent)

**Description**: Narrow channels operate one-way traffic during specific tidal windows to prevent head-on collisions.

**Example: Channel Alpha (Narrow Approach)**

**Tidal Gate Schedule**:
```
Time Window    | Direction | Max Vessels
--------------|-----------|------------
0800-1100     | INBOUND   | 5 vessels max
1100-1400     | CLOSED    | Tide too low
1400-1700     | OUTBOUND  | 4 vessels max
1700-2000     | CLOSED    | Tide too low
2000-2300     | INBOUND   | 3 vessels (night)
```

**Conflict Example**:
- **MV Inbound-1**: ETA 0830 → Inbound window ✓ **ELIGIBLE**
- **MV Inbound-2**: ETA 1000 → Inbound window ✓ **ELIGIBLE**
- **MV Outbound-1**: Planned ETD 0900 → ❌ **REJECTED** (outbound during inbound window)

**Decision**: MV Outbound-1 must either:
1. Depart before 0800 (before inbound window opens)
2. Wait until 1400 (next outbound window)

**Rationale**: Channel too narrow for passing traffic. This is a HARD safety constraint enforced by Vessel Traffic Service (VTS).

---

### 3. Tidal Current Effects - Constraint ID: T-TIDE-003

**Description**: Strong tidal currents (>2 knots) affect vessel maneuverability and tug requirements.

**Current Impact on Operations**:
```
Current Speed | Effect on Berthing | Additional Resources
--------------|-------------------|--------------------
<1 knot       | Minimal          | Standard tugs
1-2 knots     | Moderate         | +1 tug recommended
2-3 knots     | Significant      | +2 tugs required
>3 knots      | Severe           | Operations suspended
```

**Example**:
- **Vessel**: Large container ship (80,000 GT)
- **Standard tug requirement**: 3 tugs
- **Current at berth**: 2.5 knots (spring tide)
- **Adjusted requirement**: 3 + 2 = **5 tugs**

**Optimization**: AI scheduler avoids berthing during peak tidal current (typically mid-tide) if possible, scheduling for slack water periods (±1 hour from high/low tide).

---

## Weather Constraints

### 4. Wind Speed Limits - Constraint ID: T-WX-001

**Rule**: `wind_speed < crane_operational_limit`

**Type**: **HARD** constraint for crane operations

**Crane Wind Speed Limits**:

| Crane Type | Warning Threshold | Shutdown Threshold |
|-----------|------------------|-------------------|
| **Ship-to-Shore Gantry** | 25 knots | 35-40 knots |
| **Mobile Harbor Crane** | 20 knots | 30 knots |
| **Heavy-Lift Crane** | 15 knots | 25 knots |
| **Reach Stacker** | 30 knots | 45 knots |

**Wind Speed Impact**:
- **<20 knots**: Normal operations
- **20-25 knots**: Caution - reduced speeds
- **25-35 knots**: Warning - lashing/securing priority
- **35-45 knots**: Crane shutdown - no lifts
- **>45 knots**: Port suspension - vessels secure or depart

**Example Scenario: Approaching Storm**

**Weather Forecast**:
```
Time  | Wind Speed | Operational Status
------|-----------|-------------------
1200  | 25 knots  | Operations normal
1400  | 35 knots  | Caution - slow down
1600  | 45 knots  | Crane shutdown
2000  | 55 knots  | Port closure
```

**Vessel**: MV Container King
- Currently berthed at 1200
- Remaining cargo: 400 TEU (6 hours at normal speed)
- Completion at normal pace: 1800

**Problem**: Cranes shutdown at 1600 (2 hours before completion)

**AI Decision Options**:
1. **Deploy extra cranes** - Finish by 1530 before shutdown
   - Cost: $5,000 (crane premium)
   - Benefit: Vessel departs safely

2. **Suspend operations 1600-2200** - Resume after storm
   - Cost: $20,000 (demurrage + berth occupancy)
   - Risk: Vessel remains in port during storm

3. **Partial discharge** - Complete 70% by 1530, finish at next port
   - Cost: $25,000 (extra port call + cargo handling)

**AI Recommendation**: **Option 1** (deploy extra crane) - lowest cost, safest outcome.

---

### 5. Visibility Requirements - Constraint ID: T-WX-002

**Rule**: `visibility ≥ minimum_safe_visibility`

**Type**: **HARD** constraint for pilotage

**Visibility Standards**:
- **Open sea/approach**: 2 nautical miles minimum
- **Channel navigation**: 1 nautical mile minimum
- **Pilot boarding**: 500 meters minimum
- **Berthing operations**: 200 meters minimum

**Fog Scenario**:

**Conditions**: Dense fog at port entrance
- Current visibility: 200 meters
- Pilotage requirement: 500 meters minimum

**Vessel Queue**:
- MV Atlantic Voyager: ETA 0600 - ❌ **SUSPENDED**
- MV Pacific Trader: ETA 0630 - ❌ **SUSPENDED**
- MV Indian Ocean: ETA 0700 - ❌ **SUSPENDED**

**Forecast**: Fog clearing by 0900

**AI Rescheduling**:
```
Original ETA | New Berthing Time | Delay (hours)
-------------|------------------|-------------
0600         | 0930            | 3.5
0630         | 1030            | 4.0
0700         | 1130            | 4.5
```

**Rationale**: Safety overrides schedule. All pilotage operations suspended until visibility improves. This is non-negotiable.

---

### 6. Wave Height Limits - Constraint ID: T-WX-003

**Rule**: `wave_height < pilot_boarding_limit`

**Description**: Pilot boarding from pilot boat to vessel requires calm seas.

**Pilot Boarding Wave Limits**:
- **Optimal conditions**: <1.0 meter wave height
- **Acceptable**: 1.0-2.0 meters (experienced pilots only)
- **Marginal**: 2.0-3.0 meters (daylight only, high-risk)
- **Prohibited**: >3.0 meters (unsafe)

**Example**:
- **Wave height**: 3.5 meters (storm conditions)
- **Pilot boarding**: ❌ **SUSPENDED**
- **Vessels at anchorage**: 8 vessels waiting
- **Estimated clearing**: 12-18 hours

**Alternative**: Some ports have **helicopter pilot transfer** for emergency situations (medical, security), but not for routine operations.

---

### 7. Storm Warnings & Port Closure - Constraint ID: T-WX-004

**Rule**: `IF storm_category ≥ threshold THEN port_operations = SUSPENDED`

**Description**: Severe weather triggers port-wide operational suspensions.

**Storm Response Levels**:

| Alert Level | Wind Speed | Actions |
|-------------|-----------|---------|
| **Yellow Alert** | 35-45 knots | Non-essential operations suspended |
| **Orange Alert** | 45-55 knots | All cargo operations ceased, vessels secure |
| **Red Alert** | >55 knots | Port evacuation, vessels depart or double-moored |
| **Cyclone/Hurricane** | >65 knots | Port closed 24-48 hours advance, all vessels cleared |

**Pre-Storm Protocol**:
1. **72 hours before**: Storm watch issued
2. **48 hours before**: Yellow alert - prepare for suspension
3. **24 hours before**: Orange alert - complete critical operations
4. **12 hours before**: Red alert - vessels depart or secure
5. **Storm passage**: Port closed
6. **Post-storm**: Damage assessment (2-6 hours) before reopening

**Decision Impact**: AI berth allocator must avoid assigning vessels with >24-hour cargo operations if storm expected within 48 hours.

---

### 8. Temperature & Cargo Sensitivity - Constraint ID: T-WX-005

**Type**: **SOFT** constraint (commercial optimization)

**Description**: Some cargoes are temperature-sensitive and prefer certain weather conditions.

**Temperature-Sensitive Cargoes**:
- **Perishables**: Prefer cool weather (<25°C) for minimal refrigeration load
- **Chemicals**: Some have temperature restrictions (e.g., volatile liquids <30°C)
- **Bitumen/Asphalt**: Require heating if temperature <40°C
- **Steel coils**: Prefer dry weather (rain causes surface rust)

**Optimization Example**:
- **Cargo**: Steel coils (rain-sensitive)
- **Weather Forecast**:
  - Today: Heavy rain (12 hours)
  - Tomorrow: Clear skies

**Decision**: If demurrage cost is moderate, delay berthing by 12 hours to avoid water damage to steel ($50-100 per ton rust treatment cost).

---

## Integration with AI Weather Module

### Query Example:
**Question**: "Can MV Cape Ore transit the channel at 0800?"

**Expected RAG Response**:
"No. Based on tidal window calculations (T-TIDE-001), MV Cape Ore has a draft of 17.5 meters and requires minimum 1.5m UKC, totaling 19.0 meters water depth needed. At 0800, the tide is near low water (+0.2m above chart datum), providing only 16.2 meters total depth. This is 2.8 meters short of the requirement and poses a grounding risk. The vessel must wait until the high tide window at 1030-1330 (centered on 1200 HW) when depth reaches 19.5 meters. This is a HARD safety constraint that cannot be waived."

---

## Related Documents

- Layer 6: Under Keel Clearance (UKC) detailed calculations
- Weather Emergency Procedures Manual
- Tidal Predictions Tables (Port Authority)

---

**Keywords**: tidal windows, high tide, low tide, UKC, weather constraints, wind speed, visibility, wave height, storm warnings, fog, pilot boarding, crane operations, tidal current, channel navigation
