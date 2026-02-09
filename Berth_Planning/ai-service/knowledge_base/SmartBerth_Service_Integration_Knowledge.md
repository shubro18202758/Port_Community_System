# SmartBerth AI - Service Integration & API Architecture Knowledge

**Document Version:** 2.0  
**Last Updated:** February 2026  
**Purpose:** Comprehensive knowledge of service dependencies, API endpoints, data flow, and LLM integration patterns  
**Priority:** HIGH — Cross-cutting architectural knowledge

---

## 1. Service Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SmartBerth AI — Service Flow                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌──────────────────┐         ┌───────────────────────────┐           │
│   │ Vessel Tracking  │────────▶│ Vessel Arrival Prediction  │           │
│   │ Service (AIS)    │         │ (ML + LLM Reasoning)       │           │
│   └──────────────────┘         └───────────────┬───────────┘           │
│          │                                     │                        │
│          │ Real-Time Position                  │ ETA Feeds              │
│          ▼                                     ▼                        │
│   ┌──────────────────┐         ┌───────────────────────────┐           │
│   │ Digital Twin /   │◀───────│ AI Berth Allocation       │           │
│   │ Berth Overview   │         │ (Optimization Engine)     │           │
│   └──────────────────┘         └───────────────┬───────────┘           │
│                                                │                        │
│                                                ▼                        │
│                                ┌───────────────────────────┐           │
│                                │ Conflict Detection        │           │
│                                │ (Chain-of-Thought)        │           │
│                                └───────────────┬───────────┘           │
│                                                │                        │
│                     ┌──────────────────────────┴──────────┐            │
│                     ▼                                     ▼            │
│          ┌──────────────────┐              ┌──────────────────┐       │
│          │ Real-Time Alerts │              │ Re-Optimization  │       │
│          │ (All Services)   │              │ Engine           │       │
│          └──────────────────┘              └──────────────────┘       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Service Dependency Matrix

### 2.1 Upstream → Downstream Dependencies
| Upstream Service | Downstream Service | Data Transferred |
|---|---|---|
| Vessel Tracking | ETA Prediction | AIS positions, speed, course, heading |
| Vessel Tracking | Digital Twin | Live vessel positions and status |
| Vessel Tracking | Alert Service | Phase transitions, anomalies |
| ETA Prediction | Berth Allocation | Predicted ETAs with confidence |
| ETA Prediction | Conflict Detection | ETA deviations from schedule |
| ETA Prediction | Alert Service | Deviation notifications |
| Berth Allocation | Conflict Detection | Proposed allocations for validation |
| Berth Allocation | Digital Twin | Berth assignments |
| Berth Allocation | Alert Service | Allocation notifications |
| Conflict Detection | Re-Optimization | Detected conflicts requiring resolution |
| Conflict Detection | Alert Service | Conflict notifications |
| Re-Optimization | Digital Twin | Updated schedule |
| Re-Optimization | Alert Service | Schedule change notifications |
| Weather Service | ETA Prediction | Weather conditions for speed correction |
| Weather Service | Berth Allocation | Weather constraints for operations |
| Weather Service | Alert Service | Weather alerts |

### 2.2 Service Priority (Implementation Order)
1. **Priority 1:** Vessel Tracking — Foundation for all other services
2. **Priority 2:** Real-Time Alerts — Operational notification interface
3. **Priority 3:** ETA Prediction — ML + LLM reasoning
4. **Priority 4:** Berth Allotment & Optimization — Core allocation engine
5. **Priority 5:** Conflict Detection & Resolution — Schedule integrity
6. **Priority 6:** Digital Twin / Berth Overview — Aggregation and visualization
7. **Priority 7-9:** Re-Optimization Engine — Central orchestrator

---

## 3. API Endpoints Catalog

### 3.1 Currently Active Endpoints
| Endpoint | Method | Purpose | Status |
|---|---|---|---|
| `/health` | GET | Service health check | Active |
| `/model/info` | GET | AI model status | Active |
| `/model/load` | POST | Load AI model | Active |
| `/model/generate` | POST | Text generation | Active |
| `/predictions/eta/active` | GET | Active ETA predictions | Active |
| `/suggestions/berth/{vesselId}` | GET | Berth suggestions | Active |
| `/chat` | POST | Chatbot interaction | Active |
| `/explain` | POST | AI explanation | Active |
| `/pipeline/query` | POST | Unified pipeline query | Active |
| `/pipeline/stats` | GET | Pipeline statistics | Active |
| `/pipeline/knowledge/search` | POST | Knowledge base search | Active |
| `/pipeline/graph/query` | POST | Graph knowledge query | Active |
| `/pipeline/berth/compatible` | GET | Compatible berth search | Active |
| `/pipeline/port/{code}/resources` | GET | Port resources | Active |
| `/pipeline/vessel/history` | GET | Vessel history | Active |

### 3.2 Planned Endpoints (From Frontend Documentation)
| Endpoint | Method | Purpose | Priority |
|---|---|---|---|
| `/tracking/vessels/positions` | GET | All vessel positions | 1 (Critical) |
| `/tracking/vessels/{id}/position` | GET | Single vessel position | 1 |
| `/tracking/vessels/{id}/history` | GET | Position history | 1 |
| `/tracking/vessels/{id}/metrics` | GET | Derived tracking metrics | 1 |
| `/tracking/vessels/stream` | WS | Real-time vessel updates | 1 |
| `/conflicts/detect` | POST | Detect schedule conflicts | 5 |
| `/reoptimize/trigger` | POST | Trigger re-optimization | 7 |
| `/reoptimize/history` | GET | Re-optimization history | 7 |
| `/whatif/simulate` | POST | What-if simulation | 7 |
| `/whatif/impact/{changeId}` | GET | Change impact analysis | 7 |
| `/alerts/active` | GET | Active alerts | 2 |
| `/alerts/history` | GET | Alert history | 2 |
| `/alerts/{id}/acknowledge` | POST | Acknowledge alert | 2 |
| `/alerts/{id}/resolve` | POST | Resolve alert | 2 |
| `/alerts/preferences` | PUT | Alert preferences | 2 |
| `/alerts/stream` | WS | Real-time alert push | 2 |
| `/digitaltwin/state` | GET | Current port state | 6 |
| `/digitaltwin/forecast` | GET | Projected future state | 6 |
| `/digitaltwin/whatif` | POST | What-if simulation | 6 |
| `/digitaltwin/stream` | WS | Real-time state updates | 6 |

---

## 4. LLM Integration Patterns

### 4.1 Pattern: Factor Narration
**Used by:** ETA Prediction, Berth Allocation
**Purpose:** Convert array of numerical factors into human-readable explanation
**Input:** `factors: [{factorType: "WEATHER", impact: "NEGATIVE", magnitude: -25, description: "..."}]`
**Output:** Natural language explanation: "The vessel is expected to arrive 45 minutes late primarily due to adverse weather conditions (headwinds of 25 knots reducing speed by 15%) and port congestion (3 vessels queued for the same terminal)."

### 4.2 Pattern: Chain-of-Thought Reasoning
**Used by:** Conflict Detection
**Purpose:** Multi-step structured reasoning for complex conflict analysis
**Steps:**
1. Identification → What is the conflict?
2. Root Cause → Why did it occur?
3. Options → What can we do?
4. Recommendation → What should we do?
**Output:** Structured JSON with reasoning at each step

### 4.3 Pattern: Simulation Narration
**Used by:** Digital Twin (what-if), Re-Optimization
**Purpose:** Narrate the implications of schedule changes or hypothetical scenarios
**Input:** Before/after schedule snapshots + changes list
**Output:** Human-readable impact assessment: "Moving Vessel X from Berth A to Berth B would delay Vessel Y by 2 hours but free up a crane for Vessel Z, reducing overall terminal waiting time by 15%."

### 4.4 Pattern: Alert Message Generation
**Used by:** All services (via Alert Service)
**Purpose:** Transform raw event data into actionable alert messages
**Input:** Event type, severity, affected entities, context
**Output:** Title, message, suggested actions (all in natural language)

### 4.5 Pattern: Confidence Justification
**Used by:** ETA Prediction, Berth Allocation
**Purpose:** Explain why a prediction or suggestion has a given confidence level
**Input:** Confidence level (HIGH/MEDIUM/LOW), prediction factors
**Output:** "Confidence is HIGH because: reliable AIS data (updated 30 seconds ago), favorable weather conditions, and the vessel has historically maintained consistent speed on this route."

---

## 5. Data Flow Architecture

### 5.1 Operational Phases
| Phase | Timeframe | Services Active | Key Data |
|---|---|---|---|
| Pre-Arrival Declaration | 72-24 hrs before ETA | Vessel Registration, Tracking | Vessel parameters, declared ETA, cargo manifest |
| AI Processing | 24-6 hrs before ETA | ETA Prediction, Berth Allocation | AIS data, weather, UKC, constraints |
| Confirmation | 6-2 hrs before arrival | Conflict Detection, Resource Planning | Berth assignment, pilot/tug scheduling |
| Operations | During port stay | All services | Real-time monitoring, re-optimization |
| Post-Departure | After vessel departs | Analytics, History | Performance metrics, historical logging |

### 5.2 ML Model Data Requirements
| ML Model | Input Data | Training Data | Output |
|---|---|---|---|
| ETA Prediction | AIS position, weather, congestion | Vessel_Call, AIS_Parameters, Weather | Predicted ETA + confidence |
| Berth Allocation | Vessel specs, berth specs, schedule | Vessel_Parameters, Berth_Parameters, Terminal_Parameters | Ranked berth suggestions |
| Dwell Time | Cargo volume, equipment, weather | Vessel_Call, Berth_Parameters, Weather | Hours at berth |
| Resource Scheduling | Requirements, availability, certs | Pilotage_Parameters, Tugboat_Parameters, Vessel_Call | Pilot/tug assignments |

---

## 6. Backend Services Inventory

### 6.1 Currently Implemented
| Service | Description | Technology |
|---|---|---|
| SmartBerthLLM | Central AI (Claude Opus 4) | Anthropic API |
| OllamaLLM / Manager Agent | Local orchestrator (Qwen3-8B) | Ollama + GPU |
| RAG Pipeline | Knowledge retrieval | ChromaDB + SentenceTransformers |
| Knowledge Graph | Entity relationships | In-Memory NetworkX / Neo4j |
| ETA Predictor | Vessel arrival prediction | ML models + heuristics |
| Berth Allocator | Berth suggestion scoring | Constraint-based optimization |
| Weather Service | Weather data integration | WeatherAPI.com |
| Database Service | SQL Server data access | ODBC/pyodbc |

### 6.2 Requiring API Exposure
| Service | Status | Backend Code | Frontend Need |
|---|---|---|---|
| VesselTrackingService | Exists in C# backend | Yes | Needs REST API endpoints |
| ConflictDetectionService | Partial | Needs completion | Chain-of-Thought integration |
| ReoptimizationService | Exists in C# backend | Yes | Needs REST API endpoints |
| WhatIfService | Exists in C# backend | Yes | Needs REST API endpoints |
| ResourceOptimizationService | Exists in C# backend | Yes | Needs REST API endpoints |
| AlertService | Not implemented | No | Full implementation needed |
| DigitalTwinService | Not implemented | No | Full implementation needed |
| BerthStatusService | Partial | Needs completion | REST + WebSocket |

---

## 7. Data Refresh Rates

| Data Type | Refresh Rate | Method | Priority |
|---|---|---|---|
| Vessel AIS Position | 10-30 seconds | WebSocket push | Real-time |
| ETA Predictions | 60 seconds | Polling / push | Near real-time |
| Berth Suggestions | 60 seconds / on-demand | Polling | Near real-time |
| Conflict Detection | On schedule change | Event-driven | Real-time |
| Weather Data | 15-60 minutes | Scheduled polling | Periodic |
| Terminal Metrics | 5 minutes | Calculated | Periodic |
| Berth Status | On change | Event-driven | Real-time |
| Alert Notifications | Immediate | WebSocket push | Real-time |
