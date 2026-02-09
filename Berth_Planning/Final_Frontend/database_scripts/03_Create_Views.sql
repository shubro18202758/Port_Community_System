-- =============================================
-- BERTH PLANNING SYSTEM - USEFUL VIEWS
-- Purpose: Pre-built views for common queries and dashboards
-- Version: 2.0
-- Date: 2026-01-31
-- =============================================

USE [BerthPlanning]; -- Change this
GO

-- =============================================
-- VIEW 0: Berth Hierarchy
-- Shows complete port -> terminal -> berth hierarchy
-- =============================================
CREATE OR ALTER VIEW vw_BerthHierarchy AS
SELECT
    b.BerthId,
    b.BerthName,
    b.BerthCode,
    b.Length,
    b.Depth,
    b.MaxDraft,
    b.BerthType,
    b.NumberOfCranes,
    b.BollardCount,
    b.IsActive AS BerthIsActive,
    b.Latitude AS BerthLatitude,
    b.Longitude AS BerthLongitude,
    t.TerminalId,
    t.TerminalName,
    t.TerminalCode,
    t.TerminalType,
    t.OperatorName,
    t.IsActive AS TerminalIsActive,
    p.PortId,
    p.PortName,
    p.PortCode,
    p.Country,
    p.City,
    p.IsActive AS PortIsActive
FROM dbo.BERTHS b
LEFT JOIN dbo.TERMINALS t ON b.TerminalId = t.TerminalId
LEFT JOIN dbo.PORTS p ON t.PortId = p.PortId;
GO

-- =============================================
-- VIEW 1: Current Berth Status
-- Shows real-time berth occupancy status
-- =============================================
CREATE OR ALTER VIEW vw_CurrentBerthStatus
AS
SELECT 
    b.BerthId,
    b.BerthName,
    b.BerthCode,
    b.BerthType,
    b.Length,
    b.Depth,
    b.NumberOfCranes,
    b.IsActive,
    vs.ScheduleId,
    v.VesselName,
    v.VesselType,
    vs.Status,
    vs.ATB AS BerthingTime,
    vs.ETD AS DepartureTime,
    CASE 
        WHEN vs.Status = 'Berthed' THEN 'Occupied'
        WHEN vs.Status IN ('Scheduled', 'Approaching') AND vs.ETA <= DATEADD(HOUR, 2, GETUTCDATE()) THEN 'Reserved'
        WHEN b.IsActive = 0 THEN 'Inactive'
        ELSE 'Available'
    END AS BerthStatus,
    CASE 
        WHEN vs.Status = 'Berthed' THEN DATEDIFF(MINUTE, vs.ATB, GETUTCDATE())
        ELSE NULL
    END AS CurrentOccupancyMinutes
FROM dbo.BERTHS b
LEFT JOIN dbo.VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId 
    AND vs.Status IN ('Berthed', 'Scheduled', 'Approaching')
    AND (vs.ATB IS NULL OR vs.ATD IS NULL OR vs.ATD > GETUTCDATE())
LEFT JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId;
GO

-- =============================================
-- VIEW 2: Vessel Queue Dashboard
-- Shows all vessels awaiting berth or currently berthed
-- =============================================
CREATE OR ALTER VIEW vw_VesselQueueDashboard
AS
SELECT 
    vs.ScheduleId,
    v.VesselId,
    v.VesselName,
    v.IMO,
    v.VesselType,
    v.LOA,
    v.Draft,
    v.Priority,
    CASE v.Priority
        WHEN 1 THEN 'High'
        WHEN 2 THEN 'Medium'
        WHEN 3 THEN 'Low'
    END AS PriorityText,
    vs.ETA,
    vs.PredictedETA,
    vs.ETD,
    vs.Status,
    b.BerthName,
    b.BerthCode,
    vs.DwellTime,
    vs.WaitingTime,
    vs.IsOptimized,
    vs.OptimizationScore,
    vs.ConflictCount,
    CASE 
        WHEN vs.Status = 'Approaching' THEN DATEDIFF(MINUTE, GETUTCDATE(), COALESCE(vs.PredictedETA, vs.ETA))
        ELSE NULL
    END AS MinutesUntilArrival,
    CASE 
        WHEN vs.Status = 'Berthed' THEN DATEDIFF(MINUTE, vs.ATB, GETUTCDATE())
        ELSE NULL
    END AS MinutesAtBerth
FROM dbo.VESSEL_SCHEDULE vs
INNER JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
LEFT JOIN dbo.BERTHS b ON vs.BerthId = b.BerthId
WHERE vs.Status IN ('Scheduled', 'Approaching', 'Berthed');
GO

-- =============================================
-- VIEW 3: Resource Utilization
-- Shows current resource allocation status
-- =============================================
CREATE OR ALTER VIEW vw_ResourceUtilization
AS
SELECT 
    r.ResourceId,
    r.ResourceType,
    r.ResourceName,
    r.Capacity,
    r.IsAvailable,
    COUNT(ra.AllocationId) AS ActiveAllocations,
    STRING_AGG(v.VesselName, ', ') AS AssignedToVessels,
    MIN(ra.AllocatedFrom) AS NextAllocationStart,
    MAX(ra.AllocatedTo) AS LastAllocationEnd
FROM dbo.RESOURCES r
LEFT JOIN dbo.RESOURCE_ALLOCATION ra ON r.ResourceId = ra.ResourceId 
    AND ra.Status IN ('Allocated', 'InUse')
    AND ra.AllocatedTo > GETUTCDATE()
LEFT JOIN dbo.VESSEL_SCHEDULE vs ON ra.ScheduleId = vs.ScheduleId
LEFT JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
GROUP BY 
    r.ResourceId,
    r.ResourceType,
    r.ResourceName,
    r.Capacity,
    r.IsAvailable;
GO

-- =============================================
-- VIEW 4: Berth Timeline (Gantt Data)
-- Provides data for Gantt chart visualization
-- =============================================
CREATE OR ALTER VIEW vw_BerthTimeline
AS
SELECT 
    vs.ScheduleId,
    b.BerthId,
    b.BerthName,
    b.BerthCode,
    v.VesselId,
    v.VesselName,
    v.VesselType,
    v.Priority,
    vs.ETA,
    vs.PredictedETA,
    COALESCE(vs.ATB, vs.ETA) AS StartTime,
    COALESCE(vs.ATD, vs.ETD) AS EndTime,
    vs.Status,
    vs.DwellTime,
    vs.IsOptimized,
    CASE 
        WHEN vs.Status = 'Berthed' THEN '#FFA726' -- Orange
        WHEN vs.Status = 'Approaching' THEN '#66BB6A' -- Green
        WHEN vs.Status = 'Scheduled' THEN '#42A5F5' -- Blue
        ELSE '#BDBDBD' -- Gray
    END AS StatusColor
FROM dbo.VESSEL_SCHEDULE vs
INNER JOIN dbo.BERTHS b ON vs.BerthId = b.BerthId
INNER JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
WHERE vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
    AND COALESCE(vs.ATB, vs.ETA) >= DATEADD(DAY, -1, GETUTCDATE())
    AND COALESCE(vs.ATD, vs.ETD) <= DATEADD(DAY, 7, GETUTCDATE());
GO

-- =============================================
-- VIEW 5: Active Conflicts Summary
-- Shows all unresolved conflicts
-- =============================================
CREATE OR ALTER VIEW vw_ActiveConflicts
AS
SELECT 
    c.ConflictId,
    c.ConflictType,
    c.Severity,
    CASE c.Severity
        WHEN 1 THEN 'Critical'
        WHEN 2 THEN 'High'
        WHEN 3 THEN 'Medium'
        WHEN 4 THEN 'Low'
    END AS SeverityText,
    c.Description,
    c.Status,
    c.DetectedAt,
    
    -- First Schedule Details
    v1.VesselName AS Vessel1Name,
    vs1.ETA AS Vessel1ETA,
    b1.BerthName AS Vessel1Berth,
    
    -- Second Schedule Details (if applicable)
    v2.VesselName AS Vessel2Name,
    vs2.ETA AS Vessel2ETA,
    b2.BerthName AS Vessel2Berth,
    
    DATEDIFF(MINUTE, c.DetectedAt, GETUTCDATE()) AS MinutesSinceDetection
FROM dbo.CONFLICTS c
INNER JOIN dbo.VESSEL_SCHEDULE vs1 ON c.ScheduleId1 = vs1.ScheduleId
INNER JOIN dbo.VESSELS v1 ON vs1.VesselId = v1.VesselId
LEFT JOIN dbo.BERTHS b1 ON vs1.BerthId = b1.BerthId
LEFT JOIN dbo.VESSEL_SCHEDULE vs2 ON c.ScheduleId2 = vs2.ScheduleId
LEFT JOIN dbo.VESSELS v2 ON vs2.VesselId = v2.VesselId
LEFT JOIN dbo.BERTHS b2 ON vs2.BerthId = b2.BerthId
WHERE c.Status = 'Detected';
GO

-- =============================================
-- VIEW 6: Dashboard Metrics
-- Key performance indicators for the dashboard
-- =============================================
CREATE OR ALTER VIEW vw_DashboardMetrics
AS
SELECT 
    -- Vessel Counts
    (SELECT COUNT(*) FROM dbo.VESSEL_SCHEDULE WHERE Status = 'Berthed') AS VesselsBerthed,
    (SELECT COUNT(*) FROM dbo.VESSEL_SCHEDULE WHERE Status = 'Approaching') AS VesselsApproaching,
    (SELECT COUNT(*) FROM dbo.VESSEL_SCHEDULE WHERE Status = 'Scheduled') AS VesselsScheduled,
    
    -- Performance Metrics
    (SELECT AVG(CAST(WaitingTime AS FLOAT)) 
     FROM dbo.VESSEL_SCHEDULE 
     WHERE WaitingTime IS NOT NULL 
       AND CreatedAt >= DATEADD(DAY, -7, GETUTCDATE())) AS AvgWaitingTimeLast7Days,
    
    (SELECT AVG(CAST(OptimizationScore AS FLOAT))
     FROM dbo.VESSEL_SCHEDULE 
     WHERE IsOptimized = 1 
       AND CreatedAt >= DATEADD(DAY, -7, GETUTCDATE())) AS AvgOptimizationScore,
    
    -- Berth Utilization (percentage of time berths are occupied)
    (SELECT 
        CAST(SUM(CASE WHEN Status = 'Berthed' THEN 1 ELSE 0 END) AS FLOAT) / 
        NULLIF(COUNT(*), 0) * 100
     FROM dbo.BERTHS b
     LEFT JOIN dbo.VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId 
         AND vs.Status = 'Berthed'
     WHERE b.IsActive = 1) AS CurrentBerthUtilization,
    
    -- Conflicts
    (SELECT COUNT(*) FROM dbo.CONFLICTS WHERE Status = 'Detected') AS ActiveConflicts,
    (SELECT COUNT(*) FROM dbo.CONFLICTS WHERE Status = 'Detected' AND Severity = 1) AS CriticalConflicts,
    
    -- Weather Alert
    (SELECT TOP 1 CASE WHEN IsAlert = 1 THEN 1 ELSE 0 END 
     FROM dbo.WEATHER_DATA 
     ORDER BY RecordedAt DESC) AS WeatherAlert,
    
    -- Last Optimization
    (SELECT TOP 1 CreatedAt 
     FROM dbo.OPTIMIZATION_RUNS 
     WHERE Status = 'Completed' 
     ORDER BY CreatedAt DESC) AS LastOptimizationRun;
GO

-- =============================================
-- VIEW 7: Weather Forecast Display
-- Latest weather data for dashboard
-- =============================================
CREATE OR ALTER VIEW vw_CurrentWeather
AS
SELECT TOP 1
    RecordedAt,
    WindSpeed,
    WindDirection,
    Visibility,
    WaveHeight,
    Temperature,
    Precipitation,
    WeatherCondition,
    IsAlert,
    CASE 
        WHEN WindSpeed > 40 THEN 'High Wind Warning'
        WHEN Visibility < 500 THEN 'Low Visibility Warning'
        WHEN WaveHeight > 3 THEN 'High Wave Warning'
        WHEN IsAlert = 1 THEN 'Weather Alert Active'
        ELSE 'Normal Conditions'
    END AS WeatherStatus
FROM dbo.WEATHER_DATA
ORDER BY RecordedAt DESC;
GO

-- =============================================
-- VIEW 8: Upcoming Tidal Windows
-- Next high/low tides for scheduling
-- =============================================
CREATE OR ALTER VIEW vw_UpcomingTides
AS
SELECT TOP 10
    TidalId,
    TideTime,
    TideType,
    Height,
    DATEDIFF(MINUTE, GETUTCDATE(), TideTime) AS MinutesUntilTide,
    CASE 
        WHEN TideType = 'HighTide' AND Height >= 2.5 THEN 'Suitable for Deep Draft'
        WHEN TideType = 'HighTide' THEN 'Normal High Tide'
        ELSE 'Low Tide - Restrictions Apply'
    END AS TideStatus
FROM dbo.TIDAL_DATA
WHERE TideTime >= GETUTCDATE()
ORDER BY TideTime;
GO

-- =============================================
-- VIEW 9: Vessel Performance History
-- Historical performance metrics per vessel
-- =============================================
CREATE OR ALTER VIEW vw_VesselPerformanceHistory
AS
SELECT 
    v.VesselId,
    v.VesselName,
    v.IMO,
    v.VesselType,
    COUNT(vh.HistoryId) AS TotalVisits,
    AVG(vh.ActualDwellTime) AS AvgDwellTime,
    AVG(vh.ActualWaitingTime) AS AvgWaitingTime,
    AVG(vh.ETAAccuracy) AS AvgETAAccuracy,
    MAX(vh.VisitDate) AS LastVisitDate,
    MIN(vh.VisitDate) AS FirstVisitDate
FROM dbo.VESSELS v
LEFT JOIN dbo.VESSEL_HISTORY vh ON v.VesselId = vh.VesselId
GROUP BY 
    v.VesselId,
    v.VesselName,
    v.IMO,
    v.VesselType;
GO

-- =============================================
-- VIEW 10: Berth Performance Metrics
-- Performance metrics per berth
-- =============================================
CREATE OR ALTER VIEW vw_BerthPerformanceMetrics
AS
SELECT 
    b.BerthId,
    b.BerthName,
    b.BerthCode,
    b.BerthType,
    COUNT(DISTINCT vs.ScheduleId) AS TotalVesselsServed,
    AVG(vs.DwellTime) AS AvgDwellTime,
    AVG(vs.WaitingTime) AS AvgWaitingTime,
    SUM(CASE WHEN vs.ConflictCount > 0 THEN 1 ELSE 0 END) AS ConflictOccurrences,
    AVG(CASE WHEN vs.IsOptimized = 1 THEN vs.OptimizationScore ELSE NULL END) AS AvgOptimizationScore,
    -- Calculate utilization rate
    CAST(SUM(COALESCE(vs.DwellTime, 0)) AS FLOAT) / 
    NULLIF(DATEDIFF(MINUTE, MIN(vs.CreatedAt), MAX(vs.UpdatedAt)), 0) * 100 AS UtilizationRate
FROM dbo.BERTHS b
LEFT JOIN dbo.VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId
WHERE vs.Status IN ('Departed', 'Berthed')
GROUP BY 
    b.BerthId,
    b.BerthName,
    b.BerthCode,
    b.BerthType;
GO

-- =============================================
-- VIEW 11: Latest AIS Positions
-- Most recent AIS position for each vessel
-- =============================================
CREATE OR ALTER VIEW vw_LatestVesselPositions
AS
WITH LatestAIS AS (
    SELECT 
        VesselId,
        MAX(RecordedAt) AS LatestRecordedAt
    FROM dbo.AIS_DATA
    GROUP BY VesselId
)
SELECT 
    v.VesselId,
    v.VesselName,
    v.IMO,
    v.MMSI,
    v.VesselType,
    a.Latitude,
    a.Longitude,
    a.Speed,
    a.Course,
    a.Heading,
    a.NavigationStatus,
    a.RecordedAt,
    DATEDIFF(MINUTE, a.RecordedAt, GETUTCDATE()) AS MinutesSinceUpdate,
    vs.Status AS ScheduleStatus,
    vs.ETA,
    vs.PredictedETA
FROM dbo.VESSELS v
INNER JOIN LatestAIS la ON v.VesselId = la.VesselId
INNER JOIN dbo.AIS_DATA a ON v.VesselId = a.VesselId AND a.RecordedAt = la.LatestRecordedAt
LEFT JOIN dbo.VESSEL_SCHEDULE vs ON v.VesselId = vs.VesselId 
    AND vs.Status IN ('Scheduled', 'Approaching');
GO

-- =============================================
-- VERIFICATION
-- =============================================
PRINT '=============================================';
PRINT 'VIEWS CREATED SUCCESSFULLY!';
PRINT '=============================================';
PRINT '';
PRINT 'Available Views:';
PRINT '  1. vw_CurrentBerthStatus - Real-time berth occupancy';
PRINT '  2. vw_VesselQueueDashboard - Vessel queue and status';
PRINT '  3. vw_ResourceUtilization - Resource allocation status';
PRINT '  4. vw_BerthTimeline - Gantt chart data';
PRINT '  5. vw_ActiveConflicts - Unresolved conflicts';
PRINT '  6. vw_DashboardMetrics - KPIs for dashboard';
PRINT '  7. vw_CurrentWeather - Latest weather conditions';
PRINT '  8. vw_UpcomingTides - Next tidal windows';
PRINT '  9. vw_VesselPerformanceHistory - Vessel performance metrics';
PRINT ' 10. vw_BerthPerformanceMetrics - Berth performance metrics';
PRINT ' 11. vw_LatestVesselPositions - Current vessel positions';
PRINT '=============================================';
GO

-- Test query to verify views work
SELECT 'vw_DashboardMetrics' AS ViewName, * FROM vw_DashboardMetrics;
GO
