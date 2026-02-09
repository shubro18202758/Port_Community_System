# Use Case 3: Berth Allotment and Optimization

## Overview

AI-assisted berth allocation that provides ranked suggestions with confidence scores, constraint validation, and natural-language reasoning for each recommendation.

> **⚡ Key Dependency:** AI Berth Allocation is **supported by Vessel Arrival Prediction**. The allocation engine uses predicted ETAs (not just scheduled ETAs) to optimize berth assignments, accounting for expected delays and early arrivals.

## Service Dependency Chain

```
┌──────────────────┐      ┌─────────────────────────┐      ┌──────────────────────────┐
│ Vessel Tracking  │──────▶│ Vessel Arrival         │──────▶│ AI Berth Allocation     │
│ Service          │      │ Prediction             │      │ (Optimization Engine)   │
└──────────────────┘      └─────────────────────────┘      └────────────┬─────────────┘
                                                                        │
                    ┌───────────────────────────────────────────────────┘
                    │
                    ▼
      ┌──────────────────────────┐      ┌──────────────────────────┐
      │ Conflict Detection       │──────▶│ Digital Twin /           │
      │ (Chain-of-Thought)       │      │ Berth Overview           │
      └──────────────────────────┘      └──────────────────────────┘
```

### How Arrival Prediction Supports Berth Allocation

| Scenario | Without Arrival Prediction | With Arrival Prediction |
|---|---|---|
| Vessel running 2h late | Allocate based on scheduled ETA → berth sits empty | Allocate based on predicted ETA → assign another vessel to the gap |
| Vessel arriving early | Berth may be occupied → conflict | Early arrival detected → proactive reassignment |
| Multiple vessels converging | No visibility into actual arrival sequence | Optimized sequence based on predicted arrivals |
| Resource planning | Cranes/pilots scheduled for wrong time | Resources aligned with predicted times |

## Current Status

| Data Point | Status | API Endpoint | LLM Required | Upstream Dependency |
|---|---|---|---|---|
| Berth Suggestions | ✅ Dynamic | `/suggestions/berth/{vesselId}` | Yes — reasoning | Arrival Prediction |
| Confidence Score | ✅ Dynamic | `/suggestions/berth/{vesselId}` | Yes — explanation | Arrival Prediction |
| Constraint Checks | ✅ Dynamic | `/suggestions/berth/{vesselId}` | Yes — violation text | — |
| Ranking Reasoning | ✅ Dynamic | `/suggestions/berth/{vesselId}` | Yes — natural language | — |
| Alternative Suggestions | ✅ Dynamic | `/suggestions/berth/{vesselId}` | Yes — comparison | — |
| ETA-Based Timing | ✅ Dynamic | Internal | No | Arrival Prediction |
| Resource Optimization | ❌ Not Exposed | `ResourceOptimizationService` | Yes | — |
| OR-Tools Optimization | ❌ Not Exposed | `BerthOptimizationOrToolsService` | No (algorithmic) | — |

## Data Structure

```typescript
interface BerthSuggestion {
  rank: number;
  berthId: number;
  berthName: string;
  terminalId: string;
  score: number;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  reasoning: ReasoningFactor[];  // ← LLM generates natural language
  constraints: ConstraintCheck;
  violations: ConstraintViolation[];  // ← LLM for message
  timing: {
    suggestedBerthingTime: string;  // Based on predicted ETA
    basedOnPredictedETA: string;    // From Arrival Prediction
    etaConfidence: 'HIGH' | 'MEDIUM' | 'LOW';
    bufferMinutes: number;          // Safety buffer based on ETA confidence
  };
  alternativesConsidered: number;
}

interface ReasoningFactor {
  factor: string;
  weight: number;
  impact: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL';
  explanation: string;
}

interface ConstraintViolation {
  constraintType: 'LOA' | 'BEAM' | 'DRAFT' | 'CARGO' | 'HAZMAT' | 'TIDE' | 'AVAILABILITY';
  severity: 'HARD' | 'SOFT';
  message: string;  // ← LLM generates human-readable message
  resolution: string;  // ← LLM suggests resolution
}
```

## LLM Integration Points

### What the LLM Should Do

1. **Suggestion Reasoning with ETA Context** — Explain why a berth was recommended, including ETA factors:
   > "Berth CT3-CB1 is recommended for MV Pacific Star because:
   > - **ETA-based timing**: The vessel's predicted arrival (16:45, HIGH confidence) aligns with berth availability from 16:30
   > - **Draft compatibility**: Vessel draft (14.2m) is within berth limit (17.0m) with 2.8m clearance
   > - **Cargo type match**: Container berth with 5 quay cranes available
   > - **Minimal repositioning**: No crane movement required from previous vessel"

2. **Confidence Explanation with ETA Uncertainty** — Articulate confidence drivers:
   > "Confidence is MEDIUM because: Berth fit is excellent (HIGH confidence on constraints), but the vessel's ETA confidence is MEDIUM due to weather uncertainty in the approach zone. A 30-minute buffer has been added to the suggested berthing time."

3. **Constraint Violation Text** — Translate failures into actionable messages:
   > "Berth T1-MB3 cannot be used — vessel LOA (365m) exceeds the berth maximum (280m) by 85m. **Suggested alternative**: Berth CT4-CB1 (max LOA 410m) is available from 18:00."

4. **Alternative Comparison with Timing Analysis** — Compare alternatives:
   > "**Top 3 Berth Options for MV Pacific Star:**
   > | Rank | Berth | Available From | ETA Gap | Score | Key Trade-off |
   > |---|---|---|---|---|---|
   > | 1 | CT3-CB1 | 16:30 | +15 min | 94 | Optimal fit, no conflicts |
   > | 2 | CT4-CB2 | 16:00 | -45 min | 87 | Vessel would wait 45 min at anchorage |
   > | 3 | CT2-CB1 | 17:30 | +45 min | 82 | Berth available later, but longer crane setup |"

5. **Resource Optimization Reasoning** — Once exposed:
   > "Crane allocation: QC-07 and QC-08 assigned to this berth call. This pairing was selected because both cranes completed calibration yesterday and have no scheduled maintenance for 72 hours. Alternative crane pair (QC-05, QC-06) was not selected due to QC-05's scheduled inspection at 18:00."

## Real-Time Alerts Integration

| Alert Type | Trigger Condition | Severity |
|---|---|---|
| `NEW_SUGGESTION_AVAILABLE` | New optimized suggestion generated | INFO |
| `SUGGESTION_CONFLICT` | Suggested berth has new conflict | WARNING |
| `ETA_CHANGE_IMPACTS_ALLOCATION` | ETA shift > 30 min changes optimal berth | WARNING |
| `CONSTRAINT_VIOLATION` | Hard constraint violated | CRITICAL |
| `RESOURCE_CONFLICT` | Crane/tug/pilot conflict detected | WARNING |

## Backend Integration

- **Upstream Service:** `predictionService` (Vessel Arrival Prediction)
- **Service:** `suggestionService`
- **Endpoint:** `/suggestions/berth/{vesselId}`
- **Refresh Interval:** 60 seconds / On-demand / On ETA change
- **Response Type:** `BerthSuggestion[]`

## Recommended Priority

**Priority 4** — Medium effort. Dynamic suggestion data is already flowing; LLM adds reasoning. However, the quality of allocation depends on Vessel Arrival Prediction (Priority 3), which depends on Vessel Tracking (Priority 1).
