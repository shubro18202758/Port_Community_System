# Optimization Run Analysis - Case Study 5

**Data Source**: OPTIMIZATION_RUNS table
**Category**: Historical Logs

## Optimization Event Details

**Run ID**: OPT-2024-0005
**Timestamp**: 2024-06-15 08:30:00
**Vessels Processed**: 25
**Conflicts Detected**: 5
**Resolution Time**: 40 minutes

### Query Pattern
```sql
SELECT * FROM OPTIMIZATION_RUNS
WHERE OptimizationRunId = 'OPT-2024-0005'
    AND OptimizationDate >= DATEADD(DAY, -7, GETDATE());
```

**Performance Metrics**:
- Berth utilization achieved: 83%
- Average waiting time: 25 minutes
- Conflicts resolved: 5 of 5

**AI Agent Insight**: Historical optimization runs show average 85% success rate for similar vessel configurations.

**Keywords**: OPTIMIZATION_RUNS, optimization history, performance metrics, conflict resolution
