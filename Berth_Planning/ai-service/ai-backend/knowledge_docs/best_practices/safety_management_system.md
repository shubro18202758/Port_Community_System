# Safety Management System - Port Safety Standards

**Document Type**: Best Practices - Safety Protocols
**Source**: International Maritime Organization (IMO), Port Safety Standards
**Category**: Best Practices

---

## Hard Safety Constraints (Non-Negotiable)

### 1. Physical Dimension Limits
**Rule**: vessel.loa ≤ berth.length AND vessel.draft ≤ berth.max_draft

**From BERTHS and VESSELS tables**:
```sql
SELECT
    v.VesselName,
    v.LOA,
    v.Draft,
    b.BerthName,
    b.Length,
    b.MaxDraft,
    CASE
        WHEN v.LOA > b.Length THEN 'REJECTED - LOA exceeds berth'
        WHEN v.Draft > b.MaxDraft THEN 'REJECTED - Draft exceeds depth'
        ELSE 'COMPATIBLE'
    END AS SafetyCheck
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE b.BerthType = v.VesselType;
```

**AI Agent Rule**: NEVER assign vessel if physical constraints violated (HARD constraint).

---

### 2. Under Keel Clearance (UKC)
**Rule**: vessel_draft + minimum_ukc ≤ available_depth

**Minimum UKC Standards**:
- Small vessels (<10K GT): 0.8-1.0 meters
- Medium vessels (10-80K GT): 1.0-1.5 meters
- Large vessels (>80K GT): 1.5-2.0 meters
- Ultra-large (>200K GT): 2.0-3.0 meters

**Tidal Integration**:
```sql
SELECT
    v.VesselName,
    v.Draft,
    b.BerthDepth,
    td.TideHeight,
    (b.BerthDepth + td.TideHeight) - v.Draft AS CalculatedUKC,
    CASE
        WHEN (b.BerthDepth + td.TideHeight) - v.Draft >= 1.5 THEN 'SAFE'
        ELSE 'INSUFFICIENT UKC - WAIT FOR HIGH TIDE'
    END AS UKCStatus
FROM VESSELS v
CROSS JOIN BERTHS b
CROSS JOIN TIDAL_DATA td
WHERE td.TideType = 'High'
    AND td.TideDateTime >= GETDATE();
```

**AI Agent Rule**: For deep-draft vessels (draft >12m), schedule arrival during high tide window (see tidal_window_analysis.md).

---

### 3. Weather Safety Thresholds
**From WEATHER_DATA**:

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Wind <25 knots | Normal | Normal operations |
| Wind 25-35 knots | Moderate | Reduce crane speed |
| Wind 35-40 knots | Severe | Suspend crane operations |
| Wind >40 knots | Extreme | Full port shutdown |
| Visibility <500m | Critical | Navigation suspended |
| Wave height >6m | Extreme | Berthing suspended |

**AI Agent Query**:
```sql
SELECT TOP 1
    WindSpeed,
    WaveHeight,
    Visibility,
    CASE
        WHEN WindSpeed > 40 OR WaveHeight > 6 THEN 'PORT SHUTDOWN'
        WHEN WindSpeed > 35 OR Visibility < 500 THEN 'SUSPEND OPERATIONS'
        WHEN WindSpeed > 25 THEN 'REDUCED OPERATIONS'
        ELSE 'NORMAL'
    END AS PortStatus
FROM WEATHER_DATA
ORDER BY RecordedAt DESC;
```

---

### 4. Dangerous Goods Segregation
**Rule**: Incompatible dangerous goods must be separated

**IMDG Classes** (International Maritime Dangerous Goods Code):
- Class 1: Explosives → Segregate from all other classes
- Class 2: Gases → Segregate from Classes 4, 5, 8
- Class 3: Flammable liquids → Segregate from Classes 4, 5, 8
- Class 4: Flammable solids → Segregate from Classes 3, 5, 8
- Class 5: Oxidizers → Segregate from Classes 3, 4, 8
- Class 6: Toxic substances → Segregate from Class 8
- Class 7: Radioactive → Segregate from all (dedicated berth only)
- Class 8: Corrosives → Segregate from Classes 3, 4, 5, 6
- Class 9: Miscellaneous → General precautions

**AI Agent Rule**: Check VESSELS.DangerousGoods before berth assignment. Ensure sufficient separation distance (minimum 100m) between incompatible classes.

---

## Emergency Response Protocols

**From ALERTS_NOTIFICATIONS table**:
```sql
SELECT
    AlertType,
    Severity,
    Message,
    CreatedAt,
    Status
FROM ALERTS_NOTIFICATIONS
WHERE Severity IN ('High', 'Critical')
    AND Status = 'Active'
ORDER BY CreatedAt DESC;
```

**Alert Types**:
- Crane failure: Immediate notification, reassign resources
- Weather warning: 6-hour advance notice, prepare contingencies
- Vessel distress: Emergency berth allocation, clear highest-priority berth
- Dangerous goods incident: Evacuate adjacent berths, notify authorities

**AI Agent Integration**: Monitor ALERTS_NOTIFICATIONS and adjust berth assignments in real-time.

---

**Keywords**: safety management, hard constraints, UKC, weather safety, dangerous goods, IMDG, emergency response, ALERTS_NOTIFICATIONS, WEATHER_DATA, BERTHS, VESSELS
