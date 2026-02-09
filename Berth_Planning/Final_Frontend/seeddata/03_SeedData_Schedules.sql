-- ============================================
-- Berth Planning System - Seed Data: SCHEDULES
-- Vessel Schedule Records for Mumbai Port Trust
-- ============================================

-- Clear existing data
DELETE FROM VESSEL_SCHEDULE;
DBCC CHECKIDENT ('VESSEL_SCHEDULE', RESEED, 0);

-- Generate schedules for the past 30 days, current, and next 14 days
DECLARE @StartDate DATETIME = DATEADD(DAY, -30, GETDATE());
DECLARE @EndDate DATETIME = DATEADD(DAY, 14, GETDATE());
DECLARE @CurrentDate DATETIME = @StartDate;
DECLARE @VesselId INT;
DECLARE @BerthId INT;
DECLARE @DwellHours INT;
DECLARE @ETA DATETIME;
DECLARE @ETD DATETIME;
DECLARE @Status VARCHAR(20);
DECLARE @Score DECIMAL(5,2);
DECLARE @Counter INT = 0;

-- Create a temporary table for schedule generation
CREATE TABLE #ScheduleTemp (
    VesselId INT,
    BerthId INT,
    ETA DATETIME,
    PredictedETA DATETIME,
    ETD DATETIME,
    ATA DATETIME NULL,
    ATB DATETIME NULL,
    ATD DATETIME NULL,
    Status VARCHAR(20),
    DwellTime INT,
    WaitingTime INT NULL,
    OptimizationScore DECIMAL(5,2),
    IsOptimized BIT,
    ConflictCount INT
);

-- Past schedules (Departed) - Last 30 days
SET @CurrentDate = @StartDate;
WHILE @CurrentDate < DATEADD(DAY, -1, GETDATE())
BEGIN
    -- Morning arrivals (4-6 vessels per day)
    SET @Counter = 0;
    WHILE @Counter < 5
    BEGIN
        SET @VesselId = (SELECT TOP 1 VesselId FROM VESSELS ORDER BY NEWID());
        SET @BerthId = (SELECT TOP 1 BerthId FROM BERTHS WHERE IsActive = 1 ORDER BY NEWID());
        SET @DwellHours = CASE
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Container' THEN 12 + ABS(CHECKSUM(NEWID())) % 18
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Bulk' THEN 24 + ABS(CHECKSUM(NEWID())) % 36
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Tanker' THEN 18 + ABS(CHECKSUM(NEWID())) % 24
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Passenger' THEN 8 + ABS(CHECKSUM(NEWID())) % 12
            ELSE 8 + ABS(CHECKSUM(NEWID())) % 16
        END;
        SET @ETA = DATEADD(HOUR, 6 + ABS(CHECKSUM(NEWID())) % 6, @CurrentDate);
        SET @ETD = DATEADD(HOUR, @DwellHours, @ETA);
        SET @Score = 70 + (ABS(CHECKSUM(NEWID())) % 30);

        INSERT INTO #ScheduleTemp VALUES (
            @VesselId, @BerthId, @ETA,
            DATEADD(MINUTE, -15 + ABS(CHECKSUM(NEWID())) % 30, @ETA), -- Predicted ETA variance
            @ETD,
            DATEADD(MINUTE, -10 + ABS(CHECKSUM(NEWID())) % 20, @ETA), -- ATA
            DATEADD(MINUTE, 15 + ABS(CHECKSUM(NEWID())) % 30, @ETA), -- ATB
            DATEADD(MINUTE, -30 + ABS(CHECKSUM(NEWID())) % 60, @ETD), -- ATD
            'Departed',
            @DwellHours * 60,
            ABS(CHECKSUM(NEWID())) % 60,
            @Score, 1, 0
        );
        SET @Counter = @Counter + 1;
    END

    -- Afternoon arrivals (3-4 vessels per day)
    SET @Counter = 0;
    WHILE @Counter < 3
    BEGIN
        SET @VesselId = (SELECT TOP 1 VesselId FROM VESSELS ORDER BY NEWID());
        SET @BerthId = (SELECT TOP 1 BerthId FROM BERTHS WHERE IsActive = 1 ORDER BY NEWID());
        SET @DwellHours = CASE
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Container' THEN 12 + ABS(CHECKSUM(NEWID())) % 18
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Bulk' THEN 24 + ABS(CHECKSUM(NEWID())) % 36
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Tanker' THEN 18 + ABS(CHECKSUM(NEWID())) % 24
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Passenger' THEN 8 + ABS(CHECKSUM(NEWID())) % 12
            ELSE 8 + ABS(CHECKSUM(NEWID())) % 16
        END;
        SET @ETA = DATEADD(HOUR, 14 + ABS(CHECKSUM(NEWID())) % 6, @CurrentDate);
        SET @ETD = DATEADD(HOUR, @DwellHours, @ETA);
        SET @Score = 70 + (ABS(CHECKSUM(NEWID())) % 30);

        INSERT INTO #ScheduleTemp VALUES (
            @VesselId, @BerthId, @ETA,
            DATEADD(MINUTE, -15 + ABS(CHECKSUM(NEWID())) % 30, @ETA),
            @ETD,
            DATEADD(MINUTE, -10 + ABS(CHECKSUM(NEWID())) % 20, @ETA),
            DATEADD(MINUTE, 15 + ABS(CHECKSUM(NEWID())) % 30, @ETA),
            DATEADD(MINUTE, -30 + ABS(CHECKSUM(NEWID())) % 60, @ETD),
            'Departed',
            @DwellHours * 60,
            ABS(CHECKSUM(NEWID())) % 60,
            @Score, 1, 0
        );
        SET @Counter = @Counter + 1;
    END

    SET @CurrentDate = DATEADD(DAY, 1, @CurrentDate);
END

-- Current day schedules (Berthed, Approaching)
-- Get actual berth IDs from database
DECLARE @IDCT01 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'IDCT-01');
DECLARE @IDCT02 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'IDCT-02');
DECLARE @BPCT01 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'BPCT-01');
DECLARE @BPCT02 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'BPCT-02');
DECLARE @MBTN INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'MBT-N');
DECLARE @MBTC INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'MBT-C');
DECLARE @JDOT01 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'JDOT-01');
DECLARE @JDOT02 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'JDOT-02');
DECLARE @VDGC01 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'VDGC-01');
DECLARE @PDMP01 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'PDMP-01');
DECLARE @MCT01 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'MCT-01');
DECLARE @MCT02 INT = (SELECT BerthId FROM BERTHS WHERE BerthCode = 'MCT-02');

-- Get vessel IDs (use random vessels of appropriate types)
DECLARE @ContainerVessel1 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Container' ORDER BY NEWID());
DECLARE @ContainerVessel2 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Container' AND VesselId <> @ContainerVessel1 ORDER BY NEWID());
DECLARE @ContainerVessel3 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Container' AND VesselId NOT IN (@ContainerVessel1, @ContainerVessel2) ORDER BY NEWID());
DECLARE @ContainerVessel4 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Container' AND VesselId NOT IN (@ContainerVessel1, @ContainerVessel2, @ContainerVessel3) ORDER BY NEWID());
DECLARE @BulkVessel1 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Bulk' ORDER BY NEWID());
DECLARE @BulkVessel2 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Bulk' AND VesselId <> @BulkVessel1 ORDER BY NEWID());
DECLARE @TankerVessel1 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Tanker' ORDER BY NEWID());
DECLARE @TankerVessel2 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Tanker' AND VesselId <> @TankerVessel1 ORDER BY NEWID());
DECLARE @GeneralVessel1 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'General' ORDER BY NEWID());
DECLARE @GeneralVessel2 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'General' AND VesselId <> @GeneralVessel1 ORDER BY NEWID());
DECLARE @PassengerVessel1 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Passenger' ORDER BY NEWID());
DECLARE @PassengerVessel2 INT = (SELECT TOP 1 VesselId FROM VESSELS WHERE VesselType = 'Passenger' AND VesselId <> @PassengerVessel1 ORDER BY NEWID());

-- Berthed vessels (currently at berth)
INSERT INTO #ScheduleTemp VALUES
-- Container vessels at Indira Dock and Ballard Pier
(@ContainerVessel1, @IDCT01, DATEADD(HOUR, -6, GETDATE()), DATEADD(HOUR, -6.2, GETDATE()), DATEADD(HOUR, 12, GETDATE()), DATEADD(HOUR, -5.8, GETDATE()), DATEADD(HOUR, -5.5, GETDATE()), NULL, 'Berthed', 1080, 15, 92.50, 1, 0),
(@ContainerVessel2, @BPCT01, DATEADD(HOUR, -8, GETDATE()), DATEADD(HOUR, -7.8, GETDATE()), DATEADD(HOUR, 10, GETDATE()), DATEADD(HOUR, -7.5, GETDATE()), DATEADD(HOUR, -7.2, GETDATE()), NULL, 'Berthed', 1080, 20, 88.75, 1, 0),
-- Bulk vessel at Mumbai Bulk Terminal
(@BulkVessel1, @MBTN, DATEADD(HOUR, -12, GETDATE()), DATEADD(HOUR, -11.8, GETDATE()), DATEADD(HOUR, 24, GETDATE()), DATEADD(HOUR, -11.5, GETDATE()), DATEADD(HOUR, -11.2, GETDATE()), NULL, 'Berthed', 2160, 25, 87.50, 1, 0),
-- Tanker at Jawahar Dweep
(@TankerVessel1, @JDOT01, DATEADD(HOUR, -10, GETDATE()), DATEADD(HOUR, -9.8, GETDATE()), DATEADD(HOUR, 20, GETDATE()), DATEADD(HOUR, -9.5, GETDATE()), DATEADD(HOUR, -9.2, GETDATE()), NULL, 'Berthed', 1800, 30, 89.25, 1, 0),
-- General cargo at Victoria Dock
(@GeneralVessel1, @VDGC01, DATEADD(HOUR, -5, GETDATE()), DATEADD(HOUR, -4.8, GETDATE()), DATEADD(HOUR, 8, GETDATE()), DATEADD(HOUR, -4.7, GETDATE()), DATEADD(HOUR, -4.5, GETDATE()), NULL, 'Berthed', 780, 12, 90.00, 1, 0),
-- Cruise at Mumbai Cruise Terminal
(@PassengerVessel1, @MCT01, DATEADD(HOUR, -3, GETDATE()), DATEADD(HOUR, -2.9, GETDATE()), DATEADD(HOUR, 9, GETDATE()), DATEADD(HOUR, -2.8, GETDATE()), DATEADD(HOUR, -2.6, GETDATE()), NULL, 'Berthed', 720, 8, 91.50, 1, 0);

-- Approaching vessels (arriving soon)
INSERT INTO #ScheduleTemp VALUES
(@ContainerVessel3, @IDCT02, DATEADD(HOUR, 2, GETDATE()), DATEADD(HOUR, 1.8, GETDATE()), DATEADD(HOUR, 18, GETDATE()), NULL, NULL, NULL, 'Approaching', 960, NULL, 93.00, 1, 0),
(@ContainerVessel4, @BPCT02, DATEADD(HOUR, 3, GETDATE()), DATEADD(HOUR, 3.2, GETDATE()), DATEADD(HOUR, 21, GETDATE()), NULL, NULL, NULL, 'Approaching', 1080, NULL, 89.50, 1, 0),
(@BulkVessel2, @MBTC, DATEADD(HOUR, 1, GETDATE()), DATEADD(HOUR, 0.8, GETDATE()), DATEADD(HOUR, 25, GETDATE()), NULL, NULL, NULL, 'Approaching', 1440, NULL, 91.25, 1, 0),
(@TankerVessel2, @JDOT02, DATEADD(HOUR, 4, GETDATE()), DATEADD(HOUR, 4.5, GETDATE()), DATEADD(HOUR, 28, GETDATE()), NULL, NULL, NULL, 'Approaching', 1440, NULL, 85.00, 1, 0),
(@GeneralVessel2, @PDMP01, DATEADD(HOUR, 5, GETDATE()), DATEADD(HOUR, 4.8, GETDATE()), DATEADD(HOUR, 17, GETDATE()), NULL, NULL, NULL, 'Approaching', 720, NULL, 88.00, 1, 0),
(@PassengerVessel2, @MCT02, DATEADD(HOUR, 2.5, GETDATE()), DATEADD(HOUR, 2.3, GETDATE()), DATEADD(HOUR, 14.5, GETDATE()), NULL, NULL, NULL, 'Approaching', 720, NULL, 90.50, 1, 0);

-- Future schedules (Scheduled) - Next 14 days
SET @CurrentDate = DATEADD(DAY, 1, GETDATE());
WHILE @CurrentDate < @EndDate
BEGIN
    -- 6-8 scheduled arrivals per day
    SET @Counter = 0;
    WHILE @Counter < 7
    BEGIN
        SET @VesselId = (SELECT TOP 1 VesselId FROM VESSELS ORDER BY NEWID());
        SET @BerthId = (SELECT TOP 1 BerthId FROM BERTHS WHERE IsActive = 1 ORDER BY NEWID());
        SET @DwellHours = CASE
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Container' THEN 12 + ABS(CHECKSUM(NEWID())) % 18
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Bulk' THEN 24 + ABS(CHECKSUM(NEWID())) % 36
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Tanker' THEN 18 + ABS(CHECKSUM(NEWID())) % 24
            WHEN (SELECT VesselType FROM VESSELS WHERE VesselId = @VesselId) = 'Passenger' THEN 8 + ABS(CHECKSUM(NEWID())) % 12
            ELSE 8 + ABS(CHECKSUM(NEWID())) % 16
        END;
        SET @ETA = DATEADD(HOUR, ABS(CHECKSUM(NEWID())) % 24, @CurrentDate);
        SET @ETD = DATEADD(HOUR, @DwellHours, @ETA);
        SET @Score = 70 + (ABS(CHECKSUM(NEWID())) % 30);

        INSERT INTO #ScheduleTemp VALUES (
            @VesselId, @BerthId, @ETA,
            DATEADD(MINUTE, -30 + ABS(CHECKSUM(NEWID())) % 60, @ETA), -- Larger prediction variance for future
            @ETD,
            NULL, NULL, NULL,
            'Scheduled',
            @DwellHours * 60,
            NULL,
            @Score, 1, 0
        );
        SET @Counter = @Counter + 1;
    END

    SET @CurrentDate = DATEADD(DAY, 1, @CurrentDate);
END

-- Insert all schedules into main table
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, ATD, Status, DwellTime, WaitingTime, OptimizationScore, IsOptimized, ConflictCount)
SELECT VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, ATD, Status, DwellTime, WaitingTime, OptimizationScore, IsOptimized, ConflictCount
FROM #ScheduleTemp
ORDER BY ETA;

-- Add some cancelled schedules
UPDATE TOP (10) VESSEL_SCHEDULE
SET Status = 'Cancelled'
WHERE Status = 'Departed' AND ScheduleId % 30 = 0;

-- Add some conflicts
UPDATE VESSEL_SCHEDULE
SET ConflictCount = 1
WHERE ScheduleId IN (SELECT TOP 8 ScheduleId FROM VESSEL_SCHEDULE WHERE Status IN ('Scheduled', 'Approaching') ORDER BY NEWID());

-- Clean up
DROP TABLE #ScheduleTemp;

-- Display count
SELECT 'Schedules inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM VESSEL_SCHEDULE;
SELECT 'By Status:' AS Info;
SELECT Status, COUNT(*) AS Count FROM VESSEL_SCHEDULE GROUP BY Status;
