# Use Case 6: Real-Time Alerts

## Overview

Centralized alert management system that monitors all SmartBerth AI services and generates **real-time alerts for all actions**. Every state change, prediction update, conflict detection, and optimization decision triggers alert evaluation.

> **⚡ Key Principle:** The system operates on a **"no silent changes"** policy. Every significant event generates an alert with LLM-powered natural language explanation, ensuring terminal operators have full visibility into system behavior.

## Alert Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Real-Time Alert System                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   EVENT SOURCES                                                             │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│   │ Vessel      │ │ ETA         │ │ Berth       │ │ Conflict    │          │
│   │ Tracking    │ │ Prediction  │ │ Allocation  │ │ Detection   │          │
│   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘          │
│          │               │               │               │                  │
│   ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐ ┌──────┴──────┐          │
│   │ Re-Opt      │ │ Resource    │ │ Digital     │ │ Weather     │          │
│   │ Engine      │ │ Management  │ │ Twin        │ │ Service     │          │
│   └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘          │
│          │               │               │               │                  │
│          └───────────────┴───────────────┴───────────────┘                  │
│                                    │                                        │
│                                    ▼                                        │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                       ALERT PROCESSING ENGINE                        │  │
│   │                                                                      │  │
│   │   1. Event Reception — Capture event from any source                │  │
│   │   2. Alert Rule Evaluation — Match event against alert rules        │  │
│   │   3. Severity Classification — Determine INFO/WARNING/CRITICAL      │  │
│   │   4. LLM Message Generation — Create natural language alert text    │  │
│   │   5. Deduplication — Suppress duplicate/redundant alerts            │  │
│   │   6. Routing — Send to appropriate channels (UI, email, SMS, API)   │  │
│   │   7. Logging — Persist for audit and analytics                      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│                                    ▼                                        │
│   ALERT DELIVERY                                                            │
│   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│   │ UI Toast    │ │ Alert Panel │ │ WebSocket   │ │ External    │          │
│   │ Notifications│ │ Dashboard   │ │ Push        │ │ Integrations│          │
│   └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Alert Categories by Source

### Vessel Tracking Alerts

| Alert Type | Trigger | Severity | Auto-Dismiss |
|---|---|---|---|
| `VESSEL_POSITION_UPDATE` | New AIS position received | DEBUG | Yes |
| `VESSEL_SPEED_CHANGE` | Speed Δ > 3 kn | INFO | Yes (15 min) |
| `VESSEL_COURSE_DEVIATION` | Course Δ > 20° | WARNING | No |
| `VESSEL_UNEXPECTED_STOP` | Speed < 1 kn outside anchorage | WARNING | No |
| `VESSEL_PHASE_TRANSITION` | Phase change (e.g., Approaching → Anchored) | INFO | Yes (30 min) |
| `VESSEL_ENTERED_PORT_ZONE` | Vessel within 50 nm | INFO | Yes (1 hour) |
| `VESSEL_AT_PILOT_STATION` | Vessel at pilot boarding position | INFO | No |
| `AIS_DATA_STALE` | No update for > 30 min | WARNING | No |
| `AIS_DATA_LOST` | No update for > 2 hours | CRITICAL | No |

### ETA Prediction Alerts

| Alert Type | Trigger | Severity | Auto-Dismiss |
|---|---|---|---|
| `ETA_UPDATED` | New prediction generated | DEBUG | Yes |
| `ETA_DEVIATION_MINOR` | Deviation 15-30 min | INFO | Yes (30 min) |
| `ETA_DEVIATION_MODERATE` | Deviation 30-60 min | WARNING | No |
| `ETA_DEVIATION_SEVERE` | Deviation > 60 min | CRITICAL | No |
| `ETA_CONFIDENCE_DROP` | Confidence HIGH → LOW | WARNING | No |
| `ETA_EARLIER_THAN_SCHEDULED` | Predicted arrival > 30 min early | WARNING | No |

### Berth Allocation Alerts

| Alert Type | Trigger | Severity | Auto-Dismiss |
|---|---|---|---|
| `BERTH_SUGGESTION_GENERATED` | New suggestion available | INFO | Yes (1 hour) |
| `BERTH_SUGGESTION_CHANGED` | Top suggestion changed | WARNING | No |
| `BERTH_ASSIGNED` | Berth assignment confirmed | INFO | Yes (30 min) |
| `BERTH_REASSIGNED` | Assignment changed | WARNING | No |
| `CONSTRAINT_VIOLATION_SOFT` | Soft constraint violated | WARNING | No |
| `CONSTRAINT_VIOLATION_HARD` | Hard constraint violated | CRITICAL | No |
| `NO_SUITABLE_BERTH` | No berth matches vessel requirements | CRITICAL | No |

### Conflict Detection Alerts

| Alert Type | Trigger | Severity | Auto-Dismiss |
|---|---|---|---|
| `CONFLICT_DETECTED` | New conflict identified | HIGH | No |
| `CONFLICT_RESOLVED` | Conflict successfully resolved | INFO | Yes (30 min) |
| `CONFLICT_ESCALATED` | Conflict unresolved for > 30 min | CRITICAL | No |
| `OVERSTAY_WARNING` | Vessel 15 min past ETD | WARNING | No |
| `OVERSTAY_CRITICAL` | Vessel 60+ min past ETD | CRITICAL | No |
| `CASCADE_DETECTED` | Conflict affects 3+ vessels | HIGH | No |

### Re-Optimization Alerts

| Alert Type | Trigger | Severity | Auto-Dismiss |
|---|---|---|---|
| `REOPTIMIZATION_TRIGGERED` | Re-optimization started | INFO | Yes (5 min) |
| `REOPTIMIZATION_COMPLETED` | Re-optimization finished | INFO | Yes (30 min) |
| `SCHEDULE_CHANGE` | Vessel schedule modified | WARNING | No |
| `PRIORITY_CHANGED` | Vessel priority adjusted | INFO | Yes (1 hour) |
| `RESOURCE_REALLOCATED` | Crane/tug/pilot reassigned | INFO | Yes (30 min) |
| `OPTIMIZATION_FAILED` | No valid solution found | CRITICAL | No |

### Digital Twin / Berth Overview Alerts

| Alert Type | Trigger | Severity | Auto-Dismiss |
|---|---|---|---|
| `BERTH_STATUS_CHANGE` | Berth status changed (occupied/vacant/maintenance) | INFO | Yes (15 min) |
| `TERMINAL_CAPACITY_WARNING` | Terminal > 80% occupied | WARNING | No |
| `TERMINAL_CAPACITY_CRITICAL` | Terminal > 95% occupied | CRITICAL | No |
| `SIMULATION_DESYNC` | Digital Twin out of sync with reality | WARNING | No |

## Data Structure

```typescript
interface Alert {
  alertId: string;
  alertType: string;
  severity: 'DEBUG' | 'INFO' | 'WARNING' | 'HIGH' | 'CRITICAL';
  source: AlertSource;
  timestamp: string;
  title: string;
  message: string;           // ← LLM-generated natural language
  detailedExplanation?: string;  // ← Optional LLM deep-dive
  relatedEntities: RelatedEntity[];
  actionRequired: boolean;
  suggestedActions?: string[];  // ← LLM-suggested next steps
  autoDismiss: boolean;
  autoDismissAfterMs?: number;
  acknowledgedAt?: string;
  acknowledgedBy?: string;
  resolvedAt?: string;
  resolvedBy?: string;
  metadata: Record<string, any>;
}

interface AlertSource {
  service: string;
  eventType: string;
  eventId: string;
}

interface RelatedEntity {
  entityType: 'VESSEL' | 'BERTH' | 'TERMINAL' | 'PILOT' | 'TUG' | 'CRANE' | 'CHANNEL';
  entityId: string;
  entityName: string;
}

interface AlertPreferences {
  userId: string;
  severityFilter: ('DEBUG' | 'INFO' | 'WARNING' | 'HIGH' | 'CRITICAL')[];
  sourceFilter: string[];
  deliveryChannels: ('UI' | 'EMAIL' | 'SMS' | 'WEBHOOK')[];
  quietHours?: { start: string; end: string };
  groupSimilarAlerts: boolean;
  maxAlertsPerHour?: number;
}
```

## LLM Integration for Alert Messages

### Example Alert Transformations

**Raw Event:**
```json
{
  "eventType": "ETA_DEVIATION",
  "vesselId": 123,
  "vesselName": "MV Pacific Star",
  "scheduledETA": "2025-02-05T16:00:00Z",
  "predictedETA": "2025-02-05T17:15:00Z",
  "deviationMinutes": 75
}
```

**LLM-Generated Alert:**
> **⚠️ ETA Deviation — MV Pacific Star**
> 
> MV Pacific Star is now predicted to arrive 1 hour 15 minutes late (17:15 instead of 16:00).
> 
> **Likely cause**: AIS tracking shows the vessel reduced speed from 14 kn to 9 kn at 14:30 UTC, coinciding with weather advisory for 25-knot headwinds in the approach zone.
> 
> **Impact**: This may affect the berth assignment at CT3-CB1, which has a subsequent vessel scheduled at 18:00.
> 
> **Suggested action**: Review berth schedule for CT3-CB1 and consider reassigning if delay extends further.

## Backend Integration

- **Service:** `AlertService` (to be implemented)
- **Endpoints (proposed)**:
  - `GET /alerts/active` — Get all active alerts
  - `GET /alerts/history` — Get historical alerts
  - `POST /alerts/{alertId}/acknowledge` — Acknowledge an alert
  - `POST /alerts/{alertId}/resolve` — Mark alert as resolved
  - `PUT /alerts/preferences` — Update user alert preferences
  - `WS /alerts/stream` — WebSocket for real-time alert push
- **Storage:** Time-series database for alert history and analytics

## Recommended Priority

**Priority 2 — CRITICAL.** The alert system is the operational interface for terminal operators. Without robust, LLM-powered alerts:
- Operators miss important events
- System changes happen silently
- Audit trail is incomplete
- Decision-making is reactive rather than proactive
