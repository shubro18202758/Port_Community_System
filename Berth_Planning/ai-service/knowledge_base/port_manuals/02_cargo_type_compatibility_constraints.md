# Port Operations Manual: Cargo Type & Compatibility Constraints

**Document Type**: Port Operations Manual - Hard Constraints
**Category**: Layer 1 - Vessel-Level Constraints
**Classification**: HARD (Safety Critical)
**Applies To**: All cargo operations

---

## Overview

Cargo type compatibility constraints ensure that vessels are assigned to berths with appropriate cargo handling equipment and safety certifications. These are **HARD constraints** with safety, regulatory, and contamination implications.

## Constraint Definitions

### 1. Cargo Type Match - Constraint ID: V-CARGO-001

**Rule**: `berth.cargo_types CONTAINS vessel.cargo_type`

**Description**: Berth must be equipped to handle the specific cargo type being loaded/discharged.

**Primary Cargo Categories**:

| Cargo Type | Berth Requirements | Example Vessels |
|------------|-------------------|-----------------|
| **Container** | Gantry cranes (STS), reefer plugs, container yard | Container ships, feeder vessels |
| **Dry Bulk** | Grab cranes, hoppers, conveyor systems | Bulk carriers (coal, grain, ore) |
| **Liquid Bulk** | Pipeline manifolds, storage tanks, pump stations | Tankers (crude oil, chemicals, LNG) |
| **Break Bulk** | Mobile cranes, open storage, heavy-lift equipment | General cargo, project cargo |
| **RoRo** | Stern/bow ramps, vehicle lanes | Car carriers, RoRo vessels |

**Hard Rule**: A bulk carrier carrying grain CANNOT berth at a container terminal even if physically compatible. The terminal lacks grain handling conveyors/suckers required for discharge.

**Example Disqualification**:
- **Vessel**: MV Grain Master (Bulk Carrier with 45,000 MT wheat)
- **Berth T1**: Container Terminal ❌ REJECTED (no grain handling equipment)
- **Berth T2**: Liquid Bulk Terminal ❌ REJECTED (pipelines only, no solid cargo equipment)
- **Berth T3**: Dry Bulk Terminal ✓ ELIGIBLE (has grain suckers and silos)

---

### 2. Dangerous Goods (DG) Handling - Constraint ID: V-CARGO-002

**Rule**: `IF vessel.has_hazmat THEN berth.dg_certified = TRUE`

**Description**: Vessels carrying dangerous goods (IMDG classified cargo) require berths with special certifications, safety equipment, and segregation zones.

**IMDG Hazard Classes**:

| Class | Description | Segregation Requirements |
|-------|-------------|-------------------------|
| Class 1 | Explosives | 200m from all other vessels, 500m from populated areas |
| Class 2 | Gases (flammable, toxic) | 100m from passenger terminals |
| Class 3 | Flammable Liquids | 100m from ignition sources, spark-free equipment |
| Class 4 | Flammable Solids | Covered storage, fire suppression systems |
| Class 5 | Oxidizing Substances | Separate from Class 3 and 4 |
| Class 6 | Toxic Substances | Ventilation, spill containment |
| Class 7 | Radioactive Materials | Licensed berth, radiation monitoring |
| Class 8 | Corrosive Substances | Acid-resistant surfaces, neutralization equipment |
| Class 9 | Miscellaneous | Case-by-case assessment |

**Example Scenario: Chemical Tanker Segregation**:
- **Vessel**: MV Chemical Express (Methanol - IMDG Class 3 Flammable Liquid)
- **Regulatory Requirements**:
  - Minimum 100m from passenger terminals
  - No concurrent berthing with Class 1 (Explosives)
  - Spark-free crane operations

**Berth Availability Check**:
- **Berth D1**: Passenger ferry at adjacent berth (80m away) ❌ REJECTED
- **Berth D2**: Empty, 150m from nearest vessel ✓ ELIGIBLE
- **Berth D3**: Ammonium Nitrate vessel nearby (Class 1 conflict) ❌ REJECTED

**Decision**: Only Berth D2 is safe. This is a HARD constraint with legal liability - violations can result in port closure and criminal penalties.

---

### 3. Reefer Container Capability - Constraint ID: V-CARGO-003

**Rule**: `vessel.reefer_demand ≤ berth.reefer_plugs`

**Description**: Refrigerated container vessels require electrical shore power connection points (reefer plugs) to maintain cargo at -25°C to +25°C temperature range.

**Power Requirements**:
- Standard reefer plug: 380-440V, 3-phase, 32-64 Amps
- Average consumption per reefer: 3-5 kW
- Large reefer vessel: 400-600 plugs required

**Example**:
- **Vessel**: MV Fresh Atlantic (Perishable cargo - fruits, meat, pharmaceuticals)
- **Requirement**: 400 reefer containers

**Berth Capacity Check**:
- **Berth E1**: 200 reefer plugs ❌ REJECTED (insufficient - 50% shortfall)
- **Berth E2**: 500 reefer plugs ✓ ELIGIBLE
- **Berth E3**: 450 reefer plugs ✓ ELIGIBLE

**Criticality**: HARD constraint. Without adequate power, cargo spoils within 6-12 hours:
- Fresh produce: $500-1,500 per TEU loss
- Pharmaceuticals: $50,000-200,000 per TEU loss
- Total liability exposure: Multi-million dollar claims

---

### 4. Liquid Bulk Pipeline Compatibility - Constraint ID: V-CARGO-004

**Rule**: `berth.pipeline_types CONTAINS vessel.liquid_cargo_type`

**Description**: Liquid bulk terminals have dedicated pipelines for specific commodities. Cross-contamination between incompatible liquids is strictly prohibited.

**Pipeline Categories**:

| Pipeline Type | Compatible Cargoes | Incompatible Cargoes |
|--------------|-------------------|---------------------|
| **Black Products** | Crude oil, fuel oil, bitumen | Any clean/white products |
| **Clean Products** | Gasoline, diesel, jet fuel | Black products, vegetable oils |
| **Chemical Grade** | Methanol, ethanol, acids | Petroleum products |
| **Edible Oils** | Palm oil, soybean oil, sunflower oil | Chemicals, petroleum |
| **LNG/LPG** | Liquefied natural gas, propane | All other liquids |

**Example: Pipeline Mismatch**:
- **Vessel**: MV Chemical Carrier (10,000 MT Methanol)
- **Berth L1**: Crude oil pipeline ❌ REJECTED (contamination risk)
- **Berth L2**: Chemical-grade pipeline ✓ ELIGIBLE
- **Berth L3**: Edible oils pipeline ❌ REJECTED (incompatible)

**Contamination Cost**:
- Flushing and cleaning pipeline: $50,000-200,000
- Cargo value loss: $500,000+
- Port downtime: 3-7 days

**Decision**: HARD constraint - no exceptions permitted.

---

### 5. RoRo Ramp Compatibility - Constraint ID: V-CARGO-005

**Rule**: `berth.has_roro_ramp = TRUE AND berth.ramp_type IN vessel.required_ramps`

**Description**: Roll-on/Roll-off (RoRo) vessels require specialized ramps for vehicle loading/discharge.

**Ramp Types**:
- **Stern Ramp**: Most common, 25-40 meter length
- **Bow Ramp**: For bow door vessels
- **Side Ramp**: For multi-deck car carriers
- **Movable Link-Span**: Adjustable for tidal range

**Ramp Specifications**:
- Load capacity: 100-150 tons (for heavy machinery)
- Width: 10-15 meters
- Angle: Maximum 10-12 degrees gradient
- Tidal compensation: ±3-4 meters vertical adjustment

**Example**:
- **Vessel**: MV Car Express (Pure Car Carrier - 6,000 vehicles)
- **Berth R1**: Stern ramp, 35m, 120-ton capacity ✓ ELIGIBLE
- **Berth R2**: No RoRo facilities ❌ REJECTED
- **Berth R3**: Bow ramp only ❌ REJECTED (vessel has stern door)

---

## Food Safety & Contamination Prevention

**Special Rule**: Food-grade cargo CANNOT be assigned to berths previously handling contaminating substances without thorough cleaning certification.

**Contamination Risk Matrix**:

| Current Cargo | Previous Cargo | Risk Level | Action Required |
|--------------|---------------|-----------|-----------------|
| Food-grade grain | Coal | **HIGH RISK** | Complete berth washing, 48-hour drying |
| Containerized food | General cargo | **LOW RISK** | Visual inspection only |
| Edible oils | Crude oil | **PROHIBITIVE** | Never allow - use dedicated berth |

**Example**:
- **Berth J1**: Coal-dedicated (dusty, contaminated) → Can ONLY handle coal
- **Berth J2**: Clean grain berth → Food-grade only
- **Berth J3**: General bulk → Can handle either with cleaning protocols

---

## Integration with AI Decision System

### Query Example 1:
**Question**: "Can MV Grain Master with wheat cargo berth at Container Terminal T1?"

**Expected RAG Response**:
"No. Based on cargo type compatibility constraints (V-CARGO-001), Container Terminal T1 is equipped with gantry cranes for container handling and lacks the grain suction equipment, conveyors, and silos required to discharge bulk grain cargo. This is a HARD constraint - the terminal physically cannot handle this cargo type. MV Grain Master must be assigned to Dry Bulk Terminal T3 which has grain handling facilities."

### Query Example 2:
**Question**: "Why is there a segregation requirement for chemical tankers?"

**Expected RAG Response**:
"Chemical tankers carrying IMDG Class 3 (Flammable Liquids) have mandatory segregation distances per V-CARGO-002: minimum 100 meters from passenger terminals and no concurrent berthing with Class 1 explosives. This is a safety-critical HARD constraint enforced by international maritime regulations (IMDG Code). Violations pose fire/explosion risks and result in legal liability. The AI system automatically filters berths that violate segregation zones."

---

## Related Documents

- **Layer 2**: Berth Specialization & Equipment Constraints
- **Safety Manual**: Dangerous Goods Handling Procedures
- **IMDG Code**: International Maritime Dangerous Goods Regulations

---

**Keywords**: cargo type, dangerous goods, IMDG, hazmat, reefer containers, pipeline compatibility, RoRo, contamination prevention, food safety, berth specialization
