# Industry Benchmark Study 2 - Performance Comparison

**Category**: Best Practices

## Port Performance Benchmarks - 2022

### Key Metrics from Leading Ports

**Container Ports** (Singapore, Rotterdam, Shanghai):
- Berth utilization: 85% average
- Average dwell time: 17 hours
- Vessel waiting time: 14 minutes
- Crane productivity: 34 moves/hour

**Bulk Ports** (Richards Bay, Port Hedland):
- Berth utilization: 77%
- Average dwell time: 34 hours
- Loading rate: 2400 tons/hour

### Query for Comparison
```sql
-- Compare against benchmarks
SELECT
    AVG(vs.DwellTime) / 60.0 AS CurrentAvgDwellHours,
    17 AS IndustryBenchmarkHours,
    CASE
        WHEN AVG(vs.DwellTime) / 60.0 < 17 THEN 'Exceeds Benchmark'
        WHEN AVG(vs.DwellTime) / 60.0 < 19 THEN 'Meets Benchmark'
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
