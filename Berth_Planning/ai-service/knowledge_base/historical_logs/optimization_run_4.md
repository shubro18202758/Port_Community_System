# Optimization Run Analysis - Case Study 4

**Data Source**: OPTIMIZATION_RUNS table
**Category**: Historical Logs

## Optimization Event Details

**Run ID**: OPT-2024-0004
**Timestamp**: 2024-05-15 08:30:00
**Vessels Processed**: 22
**Conflicts Detected**: 4
**Resolution Time**: 35 minutes

### Query Pattern
```sql
SELECT * FROM OPTIMIZATION_RUNS
WHERE OptimizationRunId = 'OPT-2024-0004'
    AND OptimizationDate >= DATEADD(DAY, -7, GETDATE());
```

**Performance Metrics**:
- Berth utilization achieved: 82%
- Average waiting time: 26 minutes
- Conflicts resolved: 4 of 4

**AI Agent Insight**: Historical optimization runs show average 84% success rate for similar vessel configurations.

**Keywords**: OPTIMIZATION_RUNS, optimization history, performance metrics, conflict resolution
