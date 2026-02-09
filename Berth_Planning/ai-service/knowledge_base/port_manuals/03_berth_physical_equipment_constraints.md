# Port Operations Manual: Berth Physical & Equipment Constraints

**Document Type**: Port Operations Manual - Hard Constraints
**Category**: Layer 2 - Berth/Terminal-Level Constraints
**Classification**: HARD (Infrastructure Fixed)
**Applies To**: Berth allocation and terminal operations

---

## Overview

Berth physical and equipment constraints define the infrastructure limitations and specialized equipment capabilities at each berth. These are primarily HARD constraints that cannot be modified without significant capital investment.

## Physical Infrastructure Constraints

### 1. Fender Capacity - Constraint ID: B-PHYS-003

**Rule**: `vessel.displacement ≤ berth.fender_capacity`

**Description**: Fenders are rubber/foam cushioning systems that absorb berthing impact energy. They have maximum vessel displacement ratings based on:
- Fender type (cell, cone, arch, cylindrical)
- Energy absorption capacity (kJ)
- Reaction force limits (tons)

**Fender Rating Categories**:
- **Light-duty berths**: Up to 50,000 tons (coastal, feeder vessels)
- **Medium-duty berths**: 50,000-150,000 tons (Panamax, mid-size bulk carriers)
- **Heavy-duty berths**: 150,000-250,000 tons (Post-Panamax, VLCC)
- **Super-heavy berths**: 250,000+ tons (ULCV, mega tankers)

**Example Failure Scenario**:
- **Vessel**: MV Mega Container (220,000 tons displacement)
- **Berth F1**: Fender rating 180,000 tons ❌ **REJECTED**
  - Risk: Fender crushing, structural damage to quay wall
  - Repair cost: $500,000-2,000,000
  - Downtime: 30-60 days
- **Berth F3**: Fender rating 250,000 tons ✓ **ELIGIBLE**

**Decision Rationale**: Fender damage risk is unacceptable. This is a HARD constraint enforced by port engineering standards.

---

### 2. Mooring Bollard Capacity - Constraint ID: B-PHYS-004

**Rule**: `mooring_tension ≤ bollard.safe_working_load (SWL)`

**Description**: Bollards are steel posts for securing mooring lines. They have Safe Working Load (SWL) limits based on:
- Bollard type (single, double, cruciform)
- Material strength (cast iron, steel)
- Foundation depth and anchor bolts

**Bollard SWL Standards**:
- **Light bollards**: 50-75 tons SWL
- **Medium bollards**: 75-150 tons SWL
- **Heavy bollards**: 150-250 tons SWL
- **Special heavy**: 250+ tons SWL

**Mooring Tension Calculation**:
```
Tension = f(vessel_displacement, wind_speed, current_speed, wave_height)

Example:
- Vessel: 180,000 tons GT
- Wind: 45 knots (storm conditions)
- Calculated tension per bollard: 85 tons
```

**Safety Assessment**:
- **Berth G2**: Bollard SWL 100 tons → **SAFE** (85 < 100)
- **Berth G4**: Bollard SWL 60 tons → **UNSAFE** (85 > 60)

**Storm Weather Protocol**: If high winds expected (>35 knots), only berths with SWL ≥ 100 tons are eligible for large vessels.

---

### 3. Quay Load Bearing Capacity - Constraint ID: B-PHYS-005

**Rule**: `cargo_weight_per_sqm ≤ berth.max_bearing_load`

**Description**: Quay aprons have maximum load-bearing capacity measured in tons per square meter (t/m²). Exceeding this causes:
- Concrete cracking
- Foundation settlement
- Structural failure

**Typical Quay Ratings**:
- **Light-duty quays**: 2-5 t/m² (general cargo)
- **Standard quays**: 5-10 t/m² (containers, bulk)
- **Heavy-duty quays**: 10-20 t/m² (project cargo, heavy machinery)
- **Special quays**: 20+ t/m² (steel coils, heavy industrial equipment)

**Example Scenario**:
- **Cargo**: Steel coils (each coil = 25 tons, dimensions 2m × 2m)
- **Load per coil**: 25 tons / 4 m² = 6.25 t/m²
- **Quay H1 rating**: 8 t/m² ✓ **SAFE**
- **Quay H2 rating**: 4 t/m² ❌ **UNSAFE** (risk of cracking)

**Heavy-Lift Operations**: Project cargo (transformers, wind turbine blades, oil rig components) require specialized heavy-duty quays with reinforced foundations.

---

## Equipment Constraints

### 4. Shore Crane Outreach - Constraint ID: B-SPEC-003

**Rule**: `vessel.beam/2 ≤ crane.max_outreach`

**Description**: Ship-to-Shore (STS) gantry cranes have maximum outreach (horizontal reach from crane rail to furthest container stack on vessel).

**Container Vessel Beam Standards**:
- **Feeder vessels**: 6-8 containers wide (beam: 20-25m) → Outreach needed: 13-16 rows
- **Panamax**: 13 containers wide (beam: 32m) → Outreach needed: 18 rows
- **Post-Panamax**: 18-22 containers wide (beam: 43-48m) → Outreach needed: 20-22 rows
- **Mega-Max (ULCV)**: 24 containers wide (beam: 61m) → Outreach needed: 24-25 rows

**Example Disqualification**:
- **Vessel**: MV MSC Gülsün (World's largest container ship)
  - Beam: 61.5 meters
  - Container width: 24 across

- **Berth H1**: STS crane outreach = 22 containers ❌ **REJECTED**
  - Cannot reach outer 2 container stacks
  - 8% of cargo inaccessible

- **Berth H2**: STS crane outreach = 24 containers ✓ **ELIGIBLE**
- **Berth H3**: STS crane outreach = 25 containers ✓ **ELIGIBLE**

**Consequence of Insufficient Outreach**: Vessel must partially discharge/load, then shift to another berth or port → massive delay and cost.

---

### 5. Crane Availability - Constraint ID: B-SPEC-002

**Rule**: `required_cranes ≤ berth.available_cranes`

**Type**: **SOFT** constraint (can optimize crane allocation)

**Crane Productivity Standards**:
- **Single crane**: 25-35 container moves per hour (MPH)
- **Twin-lift cranes**: 40-50 MPH (lift 2 containers simultaneously)
- **Tandem operation**: 2 cranes on same vessel = 50-70 MPH combined

**Berth Crane Assignment Example**:
- **Vessel**: 2,000 TEU container vessel
- **Discharge/Load**: 1,500 moves
- **Target completion**: 12 hours
- **Required productivity**: 1,500 / 12 = 125 MPH
- **Cranes needed**: 125 / 35 = 3.6 → **4 cranes** optimal

**Berth Comparison**:
- **Berth K1**: 5 STS cranes available ✓ Can assign 4 cranes
- **Berth K2**: 3 STS cranes available → Partial (extends completion to 14-15 hours)
- **Berth K3**: 2 STS cranes available → Insufficient (20+ hours, demurrage risk)

**Optimization Opportunity**: While K2 is acceptable, K1 is preferred to minimize vessel turnaround time.

---

### 6. Bulk Berth Specialization - Constraint ID: B-SPEC-004

**Rule**: `berth.cargo_handling_system = vessel.cargo_type`

**Description**: Bulk terminals have specialized cargo handling systems that cannot handle incompatible cargoes.

**Dry Bulk Systems**:
- **Grab cranes + hoppers**: Coal, iron ore, aggregates
- **Pneumatic systems**: Grain, cement, powder materials
- **Conveyor belts**: Long-distance transfer to storage silos
- **Ship loaders**: High-capacity loading (up to 10,000 tons/hour)

**Contamination Prevention Rules**:

| Berth Type | Allowed Cargoes | PROHIBITED Cargoes |
|-----------|----------------|-------------------|
| **Coal-dedicated** | Coal, coke | ANY food-grade cargo |
| **Clean grain** | Wheat, barley, corn, soybeans | Coal, fertilizer, chemicals |
| **Fertilizer** | Urea, DAP, potash | Food-grade grain |
| **General bulk** | Aggregates, sand, steel products | Food/feed products |

**Example Rejection**:
- **Vessel**: MV Wheat Harvest (35,000 MT food-grade wheat)
- **Berth J1**: Coal-dedicated, contaminated with coal dust ❌ **REJECTED**
  - Risk: Contamination renders wheat unfit for human consumption
  - Loss value: $500-800 per ton = $17.5-28 million total
  - Legal liability: Food safety violation

- **Berth J2**: Clean grain berth with pneumatic suckers ✓ **ELIGIBLE**

**Hard Rule**: Food safety regulations prohibit ANY cross-contamination risk. This is non-negotiable.

---

## Liquid Bulk Terminal Equipment

### 7. Pipeline & Manifold Compatibility - Constraint ID: B-SPEC-004 (Liquid)

**Description**: Liquid bulk berths have dedicated pipelines with specific:
- Diameter (6-48 inch)
- Pump capacity (100-10,000 m³/hour)
- Pipeline material (steel for petroleum, stainless for chemicals)
- Heating systems (for viscous products like bitumen, palm oil)

**Pipeline Segregation**:
- **Black products pipeline**: Crude oil, fuel oil, asphalt (cannot mix with clean products)
- **White products pipeline**: Gasoline, diesel, jet fuel (separate from black)
- **Chemical pipeline**: Methanol, ethanol, acids (dedicated, cannot share)
- **Edible oils pipeline**: Food-grade vegetable oils (strictest contamination controls)

**Flushing Requirements Between Products**:
- Black-to-Black: Minimal flushing (1-2 hours)
- White-to-White: Standard flushing (4-6 hours)
- Black-to-White: Intensive flushing (24-48 hours) + testing
- Chemical-to-Food: **PROHIBITED** - cannot share pipeline

---

## RoRo Berth Specifications

### 8. Ramp Load Capacity - Constraint ID: B-SPEC-005

**Description**: RoRo ramps have maximum axle load and total weight limits.

**Ramp Specifications**:
- **Standard car carrier ramp**: 10-ton axle load, 80-100 tons total
- **Heavy RoRo ramp**: 25-ton axle load, 150-200 tons total
- **Project cargo ramp**: 40-ton axle load, 300+ tons total

**Example**:
- **Cargo**: Mining trucks (each unit = 180 tons, 6 axles = 30 tons/axle)
- **Standard ramp**: Max 10 tons/axle ❌ **REJECTED** (3× over limit)
- **Heavy ramp**: Max 25 tons/axle ❌ **REJECTED** (20% over limit)
- **Project cargo ramp**: Max 40 tons/axle ✓ **ELIGIBLE**

---

## Integration with AI Berth Allocator

### Query Example:
**Question**: "Why can't the mega container ship berth at Berth H1?"

**Expected RAG Response**:
"Based on crane outreach constraints (B-SPEC-003), the mega container vessel has a beam of 61.5 meters with containers stacked 24-wide. Berth H1's STS cranes have maximum outreach of 22 containers, which means the outer 2 container stacks (8% of cargo) would be unreachable. This is a HARD constraint - the berth's physical equipment cannot service this vessel size. The vessel must be assigned to Berth H2 or H3 which have cranes with 24-25 container outreach capability."

---

## Related Documents

- Layer 1: Vessel Physical Dimensions
- Layer 3: Resource Availability (Crane operators, equipment)
- Safety Manual: Fender and Bollard Inspection Procedures

---

**Keywords**: fender capacity, bollard SWL, quay load bearing, crane outreach, bulk terminal, pipeline, RoRo ramp, berth equipment, infrastructure constraints, port facilities
