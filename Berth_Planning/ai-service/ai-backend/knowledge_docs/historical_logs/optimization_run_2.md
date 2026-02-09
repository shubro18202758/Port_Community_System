# Optimization Run Analysis - Case Study 2

**Data Source**: OPTIMIZATION_RUNS table
**Category**: Historical Logs

## Optimization Event Details

**Run ID**: OPT-2024-0002
**Timestamp**: 2024-03-15 08:30:00
**Vessels Processed**: 16
**Conflicts Detected**: 2
**Resolution Time**: 25 minutes

### Query Pattern
```sql
SELECT * FROM OPTIMIZATION_RUNS
WHERE OptimizationRunId = 'OPT-2024-0002'
    AND OptimizationDate >= DATEADD(DAY, -7, GETDATE());
```

**Performance Metrics**:
- Berth utilization achieved: 80%
- Average waiting time: 28 minutes
- Conflicts resolved: 2 of 2

**AI Agent Insight**: Historical optimization runs show average 82% success rate for similar vessel configurations.

**Keywords**: OPTIMIZATION_RUNS, optimization history, performance metrics, conflict resolution
