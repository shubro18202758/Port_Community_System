# SmartBerth AI - Constraint Rules Reference

**Purpose:** Detailed constraint rules for berth allocation validation

---

## HARD CONSTRAINTS - PHYSICAL FIT

### HC-01: Vessel LOA vs Berth Length
```python
# Rule: Vessel must physically fit in berth
if vessel.loa > berth.max_loa:
    return VIOLATION("Vessel LOA {vessel.loa}m exceeds berth maximum {berth.max_loa}m")
```

**JNPT Berth LOA Limits:**
- NSFT Berths: 215m maximum
- NSICT Berths: 280-285m maximum
- NSIGT: 320m maximum (deep water)
- GTI Berths: 340m maximum
- BMCT Berths: 320m maximum
- Shallow Water: 230-300m maximum
- Liquid Cargo: 170-185m maximum

### HC-02: Vessel Draft vs Berth Depth
```python
# Rule: Vessel draft must not exceed berth maximum draft
if vessel.draft > berth.max_draft:
    return VIOLATION("Vessel draft {vessel.draft}m exceeds berth limit {berth.max_draft}m")
```

**JNPT Draft Limits:**
- BMCT Deep Water: 16.0m (handles ULCVs)
- NSIGT: 15.5m (deep water)
- GTI: 13.1m
- NSFT/NSICT: 12.0-13.0m
- Shallow Water: 6.5-9.0m
- Liquid Cargo: 10.0-11.0m

### HC-03: Vessel Beam vs Berth Width
```python
# Rule: Vessel beam must fit within berth constraints
if vessel.beam > berth.max_beam:
    return VIOLATION("Vessel beam {vessel.beam}m exceeds berth limit {berth.max_beam}m")
```

**JNPT Beam Limits:**
- BMCT/NSIGT: 52m (handles 61.5m ULCVs with special approval)
- GTI: 48m
- NSICT: 45m
- NSFT: 40m
- Shallow Water: 28-32m

---

## HARD CONSTRAINTS - TEMPORAL

### HC-04: No Time Overlap
```python
# Rule: Berth can only serve one vessel at a time
def check_overlap(berth, new_start, new_end):
    for existing in berth.schedules:
        if not (new_end <= existing.start or new_start >= existing.end):
            return VIOLATION("Overlap with vessel {existing.vessel}")
    return OK
```

### HC-05: Berth Must Be Active
```python
# Rule: Cannot assign to inactive berths
if not berth.is_active:
    return VIOLATION("Berth {berth.code} is not active")
```

### HC-06: No Maintenance Conflict
```python
# Rule: Cannot use berth during maintenance window
for maintenance in berth.maintenance_schedule:
    if eta >= maintenance.start and eta <= maintenance.end:
        return VIOLATION("Berth under maintenance from {start} to {end}")
```

---

## HARD CONSTRAINTS - ENVIRONMENTAL

### HC-07: Tidal Window for Deep-Draft Vessels
```python
# Rule: Deep-draft vessels must arrive during high tide
if vessel.draft > 14.0:  # Deep-draft threshold for JNPT
    tide_at_eta = get_tide_level(eta)
    ukc = tide_at_eta + channel_depth - vessel.draft - safety_margin
    if ukc < 1.0:
        return VIOLATION("Insufficient UKC {ukc}m. Need high tide window.")
```

### HC-08: Weather Safety
```python
# Rule: No operations during severe weather
weather = get_weather_at(eta)
if weather.wind_speed > 40:
    return VIOLATION("Wind speed {weather.wind_speed} km/h exceeds safe limit")
if weather.visibility < 1.0:
    return VIOLATION("Visibility {weather.visibility} km below minimum")
if weather.wave_height > 2.0:
    return VIOLATION("Wave height {weather.wave_height}m exceeds safe limit")
```

---

## HARD CONSTRAINTS - RESOURCES

### HC-09: Pilot Availability
```python
# Rule: Pilot must be available for berthing
pilots = get_available_pilots(eta, vessel.certification_required)
if not pilots:
    return VIOLATION("No certified pilot available at ETA")
```

### HC-10: Tug Availability
```python
# Rule: Required tugs must be available
tugs_required = get_tug_requirement(vessel.loa, vessel.gt)
tugs_available = get_available_tugs(eta)
if tugs_available < tugs_required:
    return VIOLATION("Only {available} tugs available, {required} needed")
```

---

## SOFT CONSTRAINTS - OPTIMIZATION WEIGHTS

### SC-01: Berth Type Match (Weight: 0.8)
```python
# Prefer berths matching vessel type
def berth_type_score(vessel, berth):
    if vessel.type == berth.type:
        return 1.0
    elif is_compatible(vessel.type, berth.type):
        return 0.5
    else:
        return 0.0
```

### SC-02: Minimize Waiting Time (Weight: 0.9)
```python
# Prioritize assignments that minimize wait
def waiting_score(eta, berth_free_time):
    wait_hours = (berth_free_time - eta).hours
    if wait_hours <= 0:
        return 1.0  # No wait
    elif wait_hours <= 2:
        return 0.8
    elif wait_hours <= 6:
        return 0.5
    else:
        return max(0, 1 - (wait_hours / 24))
```

### SC-03: Priority Respect (Weight: 0.7)
```python
# Higher priority vessels get preference
def priority_score(vessel, competing_vessels):
    if vessel.priority == 1:  # High priority
        return 1.0
    elif vessel.priority == 2:
        return 0.7
    else:
        return 0.5
```

### SC-04: Crane Availability (Weight: 0.6)
```python
# Prefer berths with more cranes for faster turnaround
def crane_score(berth, vessel_teu):
    optimal_cranes = math.ceil(vessel_teu / 2000)  # Rule of thumb
    available = berth.number_of_cranes
    if available >= optimal_cranes:
        return 1.0
    else:
        return available / optimal_cranes
```

### SC-05: Historical Performance (Weight: 0.5)
```python
# Prefer berths vessel has successfully used before
def history_score(vessel, berth):
    history = get_vessel_history(vessel.id, berth.id)
    if history and history.avg_performance_score >= 0.8:
        return 1.0
    elif history:
        return history.avg_performance_score
    else:
        return 0.5  # Neutral for new assignments
```

### SC-06: Minimize Repositioning (Weight: 0.4)
```python
# Avoid moving vessels from already assigned berths
def reposition_score(current_assignment):
    if current_assignment is None:
        return 1.0  # New assignment, no penalty
    else:
        return 0.2  # Penalty for repositioning
```

### SC-07: Even Distribution (Weight: 0.3)
```python
# Balance load across berths
def distribution_score(berth, all_berths):
    utilization = berth.current_utilization
    avg_utilization = mean(b.current_utilization for b in all_berths)
    if utilization <= avg_utilization:
        return 1.0
    else:
        return max(0.5, 1 - (utilization - avg_utilization) / 0.5)
```

### SC-08: Buffer Time (Weight: 0.5)
```python
# Maintain 30-minute gap between vessels
def buffer_score(new_eta, previous_etd):
    gap_minutes = (new_eta - previous_etd).minutes
    if gap_minutes >= 30:
        return 1.0
    elif gap_minutes >= 15:
        return 0.7
    else:
        return 0.3
```

---

## SCORING FORMULA

```python
def calculate_berth_score(vessel, berth, context):
    """Calculate overall score for vessel-berth assignment"""
    
    # Check hard constraints first
    hard_violations = check_hard_constraints(vessel, berth, context)
    if hard_violations:
        return 0, hard_violations  # Not feasible
    
    # Calculate weighted soft constraint scores
    scores = {
        'berth_type': (berth_type_score(vessel, berth), 0.8),
        'waiting': (waiting_score(vessel.eta, berth.next_free), 0.9),
        'priority': (priority_score(vessel, context.queue), 0.7),
        'cranes': (crane_score(berth, vessel.cargo_volume), 0.6),
        'history': (history_score(vessel, berth), 0.5),
        'reposition': (reposition_score(context.current_assignment), 0.4),
        'distribution': (distribution_score(berth, context.all_berths), 0.3),
        'buffer': (buffer_score(vessel.eta, berth.last_departure), 0.5),
    }
    
    # Weighted average
    total_weight = sum(w for _, w in scores.values())
    weighted_sum = sum(s * w for s, w in scores.values())
    final_score = weighted_sum / total_weight
    
    return final_score, None
```

---

## CONSTRAINT VALIDATION SEQUENCE

1. **Physical Constraints** (HC-01 to HC-03)
   - Check immediately - eliminates incompatible berths

2. **Temporal Constraints** (HC-04 to HC-06)
   - Check against schedule - finds available time slots

3. **Environmental Constraints** (HC-07 to HC-08)
   - Check at ETA - may require time adjustment

4. **Resource Constraints** (HC-09 to HC-10)
   - Check availability - may trigger resource scheduling

5. **Soft Constraint Scoring**
   - Only for feasible combinations
   - Used to rank alternatives

---

*End of Constraint Rules Reference*
