# Optimization Run Analysis - Case Study 3

**Data Source**: OPTIMIZATION_RUNS table
**Category**: Historical Logs

## Optimization Event Details

**Run ID**: OPT-2024-0003
**Timestamp**: 2024-04-15 08:30:00
**Vessels Processed**: 19
**Conflicts Detected**: 3
**Resolution Time**: 30 minutes

### Query Pattern
```sql
SELECT * FROM OPTIMIZATION_RUNS
WHERE OptimizationRunId = 'OPT-2024-0003'
    AND OptimizationDate >= DATEADD(DAY, -7, GETDATE());
```

**Performance Metrics**:
- Berth utilization achieved: 81%
- Average waiting time: 27 minutes
- Conflicts resolved: 3 of 3

**AI Agent Insight**: Historical optimization runs show average 83% success rate for similar vessel configurations.

**Keywords**: OPTIMIZATION_RUNS, optimization history, performance metrics, conflict resolution
