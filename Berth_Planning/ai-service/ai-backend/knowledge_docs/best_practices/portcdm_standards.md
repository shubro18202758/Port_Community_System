# PortCDM Standards - International Best Practices

**Document Type**: Best Practices - Industry Standards
**Source**: Port Collaborative Decision Making (PortCDM) International Standards
**Reference**: PortCDM Council, IMO FAL Convention
**Category**: Best Practices

---

## PortCDM Overview

Port Collaborative Decision Making (PortCDM) is the international standard for port operation efficiency, endorsed by the International Maritime Organization (IMO) and adopted by major ports worldwide (Rotterdam, Singapore, Hamburg, Los Angeles).

**Core Principle**: Real-time data sharing among all port stakeholders (vessels, pilots, terminals, authorities) to optimize port calls and reduce waiting times.

---

## Key Performance Indicators (KPIs)

### 1. Arrival Punctuality
**Definition**: Percentage of vessels arriving within ±30 minutes of ETA

**PortCDM Target**: >90% punctuality

**Query from VESSEL_SCHEDULE**:
```sql
SELECT
    COUNT(CASE
        WHEN ABS(DATEDIFF(MINUTE, ETA, ATA)) <= 30 THEN 1
    END) * 100.0 / COUNT(*) AS ArrivalPunctuality
FROM VESSEL_SCHEDULE
WHERE Status = 'Departed'
    AND ATA IS NOT NULL
    AND YEAR(ETA) = 2024;
```

**2024 Performance**: 87.3% (below target, improvement needed)

---

### 2. Berth Waiting Time
**Definition**: Time between vessel arrival (ATA) and berthing (ATB)

**PortCDM Target**: <30 minutes average

**Query**:
```sql
SELECT
    AVG(DATEDIFF(MINUTE, ATA, ATB)) AS AvgWaitingMinutes,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY DATEDIFF(MINUTE, ATA, ATB)) AS MedianWaitingMinutes,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY DATEDIFF(MINUTE, ATA, ATB)) AS P90WaitingMinutes
FROM VESSEL_SCHEDULE
WHERE Status = 'Departed'
    AND ATA IS NOT NULL
    AND ATB IS NOT NULL
    AND YEAR(ATA) = 2024;
```

**2024 Performance**: 28 min avg (✓ meets target), 67 min P90

---

### 3. Berth Utilization
**Definition**: Percentage of time berths are occupied with vessels

**PortCDM Target**: 85-90% (optimal range, >90% creates inflexibility)

**Query**:
```sql
SELECT
    b.BerthName,
    (SUM(vs.DwellTime) / (365.0 * 24.0 * 60.0)) * 100 AS UtilizationPercent
FROM BERTHS b
LEFT JOIN VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId
    AND YEAR(vs.ETD) = 2024
    AND vs.Status = 'Departed'
WHERE b.IsActive = 1
GROUP BY b.BerthId, b.BerthName
ORDER BY UtilizationPercent DESC;
```

**2024 Performance**: 78% avg (below target, capacity available for growth)

---

### 4. Turnaround Time (Port Stay)
**Definition**: Total time from arrival to departure (ATA to ATD)

**PortCDM Target**: Minimize while maintaining safety and service quality

**Benchmarks by Vessel Type**:
- Container: <24 hours (world-class: <18 hours)
- Bulk: <48 hours (world-class: <36 hours)
- Tanker: <36 hours (world-class: <24 hours)

**Query**:
```sql
SELECT
    v.VesselType,
    AVG(DATEDIFF(HOUR, vs.ATA, vs.ATD)) AS AvgTurnaroundHours,
    MIN(DATEDIFF(HOUR, vs.ATA, vs.ATD)) AS BestTurnaround,
    MAX(DATEDIFF(HOUR, vs.ATA, vs.ATD)) AS WorstTurnaround
FROM VESSEL_SCHEDULE vs
JOIN VESSELS v ON vs.VesselId = v.VesselId
WHERE vs.Status = 'Departed'
    AND YEAR(vs.ATA) = 2024
GROUP BY v.VesselType;
```

**2024 Performance**:
- Container: 18.7 hours (✓ world-class)
- Bulk: 38.2 hours (✓ world-class)
- Tanker: 28.4 hours (✓ exceeds target)

---

## PortCDM Data Timestamps

**Standard Timestamps** (should be recorded in VESSEL_SCHEDULE):

| Timestamp | Abbreviation | Definition | Table Column |
|-----------|--------------|------------|--------------|
| Estimated Time of Arrival | ETA | Vessel's initial arrival estimate | ETA |
| Predicted Time of Arrival | PTA | AI/system predicted arrival | PredictedETA |
| Actual Time of Arrival | ATA | Vessel arrives at pilot boarding area | ATA |
| Actual Time of Berthing | ATB | Vessel secured at berth | ATB |
| Actual Time of Departure | ATD | Vessel leaves berth | ATD |

**AI Agent Integration**: Update all timestamps in VESSEL_SCHEDULE for PortCDM compliance.

---

## AI Agent Recommendations for PortCDM Compliance

### For ETA Predictor Agent
- **Update PredictedETA regularly** (every 2-4 hours as vessel approaches)
- **Target accuracy**: ±10 minutes within 24 hours of arrival
- **Store predictions**: Log in OPTIMIZATION_RUNS or AUDIT_LOG for performance tracking

### For Berth Optimizer Agent
- **Minimize waiting time**: Prioritize berth assignments that reduce ATA-to-ATB gap
- **Optimize utilization**: Target 85-90% berth utilization
- **Balance load**: Distribute vessels across berths to avoid congestion

### For Conflict Resolver Agent
- **Resolve early**: Detect conflicts 48+ hours in advance
- **Minimize disruption**: Prefer shifting lower-priority vessels
- **Communication**: Log all changes in ALERTS_NOTIFICATIONS for stakeholder visibility

---

**Keywords**: PortCDM, port standards, KPIs, arrival punctuality, berth utilization, turnaround time, waiting time, international standards, IMO, best practices, VESSEL_SCHEDULE timestamps
