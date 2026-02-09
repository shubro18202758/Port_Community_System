# Use Case 2: Vessel Tracking

## Overview

Real-time vessel tracking powered by AIS data, with AI-driven movement analysis, anomaly detection, and port approach narration.

> **⚡ Key Role:** Vessel Tracking is the **foundational data service** that feeds the Vessel Arrival Prediction system. Without real-time tracking data, ETA predictions degrade to static schedule-based estimates.

## Service Dependency Chain

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        Vessel Tracking Service                             │
│                        (AIS Data Foundation)                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│   ┌─────────────────┐                                                      │
│   │  AIS Receiver   │──┐                                                   │
│   └─────────────────┘  │                                                   │
│                        ▼                                                   │
│   ┌──────────────────────────────────────────────────────────────────┐    │
│   │                    Position Processing Engine                     │    │
│   │  • Decode AIS messages                                           │    │
│   │  • Validate positions                                            │    │
│   │  • Store position history                                        │    │
│   │  • Calculate derived metrics (speed trends, distance-to-port)    │    │
│   └──────────────────────────────────────────────────────────────────┘    │
│                        │                                                   │
│         ┌──────────────┼──────────────┬─────────────────┐                 │
│         ▼              ▼              ▼                 ▼                 │
│   ┌───────────┐  ┌───────────┐  ┌───────────┐   ┌────────────────┐       │
│   │ ETA       │  │ Anomaly   │  │ Digital   │   │ Real-Time      │       │
│   │ Prediction│  │ Detection │  │ Twin      │   │ Alerts         │       │
│   └───────────┘  └───────────┘  └───────────┘   └────────────────┘       │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Current Status

| Data Point | Status | API Endpoint | LLM Required | Downstream Consumer |
|---|---|---|---|---|
| AIS Position Data | ⚠️ Scaffolded | `/tracking/vessels/positions` | No (raw data) | All services |
| Position History | ⚠️ Scaffolded | `/tracking/vessels/{vesselId}/history` | No (raw data) | ETA Prediction |
| Speed/Course Metrics | ⚠️ Scaffolded | `/tracking/vessels/{vesselId}/metrics` | Yes — trend analysis | ETA Prediction |
| Movement Anomaly Detection | ❌ Not Implemented | — | Yes — explanation | Alerts, Digital Twin |
| Port Approach Status | ❌ Not Implemented | — | Yes — narration | Digital Twin |
| Anchorage Queue Position | ⚠️ Partial (UI only) | — | Yes — wait time | Berth Allocation |
| Distance to Port | ⚠️ Scaffolded | Derived from position | No | ETA Prediction |
| Phase Detection | ❌ Not Implemented | — | Yes — status | All services |

## Data Structure

```typescript
interface VesselTrackingData {
  vesselId: number;
  imoNumber: string;
  mmsi: string;
  vesselName: string;
  position: {
    latitude: number;
    longitude: number;
    timestamp: string;
    accuracy: 'HIGH' | 'MEDIUM' | 'LOW';
  };
  dynamics: {
    speedOverGround: number;  // knots
    courseOverGround: number;  // degrees
    heading: number;  // degrees
    rateOfTurn: number;  // degrees/min
  };
  derived: {
    distanceToPort: number;  // nautical miles
    estimatedTimeToPort: number;  // minutes (simple distance/speed)
    phase: VesselPhase;
    speedTrend: 'INCREASING' | 'STABLE' | 'DECREASING';
    courseDeviation: number;  // degrees from expected route
  };
  navigationStatus: NavigationStatusCode;
  lastUpdated: string;
}

type VesselPhase = 
  | 'APPROACHING'      // > 50 nm from port
  | 'NEAR_PORT'        // 10-50 nm
  | 'PILOT_BOARDING'   // < 10 nm, approaching pilot station
  | 'ANCHORED'         // At anchorage
  | 'MANEUVERING'      // In channel or turning basin
  | 'BERTHING'         // Final approach to berth
  | 'AT_BERTH'         // Stationary at berth
  | 'UNBERTHING'       // Departing berth
  | 'DEPARTING';       // Outbound

type NavigationStatusCode = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 15;
// 0=Under way using engine, 1=At anchor, 2=Not under command, etc.
```

## LLM Integration Points

### What the LLM Should Do

1. **Movement Anomaly Detection & Explanation** — Analyze AIS position streams and flag unexpected behavior with natural-language explanation:
   > "MV Northern Star has reduced speed from 12 kn to 3 kn at position 22.74°N, 69.62°E and is now circling. This pattern suggests the vessel may be experiencing mechanical issues or awaiting instructions. No scheduled anchorage stop at this location."

2. **Speed/Course Deviation Explanation** — When a vessel deviates from its expected speed or heading:
   > "MV Pacific Trader's course has deviated 25° to starboard from the expected approach track. This may be a collision avoidance maneuver — AIS shows another vessel (MV Ocean Fortune) on a converging course 2 nm ahead."

3. **Port Approach Narration** — Provide real-time status narrative as vessels approach:
   > "MV Cargo Express is now 8 nm from the pilot boarding station, maintaining 11 kn on a steady approach course of 045°. At current speed, pilot boarding in approximately 44 minutes. Vessel is #3 in the pilot queue."

4. **Anchorage Wait Time Estimation** — Estimate wait time with explanation:
   > "MV Baltic Star is anchored at position ANC-MUN-01 (Outer Anchorage), queue position #7. Based on current berth availability (2 suitable berths, average turnaround 18 hours) and vessels ahead in queue, estimated wait time is 14-18 hours. This estimate assumes no priority escalations."

5. **Phase Transition Narration** — Explain vessel phase changes:
   > "MV Express Voyager has transitioned from ANCHORED to MANEUVERING. Pilot has boarded (confirmed via AIS status change to '3 - Restricted Maneuverability'). Vessel is now proceeding to Berth CT3-CB1 via the Inner Harbour Channel."

## Data Flow to ETA Prediction

| Tracking Data | ETA Model Input | Update Frequency |
|---|---|---|
| `position.latitude`, `position.longitude` | Distance-to-port calculation | Every AIS message (~10-30s) |
| `dynamics.speedOverGround` | Current speed for time calculation | Every AIS message |
| `derived.speedTrend` | Speed trajectory extrapolation | Computed every 5 min |
| `derived.phase` | Phase-specific speed assumptions | On phase transition |
| `derived.courseDeviation` | Route deviation penalty factor | Every AIS message |
| `navigationStatus` | Phase detection, anomaly flags | Every AIS message |

## Real-Time Alerts Integration

| Alert Type | Trigger Condition | Severity | Downstream Impact |
|---|---|---|---|
| `POSITION_STALE` | No AIS update for > 30 min | WARNING | ETA confidence drops |
| `SPEED_ANOMALY` | Speed change > 5 kn in 10 min | INFO | ETA recalculation |
| `COURSE_DEVIATION` | Course deviation > 30° | WARNING | Route anomaly flag |
| `UNEXPECTED_STOP` | Speed drops to < 1 kn outside anchorage | WARNING | Investigate cause |
| `PHASE_TRANSITION` | Vessel enters new phase | INFO | Update Digital Twin |
| `ANCHORAGE_ENTRY` | Vessel enters anchorage zone | INFO | Update queue position |
| `PILOT_BOARDING` | Status changes to 'Restricted Maneuvering' | INFO | Update ETA to berth |

## Backend Integration

- **Service:** `VesselTrackingService` (to be fully exposed)
- **Data Source:** AIS receiver / AIS API provider
- **Endpoints (proposed):**
  - `GET /tracking/vessels/positions` — All active vessel positions
  - `GET /tracking/vessels/{vesselId}/position` — Single vessel position
  - `GET /tracking/vessels/{vesselId}/history?hours=24` — Position history
  - `GET /tracking/vessels/{vesselId}/metrics` — Derived metrics (speed trend, distance, phase)
  - `WS /tracking/vessels/stream` — WebSocket for real-time updates
- **Refresh Interval:** Real-time (WebSocket) or 30-second polling

## Recommended Priority

**Priority 1 — CRITICAL.** Vessel Tracking is the foundation service. Without real-time AIS data exposure:
- ETA Prediction degrades to schedule-based estimates
- Anomaly detection is impossible
- Digital Twin cannot show real-time vessel positions
- Arrival Prediction confidence drops significantly
