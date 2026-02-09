# SmartBerth AI - Real-Time Alerts Knowledge

**Document Version:** 2.0  
**Last Updated:** February 2026  
**Purpose:** Comprehensive domain knowledge for the real-time alert system covering all SmartBerth services  
**Priority:** CRITICAL — System-wide operational interface

---

## 1. Alert Architecture

### 1.1 Core Principle
**No silent changes** — every significant event in SmartBerth generates an alert. The alert system is the primary interface between SmartBerth AI and port operators, providing:
- Real-time situational awareness
- Actionable notifications with LLM-generated explanations
- Historical audit trail of all events and operator responses

### 1.2 Alert Processing Pipeline
1. **Event Reception:** Raw event from source service (tracking, prediction, allocation, etc.)
2. **Rule Evaluation:** Apply alert rules to determine if event warrants an alert
3. **Severity Classification:** Assign severity based on impact magnitude and urgency
4. **LLM Message Generation:** Generate human-readable alert title, message, and suggested actions
5. **Deduplication:** Check for similar recent alerts to prevent alert fatigue
6. **Routing:** Deliver to appropriate channels (UI toast, panel, WebSocket, email, SMS)
7. **Logging:** Record alert for audit trail and analytics

---

## 2. Alert Severity Taxonomy

### 2.1 Severity Levels
| Severity | Description | Operator Action | Examples |
|---|---|---|---|
| DEBUG | System internals, not shown to operators | None | AIS heartbeat, internal state change |
| INFO | Routine operational event | Awareness only | Vessel phase change, ETA update, new suggestion |
| WARNING | Potential issue requiring monitoring | Monitor closely | ETA deviation >30 min, overstay 15 min, weather change |
| HIGH | Significant issue requiring attention | Action needed soon | Hard constraint violation, resource conflict, ETA deviation >120 min |
| CRITICAL | Urgent issue requiring immediate action | Immediate action | Berth overlap, AIS signal lost, no suitable berth, safety concern |

### 2.2 Severity Assignment Rules
- **Vessel Tracking alerts:** DEBUG (position update), INFO (phase change, speed change), WARNING (stale data, deviation), CRITICAL (signal lost, zone violation)
- **ETA Prediction alerts:** INFO (updated, minor deviation <30 min), WARNING (moderate 30-60 min), HIGH (severe >120 min), CRITICAL (confidence drop below 0.3)
- **Berth Allocation alerts:** INFO (suggestion generated), WARNING (soft constraint), HIGH (hard constraint, no berth), CRITICAL (forced reassignment)
- **Conflict Detection alerts:** WARNING (detected), HIGH (escalated), CRITICAL (cascade, unresolved >60 min)
- **Re-Optimization alerts:** INFO (triggered, completed), WARNING (schedule change), HIGH (priority change), CRITICAL (optimization failed)

---

## 3. Alert Categories (50+ Types)

### 3.1 Vessel Tracking Alerts (9 types)
| Alert Type | Severity | Description | Auto-Dismiss |
|---|---|---|---|
| POSITION_UPDATE | DEBUG | New AIS position received | 5 seconds |
| SPEED_CHANGE | INFO | Speed changed by >3 knots | 5 minutes |
| COURSE_DEVIATION | WARNING | >30° from expected course | None |
| UNEXPECTED_STOP | WARNING | Speed 0 outside designated areas | None |
| PHASE_TRANSITION | INFO | Vessel entered new phase (approaching, berthing, etc.) | 2 minutes |
| PORT_ZONE_ENTRY | INFO | Vessel crossed port approach boundary | 10 minutes |
| PILOT_STATION | INFO | Vessel arrived at pilot boarding station | None |
| AIS_STALE | WARNING | No AIS update for >30 minutes | On reception |
| AIS_LOST | CRITICAL | No AIS update for >60 minutes | On reception |

### 3.2 ETA Prediction Alerts (6 types)
| Alert Type | Severity | Description | Auto-Dismiss |
|---|---|---|---|
| ETA_UPDATED | INFO | New ETA prediction computed | 5 minutes |
| MINOR_DEVIATION | INFO | Deviation 15-30 minutes | 10 minutes |
| MODERATE_DEVIATION | WARNING | Deviation 30-60 minutes | None |
| SEVERE_DEVIATION | HIGH | Deviation >120 minutes | None |
| CONFIDENCE_DROP | WARNING | Prediction confidence significantly decreased | None |
| EARLY_ARRIVAL | INFO | Vessel arriving earlier than scheduled | 10 minutes |

### 3.3 Berth Allocation Alerts (7 types)
| Alert Type | Severity | Description | Auto-Dismiss |
|---|---|---|---|
| SUGGESTION_GENERATED | INFO | New berth suggestion available | 5 minutes |
| SUGGESTION_CHANGED | INFO | Previous suggestion updated | 5 minutes |
| BERTH_ASSIGNED | INFO | Vessel assigned to berth | 10 minutes |
| BERTH_REASSIGNED | WARNING | Vessel moved to different berth | None |
| SOFT_CONSTRAINT | WARNING | Soft constraint violated in allocation | 15 minutes |
| HARD_CONSTRAINT | HIGH | Hard constraint violation detected | None |
| NO_SUITABLE_BERTH | CRITICAL | No compatible berth available | None |

### 3.4 Conflict Detection Alerts (6 types)
| Alert Type | Severity | Description | Auto-Dismiss |
|---|---|---|---|
| CONFLICT_DETECTED | WARNING | New schedule conflict identified | None |
| CONFLICT_RESOLVED | INFO | Conflict successfully resolved | 5 minutes |
| CONFLICT_ESCALATED | HIGH | Conflict severity increased (unresolved) | None |
| OVERSTAY_WARNING | WARNING | Vessel overstay 15-60 minutes | None |
| OVERSTAY_CRITICAL | CRITICAL | Vessel overstay >60 minutes | None |
| CASCADE_CONFLICT | CRITICAL | Multiple vessels affected by propagating conflict | None |

### 3.5 Re-Optimization Alerts (6 types)
| Alert Type | Severity | Description | Auto-Dismiss |
|---|---|---|---|
| REOPT_TRIGGERED | INFO | Re-optimization process started | 2 minutes |
| REOPT_COMPLETED | INFO | Re-optimization finished successfully | 5 minutes |
| SCHEDULE_CHANGE | WARNING | Schedule modified by re-optimization | None |
| PRIORITY_CHANGE | WARNING | Vessel priority adjusted | None |
| RESOURCE_REALLOC | WARNING | Resources reassigned between operations | None |
| REOPT_FAILED | CRITICAL | Re-optimization could not find feasible solution | None |

### 3.6 Digital Twin Alerts (4 types)
| Alert Type | Severity | Description | Auto-Dismiss |
|---|---|---|---|
| BERTH_STATUS_CHANGE | INFO | Berth status changed (vacant/occupied/maintenance) | 5 minutes |
| TERMINAL_CAPACITY_WARNING | WARNING | Terminal occupancy >80% | 30 minutes |
| TERMINAL_CAPACITY_CRITICAL | CRITICAL | Terminal occupancy >95% | None |
| SIMULATION_DESYNC | WARNING | Digital twin state diverged from reality | None |

---

## 4. Alert LLM Integration

### 4.1 LLM Message Generation
For each alert, the LLM generates:
- **Title:** Short, actionable headline (e.g., "Vessel MAERSK ELBA — ETA Delayed 2 Hours")
- **Message:** Human-readable explanation with context:
  - What happened
  - Why it happened (likely cause)
  - What impact this has
  - What the operator should do
- **Suggested Actions:** 1-3 specific actions the operator can take

### 4.2 Example LLM-Generated Alert
```
Title: "Schedule Conflict — Berth BMCT-01 Double Booked"
Message: "Vessels MSC ANNA and EVER GIVEN are both scheduled to arrive at Berth BMCT-01 
between 14:00-18:00 on Feb 7. MSC ANNA is expected to arrive at 14:15 and EVER GIVEN 
at 14:45. The conflict arose because MSC ANNA's ETA shifted forward by 3 hours due to 
favorable weather conditions, overlapping with EVER GIVEN's existing reservation."
Suggested Actions:
1. Reassign MSC ANNA to Berth BMCT-02 (compatible, available 14:00-22:00)
2. Delay EVER GIVEN arrival by 4 hours (contact shipping agent)  
3. Request MSC ANNA reduce speed to original ETA window
```

---

## 5. Alert Management

### 5.1 Alert Lifecycle
1. **Active:** Alert generated, visible in operator dashboard
2. **Acknowledged:** Operator has seen and noted the alert
3. **Resolved:** Underlying issue addressed (manual or automatic)
4. **Auto-Dismissed:** Alert expired based on auto-dismiss timer
5. **Archived:** Moved to historical log for audit trail

### 5.2 Deduplication Logic
- Same source + same entity + same alert type within 5 minutes → merge into single alert
- Update existing alert with new data rather than creating duplicate
- Maintain count of merged events for severity assessment

### 5.3 User Preferences
Operators can configure:
- **Severity Filter:** Only show WARNING and above
- **Source Filter:** Only show alerts from specific services
- **Delivery Channels:** UI panel, toast notification, email, SMS, webhook
- **Quiet Hours:** Suppress non-CRITICAL alerts during specified hours
- **Group Similar:** Combine similar alerts into summary notifications
- **Rate Limit:** Maximum alerts per hour (prevent alert fatigue)

---

## 6. Alert Escalation Rules

| Condition | Action |
|---|---|
| WARNING unresolved > 30 minutes | Escalate to HIGH |
| HIGH unresolved > 60 minutes | Escalate to CRITICAL |
| CRITICAL unresolved > 120 minutes | Notify port authority / supervisor |
| Multiple CRITICALs within 1 hour | Trigger emergency protocol |
| Repeated same alert 3+ times in 1 hour | Investigate systemic issue |
