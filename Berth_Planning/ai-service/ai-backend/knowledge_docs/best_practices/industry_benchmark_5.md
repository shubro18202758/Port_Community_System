# Industry Benchmark Study 5 - Performance Comparison

**Category**: Best Practices

## Port Performance Benchmarks - 2025

### Key Metrics from Leading Ports

**Container Ports** (Singapore, Rotterdam, Shanghai):
- Berth utilization: 88% average
- Average dwell time: 14 hours
- Vessel waiting time: 17 minutes
- Crane productivity: 40 moves/hour

**Bulk Ports** (Richards Bay, Port Hedland):
- Berth utilization: 80%
- Average dwell time: 31 hours
- Loading rate: 2700 tons/hour

### Query for Comparison
```sql
-- Compare against benchmarks
SELECT
    AVG(vs.DwellTime) / 60.0 AS CurrentAvgDwellHours,
    14 AS IndustryBenchmarkHours,
    CASE
        WHEN AVG(vs.DwellTime) / 60.0 < 14 THEN 'Exceeds Benchmark'
        WHEN AVG(vs.DwellTime) / 60.0 < 16 THEN 'Meets Benchmark'
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
