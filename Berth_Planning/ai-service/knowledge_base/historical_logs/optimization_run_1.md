# Optimization Run Analysis - Case Study 1

**Data Source**: OPTIMIZATION_RUNS table
**Category**: Historical Logs

## Optimization Event Details

**Run ID**: OPT-2024-0001
**Timestamp**: 2024-02-15 08:30:00
**Vessels Processed**: 13
**Conflicts Detected**: 1
**Resolution Time**: 20 minutes

### Query Pattern
```sql
SELECT * FROM OPTIMIZATION_RUNS
WHERE OptimizationRunId = 'OPT-2024-0001'
    AND OptimizationDate >= DATEADD(DAY, -7, GETDATE());
```

**Performance Metrics**:
- Berth utilization achieved: 79%
- Average waiting time: 29 minutes
- Conflicts resolved: 1 of 1

**AI Agent Insight**: Historical optimization runs show average 81% success rate for similar vessel configurations.

**Keywords**: OPTIMIZATION_RUNS, optimization history, performance metrics, conflict resolution
