# Resource Allocation Strategy - Best Practices

**Document Type**: Best Practices - Resource Management
**Source**: Port Operations Management, Industry Standards
**Category**: Best Practices

---

## Resource Allocation Priority

### 1. Crane Assignment Strategy
**From RESOURCES table (ResourceType = 'Crane')**

**Priority Factors**:
1. Vessel priority (Priority 1 > Priority 2 > Priority 3)
2. Cargo volume (larger vessels need more cranes)
3. Time sensitivity (window vessels, perishable cargo)
4. Crane capacity match (65-ton cranes for heavy containers)

**Query Pattern**:
```sql
SELECT
    r.ResourceId,
    r.ResourceName,
    r.Capacity,
    r.IsAvailable
FROM RESOURCES r
WHERE r.ResourceType = 'Crane'
    AND r.IsAvailable = 1
    AND r.Capacity >= @RequiredCapacity
    AND NOT EXISTS (
        SELECT 1 FROM RESOURCE_ALLOCATION ra
        WHERE ra.ResourceId = r.ResourceId
            AND ra.Status = 'Allocated'
            AND @RequestedStart BETWEEN ra.AllocatedFrom AND ra.AllocatedTo
    )
ORDER BY r.Capacity ASC;  -- Prefer smallest sufficient crane (save high-capacity for large vessels)
```

**Best Practice**: Assign smallest crane that meets requirements. Reserve high-capacity cranes (65-ton) for large containers requiring heavy lift.

---

### 2. Pilot Assignment Strategy
**From RESOURCES table (ResourceType = 'Pilot')**

**Certification Matching**:
```sql
SELECT
    r.ResourceId,
    r.ResourceName,
    r.Certifications,
    r.IsAvailable
FROM RESOURCES r
WHERE r.ResourceType = 'Pilot'
    AND r.IsAvailable = 1
    AND (
        (@VesselDraft > 12 AND r.Certifications LIKE '%Deep Draft%')
        OR (@VesselType = 'Tanker' AND r.Certifications LIKE '%Tanker%')
        OR (@VesselDraft <= 12 AND r.Certifications LIKE '%Class%')
    )
ORDER BY r.ResourceId;
```

**Best Practice**: Match pilot certification to vessel requirements. Deep-draft vessels (>12m) require Class 1 pilots. Tankers require specialized tanker certification.

---

### 3. Tugboat Assignment Strategy
**From RESOURCES table (ResourceType = 'Tugboat')**

**Bollard Pull Calculation**:
```python
def calculate_tugboat_requirements(vessel_gt, vessel_loa):
    """
    Determine tugboat requirements based on vessel size
    """
    if vessel_gt < 50000:
        return {"count": 1, "min_bollard_pull": 50}
    elif vessel_gt < 100000:
        return {"count": 2, "min_bollard_pull": 60}
    else:
        return {"count": 3, "min_bollard_pull": 65}
```

**Query Pattern**:
```sql
SELECT
    r.ResourceId,
    r.ResourceName,
    r.BollardPull,
    r.IsAvailable
FROM RESOURCES r
WHERE r.ResourceType = 'Tugboat'
    AND r.IsAvailable = 1
    AND r.BollardPull >= @RequiredBollardPull
ORDER BY r.BollardPull ASC;  -- Prefer smallest sufficient tugboat
```

**Best Practice**: Assign tugboats based on vessel GT and LOA. Large vessels (GT >100K) require 3 tugboats with 65-ton minimum bollard pull.

---

### 4. Labor Gang Allocation
**From RESOURCES table (ResourceType = 'StevedoreGang')**

**Shift Optimization**:
- Day shift (06:00-14:00): Highest productivity, 86% utilization
- Evening shift (14:00-22:00): Medium productivity, 78% utilization
- Night shift (22:00-06:00): Lowest productivity, 64% utilization

**Best Practice**: Schedule high-priority vessels during day shift for maximum productivity. Use night shift for low-priority or slow cargo operations.

**Avoid Shift Handover Times**:
- 05:30-06:30 (night→day)
- 13:30-14:30 (day→evening)
- 21:30-22:30 (evening→night)

**Query Example**:
```sql
SELECT
    r.ResourceId,
    r.ResourceName,
    r.ShiftPattern,
    r.Capacity
FROM RESOURCES r
WHERE r.ResourceType = 'StevedoreGang'
    AND r.IsAvailable = 1
    AND r.ShiftPattern = 'Day'  -- Prefer day shift
ORDER BY r.Capacity DESC;
```

---

## Resource Conflict Prevention

**Check Availability Before Assignment**:
```sql
-- Detect resource conflicts
SELECT
    r.ResourceName,
    ra1.ScheduleId AS CurrentSchedule,
    ra1.AllocatedFrom AS CurrentStart,
    ra1.AllocatedTo AS CurrentEnd,
    @NewScheduleId AS RequestedSchedule,
    @RequestedStart AS RequestedStart,
    @RequestedEnd AS RequestedEnd
FROM RESOURCE_ALLOCATION ra1
JOIN RESOURCES r ON ra1.ResourceId = r.ResourceId
WHERE ra1.Status = 'Allocated'
    AND ra1.ResourceId = @RequestedResourceId
    AND (
        (@RequestedStart BETWEEN ra1.AllocatedFrom AND ra1.AllocatedTo)
        OR (@RequestedEnd BETWEEN ra1.AllocatedFrom AND ra1.AllocatedTo)
        OR (ra1.AllocatedFrom BETWEEN @RequestedStart AND @RequestedEnd)
    );
```

**Best Practice**: Always query RESOURCE_ALLOCATION before assigning resources. Detect conflicts early (48+ hours in advance) and generate alternatives.

---

**Keywords**: resource allocation, crane assignment, pilot allocation, tugboat requirements, labor gangs, shift optimization, RESOURCES table, RESOURCE_ALLOCATION, bollard pull, certifications, best practices
