# SmartBerth AI - Berth Allocation Decision Knowledge

**Purpose:** Domain knowledge for berth allocation recommendations

---

## 1. BERTH-VESSEL COMPATIBILITY MATRIX

### 1.1 JNPT Berth Capabilities

| Berth Code | Max LOA | Max Beam | Max Draft | Type | Cranes | Best For |
|------------|---------|----------|-----------|------|--------|----------|
| NSFT-B01 | 215m | 40m | 13.0m | Container | 3 | Medium containers |
| NSFT-B02 | 215m | 40m | 13.0m | Container | 3 | Medium containers |
| NSFT-B03 | 215m | 40m | 13.0m | Container | 3 | Medium containers |
| NSICT-B01 | 280m | 45m | 12.0m | Container | 4 | Large containers |
| NSICT-B02 | 285m | 45m | 12.0m | Container | 4 | Large containers |
| NSIGT-B01 | 320m | 52m | 15.5m | Container | 4 | ULCVs, deep draft |
| GTI-B01 | 340m | 48m | 13.1m | Container | 6 | Large + very large |
| GTI-B02 | 340m | 48m | 13.1m | Container | 5 | Large + very large |
| BMCT-B01 | 320m | 52m | 16.0m | Container | 4 | ULCVs |
| BMCT-B02 | 320m | 52m | 16.0m | Container | 4 | ULCVs |
| BMCT-B03 | 320m | 52m | 16.0m | Container | 4 | ULCVs |
| BMCT-B04 | 320m | 52m | 16.0m | Container | 4 | ULCVs |
| BMCT-B05 | 320m | 52m | 16.0m | Container | 4 | ULCVs |
| BMCT-B06 | 320m | 52m | 16.0m | Container | 4 | ULCVs |
| SWDT-B01 | 300m | 32m | 9.0m | General | 1 | Break bulk, general |
| SWDT-B02 | 230m | 28m | 6.5m | General | 0 | Coastal cargo |
| LCJ-B01 | 185m | 35m | 11.0m | Tanker | 0 | Petroleum |
| LCJ-B02 | 170m | 32m | 10.0m | Tanker | 0 | Chemicals |

### 1.2 Vessel Category → Berth Mapping

| Vessel Category | LOA | Draft | Suitable Berths |
|-----------------|-----|-------|-----------------|
| ULCV (24,000+ TEU) | 400m | 16.0m+ | **NONE** (exceeds all JNPT limits) |
| ULCV (20,000 TEU) | 400m | 16.0m | BMCT-B01 to B06 (with tide) |
| Large Container | 366m | 14-15m | BMCT, NSIGT (draft limits) |
| Very Large Container | 334-366m | 14-15m | GTI, BMCT, NSIGT |
| Medium Container | 261-335m | 12-14m | NSICT, GTI, BMCT |
| Small Container | 170-294m | 10-13m | NSFT, NSICT, GTI |
| Feeder | <200m | <10m | NSFT, SWDT |
| Bulk Carrier | 150-292m | 8-18m | SWDT (if draft allows) |
| Tanker | 150-200m | 10-12m | LCJ-B01, LCJ-B02 |
| General Cargo | <200m | <9m | SWDT-B01, SWDT-B02 |

---

## 2. ALLOCATION DECISION LOGIC

### 2.1 Step-by-Step Process

```
1. FILTER: Remove berths that violate hard constraints
   ├── Physical fit (LOA, beam, draft)
   ├── Berth type compatibility
   ├── Berth active status
   └── Maintenance conflicts

2. CHECK AVAILABILITY: For remaining berths
   ├── Current occupancy
   ├── Scheduled arrivals
   └── Buffer time requirements

3. SCORE: Rank feasible berths
   ├── Waiting time impact
   ├── Crane availability
   ├── Historical performance
   └── Priority alignment

4. RECOMMEND: Top 3 options with explanations
```

### 2.2 Filtering Logic (Python)
```python
def filter_feasible_berths(vessel, all_berths, context):
    """
    Return only berths that satisfy all hard constraints
    """
    feasible = []
    
    for berth in all_berths:
        # Physical constraints
        if vessel.loa > berth.max_loa:
            continue
        if vessel.beam > berth.max_beam:
            continue
        if vessel.draft > berth.max_draft:
            continue
        
        # Berth status
        if not berth.is_active:
            continue
        
        # Type compatibility
        if not is_type_compatible(vessel.type, berth.type):
            continue
        
        # Maintenance check
        if has_maintenance_conflict(berth, context.eta, context.etd):
            continue
        
        feasible.append(berth)
    
    return feasible
```

---

## 3. SCORING ALGORITHM

### 3.1 Multi-Factor Scoring
```python
def calculate_berth_score(vessel, berth, context):
    """
    Calculate overall suitability score (0-100)
    """
    scores = {}
    
    # Factor 1: Physical margin (20 points max)
    loa_margin = (berth.max_loa - vessel.loa) / berth.max_loa
    draft_margin = (berth.max_draft - vessel.draft) / berth.max_draft
    scores['physical'] = min(20, (loa_margin + draft_margin) * 10)
    
    # Factor 2: Waiting time (25 points max)
    wait_hours = get_wait_time(berth, context.eta)
    if wait_hours == 0:
        scores['waiting'] = 25
    elif wait_hours <= 2:
        scores['waiting'] = 20
    elif wait_hours <= 6:
        scores['waiting'] = 15
    elif wait_hours <= 12:
        scores['waiting'] = 10
    else:
        scores['waiting'] = max(0, 25 - wait_hours)
    
    # Factor 3: Crane efficiency (20 points max)
    optimal_cranes = estimate_optimal_cranes(vessel.cargo_volume)
    crane_ratio = min(1, berth.cranes / optimal_cranes)
    scores['cranes'] = crane_ratio * 20
    
    # Factor 4: Type match (15 points max)
    if vessel.type == berth.type:
        scores['type_match'] = 15
    elif is_compatible(vessel.type, berth.type):
        scores['type_match'] = 10
    else:
        scores['type_match'] = 0
    
    # Factor 5: Historical success (10 points max)
    history = get_history(vessel.id, berth.id)
    if history and history.success_rate >= 0.9:
        scores['history'] = 10
    elif history:
        scores['history'] = history.success_rate * 10
    else:
        scores['history'] = 5  # Neutral
    
    # Factor 6: Priority alignment (10 points max)
    if vessel.priority == 1 and berth.handles_priority:
        scores['priority'] = 10
    elif vessel.priority <= 2:
        scores['priority'] = 7
    else:
        scores['priority'] = 5
    
    total = sum(scores.values())
    return total, scores
```

### 3.2 Score Interpretation
| Score Range | Interpretation | Recommendation |
|-------------|----------------|----------------|
| 80-100 | Excellent fit | Primary recommendation |
| 60-79 | Good fit | Alternative option |
| 40-59 | Acceptable | Use if no better options |
| < 40 | Poor fit | Avoid unless necessary |

---

## 4. CONFLICT DETECTION

### 4.1 Conflict Types

| Conflict Type | Detection Rule | Severity |
|---------------|----------------|----------|
| Time Overlap | Two vessels at same berth at same time | CRITICAL |
| Resource Clash | Same pilot/tug assigned to concurrent ops | HIGH |
| Tidal Conflict | Deep-draft vessel assigned to low-tide window | HIGH |
| Priority Violation | Lower priority vessel blocks higher priority | MEDIUM |
| Buffer Violation | < 30 min gap between vessels | LOW |

### 4.2 Conflict Resolution Strategies

**Time Overlap:**
1. Move earlier vessel's ETD earlier
2. Move later vessel's ETA later
3. Assign different berth

**Resource Clash:**
1. Stagger operations by 30+ minutes
2. Assign backup resources
3. Prioritize based on vessel priority

**Tidal Conflict:**
1. Delay arrival to next high tide
2. Assign to deeper berth (if available)
3. Partial loading to reduce draft

**Priority Violation:**
1. Swap berth assignments
2. Queue lower priority vessel at anchorage
3. Request priority override from operator

---

## 5. SPECIAL SCENARIOS

### 5.1 ULCV Handling (400m LOA, 16m+ Draft)
**Challenge:** Largest vessels (MSC Ivana, Ever Ace) exceed JNPT berth limits
**Solution:**
- These vessels CANNOT berth at JNPT under normal conditions
- Recommend lightering at anchorage to reduce draft
- Or redirect to deeper ports (if possible)

### 5.2 Peak Congestion (Queue > 10 vessels)
**Strategy:**
1. Extend operating hours
2. Prioritize high-priority vessels
3. Consider anchorage-based cargo operations
4. Optimize turnaround time

### 5.3 Weather Disruption
**Strategy:**
1. Hold vessels at anchorage until conditions improve
2. Recalculate all ETAs with weather impact
3. Re-optimize berth assignments post-disruption
4. Notify all affected stakeholders

### 5.4 Emergency Priority
**Handling:**
1. Government/military vessels get absolute priority
2. Emergency cargo (medical, disaster relief) prioritized
3. Bump lower priority vessels if necessary
4. Document all priority overrides

---

## 6. RECOMMENDATION TEMPLATES

### 6.1 Primary Recommendation
```
**RECOMMENDED: {berth_name} ({berth_code})**

Score: {score}/100
Expected Wait: {wait_hours} hours
Available from: {available_time}

Reasons:
- {reason_1}
- {reason_2}
- {reason_3}
```

### 6.2 Alternative Options
```
**ALTERNATIVE 1: {berth_name}**
Score: {score}/100 | Wait: {hours} hrs
Trade-off: {trade_off_description}

**ALTERNATIVE 2: {berth_name}**
Score: {score}/100 | Wait: {hours} hrs
Trade-off: {trade_off_description}
```

### 6.3 No Feasible Berth
```
**NO SUITABLE BERTH AVAILABLE**

Reason: {constraint_violation}

Recommended Actions:
1. Queue vessel at anchorage
2. Next available berth: {berth} at {time}
3. Alternative: {alternative_suggestion}
```

---

## 7. DWELL TIME ESTIMATION

### 7.1 Factors Affecting Dwell Time
- Cargo volume (TEU or MT)
- Number of cranes available
- Crane productivity (moves/hour)
- Weather conditions during operation
- Labor shift patterns

### 7.2 Dwell Time Formula
```python
def estimate_dwell_time(vessel, berth, weather):
    """
    Estimate hours at berth
    """
    # Base moves per hour per crane
    base_productivity = 25  # TEU/hour/crane for modern cranes
    
    # Weather adjustment
    weather_factor = get_weather_productivity_factor(weather)
    adjusted_productivity = base_productivity * weather_factor
    
    # Total moves required
    total_moves = vessel.cargo_volume * 1.8  # Load + discharge
    
    # Hours for cargo ops
    cargo_hours = total_moves / (berth.cranes * adjusted_productivity)
    
    # Add buffer for berthing/unberthing
    buffer_hours = 2  # Pilot, tugs, lines
    
    return cargo_hours + buffer_hours
```

### 7.3 Typical Dwell Times by Vessel Size
| Vessel Size | TEU | Cranes | Typical Dwell |
|-------------|-----|--------|---------------|
| ULCV | 20,000+ | 4-6 | 24-36 hours |
| Large | 10,000-20,000 | 4 | 18-24 hours |
| Medium | 5,000-10,000 | 3 | 12-18 hours |
| Small | <5,000 | 2-3 | 6-12 hours |
| Feeder | <2,000 | 1-2 | 4-8 hours |

---

## 8. OPERATOR OVERRIDE HANDLING

### 8.1 When Operators May Override
- Customer preference (contractual berth)
- Operational efficiency (gang availability)
- Emergency situations
- Strategic business reasons

### 8.2 Override Validation
```python
def validate_override(operator_choice, ai_recommendation):
    """
    Check if override is valid and warn of risks
    """
    warnings = []
    
    # Check hard constraints
    violations = check_hard_constraints(vessel, operator_choice)
    if violations:
        return REJECT, "Hard constraint violation: " + str(violations)
    
    # Check score difference
    ai_score = ai_recommendation.score
    override_score = calculate_score(vessel, operator_choice)
    if override_score < ai_score - 20:
        warnings.append(f"Score drop: {ai_score} → {override_score}")
    
    # Check waiting time impact
    ai_wait = ai_recommendation.wait_time
    override_wait = calculate_wait(operator_choice)
    if override_wait > ai_wait + 2:
        warnings.append(f"Additional wait: +{override_wait - ai_wait} hours")
    
    return ALLOW_WITH_WARNINGS, warnings
```

---

*End of Berth Allocation Decision Knowledge*
