-- =============================================
-- SEED DATA: VESSEL SCHEDULES
-- Creates 50+ active schedules to match UI
-- Validates: LOA, Beam, Draft vs Berth limits
-- =============================================

USE [BerthPlanning];
GO

SET NOCOUNT ON;
PRINT '=== SEEDING VESSEL SCHEDULES ===';

DECLARE @Now DATETIME2 = GETUTCDATE();

-- Show terminal/berth summary
PRINT 'Terminal & Berth Summary:';
SELECT t.TerminalCode, t.TerminalName, COUNT(b.BerthId) AS Berths
FROM TERMINALS t
LEFT JOIN BERTHS b ON b.TerminalId = t.TerminalId
GROUP BY t.TerminalCode, t.TerminalName
ORDER BY t.TerminalCode;

-- =============================================
-- BERTHED VESSELS (Fill all berths = 36)
-- =============================================
PRINT '';
PRINT 'Creating BERTHED schedules (all berths)...';

-- Container berths (9) -> Container ships
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT v.VesselId, b.BerthId,
    DATEADD(HOUR, -8 - (ROW_NUMBER() OVER (ORDER BY v.VesselId) % 4), @Now),
    DATEADD(HOUR, -8 - (ROW_NUMBER() OVER (ORDER BY v.VesselId) % 4), @Now),
    DATEADD(HOUR, 6 + (ROW_NUMBER() OVER (ORDER BY v.VesselId) % 6), @Now),
    DATEADD(HOUR, -7 - (ROW_NUMBER() OVER (ORDER BY v.VesselId) % 4), @Now),
    DATEADD(HOUR, -6 - (ROW_NUMBER() OVER (ORDER BY v.VesselId) % 4), @Now),
    'Berthed', 480, 60, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 1
FROM (
    SELECT v.*, ROW_NUMBER() OVER (ORDER BY v.VesselId) AS rn
    FROM VESSELS v WHERE v.VesselType = 'Container Ship'
) v
INNER JOIN (
    SELECT b.*, ROW_NUMBER() OVER (ORDER BY b.BerthId) AS rn
    FROM BERTHS b WHERE b.BerthType = 'Container'
) b ON v.rn = b.rn
WHERE v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft;

DECLARE @ContainerBerthed INT = @@ROWCOUNT;
PRINT 'Container berths filled: ' + CAST(@ContainerBerthed AS VARCHAR);

-- Liquid berths (4) -> Tankers
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT v.VesselId, b.BerthId,
    DATEADD(HOUR, -10, @Now), DATEADD(HOUR, -10, @Now), DATEADD(HOUR, 8, @Now),
    DATEADD(HOUR, -9, @Now), DATEADD(HOUR, -8, @Now), 'Berthed',
    540, 60, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 1
FROM (
    SELECT v.*, ROW_NUMBER() OVER (ORDER BY v.VesselId) AS rn
    FROM VESSELS v WHERE v.VesselType = 'Tanker'
      AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE)
) v
INNER JOIN (
    SELECT b.*, ROW_NUMBER() OVER (ORDER BY b.BerthId) AS rn
    FROM BERTHS b WHERE b.BerthType = 'Liquid Bulk'
      AND b.BerthId NOT IN (SELECT BerthId FROM VESSEL_SCHEDULE WHERE Status = 'Berthed')
) b ON v.rn = b.rn
WHERE v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft;

DECLARE @LiquidBerthed INT = @@ROWCOUNT;
PRINT 'Liquid berths filled: ' + CAST(@LiquidBerthed AS VARCHAR);

-- Dry Bulk + Mechanised berths (8) -> Bulk Carriers
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT v.VesselId, b.BerthId,
    DATEADD(HOUR, -12, @Now), DATEADD(HOUR, -12, @Now), DATEADD(HOUR, 10, @Now),
    DATEADD(HOUR, -11, @Now), DATEADD(HOUR, -10, @Now), 'Berthed',
    600, 60, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 1
FROM (
    SELECT v.*, ROW_NUMBER() OVER (ORDER BY v.VesselId) AS rn
    FROM VESSELS v WHERE v.VesselType = 'Bulk Carrier'
      AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE)
) v
INNER JOIN (
    SELECT b.*, ROW_NUMBER() OVER (ORDER BY b.BerthId) AS rn
    FROM BERTHS b WHERE b.BerthType IN ('Dry Bulk', 'Mechanised Bulk')
      AND b.BerthId NOT IN (SELECT BerthId FROM VESSEL_SCHEDULE WHERE Status = 'Berthed')
) b ON v.rn = b.rn
WHERE v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft;

DECLARE @BulkBerthed INT = @@ROWCOUNT;
PRINT 'Bulk berths filled: ' + CAST(@BulkBerthed AS VARCHAR);

-- LNG berth (1) -> LNG Carrier
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 1 v.VesselId, b.BerthId,
    DATEADD(HOUR, -6, @Now), DATEADD(HOUR, -6, @Now), DATEADD(HOUR, 12, @Now),
    DATEADD(HOUR, -5, @Now), DATEADD(HOUR, -4, @Now), 'Berthed',
    480, 60, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 1
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE b.BerthType = 'LNG' AND v.VesselType = 'LNG Carrier'
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE)
  AND b.BerthId NOT IN (SELECT BerthId FROM VESSEL_SCHEDULE WHERE Status = 'Berthed');

DECLARE @LNGBerthed INT = @@ROWCOUNT;
PRINT 'LNG berth filled: ' + CAST(@LNGBerthed AS VARCHAR);

-- SPM berths (2) -> Tankers (remaining)
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT v.VesselId, b.BerthId,
    DATEADD(HOUR, -14, @Now), DATEADD(HOUR, -14, @Now), DATEADD(HOUR, 12, @Now),
    DATEADD(HOUR, -13, @Now), DATEADD(HOUR, -12, @Now), 'Berthed',
    720, 60, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 1
FROM (
    SELECT v.*, ROW_NUMBER() OVER (ORDER BY v.VesselId) AS rn
    FROM VESSELS v WHERE v.VesselType = 'Tanker'
      AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE)
) v
INNER JOIN (
    SELECT b.*, ROW_NUMBER() OVER (ORDER BY b.BerthId) AS rn
    FROM BERTHS b WHERE b.BerthType = 'SPM'
      AND b.BerthId NOT IN (SELECT BerthId FROM VESSEL_SCHEDULE WHERE Status = 'Berthed')
) b ON v.rn = b.rn
WHERE v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft;

DECLARE @SPMBerthed INT = @@ROWCOUNT;
PRINT 'SPM berths filled: ' + CAST(@SPMBerthed AS VARCHAR);

-- RO-RO berth (1) -> Car Carrier
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 1 v.VesselId, b.BerthId,
    DATEADD(HOUR, -4, @Now), DATEADD(HOUR, -4, @Now), DATEADD(HOUR, 8, @Now),
    DATEADD(HOUR, -3, @Now), DATEADD(HOUR, -2, @Now), 'Berthed',
    360, 60, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 1
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE b.BerthType = 'RO-RO' AND v.VesselType = 'Car Carrier'
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE)
  AND b.BerthId NOT IN (SELECT BerthId FROM VESSEL_SCHEDULE WHERE Status = 'Berthed');

DECLARE @ROROBerthed INT = @@ROWCOUNT;
PRINT 'RO-RO berth filled: ' + CAST(@ROROBerthed AS VARCHAR);

-- Multipurpose + Break Bulk berths (10) -> General Cargo + remaining Car Carriers
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT v.VesselId, b.BerthId,
    DATEADD(HOUR, -6, @Now), DATEADD(HOUR, -6, @Now), DATEADD(HOUR, 6, @Now),
    DATEADD(HOUR, -5, @Now), DATEADD(HOUR, -4, @Now), 'Berthed',
    360, 60, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 1
FROM (
    SELECT v.*, ROW_NUMBER() OVER (ORDER BY v.VesselId) AS rn
    FROM VESSELS v WHERE v.VesselType IN ('General Cargo', 'Car Carrier')
      AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE)
) v
INNER JOIN (
    SELECT b.*, ROW_NUMBER() OVER (ORDER BY b.BerthId) AS rn
    FROM BERTHS b WHERE b.BerthType IN ('Multipurpose', 'Break Bulk')
      AND b.BerthId NOT IN (SELECT BerthId FROM VESSEL_SCHEDULE WHERE Status = 'Berthed')
) b ON v.rn = b.rn
WHERE v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft;

DECLARE @MPBerthed INT = @@ROWCOUNT;
PRINT 'Multipurpose berths filled: ' + CAST(@MPBerthed AS VARCHAR);

-- =============================================
-- APPROACHING VESSELS (10 vessels)
-- =============================================
PRINT '';
PRINT 'Creating APPROACHING schedules...';

-- Approaching Container Ships
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 4 v.VesselId, b.BerthId,
    DATEADD(MINUTE, -45, @Now), DATEADD(MINUTE, -45, @Now), DATEADD(HOUR, 10, @Now),
    DATEADD(MINUTE, -30, @Now), 'Approaching',
    480, 45, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 0
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE v.VesselType = 'Container Ship' AND b.BerthType = 'Container'
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE);

DECLARE @ApproachContainer INT = @@ROWCOUNT;
PRINT 'Approaching containers: ' + CAST(@ApproachContainer AS VARCHAR);

-- Approaching Tankers
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 2 v.VesselId, b.BerthId,
    DATEADD(MINUTE, -30, @Now), DATEADD(MINUTE, -30, @Now), DATEADD(HOUR, 12, @Now),
    DATEADD(MINUTE, -15, @Now), 'Approaching',
    540, 30, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 0
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE v.VesselType = 'Tanker' AND b.BerthType IN ('Liquid Bulk', 'SPM')
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE);

DECLARE @ApproachTanker INT = @@ROWCOUNT;
PRINT 'Approaching tankers: ' + CAST(@ApproachTanker AS VARCHAR);

-- Approaching Bulk Carriers
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 2 v.VesselId, b.BerthId,
    DATEADD(MINUTE, -60, @Now), DATEADD(MINUTE, -60, @Now), DATEADD(HOUR, 14, @Now),
    DATEADD(MINUTE, -45, @Now), 'Approaching',
    600, 45, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 0
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE v.VesselType = 'Bulk Carrier' AND b.BerthType IN ('Dry Bulk', 'Mechanised Bulk')
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE);

DECLARE @ApproachBulk INT = @@ROWCOUNT;
PRINT 'Approaching bulk: ' + CAST(@ApproachBulk AS VARCHAR);

-- Approaching LNG
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, ATA, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 2 v.VesselId, b.BerthId,
    DATEADD(MINUTE, -20, @Now), DATEADD(MINUTE, -20, @Now), DATEADD(HOUR, 16, @Now),
    DATEADD(MINUTE, -10, @Now), 'Approaching',
    480, 20, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 0
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE v.VesselType = 'LNG Carrier' AND b.BerthType = 'LNG'
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE);

DECLARE @ApproachLNG INT = @@ROWCOUNT;
PRINT 'Approaching LNG: ' + CAST(@ApproachLNG AS VARCHAR);

-- =============================================
-- SCHEDULED VESSELS (In Queue - 10 vessels)
-- =============================================
PRINT '';
PRINT 'Creating SCHEDULED (queue) schedules...';

-- Scheduled Container Ships
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 3 v.VesselId, b.BerthId,
    DATEADD(HOUR, 3, @Now), DATEADD(HOUR, 3, @Now), DATEADD(HOUR, 13, @Now),
    'Scheduled', 480, 0, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 0
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE v.VesselType = 'Container Ship' AND b.BerthType = 'Container'
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE);

DECLARE @ScheduledContainer INT = @@ROWCOUNT;
PRINT 'Scheduled containers: ' + CAST(@ScheduledContainer AS VARCHAR);

-- Scheduled LNG
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 2 v.VesselId, b.BerthId,
    DATEADD(HOUR, 5, @Now), DATEADD(HOUR, 5, @Now), DATEADD(HOUR, 17, @Now),
    'Scheduled', 480, 0, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 0
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE v.VesselType = 'LNG Carrier' AND b.BerthType = 'LNG'
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE);

DECLARE @ScheduledLNG INT = @@ROWCOUNT;
PRINT 'Scheduled LNG: ' + CAST(@ScheduledLNG AS VARCHAR);

-- Scheduled Car Carriers
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 3 v.VesselId, b.BerthId,
    DATEADD(HOUR, 4, @Now), DATEADD(HOUR, 4, @Now), DATEADD(HOUR, 12, @Now),
    'Scheduled', 360, 0, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 0
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE v.VesselType = 'Car Carrier' AND b.BerthType IN ('RO-RO', 'Multipurpose')
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE);

DECLARE @ScheduledCar INT = @@ROWCOUNT;
PRINT 'Scheduled car carriers: ' + CAST(@ScheduledCar AS VARCHAR);

-- Scheduled General Cargo
INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD, Status, DwellTime, WaitingTime, CargoType, CargoQuantity, CargoUnit, PortCode, IsOptimized)
SELECT TOP 2 v.VesselId, b.BerthId,
    DATEADD(HOUR, 6, @Now), DATEADD(HOUR, 6, @Now), DATEADD(HOUR, 14, @Now),
    'Scheduled', 360, 0, v.CargoType, v.CargoVolume, v.CargoUnit, 'INMUN', 0
FROM VESSELS v
CROSS JOIN BERTHS b
WHERE v.VesselType = 'General Cargo' AND b.BerthType IN ('Multipurpose', 'Break Bulk')
  AND v.LOA <= b.MaxLOA AND v.Beam <= b.MaxBeam AND v.Draft <= b.MaxDraft
  AND v.VesselId NOT IN (SELECT VesselId FROM VESSEL_SCHEDULE);

DECLARE @ScheduledGeneral INT = @@ROWCOUNT;
PRINT 'Scheduled general cargo: ' + CAST(@ScheduledGeneral AS VARCHAR);

-- =============================================
-- DO NOT DELETE UNUSED VESSELS (keep all 60)
-- =============================================
PRINT '';
PRINT '=== FINAL RESULTS ===';

SELECT
    t.TerminalCode,
    t.TerminalName,
    (SELECT COUNT(*) FROM BERTHS WHERE TerminalId = t.TerminalId) AS Berths,
    COUNT(CASE WHEN vs.Status = 'Berthed' THEN 1 END) AS Berthed,
    COUNT(CASE WHEN vs.Status = 'Approaching' THEN 1 END) AS Approaching,
    COUNT(CASE WHEN vs.Status = 'Scheduled' THEN 1 END) AS InQueue,
    COUNT(vs.ScheduleId) AS Total
FROM TERMINALS t
LEFT JOIN BERTHS b ON b.TerminalId = t.TerminalId
LEFT JOIN VESSEL_SCHEDULE vs ON vs.BerthId = b.BerthId
GROUP BY t.TerminalId, t.TerminalCode, t.TerminalName
ORDER BY t.TerminalCode;

SELECT Status, COUNT(*) AS Count FROM VESSEL_SCHEDULE GROUP BY Status;

DECLARE @TotalSchedules INT;
SELECT @TotalSchedules = COUNT(*) FROM VESSEL_SCHEDULE;
PRINT '';
PRINT 'Total Schedules Created: ' + CAST(@TotalSchedules AS VARCHAR);

SELECT 'VESSELS' AS [Table], COUNT(*) AS Records FROM VESSELS
UNION ALL SELECT 'SCHEDULES', COUNT(*) FROM VESSEL_SCHEDULE;
GO
