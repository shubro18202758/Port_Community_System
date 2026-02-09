# Optimization Run Analysis - Case Study 6

**Data Source**: OPTIMIZATION_RUNS table
**Category**: Historical Logs

## Optimization Event Details

**Run ID**: OPT-2024-0006
**Timestamp**: 2024-07-15 08:30:00
**Vessels Processed**: 28
**Conflicts Detected**: 6
**Resolution Time**: 45 minutes

### Query Pattern
```sql
SELECT * FROM OPTIMIZATION_RUNS
WHERE OptimizationRunId = 'OPT-2024-0006'
    AND OptimizationDate >= DATEADD(DAY, -7, GETDATE());
```

**Performance Metrics**:
- Berth utilization achieved: 84%
- Average waiting time: 24 minutes
- Conflicts resolved: 6 of 6

**AI Agent Insight**: Historical optimization runs show average 86% success rate for similar vessel configurations.

**Keywords**: OPTIMIZATION_RUNS, optimization history, performance metrics, conflict resolution
