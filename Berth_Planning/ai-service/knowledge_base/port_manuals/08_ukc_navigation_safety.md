# Port Operations Manual: Under Keel Clearance (UKC) & Navigation Safety

**Document Type**: Port Operations Manual - Hard Constraints (Safety Critical)
**Category**: Layer 6 - UKC & Navigation Safety Constraints
**Classification**: HARD (ALL constraints non-negotiable)
**Applies To**: Deep-draft vessels, channel transit, navigation safety

---

## Overview

Under Keel Clearance (UKC) and navigation safety constraints are the most critical safety parameters in berth allocation and vessel transit. These are **ABSOLUTE HARD CONSTRAINTS** - violations result in grounding, collision, or environmental disaster. No commercial, operational, or political considerations can override these requirements.

**UKC Definition**: The vertical distance between the deepest point of a vessel's keel and the seabed. Insufficient UKC causes grounding.

---

## UKC Constraint Components

### 1. Static UKC - Constraint ID: N-UKC-001

**Rule**: `available_depth - vessel_static_draft ≥ minimum_static_UKC`

**Description**: Static UKC is the clearance when vessel is at rest (zero speed, no external forces).

**Minimum Static UKC Standards**:

| Vessel Type | Minimum UKC | Rationale |
|------------|-------------|-----------|
| **Small vessels** (<10,000 GT) | 0.8-1.0 meters | Moderate safety margin |
| **Medium vessels** (10,000-80,000 GT) | 1.0-1.5 meters | Standard commercial vessels |
| **Large vessels** (80,000-200,000 GT) | 1.5-2.0 meters | Post-Panamax, bulk carriers |
| **Very large** (>200,000 GT) | 2.0-3.0 meters | VLCC, ULCV |
| **Ultra-deep draft** (Draft >18m) | 2.5-3.5 meters | Safety + uncertainty margin |

**Calculation Example**:
```
Vessel: MV Iron Duke (Capesize Bulk Carrier)
Static Draft: 17.8 meters
Required UKC: 1.5 meters (minimum)
Minimum Safe Depth Required: 17.8 + 1.5 = 19.3 meters

Channel Specifications:
- Charted Depth: 18.5 meters
- Current Tide: +2.0 meters (High Water)
- Available Depth: 20.5 meters

Static UKC Check: 20.5 - 17.8 = 2.7 meters ✓ SAFE (2.7 > 1.5)
```

---

### 2. Dynamic UKC - Squat Effect - Constraint ID: N-UKC-002

**Rule**: `total_UKC = static_UKC - squat - heel - wave_response ≥ minimum_total_UKC`

**Description**: When vessels move through water, they sink deeper (squat effect). This dynamic sinkage reduces effective UKC.

**Squat Calculation Formula**:
```
Squat (meters) = (Cb × V² × B) / (g × d)

Where:
- Cb = Block coefficient (vessel fullness: 0.6-0.85)
- V = Vessel speed (m/s)
- B = Vessel beam (meters)
- g = Gravity constant (9.81 m/s²)
- d = Water depth under keel (meters)

Simplified: Squat ≈ 0.02 × V² × Cb

Example:
Vessel speed: 8 knots = 4.1 m/s
Block coefficient: 0.80 (bulk carrier)
Squat = 0.02 × (4.1)² × 0.80 = 0.27 meters
```

**Speed vs. Squat Relationship**:
| Speed (knots) | Approximate Squat (large vessel) |
|---------------|--------------------------------|
| 4 knots | 0.10-0.15 meters |
| 6 knots | 0.20-0.30 meters |
| 8 knots | 0.35-0.50 meters |
| 10 knots | 0.55-0.75 meters |
| 12 knots | 0.80-1.20 meters |

**Critical Insight**: Squat increases with SQUARE of speed. Doubling speed quadruples squat.

**Channel Speed Restrictions** (to manage squat):
- **Deep channels** (depth > 2× draft): 10-12 knots permitted
- **Moderate channels** (depth = 1.5-2× draft): 6-8 knots max
- **Shallow channels** (depth < 1.5× draft): 4-6 knots max, pilot mandatory

---

### 3. Heel Allowance (Turning) - Constraint ID: N-UKC-003

**Rule**: `heel_sinkage = (B/2) × sin(heel_angle)`

**Description**: When vessels turn, they heel (lean) to one side, causing one side of the keel to sink deeper.

**Heel Angle in Turns**:
- **Gentle turn (>1000m radius)**: 3-5° heel
- **Moderate turn (500-1000m radius)**: 8-12° heel
- **Sharp turn (<500m radius)**: 15-20° heel (emergency only)

**Heel Depth Calculation Example**:
```
Vessel Beam: 48 meters
Turn: 15° heel (sharp turn in narrow channel)

Heel Sinkage = (48/2) × sin(15°)
             = 24 × 0.259
             = 6.2 meters additional depth on one side
```

**Practical Impact**:
- **Port side keel**: Rises 3 meters (gains UKC)
- **Starboard side keel**: Sinks 3 meters (loses UKC)

**Critical Decision**: For ultra-large vessels in shallow channels, sharp turns may be prohibited due to heel sinkage risk.

---

### 4. Wave Response Allowance - Constraint ID: N-UKC-004

**Rule**: `wave_allowance = function(wave_height, wave_period, vessel_length)`

**Description**: Ocean waves cause vessels to pitch (bow/stern up-down) and heave (entire vessel up-down), temporarily reducing UKC.

**Wave Allowance Standards**:

| Sea State | Wave Height | Wave Allowance (Large Vessel) |
|-----------|------------|------------------------------|
| **Calm (0-1)** | 0-0.5m | +0.0-0.1m |
| **Smooth (2)** | 0.5-1.25m | +0.1-0.2m |
| **Slight (3)** | 1.25-2.5m | +0.2-0.4m |
| **Moderate (4)** | 2.5-4.0m | +0.4-0.7m |
| **Rough (5)** | 4.0-6.0m | +0.7-1.2m |
| **Very Rough (6+)** | >6.0m | Operations suspended |

**Example**:
- **Sea State 3** (slight seas, 2m wave height)
- **Wave Allowance**: 0.3 meters
- **Impact**: Must add 0.3m to required UKC calculation

---

## Complete UKC Calculation (All Factors)

### Comprehensive Example: Capesize Bulk Carrier Transit

**Vessel Specifications**:
- Name: MV Iron Duke
- LOA: 289 meters
- Beam: 45 meters
- Static Draft: 17.8 meters
- Block Coefficient (Cb): 0.82
- Transit Speed: 8 knots (4.1 m/s)

**Channel Specifications**:
- Charted Depth: 18.5 meters
- Current Tide: +2.0 meters (High Water)
- Available Depth: 20.5 meters

**Environmental Conditions**:
- Sea State: 3 (slight seas, 2m waves)
- Channel: Requires 15° turn at narrowest point

**UKC Calculation Breakdown**:

```
┌───────────────────────────────────────────────────────┐
│ Component                | Value    | Calculation     │
├───────────────────────────────────────────────────────┤
│ Static Draft             | 17.80 m  | Given           │
│ Squat (8 knots)          | +0.45 m  | 0.02×V²×Cb      │
│ Heel (15° turn)          | +0.30 m  | B/2×sin(15°)    │
│ Wave Response            | +0.25 m  | Sea State 3     │
├───────────────────────────────────────────────────────┤
│ TOTAL DYNAMIC DRAFT      | 18.80 m  | Sum of above    │
│ Available Depth          | 20.50 m  | Chart + Tide    │
│ CALCULATED UKC           | 1.70 m   | 20.50 - 18.80   │
│ REQUIRED MIN UKC         | 1.50 m   | Port standard   │
├───────────────────────────────────────────────────────┤
│ SAFETY MARGIN            | 0.20 m   | Excess UKC      │
│ STATUS                   | ✓ SAFE   | 1.70 > 1.50     │
└───────────────────────────────────────────────────────┘
```

**AI Decision**: **APPROVED** for current tidal window (High Water ± 1.5 hours). Transit must occur between 1030-1330.

**If Attempted at Low Water** (+0.2m tide):
```
Available Depth: 18.7 meters
Dynamic Draft: 18.8 meters
Calculated UKC: -0.1 meters ❌ GROUNDING RISK
Status: REJECTED
```

---

## Channel Navigation Constraints

### 5. Channel Width Requirements - Constraint ID: N-CHAN-001

**Rule**: `channel_width ≥ vessel_beam × safety_factor`

**Description**: Channels must be sufficiently wide for vessel to navigate without running aground on channel edges.

**Channel Width Standards**:
- **One-way traffic**: Minimum 3× vessel beam
- **Two-way traffic (wide channel)**: Minimum 6× vessel beam
- **Two-way traffic (narrow)**: Alternating one-way windows (tidal gates)

**Example**:
- **Vessel Beam**: 48 meters (ULCV)
- **Channel Width**: 200 meters
- **Safety Factor**: 200 / 48 = 4.2× beam
- **Assessment**: Adequate for one-way traffic, insufficient for two-way (need 6× = 288m)

**Decision**: Operate as one-way channel with tidal gates (see Layer 4 - Tidal Gate constraints).

---

### 6. Bend Radius Limitations - Constraint ID: N-CHAN-002

**Rule**: `bend_radius ≥ vessel_LOA × minimum_ratio`

**Description**: Sharp bends require vessels to turn tightly, increasing heel and drift. Very large vessels cannot negotiate tight bends.

**Minimum Bend Radius**:
- **Standard vessels (<250m LOA)**: 3× LOA (e.g., 750m radius)
- **Large vessels (250-350m LOA)**: 4× LOA (e.g., 1400m radius)
- **Ultra-large (>350m LOA)**: 5× LOA (e.g., 2000m radius)

**Example Disqualification**:
- **Vessel**: ULCV (400m LOA)
- **Required radius**: 5× 400 = 2,000 meters
- **Channel bend radius**: 1,200 meters
- **Decision**: ❌ **REJECTED** - Vessel cannot safely navigate this bend

**Alternative**: Use tug escort through bend (if feasible) or prohibit vessel from this route entirely.

---

### 7. Traffic Separation Schemes - Constraint ID: N-CHAN-003

**Rule**: `inbound_outbound_lanes_must_be_separated`

**Description**: Busy ports use Traffic Separation Schemes (TSS) with dedicated inbound/outbound lanes, similar to highway lanes.

**TSS Components**:
- **Inbound lane**: Minimum width 500-1000 meters
- **Outbound lane**: Minimum width 500-1000 meters
- **Separation zone**: 200-500 meters (buffer between lanes)
- **Pilot boarding area**: Designated offshore zone

**VTS (Vessel Traffic Service) Management**:
- Radar monitoring of all vessel positions
- Traffic sequencing (inbound/outbound scheduling)
- Collision avoidance coordination
- Real-time weather/tide updates

---

### 8. Speed Limits - Constraint ID: N-CHAN-004

**Rule**: `vessel_speed ≤ channel_speed_limit`

**Description**: Channels have maximum speed limits to:
1. Control squat effect (see N-UKC-002)
2. Reduce wave wash (bank erosion)
3. Maintain maneuverability
4. Minimize collision risk

**Typical Speed Limits**:
- **Open approach channel**: 10-12 knots
- **Inner harbor**: 6-8 knots
- **Narrow channel (<500m wide)**: 4-6 knots
- **Berthing area**: 2-3 knots (dead slow)

---

## Anchorage Management

### 9. Anchorage Capacity - Constraint ID: N-ANCH-001

**Rule**: `occupied_anchorage_positions < maximum_capacity`

**Description**: Anchorage areas have limited capacity based on water area and safe separation distances.

**Anchorage Design Standards**:
- **Swing circle radius**: Minimum 1.5× vessel LOA
- **Vessel separation**: Minimum 2× swing circle diameter
- **Depth zoning**: Deep anchorage (>15m), shallow anchorage (<15m)

**Capacity Calculation Example**:
```
Anchorage Area: 5 km × 3 km = 15 km²
Average Vessel LOA: 200 meters
Swing Circle Radius: 1.5 × 200 = 300 meters
Swing Circle Area: π × (300)² = 0.28 km²
Separation Required: 2× diameter = 1.2 km between centers
Effective Area per Vessel: 1.2 × 1.2 = 1.44 km²
Maximum Capacity: 15 km² / 1.44 km² = ~10 vessels
```

**Congestion Management**:
- **<70% capacity**: Normal operations
- **70-85% capacity**: Monitor closely
- **85-95% capacity**: Limit new arrivals
- **>95% capacity**: Anchorage full - vessels diverted to alternate anchorage or drift at sea

---

### 10. Swing Circle Conflicts - Constraint ID: N-ANCH-003

**Rule**: `vessel_swing_circles_must_not_overlap`

**Description**: When vessels anchor, they swing around the anchor point with tidal/wind changes. Swing circles must not overlap to prevent collisions.

**Example Scenario**:
- **Anchorage Position A1**: MV Atlantic Star (300m LOA, swing radius 450m)
- **Anchorage Position A2**: 800 meters from A1
- **New Arrival**: MV Pacific Giant (280m LOA, swing radius 420m)

**Separation Check**:
```
Min Required Separation = 450m + 420m = 870 meters
Actual Separation = 800 meters
Gap = 800 - 870 = -70 meters ❌ CONFLICT
```

**Decision**: MV Pacific Giant cannot use Position A2 (too close to A1). Assign to Position A4 (1200m separation) instead.

---

## Integration with AI Navigation Module

### Query Example:
**Question**: "Why can't MV Iron Duke transit the channel at low tide?"

**Expected RAG Response**:
"Based on Under Keel Clearance calculations (N-UKC-001, N-UKC-002, N-UKC-003, N-UKC-004), MV Iron Duke requires a total of 19.3 meters water depth:

- Static draft: 17.8m
- Dynamic squat at 8 knots: +0.45m
- Heel allowance (15° turn): +0.30m
- Wave response (Sea State 3): +0.25m
- **Total dynamic draft**: 18.8m
- **Required minimum UKC**: 1.5m
- **Total depth needed**: 18.8 + 1.5 = 20.3 meters

At low tide (+0.2m above chart datum), the channel provides only 18.7 meters depth, which is 1.6 meters short of the requirement. Attempting transit would result in grounding (keel striking seabed), causing:
- Vessel structural damage ($5-50 million)
- Cargo loss (potential total loss)
- Channel blockage (port closure)
- Environmental damage (for oil/chemical cargoes)

This is an ABSOLUTE HARD constraint. The vessel must wait for high tide (available depth 20.5m) within the tidal window of 1030-1330. No commercial, operational, or priority considerations can override this safety requirement."

---

## Related Documents

- Tidal Prediction Tables
- Channel Navigation Charts
- VTS Operating Procedures
- Port Safety Management System

---

**Keywords**: under keel clearance, UKC, squat effect, dynamic draft, navigation safety, channel navigation, grounding prevention, tidal windows, heel allowance, wave response, channel width, bend radius, anchorage management, swing circle, traffic separation
