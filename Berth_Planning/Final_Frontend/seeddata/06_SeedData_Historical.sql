-- ============================================
-- Berth Planning System - Seed Data: HISTORICAL
-- Vessel History, AIS Data, Berth Maintenance
-- Uses dynamic IDs from actual data
-- ============================================

-- Clear existing data
DELETE FROM VESSEL_HISTORY;
DELETE FROM AIS_DATA;
DELETE FROM BERTH_MAINTENANCE;
DBCC CHECKIDENT ('VESSEL_HISTORY', RESEED, 0);
DBCC CHECKIDENT ('AIS_DATA', RESEED, 0);
DBCC CHECKIDENT ('BERTH_MAINTENANCE', RESEED, 0);

-- Get counts for dynamic ID generation
DECLARE @MaxVesselId INT = (SELECT MAX(VesselId) FROM VESSELS);
DECLARE @MinVesselId INT = (SELECT MIN(VesselId) FROM VESSELS);
DECLARE @MaxBerthId INT = (SELECT MAX(BerthId) FROM BERTHS);
DECLARE @MinBerthId INT = (SELECT MIN(BerthId) FROM BERTHS);

-- ============================================
-- VESSEL HISTORY (Past visits)
-- ============================================

DECLARE @HistoryStart DATE = DATEADD(YEAR, -2, GETDATE());
DECLARE @HistoryEnd DATE = DATEADD(DAY, -1, GETDATE());
DECLARE @CurrentDate DATE = @HistoryStart;
DECLARE @VesselId INT;
DECLARE @BerthId INT;
DECLARE @VisitDate DATETIME;
DECLARE @DwellHours INT;
DECLARE @Counter INT;

CREATE TABLE #HistoryTemp (
    VesselId INT,
    BerthId INT,
    VisitDate DATETIME,
    ActualDwellTime INT,
    ActualWaitingTime INT,
    ETAAccuracy DECIMAL(5,2),
    Notes NVARCHAR(500)
);

WHILE @CurrentDate < @HistoryEnd
BEGIN
    -- 3-6 vessel visits per day historically
    SET @Counter = 3 + ABS(CHECKSUM(NEWID())) % 4;

    WHILE @Counter > 0
    BEGIN
        -- Use actual vessel and berth IDs from the tables
        SET @VesselId = (SELECT TOP 1 VesselId FROM VESSELS ORDER BY NEWID());
        SET @BerthId = (SELECT TOP 1 BerthId FROM BERTHS ORDER BY NEWID());
        SET @DwellHours = 8 + ABS(CHECKSUM(NEWID())) % 60;
        SET @VisitDate = DATEADD(HOUR, ABS(CHECKSUM(NEWID())) % 24, CAST(@CurrentDate AS DATETIME));

        INSERT INTO #HistoryTemp VALUES (
            @VesselId,
            @BerthId,
            @VisitDate,
            @DwellHours * 60 + (ABS(CHECKSUM(NEWID())) % 60 - 30), -- Actual dwell with variance
            ABS(CHECKSUM(NEWID())) % 120, -- Waiting time 0-120 minutes
            70 + (ABS(CHECKSUM(NEWID())) % 31), -- ETA Accuracy 70-100%
            CASE WHEN ABS(CHECKSUM(NEWID())) % 100 < 10
                THEN CASE ABS(CHECKSUM(NEWID())) % 5
                    WHEN 0 THEN 'Crane breakdown during operations'
                    WHEN 1 THEN 'Weather delay - high winds'
                    WHEN 2 THEN 'Labor shortage on shift'
                    WHEN 3 THEN 'Cargo documentation issue'
                    WHEN 4 THEN 'Equipment malfunction'
                END
                ELSE NULL
            END
        );

        SET @Counter = @Counter - 1;
    END

    SET @CurrentDate = DATEADD(DAY, 1, @CurrentDate);
END

-- Insert historical data
INSERT INTO VESSEL_HISTORY (VesselId, BerthId, VisitDate, ActualDwellTime, ActualWaitingTime, ETAAccuracy, Notes)
SELECT VesselId, BerthId, VisitDate, ActualDwellTime, ActualWaitingTime, ETAAccuracy, Notes
FROM #HistoryTemp;

DROP TABLE #HistoryTemp;

-- ============================================
-- AIS DATA (Real-time vessel tracking)
-- ============================================

DECLARE @AISTime DATETIME = DATEADD(HOUR, -48, GETDATE());
DECLARE @Lat DECIMAL(10,6);
DECLARE @Long DECIMAL(10,6);
DECLARE @Speed DECIMAL(5,2);
DECLARE @Course DECIMAL(5,2);
DECLARE @Heading DECIMAL(5,2);
DECLARE @NavStatus VARCHAR(50);
DECLARE @VesselCount INT = (SELECT COUNT(*) FROM VESSELS);

CREATE TABLE #AISTemp (
    VesselId INT,
    Latitude DECIMAL(10,7),
    Longitude DECIMAL(10,7),
    Speed DECIMAL(5,2),
    Course DECIMAL(5,2),
    Heading DECIMAL(5,2),
    NavigationStatus VARCHAR(50),
    RecordedAt DATETIME
);

-- Generate AIS tracks for all vessels (or up to 50)
DECLARE @VesselCursor CURSOR;
DECLARE @CurrentVesselId INT;
DECLARE @ProcessedCount INT = 0;

SET @VesselCursor = CURSOR FOR
    SELECT TOP 50 VesselId FROM VESSELS ORDER BY VesselId;

OPEN @VesselCursor;
FETCH NEXT FROM @VesselCursor INTO @CurrentVesselId;

WHILE @@FETCH_STATUS = 0 AND @ProcessedCount < 50
BEGIN
    SET @AISTime = DATEADD(HOUR, -48, GETDATE());
    -- Starting position near Mumbai (approaching from Arabian Sea)
    SET @Lat = 18.80 + (ABS(CHECKSUM(NEWID())) % 100) / 1000.0;
    SET @Long = 72.70 + (ABS(CHECKSUM(NEWID())) % 200) / 1000.0;

    WHILE @AISTime < GETDATE()
    BEGIN
        -- Gradually approach port
        SET @Lat = @Lat + 0.001 + (ABS(CHECKSUM(NEWID())) % 10) / 10000.0;
        SET @Long = @Long + 0.002 + (ABS(CHECKSUM(NEWID())) % 20) / 10000.0;

        -- Keep coordinates in valid range for Mumbai area
        IF @Lat > 19.10 SET @Lat = 18.85;
        IF @Long > 73.00 SET @Long = 72.75;

        SET @Speed = CASE
            WHEN @AISTime < DATEADD(HOUR, -12, GETDATE()) THEN 12 + (ABS(CHECKSUM(NEWID())) % 60) / 10.0 -- At sea
            WHEN @AISTime < DATEADD(HOUR, -4, GETDATE()) THEN 6 + (ABS(CHECKSUM(NEWID())) % 40) / 10.0 -- Approaching
            ELSE (ABS(CHECKSUM(NEWID())) % 30) / 10.0 -- Near/at berth
        END;

        SET @Course = 30 + ABS(CHECKSUM(NEWID())) % 60;
        SET @Heading = 30 + ABS(CHECKSUM(NEWID())) % 60;

        SET @NavStatus = CASE
            WHEN @Speed > 10 THEN 'UnderWayUsingEngine'
            WHEN @Speed > 2 THEN 'Restricted'
            WHEN @Speed > 0.5 THEN 'Moored'
            ELSE 'AtAnchor'
        END;

        INSERT INTO #AISTemp VALUES (
            @CurrentVesselId,
            @Lat,
            @Long,
            @Speed,
            @Course,
            @Heading,
            @NavStatus,
            @AISTime
        );

        SET @AISTime = DATEADD(MINUTE, 10 + ABS(CHECKSUM(NEWID())) % 20, @AISTime);
    END

    SET @ProcessedCount = @ProcessedCount + 1;
    FETCH NEXT FROM @VesselCursor INTO @CurrentVesselId;
END

CLOSE @VesselCursor;
DEALLOCATE @VesselCursor;

-- Insert AIS data
INSERT INTO AIS_DATA (VesselId, Latitude, Longitude, Speed, Course, Heading, NavigationStatus, RecordedAt)
SELECT VesselId, Latitude, Longitude, Speed, Course, Heading, NavigationStatus, RecordedAt
FROM #AISTemp;

DROP TABLE #AISTemp;

-- ============================================
-- BERTH MAINTENANCE (Scheduled and completed)
-- Uses actual berth IDs from database
-- ============================================

-- Get berth IDs by terminal type for realistic maintenance
DECLARE @ContainerBerth1 INT = (SELECT TOP 1 BerthId FROM BERTHS WHERE BerthType = 'Container' ORDER BY BerthId);
DECLARE @ContainerBerth2 INT = (SELECT TOP 1 BerthId FROM BERTHS WHERE BerthType = 'Container' AND BerthId > @ContainerBerth1 ORDER BY BerthId);
DECLARE @ContainerBerth3 INT = (SELECT TOP 1 BerthId FROM BERTHS WHERE BerthType = 'Container' AND BerthId > @ContainerBerth2 ORDER BY BerthId);
DECLARE @BulkBerth1 INT = (SELECT TOP 1 BerthId FROM BERTHS WHERE BerthType = 'Bulk' ORDER BY BerthId);
DECLARE @BulkBerth2 INT = (SELECT TOP 1 BerthId FROM BERTHS WHERE BerthType = 'Bulk' AND BerthId > @BulkBerth1 ORDER BY BerthId);
DECLARE @TankerBerth1 INT = (SELECT TOP 1 BerthId FROM BERTHS WHERE BerthType = 'Tanker' ORDER BY BerthId);
DECLARE @GeneralBerth1 INT = (SELECT TOP 1 BerthId FROM BERTHS WHERE BerthType = 'General' ORDER BY BerthId);
DECLARE @PassengerBerth1 INT = (SELECT TOP 1 BerthId FROM BERTHS WHERE BerthType = 'Passenger' ORDER BY BerthId);

INSERT INTO BERTH_MAINTENANCE (BerthId, StartTime, EndTime, MaintenanceType, Status, Description)
VALUES
-- Past maintenance (Completed)
(@ContainerBerth1, DATEADD(DAY, -60, GETDATE()), DATEADD(DAY, -58, GETDATE()), 'Routine', 'Completed', 'Quarterly crane inspection and lubrication'),
(@ContainerBerth2, DATEADD(DAY, -45, GETDATE()), DATEADD(DAY, -43, GETDATE()), 'StructuralRepair', 'Completed', 'Fender replacement after vessel contact'),
(@ContainerBerth3, DATEADD(DAY, -30, GETDATE()), DATEADD(DAY, -29, GETDATE()), 'Routine', 'Completed', 'Bollard stress testing'),
(@BulkBerth1, DATEADD(DAY, -40, GETDATE()), DATEADD(DAY, -35, GETDATE()), 'CraneRepair', 'Completed', 'Bulk conveyor belt replacement'),
(@TankerBerth1, DATEADD(DAY, -50, GETDATE()), DATEADD(DAY, -47, GETDATE()), 'Routine', 'Completed', 'Pipeline inspection and repair'),

-- Current maintenance (InProgress)
(@ContainerBerth2, DATEADD(DAY, -2, GETDATE()), DATEADD(DAY, 1, GETDATE()), 'CraneRepair', 'InProgress', 'Crane rail alignment correction'),
(@BulkBerth2, DATEADD(DAY, -1, GETDATE()), DATEADD(DAY, 2, GETDATE()), 'Routine', 'InProgress', 'Dust suppression system overhaul'),

-- Scheduled maintenance (Future)
(@ContainerBerth1, DATEADD(DAY, 7, GETDATE()), DATEADD(DAY, 10, GETDATE()), 'Routine', 'Scheduled', 'Annual crane certification'),
(@ContainerBerth3, DATEADD(DAY, 14, GETDATE()), DATEADD(DAY, 16, GETDATE()), 'Routine', 'Scheduled', 'Fender inspection and replacement'),
(@BulkBerth1, DATEADD(DAY, 21, GETDATE()), DATEADD(DAY, 22, GETDATE()), 'Routine', 'Scheduled', 'Electrical system inspection'),
(@TankerBerth1, DATEADD(DAY, 5, GETDATE()), DATEADD(DAY, 6, GETDATE()), 'Routine', 'Scheduled', 'Tanker terminal safety equipment check'),
(@GeneralBerth1, DATEADD(DAY, 8, GETDATE()), DATEADD(DAY, 12, GETDATE()), 'CraneRepair', 'Scheduled', 'General cargo crane motor replacement');

-- Display counts
SELECT 'Vessel History records: ' + CAST(COUNT(*) AS VARCHAR) FROM VESSEL_HISTORY;
SELECT 'AIS Data records: ' + CAST(COUNT(*) AS VARCHAR) FROM AIS_DATA;
SELECT 'Berth Maintenance records: ' + CAST(COUNT(*) AS VARCHAR) FROM BERTH_MAINTENANCE;
