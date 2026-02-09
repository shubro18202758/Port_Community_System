# SmartBerth AI – Berth Allocation Constraints

---

## 1. Constraint Classification (High-Level)

Berth allocation constraints are classified into five layers:

- Vessel-Level Constraints  
- Berth / Terminal-Level Constraints  
- Operational Resource Constraints  
- Temporal & Environmental Constraints  
- Policy, Priority & Commercial Constraints  

Each constraint is:

- **Hard** (must be satisfied)  
- **Soft** (optimizable with penalty)  

---

## 2. Vessel-Level Constraints

These constraints are intrinsic to the vessel and non-negotiable.

---

### 2.1 Physical Dimensions (HARD)

| Constraint | Description | Data Field |
|---|---|---|
| Length Overall (LOA) | Vessel length must fit berth | `vessel.loa ≤ berth.max_loa` |
| Beam | Vessel width vs berth width | `vessel.beam ≤ berth.max_beam` |
| Draft | Draft vs berth depth | `vessel.draft ≤ berth.max_draft` |
| Air Draft (if applicable) | Bridge / gantry clearance | `vessel.air_draft ≤ terminal.max_air_draft` |

---

### 2.2 Vessel Type & Cargo (HARD)

| Constraint | Description |
|---|---|
| Cargo type compatibility | Container, bulk, liquid, RoRo (Roll-on/Roll-off) |
| Hazardous cargo rules | DG segregation requirements |
| Reefer requirement | Power points availability |
| Tank cleaning / safety | Special berth requirements |

---

### 2.3 Vessel Readiness Constraints (HARD)

| Constraint | Description |
|---|---|
| Pilot availability | Must be available at ETA |
| Tug requirement | Number & class |
| Towage window | Time-bound |
| Previous port delay | Risk factor |

---

## 3. Berth / Terminal-Level Constraints

These define what the terminal can physically and operationally support.

---

### 3.1 Berth Physical Constraints (HARD)

| Constraint | Description |
|---|---|
| Berth length | Max LOA |
| Water depth | Max draft |
| Fender strength | Vessel size limits |
| Mooring capacity | Line requirements |

---

### 3.2 Berth Availability (HARD)

| Constraint | Description |
|---|---|
| Maintenance window | Planned closures |
| Berth occupancy | Time overlap |
| Shift-based capacity | Labor availability |

---

## 4. Operational Resource Constraints

These cut across vessels and berths.

---

### 4.1 Human Resources (HARD)

| Constraint | Description |
|---|---|
| Pilot roster | Skill & availability |
| Tug crew | Class-certified |
| Gang availability | Labor shifts |

---

## 5. Temporal & Environmental Constraints

Time-dependent constraints that often trigger re-optimization.

---

### 5.1 Tidal Constraints (HARD)

| Constraint | Description |
|---|---|
| High-draft windows | Tide-dependent berthing |
| One-way navigation | Channel limits |
| Daylight-only ops | Safety rules |

---

### 5.2 Weather Constraints (HARD / SOFT)

| Constraint | Description |
|---|---|
| Wind speed limits | Crane operation |
| Visibility | Pilot boarding |
| Storm alerts | Suspension rules |

---

## 6. Policy, Priority & Commercial Constraints

These are port-specific and critical for explainability.

---

### 6.1 Priority Rules (SOFT with weight)

| Constraint | Description |
|---|---|
| Liner priority | Strategic customers |
| Government vessels | Absolute priority |
| Perishable cargo | Time-sensitive |
| Transshipment vessels | Network impact |

---

### 6.2 Commercial Constraints (SOFT)

| Constraint | Description |
|---|---|
| Contractual berth | Dedicated usage |
| Penalty minimization | Demurrage risk |
| Service-level agreements | TAT commitments |

---

## KaiTETHON

**KaiTETHON – India's premier AI-powered logistics and cargo hackathon**
