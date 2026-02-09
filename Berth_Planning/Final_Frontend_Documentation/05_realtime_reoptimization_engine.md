# Use Case 5: Real-Time Re-Optimization Engine

## Overview

Dynamic schedule re-optimization that automatically adjusts berth assignments, resource allocation, and priorities in response to real-time events, with AI-generated explanations of every change.

> **⚡ Key Integration:** The Re-Optimization Engine is the **central orchestrator** that responds to changes from all upstream services. Every ETA update, conflict detection, and resource change triggers potential re-optimization, with real-time alerts for all actions.

## System Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Real-Time Re-Optimization Engine                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   INPUTS (Trigger Sources)                                                  │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │ Vessel Tracking │  │ ETA Predictions │  │ Conflict        │            │
│   │ (Position Δ)    │  │ (ETA Δ)         │  │ Detection       │            │
│   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│            │                    │                    │                      │
│            └────────────────────┼────────────────────┘                      │
│                                 ▼                                           │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    RE-OPTIMIZATION DECISION ENGINE                   │  │
│   │                                                                      │  │
│   │   1. Evaluate trigger significance                                   │  │
│   │   2. Assess current schedule stability                               │  │
│   │   3. Generate optimization candidates                                │  │
│   │   4. Score candidates (minimize disruption, maximize throughput)     │  │
│   │   5. Select optimal adjustment                                       │  │
│   │   6. Generate LLM explanation                                        │  │
│   │   7. Execute change + emit alerts                                    │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                 │                                           │
│                                 ▼                                           │
│   OUTPUTS                                                                   │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│   │ Updated         │  │ Real-Time       │  │ Digital Twin    │            │
│   │ Schedule        │  │ Alerts          │  │ Visualization   │            │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Current Status

| Data Point | Status | API Endpoint | LLM Required | Alert Integration |
|---|---|---|---|---|
| Schedule Re-optimization | ❌ Not Exposed | `ReoptimizationService` | Yes — change explanation | Yes |
| Cascade Impact Analysis | ❌ Not Exposed | `ReoptimizationService` | Yes — affected vessels | Yes |
| Priority Adjustment | ❌ Not Exposed | — | Yes — justification | Yes |
| Resource Reallocation | ❌ Not Exposed | `ResourceOptimizationService` | Yes — reasoning | Yes |
| Gantt Drag-Drop Validation | ⚠️ Frontend-only | — | Yes — constraint check | Yes |
| What-If Simulation | ❌ Not Exposed | `WhatIfService` | Yes — impact narration | Yes |
| Auto-Adjustment Mode | ❌ Not Implemented | — | Yes — mode explanation | Yes |

## Data Structure

```typescript
interface ReoptimizationEvent {
  eventId: string;
  triggerType: TriggerType;
  triggerSource: string;
  timestamp: string;
  beforeState: ScheduleSnapshot;
  afterState: ScheduleSnapshot;
  changes: ScheduleChange[];
  explanation: LLMExplanation;
  alerts: Alert[];
  cascadeImpact: CascadeImpact;
}

type TriggerType = 
  | 'ETA_CHANGE'           // Vessel arrival prediction changed
  | 'CONFLICT_DETECTED'    // New conflict from ConflictDetectionService
  | 'RESOURCE_UNAVAILABLE' // Crane/tug/pilot became unavailable
  | 'VESSEL_DELAY'         // Vessel reports delay
  | 'WEATHER_CHANGE'       // Weather impacts operations
  | 'PRIORITY_OVERRIDE'    // Manual priority change by operator
  | 'BERTH_UNAVAILABLE'    // Berth taken offline (maintenance, damage)
  | 'MANUAL_ADJUSTMENT';   // Operator drags vessel on Gantt

interface ScheduleChange {
  changeType: 'BERTH_REASSIGN' | 'TIME_SHIFT' | 'PRIORITY_CHANGE' | 'RESOURCE_REALLOC';
  vesselId: number;
  vesselName: string;
  before: any;
  after: any;
  reason: string;
}

interface LLMExplanation {
  summary: string;            // One-line summary
  detailedExplanation: string; // Full explanation
  affectedParties: string[];  // Who needs to know
  actionRequired: boolean;    // Does operator need to act?
  confidenceLevel: 'HIGH' | 'MEDIUM' | 'LOW';
}

interface CascadeImpact {
  directlyAffectedVessels: string[];
  indirectlyAffectedVessels: string[];
  totalDelayMinutes: number;
  resourcesAffected: string[];
  alertsGenerated: number;
}

interface Alert {
  alertId: string;
  alertType: AlertType;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  title: string;
  message: string;          // ← LLM-generated natural language
  timestamp: string;
  relatedEntities: string[];
  actionRequired: boolean;
  dismissible: boolean;
}
```

## LLM Integration Points

### What the LLM Should Do

1. **Change Explanation** — Generate clear summaries:
   > "**Schedule Adjustment (15:42)**
   > 
   > MV Pacific Star's berth assignment has been changed from CT3-CB1 (16:00) to CT4-CB1 (16:15).
   > 
   > **Reason**: MV Ocean Fortune at CT3-CB1 is running 45 minutes behind schedule due to crane QC-05 maintenance delay. Rather than holding MV Pacific Star at anchorage, the system reassigned to CT4-CB1 which became available 15 minutes earlier than scheduled.
   > 
   > **Impact**: No delay to MV Pacific Star. CT4-CB1's original vessel (MV Baltic Trader) was already rescheduled due to its own ETA delay."

2. **Cascade Impact Narration**:
   > "**Cascade Impact Analysis**
   > 
   > The delay of MV Ocean Fortune has triggered 3 downstream adjustments:
   > 
   > | Vessel | Original Plan | New Plan | Impact |
   > |---|---|---|---|
   > | MV Pacific Star | CT3-CB1 @ 16:00 | CT4-CB1 @ 16:15 | +15 min (berth change) |
   > | MV Baltic Trader | CT4-CB1 @ 15:00 | CT4-CB2 @ 15:30 | +30 min (both berth and time change) |
   > | MV Cargo Express | CT4-CB2 @ 16:00 | No change | Unaffected |
   > 
   > **Total cascade impact**: 2 vessels affected, 45 vessel-minutes of delay."

3. **Priority Adjustment Justification**:
   > "MV Cargo Express has been elevated from Priority 3 to Priority 1.
   > 
   > **Justification**:
   > - Cargo type: Perishable goods (refrigerated containers)
   > - Current status: At anchorage for 8 hours (approaching spoilage risk threshold)
   > - Next port connection: Tight window for transshipment at Singapore
   > 
   > **Trade-off**: This priority change delays MV Northern Star by 2 hours, but MV Northern Star is carrying non-perishable bulk cargo with flexible delivery windows."

4. **Gantt Drag-Drop Validation**:
   > "**Validation Result: NOT RECOMMENDED**
   > 
   > You attempted to move MV Pacific Star to Berth T1-MB3 at 17:00.
   > 
   > **Conflicts detected**:
   > 1. ❌ Vessel LOA (365m) exceeds berth maximum (280m)
   > 2. ⚠️ Berth T1-MB3 is a multipurpose berth, not optimized for container operations
   > 3. ⚠️ This would leave CT3-CB1 idle for 3 hours until the next scheduled vessel
   > 
   > **Suggested alternative**: Keep MV Pacific Star at CT3-CB1 but shift time to 17:15, or reassign to CT4-CB2 which becomes available at 16:45."

## Real-Time Alerts Integration

Every re-optimization action generates alerts:

| Alert Type | Trigger | Severity | Auto-Dismiss |
|---|---|---|---|
| `SCHEDULE_OPTIMIZED` | Automatic re-optimization completed | INFO | Yes (30 min) |
| `BERTH_REASSIGNED` | Vessel moved to different berth | WARNING | No |
| `TIME_SHIFTED` | Vessel berthing time changed > 30 min | WARNING | No |
| `PRIORITY_CHANGED` | Vessel priority adjusted | INFO | Yes (1 hour) |
| `RESOURCE_REALLOCATED` | Crane/tug/pilot reassigned | INFO | Yes (30 min) |
| `CASCADE_ALERT` | Change affects 3+ downstream vessels | HIGH | No |
| `MANUAL_OVERRIDE_CONFLICT` | Operator change creates conflict | CRITICAL | No |
| `OPTIMIZATION_BLOCKED` | System cannot find valid solution | CRITICAL | No |

## Backend Integration

- **Services (to be exposed)**:
  - `ReoptimizationService.cs`
  - `WhatIfService.cs`
  - `ResourceOptimizationService.cs`
- **Endpoints (proposed)**:
  - `POST /reoptimize/trigger` — Manually trigger re-optimization
  - `GET /reoptimize/history` — View recent re-optimization events
  - `POST /whatif/simulate` — Simulate a proposed change
  - `GET /whatif/impact/{changeId}` — Get impact analysis for a change
- **Real-time**: WebSocket for push notifications of all changes

## Recommended Priority

**Priority 8–9** — High effort. Requires:
1. API exposure for ReoptimizationService, WhatIfService, ResourceOptimizationService
2. Real-time alert infrastructure
3. LLM integration for all explanation generation
4. WebSocket integration for live updates to Digital Twin

This is the "brain" of the system — it ties together all other services into a cohesive, intelligent scheduling platform.
