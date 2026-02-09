-- ============================================
-- Berth Planning System - Seed Data: RESOURCES
-- Resources and Resource Allocations
-- Matches table schema: ResourceType IN ('Crane', 'Tugboat', 'Pilot', 'Labor', 'Other')
-- ============================================

-- Clear existing data
DELETE FROM RESOURCE_ALLOCATION;
DELETE FROM RESOURCES;
DBCC CHECKIDENT ('RESOURCES', RESEED, 0);
DBCC CHECKIDENT ('RESOURCE_ALLOCATION', RESEED, 0);

-- Insert Resources (NO Location column - not in schema)
INSERT INTO RESOURCES (ResourceName, ResourceType, Capacity, IsAvailable)
VALUES
-- Pilots (15 pilots)
('Pilot Team A1', 'Pilot', 1, 1),
('Pilot Team A2', 'Pilot', 1, 1),
('Pilot Team A3', 'Pilot', 1, 1),
('Pilot Team A4', 'Pilot', 1, 0), -- On leave
('Pilot Team B1', 'Pilot', 1, 1),
('Pilot Team B2', 'Pilot', 1, 1),
('Pilot Team B3', 'Pilot', 1, 1),
('Pilot Team B4', 'Pilot', 1, 1),
('Pilot Team C1', 'Pilot', 1, 1),
('Pilot Team C2', 'Pilot', 1, 1),
('Pilot Team C3', 'Pilot', 1, 0), -- Training
('Senior Pilot SP1', 'Pilot', 1, 1),
('Senior Pilot SP2', 'Pilot', 1, 1),
('Night Pilot N1', 'Pilot', 1, 1),
('Night Pilot N2', 'Pilot', 1, 1),

-- Tugboats (12 tugs)
('Tugboat TITAN', 'Tugboat', 80, 1),
('Tugboat HERCULES', 'Tugboat', 80, 1),
('Tugboat ATLAS', 'Tugboat', 75, 1),
('Tugboat ZEUS', 'Tugboat', 75, 1),
('Tugboat POSEIDON', 'Tugboat', 70, 1),
('Tugboat NEPTUNE', 'Tugboat', 70, 1),
('Tugboat TRITON', 'Tugboat', 65, 1),
('Tugboat OCEANUS', 'Tugboat', 65, 1),
('Tugboat STORM', 'Tugboat', 60, 0), -- Under maintenance
('Tugboat WAVE', 'Tugboat', 60, 1),
('Harbor Tug HT1', 'Tugboat', 50, 1),
('Harbor Tug HT2', 'Tugboat', 50, 1),

-- Cranes (18 cranes across terminals)
('Crane CTA-C1', 'Crane', 65, 1),
('Crane CTA-C2', 'Crane', 65, 1),
('Crane CTA-C3', 'Crane', 65, 1),
('Crane CTA-C4', 'Crane', 60, 1),
('Crane CTA-C5', 'Crane', 60, 1),
('Crane CTA-C6', 'Crane', 55, 0), -- Maintenance
('Crane CTB-C1', 'Crane', 60, 1),
('Crane CTB-C2', 'Crane', 60, 1),
('Crane CTB-C3', 'Crane', 55, 1),
('Crane CTB-C4', 'Crane', 55, 1),
('Crane CTC-C1', 'Crane', 50, 1),
('Crane CTC-C2', 'Crane', 50, 1),
('Crane CTC-C3', 'Crane', 45, 1),
('Crane BLK-C1', 'Crane', 40, 1),
('Crane BLK-C2', 'Crane', 40, 1),
('Crane BLK-C3', 'Crane', 35, 1),
('Crane GEN-C1', 'Crane', 30, 1),
('Crane GEN-C2', 'Crane', 30, 1),

-- Labor Teams (10 teams)
('Labor Team L1', 'Labor', 20, 1),
('Labor Team L2', 'Labor', 20, 1),
('Labor Team L3', 'Labor', 18, 1),
('Labor Team L4', 'Labor', 18, 1),
('Labor Team L5', 'Labor', 15, 1),
('Labor Team L6', 'Labor', 15, 1),
('Labor Team L7', 'Labor', 15, 1),
('Labor Team L8', 'Labor', 12, 1),
('Labor Team L9', 'Labor', 12, 1),
('Labor Team L10', 'Labor', 10, 0), -- On standby

-- Other Equipment (Mooring teams etc.)
('Mooring Team M1', 'Other', 6, 1),
('Mooring Team M2', 'Other', 6, 1),
('Mooring Team M3', 'Other', 5, 1),
('Mooring Team M4', 'Other', 5, 1),
('Mooring Team M5', 'Other', 5, 1),
('Mooring Team M6', 'Other', 5, 1),
('Mooring Team M7', 'Other', 4, 1),
('Mooring Team M8', 'Other', 4, 1);

-- Generate Resource Allocations for current and upcoming schedules
-- Status must be: 'Allocated', 'InUse', 'Released'
INSERT INTO RESOURCE_ALLOCATION (ResourceId, ScheduleId, AllocatedFrom, AllocatedTo, Status)
SELECT
    r.ResourceId,
    vs.ScheduleId,
    DATEADD(HOUR, -1, vs.ETA),
    DATEADD(HOUR, 1, vs.ETA),
    CASE
        WHEN vs.Status = 'Departed' THEN 'Released'
        WHEN vs.Status = 'Berthed' THEN 'InUse'
        ELSE 'Allocated'
    END
FROM VESSEL_SCHEDULE vs
CROSS APPLY (
    SELECT TOP 1 ResourceId FROM RESOURCES
    WHERE ResourceType = 'Pilot' AND IsAvailable = 1
    ORDER BY NEWID()
) r
WHERE vs.Status IN ('Berthed', 'Approaching', 'Scheduled', 'Departed')
AND vs.ETA > DATEADD(DAY, -7, GETDATE());

-- Allocate tugboats
INSERT INTO RESOURCE_ALLOCATION (ResourceId, ScheduleId, AllocatedFrom, AllocatedTo, Status)
SELECT
    r.ResourceId,
    vs.ScheduleId,
    DATEADD(HOUR, -2, vs.ETA),
    DATEADD(HOUR, 2, vs.ETA),
    CASE
        WHEN vs.Status = 'Departed' THEN 'Released'
        WHEN vs.Status = 'Berthed' THEN 'InUse'
        ELSE 'Allocated'
    END
FROM VESSEL_SCHEDULE vs
CROSS APPLY (
    SELECT TOP 1 ResourceId FROM RESOURCES
    WHERE ResourceType = 'Tugboat' AND IsAvailable = 1
    ORDER BY NEWID()
) r
WHERE vs.Status IN ('Berthed', 'Approaching', 'Scheduled', 'Departed')
AND vs.ETA > DATEADD(DAY, -7, GETDATE());

-- Allocate cranes for container vessels
INSERT INTO RESOURCE_ALLOCATION (ResourceId, ScheduleId, AllocatedFrom, AllocatedTo, Status)
SELECT
    r.ResourceId,
    vs.ScheduleId,
    vs.ETA,
    vs.ETD,
    CASE
        WHEN vs.Status = 'Departed' THEN 'Released'
        WHEN vs.Status = 'Berthed' THEN 'InUse'
        ELSE 'Allocated'
    END
FROM VESSEL_SCHEDULE vs
INNER JOIN VESSELS v ON vs.VesselId = v.VesselId
CROSS APPLY (
    SELECT TOP 2 ResourceId FROM RESOURCES
    WHERE ResourceType = 'Crane' AND IsAvailable = 1
    ORDER BY NEWID()
) r
WHERE v.VesselType = 'Container'
AND vs.Status IN ('Berthed', 'Approaching', 'Scheduled', 'Departed')
AND vs.ETA > DATEADD(DAY, -7, GETDATE());

-- Display counts
SELECT 'Resources inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM RESOURCES;
SELECT 'Resource Allocations inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM RESOURCE_ALLOCATION;
SELECT ResourceType, COUNT(*) AS Count FROM RESOURCES GROUP BY ResourceType;
