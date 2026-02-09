-- =============================================
-- BERTH PLANNING SYSTEM - SQL JOBS
-- Purpose: Automated vessel movement simulation for hackathon demo
-- Moves vessels through lifecycle: Scheduled -> Approaching -> Berthed -> Departed
-- Auto-assigns berths & resources, generates daily schedules
-- Version: 1.0
-- Date: 2026-02-04
-- =============================================

USE [BerthPlanning]; -- Change this to your database name
GO

-- =============================================
-- JOB 1: sp_Job_AdvanceApproaching
-- Move Scheduled -> Approaching
-- Vessels whose ETA is within 2 hours are "approaching"
-- =============================================
CREATE OR ALTER PROCEDURE sp_Job_AdvanceApproaching
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Now DATETIME2 = GETUTCDATE();
    DECLARE @Count INT = 0;
    DECLARE @ScheduleId INT;
    DECLARE @VesselName NVARCHAR(200);
    DECLARE @ETA DATETIME2;

    -- Cursor through schedules that should transition to Approaching
    DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
        SELECT vs.ScheduleId, v.VesselName, vs.ETA
        FROM dbo.VESSEL_SCHEDULE vs
        INNER JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
        WHERE vs.Status = 'Scheduled'
          AND vs.ETA <= DATEADD(HOUR, 2, @Now)
          AND vs.ETA >= DATEADD(HOUR, -6, @Now); -- Don't advance very old ones

    OPEN cur;
    FETCH NEXT FROM cur INTO @ScheduleId, @VesselName, @ETA;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        BEGIN TRY
            -- Set ATA close to ETA with small random variance (-30 to +15 mins)
            DECLARE @ATA DATETIME2 = DATEADD(MINUTE,
                -(ABS(CHECKSUM(NEWID()) % 30)) + (ABS(CHECKSUM(NEWID()) % 15)),
                @ETA);

            -- If ATA would be in the future, cap it to now
            IF @ATA > @Now SET @ATA = @Now;

            -- Update schedule to Approaching
            UPDATE dbo.VESSEL_SCHEDULE
            SET Status = 'Approaching',
                ATA = @ATA,
                AnchorageArrival = DATEADD(MINUTE, -(ABS(CHECKSUM(NEWID()) % 20) + 10), @ATA),
                UpdatedAt = @Now
            WHERE ScheduleId = @ScheduleId;

            -- Create alert
            INSERT INTO dbo.ALERTS_NOTIFICATIONS (AlertType, RelatedEntityId, EntityType, Severity, Message)
            VALUES ('VesselApproaching', @ScheduleId, 'Schedule', 'Medium',
                'Vessel ' + @VesselName + ' is now approaching port. ETA: ' + CONVERT(NVARCHAR(30), @ETA, 120));

            SET @Count = @Count + 1;
        END TRY
        BEGIN CATCH
            -- Log error but continue with next vessel
            PRINT 'Error advancing schedule ' + CAST(@ScheduleId AS VARCHAR) + ': ' + ERROR_MESSAGE();
        END CATCH

        FETCH NEXT FROM cur INTO @ScheduleId, @VesselName, @ETA;
    END

    CLOSE cur;
    DEALLOCATE cur;

    SELECT @Count AS VesselsAdvancedToApproaching;
END
GO

-- =============================================
-- JOB 2: sp_Job_BerthApproaching
-- Move Approaching -> Berthed
-- Vessels that have been approaching long enough get berthed
-- =============================================
CREATE OR ALTER PROCEDURE sp_Job_BerthApproaching
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Now DATETIME2 = GETUTCDATE();
    DECLARE @Count INT = 0;
    DECLARE @ScheduleId INT;
    DECLARE @VesselId INT;
    DECLARE @VesselName NVARCHAR(200);
    DECLARE @BerthId INT;
    DECLARE @ATA DATETIME2;
    DECLARE @ETA DATETIME2;
    DECLARE @VesselLOA DECIMAL(8,2);
    DECLARE @VesselDraft DECIMAL(6,2);
    DECLARE @VesselType NVARCHAR(50);

    -- Cursor through approaching vessels ready to berth
    -- Berth after 30-90 minutes of approaching (randomized per vessel)
    DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
        SELECT vs.ScheduleId, vs.VesselId, v.VesselName, vs.BerthId, vs.ATA, vs.ETA,
               v.LOA, v.Draft, v.VesselType
        FROM dbo.VESSEL_SCHEDULE vs
        INNER JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
        WHERE vs.Status = 'Approaching'
          AND vs.ATA IS NOT NULL
          AND DATEDIFF(MINUTE, vs.ATA, @Now) >= 30; -- At least 30 mins since arrival

    OPEN cur;
    FETCH NEXT FROM cur INTO @ScheduleId, @VesselId, @VesselName, @BerthId, @ATA, @ETA,
                             @VesselLOA, @VesselDraft, @VesselType;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        BEGIN TRY
            -- If no berth assigned yet, find one
            IF @BerthId IS NULL
            BEGIN
                -- Find compatible available berth
                SELECT TOP 1 @BerthId = b.BerthId
                FROM dbo.BERTHS b
                INNER JOIN dbo.TERMINALS t ON b.TerminalId = t.TerminalId
                WHERE b.IsActive = 1
                  AND b.Length >= @VesselLOA
                  AND b.MaxDraft >= @VesselDraft
                  AND (b.BerthType = @VesselType OR b.BerthType = 'General')
                  AND NOT EXISTS (
                      SELECT 1 FROM dbo.VESSEL_SCHEDULE vs2
                      WHERE vs2.BerthId = b.BerthId
                        AND vs2.Status IN ('Berthed', 'Approaching')
                        AND vs2.ScheduleId != @ScheduleId
                  )
                ORDER BY
                    CASE WHEN b.BerthType = @VesselType THEN 0 ELSE 1 END, -- Prefer type match
                    b.Length ASC; -- Prefer smallest fitting berth

                IF @BerthId IS NULL
                BEGIN
                    -- No berth available, try any fitting berth ignoring type
                    SELECT TOP 1 @BerthId = b.BerthId
                    FROM dbo.BERTHS b
                    WHERE b.IsActive = 1
                      AND b.Length >= @VesselLOA
                      AND b.MaxDraft >= @VesselDraft
                      AND NOT EXISTS (
                          SELECT 1 FROM dbo.VESSEL_SCHEDULE vs2
                          WHERE vs2.BerthId = b.BerthId
                            AND vs2.Status IN ('Berthed', 'Approaching')
                            AND vs2.ScheduleId != @ScheduleId
                      )
                    ORDER BY b.Length ASC;
                END

                -- Update berth assignment
                IF @BerthId IS NOT NULL
                BEGIN
                    UPDATE dbo.VESSEL_SCHEDULE
                    SET BerthId = @BerthId
                    WHERE ScheduleId = @ScheduleId;
                END
                ELSE
                BEGIN
                    -- Skip - no berth available
                    FETCH NEXT FROM cur INTO @ScheduleId, @VesselId, @VesselName, @BerthId, @ATA, @ETA,
                                             @VesselLOA, @VesselDraft, @VesselType;
                    CONTINUE;
                END
            END

            -- Calculate berthing time (30-90 mins after ATA)
            DECLARE @WaitMins INT = 30 + (ABS(CHECKSUM(NEWID()) % 61)); -- 30-90 mins
            DECLARE @ATB DATETIME2 = DATEADD(MINUTE, @WaitMins, @ATA);
            IF @ATB > @Now SET @ATB = @Now;

            -- Calculate lifecycle timestamps
            DECLARE @PilotBoardingTime DATETIME2 = DATEADD(MINUTE, -20, @ATB);
            DECLARE @BerthArrivalTime DATETIME2 = @ATB;
            DECLARE @FirstLineTime DATETIME2 = DATEADD(MINUTE, 5, @ATB);
            DECLARE @AllFastTime DATETIME2 = DATEADD(MINUTE, 15, @ATB);
            DECLARE @CargoStartTime DATETIME2 = DATEADD(MINUTE, 30, @AllFastTime);

            -- Determine cargo operation details from vessel
            DECLARE @CargoType NVARCHAR(100);
            DECLARE @CargoOperation NVARCHAR(50);
            DECLARE @TugsNeeded INT;
            DECLARE @PilotsNeeded INT;
            DECLARE @ArrivalDraft DECIMAL(6,2);

            SELECT @CargoType = COALESCE(CargoType, VesselType),
                   @ArrivalDraft = Draft
            FROM dbo.VESSELS WHERE VesselId = @VesselId;

            -- Assign tugs based on vessel size
            SET @TugsNeeded = CASE
                WHEN @VesselLOA > 300 THEN 3
                WHEN @VesselLOA > 200 THEN 2
                ELSE 1
            END;
            SET @PilotsNeeded = CASE WHEN @VesselLOA > 250 THEN 2 ELSE 1 END;
            SET @CargoOperation = CASE
                WHEN ABS(CHECKSUM(NEWID()) % 3) = 0 THEN 'Loading'
                WHEN ABS(CHECKSUM(NEWID()) % 3) = 1 THEN 'Discharge'
                ELSE 'Both'
            END;

            -- Calculate waiting time
            DECLARE @WaitingHours DECIMAL(8,2) = CAST(DATEDIFF(MINUTE, @ATA, @ATB) AS DECIMAL(8,2)) / 60.0;
            DECLARE @ETAVariance DECIMAL(8,2) = CAST(DATEDIFF(MINUTE, @ETA, @ATA) AS DECIMAL(8,2)) / 60.0;
            DECLARE @BerthingDelay INT = DATEDIFF(MINUTE, @ATA, @ATB);

            -- Update schedule to Berthed with all lifecycle data
            UPDATE dbo.VESSEL_SCHEDULE
            SET Status = 'Berthed',
                ATB = @ATB,
                PilotBoardingTime = @PilotBoardingTime,
                BerthArrivalTime = @BerthArrivalTime,
                FirstLineTime = @FirstLineTime,
                AllFastTime = @AllFastTime,
                CargoStartTime = @CargoStartTime,
                CargoType = @CargoType,
                CargoOperation = @CargoOperation,
                TugsAssigned = @TugsNeeded,
                PilotsAssigned = @PilotsNeeded,
                WaitingTimeHours = @WaitingHours,
                ETAVarianceHours = @ETAVariance,
                BerthingDelayMins = @BerthingDelay,
                ArrivalDraft = @ArrivalDraft,
                UpdatedAt = @Now
            WHERE ScheduleId = @ScheduleId;

            -- Allocate resources: Pilots
            DECLARE @ResourceId INT;
            DECLARE @PilotCount INT = 0;

            DECLARE resCur CURSOR LOCAL FAST_FORWARD FOR
                SELECT TOP (@PilotsNeeded) ResourceId
                FROM dbo.RESOURCES
                WHERE ResourceType = 'Pilot'
                  AND IsAvailable = 1
                  AND ResourceId NOT IN (
                      SELECT ResourceId FROM dbo.RESOURCE_ALLOCATION
                      WHERE Status IN ('Allocated', 'InUse')
                        AND AllocatedTo > @Now
                  )
                ORDER BY NEWID();

            OPEN resCur;
            FETCH NEXT FROM resCur INTO @ResourceId;
            WHILE @@FETCH_STATUS = 0
            BEGIN
                INSERT INTO dbo.RESOURCE_ALLOCATION (ScheduleId, ResourceId, AllocatedFrom, AllocatedTo, Quantity, Status)
                VALUES (@ScheduleId, @ResourceId, @ATB, DATEADD(HOUR, 24, @ATB), 1, 'InUse');
                SET @PilotCount = @PilotCount + 1;
                FETCH NEXT FROM resCur INTO @ResourceId;
            END
            CLOSE resCur;
            DEALLOCATE resCur;

            -- Allocate resources: Tugboats
            DECLARE @TugCount INT = 0;

            DECLARE tugCur CURSOR LOCAL FAST_FORWARD FOR
                SELECT TOP (@TugsNeeded) ResourceId
                FROM dbo.RESOURCES
                WHERE ResourceType = 'Tugboat'
                  AND IsAvailable = 1
                  AND ResourceId NOT IN (
                      SELECT ResourceId FROM dbo.RESOURCE_ALLOCATION
                      WHERE Status IN ('Allocated', 'InUse')
                        AND AllocatedTo > @Now
                  )
                ORDER BY NEWID();

            OPEN tugCur;
            FETCH NEXT FROM tugCur INTO @ResourceId;
            WHILE @@FETCH_STATUS = 0
            BEGIN
                INSERT INTO dbo.RESOURCE_ALLOCATION (ScheduleId, ResourceId, AllocatedFrom, AllocatedTo, Quantity, Status)
                VALUES (@ScheduleId, @ResourceId, @ATB, DATEADD(HOUR, 24, @ATB), 1, 'InUse');
                SET @TugCount = @TugCount + 1;
                FETCH NEXT FROM tugCur INTO @ResourceId;
            END
            CLOSE tugCur;
            DEALLOCATE tugCur;

            -- Allocate resources: Cranes (1-3 based on vessel type)
            DECLARE @CranesNeeded INT = CASE
                WHEN @VesselType IN ('Container', 'Bulk') THEN 2 + (ABS(CHECKSUM(NEWID()) % 2))
                ELSE 1
            END;
            DECLARE @CraneCount INT = 0;

            DECLARE craneCur CURSOR LOCAL FAST_FORWARD FOR
                SELECT TOP (@CranesNeeded) ResourceId
                FROM dbo.RESOURCES
                WHERE ResourceType = 'Crane'
                  AND IsAvailable = 1
                  AND ResourceId NOT IN (
                      SELECT ResourceId FROM dbo.RESOURCE_ALLOCATION
                      WHERE Status IN ('Allocated', 'InUse')
                        AND AllocatedTo > @Now
                  )
                ORDER BY NEWID();

            OPEN craneCur;
            FETCH NEXT FROM craneCur INTO @ResourceId;
            WHILE @@FETCH_STATUS = 0
            BEGIN
                INSERT INTO dbo.RESOURCE_ALLOCATION (ScheduleId, ResourceId, AllocatedFrom, AllocatedTo, Quantity, Status)
                VALUES (@ScheduleId, @ResourceId, @ATB, DATEADD(HOUR, 24, @ATB), 1, 'InUse');
                SET @CraneCount = @CraneCount + 1;
                FETCH NEXT FROM craneCur INTO @ResourceId;
            END
            CLOSE craneCur;
            DEALLOCATE craneCur;

            -- Create alert
            INSERT INTO dbo.ALERTS_NOTIFICATIONS (AlertType, RelatedEntityId, EntityType, Severity, Message)
            VALUES ('VesselBerthed', @ScheduleId, 'Schedule', 'Low',
                'Vessel ' + @VesselName + ' has berthed. Resources: '
                + CAST(@PilotCount AS VARCHAR) + ' pilots, '
                + CAST(@TugCount AS VARCHAR) + ' tugs, '
                + CAST(@CraneCount AS VARCHAR) + ' cranes assigned.');

            SET @Count = @Count + 1;
        END TRY
        BEGIN CATCH
            PRINT 'Error berthing schedule ' + CAST(@ScheduleId AS VARCHAR) + ': ' + ERROR_MESSAGE();
        END CATCH

        FETCH NEXT FROM cur INTO @ScheduleId, @VesselId, @VesselName, @BerthId, @ATA, @ETA,
                                 @VesselLOA, @VesselDraft, @VesselType;
    END

    CLOSE cur;
    DEALLOCATE cur;

    SELECT @Count AS VesselsBerthed;
END
GO

-- =============================================
-- JOB 3: sp_Job_DepartBerthed
-- Move Berthed -> Departed
-- Vessels whose ETD has passed or dwell time exceeded
-- =============================================
CREATE OR ALTER PROCEDURE sp_Job_DepartBerthed
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Now DATETIME2 = GETUTCDATE();
    DECLARE @Count INT = 0;
    DECLARE @ScheduleId INT;
    DECLARE @VesselId INT;
    DECLARE @VesselName NVARCHAR(200);
    DECLARE @BerthId INT;
    DECLARE @ATB DATETIME2;
    DECLARE @ATA DATETIME2;
    DECLARE @ETA DATETIME2;
    DECLARE @ETD DATETIME2;
    DECLARE @DwellTime INT;

    -- Cursor through berthed vessels ready to depart
    DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
        SELECT vs.ScheduleId, vs.VesselId, v.VesselName, vs.BerthId,
               vs.ATB, vs.ATA, vs.ETA, vs.ETD, vs.DwellTime
        FROM dbo.VESSEL_SCHEDULE vs
        INNER JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
        WHERE vs.Status = 'Berthed'
          AND vs.ATB IS NOT NULL
          AND (
              -- ETD has passed
              (vs.ETD IS NOT NULL AND vs.ETD <= @Now)
              -- OR dwell time exceeded (if DwellTime set)
              OR (vs.DwellTime IS NOT NULL AND DATEADD(MINUTE, vs.DwellTime, vs.ATB) <= @Now)
              -- OR been berthed for at least 8 hours (fallback)
              OR DATEDIFF(HOUR, vs.ATB, @Now) >= 8
          );

    OPEN cur;
    FETCH NEXT FROM cur INTO @ScheduleId, @VesselId, @VesselName, @BerthId,
                             @ATB, @ATA, @ETA, @ETD, @DwellTime;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        BEGIN TRY
            -- Calculate departure time
            DECLARE @ATD DATETIME2;
            IF @ETD IS NOT NULL AND @ETD <= @Now
                SET @ATD = DATEADD(MINUTE, ABS(CHECKSUM(NEWID()) % 30), @ETD); -- Depart 0-30 mins after ETD
            ELSE IF @DwellTime IS NOT NULL
                SET @ATD = DATEADD(MINUTE, @DwellTime + (ABS(CHECKSUM(NEWID()) % 30)), @ATB);
            ELSE
                SET @ATD = @Now;

            -- Don't set ATD in the future
            IF @ATD > @Now SET @ATD = @Now;

            -- Calculate cargo complete time (1-2 hours before departure)
            DECLARE @CargoCompleteTime DATETIME2 = DATEADD(MINUTE, -(60 + ABS(CHECKSUM(NEWID()) % 60)), @ATD);
            IF @CargoCompleteTime < @ATB SET @CargoCompleteTime = DATEADD(MINUTE, 30, @ATB);

            -- Calculate actual metrics
            DECLARE @ActualDwellMins INT = DATEDIFF(MINUTE, @ATB, @ATD);
            DECLARE @ActualWaitMins INT = CASE WHEN @ATA IS NOT NULL AND @ATB IS NOT NULL
                                               THEN DATEDIFF(MINUTE, @ATA, @ATB) ELSE 0 END;
            DECLARE @DwellHours DECIMAL(8,2) = CAST(@ActualDwellMins AS DECIMAL(8,2)) / 60.0;
            DECLARE @WaitHours DECIMAL(8,2) = CAST(@ActualWaitMins AS DECIMAL(8,2)) / 60.0;
            DECLARE @ETAVar DECIMAL(8,2) = CASE WHEN @ATA IS NOT NULL AND @ETA IS NOT NULL
                                                THEN CAST(DATEDIFF(MINUTE, @ETA, @ATA) AS DECIMAL(8,2)) / 60.0
                                                ELSE 0 END;
            DECLARE @DepartureDraft DECIMAL(6,2);
            SELECT @DepartureDraft = Draft - (ABS(CHECKSUM(NEWID()) % 20) * 0.1) FROM dbo.VESSELS WHERE VesselId = @VesselId;
            IF @DepartureDraft < 3.0 SET @DepartureDraft = 3.0;

            -- ETA Accuracy
            DECLARE @ETAAccuracy DECIMAL(5,2) = CASE
                WHEN @ATA IS NOT NULL AND @ETA IS NOT NULL AND @ATA <= @ETA THEN 100.0
                WHEN @ATA IS NOT NULL AND @ETA IS NOT NULL
                    THEN CASE
                        WHEN DATEDIFF(MINUTE, @ETA, @ATD) > 0
                            THEN 100.0 - (CAST(DATEDIFF(MINUTE, @ETA, @ATA) AS FLOAT) / NULLIF(DATEDIFF(MINUTE, @ETA, @ATD), 0) * 100.0)
                        ELSE 50.0
                    END
                ELSE 80.0
            END;
            IF @ETAAccuracy < 0 SET @ETAAccuracy = 0;
            IF @ETAAccuracy > 100 SET @ETAAccuracy = 100;

            -- Update schedule to Departed
            UPDATE dbo.VESSEL_SCHEDULE
            SET Status = 'Departed',
                ATD = @ATD,
                CargoCompleteTime = @CargoCompleteTime,
                DwellTime = @ActualDwellMins,
                WaitingTime = @ActualWaitMins,
                DwellTimeHours = @DwellHours,
                WaitingTimeHours = @WaitHours,
                ETAVarianceHours = @ETAVar,
                DepartureDraft = @DepartureDraft,
                UpdatedAt = @Now
            WHERE ScheduleId = @ScheduleId;

            -- Record in history
            INSERT INTO dbo.VESSEL_HISTORY (VesselId, BerthId, VisitDate, ActualDwellTime, ActualWaitingTime, ETAAccuracy)
            VALUES (@VesselId, @BerthId, @ATD,
                    CASE WHEN @ActualDwellMins > 0 THEN @ActualDwellMins ELSE 1 END, -- Ensure positive
                    @ActualWaitMins, @ETAAccuracy);

            -- Release resources
            UPDATE dbo.RESOURCE_ALLOCATION
            SET Status = 'Released'
            WHERE ScheduleId = @ScheduleId
              AND Status IN ('Allocated', 'InUse');

            -- Create alert
            INSERT INTO dbo.ALERTS_NOTIFICATIONS (AlertType, RelatedEntityId, EntityType, Severity, Message)
            VALUES ('VesselDeparted', @ScheduleId, 'Schedule', 'Low',
                'Vessel ' + @VesselName + ' has departed. Dwell: ' + CAST(@DwellHours AS VARCHAR) + 'h, Wait: ' + CAST(@WaitHours AS VARCHAR) + 'h');

            SET @Count = @Count + 1;
        END TRY
        BEGIN CATCH
            PRINT 'Error departing schedule ' + CAST(@ScheduleId AS VARCHAR) + ': ' + ERROR_MESSAGE();
        END CATCH

        FETCH NEXT FROM cur INTO @ScheduleId, @VesselId, @VesselName, @BerthId,
                                 @ATB, @ATA, @ETA, @ETD, @DwellTime;
    END

    CLOSE cur;
    DEALLOCATE cur;

    SELECT @Count AS VesselsDeparted;
END
GO

-- =============================================
-- JOB 4: sp_Job_GenerateDailySchedules
-- Auto-create vessel schedules for upcoming days
-- Generates 5-8 schedules per day for next 7 days
-- =============================================
CREATE OR ALTER PROCEDURE sp_Job_GenerateDailySchedules
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Now DATETIME2 = GETUTCDATE();
    DECLARE @TotalCreated INT = 0;
    DECLARE @DayOffset INT = 0;

    -- Generate for today + next 7 days
    WHILE @DayOffset <= 7
    BEGIN
        DECLARE @TargetDate DATE = CAST(DATEADD(DAY, @DayOffset, @Now) AS DATE);

        -- Check how many schedules already exist for this date
        DECLARE @ExistingCount INT;
        SELECT @ExistingCount = COUNT(*)
        FROM dbo.VESSEL_SCHEDULE
        WHERE CAST(ETA AS DATE) = @TargetDate
          AND Status != 'Cancelled';

        -- Only generate if fewer than 5 schedules exist for that day
        IF @ExistingCount < 5
        BEGIN
            DECLARE @ToGenerate INT = (5 + ABS(CHECKSUM(NEWID()) % 4)) - @ExistingCount; -- Generate 5-8 total
            IF @ToGenerate < 1 SET @ToGenerate = 1;

            DECLARE @Generated INT = 0;
            DECLARE @Attempts INT = 0;

            WHILE @Generated < @ToGenerate AND @Attempts < @ToGenerate * 3
            BEGIN
                SET @Attempts = @Attempts + 1;

                -- Pick a random vessel not currently active
                DECLARE @VesselId INT;
                DECLARE @VesselLOA DECIMAL(8,2);
                DECLARE @VesselDraft DECIMAL(6,2);
                DECLARE @VesselType NVARCHAR(50);
                DECLARE @VesselCargoType NVARCHAR(100);
                DECLARE @VesselName NVARCHAR(200);

                SELECT TOP 1
                    @VesselId = VesselId,
                    @VesselLOA = LOA,
                    @VesselDraft = Draft,
                    @VesselType = VesselType,
                    @VesselCargoType = COALESCE(CargoType, VesselType),
                    @VesselName = VesselName
                FROM dbo.VESSELS
                WHERE VesselId NOT IN (
                    SELECT VesselId FROM dbo.VESSEL_SCHEDULE
                    WHERE Status IN ('Scheduled', 'Approaching', 'Berthed')
                )
                AND VesselId NOT IN (
                    SELECT VesselId FROM dbo.VESSEL_SCHEDULE
                    WHERE CAST(ETA AS DATE) = @TargetDate
                      AND Status != 'Cancelled'
                )
                ORDER BY NEWID();

                IF @VesselId IS NULL
                BEGIN
                    -- All vessels busy, just pick any vessel
                    SELECT TOP 1
                        @VesselId = VesselId,
                        @VesselLOA = LOA,
                        @VesselDraft = Draft,
                        @VesselType = VesselType,
                        @VesselCargoType = COALESCE(CargoType, VesselType),
                        @VesselName = VesselName
                    FROM dbo.VESSELS
                    ORDER BY NEWID();
                END

                IF @VesselId IS NULL BREAK; -- No vessels at all

                -- Find compatible berth
                DECLARE @BerthId INT = NULL;
                DECLARE @ETATime DATETIME2;
                DECLARE @ETDTime DATETIME2;
                DECLARE @DwellMins INT;

                -- Determine dwell time by vessel type
                SET @DwellMins = CASE @VesselType
                    WHEN 'Container' THEN 720 + (ABS(CHECKSUM(NEWID()) % 720))    -- 12-24h
                    WHEN 'Bulk' THEN 1440 + (ABS(CHECKSUM(NEWID()) % 1440))       -- 24-48h
                    WHEN 'Tanker' THEN 1080 + (ABS(CHECKSUM(NEWID()) % 1080))     -- 18-36h
                    WHEN 'General' THEN 480 + (ABS(CHECKSUM(NEWID()) % 480))      -- 8-16h
                    WHEN 'Passenger' THEN 480 + (ABS(CHECKSUM(NEWID()) % 240))    -- 8-12h
                    WHEN 'Ro-Ro' THEN 360 + (ABS(CHECKSUM(NEWID()) % 360))        -- 6-12h
                    ELSE 480 + (ABS(CHECKSUM(NEWID()) % 960))                     -- 8-24h
                END;

                -- Spread ETAs across the day: morning rush (06-10), afternoon (13-17), evening (20-23)
                DECLARE @TimeSlot INT = ABS(CHECKSUM(NEWID()) % 3);
                DECLARE @HourBase INT = CASE @TimeSlot
                    WHEN 0 THEN 6  + (ABS(CHECKSUM(NEWID()) % 5))  -- 06-10
                    WHEN 1 THEN 13 + (ABS(CHECKSUM(NEWID()) % 5))  -- 13-17
                    ELSE 20 + (ABS(CHECKSUM(NEWID()) % 4))         -- 20-23
                END;
                DECLARE @MinuteOffset INT = ABS(CHECKSUM(NEWID()) % 60);

                SET @ETATime = DATEADD(MINUTE, @MinuteOffset,
                               DATEADD(HOUR, @HourBase,
                               CAST(@TargetDate AS DATETIME2)));
                SET @ETDTime = DATEADD(MINUTE, @DwellMins, @ETATime);

                -- Find available compatible berth for this time window
                SELECT TOP 1 @BerthId = b.BerthId
                FROM dbo.BERTHS b
                INNER JOIN dbo.TERMINALS t ON b.TerminalId = t.TerminalId
                WHERE b.IsActive = 1
                  AND b.Length >= @VesselLOA
                  AND b.MaxDraft >= @VesselDraft
                  AND (b.BerthType = @VesselType OR b.BerthType = 'General')
                  AND NOT EXISTS (
                      SELECT 1 FROM dbo.VESSEL_SCHEDULE vs
                      WHERE vs.BerthId = b.BerthId
                        AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
                        AND vs.ETA <= @ETDTime
                        AND vs.ETD >= @ETATime
                  )
                ORDER BY
                    CASE WHEN b.BerthType = @VesselType THEN 0 ELSE 1 END,
                    NEWID();

                IF @BerthId IS NULL
                BEGIN
                    -- Try without type matching
                    SELECT TOP 1 @BerthId = b.BerthId
                    FROM dbo.BERTHS b
                    WHERE b.IsActive = 1
                      AND b.Length >= @VesselLOA
                      AND b.MaxDraft >= @VesselDraft
                      AND NOT EXISTS (
                          SELECT 1 FROM dbo.VESSEL_SCHEDULE vs
                          WHERE vs.BerthId = b.BerthId
                            AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
                            AND vs.ETA <= @ETDTime
                            AND vs.ETD >= @ETATime
                      )
                    ORDER BY NEWID();
                END

                IF @BerthId IS NULL CONTINUE; -- No berth available for this slot

                -- Determine cargo details
                DECLARE @CargoQty DECIMAL(12,2) = CASE @VesselType
                    WHEN 'Container' THEN 500 + (ABS(CHECKSUM(NEWID()) % 4500))       -- 500-5000 TEU
                    WHEN 'Bulk' THEN 10000 + (ABS(CHECKSUM(NEWID()) % 70000))         -- 10K-80K MT
                    WHEN 'Tanker' THEN 20000 + (ABS(CHECKSUM(NEWID()) % 280000))      -- 20K-300K MT
                    WHEN 'General' THEN 1000 + (ABS(CHECKSUM(NEWID()) % 14000))       -- 1K-15K MT
                    ELSE 500 + (ABS(CHECKSUM(NEWID()) % 9500))                        -- 500-10K
                END;

                DECLARE @CargoUnit NVARCHAR(20) = CASE @VesselType
                    WHEN 'Container' THEN 'TEU'
                    WHEN 'Passenger' THEN 'PAX'
                    ELSE 'MT'
                END;

                DECLARE @TugsAssigned INT = CASE
                    WHEN @VesselLOA > 300 THEN 3
                    WHEN @VesselLOA > 200 THEN 2
                    ELSE 1
                END;

                DECLARE @OptScore DECIMAL(5,2) = 70 + (ABS(CHECKSUM(NEWID()) % 26)); -- 70-95

                -- Get port code for the berth
                DECLARE @PortCode NVARCHAR(10);
                SELECT @PortCode = p.PortCode
                FROM dbo.BERTHS b
                INNER JOIN dbo.TERMINALS t ON b.TerminalId = t.TerminalId
                INNER JOIN dbo.PORTS p ON t.PortId = p.PortId
                WHERE b.BerthId = @BerthId;

                -- Get terminal type
                DECLARE @TermType NVARCHAR(50);
                SELECT @TermType = t.TerminalType
                FROM dbo.BERTHS b
                INNER JOIN dbo.TERMINALS t ON b.TerminalId = t.TerminalId
                WHERE b.BerthId = @BerthId;

                -- Generate voyage number
                DECLARE @VoyageNum NVARCHAR(50) = 'V' + FORMAT(@TargetDate, 'yyMMdd') + '-' + RIGHT('00' + CAST(@Generated + 1 AS VARCHAR), 2);

                -- Insert schedule
                BEGIN TRY
                    INSERT INTO dbo.VESSEL_SCHEDULE (
                        VesselId, BerthId, ETA, ETD, Status, DwellTime,
                        OptimizationScore, IsOptimized,
                        PortCode, VoyageNumber, CargoType, CargoQuantity, CargoUnit,
                        TugsAssigned, PilotsAssigned, TerminalType
                    )
                    VALUES (
                        @VesselId, @BerthId, @ETATime, @ETDTime, 'Scheduled', @DwellMins,
                        @OptScore, 1,
                        @PortCode, @VoyageNum, @VesselCargoType, @CargoQty, @CargoUnit,
                        @TugsAssigned, CASE WHEN @VesselLOA > 250 THEN 2 ELSE 1 END, @TermType
                    );

                    SET @Generated = @Generated + 1;
                    SET @TotalCreated = @TotalCreated + 1;
                END TRY
                BEGIN CATCH
                    -- Skip if insert fails (e.g., constraint violation)
                    PRINT 'Error creating schedule for vessel ' + CAST(@VesselId AS VARCHAR) + ': ' + ERROR_MESSAGE();
                END CATCH
            END
        END

        SET @DayOffset = @DayOffset + 1;
    END

    -- Log generation summary
    IF @TotalCreated > 0
    BEGIN
        INSERT INTO dbo.ALERTS_NOTIFICATIONS (AlertType, RelatedEntityId, EntityType, Severity, Message)
        VALUES ('ScheduleGenerated', 0, 'System', 'Low',
            'Auto-generated ' + CAST(@TotalCreated AS VARCHAR) + ' new vessel schedules for upcoming days.');
    END

    SELECT @TotalCreated AS SchedulesGenerated;
END
GO

-- =============================================
-- JOB 5: sp_Job_UpdateAISPositions
-- Simulate AIS vessel movement for approaching vessels
-- Updates lat/lon, speed, course as vessels approach port
-- =============================================
CREATE OR ALTER PROCEDURE sp_Job_UpdateAISPositions
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @Now DATETIME2 = GETUTCDATE();
    DECLARE @Count INT = 0;

    -- Mumbai Port coordinates (default target)
    DECLARE @PortLat DECIMAL(10,6) = 18.9400;
    DECLARE @PortLon DECIMAL(10,6) = 72.8400;

    -- Process each approaching vessel
    DECLARE @VesselId INT;
    DECLARE @MMSI NVARCHAR(50);
    DECLARE @ETA DATETIME2;
    DECLARE @ATA DATETIME2;
    DECLARE @VesselType NVARCHAR(50);
    DECLARE @ScheduleId INT;
    DECLARE @BerthId INT;
    DECLARE @PortCode NVARCHAR(10);

    DECLARE cur CURSOR LOCAL FAST_FORWARD FOR
        SELECT vs.ScheduleId, vs.VesselId, v.MMSI, vs.ETA, vs.ATA, v.VesselType,
               vs.BerthId, vs.PortCode
        FROM dbo.VESSEL_SCHEDULE vs
        INNER JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
        WHERE vs.Status IN ('Approaching', 'Scheduled')
          AND vs.ETA IS NOT NULL
          AND vs.ETA >= DATEADD(HOUR, -2, @Now)
          AND vs.ETA <= DATEADD(HOUR, 24, @Now);

    OPEN cur;
    FETCH NEXT FROM cur INTO @ScheduleId, @VesselId, @MMSI, @ETA, @ATA, @VesselType, @BerthId, @PortCode;

    WHILE @@FETCH_STATUS = 0
    BEGIN
        BEGIN TRY
            -- Get port coordinates if available
            IF @PortCode IS NOT NULL
            BEGIN
                SELECT TOP 1 @PortLat = Latitude, @PortLon = Longitude
                FROM dbo.PORTS WHERE PortCode = @PortCode
                  AND Latitude IS NOT NULL AND Longitude IS NOT NULL;
            END

            -- Calculate progress (0.0 = far away, 1.0 = arrived)
            DECLARE @TotalMinutes FLOAT = DATEDIFF(MINUTE, DATEADD(HOUR, -12, @ETA), @ETA); -- 12h journey
            DECLARE @ElapsedMinutes FLOAT = DATEDIFF(MINUTE, DATEADD(HOUR, -12, @ETA), @Now);
            DECLARE @Progress FLOAT = CASE
                WHEN @TotalMinutes <= 0 THEN 1.0
                ELSE @ElapsedMinutes / @TotalMinutes
            END;
            IF @Progress < 0 SET @Progress = 0;
            IF @Progress > 1.0 SET @Progress = 1.0;

            -- Calculate position (linear interpolation from start point to port)
            -- Start from ~200 nautical miles away, direction varies
            DECLARE @StartOffsetLat DECIMAL(10,6) = 3.0 * (1.0 + (ABS(CHECKSUM(NEWID(), @VesselId) % 100) / 100.0));
            DECLARE @StartOffsetLon DECIMAL(10,6) = 2.0 * (1.0 + (ABS(CHECKSUM(NEWID(), @VesselId + 1) % 100) / 100.0));

            -- Randomize approach direction
            DECLARE @DirSeed INT = ABS(@VesselId) % 4;
            IF @DirSeed = 0 BEGIN SET @StartOffsetLat = -@StartOffsetLat; END
            IF @DirSeed = 1 BEGIN SET @StartOffsetLon = -@StartOffsetLon; END
            IF @DirSeed = 2 BEGIN SET @StartOffsetLat = -@StartOffsetLat; SET @StartOffsetLon = -@StartOffsetLon; END

            DECLARE @CurrentLat DECIMAL(10,6) = @PortLat + (@StartOffsetLat * (1.0 - @Progress));
            DECLARE @CurrentLon DECIMAL(10,6) = @PortLon + (@StartOffsetLon * (1.0 - @Progress));

            -- Add small random jitter for realism
            SET @CurrentLat = @CurrentLat + (ABS(CHECKSUM(NEWID()) % 100) - 50) * 0.0001;
            SET @CurrentLon = @CurrentLon + (ABS(CHECKSUM(NEWID()) % 100) - 50) * 0.0001;

            -- Speed: decreasing as vessel approaches (14-20 kn ocean, 8-12 approach, 3-6 pilotage)
            DECLARE @Speed DECIMAL(5,1) = CASE
                WHEN @Progress < 0.5 THEN 14.0 + (ABS(CHECKSUM(NEWID()) % 70) / 10.0)  -- 14-21 kn
                WHEN @Progress < 0.8 THEN 8.0 + (ABS(CHECKSUM(NEWID()) % 50) / 10.0)   -- 8-13 kn
                ELSE 3.0 + (ABS(CHECKSUM(NEWID()) % 40) / 10.0)                         -- 3-7 kn
            END;

            -- Course: pointing toward port
            DECLARE @Course DECIMAL(5,1) = CASE
                WHEN @PortLon > @CurrentLon AND @PortLat > @CurrentLat THEN 45 + (ABS(CHECKSUM(NEWID()) % 20) - 10)
                WHEN @PortLon > @CurrentLon AND @PortLat <= @CurrentLat THEN 135 + (ABS(CHECKSUM(NEWID()) % 20) - 10)
                WHEN @PortLon <= @CurrentLon AND @PortLat <= @CurrentLat THEN 225 + (ABS(CHECKSUM(NEWID()) % 20) - 10)
                ELSE 315 + (ABS(CHECKSUM(NEWID()) % 20) - 10)
            END;
            IF @Course < 0 SET @Course = @Course + 360;
            IF @Course >= 360 SET @Course = @Course - 360;

            -- Distance to port (approximate NM)
            DECLARE @DistanceToPort DECIMAL(10,2) = SQRT(
                POWER((@PortLat - @CurrentLat) * 60, 2) +
                POWER((@PortLon - @CurrentLon) * 60 * COS(RADIANS(@PortLat)), 2)
            );

            -- Phase
            DECLARE @Phase NVARCHAR(50) = CASE
                WHEN @Progress < 0.5 THEN 'ocean'
                WHEN @Progress < 0.8 THEN 'approach'
                WHEN @Progress < 0.95 THEN 'pilotage'
                ELSE 'berthing'
            END;

            -- Navigation Status
            DECLARE @NavStatus NVARCHAR(50) = CASE
                WHEN @Phase = 'ocean' THEN 'Under way using engine'
                WHEN @Phase = 'approach' THEN 'Under way using engine'
                WHEN @Phase = 'pilotage' THEN 'Under way using engine'
                ELSE 'Moored'
            END;

            DECLARE @NavStatusCode INT = CASE
                WHEN @Phase = 'berthing' THEN 5 -- Moored
                WHEN @Speed < 0.5 THEN 1 -- At anchor
                ELSE 0 -- Under way
            END;

            DECLARE @TimeToPort INT = CASE
                WHEN @Speed > 0 THEN CAST(@DistanceToPort / @Speed * 60 AS INT)
                ELSE DATEDIFF(MINUTE, @Now, @ETA)
            END;

            -- Upsert AIS record
            IF EXISTS (SELECT 1 FROM dbo.AIS_DATA WHERE VesselId = @VesselId AND RecordedAt >= DATEADD(MINUTE, -20, @Now))
            BEGIN
                -- Update most recent record
                UPDATE TOP(1) dbo.AIS_DATA
                SET Latitude = @CurrentLat,
                    Longitude = @CurrentLon,
                    Speed = @Speed,
                    Course = @Course,
                    Heading = @Course,
                    NavigationStatus = @NavStatus,
                    NavigationStatusCode = @NavStatusCode,
                    RecordedAt = @Now,
                    PortCode = @PortCode,
                    VesselType = @VesselType,
                    ETA = @ETA,
                    TimeToPort = @TimeToPort,
                    Phase = @Phase,
                    DistanceToPort = @DistanceToPort
                WHERE VesselId = @VesselId
                  AND RecordedAt >= DATEADD(MINUTE, -20, @Now);
            END
            ELSE
            BEGIN
                -- Insert new AIS record
                INSERT INTO dbo.AIS_DATA (
                    VesselId, MMSI, Latitude, Longitude, Speed, Course, Heading,
                    NavigationStatus, RecordedAt, PortCode, VesselType, ETA,
                    TimeToPort, Phase, DistanceToPort, NavigationStatusCode
                )
                VALUES (
                    @VesselId, @MMSI, @CurrentLat, @CurrentLon, @Speed, @Course, @Course,
                    @NavStatus, @Now, @PortCode, @VesselType, @ETA,
                    @TimeToPort, @Phase, @DistanceToPort, @NavStatusCode
                );
            END

            SET @Count = @Count + 1;
        END TRY
        BEGIN CATCH
            PRINT 'Error updating AIS for vessel ' + CAST(@VesselId AS VARCHAR) + ': ' + ERROR_MESSAGE();
        END CATCH

        FETCH NEXT FROM cur INTO @ScheduleId, @VesselId, @MMSI, @ETA, @ATA, @VesselType, @BerthId, @PortCode;
    END

    CLOSE cur;
    DEALLOCATE cur;

    SELECT @Count AS AISPositionsUpdated;
END
GO

-- =============================================
-- JOB 6: sp_Job_MasterRunner
-- Orchestrator - runs all jobs in correct order
-- =============================================
CREATE OR ALTER PROCEDURE sp_Job_MasterRunner
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @StartTime DATETIME2 = GETUTCDATE();
    DECLARE @Departed INT = 0;
    DECLARE @Berthed INT = 0;
    DECLARE @Approached INT = 0;
    DECLARE @Scheduled INT = 0;
    DECLARE @AISUpdated INT = 0;
    DECLARE @StepStart DATETIME2;

    PRINT '=============================================';
    PRINT 'BerthPlanning Auto-Simulation - Starting';
    PRINT 'Run Time: ' + CONVERT(NVARCHAR(30), @StartTime, 120);
    PRINT '=============================================';

    -- Step 1: Depart vessels first (free up berths)
    BEGIN TRY
        SET @StepStart = GETUTCDATE();
        PRINT '';
        PRINT 'Step 1: Departing berthed vessels...';

        CREATE TABLE #DepartResult (VesselsDeparted INT);
        INSERT INTO #DepartResult EXEC sp_Job_DepartBerthed;
        SELECT @Departed = VesselsDeparted FROM #DepartResult;
        DROP TABLE #DepartResult;

        PRINT '  -> ' + CAST(@Departed AS VARCHAR) + ' vessels departed (' + CAST(DATEDIFF(MILLISECOND, @StepStart, GETUTCDATE()) AS VARCHAR) + 'ms)';
    END TRY
    BEGIN CATCH
        PRINT '  -> ERROR: ' + ERROR_MESSAGE();
    END CATCH

    -- Step 2: Berth approaching vessels
    BEGIN TRY
        SET @StepStart = GETUTCDATE();
        PRINT '';
        PRINT 'Step 2: Berthing approaching vessels...';

        CREATE TABLE #BerthResult (VesselsBerthed INT);
        INSERT INTO #BerthResult EXEC sp_Job_BerthApproaching;
        SELECT @Berthed = VesselsBerthed FROM #BerthResult;
        DROP TABLE #BerthResult;

        PRINT '  -> ' + CAST(@Berthed AS VARCHAR) + ' vessels berthed (' + CAST(DATEDIFF(MILLISECOND, @StepStart, GETUTCDATE()) AS VARCHAR) + 'ms)';
    END TRY
    BEGIN CATCH
        PRINT '  -> ERROR: ' + ERROR_MESSAGE();
    END CATCH

    -- Step 3: Advance scheduled to approaching
    BEGIN TRY
        SET @StepStart = GETUTCDATE();
        PRINT '';
        PRINT 'Step 3: Advancing scheduled vessels to approaching...';

        CREATE TABLE #ApproachResult (VesselsAdvancedToApproaching INT);
        INSERT INTO #ApproachResult EXEC sp_Job_AdvanceApproaching;
        SELECT @Approached = VesselsAdvancedToApproaching FROM #ApproachResult;
        DROP TABLE #ApproachResult;

        PRINT '  -> ' + CAST(@Approached AS VARCHAR) + ' vessels now approaching (' + CAST(DATEDIFF(MILLISECOND, @StepStart, GETUTCDATE()) AS VARCHAR) + 'ms)';
    END TRY
    BEGIN CATCH
        PRINT '  -> ERROR: ' + ERROR_MESSAGE();
    END CATCH

    -- Step 4: Generate daily schedules
    BEGIN TRY
        SET @StepStart = GETUTCDATE();
        PRINT '';
        PRINT 'Step 4: Generating daily schedules...';

        CREATE TABLE #ScheduleResult (SchedulesGenerated INT);
        INSERT INTO #ScheduleResult EXEC sp_Job_GenerateDailySchedules;
        SELECT @Scheduled = SchedulesGenerated FROM #ScheduleResult;
        DROP TABLE #ScheduleResult;

        PRINT '  -> ' + CAST(@Scheduled AS VARCHAR) + ' new schedules generated (' + CAST(DATEDIFF(MILLISECOND, @StepStart, GETUTCDATE()) AS VARCHAR) + 'ms)';
    END TRY
    BEGIN CATCH
        PRINT '  -> ERROR: ' + ERROR_MESSAGE();
    END CATCH

    -- Step 5: Update AIS positions
    BEGIN TRY
        SET @StepStart = GETUTCDATE();
        PRINT '';
        PRINT 'Step 5: Updating AIS positions...';

        CREATE TABLE #AISResult (AISPositionsUpdated INT);
        INSERT INTO #AISResult EXEC sp_Job_UpdateAISPositions;
        SELECT @AISUpdated = AISPositionsUpdated FROM #AISResult;
        DROP TABLE #AISResult;

        PRINT '  -> ' + CAST(@AISUpdated AS VARCHAR) + ' AIS positions updated (' + CAST(DATEDIFF(MILLISECOND, @StepStart, GETUTCDATE()) AS VARCHAR) + 'ms)';
    END TRY
    BEGIN CATCH
        PRINT '  -> ERROR: ' + ERROR_MESSAGE();
    END CATCH

    -- Log to audit
    DECLARE @Duration INT = DATEDIFF(MILLISECOND, @StartTime, GETUTCDATE());
    DECLARE @Summary NVARCHAR(MAX) = '{"departed":' + CAST(@Departed AS VARCHAR)
        + ',"berthed":' + CAST(@Berthed AS VARCHAR)
        + ',"approaching":' + CAST(@Approached AS VARCHAR)
        + ',"schedulesGenerated":' + CAST(@Scheduled AS VARCHAR)
        + ',"aisUpdated":' + CAST(@AISUpdated AS VARCHAR)
        + ',"durationMs":' + CAST(@Duration AS VARCHAR) + '}';

    INSERT INTO dbo.AUDIT_LOG (UserId, Action, EntityType, EntityId, NewValue)
    VALUES ('SYSTEM', 'AutoSimulation', 'Job', 0, @Summary);

    PRINT '';
    PRINT '=============================================';
    PRINT 'BerthPlanning Auto-Simulation - Complete';
    PRINT 'Duration: ' + CAST(@Duration AS VARCHAR) + 'ms';
    PRINT 'Summary: ' + @Summary;
    PRINT '=============================================';

    -- Return summary as result set
    SELECT
        @Departed AS VesselsDeparted,
        @Berthed AS VesselsBerthed,
        @Approached AS VesselsApproaching,
        @Scheduled AS SchedulesGenerated,
        @AISUpdated AS AISPositionsUpdated,
        @Duration AS TotalDurationMs,
        @StartTime AS RunStartTime,
        GETUTCDATE() AS RunEndTime;
END
GO

-- =============================================
-- JOB 7: SQL Server Agent Job Setup
-- Creates automated SQL Agent Jobs for periodic execution
-- NOTE: Requires SQL Server Agent to be running
-- =============================================

-- Helper: Create the Agent Job for 15-minute simulation
IF EXISTS (SELECT 1 FROM msdb.dbo.sysjobs WHERE name = N'BerthPlanning_AutoSimulation')
BEGIN
    EXEC msdb.dbo.sp_delete_job @job_name = N'BerthPlanning_AutoSimulation', @delete_unused_schedule = 1;
END
GO

BEGIN TRY
    DECLARE @jobId BINARY(16);

    -- Create the job
    EXEC msdb.dbo.sp_add_job
        @job_name = N'BerthPlanning_AutoSimulation',
        @enabled = 1,
        @description = N'Berth Planning Hackathon Demo - Auto-simulate vessel movements every 10 minutes',
        @category_name = N'[Uncategorized (Local)]',
        @owner_login_name = N'sa',
        @job_id = @jobId OUTPUT;

    -- Add job step
    EXEC msdb.dbo.sp_add_jobstep
        @job_id = @jobId,
        @step_name = N'Run Master Simulation',
        @step_id = 1,
        @subsystem = N'TSQL',
        @command = N'EXEC sp_Job_MasterRunner',
        @database_name = N'BerthPlanning',
        @retry_attempts = 1,
        @retry_interval = 5;

    -- Create schedule: Every 15 minutes
    EXEC msdb.dbo.sp_add_jobschedule
        @job_id = @jobId,
        @name = N'Every15Minutes',
        @enabled = 1,
        @freq_type = 4,           -- Daily
        @freq_interval = 1,       -- Every 1 day
        @freq_subday_type = 4,    -- Minutes
        @freq_subday_interval = 10, -- Every 10 minutes
        @active_start_date = 20260204,
        @active_start_time = 0;    -- Starting at midnight

    -- Add to local server
    EXEC msdb.dbo.sp_add_jobserver
        @job_id = @jobId,
        @server_name = N'(local)';

    PRINT 'SQL Agent Job "BerthPlanning_AutoSimulation" created successfully (every 10 mins)';
END TRY
BEGIN CATCH
    PRINT 'Note: Could not create SQL Agent Job (requires SQL Server Agent). Error: ' + ERROR_MESSAGE();
    PRINT 'You can manually run: EXEC sp_Job_MasterRunner';
END CATCH
GO

-- Create daily schedule generation job
IF EXISTS (SELECT 1 FROM msdb.dbo.sysjobs WHERE name = N'BerthPlanning_DailyScheduleGen')
BEGIN
    EXEC msdb.dbo.sp_delete_job @job_name = N'BerthPlanning_DailyScheduleGen', @delete_unused_schedule = 1;
END
GO

BEGIN TRY
    DECLARE @dailyJobId BINARY(16);

    EXEC msdb.dbo.sp_add_job
        @job_name = N'BerthPlanning_DailyScheduleGen',
        @enabled = 1,
        @description = N'Berth Planning - Generate daily vessel schedules at midnight',
        @category_name = N'[Uncategorized (Local)]',
        @owner_login_name = N'sa',
        @job_id = @dailyJobId OUTPUT;

    EXEC msdb.dbo.sp_add_jobstep
        @job_id = @dailyJobId,
        @step_name = N'Generate Daily Schedules',
        @step_id = 1,
        @subsystem = N'TSQL',
        @command = N'EXEC sp_Job_GenerateDailySchedules',
        @database_name = N'BerthPlanning',
        @retry_attempts = 2,
        @retry_interval = 10;

    -- Schedule: Daily at midnight
    EXEC msdb.dbo.sp_add_jobschedule
        @job_id = @dailyJobId,
        @name = N'DailyMidnight',
        @enabled = 1,
        @freq_type = 4,           -- Daily
        @freq_interval = 1,       -- Every 1 day
        @freq_subday_type = 1,    -- At specified time
        @active_start_date = 20260204,
        @active_start_time = 0;    -- Midnight

    EXEC msdb.dbo.sp_add_jobserver
        @job_id = @dailyJobId,
        @server_name = N'(local)';

    PRINT 'SQL Agent Job "BerthPlanning_DailyScheduleGen" created successfully (daily at midnight)';
END TRY
BEGIN CATCH
    PRINT 'Note: Could not create daily SQL Agent Job. Error: ' + ERROR_MESSAGE();
    PRINT 'You can manually run: EXEC sp_Job_GenerateDailySchedules';
END CATCH
GO

-- =============================================
-- VERIFICATION & USAGE
-- =============================================
PRINT '';
PRINT '=============================================';
PRINT 'SQL JOBS CREATED SUCCESSFULLY!';
PRINT '=============================================';
PRINT '';
PRINT 'Stored Procedures Created:';
PRINT '  1. sp_Job_AdvanceApproaching   - Move Scheduled -> Approaching';
PRINT '  2. sp_Job_BerthApproaching     - Move Approaching -> Berthed';
PRINT '  3. sp_Job_DepartBerthed        - Move Berthed -> Departed';
PRINT '  4. sp_Job_GenerateDailySchedules - Auto-create future schedules';
PRINT '  5. sp_Job_UpdateAISPositions    - Simulate vessel AIS movement';
PRINT '  6. sp_Job_MasterRunner         - Run all jobs in sequence';
PRINT '';
PRINT 'Quick Start:';
PRINT '  EXEC sp_Job_MasterRunner              -- Run full simulation cycle';
PRINT '  EXEC sp_Job_GenerateDailySchedules     -- Generate schedules only';
PRINT '  EXEC sp_Job_UpdateAISPositions          -- Update AIS only';
PRINT '';
PRINT 'SQL Agent Jobs:';
PRINT '  BerthPlanning_AutoSimulation   - Every 10 minutes';
PRINT '  BerthPlanning_DailyScheduleGen - Daily at midnight';
PRINT '';
PRINT 'Vessel Lifecycle: Scheduled -> Approaching -> Berthed -> Departed';
PRINT '=============================================';
GO
