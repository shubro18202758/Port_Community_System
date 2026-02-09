# SmartBerth AI - Conflict Detection & Resolution Knowledge

**Document Version:** 2.0  
**Last Updated:** February 2026  
**Purpose:** Comprehensive domain knowledge for conflict detection, resolution, and Chain-of-Thought reasoning  
**Priority:** HIGH — Critical for schedule integrity

---

## 1. Conflict Types

### 1.1 BERTH_OVERLAP
**Definition:** Two or more vessels assigned to the same berth with overlapping time windows.
- **Detection Rule:** Vessel A departure time > Vessel B arrival time at same berth
- **Turnaround Buffer:** Minimum 2-hour buffer required between consecutive vessels
- **Severity:** CRITICAL if time overlap > 30 minutes, HIGH if < 30 minutes

### 1.2 ETA_DEVIATION
**Definition:** Predicted ETA differs significantly from the scheduled berth window.
- **Thresholds:**
  - < 15 minutes: No action (within normal variance)
  - 15-30 minutes: INFO — Monitor closely
  - 30-60 minutes: WARNING — Consider schedule adjustment
  - 60-120 minutes: HIGH — Re-optimization recommended
  - > 120 minutes: CRITICAL — Immediate re-allocation required
- **Detection:** Continuous comparison of ML-predicted ETA vs. scheduled berth window

### 1.3 OVERSTAY
**Definition:** Vessel remains at berth beyond scheduled departure time.
- **Causes:** Cargo operations delay, weather hold, equipment breakdown, crew issues
- **Thresholds:**
  - 0-15 minutes: Normal tolerance
  - 15-30 minutes: WARNING — Notify downstream vessels
  - 30-60 minutes: HIGH — Trigger contingency planning
  - > 60 minutes: CRITICAL — Force re-optimization of all downstream schedules
- **Cascade Impact:** Each hour of overstay can delay 2-4 subsequent vessels

### 1.4 RESOURCE_CONFLICT
**Definition:** Same resource (pilot, tug, crane) assigned to multiple simultaneous operations.
- **Detection:** Time overlap check across all assignments for each resource
- **Severity:** HIGH for pilots/tugs (safety-critical), MEDIUM for cranes
- **Resolution:** Re-assign from available pool or delay lower-priority operation

### 1.5 CONSTRAINT_VIOLATION
**Definition:** Berth assignment violates physical or operational constraints.
- **Hard Constraints (never violate):**
  - Vessel LOA > Berth max LOA
  - Vessel draft > Berth/channel depth (considering UKC)
  - Vessel beam > Berth max beam
  - Incompatible cargo type
  - Hazmat vessel at non-hazmat berth
- **Soft Constraints (optimization trade-offs):**
  - Non-optimal crane allocation
  - Preferred terminal not available
  - Tidal window tight but feasible
- **Severity:** CRITICAL for hard violations, MEDIUM for soft violations

### 1.6 CASCADE_CONFLICT
**Definition:** A single disruption (delay, berth closure, resource failure) propagates through the schedule affecting multiple vessels.
- **Analysis Steps:**
  1. Identify root cause event
  2. Trace all directly affected berth assignments
  3. Identify indirectly affected (vessels waiting for now-delayed vessels' berths)
  4. Calculate total cascade delay in vessel-hours
  5. Quantify resource impacts
- **Severity:** Based on total vessels affected: 1-2 (MEDIUM), 3-5 (HIGH), >5 (CRITICAL)

---

## 2. Chain-of-Thought (CoT) Reasoning Framework

SmartBerth uses structured 4-step Chain-of-Thought reasoning for conflict analysis:

### Step 1: Conflict Identification
**Objective:** What exactly is the conflict?
- **Conflict Summary:** One-sentence description of the conflict
- **Entities Involved:** List all vessels, berths, resources affected
- **Timeline of Events:** Chronological sequence leading to conflict
- **Current State:** What is currently happening vs. what was planned

### Step 2: Root Cause Analysis
**Objective:** Why did this conflict occur?
- **Primary Cause:** The main trigger event (e.g., "Vessel X delayed by 3 hours due to weather")
- **Contributing Factors:** Additional factors that amplified the issue
- **Upstream Issues:** Were there preceding events that set the stage?
- **Reasoning:** Chain of logic from cause to effect

### Step 3: Resolution Option Generation
**Objective:** What are the possible solutions?
For each option, analyze:
- **Action Steps:** Specific steps required to implement
- **Estimated Impact:**
  - Time Impact: Total vessel-hours of delay
  - Cost Impact: Financial implications (berth charges, overtime, cargo penalties)
  - Risk Factor: Likelihood of creating new conflicts
- **Affected Vessels:** Which vessels are impacted by this resolution
- **Resources Required:** Additional pilots, tugs, cranes needed
- **Downstream Effects:** How this resolution affects the rest of the schedule

### Step 4: Recommendation with Reasoning
**Objective:** What should we do and why?
- **Recommended Option:** Selected resolution with justification
- **Justification:** Why this option is preferred over alternatives
- **Assumptions:** What conditions must remain true for success
- **Residual Risks:** What could still go wrong
- **Monitoring Advice:** What to watch for after implementing the resolution

---

## 3. Resolution Strategies

### 3.1 Berth Reassignment
- Move affected vessel to alternative compatible berth
- Check all constraints before reassignment
- Update all downstream resource bookings (pilots, tugs, cranes)
- Best when: alternative berth available with minimal impact

### 3.2 Time Shift
- Delay or advance the berth window for affected vessel
- Calculate cascade impact on subsequent vessels
- Best when: small delay with adequate schedule buffer

### 3.3 Priority Override
- Elevate priority of perishable/time-sensitive cargo
- May displace lower-priority vessels
- Requires explicit justification (e.g., reefer cargo, transshipment deadline)
- Best when: critical cargo at risk of loss

### 3.4 Resource Reallocation
- Reassign pilots/tugs/cranes from lower-priority operations
- Must verify certifications and equipment compatibility
- Best when: resource conflict, not berth conflict

### 3.5 Speed Adjustment Request
- Request vessel to increase/decrease speed to adjust ETA
- Fuel cost implications shared with shipping agent
- Only feasible for vessels > 12 hours from port
- Best when: ETA deviation can be corrected en route

---

## 4. Severity Escalation Rules

| Initial Severity | Time Without Resolution | Escalated Severity | Action |
|---|---|---|---|
| INFO | n/a | Stays INFO | Monitor only |
| WARNING | > 30 minutes | HIGH | Automatic re-optimization triggered |
| HIGH | > 60 minutes | CRITICAL | Supervisor notification, manual review |
| CRITICAL | > 120 minutes | CRITICAL+ | Port authority escalation |

---

## 5. Priority Rules for Conflict Resolution

### 5.1 Vessel Priority Hierarchy
1. **Safety-critical:** Vessels with crew medical emergency, distress, or hazmat incidents
2. **Government/Military:** Coast Guard, Navy, government official vessels
3. **Perishable Cargo:** Reefer containers, fresh produce, live animals
4. **Transshipment Connection:** Vessels with tight transshipment deadlines
5. **Schedule Liner:** Regular liner services with published schedules
6. **Hazmat Cargo:** Hazardous material requiring specialized berths
7. **High-value Cargo:** Automotive, electronics, pharmaceuticals
8. **Standard Cargo:** Regular container, bulk, and general cargo
9. **Repositioning:** Empty vessel repositioning, ballast voyages

### 5.2 Commercial Priority Factors
- Contract terms (guaranteed berth window penalties)
- Port charges and demurrage costs
- Cargo value and time-sensitivity
- Relationship tier (premium vs. standard customers)

---

## 6. Overstay Detection and Management

### 6.1 Causes of Overstay
| Cause | Frequency | Average Delay | Predictability |
|---|---|---|---|
| Cargo volume underestimated | 35% | 4-8 hours | Historical patterns help |
| Equipment breakdown (crane) | 20% | 2-12 hours | Maintenance schedules |
| Weather hold (wind/rain) | 15% | 4-24 hours | Weather forecast |
| Labor issues | 10% | 2-8 hours | Shift patterns |
| Documentation delays | 10% | 1-4 hours | Administrative patterns |
| Vessel technical issues | 5% | 6-48 hours | Unpredictable |
| Inter-modal delays | 5% | 2-6 hours | Rail/truck schedules |

### 6.2 Overstay Impact Calculation
```
Cascade Delay = Overstay Duration × Downstream_Vessel_Count × Impact_Factor
where Impact_Factor = 0.7 for same terminal, 0.3 for different terminal
```

---

## 7. What-If Scenario Analysis

### 7.1 Scenario Types
- **Vessel Delay:** What if Vessel X arrives N hours late?
- **Berth Closure:** What if Berth Y is unavailable for N hours?
- **Vessel Surge:** What if N additional vessels request berths?
- **Resource Outage:** What if crane Z breaks down?
- **Weather Event:** What if wind exceeds safe operating limits?

### 7.2 What-If Analysis Process
1. Snapshot current schedule state
2. Apply hypothetical change
3. Run constraint checker on modified schedule
4. Identify new conflicts
5. Run auto-resolution for each conflict
6. Compare before/after schedules
7. Calculate total impact (vessel-hours delay, cost, risk)
8. Generate LLM explanation of impact and recommendations
