# Use Case 1: Vessel Arrival Prediction

## Overview

AI-powered prediction and natural-language explanation of vessel estimated time of arrival (ETA), including deviation analysis, confidence scoring, and contextual factor breakdowns.

> **⚡ Key Dependency:** Vessel Arrival Prediction is **fed by the Vessel Tracking Service**. Real-time AIS position data from Vessel Tracking is the primary input to the ML prediction model.

## Service Dependency Chain

```
┌────────────────────────┐      ┌─────────────────────────────┐      ┌─────────────────────┐
│  Vessel Tracking       │      │  Vessel Arrival Prediction  │      │  AI Berth Allocation│
│  Service               │─────▶│  Service                    │─────▶│  Service            │
│  (AIS Data)            │      │  (ML Model + LLM)           │      │  (Uses ETA)         │
└────────────────────────┘      └─────────────────────────────┘      └─────────────────────┘
         │                                    │
         │ Position, Speed,                   │ Predicted ETA,
         │ Course, Heading                    │ Confidence, Factors
         ▼                                    ▼
   Input Features                      Output to Downstream
```

## Current Status

| Data Point | Status | API Endpoint | LLM Required | Upstream Dependency |
|---|---|---|---|---|
| Predicted ETA | ✅ Dynamic | `/predictions/eta/active` | Yes — for reasoning | Vessel Tracking |
| Deviation Minutes | ✅ Dynamic | `/predictions/eta/active` | Yes — for explanation | Vessel Tracking |
| Confidence Level | ✅ Dynamic | `/predictions/eta/active` | Yes — for justification | Vessel Tracking |
| Prediction Factors | ✅ Dynamic | `/predictions/eta/active` | Yes — natural language | Vessel Tracking |
| AIS-Based Speed Analysis | ✅ Dynamic | `/tracking/vessels/{vesselId}/speed` | Yes — trend explanation | Vessel Tracking |
| Weather Impact Analysis | ❌ Not Implemented | — | Yes | Weather API |
| Traffic Congestion Analysis | ❌ Not Implemented | — | Yes | Vessel Tracking (aggregate) |
| Historical Pattern Explanation | ❌ Not Implemented | — | Yes | Historical DB |

## Data Structure

```typescript
interface ETAPrediction {
  vesselId: number;
  vesselName: string;
  originalETA: string;
  predictedETA: string;
  deviationMinutes: number;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  factors: PredictionFactor[];  // ← LLM generates natural language
  trackingData: {
    currentPosition: { lat: number; lng: number };
    currentSpeed: number;
    currentCourse: number;
    distanceToPort: number;
    lastUpdated: string;
  };
}

interface PredictionFactor {
  factorType: 'SPEED' | 'WEATHER' | 'TRAFFIC' | 'HISTORICAL' | 'PORT_CONGESTION';
  impact: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  magnitude: number;  // -100 to +100
  description: string;
}
```

## LLM Integration Points

### What the LLM Should Do

1. **ETA Reasoning** — Convert raw prediction data into human-readable explanations:
   > "MV Pacific Star is running 45 minutes late. Current AIS data shows the vessel reduced speed from 14 kn to 10 kn after passing Waypoint Charlie, likely due to increased headwinds in the approach channel."

2. **Deviation Explanation** — Provide root-cause narrative for deviation minutes:
   > "The +90 minute deviation is attributed to: (1) 30 minutes lost during pilot boarding delay at previous port, (2) 45 minutes from reduced speed in adverse weather zone, (3) 15 minutes from increased traffic density at anchorage approach."

3. **Confidence Justification** — Explain why confidence is HIGH, MEDIUM, or LOW:
   > "Confidence is MEDIUM because: AIS data shows consistent speed over the last 6 hours (positive), but weather forecast indicates potential squalls in the approach zone (uncertainty factor), and this vessel's historical arrival variance is ±25 minutes (moderate)."

4. **Factor Narration** — Transform the `factors` array into a cohesive summary:
   > "Three factors are influencing this ETA: favorable current (+15 min), reduced visibility forecast (-20 min), and standard vessel performance based on historical data (+5 min)."

### Vessel Tracking Data Integration

The Vessel Tracking Service provides the following inputs to the prediction model:

| Tracking Data Point | Use in Prediction |
|---|---|
| Current Position (lat/lng) | Distance-to-port calculation |
| Speed Over Ground (SOG) | Speed trend analysis |
| Course Over Ground (COG) | Route deviation detection |
| Heading | Comparison with expected approach heading |
| Navigation Status | Phase detection (approaching, anchored, maneuvering) |
| Position History (24h) | Speed pattern analysis, anomaly detection |

### Features Not Yet Implemented (Require LLM + Tracking)

- **Weather Impact Analysis** — Correlate weather data with speed changes detected in AIS tracking and explain the causal link.
- **Traffic Congestion Analysis** — Use aggregate Vessel Tracking data to assess port/channel congestion and describe its effect on arrival timing.
- **Historical Pattern Explanation** — Compare current tracking data with historical arrival patterns for the same vessel or route.

## Real-Time Alerts Integration

Every ETA prediction change triggers alert evaluation:

| Alert Type | Trigger Condition | Severity |
|---|---|---|
| `ETA_DEVIATION_MINOR` | `deviationMinutes` > 30 | INFO |
| `ETA_DEVIATION_SIGNIFICANT` | `deviationMinutes` > 60 | WARNING |
| `ETA_DEVIATION_CRITICAL` | `deviationMinutes` > 120 | CRITICAL |
| `CONFIDENCE_DROP` | Confidence changes from HIGH to LOW | WARNING |
| `TRACKING_DATA_STALE` | `lastUpdated` > 30 minutes ago | WARNING |

## Backend Integration

- **Upstream Service:** `VesselTrackingService` (AIS data feed)
- **Service:** `predictionService`
- **Endpoint:** `/predictions/eta/active`
- **Refresh Interval:** 60 seconds (synced with AIS update frequency)
- **Response Type:** `ETAPrediction[]`

## Recommended Priority

**Priority 3** — Medium effort. Dynamic data is already being fetched; the LLM layer adds explanation and reasoning. However, full functionality requires the Vessel Tracking Service (Priority 1) to be fully exposed first.
