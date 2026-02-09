# Dwell Time Analysis by Vessel Type - Historical Study

**Document Type**: Historical Analysis - Turnaround Time Patterns
**Data Source**: VESSEL_SCHEDULE, VESSELS tables (2023-2024)
**Analysis Period**: 24 months (17,520 vessel movements)
**Category**: Historical Logs

---

## Container Vessels - Dwell Time Analysis

### Query Pattern
```sql
SELECT
    v.LOA,
    v.GT,
    AVG(vs.DwellTime) / 60.0 AS AvgDwellHours,
    COUNT(*) AS SampleSize
FROM VESSEL_SCHEDULE vs
JOIN VESSELS v ON vs.VesselId = v.VesselId
WHERE v.VesselType = 'Container'
    AND vs.Status = 'Departed'
    AND vs.DwellTime IS NOT NULL
GROUP BY v.LOA, v.GT;
```

**Results**:
- Small container (LOA <200m, <50K GT): 14.2 hours avg, 2,847 samples
- Medium container (200-280m, 50-100K GT): 18.7 hours avg, 4,123 samples
- Large container (280-350m, 100-150K GT): 26.3 hours avg, 1,892 samples
- Ultra-large (>350m, >150K GT): 32.8 hours avg, 234 samples

**AI Prediction Model**: `dwell_hours = 8.5 + (LOA / 10) + (TEU_count / 500) - (crane_count * 2.3)`

---

## Bulk Carriers - Dwell Time Analysis

**Average by Cargo Type** (from VESSEL_SCHEDULE):
- Grain cargo: 32.5 hours (conveyor loading: 2,500 tons/hour)
- Coal/Ore: 36.7 hours (grab crane loading: 1,800 tons/hour)
- General bulk: 28.9 hours (varies by handling method)

**Berthing Equipment Impact**:
- Specialized conveyor systems: 15% faster vs general equipment
- Multi-grab cranes (2+): 25% faster vs single crane

---

## Tanker Vessels - Dwell Time Analysis

**Average by Product Type**:
- Crude oil: 28.4 hours (pipeline: 2,000 m³/hour)
- Chemical: 24.8 hours (smaller volumes, careful handling)
- LNG: 31.2 hours (specialized cryogenic equipment)

**Critical Factor**: Pipeline compatibility reduces dwell time by 18%

---

**Keywords**: dwell time, turnaround time, vessel type analysis, container vessels, bulk carriers, tankers, VESSEL_SCHEDULE, DwellTime column, historical patterns
