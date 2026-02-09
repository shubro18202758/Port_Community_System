# SmartBerth AI - ETA Prediction Knowledge

**Purpose:** Domain knowledge for ETA prediction model

---

## 1. ETA CALCULATION METHODOLOGY

### 1.1 Haversine Distance Formula
The Haversine formula calculates the great-circle distance between two points on Earth:

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate distance in nautical miles between two coordinates
    """
    R = 3440.065  # Earth radius in nautical miles
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c  # Distance in nautical miles
```

### 1.2 Base ETA Calculation
```python
def calculate_base_eta(vessel_position, port_position, vessel_speed):
    """
    Calculate ETA based on current position and speed
    """
    distance_nm = haversine_distance(
        vessel_position.lat, vessel_position.lon,
        port_position.lat, port_position.lon
    )
    
    if vessel_speed > 0:
        travel_hours = distance_nm / vessel_speed
        base_eta = current_time + timedelta(hours=travel_hours)
    else:
        base_eta = None  # Vessel stationary
    
    return base_eta, distance_nm
```

---

## 2. WEATHER IMPACT FACTORS

### 2.1 Wind Speed Impact
| Wind Speed (km/h) | Speed Reduction | Delay Factor |
|-------------------|-----------------|--------------|
| 0-15 | 0% | 1.00 |
| 15-25 | 5% | 1.05 |
| 25-35 | 10% | 1.10 |
| 35-45 | 15% | 1.15 |
| 45-55 | 25% | 1.25 |
| > 55 | 35-50% | 1.35-1.50 |

### 2.2 Wave Height Impact
| Wave Height (m) | Speed Reduction | Delay Factor |
|-----------------|-----------------|--------------|
| 0-1.0 | 0% | 1.00 |
| 1.0-2.0 | 5% | 1.05 |
| 2.0-3.0 | 10% | 1.10 |
| 3.0-4.0 | 20% | 1.20 |
| > 4.0 | 30%+ | 1.30+ |

### 2.3 Visibility Impact
| Visibility (km) | Speed Reduction | Notes |
|-----------------|-----------------|-------|
| > 5 | 0% | Normal operations |
| 3-5 | 5% | Reduced speed |
| 1-3 | 15% | Caution required |
| 0.5-1.0 | 30% | Pilotage may be suspended |
| < 0.5 | N/A | Navigation suspended |

### 2.4 Combined Weather Impact Formula
```python
def calculate_weather_impact(weather_data):
    """
    Calculate combined weather delay factor
    """
    wind_factor = get_wind_factor(weather_data.wind_speed)
    wave_factor = get_wave_factor(weather_data.wave_height)
    visibility_factor = get_visibility_factor(weather_data.visibility)
    
    # Combined impact (not additive, use worst case with adjustment)
    max_factor = max(wind_factor, wave_factor, visibility_factor)
    avg_factor = (wind_factor + wave_factor + visibility_factor) / 3
    
    # Weighted combination: 70% max, 30% average
    combined_factor = 0.7 * max_factor + 0.3 * avg_factor
    
    return combined_factor
```

---

## 3. VESSEL-SPECIFIC FACTORS

### 3.1 Vessel Size Impact
| Vessel Category | LOA (m) | Typical Speed (kn) | Approach Speed (kn) |
|-----------------|---------|-------------------|---------------------|
| ULCV | 366-400 | 18-22 | 8-10 |
| Large Container | 334-367 | 20-24 | 10-12 |
| Medium Container | 261-335 | 18-22 | 10-12 |
| Small Container | 170-294 | 15-20 | 8-10 |
| Bulk Carrier | 150-292 | 12-15 | 6-8 |
| Tanker | 150-200 | 12-14 | 5-7 |

### 3.2 Draft Impact on Speed
Deep-draft vessels (draft > 14m) may need to:
- Wait for high tide at channel entrance
- Reduce speed in shallow sections
- Use tidal windows for berthing

```python
def draft_delay_factor(vessel_draft, channel_depth, tide_level):
    """
    Calculate delay due to draft restrictions
    """
    ukc = channel_depth + tide_level - vessel_draft
    
    if ukc >= 2.0:
        return 1.0  # No delay
    elif ukc >= 1.0:
        return 1.1  # 10% delay for caution
    else:
        # Need to wait for better tide
        hours_to_high_tide = get_hours_to_high_tide()
        return 1.0 + (hours_to_high_tide / 24)  # Significant delay
```

---

## 4. PORT CONGESTION FACTORS

### 4.1 Queue Length Impact
| Vessels in Queue | Expected Wait (hrs) | Delay Factor |
|------------------|---------------------|--------------|
| 0-2 | 0-2 | 1.00 |
| 3-5 | 2-4 | 1.05 |
| 6-10 | 4-8 | 1.10 |
| > 10 | 8+ | 1.15+ |

### 4.2 Berth Availability
```python
def congestion_delay_factor(queue_length, available_berths, historical_turnover):
    """
    Estimate delay due to port congestion
    """
    avg_dwell_time = historical_turnover['avg_dwell_hours']
    vessels_ahead = queue_length
    
    expected_wait = (vessels_ahead / available_berths) * avg_dwell_time
    
    # Convert to delay factor
    if expected_wait <= 2:
        return 1.0
    else:
        return 1.0 + (expected_wait / 24) * 0.1
```

---

## 5. HISTORICAL PATTERN ANALYSIS

### 5.1 Vessel-Specific Patterns
Track historical performance for each vessel:
- Average deviation from declared ETA
- Typical speed patterns
- Common delay causes

```python
def vessel_history_adjustment(vessel_id):
    """
    Adjust ETA based on vessel's historical performance
    """
    history = get_vessel_history(vessel_id)
    
    if history and history.visit_count >= 3:
        avg_delay = history.avg_eta_deviation_hours
        stddev = history.eta_deviation_stddev
        
        # Adjust prediction toward historical average
        adjustment_hours = avg_delay * 0.7  # Weight historical data 70%
        return adjustment_hours
    
    return 0  # No adjustment for vessels without history
```

### 5.2 Route-Specific Patterns
Track common routes to JNPT:
- Singapore → JNPT: ~5-7 days
- Colombo → JNPT: ~2-3 days
- Dubai → JNPT: ~2 days
- China → JNPT: ~10-14 days

---

## 6. CONFIDENCE SCORING

### 6.1 Confidence Factors
| Factor | High Confidence | Medium Confidence | Low Confidence |
|--------|-----------------|-------------------|----------------|
| Distance to port | < 100 nm | 100-500 nm | > 500 nm |
| AIS data freshness | < 1 hr | 1-6 hrs | > 6 hrs |
| Weather stability | Clear forecast | Variable | Storm warning |
| Vessel history | 5+ visits | 1-4 visits | First visit |
| Speed consistency | Stable | Varying | Erratic |

### 6.2 Confidence Calculation
```python
def calculate_eta_confidence(vessel, weather, distance, ais_age):
    """
    Calculate confidence score (0-100%)
    """
    scores = []
    
    # Distance factor (closer = higher confidence)
    if distance < 50:
        scores.append(95)
    elif distance < 100:
        scores.append(85)
    elif distance < 300:
        scores.append(70)
    else:
        scores.append(50)
    
    # AIS freshness factor
    if ais_age.minutes < 15:
        scores.append(95)
    elif ais_age.minutes < 60:
        scores.append(80)
    elif ais_age.hours < 6:
        scores.append(60)
    else:
        scores.append(40)
    
    # Weather factor
    if weather.condition == 'Clear':
        scores.append(90)
    elif weather.condition in ['Cloudy', 'Light Rain']:
        scores.append(75)
    else:
        scores.append(50)
    
    # Historical factor
    history_count = get_visit_count(vessel.id)
    if history_count >= 5:
        scores.append(90)
    elif history_count >= 1:
        scores.append(70)
    else:
        scores.append(60)
    
    # Weighted average
    return int(sum(scores) / len(scores))
```

---

## 7. ETA UPDATE TRIGGERS

### 7.1 Automatic Updates
- New AIS position received (every 5-15 min)
- Weather forecast update (hourly)
- Tidal data update (every 6 hours)

### 7.2 Re-calculation Thresholds
| Change Type | Threshold | Action |
|-------------|-----------|--------|
| Speed change | > 2 knots | Recalculate ETA |
| Course change | > 15 degrees | Recalculate ETA |
| Weather change | Condition change | Apply new factor |
| Queue change | +/- 3 vessels | Recalculate delay |

---

## 8. JNPT-SPECIFIC PARAMETERS

### 8.1 Port Coordinates
- Latitude: 18.9453°N
- Longitude: 72.9400°E

### 8.2 Approach Sequence
1. **Pilot Station:** 10 nm from port
2. **Anchorage Alpha:** 5 nm from port
3. **Channel Entry:** 3 nm from berths
4. **Berth Arrival:** 0 nm

### 8.3 Typical Approach Times
| Segment | Distance | Typical Time |
|---------|----------|--------------|
| 100 nm out → Pilot Station | 90 nm | 5-6 hours |
| Pilot Station → Anchorage | 5 nm | 30 min |
| Anchorage → Channel Entry | 2 nm | 15 min |
| Channel → Berth | 3-8 nm | 30-60 min |

---

## 9. EXPLANATION TEMPLATES

### 9.1 ETA Increase Explanations
- "ETA delayed by {hours} hours due to high wind speed ({speed} km/h) in the approach area"
- "Vessel reduced speed from {old} to {new} knots, adding {hours} hours to ETA"
- "Weather deterioration expected - rain and reduced visibility forecast"
- "Port congestion with {n} vessels in queue - expected wait time: {hours} hours"
- "Deep draft ({draft}m) requires high tide window - next available at {time}"

### 9.2 ETA Decrease Explanations
- "Vessel increased speed to {speed} knots, reducing ETA by {hours} hours"
- "Weather conditions improved - clear skies and calm seas"
- "Queue reduced - berth becoming available earlier than expected"
- "Favorable current (+{knots} knots effective speed)"

### 9.3 Confidence Explanations
- "High confidence (>85%): Vessel within 100nm, stable speed, good weather"
- "Medium confidence (60-85%): Variable conditions, moderate distance"
- "Low confidence (<60%): Far from port, weather uncertainty, first visit"

---

*End of ETA Prediction Knowledge*
