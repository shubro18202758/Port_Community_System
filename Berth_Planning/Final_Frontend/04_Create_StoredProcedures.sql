-- =============================================
-- BERTH PLANNING SYSTEM - STORED PROCEDURES
-- Purpose: Reusable procedures for common operations
-- =============================================

USE [BerthPlanning]; -- Change this
GO

-- =============================================
-- SP 1: Get Berth Availability
-- Check if berth is available for a time window
-- =============================================
CREATE OR ALTER PROCEDURE sp_CheckBerthAvailability
    @BerthId INT,
    @StartTime DATETIME2,
    @EndTime DATETIME2
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Check for conflicts with existing schedules
    SELECT 
        vs.ScheduleId,
        v.VesselName,
        vs.ETA,
        vs.ETD,
        vs.Status,
        CASE 
            WHEN vs.Status = 'Berthed' THEN 'CONFLICT: Berth currently occupied'
            WHEN (vs.ETA <= @EndTime AND vs.ETD >= @StartTime) THEN 'CONFLICT: Time window overlaps'
            ELSE 'OK'
        END AS AvailabilityStatus
    FROM dbo.VESSEL_SCHEDULE vs
    INNER JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
    WHERE vs.BerthId = @BerthId
        AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
        AND (
            (vs.ETA <= @EndTime AND vs.ETD >= @StartTime) -- Overlapping time window
            OR vs.Status = 'Berthed' -- Currently occupied
        );
    
    -- Check for maintenance
    SELECT 
        MaintenanceId,
        MaintenanceType,
        StartTime,
        EndTime,
        Status,
        'CONFLICT: Berth under maintenance' AS AvailabilityStatus
    FROM dbo.BERTH_MAINTENANCE
    WHERE BerthId = @BerthId
        AND Status IN ('Scheduled', 'InProgress')
        AND StartTime <= @EndTime 
        AND EndTime >= @StartTime;
    
    -- Summary
    IF NOT EXISTS (
        SELECT 1 FROM dbo.VESSEL_SCHEDULE 
        WHERE BerthId = @BerthId
            AND Status IN ('Scheduled', 'Approaching', 'Berthed')
            AND (ETA <= @EndTime AND ETD >= @StartTime)
    ) AND NOT EXISTS (
        SELECT 1 FROM dbo.BERTH_MAINTENANCE 
        WHERE BerthId = @BerthId
            AND Status IN ('Scheduled', 'InProgress')
            AND StartTime <= @EndTime AND EndTime >= @StartTime
    )
    BEGIN
        SELECT 'AVAILABLE' AS BerthAvailability, 
               'Berth is available for the requested time window' AS Message;
    END
    ELSE
    BEGIN
        SELECT 'UNAVAILABLE' AS BerthAvailability,
               'Berth has conflicts during the requested time window' AS Message;
    END
END
GO

-- =============================================
-- SP 2: Find Compatible Berths for Vessel (by VesselId)
-- Find all berths that can accommodate a vessel
-- =============================================
CREATE OR ALTER PROCEDURE sp_FindCompatibleBerthsByVessel
    @VesselId INT,
    @ETA DATETIME2,
    @DwellTime INT -- in minutes
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @ETD DATETIME2 = DATEADD(MINUTE, @DwellTime, @ETA);
    DECLARE @VesselLOA DECIMAL(8,2);
    DECLARE @VesselDraft DECIMAL(6,2);
    DECLARE @VesselType NVARCHAR(50);

    -- Get vessel details
    SELECT
        @VesselLOA = LOA,
        @VesselDraft = Draft,
        @VesselType = VesselType
    FROM dbo.VESSELS
    WHERE VesselId = @VesselId;

    -- Find compatible berths
    SELECT
        b.BerthId,
        b.TerminalId,
        b.BerthName,
        b.BerthCode,
        b.BerthType,
        b.Length,
        b.Depth,
        b.MaxDraft,
        b.NumberOfCranes,
        t.TerminalName,
        t.TerminalCode,
        p.PortName,
        p.PortCode,

        -- Compatibility checks
        CASE WHEN b.Length >= @VesselLOA THEN 'OK' ELSE 'TOO SHORT' END AS LengthCheck,
        CASE WHEN b.MaxDraft >= @VesselDraft THEN 'OK' ELSE 'INSUFFICIENT DEPTH' END AS DraftCheck,
        CASE WHEN b.BerthType = @VesselType OR b.BerthType = 'General' THEN 'MATCH' ELSE 'TYPE MISMATCH' END AS TypeCheck,
        CASE WHEN b.IsActive = 1 THEN 'ACTIVE' ELSE 'INACTIVE' END AS StatusCheck,

        -- Check availability
        CASE
            WHEN EXISTS (
                SELECT 1 FROM dbo.VESSEL_SCHEDULE vs
                WHERE vs.BerthId = b.BerthId
                    AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
                    AND vs.ETA <= @ETD
                    AND vs.ETD >= @ETA
            ) THEN 'OCCUPIED'
            WHEN EXISTS (
                SELECT 1 FROM dbo.BERTH_MAINTENANCE bm
                WHERE bm.BerthId = b.BerthId
                    AND bm.Status IN ('Scheduled', 'InProgress')
                    AND bm.StartTime <= @ETD
                    AND bm.EndTime >= @ETA
            ) THEN 'MAINTENANCE'
            ELSE 'AVAILABLE'
        END AS AvailabilityStatus,

        -- Overall compatibility score
        CASE
            WHEN b.Length >= @VesselLOA
                AND b.MaxDraft >= @VesselDraft
                AND b.IsActive = 1
                AND NOT EXISTS (
                    SELECT 1 FROM dbo.VESSEL_SCHEDULE vs
                    WHERE vs.BerthId = b.BerthId
                        AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
                        AND vs.ETA <= @ETD AND vs.ETD >= @ETA
                )
                AND NOT EXISTS (
                    SELECT 1 FROM dbo.BERTH_MAINTENANCE bm
                    WHERE bm.BerthId = b.BerthId
                        AND bm.Status IN ('Scheduled', 'InProgress')
                        AND bm.StartTime <= @ETD AND bm.EndTime >= @ETA
                )
            THEN 'COMPATIBLE'
            ELSE 'NOT COMPATIBLE'
        END AS OverallCompatibility

    FROM dbo.BERTHS b
    LEFT JOIN dbo.TERMINALS t ON b.TerminalId = t.TerminalId
    LEFT JOIN dbo.PORTS p ON t.PortId = p.PortId
    ORDER BY
        CASE
            WHEN b.Length >= @VesselLOA
                AND b.MaxDraft >= @VesselDraft
                AND b.IsActive = 1
            THEN 0 ELSE 1
        END,
        p.PortName,
        t.TerminalName,
        b.BerthName;
END
GO

-- =============================================
-- SP 2b: Find Compatible Berths (by dimensions)
-- Used by API for vessel LOA/Draft lookups
-- =============================================
CREATE OR ALTER PROCEDURE sp_FindCompatibleBerths
    @VesselLOA DECIMAL(8,2),
    @VesselDraft DECIMAL(6,2)
AS
BEGIN
    SET NOCOUNT ON;

    -- Find compatible berths based on dimensions only
    SELECT
        b.BerthId,
        b.TerminalId,
        b.BerthName,
        b.BerthCode,
        b.BerthType,
        b.Length,
        b.Depth,
        b.MaxDraft,
        b.NumberOfCranes,
        b.BollardCount,
        b.IsActive,
        b.Latitude,
        b.Longitude,
        b.CreatedAt,
        b.UpdatedAt,
        t.TerminalName,
        t.TerminalCode,
        p.PortName,
        p.PortCode
    FROM dbo.BERTHS b
    LEFT JOIN dbo.TERMINALS t ON b.TerminalId = t.TerminalId
    LEFT JOIN dbo.PORTS p ON t.PortId = p.PortId
    WHERE b.IsActive = 1
        AND b.Length >= @VesselLOA
        AND b.MaxDraft >= @VesselDraft
    ORDER BY
        p.PortName,
        t.TerminalName,
        b.BerthName;
END
GO

-- =============================================
-- SP 3: Allocate Vessel to Berth
-- Create a new schedule entry with validation
-- =============================================
CREATE OR ALTER PROCEDURE sp_AllocateVesselToBerth
    @VesselId INT,
    @BerthId INT,
    @ETA DATETIME2,
    @ETD DATETIME2,
    @Priority INT = 2,
    @DwellTime INT = NULL,
    @ScheduleId INT OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        -- Validate vessel exists
        IF NOT EXISTS (SELECT 1 FROM dbo.VESSELS WHERE VesselId = @VesselId)
        BEGIN
            RAISERROR('Vessel not found', 16, 1);
            RETURN;
        END
        
        -- Validate berth exists and is active
        IF NOT EXISTS (SELECT 1 FROM dbo.BERTHS WHERE BerthId = @BerthId AND IsActive = 1)
        BEGIN
            RAISERROR('Berth not found or inactive', 16, 1);
            RETURN;
        END
        
        -- Check for conflicts
        IF EXISTS (
            SELECT 1 FROM dbo.VESSEL_SCHEDULE 
            WHERE BerthId = @BerthId
                AND Status IN ('Scheduled', 'Approaching', 'Berthed')
                AND ETA <= @ETD 
                AND ETD >= @ETA
        )
        BEGIN
            RAISERROR('Time conflict detected - berth already allocated for this time window', 16, 1);
            RETURN;
        END
        
        -- Calculate dwell time if not provided
        IF @DwellTime IS NULL
        BEGIN
            SET @DwellTime = DATEDIFF(MINUTE, @ETA, @ETD);
        END
        
        -- Insert schedule
        INSERT INTO dbo.VESSEL_SCHEDULE (
            VesselId, 
            BerthId, 
            ETA, 
            ETD, 
            Status, 
            DwellTime,
            IsOptimized
        )
        VALUES (
            @VesselId,
            @BerthId,
            @ETA,
            @ETD,
            'Scheduled',
            @DwellTime,
            0 -- Manual allocation
        );
        
        SET @ScheduleId = SCOPE_IDENTITY();
        
        COMMIT TRANSACTION;
        
        SELECT 
            @ScheduleId AS ScheduleId,
            'SUCCESS' AS Status,
            'Vessel successfully allocated to berth' AS Message;
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        SELECT 
            NULL AS ScheduleId,
            'ERROR' AS Status,
            ERROR_MESSAGE() AS Message;
    END CATCH
END
GO

-- =============================================
-- SP 4: Update Vessel ETA
-- Update ETA and trigger re-optimization if needed
-- =============================================
CREATE OR ALTER PROCEDURE sp_UpdateVesselETA
    @ScheduleId INT,
    @NewETA DATETIME2,
    @NewPredictedETA DATETIME2 = NULL,
    @Reason NVARCHAR(500) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        DECLARE @OldETA DATETIME2;
        DECLARE @VesselId INT;
        DECLARE @BerthId INT;
        
        -- Get current ETA
        SELECT 
            @OldETA = ETA,
            @VesselId = VesselId,
            @BerthId = BerthId
        FROM dbo.VESSEL_SCHEDULE
        WHERE ScheduleId = @ScheduleId;
        
        -- Update ETA
        UPDATE dbo.VESSEL_SCHEDULE
        SET 
            ETA = @NewETA,
            PredictedETA = COALESCE(@NewPredictedETA, @NewETA),
            UpdatedAt = GETUTCDATE()
        WHERE ScheduleId = @ScheduleId;
        
        -- Create alert if significant change (>30 minutes)
        IF ABS(DATEDIFF(MINUTE, @OldETA, @NewETA)) > 30
        BEGIN
            INSERT INTO dbo.ALERTS_NOTIFICATIONS (
                AlertType,
                RelatedEntityId,
                EntityType,
                Severity,
                Message
            )
            VALUES (
                'ETAUpdate',
                @ScheduleId,
                'Schedule',
                CASE 
                    WHEN ABS(DATEDIFF(MINUTE, @OldETA, @NewETA)) > 120 THEN 'High'
                    ELSE 'Medium'
                END,
                'ETA updated by ' + CAST(DATEDIFF(MINUTE, @OldETA, @NewETA) AS VARCHAR) + ' minutes. Reason: ' + COALESCE(@Reason, 'Not specified')
            );
        END
        
        -- Check for new conflicts
        IF EXISTS (
            SELECT 1 FROM dbo.VESSEL_SCHEDULE vs
            WHERE vs.BerthId = @BerthId
                AND vs.ScheduleId != @ScheduleId
                AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
                AND vs.ETA <= DATEADD(MINUTE, 360, @NewETA) -- Assuming 6 hour dwell time
                AND vs.ETD >= @NewETA
        )
        BEGIN
            -- Log conflict
            INSERT INTO dbo.CONFLICTS (
                ConflictType,
                ScheduleId1,
                ScheduleId2,
                Description,
                Severity,
                Status
            )
            SELECT TOP 1
                'BerthOverlap',
                @ScheduleId,
                vs.ScheduleId,
                'ETA update caused berth overlap conflict',
                2,
                'Detected'
            FROM dbo.VESSEL_SCHEDULE vs
            WHERE vs.BerthId = @BerthId
                AND vs.ScheduleId != @ScheduleId
                AND vs.Status IN ('Scheduled', 'Approaching', 'Berthed')
                AND vs.ETA <= DATEADD(MINUTE, 360, @NewETA)
                AND vs.ETD >= @NewETA;
        END
        
        COMMIT TRANSACTION;
        
        SELECT 
            'SUCCESS' AS Status,
            'ETA updated successfully' AS Message,
            @NewETA AS NewETA,
            @OldETA AS OldETA,
            DATEDIFF(MINUTE, @OldETA, @NewETA) AS ChangeInMinutes;
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        SELECT 
            'ERROR' AS Status,
            ERROR_MESSAGE() AS Message;
    END CATCH
END
GO

-- =============================================
-- SP 5: Record Vessel Arrival
-- Update schedule when vessel actually arrives
-- =============================================
CREATE OR ALTER PROCEDURE sp_RecordVesselArrival
    @ScheduleId INT,
    @ActualArrivalTime DATETIME2 = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SET @ActualArrivalTime = COALESCE(@ActualArrivalTime, GETUTCDATE());
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        DECLARE @ETA DATETIME2;
        DECLARE @WaitingTime INT;
        
        -- Get ETA
        SELECT @ETA = COALESCE(PredictedETA, ETA)
        FROM dbo.VESSEL_SCHEDULE
        WHERE ScheduleId = @ScheduleId;
        
        -- Calculate waiting time (if arrived late)
        SET @WaitingTime = CASE 
            WHEN @ActualArrivalTime > @ETA 
            THEN DATEDIFF(MINUTE, @ETA, @ActualArrivalTime)
            ELSE 0
        END;
        
        -- Update schedule
        UPDATE dbo.VESSEL_SCHEDULE
        SET 
            ATA = @ActualArrivalTime,
            Status = 'Approaching',
            WaitingTime = @WaitingTime,
            UpdatedAt = GETUTCDATE()
        WHERE ScheduleId = @ScheduleId;
        
        COMMIT TRANSACTION;
        
        SELECT 
            'SUCCESS' AS Status,
            'Vessel arrival recorded' AS Message,
            @ActualArrivalTime AS ArrivalTime,
            @WaitingTime AS WaitingTimeMinutes;
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        SELECT 
            'ERROR' AS Status,
            ERROR_MESSAGE() AS Message;
    END CATCH
END
GO

-- =============================================
-- SP 6: Record Vessel Berthing
-- Update when vessel docks at berth
-- =============================================
CREATE OR ALTER PROCEDURE sp_RecordVesselBerthing
    @ScheduleId INT,
    @BerthingTime DATETIME2 = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SET @BerthingTime = COALESCE(@BerthingTime, GETUTCDATE());
    
    UPDATE dbo.VESSEL_SCHEDULE
    SET 
        ATB = @BerthingTime,
        Status = 'Berthed',
        UpdatedAt = GETUTCDATE()
    WHERE ScheduleId = @ScheduleId;
    
    SELECT 
        'SUCCESS' AS Status,
        'Vessel berthing recorded' AS Message,
        @BerthingTime AS BerthingTime;
END
GO

-- =============================================
-- SP 7: Record Vessel Departure
-- Complete the schedule when vessel leaves
-- =============================================
CREATE OR ALTER PROCEDURE sp_RecordVesselDeparture
    @ScheduleId INT,
    @DepartureTime DATETIME2 = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    SET @DepartureTime = COALESCE(@DepartureTime, GETUTCDATE());
    
    BEGIN TRY
        BEGIN TRANSACTION;
        
        DECLARE @VesselId INT;
        DECLARE @BerthId INT;
        DECLARE @ATB DATETIME2;
        DECLARE @ATA DATETIME2;
        DECLARE @ETA DATETIME2;
        DECLARE @ActualDwellTime INT;
        DECLARE @ActualWaitingTime INT;
        DECLARE @ETAAccuracy DECIMAL(5,2);
        
        -- Get schedule details
        SELECT 
            @VesselId = VesselId,
            @BerthId = BerthId,
            @ATB = ATB,
            @ATA = ATA,
            @ETA = COALESCE(PredictedETA, ETA)
        FROM dbo.VESSEL_SCHEDULE
        WHERE ScheduleId = @ScheduleId;
        
        -- Calculate actual times
        SET @ActualDwellTime = DATEDIFF(MINUTE, @ATB, @DepartureTime);
        SET @ActualWaitingTime = DATEDIFF(MINUTE, @ATA, @ATB);
        
        -- Calculate ETA accuracy
        SET @ETAAccuracy = CASE 
            WHEN @ATA <= @ETA 
            THEN 100.0
            ELSE 100.0 - (CAST(DATEDIFF(MINUTE, @ETA, @ATA) AS FLOAT) / NULLIF(DATEDIFF(MINUTE, @ETA, @DepartureTime), 0) * 100.0)
        END;
        
        -- Update schedule
        UPDATE dbo.VESSEL_SCHEDULE
        SET 
            ATD = @DepartureTime,
            Status = 'Departed',
            DwellTime = @ActualDwellTime,
            WaitingTime = @ActualWaitingTime,
            UpdatedAt = GETUTCDATE()
        WHERE ScheduleId = @ScheduleId;
        
        -- Record in history
        INSERT INTO dbo.VESSEL_HISTORY (
            VesselId,
            BerthId,
            VisitDate,
            ActualDwellTime,
            ActualWaitingTime,
            ETAAccuracy
        )
        VALUES (
            @VesselId,
            @BerthId,
            @DepartureTime,
            @ActualDwellTime,
            @ActualWaitingTime,
            @ETAAccuracy
        );
        
        -- Release resources
        UPDATE dbo.RESOURCE_ALLOCATION
        SET Status = 'Released'
        WHERE ScheduleId = @ScheduleId
            AND Status IN ('Allocated', 'InUse');
        
        COMMIT TRANSACTION;
        
        SELECT 
            'SUCCESS' AS Status,
            'Vessel departure recorded and logged to history' AS Message,
            @DepartureTime AS DepartureTime,
            @ActualDwellTime AS ActualDwellTimeMinutes,
            @ActualWaitingTime AS ActualWaitingTimeMinutes,
            @ETAAccuracy AS ETAAccuracyPercent;
            
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;
            
        SELECT 
            'ERROR' AS Status,
            ERROR_MESSAGE() AS Message;
    END CATCH
END
GO

-- =============================================
-- SP 8: Get Performance Dashboard Data
-- Comprehensive dashboard statistics
-- =============================================
CREATE OR ALTER PROCEDURE sp_GetDashboardStats
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Current Status
    SELECT 
        COUNT(CASE WHEN Status = 'Berthed' THEN 1 END) AS VesselsBerthed,
        COUNT(CASE WHEN Status = 'Approaching' THEN 1 END) AS VesselsApproaching,
        COUNT(CASE WHEN Status = 'Scheduled' THEN 1 END) AS VesselsScheduled
    FROM dbo.VESSEL_SCHEDULE
    WHERE Status IN ('Berthed', 'Approaching', 'Scheduled');
    
    -- Performance Metrics (Last 30 Days)
    SELECT 
        AVG(CAST(WaitingTime AS FLOAT)) AS AvgWaitingTime,
        MAX(WaitingTime) AS MaxWaitingTime,
        MIN(WaitingTime) AS MinWaitingTime,
        AVG(CAST(DwellTime AS FLOAT)) AS AvgDwellTime,
        AVG(CAST(OptimizationScore AS FLOAT)) AS AvgOptimizationScore
    FROM dbo.VESSEL_SCHEDULE
    WHERE Status = 'Departed'
        AND ATD >= DATEADD(DAY, -30, GETUTCDATE());
    
    -- Berth Utilization
    SELECT 
        b.BerthId,
        b.BerthName,
        COUNT(vs.ScheduleId) AS VesselsServed,
        AVG(CAST(vs.DwellTime AS FLOAT)) AS AvgDwellTime,
        CASE 
            WHEN EXISTS (
                SELECT 1 FROM dbo.VESSEL_SCHEDULE 
                WHERE BerthId = b.BerthId AND Status = 'Berthed'
            ) THEN 'Occupied'
            ELSE 'Available'
        END AS CurrentStatus
    FROM dbo.BERTHS b
    LEFT JOIN dbo.VESSEL_SCHEDULE vs ON b.BerthId = vs.BerthId
        AND vs.Status = 'Departed'
        AND vs.ATD >= DATEADD(DAY, -30, GETUTCDATE())
    WHERE b.IsActive = 1
    GROUP BY b.BerthId, b.BerthName;
    
    -- Active Conflicts
    SELECT 
        COUNT(*) AS TotalConflicts,
        SUM(CASE WHEN Severity = 1 THEN 1 ELSE 0 END) AS CriticalConflicts,
        SUM(CASE WHEN Severity = 2 THEN 1 ELSE 0 END) AS HighConflicts
    FROM dbo.CONFLICTS
    WHERE Status = 'Detected';
END
GO

-- =============================================
-- SP 9: Update Schedule Status
-- Update schedule status with validation
-- =============================================
CREATE OR ALTER PROCEDURE sp_UpdateScheduleStatus
    @ScheduleId INT,
    @NewStatus NVARCHAR(50)
AS
BEGIN
    SET NOCOUNT ON;

    BEGIN TRY
        -- Validate status
        IF @NewStatus NOT IN ('Scheduled', 'Approaching', 'Berthed', 'Departed', 'Cancelled')
        BEGIN
            RAISERROR('Invalid status value', 16, 1);
            RETURN;
        END

        -- Update status
        UPDATE dbo.VESSEL_SCHEDULE
        SET
            Status = @NewStatus,
            UpdatedAt = GETUTCDATE(),
            -- Set actual times based on status
            ATA = CASE WHEN @NewStatus = 'Approaching' AND ATA IS NULL THEN GETUTCDATE() ELSE ATA END,
            ATB = CASE WHEN @NewStatus = 'Berthed' AND ATB IS NULL THEN GETUTCDATE() ELSE ATB END,
            ATD = CASE WHEN @NewStatus = 'Departed' AND ATD IS NULL THEN GETUTCDATE() ELSE ATD END
        WHERE ScheduleId = @ScheduleId;

        SELECT
            'SUCCESS' AS Status,
            'Schedule status updated successfully' AS Message,
            @NewStatus AS NewStatus;

    END TRY
    BEGIN CATCH
        SELECT
            'ERROR' AS Status,
            ERROR_MESSAGE() AS Message;
    END CATCH
END
GO

-- =============================================
-- VERIFICATION
-- =============================================
PRINT '=============================================';
PRINT 'STORED PROCEDURES CREATED SUCCESSFULLY!';
PRINT '=============================================';
PRINT '';
PRINT 'Available Procedures:';
PRINT '  1. sp_CheckBerthAvailability - Check if berth is available';
PRINT '  2. sp_FindCompatibleBerthsByVessel - Find compatible berths for vessel by VesselId';
PRINT '  3. sp_FindCompatibleBerths - Find compatible berths by LOA/Draft dimensions';
PRINT '  4. sp_AllocateVesselToBerth - Create new schedule allocation';
PRINT '  5. sp_UpdateVesselETA - Update vessel ETA';
PRINT '  6. sp_RecordVesselArrival - Record actual arrival';
PRINT '  7. sp_RecordVesselBerthing - Record berthing';
PRINT '  8. sp_RecordVesselDeparture - Record departure';
PRINT '  9. sp_GetDashboardStats - Get dashboard statistics';
PRINT ' 10. sp_UpdateScheduleStatus - Update schedule status';
PRINT '=============================================';
GO
