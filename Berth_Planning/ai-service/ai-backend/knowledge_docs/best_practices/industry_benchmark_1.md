# Industry Benchmark Study 1 - Performance Comparison

**Category**: Best Practices

## Port Performance Benchmarks - 2021

### Key Metrics from Leading Ports

**Container Ports** (Singapore, Rotterdam, Shanghai):
- Berth utilization: 84% average
- Average dwell time: 18 hours
- Vessel waiting time: 13 minutes
- Crane productivity: 32 moves/hour

**Bulk Ports** (Richards Bay, Port Hedland):
- Berth utilization: 76%
- Average dwell time: 35 hours
- Loading rate: 2300 tons/hour

### Query for Comparison
```sql
-- Compare against benchmarks
SELECT
    AVG(vs.DwellTime) / 60.0 AS CurrentAvgDwellHours,
    18 AS IndustryBenchmarkHours,
    CASE
        WHEN AVG(vs.DwellTime) / 60.0 < 18 THEN 'Exceeds Benchmark'
        WHEN AVG(vs.DwellTime) / 60.0 < 20 THEN 'Meets Benchmark'
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
