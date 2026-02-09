# Use Case 7: Berth Overview & Digital Twin

## Overview

Interactive visualization of all terminal berths with real-time status, vessel positions, and **port-like simulation in a Digital Twin environment**. The Digital Twin provides a unified operational view that integrates data from all SmartBerth AI services.

> **⚡ Key Capability:** The Berth Overview provides a **Digital Twin simulation** of the entire port, showing real-time berth occupancy, vessel movements, resource positions, and predicted future states — all in a single, interactive visualization.

## Digital Twin Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Digital Twin / Berth Overview                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   DATA AGGREGATION LAYER                                                    │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│   │ Vessel      │ │ Berth       │ │ Resource    │ │ Schedule    │          │
│   │ Tracking    │ │ Status      │ │ Positions   │ │ Data        │          │
│   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘          │
│          │               │               │               │                  │
│          └───────────────┴───────────────┴───────────────┘                  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    DIGITAL TWIN STATE ENGINE                         │  │
│   │                                                                      │  │
│   │   • Maintain real-time state of all port entities                   │  │
│   │   • Interpolate positions between AIS updates                       │  │
│   │   • Project future states based on current trajectories             │  │
│   │   • Sync with optimization engine for "what-if" visualization       │  │
│   │   • Generate simulation playback for planning scenarios             │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   VISUALIZATION LAYER                                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                                                                      │  │
│   │   ┌─────────────────────────────────────────────────────────────┐   │  │
│   │   │                    PORT MAP VIEW                             │   │  │
│   │   │                                                              │   │  │
│   │   │   [Berth CT1-CB1]  [Berth CT1-CB2]  [Berth CT2-CB1]        │   │  │
│   │   │   ████████████████  ░░░░░░░░░░░░░░░░  ████████████████       │   │  │
│   │   │   MV Pacific Star   (VACANT)          MV Ocean Fortune       │   │  │
│   │   │   ETA: 16:45        Available: Now    ETD: 17:30            │   │  │
│   │   │                                                              │   │  │
│   │   │   [Berth CT3-CB1]  [Berth CT3-CB2]  [Berth CT3-CB3]        │   │  │
│   │   │   ████████████████  ████████████████  ░░░░░░░░░░░░░░░░       │   │  │
│   │   │   MV Baltic Trader  MV Cargo Express  (MAINTENANCE)          │   │  │
│   │   │   ETD: 18:00        ETD: 19:30        Until: 20:00          │   │  │
│   │   │                                                              │   │  │
│   │   │   ─────────────── APPROACH CHANNEL ───────────────          │   │  │
│   │   │          🚢 MV Northern Star (Inbound, ETA 17:15)           │   │  │
│   │   │                                                              │   │  │
│   │   │   ═══════════════ ANCHORAGE AREA ═══════════════            │   │  │
│   │   │   ⚓ MV Express (Queue #1)  ⚓ MV Horizon (Queue #2)        │   │  │
│   │   │                                                              │   │  │
│   │   └─────────────────────────────────────────────────────────────┘   │  │
│   │                                                                      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Current Status

| Feature | Status | Data Source | LLM Required |
|---|---|---|---|
| Berth Grid View | ⚠️ Partial | Schedule data | No |
| Real-Time Vessel Positions | ❌ Not Implemented | Vessel Tracking | No |
| Berth Occupancy Status | ⚠️ Partial | Schedule data | No |
| Resource Positions (Cranes, Tugs) | ❌ Not Implemented | Resource service | No |
| Interactive Tooltips | ⚠️ Partial | Multiple sources | Yes — contextual info |
| Time Slider (Past/Future) | ❌ Not Implemented | Historical + Predictions | No |
| What-If Overlay | ❌ Not Implemented | WhatIfService | Yes — impact visualization |
| Vessel Trajectory Animation | ❌ Not Implemented | Vessel Tracking | No |
| Alert Overlay | ❌ Not Implemented | Alert Service | Yes — alert context |
| Port Simulation Mode | ❌ Not Implemented | All services | Yes — narration |

## Data Structure

```typescript
interface DigitalTwinState {
  timestamp: string;
  viewMode: 'REALTIME' | 'HISTORICAL' | 'SIMULATION' | 'WHATIF';
  terminals: TerminalState[];
  channels: ChannelState[];
  anchorages: AnchorageState[];
  vessels: VesselState[];
  resources: ResourceState[];
  alerts: ActiveAlert[];
  simulationContext?: SimulationContext;
}

interface TerminalState {
  terminalId: string;
  terminalName: string;
  berths: BerthState[];
  overallOccupancy: number;  // 0-100%
  activeAlerts: number;
}

interface BerthState {
  berthId: string;
  berthName: string;
  status: 'VACANT' | 'OCCUPIED' | 'RESERVED' | 'MAINTENANCE' | 'OFFLINE';
  currentVessel?: {
    vesselId: number;
    vesselName: string;
    berthingTime: string;
    scheduledETD: string;
    predictedETD: string;
    cargoProgress: number;  // 0-100%
    alerts: string[];
  };
  nextVessel?: {
    vesselId: number;
    vesselName: string;
    predictedETA: string;
    etaConfidence: 'HIGH' | 'MEDIUM' | 'LOW';
  };
  assignedResources: {
    cranes: string[];
    tugs: string[];
    pilots: string[];
  };
  physicalProperties: {
    length: number;
    depth: number;
    maxDraft: number;
    maxLOA: number;
  };
  position: {
    latitude: number;
    longitude: number;
    orientation: number;  // degrees
  };
}

interface VesselState {
  vesselId: number;
  vesselName: string;
  imoNumber: string;
  position: {
    latitude: number;
    longitude: number;
    heading: number;
    speed: number;
  };
  phase: VesselPhase;
  destination?: {
    berthId: string;
    berthName: string;
    predictedArrival: string;
  };
  visualProperties: {
    length: number;  // for rendering to scale
    beam: number;
    color: string;   // based on vessel type or status
  };
  trajectory?: {
    historicalPositions: Position[];  // last 1 hour
    predictedPath: Position[];        // next 2 hours
  };
}

interface SimulationContext {
  simulationType: 'REPLAY' | 'FORECAST' | 'WHATIF';
  startTime: string;
  endTime: string;
  playbackSpeed: number;  // 1x, 2x, 4x, etc.
  whatIfChanges?: ScheduleChange[];
  narration?: {
    enabled: boolean;
    currentNarration: string;  // ← LLM-generated
    upcomingEvents: NarratedEvent[];
  };
}

interface NarratedEvent {
  timestamp: string;
  eventType: string;
  narration: string;  // ← LLM-generated natural language
  entities: string[];
}
```

## Visualization Modes

### 1. Real-Time View (Default)
Live view of the port showing current berth occupancy, vessel positions, and active alerts.

**LLM Integration:**
- Contextual tooltips with natural language summaries
- Alert explanations overlaid on affected berths/vessels

### 2. Historical Replay
Playback of past port operations for review and analysis.

**LLM Integration:**
- Narration of significant events as they occur in playback
- Post-event analysis summaries

### 3. Forecast View
Projected future state based on current schedules and predictions.

**LLM Integration:**
- Explanation of projected conflicts
- Confidence indicators with justification

### 4. What-If Simulation
Interactive simulation of proposed schedule changes.

**LLM Integration:**
- Real-time narration of change impacts
- Comparison with baseline scenario

## LLM Integration Points

### What the LLM Should Do

1. **Berth Status Narration** — Generate contextual summaries for each berth:
   > "**Berth CT3-CB1 Status**
   > 
   > Currently occupied by MV Pacific Star (arrived 14:30, now completing container discharge).
   > - Cargo progress: 78% complete (estimated finish: 17:45)
   > - Scheduled ETD: 18:30
   > - Cranes: QC-07, QC-08 (both operational)
   > 
   > Next vessel: MV Baltic Trader (ETA 19:00, HIGH confidence)
   > - Turnaround buffer: 30 minutes (adequate)"

2. **Terminal Overview Summary** — Aggregate terminal status:
   > "**Container Terminal 3 Overview**
   > 
   > Occupancy: 2/3 berths (67%)
   > - CT3-CB1: Occupied (MV Pacific Star, ETD 18:30)
   > - CT3-CB2: Occupied (MV Cargo Express, ETD 19:30)
   > - CT3-CB3: Maintenance until 20:00
   > 
   > Incoming vessels (next 4 hours): 2
   > Active alerts: 1 (ETD warning on MV Pacific Star)
   > 
   > Capacity assessment: Terminal will reach 100% operational occupancy by 19:00. Consider expediting MV Pacific Star departure or diverting MV Baltic Trader to CT4."

3. **Vessel Approach Narration** — Track vessels in real-time:
   > "MV Northern Star is currently 8 nm from the pilot boarding station, maintaining 11 knots on course 045°. Pilot vessel dispatched and will intercept in approximately 25 minutes. The vessel is on track for its predicted arrival at Berth CT2-CB1 at 17:15."

4. **Simulation Narration** — Explain what-if scenarios:
   > "**What-If Analysis: Move MV Pacific Star ETD from 18:30 to 17:30**
   > 
   > If MV Pacific Star departs 1 hour early:
   > - ✅ CT3-CB1 becomes available at 17:30 instead of 18:30
   > - ✅ MV Baltic Trader can berth at 17:45 instead of 19:00 (1h 15min improvement)
   > - ⚠️ Requires expediting cargo discharge (currently at 78%, target 100% by 17:15)
   > - ⚠️ Tug availability: TUG-05 and TUG-07 would need reassignment from CT4 operations
   > 
   > Feasibility: MEDIUM — cargo expedition is possible but tight. Recommend confirming with terminal operations before committing."

5. **Alert Overlay Context** — Explain alerts in spatial context:
   > "🔴 Alert on Berth CT3-CB1: MV Pacific Star is approaching scheduled ETD with cargo operations still in progress. If current discharge rate continues, the vessel will overstay by approximately 45 minutes, impacting the arrival of MV Baltic Trader."

## Real-Time Alerts Integration

The Digital Twin serves as the **primary visualization surface for alerts**:

| Alert Display | Behavior |
|---|---|
| Berth-level alerts | Berth boundary flashes, color indicates severity |
| Vessel-level alerts | Vessel icon pulses, tooltip shows alert details |
| Channel alerts | Channel segment highlighted with warning color |
| Terminal alerts | Terminal header shows alert count and severity |
| Port-wide alerts | Full-screen overlay for CRITICAL alerts |

## Backend Integration

- **Service:** `DigitalTwinService` (to be implemented)
- **Data Sources:**
  - `VesselTrackingService` — Real-time vessel positions
  - `BerthStatusService` — Berth occupancy and reservations
  - `ResourceService` — Crane, tug, pilot positions
  - `AlertService` — Active alerts for overlay
  - `ReoptimizationService` — Schedule data
  - `WhatIfService` — Simulation capabilities
- **Endpoints (proposed):**
  - `GET /digitaltwin/state` — Get current port state
  - `GET /digitaltwin/state?timestamp={iso}` — Get historical state
  - `GET /digitaltwin/forecast?hours={n}` — Get projected future state
  - `POST /digitaltwin/whatif` — Run what-if simulation
  - `WS /digitaltwin/stream` — WebSocket for real-time state updates
- **Refresh Rate:** 
  - Vessel positions: Every AIS update (~10-30 seconds)
  - Berth status: On change
  - Alerts: Real-time push

## Recommended Priority

**Priority 6** — Medium effort. The Digital Twin is the **operational command center** that ties all other services together. It depends on:
1. Vessel Tracking (Priority 1) for real-time positions
2. Alert Service (Priority 2) for alert overlay
3. All other services for complete state representation

The Digital Twin transforms raw data into situational awareness, making it essential for effective terminal operations.
