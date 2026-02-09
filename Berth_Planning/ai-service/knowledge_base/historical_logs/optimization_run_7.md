# Optimization Run Analysis - Case Study 7

**Data Source**: OPTIMIZATION_RUNS table
**Category**: Historical Logs

## Optimization Event Details

**Run ID**: OPT-2024-0007
**Timestamp**: 2024-08-15 08:30:00
**Vessels Processed**: 31
**Conflicts Detected**: 7
**Resolution Time**: 50 minutes

### Query Pattern
```sql
SELECT * FROM OPTIMIZATION_RUNS
WHERE OptimizationRunId = 'OPT-2024-0007'
    AND OptimizationDate >= DATEADD(DAY, -7, GETDATE());
```

**Performance Metrics**:
- Berth utilization achieved: 85%
- Average waiting time: 23 minutes
- Conflicts resolved: 7 of 7

**AI Agent Insight**: Historical optimization runs show average 87% success rate for similar vessel configurations.

**Keywords**: OPTIMIZATION_RUNS, optimization history, performance metrics, conflict resolution
