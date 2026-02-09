# SmartBerth AI - Berth Allocation & Optimization Enhanced Knowledge

**Document Version:** 2.0  
**Last Updated:** February 2026  
**Purpose:** Enhanced domain knowledge for berth allocation optimization including ETA integration, resource planning, and LLM reasoning  
**Priority:** HIGH — Core allocation engine

---

## 1. Berth Suggestion Scoring Framework

### 1.1 Multi-Factor Scoring
Each berth candidate is scored on a 0-100 scale using weighted factors:

| Factor | Weight | Description |
|---|---|---|
| Constraint Compliance | 0.30 | Hard/soft constraint satisfaction |
| Timing Fit | 0.25 | How well predicted ETA matches available window |
| Equipment Match | 0.15 | Crane/equipment compatibility with cargo type |
| Utilization Optimization | 0.15 | Impact on terminal throughput and berth usage |
| Waiting Time | 0.10 | Expected waiting time before berthing |
| Priority Score | 0.05 | Vessel priority alignment |

### 1.2 Constraint Checking Hierarchy
**Hard Constraints (must pass — any failure = berth disqualified):**
1. **LOA Check:** Vessel LOA ≤ Berth max LOA (with 10-15% safety margin recommended)
2. **Beam Check:** Vessel beam ≤ Berth max beam
3. **Draft Check:** Vessel draft ≤ Channel/berth depth minus required UKC
4. **Cargo Compatibility:** Vessel cargo type matches berth terminal type
5. **Hazmat Restriction:** Hazmat vessels only at designated hazmat berths
6. **Availability Check:** Berth not under maintenance/offline

**Soft Constraints (optimization trade-offs — scored but not disqualifying):**
1. **Crane Optimization:** Number of cranes matches cargo volume needs
2. **Preferred Terminal:** Shipping line's preferred terminal/operator
3. **Tidal Window:** Deep-draft vessels may need specific tidal windows
4. **Resource Proximity:** Distance of available pilots/tugs from berth
5. **Downstream Efficiency:** Impact on terminal throughput
6. **Night Operations:** Some berths have night operation restrictions

---

## 2. ETA-Driven Allocation (Enhanced)

### 2.1 Why Predicted ETA Over Scheduled ETA
SmartBerth uses ML-predicted ETA instead of the declared scheduled ETA because:
- Declared ETAs are typically 24-72 hours old and based on planned departure time
- ML-predicted ETAs incorporate real-time AIS data, weather, and traffic conditions
- Predicted ETAs are continuously updated as the vessel approaches
- Accuracy improvement: predicted ETA is typically within 30 minutes vs. 2-6 hour variance for declared ETA

### 2.2 ETA Confidence Impact on Allocation
| ETA Confidence | Buffer Added | Allocation Strategy |
|---|---|---|
| HIGH (>0.8) | 30 minutes | Firm berth assignment, tight scheduling |
| MEDIUM (0.5-0.8) | 60 minutes | Provisional assignment, backup berth identified |
| LOW (<0.5) | 120 minutes | Tentative assignment, multiple alternatives ready |

### 2.3 ETA Change Triggers
When predicted ETA changes significantly:
1. Re-evaluate current berth assignment feasibility
2. Check if change creates conflicts with adjacent vessels
3. If berth no longer optimal, generate new suggestions
4. Notify operator of recommendation change
5. Update downstream resource planning (pilots, tugs)

---

## 3. Resource Planning Integration

### 3.1 Resource Types and Allocation Rules
| Resource | Determination Factors | Lead Time | Constraint Type |
|---|---|---|---|
| **Pilot** | Vessel LOA, draft, channel conditions | 2-4 hours | Hard (pilotage compulsory) |
| **Tugs** | Vessel DWT, berth location, weather | 1-2 hours | Hard (count), Soft (type) |
| **Cranes** | Cargo type, volume, berth equipment | At berthing | Soft (optimization) |
| **Forklifts** | Cargo type (breakbulk/general) | At berthing | Soft |
| **Berth Gangs** | Cargo volume, shift schedule | At berthing | Soft |

### 3.2 Pilot Assignment Rules
- Pilotage compulsory for vessels >200m LOA in approach channel
- Night operations: only certified night-operation pilots
- Adverse weather: only adverse-weather-certified pilots
- Maximum continuous duty: 12 hours per pilot
- Handover time between assignments: minimum 30 minutes

### 3.3 Tug Assignment Rules
- Vessel >50,000 DWT: minimum 2 tugs
- Vessel >100,000 DWT: minimum 3 tugs
- Wind speed >20 knots: add 1 extra tug
- Deep-draft berths: require higher bollard pull tugs
- Combined bollard pull must exceed vessel displacement × safety factor

---

## 4. Berth Suggestion Reasoning (LLM Output)

### 4.1 Reasoning Structure
For each recommended berth, the LLM generates:
```json
{
  "reasoning": [
    {
      "factor": "Dimensional Compatibility",
      "weight": 0.30,
      "impact": "POSITIVE",
      "explanation": "Vessel LOA of 285m fits within Berth BMCT-01's max LOA of 320m with adequate safety margin."
    },
    {
      "factor": "ETA Timing",
      "weight": 0.25,
      "impact": "POSITIVE", 
      "explanation": "Predicted ETA of 14:30 aligns with berth availability window starting 14:00 with 30-minute buffer."
    },
    {
      "factor": "Equipment",
      "weight": 0.15,
      "impact": "NEUTRAL",
      "explanation": "4 STS gantry cranes available, adequate for 2,500 TEU container operation."
    }
  ],
  "confidence": "HIGH",
  "confidenceExplanation": "Confidence is HIGH because all hard constraints are satisfied, predicted ETA has 92% confidence, and the berth has no competing assignments within the next 24 hours.",
  "alternatives": [
    {
      "berthId": "BMCT-02",
      "rank": 2,
      "tradeoff": "Similar capabilities but 1 fewer crane, adding approximately 4 hours to cargo operations."
    }
  ]
}
```

### 4.2 Constraint Violation Messages
When constraints are violated, the LLM generates actionable messages:
- **Hard violation:** "Vessel draft of 14.5m exceeds Berth NSICT-01 maximum draft of 12.0m. The vessel cannot safely berth here. Alternative: BMCT-01 (max draft 16.0m) or NSIGT-01 (max draft 15.5m)."
- **Soft violation:** "Berth has 3 cranes but vessel cargo volume of 4,000 TEU ideally requires 5 cranes. Cargo operations will take approximately 6 hours longer. Consider GTI-02 with 5 cranes if timing permits."

---

## 5. OR-Tools Optimization (Advanced)

### 5.1 Optimization Model
The OR-Tools-based optimizer solves the Berth Allocation Problem (BAP):
- **Objective:** Minimize total weighted waiting time + maximize berth utilization
- **Variables:** berth assignment, arrival time, departure time for each vessel
- **Constraints:** Physical dimensions, no overlap, resource availability, tidal windows

### 5.2 Optimization Algorithms
| Algorithm | Type | Use Case | Speed |
|---|---|---|---|
| Greedy Heuristic | Rule-based | Quick initial assignment | < 1 second |
| Genetic Algorithm | Metaheuristic | Complex multi-vessel optimization | 5-30 seconds |
| CP-SAT Solver | Constraint Programming | Optimal solution for small instances | 10-60 seconds |
| OR-Tools BAP | Mixed Integer Programming | Production optimization | 30-120 seconds |

### 5.3 Optimization Objectives (Multi-Objective)
1. **Minimize Total Waiting Time:** Sum of hours each vessel waits at anchorage
2. **Maximize Berth Utilization:** Percentage of time berths are productively occupied
3. **Minimize Berth Swaps:** Number of vessels moved from initial assignment
4. **Minimize Resource Idle Time:** Gaps between pilot/tug assignments
5. **Maximize Priority Adherence:** High-priority vessels served first

---

## 6. Tidal Window Planning

### 6.1 Tidal Constraints for Deep-Draft Vessels
At JNPT, the tidal range is approximately 5 meters:
- High tide adds up to 2.5m above chart datum
- Vessels with draft exceeding channel depth at low tide must time their transit

### 6.2 Tidal Window Calculation
```
Available_Depth = Chart_Datum_Depth + Tide_Height
Required_Depth = Vessel_Draft + Required_UKC
Tidal_Window = periods where Available_Depth >= Required_Depth
```

### 6.3 Tidal Impact on Scheduling
- Deep-draft vessels may only transit the approach channel during specific tidal windows
- Windows typically 3-6 hours around high tide
- Missing a tidal window can delay berthing by 12+ hours (next tide cycle)
- LLM explains: "Vessel requires tidal window for safe channel transit. Next available window: 16:00-22:00 today. Missing this window would delay berthing to 04:00-10:00 tomorrow."

---

## 7. Berth Allocation Decision Tree

```
1. Receive vessel arrival notification
2. Extract vessel parameters (LOA, beam, draft, cargo type, DWT)
3. Get predicted ETA (with confidence level)
4. For each active berth:
   a. Check hard constraints (LOA, beam, draft, cargo) → PASS/FAIL
   b. Check tidal window (if applicable) → PASS/FAIL
   c. Check time availability → PASS/FAIL
   d. Score soft constraints (cranes, terminal preference, etc.)
   e. Calculate overall score
5. Rank suitable berths by score
6. Check for conflicts with existing assignments
7. Verify resource availability (pilots, tugs) for top berth
8. Generate LLM reasoning for top 3 suggestions
9. Present to operator / auto-assign based on confidence
```
