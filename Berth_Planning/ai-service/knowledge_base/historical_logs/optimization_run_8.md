# Optimization Run Analysis - Case Study 8

**Data Source**: OPTIMIZATION_RUNS table
**Category**: Historical Logs

## Optimization Event Details

**Run ID**: OPT-2024-0008
**Timestamp**: 2024-09-15 08:30:00
**Vessels Processed**: 34
**Conflicts Detected**: 8
**Resolution Time**: 55 minutes

### Query Pattern
```sql
SELECT * FROM OPTIMIZATION_RUNS
WHERE OptimizationRunId = 'OPT-2024-0008'
    AND OptimizationDate >= DATEADD(DAY, -7, GETDATE());
```

**Performance Metrics**:
- Berth utilization achieved: 86%
- Average waiting time: 22 minutes
- Conflicts resolved: 8 of 8

**AI Agent Insight**: Historical optimization runs show average 88% success rate for similar vessel configurations.

**Keywords**: OPTIMIZATION_RUNS, optimization history, performance metrics, conflict resolution
