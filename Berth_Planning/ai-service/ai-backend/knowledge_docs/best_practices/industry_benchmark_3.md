# Industry Benchmark Study 3 - Performance Comparison

**Category**: Best Practices

## Port Performance Benchmarks - 2023

### Key Metrics from Leading Ports

**Container Ports** (Singapore, Rotterdam, Shanghai):
- Berth utilization: 86% average
- Average dwell time: 16 hours
- Vessel waiting time: 15 minutes
- Crane productivity: 36 moves/hour

**Bulk Ports** (Richards Bay, Port Hedland):
- Berth utilization: 78%
- Average dwell time: 33 hours
- Loading rate: 2500 tons/hour

### Query for Comparison
```sql
-- Compare against benchmarks
SELECT
    AVG(vs.DwellTime) / 60.0 AS CurrentAvgDwellHours,
    16 AS IndustryBenchmarkHours,
    CASE
        WHEN AVG(vs.DwellTime) / 60.0 < 16 THEN 'Exceeds Benchmark'
        WHEN AVG(vs.DwellTime) / 60.0 < 18 THEN 'Meets Benchmark'
        ELSE 'Below Benchmark'
    END AS PerformanceRating
FROM VESSEL_SCHEDULE vs
JOIN VESSELS v ON vs.VesselId = v.VesselId
WHERE v.VesselType = 'Container'
    AND vs.Status = 'Departed'
    AND YEAR(vs.ETD) = 2024;
```

**AI Agent Target**: Aim for or exceed industry benchmarks in optimization decisions.

**Keywords**: industry benchmarks, port performance, comparative analysis, KPIs, world-class ports
