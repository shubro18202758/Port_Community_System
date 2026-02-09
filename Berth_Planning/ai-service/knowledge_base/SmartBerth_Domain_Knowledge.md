# SmartBerth AI - Comprehensive Domain Knowledge Base

**Document Version:** 1.0  
**Last Updated:** February 2026  
**Purpose:** Consolidated knowledge for AI/RAG system reference

---

## 1. SYSTEM OVERVIEW

### 1.1 What is SmartBerth AI?
SmartBerth AI is an AI-powered berth planning and allocation optimization system designed for maritime ports, specifically targeting JNPT (Jawaharlal Nehru Port Trust) in Navi Mumbai, India.

### 1.2 Core Objectives
- **Predict vessel arrival times** using AIS data, weather, and historical patterns
- **Optimize berth allocation** to minimize waiting time and maximize throughput
- **Provide real-time re-optimization** when delays or disruptions occur
- **Generate natural language explanations** for all AI decisions (XAI)

### 1.3 Key Stakeholders
| Stakeholder | Role | System Interaction |
|-------------|------|-------------------|
| Shipping Agent | Declares vessel ETA, cargo, crew | PCS/MSW entry & status viewing |
| Terminal Operator | Manages berths & cargo operations | SmartBerth planning interface |
| Port Authority | Oversees port operations | PCS admin & resource allocation |
| Pilot Service | Vessel navigation | Pilot scheduling system |
| Tug Operator | Berthing assistance | Tug dispatch system |

---

## 2. PORT INFRASTRUCTURE - JNPT

### 2.1 Port Location
- **Port Code:** INNSA
- **Name:** Jawaharlal Nehru Port Trust
- **Location:** Navi Mumbai, India
- **Coordinates:** 18.9453°N, 72.9400°E
- **Timezone:** Asia/Kolkata (IST, UTC+5:30)

### 2.2 Terminals (7 Active)

| Terminal Code | Name | Operator | Type | Berths |
|---------------|------|----------|------|--------|
| INNSA-NSFT | Nhava Sheva Freeport Terminal | NSFT Pvt Ltd | Container | 3 |
| INNSA-NSICT | DP World - NSICT | DP World | Container | 2 |
| INNSA-NSIGT | DP World - NSIGT | DP World | Container | 1 (Deep Water) |
| INNSA-GTI | APM Terminals - GTI | APM/CONCOR | Container | 2 |
| INNSA-BMCT | PSA Mumbai - BMCT | PSA International | Container | 6 (Deep Water) |
| INNSA-SWDT | JM Baxi Shallow Water | JM Baxi & Co | General | 2 |
| INNSA-LCJ | JNPT Liquid Cargo Jetty | JNPT | Liquid | 2 |

### 2.3 Berth Specifications Summary

**Container Berths (14 total):**
- **NSFT Berths (3):** Max LOA 215m, Max Draft 13.0m, 3 cranes each
- **NSICT Berths (2):** Max LOA 280-285m, Max Draft 12.0m, 4 cranes each
- **NSIGT Deep Water (1):** Max LOA 320m, Max Draft 15.5m, 4 cranes
- **GTI Berths (2):** Max LOA 340m, Max Draft 13.1m, 5-6 cranes
- **BMCT Berths (6):** Max LOA 320m, Max Draft 16.0m, 4 cranes each

**General/Other Berths (4 total):**
- **Shallow Water Berth:** Max LOA 300m, Max Draft 9.0m
- **Coastal Distribution:** Max LOA 230m, Max Draft 6.5m
- **Liquid Cargo Jetties (2):** Max LOA 170-185m, Max Draft 10-11m

### 2.4 Navigation Channels

| Channel | Depth | Max LOA | Max Draft | Restrictions |
|---------|-------|---------|-----------|--------------|
| Main Approach | 15.0m | 400m | 15.0m | Night Restricted, Two-Way |
| Inner Harbour | 13.1m | 350m | 13.0m | None, Two-Way |
| BMCT Deep Water | 16.5m | 400m | 16.35m | Day Only, One-Way |
| Shallow Water | 10.0m | 300m | 9.0m | Night Restricted, Tidal Window |

### 2.5 Anchorages

| Anchorage | Type | Max Vessels | Max LOA | Max Draft | Avg Wait |
|-----------|------|-------------|---------|-----------|----------|
| Alpha | General | 15 | 400m | 14.0m | 3.5 hrs |
| Bravo | Deep Draft | 10 | 400m | 16.0m | 4.0 hrs |

---

## 3. CONSTRAINT FRAMEWORK

### 3.1 Hard Constraints (MUST NEVER VIOLATE)

| ID | Constraint | Rule | Priority |
|----|-----------|------|----------|
| HC-01 | Physical Fit - Length | `vessel.loa ≤ berth.max_loa` | CRITICAL |
| HC-02 | Physical Fit - Draft | `vessel.draft ≤ berth.max_draft` | CRITICAL |
| HC-03 | Physical Fit - Beam | `vessel.beam ≤ berth.max_beam` | CRITICAL |
| HC-04 | No Time Overlap | No two vessels at same berth at same time | CRITICAL |
| HC-05 | Berth Active | `berth.is_active = true` | CRITICAL |
| HC-06 | No Maintenance Conflict | Berth not under maintenance | CRITICAL |
| HC-07 | Tidal Window | Deep-draft vessels must use high tide | CRITICAL |
| HC-08 | Weather Safety | No operations during severe weather | CRITICAL |
| HC-09 | Resource Availability | Pilot and tugs must be available | CRITICAL |
| HC-10 | Cargo Type Match | Vessel type compatible with berth type | HIGH |

### 3.2 Soft Constraints (Optimization Objectives)

| ID | Constraint | Weight | Description |
|----|-----------|--------|-------------|
| SC-01 | Berth Type Match | 0.8 | Prefer matching cargo/berth types |
| SC-02 | Minimize Waiting Time | 0.9 | Reduce anchorage wait |
| SC-03 | Priority Respect | 0.7 | Higher priority vessels first |
| SC-04 | Crane Availability | 0.6 | Prefer berths with more cranes |
| SC-05 | Historical Performance | 0.5 | Use berths vessel has used before |
| SC-06 | Minimize Repositioning | 0.4 | Avoid unnecessary vessel moves |
| SC-07 | Even Distribution | 0.3 | Balance load across berths |
| SC-08 | Buffer Time | 0.5 | Maintain 30-min gap between vessels |

### 3.3 Dynamic Constraints

| ID | Constraint | Trigger |
|----|-----------|---------|
| DC-01 | Weather Restrictions | Wind > 40 km/h, visibility < 1km |
| DC-02 | Tidal Windows | High-draft vessels during high tide |
| DC-03 | Equipment Failure | Crane/fender breakdown |
| DC-04 | Pilot Shift Changes | Roster availability |
| DC-05 | Emergency Priority | Government/emergency vessels |

---

## 4. VESSEL CLASSIFICATION

### 4.1 Vessel Types in JNPT
- **Container Vessels:** 23 vessels (ranging from 1,620 to 24,346 TEU)
- **Bulk Carriers:** 3 vessels (coal, grain, iron ore)
- **Tankers:** 2 vessels (petroleum, chemicals)
- **General Cargo:** 2 vessels (break bulk, coastal)

### 4.2 Size Categories

| Category | LOA Range | Draft Range | TEU Capacity |
|----------|-----------|-------------|--------------|
| ULCV (Ultra Large) | 366-400m | 15.0-16.35m | 18,000-24,346 |
| Large Container | 334-367m | 14.0-15.0m | 8,500-14,400 |
| Medium Container | 261-335m | 12.5-14.5m | 3,500-9,600 |
| Small Container | 170-294m | 9.8-13.5m | 1,620-5,600 |
| Bulk/Tanker | 150-292m | 8.5-18.2m | N/A |

### 4.3 Priority Levels
- **Priority 1:** Strategic customers, large liners, transshipment hubs
- **Priority 2:** Regular customers, medium vessels
- **Priority 3:** Spot bookings, feeder vessels, coastal

---

## 5. DATA SOURCES & ML MODELS

### 5.1 Real-Time Data Sources

| Source | Update Frequency | Purpose |
|--------|------------------|---------|
| AIS Data | Every 5-15 min | Vessel position, speed, ETA |
| Weather Data | Hourly | Wind, visibility, precipitation |
| Tidal Data | 2x daily | High/low tide times and heights |
| Port Congestion | Real-time | Queue length, berth availability |

### 5.2 Training Datasets

| Dataset | Records | Primary Use |
|---------|---------|-------------|
| Port Parameters | 150 | Port identification |
| Terminal Parameters | 653 | Terminal matching |
| Berth Parameters | 2,848 | Berth allocation |
| Channel Parameters | 543 | UKC calculation |
| Vessel Parameters | 3,000 | Vessel identification |
| Weather Parameters | 52,500 | ETA adjustment |
| AIS Data | 125,349 | Real-time prediction |
| Vessel Call Data | 5,000 | Ground truth ML data |

### 5.3 ML Model Requirements

**ETA Prediction Model:**
- Inputs: AIS position, weather, vessel type, historical delays
- Output: Predicted ETA with confidence score
- Target Accuracy: ±10-15%

**Berth Allocation Model:**
- Inputs: Vessel dimensions, cargo type, berth availability
- Output: Ranked berth recommendations
- Constraint: 100% hard constraint compliance

**Dwell Time Prediction:**
- Inputs: Cargo volume, crane availability, weather
- Output: Expected time at berth (hours)

---

## 6. OPERATIONAL WORKFLOWS

### 6.1 Pre-Arrival Phase (72-24 hours before ETA)
1. Shipping agent submits vessel pre-arrival notification via PCS
2. FAL Forms submitted through MSW
3. Service requests (pilotage, tugs) submitted
4. SmartBerth AI begins initial berth allocation

### 6.2 Approach Phase (24-6 hours before ETA)
1. AIS data integration for real-time tracking
2. Weather and tidal data fetched
3. ETA continuously updated
4. Re-optimization if delays detected

### 6.3 Arrival Phase (6-0 hours)
1. Final ETA confirmation
2. Resource scheduling (pilots, tugs)
3. Berth readiness verification
4. Alert generation for conflicts

### 6.4 Berthing Phase
1. Pilot boarding recorded
2. First line time recorded
3. All fast time recorded
4. Cargo operations begin

### 6.5 Departure Phase
1. Cargo completion recorded
2. ATD recorded
3. Dwell time calculated
4. Data fed back for ML training

---

## 7. KEY PERFORMANCE INDICATORS (KPIs)

### 7.1 Operational KPIs
- **Average Waiting Time:** Target < 4 hours
- **Berth Utilization:** Target > 70%
- **Vessel Turnaround Time (TAT):** Target reduction 15-25%
- **Throughput:** Vessels per day, TEU per day

### 7.2 AI Model KPIs
- **ETA Prediction Accuracy:** ±10-15%
- **Conflict Detection Rate:** 100%
- **Optimization Runtime:** < 5 seconds
- **Re-optimization Response:** < 10 seconds
- **False Alert Rate:** < 20%

### 7.3 User Satisfaction KPIs
- **Explanation Latency:** < 2 seconds
- **Chatbot Response Time:** < 3 seconds
- **Dashboard Refresh Rate:** Real-time

---

## 8. UNDER KEEL CLEARANCE (UKC) CALCULATION

### 8.1 UKC Components
- **Static Draft:** Vessel draft at current loading
- **Dynamic Draft (Squat):** Additional draft due to vessel speed
- **Heel Allowance:** Draft increase due to vessel turn/heel
- **Wave Allowance:** Draft increase due to wave action
- **Tidal Height:** Water level above/below chart datum
- **Safety Margin:** Minimum clearance required

### 8.2 UKC Formula
```
Available Depth = Channel Depth + Tidal Height
Required Depth = Static Draft + Squat + Heel + Wave + Safety Margin
UKC = Available Depth - Required Depth
```

### 8.3 UKC Requirements by Vessel Type
- **Container Vessels:** Min 1.0m UKC
- **Tankers:** Min 1.5m UKC (due to cargo sensitivity)
- **Bulk Carriers:** Min 1.0m UKC

---

## 9. WEATHER IMPACT FACTORS

### 9.1 Wind Speed Thresholds
- **< 20 km/h:** Normal operations, minimal impact
- **20-30 km/h:** Reduced crane efficiency
- **30-40 km/h:** Caution advised, some restrictions
- **> 40 km/h:** Operations suspended

### 9.2 Visibility Thresholds
- **> 3 km:** Normal operations
- **1-3 km:** Reduced speed, caution
- **< 1 km:** Pilotage suspended

### 9.3 Wave Height Thresholds
- **< 1.0m:** Normal operations
- **1.0-2.0m:** Reduced mooring efficiency
- **> 2.0m:** Berthing operations suspended

---

## 10. CHATBOT QUERY PATTERNS

### 10.1 Vessel Queries
- "Which vessels are arriving in the next 12 hours?"
- "Tell me the status of Vessel [NAME]"
- "Why is Vessel [NAME] still waiting?"
- "What is the ETA for [VESSEL_NAME]?"

### 10.2 Berth Queries
- "Which vessel is at Berth [X] right now?"
- "When will Berth [X] be free?"
- "Which berths are available for a [SIZE] vessel?"

### 10.3 Explanation Queries
- "Why was Vessel [X] moved to Berth [Y]?"
- "Why did the ETA change?"
- "What is the impact if Vessel [X] is delayed by [N] hours?"

### 10.4 Analytics Queries
- "Show vessel demand for the next 48 hours"
- "Traffic load by berth"
- "Is the ETA model performing well?"

---

## 11. ERROR HANDLING & FALLBACKS

### 11.1 Data Unavailability
- **AIS Data Missing:** Use declared ETA with reduced confidence
- **Weather Data Missing:** Use historical averages
- **Tidal Data Missing:** Use astronomical predictions

### 11.2 Constraint Violations
- **No Feasible Berth:** Queue vessel at anchorage, alert operator
- **Resource Unavailable:** Suggest alternative time slots
- **Weather Restriction:** Calculate next safe window

### 11.3 System Failures
- **LLM API Unavailable:** Fall back to rule-based decisions
- **Database Connection Lost:** Use cached data with staleness warning
- **Optimization Timeout:** Use greedy heuristics

---

## 12. GLOSSARY

| Term | Definition |
|------|------------|
| AIS | Automatic Identification System - vessel tracking |
| ATB | Actual Time of Berthing |
| ATA | Actual Time of Arrival |
| ATD | Actual Time of Departure |
| ETA | Estimated Time of Arrival |
| ETD | Estimated Time of Departure |
| FAL | Facilitation of International Maritime Traffic (IMO forms) |
| GT | Gross Tonnage |
| LOA | Length Overall - total length of vessel |
| MSW | Maritime Single Window |
| PCS | Port Community System |
| RAG | Retrieval Augmented Generation |
| TAT | Turnaround Time |
| TEU | Twenty-foot Equivalent Unit (container measure) |
| TOS | Terminal Operating System |
| UKC | Under Keel Clearance |
| ULCV | Ultra Large Container Vessel |
| VTS | Vessel Traffic Service |

---

*End of Domain Knowledge Document*
