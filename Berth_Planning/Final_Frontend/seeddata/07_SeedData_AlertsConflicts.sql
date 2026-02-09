-- ============================================
-- Berth Planning System - Seed Data: ALERTS & CONFLICTS
-- Alerts, Notifications, and Conflict Records
-- Matches table schema exactly
-- Schema: CONFLICTS.Status IN ('Detected', 'Resolved', 'Ignored')
--         CONFLICTS.Severity INT (1=Critical, 2=High, 3=Medium, 4=Low)
--         CONFLICTS.ConflictType IN ('BerthOverlap', 'ResourceUnavailable', 'TidalConstraint', 'PriorityViolation')
--         Table name is ALERTS_NOTIFICATIONS (not ALERT_NOTIFICATIONS)
-- ============================================

-- Clear existing data
DELETE FROM ALERTS_NOTIFICATIONS;
DELETE FROM CONFLICTS;
DBCC CHECKIDENT ('ALERTS_NOTIFICATIONS', RESEED, 0);
DBCC CHECKIDENT ('CONFLICTS', RESEED, 0);

-- ============================================
-- CONFLICTS (Current and historical)
-- Schema: ConflictId, ConflictType, ScheduleId1, ScheduleId2, Description, Severity (INT 1-4), Status, DetectedAt, ResolvedAt, Resolution
-- ============================================

-- Get some schedule IDs for conflicts
DECLARE @Schedule1 INT, @Schedule2 INT, @Schedule3 INT, @Schedule4 INT;
SELECT TOP 1 @Schedule1 = ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Scheduled' ORDER BY ETA;
SELECT TOP 1 @Schedule2 = ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Scheduled' AND ScheduleId > @Schedule1 ORDER BY ETA;
SELECT TOP 1 @Schedule3 = ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Approaching' ORDER BY ETA;
SELECT TOP 1 @Schedule4 = ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Berthed' ORDER BY ETA;

INSERT INTO CONFLICTS (ConflictType, ScheduleId1, ScheduleId2, Description, Severity, Status, DetectedAt, ResolvedAt, Resolution)
VALUES
-- Detected conflicts (active/unresolved)
('BerthOverlap', @Schedule1, @Schedule2, 'Two vessels scheduled for overlapping time slots at Berth 1', 1, 'Detected', DATEADD(HOUR, -2, GETDATE()), NULL, NULL),
('ResourceUnavailable', @Schedule3, NULL, 'Required pilot unavailable during vessel approach window', 2, 'Detected', DATEADD(HOUR, -1, GETDATE()), NULL, NULL),
('TidalConstraint', @Schedule1, NULL, 'Deep-draft vessel scheduled outside high tide window', 1, 'Detected', DATEADD(MINUTE, -30, GETDATE()), NULL, NULL),
('PriorityViolation', @Schedule4, NULL, 'High priority vessel delayed due to lower priority vessel occupying berth', 2, 'Detected', GETDATE(), NULL, NULL),

-- More detected conflicts (pending resolution)
('BerthOverlap', @Schedule2, @Schedule1, 'Potential overlap detected for next week schedules', 3, 'Detected', DATEADD(HOUR, -12, GETDATE()), NULL, NULL),
('ResourceUnavailable', @Schedule3, NULL, 'Tugboat shortage during peak hours', 2, 'Detected', DATEADD(HOUR, -4, GETDATE()), NULL, NULL),

-- Resolved conflicts (historical)
('BerthOverlap',
    (SELECT TOP 1 ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Departed' ORDER BY NEWID()),
    (SELECT TOP 1 ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Departed' ORDER BY NEWID()),
    'Resolved by delaying second vessel by 4 hours',
    1, 'Resolved', DATEADD(DAY, -5, GETDATE()), DATEADD(DAY, -5, DATEADD(HOUR, 2, GETDATE())), 'Delayed MV Pacific Trader arrival'),

('ResourceUnavailable',
    (SELECT TOP 1 ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Departed' ORDER BY NEWID()),
    NULL,
    'Tugboat STORM was under maintenance',
    2, 'Resolved', DATEADD(DAY, -3, GETDATE()), DATEADD(DAY, -3, DATEADD(HOUR, 3, GETDATE())), 'Assigned alternative tugboat WAVE'),

('TidalConstraint',
    (SELECT TOP 1 ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Departed' ORDER BY NEWID()),
    NULL,
    'VLCC required high tide for safe entry',
    1, 'Resolved', DATEADD(DAY, -7, GETDATE()), DATEADD(DAY, -7, DATEADD(HOUR, 1, GETDATE())), 'Rescheduled arrival to next high tide'),

('PriorityViolation',
    (SELECT TOP 1 ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Departed' ORDER BY NEWID()),
    NULL,
    'Lower priority vessel was assigned berth before high priority vessel',
    2, 'Resolved', DATEADD(DAY, -10, GETDATE()), DATEADD(DAY, -9, GETDATE()), 'Swapped berth assignments'),

('ResourceUnavailable',
    (SELECT TOP 1 ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Departed' ORDER BY NEWID()),
    NULL,
    'No available cranes during peak hours',
    3, 'Resolved', DATEADD(DAY, -15, GETDATE()), DATEADD(DAY, -14, GETDATE()), 'Extended crane operation hours'),

-- Ignored conflicts (acknowledged but no action taken)
('BerthOverlap',
    (SELECT TOP 1 ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Departed' ORDER BY NEWID()),
    (SELECT TOP 1 ScheduleId FROM VESSEL_SCHEDULE WHERE Status = 'Departed' ORDER BY NEWID()),
    'Minor overlap of 15 minutes - within acceptable tolerance',
    4, 'Ignored', DATEADD(DAY, -20, GETDATE()), DATEADD(DAY, -20, DATEADD(MINUTE, 30, GETDATE())), 'Within acceptable tolerance, no action needed');

-- ============================================
-- ALERTS_NOTIFICATIONS (correct table name)
-- Schema: AlertId, AlertType, RelatedEntityId, EntityType, Severity (VARCHAR: Critical/High/Medium/Low), Message, IsRead, CreatedAt, ReadAt
-- ============================================

INSERT INTO ALERTS_NOTIFICATIONS (AlertType, RelatedEntityId, EntityType, Severity, Message, IsRead, CreatedAt, ReadAt)
VALUES
-- Current/Active alerts (unread)
('ConflictDetected', 1, 'Conflict', 'Critical', 'URGENT: Berth overlap conflict detected - Berth 1, vessels scheduled within 2 hours of each other', 0, DATEADD(HOUR, -2, GETDATE()), NULL),
('ConflictDetected', 2, 'Conflict', 'High', 'Pilot unavailable for vessel MV Atlantic Star approach', 0, DATEADD(HOUR, -1, GETDATE()), NULL),
('ConflictDetected', 3, 'Conflict', 'Critical', 'Tidal window violation: Deep-draft vessel scheduled at low tide', 0, DATEADD(MINUTE, -30, GETDATE()), NULL),
('WeatherWarning', NULL, 'Weather', 'High', 'High wind alert: Wind speeds expected to reach 35 km/h in next 6 hours', 0, DATEADD(HOUR, -3, GETDATE()), NULL),
('WeatherWarning', NULL, 'Weather', 'Medium', 'Wave height advisory: 2.5m waves expected in outer anchorage', 0, DATEADD(HOUR, -2, GETDATE()), NULL),
('DelayAlert', 6, 'Berth', 'Medium', 'Berth CTB-02 crane maintenance in progress - capacity reduced', 0, DATEADD(DAY, -1, GETDATE()), NULL),
('ResourceShortage', NULL, 'Resource', 'Medium', 'Low tugboat availability: Only 3 tugs available for next 4 hours', 0, DATEADD(HOUR, -4, GETDATE()), NULL),
('DelayAlert', @Schedule3, 'Schedule', 'Low', 'Vessel PACIFIC TRADER reporting 30-minute ETA delay', 0, DATEADD(MINUTE, -45, GETDATE()), NULL),
('ConflictDetected', @Schedule1, 'Schedule', 'Low', 'AI prediction: Vessel likely to arrive 15 minutes early based on AIS data', 0, DATEADD(MINUTE, -20, GETDATE()), NULL),
('ConflictDetected', NULL, 'System', 'Low', 'AI suggestion: Berth utilization can be improved by 12% with schedule optimization', 0, DATEADD(HOUR, -6, GETDATE()), NULL),

-- Read alerts (recent history)
('ConflictDetected', 7, 'Conflict', 'Medium', 'Berth overlap conflict resolved - MV Pacific Trader delayed 4 hours', 1, DATEADD(DAY, -5, GETDATE()), DATEADD(DAY, -5, DATEADD(HOUR, 1, GETDATE()))),
('ConflictDetected', 8, 'Conflict', 'Medium', 'Resource conflict resolved - Alternative tugboat assigned', 1, DATEADD(DAY, -3, GETDATE()), DATEADD(DAY, -3, DATEADD(HOUR, 2, GETDATE()))),
('WeatherWarning', NULL, 'Weather', 'High', 'Storm warning lifted - Operations resumed', 1, DATEADD(DAY, -14, GETDATE()), DATEADD(DAY, -14, DATEADD(HOUR, 2, GETDATE()))),
('DelayAlert', 5, 'Berth', 'Low', 'Berth BLK-01 concrete deck repair completed', 1, DATEADD(DAY, -20, GETDATE()), DATEADD(DAY, -20, DATEADD(HOUR, 1, GETDATE()))),
('ConflictDetected', NULL, 'Schedule', 'Low', 'Vessel MSC OSCAR successfully berthed at CTA-01', 1, DATEADD(DAY, -1, GETDATE()), DATEADD(DAY, -1, DATEADD(MINUTE, 30, GETDATE()))),
('ConflictDetected', NULL, 'Schedule', 'Low', 'Vessel EVER ACE departed from CTA-02', 1, DATEADD(DAY, -2, GETDATE()), DATEADD(DAY, -2, DATEADD(HOUR, 1, GETDATE()))),
('ConflictDetected', NULL, 'System', 'Low', 'Daily system health check completed - All systems operational', 1, DATEADD(DAY, -1, GETDATE()), DATEADD(DAY, -1, DATEADD(HOUR, 8, GETDATE()))),

-- More historical alerts
('ConflictDetected', 9, 'Conflict', 'Critical', 'Tidal constraint violation detected', 1, DATEADD(DAY, -7, GETDATE()), DATEADD(DAY, -7, DATEADD(MINUTE, 15, GETDATE()))),
('ConflictDetected', 9, 'Conflict', 'Medium', 'Tidal conflict resolved - Arrival rescheduled', 1, DATEADD(DAY, -7, DATEADD(HOUR, 1, GETDATE())), DATEADD(DAY, -7, DATEADD(HOUR, 2, GETDATE()))),
('ConflictDetected', NULL, 'Schedule', 'Low', 'AI ETA prediction accuracy for last week: 94.2%', 1, DATEADD(DAY, -7, GETDATE()), DATEADD(DAY, -6, GETDATE())),
('ConflictDetected', NULL, 'System', 'Low', 'Weekly optimization report: 847 vessels processed, 23 conflicts resolved', 1, DATEADD(DAY, -7, GETDATE()), DATEADD(DAY, -6, GETDATE())),

-- Performance alerts
('DelayAlert', 1, 'Berth', 'Medium', 'Berth CTA-01 utilization dropped to 65% - below target', 1, DATEADD(DAY, -10, GETDATE()), DATEADD(DAY, -9, GETDATE())),
('DelayAlert', NULL, 'System', 'Low', 'Average vessel waiting time increased to 45 minutes', 1, DATEADD(DAY, -12, GETDATE()), DATEADD(DAY, -11, GETDATE())),
('ResourceShortage', NULL, 'System', 'High', 'Port approaching 90% capacity for weekend', 1, DATEADD(DAY, -3, GETDATE()), DATEADD(DAY, -3, DATEADD(HOUR, 2, GETDATE())));

-- Display counts
SELECT 'Conflicts inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM CONFLICTS;
SELECT 'Alert Notifications inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM ALERTS_NOTIFICATIONS;

-- Summary
SELECT 'Detected Conflicts: ' + CAST(COUNT(*) AS VARCHAR) FROM CONFLICTS WHERE Status = 'Detected';
SELECT 'Resolved Conflicts: ' + CAST(COUNT(*) AS VARCHAR) FROM CONFLICTS WHERE Status = 'Resolved';
SELECT 'Unread Alerts: ' + CAST(COUNT(*) AS VARCHAR) FROM ALERTS_NOTIFICATIONS WHERE IsRead = 0;
SELECT 'Critical Alerts: ' + CAST(COUNT(*) AS VARCHAR) FROM ALERTS_NOTIFICATIONS WHERE Severity = 'Critical' AND IsRead = 0;
