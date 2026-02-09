# SmartBerth AI - Vessel Tracking & AIS Data Knowledge

**Document Version:** 2.0  
**Last Updated:** February 2026  
**Purpose:** Comprehensive domain knowledge for vessel tracking, AIS interpretation, and movement analysis  
**Priority:** CRITICAL — Foundation service for all SmartBerth operations

---

## 1. AIS (Automatic Identification System) Data Interpretation

### 1.1 AIS Message Types
AIS provides real-time vessel position, course, speed, and identity data. Key fields:
- **MMSI**: Maritime Mobile Service Identity (9-digit unique radio identifier)
- **IMO Number**: International Maritime Organization 7-digit permanent vessel identifier
- **SOG (Speed Over Ground)**: Vessel speed in knots as measured by GPS
- **COG (Course Over Ground)**: True bearing of vessel movement in degrees (0-360)
- **Heading**: Direction the vessel bow is pointing (may differ from COG due to current/wind)
- **Rate of Turn (ROT)**: Angular velocity indicating turning maneuver
- **Navigation Status**: Encoded status per ITU standard

### 1.2 Navigation Status Codes (ITU Standard)
| Code | Status | Meaning |
|------|--------|---------|
| 0 | Under way using engine | Normal powered transit |
| 1 | At anchor | Vessel anchored at designated area |
| 2 | Not under command | Unable to maneuver (mechanical failure) |
| 3 | Restricted maneuverability | Limited movement (dredging, diving, etc.) |
| 4 | Constrained by draft | Vessel draft exceeds safe transit limits |
| 5 | Moored | Secured alongside berth |
| 6 | Aground | Vessel has run aground |
| 7 | Engaged in fishing | Active fishing operations |
| 8 | Under way sailing | Using wind power, no engine |
| 15 | Not defined / Default | Status not set by vessel |

### 1.3 AIS Data Quality Considerations
- AIS update frequency varies: every 2-10 seconds for fast-moving vessels, every 3 minutes for anchored vessels
- Position accuracy depends on GPS quality (typically ±10m)
- Some vessels may have intermittent AIS transmission (requires interpolation)
- Stale data alert: >30 minutes without update triggers WARNING
- Lost signal: >60 minutes triggers CRITICAL alert

---

## 2. Vessel Phase Detection

### 2.1 Approach Phases
SmartBerth classifies vessel approach into phases based on distance to port:

| Phase | Distance to Port | Typical Speed | Description |
|-------|-----------------|---------------|-------------|
| APPROACHING | >50 NM | 12-20 knots | Open sea transit toward port |
| NEAR_PORT | 10-50 NM | 8-14 knots | Approaching pilot boarding area |
| PILOT_BOARDING | 3-10 NM | 6-10 knots | At pilot station, awaiting pilot |
| ANCHORED | Variable | 0-1 knots | Waiting at anchorage for berth |
| MANEUVERING | <3 NM | 3-6 knots | Under pilot, navigating channel |
| BERTHING | <0.5 NM | 0-3 knots | Final approach with tug assistance |
| AT_BERTH | 0 NM | 0 knots | Moored alongside berth |
| UNBERTHING | <0.5 NM | 0-3 knots | Departing berth with tug assistance |
| DEPARTING | <10 NM | 6-14 knots | Outbound transit, releasing pilot |

### 2.2 Phase Transition Rules
- Phase transitions trigger alerts and schedule updates
- Each phase transition verified by: distance threshold + speed + navigation status
- Unexpected phase transitions (e.g., APPROACHING → ANCHORED without NEAR_PORT) flag anomaly

---

## 3. Movement Analysis

### 3.1 Speed Trend Analysis
Speed trends computed every 5 minutes from AIS position history:
- **INCREASING**: Average speed increasing (vessel acceleration)
- **STABLE**: Speed variation < 2 knots over 15 minutes
- **DECREASING**: Average speed decreasing (vessel decelerating or stopping)
- **STOPPED**: Speed < 0.5 knots for > 10 minutes

### 3.2 Course Deviation Detection
- Expected route calculated from declared destination and current position
- Deviation threshold: > 30° from expected course for > 10 minutes → alert
- Cause analysis: weather avoidance, traffic separation, equipment failure

### 3.3 Anomaly Detection Criteria
| Anomaly Type | Trigger | Severity |
|---|---|---|
| Unexpected Stop | Speed drops to 0 outside anchorage/berth | WARNING |
| Speed Surge | >5 knots increase in 10 minutes | INFO |
| Course Reversal | >120° course change | WARNING |
| AIS Gap | No position update for >30 minutes | WARNING |
| AIS Lost | No position update for >60 minutes | CRITICAL |
| Zone Violation | Vessel enters restricted area | CRITICAL |
| Dragging Anchor | Anchored vessel position drift >100m | HIGH |

---

## 4. Distance and Time Calculations

### 4.1 Distance to Port Formula
The Haversine formula calculates great-circle distance between vessel position and port reference point:

```
distance_nm = R × c
where:
  R = 3440.065 (Earth radius in nautical miles)
  a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
  c = 2 × arcsin(√a)
```

### 4.2 Simple ETA Estimate from Tracking
```
estimated_hours = distance_nm / speed_over_ground
estimated_arrival = current_time + estimated_hours
```
Note: This is the simplest estimate. The ML-based ETA prediction model adds weather, traffic, historical pattern, and port congestion corrections.

### 4.3 Position Interpolation
Between AIS updates, vessel position can be interpolated:
```
interpolated_lat = last_lat + (speed × cos(course) × elapsed_time / 60)
interpolated_lon = last_lon + (speed × sin(course) × elapsed_time / (60 × cos(last_lat)))
```

---

## 5. Alert Thresholds for Vessel Tracking

| Alert Type | Threshold | Severity | Auto-Dismiss |
|---|---|---|---|
| Position Update | New AIS position received | DEBUG | 5 seconds |
| Speed Change | ΔSpeed > 3 knots | INFO | 5 minutes |
| Course Deviation | Δ > 30° from expected | WARNING | None |
| Unexpected Stop | Speed = 0 outside designated area | WARNING | None |
| Phase Transition | Vessel enters new phase | INFO | 2 minutes |
| Port Zone Entry | Vessel crosses port approach zone | INFO | 10 minutes |
| Pilot Station Arrival | Vessel within 5 NM of pilot station | INFO | None |
| AIS Data Stale | No update > 30 minutes | WARNING | On reception |
| AIS Signal Lost | No update > 60 minutes | CRITICAL | On reception |

---

## 6. Integration Points

### 6.1 Vessel Tracking feeds these downstream services:
1. **ETA Prediction** — AIS positions, speed, course feed into ML model
2. **Berth Allocation** — Predicted arrival drives berth scheduling
3. **Conflict Detection** — Position changes trigger schedule re-evaluation
4. **Digital Twin** — Live vessel positions rendered on port map
5. **Real-Time Alerts** — Every tracking event evaluated against alert rules
6. **Resource Planning** — Phase transitions trigger pilot/tug scheduling

### 6.2 Required Vessel Data Fields
| Field | Source | Update Frequency |
|---|---|---|
| Position (lat/lng) | AIS | 2-30 seconds |
| Speed Over Ground | AIS | 2-30 seconds |
| Course Over Ground | AIS | 2-30 seconds |
| Heading | AIS | 2-30 seconds |
| Navigation Status | AIS | On change |
| Distance to Port | Calculated | On position update |
| Phase | Calculated | On position update |
| Speed Trend | Calculated | Every 5 minutes |
| Course Deviation | Calculated | Every 5 minutes |
