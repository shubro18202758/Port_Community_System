# Use Case 4: Conflict Detection and Resolution

## Overview

Detection of schedule conflicts and deviations (ETA shifts, overstays, berth overlaps, resource conflicts) with **AI-generated Chain-of-Thought reasoning** for root-cause analysis and resolution recommendations.

> **⚡ Key Enhancement:** Conflict Detection is **powered by Chain-of-Thought (CoT) reasoning**. Instead of simple rule-based conflict flags, the LLM performs multi-step logical analysis to identify the root cause, evaluate resolution options, and recommend the optimal action with full reasoning transparency.

## Chain-of-Thought Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    Conflict Detection — Chain-of-Thought Flow              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   STEP 1: Conflict Identification                                          │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │ Input: Schedule state, ETA predictions, resource allocations         │  │
│   │ Process: Rule-based conflict detection                               │  │
│   │ Output: List of potential conflicts with affected entities           │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│   STEP 2: Root Cause Analysis (LLM Chain-of-Thought)                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │ LLM Prompt: "Analyze this conflict and identify the root cause.     │  │
│   │ Think step by step:                                                  │  │
│   │ 1. What entities are involved?                                       │  │
│   │ 2. What is the timeline of events leading to this conflict?          │  │
│   │ 3. What is the primary cause vs contributing factors?                │  │
│   │ 4. Is this conflict cascading from another upstream issue?"          │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│   STEP 3: Resolution Option Generation (LLM Chain-of-Thought)              │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │ LLM Prompt: "Generate resolution options. Think step by step:        │  │
│   │ 1. What are all possible ways to resolve this conflict?              │  │
│   │ 2. For each option, what are the downstream impacts?                 │  │
│   │ 3. What resources are required for each option?                      │  │
│   │ 4. What are the trade-offs (time, cost, risk)?"                      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                              │                                              │
│                              ▼                                              │
│   STEP 4: Recommendation with Reasoning                                    │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │ LLM Prompt: "Recommend the best resolution. Explain your reasoning: │  │
│   │ 1. Why is this option better than alternatives?                      │  │
│   │ 2. What assumptions are you making?                                  │  │
│   │ 3. What risks remain?                                                │  │
│   │ 4. What should the operator monitor after implementation?"           │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Current Status

| Data Point | Status | API Endpoint | LLM Required | CoT Required |
|---|---|---|---|---|
| Berth Overlap Detection | ✅ Frontend-only | — | Yes — explanation | Yes |
| ETA Deviation Alert | ✅ Frontend-only | — | Yes — root cause | Yes |
| Overstay Detection | ✅ Frontend-only | `App.tsx` | Yes — resolution | Yes |
| Approaching ETD Warning | ✅ Frontend-only | `App.tsx` | Yes — action rec | No |
| Resource Conflict | ❌ Not Exposed | `ConflictDetectionService` | Yes — resolution | Yes |
| Constraint Violations | ⚠️ Partial | Suggestion response | Yes — explanation | No |
| What-If Analysis | ❌ Not Exposed | `WhatIfService` | Yes — impact | Yes |
| Cascade Analysis | ❌ Not Implemented | — | Yes — chain impact | Yes |

## Data Structure

```typescript
interface ConflictDetectionResult {
  conflictId: string;
  conflictType: ConflictType;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  detectedAt: string;
  affectedEntities: AffectedEntity[];
  chainOfThought: ChainOfThoughtAnalysis;  // ← LLM reasoning
  resolutionOptions: ResolutionOption[];
  recommendedResolution: ResolutionOption;
  alerts: Alert[];
}

type ConflictType = 
  | 'BERTH_OVERLAP'        // Two vessels assigned overlapping times at same berth
  | 'ETA_DEVIATION'        // Predicted ETA differs significantly from scheduled
  | 'OVERSTAY'             // Vessel exceeds scheduled departure time
  | 'RESOURCE_CONFLICT'    // Crane/tug/pilot double-booked
  | 'CONSTRAINT_VIOLATION' // Hard constraint violated (draft, LOA, cargo)
  | 'CASCADE_CONFLICT';    // Conflict caused by upstream issue

interface ChainOfThoughtAnalysis {
  step1_identification: {
    conflictSummary: string;
    entitiesInvolved: string[];
    timelineOfEvents: string[];
  };
  step2_rootCause: {
    primaryCause: string;
    contributingFactors: string[];
    upstreamIssues: string[];
    reasoning: string;  // Full CoT reasoning text
  };
  step3_resolutionOptions: {
    options: ResolutionOption[];
    reasoning: string;  // Full CoT reasoning text
  };
  step4_recommendation: {
    recommendedOption: string;
    justification: string;
    assumptions: string[];
    residualRisks: string[];
    monitoringAdvice: string;
    reasoning: string;  // Full CoT reasoning text
  };
}

interface ResolutionOption {
  optionId: string;
  description: string;
  actionSteps: string[];
  estimatedImpact: {
    timeImpact: string;
    costImpact: string;
    riskLevel: 'LOW' | 'MEDIUM' | 'HIGH';
  };
  affectedVessels: string[];
  resourcesRequired: string[];
}
```

## LLM Chain-of-Thought Integration

### Example: Berth Overlap Conflict

**Input to LLM:**
```json
{
  "conflictType": "BERTH_OVERLAP",
  "berth": "CT3-CB1",
  "vessel1": { "name": "MV Pacific Star", "scheduledBerthing": "16:00", "predictedETA": "16:45" },
  "vessel2": { "name": "MV Ocean Fortune", "scheduledBerthing": "16:30", "currentStatus": "AT_BERTH" },
  "currentTime": "15:30"
}
```

**LLM Chain-of-Thought Response:**

> **STEP 1: Conflict Identification**
> 
> A berth overlap conflict exists at Berth CT3-CB1:
> - MV Ocean Fortune is currently at berth (arrived earlier today)
> - MV Pacific Star is scheduled to berth at 16:00, with predicted ETA of 16:45
> - MV Ocean Fortune's scheduled ETD is 16:30, but cargo operations are running behind schedule
> 
> **STEP 2: Root Cause Analysis**
> 
> Let me trace the chain of events:
> 1. MV Ocean Fortune berthed on schedule at 08:00 this morning
> 2. Cargo discharge was delayed by 90 minutes due to crane QC-05 breakdown from 10:00-11:30
> 3. This pushed the cargo completion estimate from 15:30 to 17:00
> 4. The scheduled ETD of 16:30 is now unrealistic
> 5. Meanwhile, MV Pacific Star's ETA has slipped from 16:00 to 16:45 due to weather delays
> 
> **Primary cause**: Crane breakdown on MV Ocean Fortune causing overstay
> **Contributing factor**: MV Pacific Star's delayed ETA partially mitigates the conflict but doesn't resolve it
> 
> **STEP 3: Resolution Options**
> 
> Option A: **Wait for Natural Resolution**
> - MV Pacific Star's predicted ETA is 16:45
> - If MV Ocean Fortune can depart by 16:30 (unlikely given cargo status), conflict resolves naturally
> - Risk: HIGH — cargo operations show 17:00 completion estimate
> 
> Option B: **Hold MV Pacific Star at Anchorage**
> - Direct MV Pacific Star to anchorage upon arrival
> - Wait for MV Ocean Fortune to complete and depart
> - Estimated delay to MV Pacific Star: 1-2 hours
> - Cost: Anchorage fees, pilot re-dispatch
> 
> Option C: **Reassign MV Pacific Star to Alternate Berth**
> - Berth CT4-CB1 is available from 16:00
> - Same terminal, similar crane configuration
> - Requires crane reallocation (QC-09, QC-10 instead of QC-07, QC-08)
> - No delay to MV Pacific Star
> 
> Option D: **Expedite MV Ocean Fortune Departure**
> - Request expedited cargo completion (overtime crew)
> - Risk: May compromise cargo handling quality
> - May not achieve 16:30 departure even with expedition
> 
> **STEP 4: Recommendation**
> 
> **Recommended: Option C — Reassign MV Pacific Star to CT4-CB1**
> 
> Justification:
> - Eliminates conflict with zero delay to MV Pacific Star
> - CT4-CB1 is operationally equivalent (same draft clearance, similar crane capacity)
> - Crane reallocation is straightforward — QC-09 and QC-10 are idle
> - No impact to MV Ocean Fortune's cargo operations
> 
> Assumptions:
> - CT4-CB1 remains available (no competing claims in the next 30 minutes)
> - QC-09 and QC-10 are operational
> 
> Residual risks:
> - If another vessel claims CT4-CB1 before confirmation, Option B becomes the fallback
> 
> Monitoring advice:
> - Track MV Pacific Star's position to confirm 16:45 ETA holds
> - Confirm MV Ocean Fortune's cargo completion by 17:00
> - Alert if CT4-CB1 availability changes

## Real-Time Alerts Integration

Every conflict triggers immediate alerts:

| Alert Type | Trigger | Severity | CoT Analysis |
|---|---|---|---|
| `BERTH_OVERLAP_DETECTED` | Two vessels claim same berth window | CRITICAL | Yes — full analysis |
| `OVERSTAY_WARNING` | Vessel 30 min beyond ETD | WARNING | Yes — root cause |
| `OVERSTAY_CRITICAL` | Vessel 60+ min beyond ETD | CRITICAL | Yes — resolution |
| `RESOURCE_DOUBLE_BOOK` | Same crane/pilot assigned twice | HIGH | Yes — resolution |
| `CASCADE_ALERT` | Conflict affects downstream schedule | HIGH | Yes — chain analysis |
| `ETA_CONFLICT` | Predicted ETA creates new conflict | WARNING | Yes — preemptive |

## Backend Integration

- **Service:** `ConflictDetectionService` (to be exposed)
- **Endpoint (proposed):** `/conflicts/detect`
- **What-If Service:** `WhatIfService` for resolution impact analysis
- **Refresh Interval:** Real-time (on any schedule change or ETA update)

## Recommended Priority

**Priority 5** — High effort. Conflict Detection requires:
1. Backend service exposure
2. LLM integration with structured CoT prompts
3. Real-time alert integration
4. What-If service for resolution impact analysis

Chain-of-Thought reasoning is the key differentiator — it transforms conflict detection from "flag and alert" to "analyze, explain, and recommend."
