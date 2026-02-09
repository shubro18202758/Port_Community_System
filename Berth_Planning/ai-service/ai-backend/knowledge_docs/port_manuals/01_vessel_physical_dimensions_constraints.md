# Port Operations Manual: Vessel Physical Dimensions Constraints

**Document Type**: Port Operations Manual - Hard Constraints
**Category**: Layer 1 - Vessel-Level Constraints
**Classification**: HARD (Non-Negotiable)
**Applies To**: All vessel berthing operations

---

## Overview

Physical dimension constraints are the most fundamental berth allocation requirements. These are **non-negotiable HARD constraints** - physical incompatibility means NO allocation is possible, regardless of commercial or operational considerations.

## Constraint Definitions

### 1. Length Overall (LOA) - Constraint ID: V-DIM-001

**Formula**: `vessel.loa ≤ berth.max_loa`

**Description**: The vessel's length overall (LOA) must not exceed the berth's maximum LOA capacity. This includes safety margins for mooring lines and vessel movement.

**Typical Safety Margins**:
- Container vessels: 10-15 meters clearance
- Bulk carriers: 5-10 meters clearance
- Tankers: 15-20 meters clearance

**Example Scenario**:
A Post-Panamax container vessel (LOA: 366m) cannot be assigned to a berth with maximum LOA of 350m. Even if the berth is otherwise perfect, this is a complete disqualification.

---

### 2. Beam (Vessel Width) - Constraint ID: V-DIM-002

**Formula**: `vessel.beam ≤ berth.max_beam`

**Description**: Vessel beam must fit within berth alongside clearances, considering fender systems and adjacent berth operations.

**Critical Considerations**:
- Ultra-Large Container Vessels (ULCV): Beam up to 61.5 meters
- Minimum clearance from adjacent berths: 5 meters
- Fender compression allowance: 1-2 meters

---

### 3. Static Draft - Constraint ID: V-DIM-003

**Formula**: `vessel.draft ≤ berth.max_draft`

**Description**: The vessel's arrival draft must not exceed available water depth at the berth.

**Important Notes**:
- Static draft is measured when vessel is at rest
- Must account for tidal variations (see tidal window calculations)
- Charted depth + tidal height - vessel draft = Under Keel Clearance (UKC)
- Minimum UKC requirement: 1.5 meters (standard), 2.0 meters (large vessels)

**Tidal Dependency**:
Some vessels may only be eligible during high tide windows. For example:
- Vessel draft: 14.5m
- Berth charted depth: 14.0m
- High tide addition: +1.2m
- Available depth at high tide: 15.2m ✓ ELIGIBLE
- Available depth at low tide: 14.0m ✗ REJECTED

---

### 4. Air Draft (Height Above Water) - Constraint ID: V-DIM-004

**Formula**: `vessel.air_draft ≤ terminal.max_air_draft`

**Description**: Air draft is the height from keel to the highest point on the vessel (mast, antenna, stack). Critical for berths requiring passage under bridges or gantry cranes.

**Common Air Draft Restrictions**:
- River ports with highway bridges: 45-55 meters
- Terminals with overhead gantry cranes: 48-52 meters
- Open berths: No restriction

**Example**:
A vessel with 52m air draft cannot reach a berth if the approach requires passing under a 48m gantry crane. Alternative: Assign to outer berth with no air draft restriction.

---

### 5. Gross Tonnage (GT) Limit - Constraint ID: V-DIM-005

**Formula**: `vessel.gt ≤ berth.max_gt`

**Description**: Berths have maximum gross tonnage limits based on fender capacity, mooring bollard strength, and structural quay loading.

**GT Categories**:
- Small vessels: <10,000 GT
- Medium vessels: 10,000-50,000 GT
- Large vessels: 50,000-150,000 GT
- Very Large vessels: >150,000 GT

**Structural Impact**:
A vessel with 220,000 GT displacement exceeds a berth rated for 180,000 GT maximum. This creates risk of:
- Fender damage
- Bollard failure
- Quay wall structural stress

**Decision**: REJECTED - Must assign to berth with 250,000 GT+ rating.

---

## Constraint Hierarchy

**All physical dimension constraints are EQUAL in priority** - violation of ANY dimension constraint results in immediate disqualification from berth consideration.

### Constraint Check Order (for computational efficiency):
1. **LOA** - Fastest to check, filters out ~40% of incompatible berths
2. **Draft** - Checks depth + tidal windows
3. **Beam** - Verifies lateral clearance
4. **Air Draft** - Only for berths with overhead restrictions
5. **GT** - Final structural capacity verification

---

## Integration with AI Decision System

### Query Example for RAG Retrieval:
**User Question**: "Why can't MV Pacific Fortune (LOA: 366m) berth at Berth A1?"

**Expected RAG Response**:
"Based on port operations manual for physical dimensions, MV Pacific Fortune has LOA of 366 meters which exceeds Berth A1's maximum LOA capacity of 350 meters. This is a HARD constraint violation (V-DIM-001) and cannot be overridden. Vessel physical dimensions are non-negotiable - the vessel physically cannot fit safely. Alternative berths with LOA ≥ 366m must be considered (e.g., Berth A2 with 400m LOA capacity)."

---

## Related Constraints

- **Layer 2**: Berth Physical Constraints (berth-side specifications)
- **Layer 4**: Tidal Windows (affects dynamic draft calculations)
- **Layer 6**: Under Keel Clearance (UKC) - safety margins for draft

---

## Regulatory References

- **IMO Resolution A.1120(30)**: Mooring arrangements for ships at berth
- **PIANC Report 145**: Guidelines for berth design
- **Port Authority Safety Code**: Minimum clearance requirements

---

**Keywords**: LOA, beam, draft, air draft, gross tonnage, vessel dimensions, physical constraints, hard constraints, berth allocation, vessel-berth compatibility
