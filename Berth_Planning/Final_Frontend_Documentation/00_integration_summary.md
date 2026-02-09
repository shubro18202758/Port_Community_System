# SmartBerth AI — LLM Integration Summary

## Overview

This document summarizes the current state of LLM integration across all SmartBerth AI use cases, highlighting what is already fetching dynamic data, what backend services need API exposure, and where LLM-powered natural language generation is needed.

## System Architecture: Core Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SmartBerth AI — Service Flow                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────────┐         ┌──────────────────────────┐                │
│   │ Vessel Tracking  │────────▶│ Vessel Arrival Prediction │                │
│   │ Service (AIS)    │         │ (ML + LLM Reasoning)      │                │
│   └──────────────────┘         └────────────┬─────────────┘                │
│          │                                  │                               │
│          │ Real-Time                        │ ETA Feeds                     │
│          │ Position                         ▼                               │
│          │                     ┌──────────────────────────┐                │
│          │                     │ AI Berth Allocation      │                │
│          │                     │ (Optimization Engine)    │                │
│          │                     └────────────┬─────────────┘                │
│          │                                  │                               │
│          │                                  │ Allocation                    │
│          │                                  ▼ Proposals                     │
│          │                     ┌──────────────────────────┐                │
│          │                     │ Conflict Detection       │                │
│          └────────────────────▶│ (Chain-of-Thought)       │                │
│                                └────────────┬─────────────┘                │
│                                             │                               │
│                                             │ Validated                     │
│                                             ▼ Schedule                      │
│                                ┌──────────────────────────┐                │
│                                │ Digital Twin / Berth     │                │
│                                │ Overview (Simulation)    │                │
│                                └──────────────────────────┘                │
│                                             │                               │
│                     ┌───────────────────────┴───────────────────────┐      │
│                     ▼                                               ▼      │
│          ┌──────────────────┐                          ┌──────────────────┐│
│          │ Real-Time Alerts │                          │ Re-Optimization  ││
│          │ (All Actions)    │                          │ Engine           ││
│          └──────────────────┘                          └──────────────────┘│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Dependency Relationships

| Upstream Service | Downstream Service | Relationship |
|---|---|---|
| **Vessel Tracking** | Vessel Arrival Prediction | AIS positions feed ETA ML model |
| **Vessel Arrival Prediction** | AI Berth Allocation | Predicted ETAs drive allocation timing |
| **AI Berth Allocation** | Conflict Detection | Proposed allocations validated via CoT |
| **Conflict Detection** | Digital Twin / Berth Overview | Validated schedules rendered in simulation |
| **All Services** | Real-Time Alerts | Every state change triggers alert evaluation |

---

## Currently Fetching Dynamic Data (2 Endpoints)

| Endpoint | Purpose |
|---|---|
| `/predictions/eta/active` | ETA predictions with factors |
| `/suggestions/berth/{vesselId}` | Berth suggestions with reasoning |

## Backend Services Not Exposed to Frontend

These services exist in the backend but need API endpoints before the frontend (and LLM layer) can consume them:

| Service | Purpose | Priority |
|---|---|---|
| **VesselTrackingService** | AIS stream, position history, movement analysis | Critical — feeds Arrival Prediction |
| **ReoptimizationService** | Real-time schedule adjustments | High |
| **WhatIfService** | Impact analysis for manual changes | High |
| **ResourceOptimizationService** | Crane/tug/pilot optimization | Medium |
| **ConflictDetectionService** | Schedule conflict detection (Chain-of-Thought) | High |
| **DigitalTwinService** | Port simulation, berth overview visualization | Medium |
| **AlertService** | Centralized real-time alert management | Critical |

## Features Needing LLM Integration

| Feature | LLM Capability Required | Use Case |
|---|---|---|
| Chatbot Responses | Natural Language Understanding | All |
| ETA Prediction Explanation | Factor narration, confidence justification | Vessel Arrival |
| Berth Suggestion Reasoning | Constraint explanation, alternative comparison | Berth Allocation |
| Conflict Detection | **Chain-of-Thought reasoning** for multi-step validation | Conflict Detection |
| Overstay Resolution | Root-cause analysis, action recommendations | Deviation Detection |
| Re-optimization Notifications | Change explanation, cascade impact narration | Re-Optimization |
| What-If Impact Analysis | Scenario comparison, trade-off articulation | Re-Optimization |
| Alert Explanations | Context-aware alert text generation | Real-Time Alerts |
| Digital Twin Narration | Simulation state explanation | Berth Overview |

## Recommended Priority Roadmap

| Priority | Feature | Category | Effort | Dependencies |
|---|---|---|---|---|
| 1 | Vessel Tracking API Exposure | Vessel Tracking | High | AIS data feed |
| 2 | Real-Time Alert Service | Alerts | High | All services |
| 3 | ETA Prediction + LLM Explanation | Vessel Arrival | Medium | Vessel Tracking |
| 4 | Berth Suggestion Reasoning | Berth Allotment | Medium | ETA Prediction |
| 5 | Conflict Detection (CoT) | Conflict Detection | High | Berth Allocation |
| 6 | Digital Twin / Berth Overview | Visualization | Medium | All upstream |
| 7 | Overstay Resolution | Deviation Detection | Medium | Conflict Detection |
| 8 | Re-optimization Notifications | Re-Optimization | High | Alert Service |
| 9 | What-If Impact Analysis | Re-Optimization | High | All services |
| 10 | Chatbot NLU | All | High | All services |

---

## Use Case Index

| # | Use Case | File | Key Enhancement |
|---|---|---|---|
| 1 | [Vessel Arrival Prediction](./01_vessel_arrival_prediction.md) | `01_vessel_arrival_prediction.md` | Fed by Vessel Tracking |
| 2 | [Vessel Tracking](./02_vessel_tracking.md) | `02_vessel_tracking.md` | Foundation for Arrival Prediction |
| 3 | [Berth Allotment & Optimization](./03_berth_allotment_optimization.md) | `03_berth_allotment_optimization.md` | Supported by Arrival Prediction |
| 4 | [Conflict Detection & Resolution](./04_conflict_detection_resolution.md) | `04_conflict_detection_resolution.md` | **Chain-of-Thought reasoning** |
| 5 | [Real-Time Re-Optimization Engine](./05_realtime_reoptimization_engine.md) | `05_realtime_reoptimization_engine.md` | Integrated alerts |
| 6 | [Real-Time Alerts](./06_realtime_alerts.md) | `06_realtime_alerts.md` | **System-wide alert layer** |
| 7 | [Berth Overview & Digital Twin](./07_berth_overview_digital_twin.md) | `07_berth_overview_digital_twin.md` | **Port simulation visualization** |
