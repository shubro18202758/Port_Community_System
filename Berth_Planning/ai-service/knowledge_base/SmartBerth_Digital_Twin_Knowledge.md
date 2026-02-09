# SmartBerth AI - Digital Twin & Berth Overview Knowledge

**Document Version:** 2.0  
**Last Updated:** February 2026  
**Purpose:** Comprehensive domain knowledge for digital twin visualization, port simulation, and berth overview  
**Priority:** MEDIUM — Aggregation and visualization layer

---

## 1. Digital Twin Concept

### 1.1 Definition
The SmartBerth Digital Twin is a real-time virtual representation of the entire port, showing:
- Current state of every berth (occupied, vacant, reserved, maintenance, offline)
- Live vessel positions (from AIS tracking)
- Resource deployment (cranes, tugs, pilots)
- Active alerts overlaid spatially on the port map
- Schedule forecast and predicted future state

### 1.2 Data Sources
The Digital Twin aggregates data from all SmartBerth services:
| Data Type | Source Service | Update Frequency |
|---|---|---|
| Vessel Positions | Vessel Tracking Service | Every 10-30 seconds (AIS) |
| Berth Status | Berth Status Service | On change |
| Resource Deployment | Resource Service | On assignment change |
| Active Alerts | Alert Service | Real-time push |
| Schedule Changes | Re-Optimization Service | On change |
| Weather Conditions | Weather Service | Every 15-60 minutes |
| ETA Predictions | ETA Prediction Service | Every 60 seconds |

---

## 2. Visualization Modes

### 2.1 Real-Time View (Default)
- Shows live port state as it is right now
- Berths color-coded by status (green=vacant, blue=occupied, yellow=reserved, red=maintenance, gray=offline)
- Vessels displayed at current AIS positions with scale rendering (LOA/beam proportional)
- Active alerts shown as overlays at relevant locations
- Refresh: continuous (WebSocket-driven)

### 2.2 Historical Replay
- Play back port activity over a past time period
- Playback speed: 1x, 2x, 4x, 10x
- LLM narrates significant events as they occur in playback:
  - "At 14:30, Vessel MAERSK ELBA arrived at Berth BMCT-01 after 2 hours at anchorage due to berth unavailability"
- Useful for incident analysis, pattern recognition, training

### 2.3 Forecast View
- Projects future port state based on current schedule and predictions
- Shows predicted vessel arrivals, departures, and berth transitions
- Highlights potential conflicts (overlapping assignments, tight turnarounds)
- Confidence indicators on each prediction (HIGH/MEDIUM/LOW)
- Forecast horizon: configurable, typically 24-72 hours

### 2.4 What-If Simulation
- Interactive mode where operator can make hypothetical changes
- Compare baseline (current plan) vs. modified plan side-by-side
- LLM generates feasibility assessment and impact narration
- Changes don't affect real operations until explicitly applied
- Use cases: "What if Berth 3 goes offline for maintenance?", "What if 5 extra vessels arrive tomorrow?"

---

## 3. Berth State Model

### 3.1 Berth Status Values
| Status | Description | Visual | Transitions To |
|---|---|---|---|
| VACANT | No vessel assigned, available for allocation | Green | RESERVED, OCCUPIED, MAINTENANCE |
| RESERVED | Berth assigned to incoming vessel | Yellow | OCCUPIED, VACANT (cancellation) |
| OCCUPIED | Vessel currently moored at berth | Blue | VACANT (departure) |
| MAINTENANCE | Scheduled maintenance, not available | Red | VACANT (maintenance complete) |
| OFFLINE | Unexpected closure (damage, incident) | Gray | MAINTENANCE, VACANT |

### 3.2 Berth Data Model
Each berth in the digital twin includes:
- **Identification:** berthId, berthName, terminalId, terminalName
- **Physical Properties:** length (m), depth (m), maxDraft (m), maxLOA (m), maxBeam (m)
- **Position:** latitude, longitude, orientation (degrees)
- **Current Vessel:** vesselId, vesselName, cargoType, cargoProgress (0-100%), arrivalTime, estimatedDepartureTime
- **Next Vessel:** vesselId, vesselName, predictedArrival, etaConfidence
- **Resources:** assigned cranes (count, type), assigned tugs, assigned pilots
- **Status:** current status enum with last change timestamp

---

## 4. Terminal Overview Metrics

### 4.1 Terminal-Level Aggregation
For each terminal, the digital twin calculates:
- **Overall Occupancy:** percentage of berths currently occupied
- **Active Alerts:** count of unresolved alerts across all terminal berths
- **Throughput Rate:** vessels processed per 24 hours (rolling)
- **Average Dwell Time:** mean hours vessels spend at berth
- **Average Waiting Time:** mean hours vessels wait at anchorage

### 4.2 Terminal Capacity Thresholds
| Occupancy | Status | Alert |
|---|---|---|
| 0-60% | Normal | None |
| 60-80% | Busy | INFO |
| 80-95% | High Load | WARNING — may require pre-allocation |
| 95-100% | Near Full | CRITICAL — new arrivals must wait |

### 4.3 LLM Terminal Summary Generation
The LLM generates contextual terminal summaries:
```
"GTI Terminal is at 83% occupancy with 5 of 6 berths occupied. Average dwell time is 
18 hours. Two vessels are expected to depart within the next 4 hours, which will reduce 
occupancy to 50%. One pending alert: Berth GTI-03 has a crane maintenance scheduled 
for 08:00 tomorrow that will reduce unloading capacity."
```

---

## 5. Vessel Visualization

### 5.1 Vessel State in Digital Twin
Each vessel is rendered with:
- **Position:** latitude, longitude (from AIS)
- **Visual Properties:** length (LOA), beam (width), color (by vessel type)
- **Phase:** current approach phase (APPROACHING, NEAR_PORT, AT_BERTH, etc.)
- **Destination:** assigned berth with predicted arrival time
- **Trajectory:** 
  - Historical path (last 24 hours as trail line)
  - Predicted path (based on current course and speed)

### 5.2 Vessel Type Color Coding
| Vessel Type | Color | Icon |
|---|---|---|
| Container | Blue | Container ship silhouette |
| Tanker | Orange | Tanker silhouette |
| Bulk Carrier | Brown | Bulk carrier silhouette |
| LNG/LPG | Red | Gas carrier silhouette |
| Ro-Ro | Purple | Car carrier silhouette |
| Cruise | White | Cruise ship silhouette |
| General Cargo | Gray | Cargo ship silhouette |

---

## 6. Resource Overlay

### 6.1 Resource Visualization
The digital twin shows resource deployment:
- **Cranes:** Shown at berth locations, count and type
- **Tugs:** Shown at current position, assigned vessel
- **Pilots:** Shown at assigned vessel or pilot station
- **Status indicators:** Available (green), Assigned (blue), Unavailable (red)

### 6.2 Cargo Progress Tracking
For occupied berths:
- **Progress Bar:** 0-100% cargo operations complete
- **ETC (Estimated Time to Complete):** Based on cargo volume, crane capacity, and current rate
- **Phase:** Loading / Unloading / Waiting for next operation

---

## 7. Simulation Capabilities

### 7.1 What-If Simulation Process
1. Operator defines scenario (berth closure, vessel surge, weather event, etc.)
2. System snapshots current state as baseline
3. Applies hypothetical changes
4. Runs optimization engine on modified state
5. Renders both baseline and modified states side-by-side
6. LLM generates impact narration:
   - How many vessels affected
   - Total delay impact
   - Resource implications
   - Recommended mitigations

### 7.2 Playback Controls
- Play / Pause
- Speed: 1x, 2x, 4x, 10x
- Jump to timestamp
- Event markers on timeline (conflicts, arrivals, departures)

---

## 8. Port Layout Model

### 8.1 JNPT Port Layout
- **Approach Channel:** 14.5m depth, 250m width, one-way for large vessels
- **Pilot Boarding Area:** 18.95°N, 72.82°E (approximately 5 NM from port)
- **Anchorage Zone:** Multiple zones categorized by vessel type and cargo
- **Terminal Layout:**
  - Inner Harbor: NSFT (3 berths), NSICT (2 berths)
  - Central: GTI (2 berths), NSIGT (1 berth)
  - Outer: BMCT (6 berths, deep water)
  - Specialty: SWDT (2 berths, shallow draft), LCJ (2 berths, liquid cargo)

### 8.2 Geographic Coordinates for Rendering
| Feature | Latitude | Longitude | Description |
|---|---|---|---|
| Port Reference Point | 18.9453°N | 72.9400°E | JNPT main entrance |
| Pilot Station | 18.95°N | 72.82°E | Pilot boarding area |
| Anchorage Alpha | 18.90°N | 72.80°E | General anchorage |
| Channel Entrance | 18.93°N | 72.83°E | Approach channel start |
| BMCT Terminal | 18.95°N | 72.95°E | Deep water terminal |
| GTI Terminal | 18.94°N | 72.94°E | APM Terminals |

---

## 9. Synchronization & Performance

### 9.1 Update Strategy
- AIS positions: WebSocket push, every 10-30 seconds per vessel
- Berth status: Event-driven, pushed on change
- Alerts: Real-time push via WebSocket
- Schedule updates: Event-driven from re-optimization service
- Terminal metrics: Recalculated every 5 minutes

### 9.2 Desync Detection
If digital twin state diverges from actual operations:
- Trigger SIMULATION_DESYNC alert
- Auto-reconcile by re-fetching state from source services
- Log discrepancy for debugging

### 9.3 Turnaround Buffer
Between consecutive vessels at the same berth:
- Minimum buffer: 2 hours
- Includes: vessel departure maneuver, berth inspection, fender reset, next vessel approach
- Buffer shown as gap between vessel bars in Gantt chart
