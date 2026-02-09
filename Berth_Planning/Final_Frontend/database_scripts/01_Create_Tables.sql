-- =============================================
-- BERTH PLANNING & ALLOCATION OPTIMIZATION SYSTEM
-- MS-SQL Server Database Schema (Consolidated)
-- All 23 tables in one script
-- Version: 4.0
-- Date: 2026-02-04
-- =============================================

USE [BerthPlanning];
GO

-- =============================================
-- DROP EXISTING TABLES (in FK-safe order)
-- Uncomment to recreate from scratch
-- =============================================
/*
IF OBJECT_ID('dbo.UKC_DATA', 'U') IS NOT NULL DROP TABLE dbo.UKC_DATA;
IF OBJECT_ID('dbo.RESOURCE_ALLOCATION', 'U') IS NOT NULL DROP TABLE dbo.RESOURCE_ALLOCATION;
IF OBJECT_ID('dbo.VESSEL_HISTORY', 'U') IS NOT NULL DROP TABLE dbo.VESSEL_HISTORY;
IF OBJECT_ID('dbo.CONFLICTS', 'U') IS NOT NULL DROP TABLE dbo.CONFLICTS;
IF OBJECT_ID('dbo.ALERTS_NOTIFICATIONS', 'U') IS NOT NULL DROP TABLE dbo.ALERTS_NOTIFICATIONS;
IF OBJECT_ID('dbo.AUDIT_LOG', 'U') IS NOT NULL DROP TABLE dbo.AUDIT_LOG;
IF OBJECT_ID('dbo.AIS_DATA', 'U') IS NOT NULL DROP TABLE dbo.AIS_DATA;
IF OBJECT_ID('dbo.WEATHER_DATA', 'U') IS NOT NULL DROP TABLE dbo.WEATHER_DATA;
IF OBJECT_ID('dbo.TIDAL_DATA', 'U') IS NOT NULL DROP TABLE dbo.TIDAL_DATA;
IF OBJECT_ID('dbo.OPTIMIZATION_RUNS', 'U') IS NOT NULL DROP TABLE dbo.OPTIMIZATION_RUNS;
IF OBJECT_ID('dbo.KNOWLEDGE_BASE', 'U') IS NOT NULL DROP TABLE dbo.KNOWLEDGE_BASE;
IF OBJECT_ID('dbo.USER_PREFERENCES', 'U') IS NOT NULL DROP TABLE dbo.USER_PREFERENCES;
IF OBJECT_ID('dbo.VESSEL_SCHEDULE', 'U') IS NOT NULL DROP TABLE dbo.VESSEL_SCHEDULE;
IF OBJECT_ID('dbo.BERTH_MAINTENANCE', 'U') IS NOT NULL DROP TABLE dbo.BERTH_MAINTENANCE;
IF OBJECT_ID('dbo.RESOURCES', 'U') IS NOT NULL DROP TABLE dbo.RESOURCES;
IF OBJECT_ID('dbo.BERTHS', 'U') IS NOT NULL DROP TABLE dbo.BERTHS;
IF OBJECT_ID('dbo.TERMINALS', 'U') IS NOT NULL DROP TABLE dbo.TERMINALS;
IF OBJECT_ID('dbo.CHANNELS', 'U') IS NOT NULL DROP TABLE dbo.CHANNELS;
IF OBJECT_ID('dbo.ANCHORAGES', 'U') IS NOT NULL DROP TABLE dbo.ANCHORAGES;
IF OBJECT_ID('dbo.PILOTS', 'U') IS NOT NULL DROP TABLE dbo.PILOTS;
IF OBJECT_ID('dbo.TUGBOATS', 'U') IS NOT NULL DROP TABLE dbo.TUGBOATS;
IF OBJECT_ID('dbo.PORTS', 'U') IS NOT NULL DROP TABLE dbo.PORTS;
IF OBJECT_ID('dbo.VESSELS', 'U') IS NOT NULL DROP TABLE dbo.VESSELS;
*/

-- =============================================
-- 1. PORTS
-- =============================================
IF OBJECT_ID('dbo.PORTS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.PORTS (
        PortId INT IDENTITY(1,1) NOT NULL,
        PortName NVARCHAR(200) NOT NULL,
        PortCode NVARCHAR(10) NOT NULL,
        Country NVARCHAR(100) NULL,
        City NVARCHAR(100) NULL,
        TimeZone NVARCHAR(50) NULL,
        Latitude DECIMAL(10,7) NULL,
        Longitude DECIMAL(10,7) NULL,
        ContactEmail NVARCHAR(200) NULL,
        ContactPhone NVARCHAR(50) NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Ports PRIMARY KEY CLUSTERED (PortId),
        CONSTRAINT UQ_Ports_PortCode UNIQUE (PortCode)
    );

    CREATE NONCLUSTERED INDEX IX_Ports_Country ON dbo.PORTS(Country);
    CREATE NONCLUSTERED INDEX IX_Ports_IsActive ON dbo.PORTS(IsActive);
END
GO

-- =============================================
-- 2. TERMINALS
-- =============================================
IF OBJECT_ID('dbo.TERMINALS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.TERMINALS (
        TerminalId INT IDENTITY(1,1) NOT NULL,
        PortId INT NOT NULL,
        TerminalName NVARCHAR(200) NOT NULL,
        TerminalCode NVARCHAR(20) NOT NULL,
        TerminalType NVARCHAR(50) NULL,
        OperatorName NVARCHAR(200) NULL,
        TotalBerths INT NULL DEFAULT 0,
        Latitude DECIMAL(10,7) NULL,
        Longitude DECIMAL(10,7) NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Terminals PRIMARY KEY CLUSTERED (TerminalId),
        CONSTRAINT UQ_Terminals_TerminalCode UNIQUE (TerminalCode),
        CONSTRAINT FK_Terminals_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId)
    );

    CREATE NONCLUSTERED INDEX IX_Terminals_PortId ON dbo.TERMINALS(PortId);
    CREATE NONCLUSTERED INDEX IX_Terminals_TerminalType ON dbo.TERMINALS(TerminalType);
    CREATE NONCLUSTERED INDEX IX_Terminals_IsActive ON dbo.TERMINALS(IsActive);
END
GO

-- =============================================
-- 3. VESSELS
-- =============================================
IF OBJECT_ID('dbo.VESSELS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.VESSELS (
        VesselId INT IDENTITY(1,1) NOT NULL,
        VesselName NVARCHAR(200) NOT NULL,
        IMO NVARCHAR(20) NULL,
        MMSI NVARCHAR(20) NULL,
        VesselType NVARCHAR(50) NULL,
        LOA DECIMAL(8,2) NULL,
        Beam DECIMAL(6,2) NULL,
        Draft DECIMAL(6,2) NULL,
        GrossTonnage INT NULL,
        CargoType NVARCHAR(100) NULL,
        CargoVolume DECIMAL(12,2) NULL,
        CargoUnit NVARCHAR(20) NULL,
        Priority INT NOT NULL DEFAULT 2,
        FlagState NVARCHAR(10) NULL,
        FlagStateName NVARCHAR(100) NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Vessels PRIMARY KEY CLUSTERED (VesselId),
        CONSTRAINT UQ_Vessels_IMO UNIQUE (IMO),
        CONSTRAINT CK_Vessels_Priority CHECK (Priority BETWEEN 1 AND 3),
        CONSTRAINT CK_Vessels_LOA CHECK (LOA > 0),
        CONSTRAINT CK_Vessels_Beam CHECK (Beam > 0),
        CONSTRAINT CK_Vessels_Draft CHECK (Draft > 0)
    );

    CREATE NONCLUSTERED INDEX IX_Vessels_VesselType ON dbo.VESSELS(VesselType);
    CREATE NONCLUSTERED INDEX IX_Vessels_Priority ON dbo.VESSELS(Priority);
    CREATE NONCLUSTERED INDEX IX_Vessels_MMSI ON dbo.VESSELS(MMSI);
END
GO

-- =============================================
-- 4. BERTHS
-- =============================================
IF OBJECT_ID('dbo.BERTHS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.BERTHS (
        BerthId INT IDENTITY(1,1) NOT NULL,
        TerminalId INT NULL,
        PortId INT NULL,
        PortCode NVARCHAR(10) NULL,
        BerthName NVARCHAR(100) NOT NULL,
        BerthCode NVARCHAR(20) NOT NULL,
        Length DECIMAL(8,2) NOT NULL,
        Depth DECIMAL(6,2) NOT NULL,
        MaxDraft DECIMAL(6,2) NOT NULL,
        MaxLOA DECIMAL(8,2) NULL,
        MaxBeam DECIMAL(6,2) NULL,
        BerthType NVARCHAR(50) NULL,
        NumberOfCranes INT NOT NULL DEFAULT 0,
        BollardCount INT NOT NULL DEFAULT 0,
        IsActive BIT NOT NULL DEFAULT 1,
        Latitude DECIMAL(10,7) NULL,
        Longitude DECIMAL(10,7) NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Berths PRIMARY KEY CLUSTERED (BerthId),
        CONSTRAINT UQ_Berths_BerthCode UNIQUE (BerthCode),
        CONSTRAINT FK_Berths_Terminals FOREIGN KEY (TerminalId) REFERENCES dbo.TERMINALS(TerminalId),
        CONSTRAINT FK_Berths_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId),
        CONSTRAINT CK_Berths_Length CHECK (Length > 0),
        CONSTRAINT CK_Berths_Depth CHECK (Depth > 0),
        CONSTRAINT CK_Berths_MaxDraft CHECK (MaxDraft > 0)
    );

    CREATE NONCLUSTERED INDEX IX_Berths_TerminalId ON dbo.BERTHS(TerminalId);
    CREATE NONCLUSTERED INDEX IX_Berths_BerthType ON dbo.BERTHS(BerthType);
    CREATE NONCLUSTERED INDEX IX_Berths_IsActive ON dbo.BERTHS(IsActive);
END
GO

-- =============================================
-- 5. VESSEL_SCHEDULE
-- =============================================
IF OBJECT_ID('dbo.VESSEL_SCHEDULE', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.VESSEL_SCHEDULE (
        ScheduleId INT IDENTITY(1,1) NOT NULL,
        VesselId INT NOT NULL,
        BerthId INT NULL,

        -- Estimated Times
        ETA DATETIME2 NULL,
        PredictedETA DATETIME2 NULL,
        ETD DATETIME2 NULL,

        -- Actual Times
        ATA DATETIME2 NULL,
        ATB DATETIME2 NULL,
        ATD DATETIME2 NULL,

        -- Lifecycle Timestamps
        AnchorageArrival DATETIME2 NULL,
        PilotBoardingTime DATETIME2 NULL,
        BerthArrivalTime DATETIME2 NULL,
        FirstLineTime DATETIME2 NULL,
        AllFastTime DATETIME2 NULL,
        CargoStartTime DATETIME2 NULL,
        CargoCompleteTime DATETIME2 NULL,

        -- Status and Metrics
        Status NVARCHAR(50) NOT NULL DEFAULT 'Scheduled',
        DwellTime INT NULL,
        WaitingTime INT NULL,

        -- Cargo Info
        CargoType NVARCHAR(100) NULL,
        CargoQuantity DECIMAL(12,2) NULL,
        CargoUnit NVARCHAR(20) NULL,
        CargoOperation NVARCHAR(50) NULL,

        -- Voyage Info
        PortCode NVARCHAR(10) NULL,
        VoyageNumber NVARCHAR(50) NULL,
        ShippingLine NVARCHAR(200) NULL,
        TerminalType NVARCHAR(50) NULL,

        -- Resource Assignments
        TugsAssigned INT NULL,
        PilotsAssigned INT NULL,

        -- Performance Metrics
        WaitingTimeHours DECIMAL(8,2) NULL,
        DwellTimeHours DECIMAL(8,2) NULL,
        ETAVarianceHours DECIMAL(8,2) NULL,
        BerthingDelayMins INT NULL,
        ArrivalDraft DECIMAL(6,2) NULL,
        DepartureDraft DECIMAL(6,2) NULL,

        -- Optimization
        OptimizationScore DECIMAL(5,2) NULL,
        IsOptimized BIT NOT NULL DEFAULT 0,
        ConflictCount INT NOT NULL DEFAULT 0,

        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_VesselSchedule PRIMARY KEY CLUSTERED (ScheduleId),
        CONSTRAINT FK_VesselSchedule_Vessels FOREIGN KEY (VesselId) REFERENCES dbo.VESSELS(VesselId),
        CONSTRAINT FK_VesselSchedule_Berths FOREIGN KEY (BerthId) REFERENCES dbo.BERTHS(BerthId),
        CONSTRAINT CK_VesselSchedule_Status CHECK (Status IN ('Scheduled', 'Approaching', 'Berthed', 'Departed', 'Cancelled')),
        CONSTRAINT CK_VesselSchedule_DwellTime CHECK (DwellTime > 0),
        CONSTRAINT CK_VesselSchedule_WaitingTime CHECK (WaitingTime >= 0)
    );

    CREATE NONCLUSTERED INDEX IX_VesselSchedule_VesselId ON dbo.VESSEL_SCHEDULE(VesselId);
    CREATE NONCLUSTERED INDEX IX_VesselSchedule_BerthId ON dbo.VESSEL_SCHEDULE(BerthId);
    CREATE NONCLUSTERED INDEX IX_VesselSchedule_Status ON dbo.VESSEL_SCHEDULE(Status);
    CREATE NONCLUSTERED INDEX IX_VesselSchedule_ETA ON dbo.VESSEL_SCHEDULE(ETA);
    CREATE NONCLUSTERED INDEX IX_VesselSchedule_BerthId_ETA ON dbo.VESSEL_SCHEDULE(BerthId, ETA) INCLUDE (ETD, Status);
END
GO

-- =============================================
-- 6. RESOURCES
-- =============================================
IF OBJECT_ID('dbo.RESOURCES', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.RESOURCES (
        ResourceId INT IDENTITY(1,1) NOT NULL,
        ResourceType NVARCHAR(50) NOT NULL,
        ResourceName NVARCHAR(100) NOT NULL,
        Capacity INT NOT NULL DEFAULT 1,
        IsAvailable BIT NOT NULL DEFAULT 1,
        MaintenanceSchedule DATETIME2 NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Resources PRIMARY KEY CLUSTERED (ResourceId),
        CONSTRAINT CK_Resources_Type CHECK (ResourceType IN ('Crane', 'Tugboat', 'Pilot', 'Labor', 'Mooring', 'Other')),
        CONSTRAINT CK_Resources_Capacity CHECK (Capacity > 0)
    );

    CREATE NONCLUSTERED INDEX IX_Resources_Type ON dbo.RESOURCES(ResourceType);
    CREATE NONCLUSTERED INDEX IX_Resources_IsAvailable ON dbo.RESOURCES(IsAvailable);
END
GO

-- =============================================
-- 7. RESOURCE_ALLOCATION
-- =============================================
IF OBJECT_ID('dbo.RESOURCE_ALLOCATION', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.RESOURCE_ALLOCATION (
        AllocationId INT IDENTITY(1,1) NOT NULL,
        ScheduleId INT NOT NULL,
        ResourceId INT NOT NULL,
        AllocatedFrom DATETIME2 NOT NULL,
        AllocatedTo DATETIME2 NOT NULL,
        Quantity INT NOT NULL DEFAULT 1,
        Status NVARCHAR(50) NOT NULL DEFAULT 'Allocated',
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_ResourceAllocation PRIMARY KEY CLUSTERED (AllocationId),
        CONSTRAINT FK_ResourceAllocation_Schedule FOREIGN KEY (ScheduleId) REFERENCES dbo.VESSEL_SCHEDULE(ScheduleId),
        CONSTRAINT FK_ResourceAllocation_Resources FOREIGN KEY (ResourceId) REFERENCES dbo.RESOURCES(ResourceId),
        CONSTRAINT CK_ResourceAllocation_Status CHECK (Status IN ('Allocated', 'InUse', 'Released')),
        CONSTRAINT CK_ResourceAllocation_Quantity CHECK (Quantity > 0),
        CONSTRAINT CK_ResourceAllocation_TimeRange CHECK (AllocatedFrom < AllocatedTo)
    );

    CREATE NONCLUSTERED INDEX IX_ResourceAllocation_ScheduleId ON dbo.RESOURCE_ALLOCATION(ScheduleId);
    CREATE NONCLUSTERED INDEX IX_ResourceAllocation_ResourceId ON dbo.RESOURCE_ALLOCATION(ResourceId);
    CREATE NONCLUSTERED INDEX IX_ResourceAllocation_TimeRange ON dbo.RESOURCE_ALLOCATION(ResourceId, AllocatedFrom, AllocatedTo);
END
GO

-- =============================================
-- 8. WEATHER_DATA
-- =============================================
IF OBJECT_ID('dbo.WEATHER_DATA', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.WEATHER_DATA (
        WeatherId INT IDENTITY(1,1) NOT NULL,
        PortId INT NULL,
        PortCode NVARCHAR(10) NULL,
        RecordedAt DATETIME2 NOT NULL,
        WindSpeed DECIMAL(5,2) NULL,
        WindDirection INT NULL,
        WindDirectionText NVARCHAR(10) NULL,
        Visibility INT NULL,
        WaveHeight DECIMAL(4,2) NULL,
        Temperature DECIMAL(5,2) NULL,
        Precipitation DECIMAL(5,2) NULL,
        WeatherCondition NVARCHAR(100) NULL,
        Climate NVARCHAR(50) NULL,
        Season NVARCHAR(20) NULL,
        IsAlert BIT NOT NULL DEFAULT 0,
        FetchedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_WeatherData PRIMARY KEY CLUSTERED (WeatherId),
        CONSTRAINT FK_WeatherData_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId),
        CONSTRAINT CK_WeatherData_WindDirection CHECK (WindDirection BETWEEN 0 AND 360)
    );

    CREATE NONCLUSTERED INDEX IX_WeatherData_RecordedAt ON dbo.WEATHER_DATA(RecordedAt DESC);
    CREATE NONCLUSTERED INDEX IX_WeatherData_IsAlert ON dbo.WEATHER_DATA(IsAlert) WHERE IsAlert = 1;
END
GO

-- =============================================
-- 9. TIDAL_DATA
-- =============================================
IF OBJECT_ID('dbo.TIDAL_DATA', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.TIDAL_DATA (
        TidalId INT IDENTITY(1,1) NOT NULL,
        TideTime DATETIME2 NOT NULL,
        TideType NVARCHAR(20) NOT NULL,
        Height DECIMAL(5,2) NOT NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_TidalData PRIMARY KEY CLUSTERED (TidalId),
        CONSTRAINT CK_TidalData_Type CHECK (TideType IN ('HighTide', 'LowTide'))
    );

    CREATE NONCLUSTERED INDEX IX_TidalData_TideTime ON dbo.TIDAL_DATA(TideTime);
    CREATE NONCLUSTERED INDEX IX_TidalData_TideType ON dbo.TIDAL_DATA(TideType);
END
GO

-- =============================================
-- 10. AIS_DATA
-- =============================================
IF OBJECT_ID('dbo.AIS_DATA', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.AIS_DATA (
        AISId INT IDENTITY(1,1) NOT NULL,
        VesselId INT NOT NULL,
        MMSI NVARCHAR(20) NULL,
        PortCode NVARCHAR(10) NULL,
        VesselType NVARCHAR(50) NULL,
        Latitude DECIMAL(10,7) NOT NULL,
        Longitude DECIMAL(10,7) NOT NULL,
        Speed DECIMAL(5,2) NULL,
        Course DECIMAL(5,2) NULL,
        Heading DECIMAL(5,2) NULL,
        NavigationStatus NVARCHAR(50) NULL,
        NavigationStatusCode INT NULL,
        ETA DATETIME2 NULL,
        TimeToPort INT NULL,
        Phase NVARCHAR(50) NULL,
        DistanceToPort DECIMAL(10,2) NULL,
        RecordedAt DATETIME2 NOT NULL,
        FetchedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_AISData PRIMARY KEY CLUSTERED (AISId),
        CONSTRAINT FK_AISData_Vessels FOREIGN KEY (VesselId) REFERENCES dbo.VESSELS(VesselId),
        CONSTRAINT CK_AISData_Latitude CHECK (Latitude BETWEEN -90 AND 90),
        CONSTRAINT CK_AISData_Longitude CHECK (Longitude BETWEEN -180 AND 180),
        CONSTRAINT CK_AISData_Speed CHECK (Speed >= 0),
        CONSTRAINT CK_AISData_Course CHECK (Course BETWEEN 0 AND 360),
        CONSTRAINT CK_AISData_Heading CHECK (Heading BETWEEN 0 AND 360)
    );

    CREATE NONCLUSTERED INDEX IX_AISData_VesselId_RecordedAt ON dbo.AIS_DATA(VesselId, RecordedAt DESC);
    CREATE NONCLUSTERED INDEX IX_AISData_MMSI ON dbo.AIS_DATA(MMSI);
END
GO

-- =============================================
-- 11. CONFLICTS
-- =============================================
IF OBJECT_ID('dbo.CONFLICTS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CONFLICTS (
        ConflictId INT IDENTITY(1,1) NOT NULL,
        ConflictType NVARCHAR(50) NOT NULL,
        ScheduleId1 INT NOT NULL,
        ScheduleId2 INT NULL,
        Description NVARCHAR(500) NULL,
        Severity INT NOT NULL DEFAULT 2,
        Status NVARCHAR(50) NOT NULL DEFAULT 'Detected',
        DetectedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        ResolvedAt DATETIME2 NULL,
        Resolution NVARCHAR(MAX) NULL,

        CONSTRAINT PK_Conflicts PRIMARY KEY CLUSTERED (ConflictId),
        CONSTRAINT FK_Conflicts_Schedule1 FOREIGN KEY (ScheduleId1) REFERENCES dbo.VESSEL_SCHEDULE(ScheduleId),
        CONSTRAINT FK_Conflicts_Schedule2 FOREIGN KEY (ScheduleId2) REFERENCES dbo.VESSEL_SCHEDULE(ScheduleId),
        CONSTRAINT CK_Conflicts_Type CHECK (ConflictType IN ('BerthOverlap', 'ResourceUnavailable', 'TidalConstraint', 'PriorityViolation')),
        CONSTRAINT CK_Conflicts_Severity CHECK (Severity BETWEEN 1 AND 4),
        CONSTRAINT CK_Conflicts_Status CHECK (Status IN ('Detected', 'Resolved', 'Ignored'))
    );

    CREATE NONCLUSTERED INDEX IX_Conflicts_Status ON dbo.CONFLICTS(Status);
    CREATE NONCLUSTERED INDEX IX_Conflicts_ScheduleId1 ON dbo.CONFLICTS(ScheduleId1);
    CREATE NONCLUSTERED INDEX IX_Conflicts_ScheduleId2 ON dbo.CONFLICTS(ScheduleId2);
    CREATE NONCLUSTERED INDEX IX_Conflicts_DetectedAt ON dbo.CONFLICTS(DetectedAt DESC);
END
GO

-- =============================================
-- 12. OPTIMIZATION_RUNS
-- =============================================
IF OBJECT_ID('dbo.OPTIMIZATION_RUNS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.OPTIMIZATION_RUNS (
        RunId INT IDENTITY(1,1) NOT NULL,
        RunType NVARCHAR(50) NOT NULL,
        Algorithm NVARCHAR(100) NULL,
        InputParameters NVARCHAR(MAX) NULL,
        OutputResults NVARCHAR(MAX) NULL,
        ExecutionTime INT NULL,
        ImprovementScore DECIMAL(5,2) NULL,
        Status NVARCHAR(50) NOT NULL DEFAULT 'Running',
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        CompletedAt DATETIME2 NULL,

        CONSTRAINT PK_OptimizationRuns PRIMARY KEY CLUSTERED (RunId),
        CONSTRAINT CK_OptimizationRuns_Type CHECK (RunType IN ('Initial', 'ReOptimization', 'ConflictResolution')),
        CONSTRAINT CK_OptimizationRuns_Status CHECK (Status IN ('Running', 'Completed', 'Failed')),
        CONSTRAINT CK_OptimizationRuns_ExecutionTime CHECK (ExecutionTime >= 0)
    );

    CREATE NONCLUSTERED INDEX IX_OptimizationRuns_CreatedAt ON dbo.OPTIMIZATION_RUNS(CreatedAt DESC);
    CREATE NONCLUSTERED INDEX IX_OptimizationRuns_Status ON dbo.OPTIMIZATION_RUNS(Status);
END
GO

-- =============================================
-- 13. KNOWLEDGE_BASE
-- =============================================
IF OBJECT_ID('dbo.KNOWLEDGE_BASE', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.KNOWLEDGE_BASE (
        KnowledgeId INT IDENTITY(1,1) NOT NULL,
        DocumentType NVARCHAR(100) NULL,
        Title NVARCHAR(500) NOT NULL,
        Content NVARCHAR(MAX) NOT NULL,
        Embedding VARBINARY(MAX) NULL,
        Metadata NVARCHAR(MAX) NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_KnowledgeBase PRIMARY KEY CLUSTERED (KnowledgeId)
    );

    CREATE NONCLUSTERED INDEX IX_KnowledgeBase_DocumentType ON dbo.KNOWLEDGE_BASE(DocumentType);
    CREATE NONCLUSTERED INDEX IX_KnowledgeBase_CreatedAt ON dbo.KNOWLEDGE_BASE(CreatedAt DESC);
END
GO

-- =============================================
-- 14. VESSEL_HISTORY
-- =============================================
IF OBJECT_ID('dbo.VESSEL_HISTORY', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.VESSEL_HISTORY (
        HistoryId INT IDENTITY(1,1) NOT NULL,
        VesselId INT NOT NULL,
        BerthId INT NOT NULL,
        VisitDate DATETIME2 NOT NULL,
        ActualDwellTime INT NULL,
        ActualWaitingTime INT NULL,
        ETAAccuracy DECIMAL(5,2) NULL,
        Notes NVARCHAR(500) NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_VesselHistory PRIMARY KEY CLUSTERED (HistoryId),
        CONSTRAINT FK_VesselHistory_Vessels FOREIGN KEY (VesselId) REFERENCES dbo.VESSELS(VesselId),
        CONSTRAINT FK_VesselHistory_Berths FOREIGN KEY (BerthId) REFERENCES dbo.BERTHS(BerthId),
        CONSTRAINT CK_VesselHistory_DwellTime CHECK (ActualDwellTime > 0),
        CONSTRAINT CK_VesselHistory_WaitingTime CHECK (ActualWaitingTime >= 0)
    );

    CREATE NONCLUSTERED INDEX IX_VesselHistory_VesselId ON dbo.VESSEL_HISTORY(VesselId);
    CREATE NONCLUSTERED INDEX IX_VesselHistory_BerthId ON dbo.VESSEL_HISTORY(BerthId);
    CREATE NONCLUSTERED INDEX IX_VesselHistory_VisitDate ON dbo.VESSEL_HISTORY(VisitDate DESC);
END
GO

-- =============================================
-- 15. BERTH_MAINTENANCE
-- =============================================
IF OBJECT_ID('dbo.BERTH_MAINTENANCE', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.BERTH_MAINTENANCE (
        MaintenanceId INT IDENTITY(1,1) NOT NULL,
        BerthId INT NOT NULL,
        StartTime DATETIME2 NOT NULL,
        EndTime DATETIME2 NOT NULL,
        MaintenanceType NVARCHAR(50) NULL,
        Status NVARCHAR(50) NOT NULL DEFAULT 'Scheduled',
        Description NVARCHAR(500) NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_BerthMaintenance PRIMARY KEY CLUSTERED (MaintenanceId),
        CONSTRAINT FK_BerthMaintenance_Berths FOREIGN KEY (BerthId) REFERENCES dbo.BERTHS(BerthId),
        CONSTRAINT CK_BerthMaintenance_Status CHECK (Status IN ('Scheduled', 'InProgress', 'Completed', 'Cancelled')),
        CONSTRAINT CK_BerthMaintenance_TimeRange CHECK (StartTime < EndTime)
    );

    CREATE NONCLUSTERED INDEX IX_BerthMaintenance_BerthId ON dbo.BERTH_MAINTENANCE(BerthId);
    CREATE NONCLUSTERED INDEX IX_BerthMaintenance_Status ON dbo.BERTH_MAINTENANCE(Status);
    CREATE NONCLUSTERED INDEX IX_BerthMaintenance_TimeRange ON dbo.BERTH_MAINTENANCE(BerthId, StartTime, EndTime);
END
GO

-- =============================================
-- 16. ALERTS_NOTIFICATIONS
-- =============================================
IF OBJECT_ID('dbo.ALERTS_NOTIFICATIONS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ALERTS_NOTIFICATIONS (
        AlertId INT IDENTITY(1,1) NOT NULL,
        AlertType NVARCHAR(50) NOT NULL,
        RelatedEntityId INT NULL,
        EntityType NVARCHAR(50) NULL,
        Severity NVARCHAR(20) NOT NULL DEFAULT 'Medium',
        Message NVARCHAR(500) NOT NULL,
        IsRead BIT NOT NULL DEFAULT 0,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        ReadAt DATETIME2 NULL,

        CONSTRAINT PK_AlertsNotifications PRIMARY KEY CLUSTERED (AlertId),
        CONSTRAINT CK_AlertsNotifications_Severity CHECK (Severity IN ('Critical', 'High', 'Medium', 'Low'))
    );

    CREATE NONCLUSTERED INDEX IX_AlertsNotifications_IsRead ON dbo.ALERTS_NOTIFICATIONS(IsRead) WHERE IsRead = 0;
    CREATE NONCLUSTERED INDEX IX_AlertsNotifications_CreatedAt ON dbo.ALERTS_NOTIFICATIONS(CreatedAt DESC);
    CREATE NONCLUSTERED INDEX IX_AlertsNotifications_Severity ON dbo.ALERTS_NOTIFICATIONS(Severity);
END
GO

-- =============================================
-- 17. USER_PREFERENCES
-- =============================================
IF OBJECT_ID('dbo.USER_PREFERENCES', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.USER_PREFERENCES (
        PreferenceId INT IDENTITY(1,1) NOT NULL,
        UserId NVARCHAR(100) NOT NULL,
        PreferenceKey NVARCHAR(100) NOT NULL,
        PreferenceValue NVARCHAR(MAX) NULL,
        UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_UserPreferences PRIMARY KEY CLUSTERED (PreferenceId),
        CONSTRAINT UQ_UserPreferences_UserKey UNIQUE (UserId, PreferenceKey)
    );

    CREATE NONCLUSTERED INDEX IX_UserPreferences_UserId ON dbo.USER_PREFERENCES(UserId);
END
GO

-- =============================================
-- 18. AUDIT_LOG
-- =============================================
IF OBJECT_ID('dbo.AUDIT_LOG', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.AUDIT_LOG (
        LogId BIGINT IDENTITY(1,1) NOT NULL,
        UserId NVARCHAR(100) NULL,
        Action NVARCHAR(50) NOT NULL,
        EntityType NVARCHAR(50) NOT NULL,
        EntityId INT NOT NULL,
        OldValue NVARCHAR(MAX) NULL,
        NewValue NVARCHAR(MAX) NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_AuditLog PRIMARY KEY CLUSTERED (LogId)
    );

    CREATE NONCLUSTERED INDEX IX_AuditLog_EntityType_EntityId ON dbo.AUDIT_LOG(EntityType, EntityId);
    CREATE NONCLUSTERED INDEX IX_AuditLog_CreatedAt ON dbo.AUDIT_LOG(CreatedAt DESC);
    CREATE NONCLUSTERED INDEX IX_AuditLog_UserId ON dbo.AUDIT_LOG(UserId);
END
GO

-- =============================================
-- 19. ANCHORAGES (moved before CHANNELS for FK dependency)
-- =============================================
IF OBJECT_ID('dbo.ANCHORAGES', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ANCHORAGES (
        AnchorageId INT IDENTITY(1,1) NOT NULL,
        PortId INT NOT NULL,
        AnchorageName NVARCHAR(200) NOT NULL,
        AnchorageType NVARCHAR(50) NULL,
        Latitude DECIMAL(10,7) NULL,
        Longitude DECIMAL(10,7) NULL,
        Depth INT NULL,
        MaxVessels INT NULL,
        CurrentOccupancy INT NULL DEFAULT 0,
        MaxVesselLOA INT NULL,
        MaxVesselDraft DECIMAL(6,2) NULL,
        AverageWaitingTime DECIMAL(8,2) NULL,
        STSCargoOpsPermitted BIT NULL DEFAULT 0,
        QuarantineAnchorage BIT NULL DEFAULT 0,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Anchorages PRIMARY KEY CLUSTERED (AnchorageId),
        CONSTRAINT FK_Anchorages_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId)
    );

    CREATE NONCLUSTERED INDEX IX_Anchorages_PortId ON dbo.ANCHORAGES(PortId);
    CREATE NONCLUSTERED INDEX IX_Anchorages_AnchorageType ON dbo.ANCHORAGES(AnchorageType);
END
GO

-- =============================================
-- 20. CHANNELS
-- =============================================
IF OBJECT_ID('dbo.CHANNELS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CHANNELS (
        ChannelId INT IDENTITY(1,1) NOT NULL,
        PortId INT NOT NULL,
        ChannelName NVARCHAR(200) NOT NULL,
        ChannelLength DECIMAL(10,2) NULL,
        ChannelWidth DECIMAL(8,2) NULL,
        ChannelDepth DECIMAL(6,2) NULL,
        ChannelDepthAtChartDatum DECIMAL(6,2) NULL,
        OneWayOrTwoWay NVARCHAR(20) NULL,
        MaxVesselLOA DECIMAL(8,2) NULL,
        MaxVesselBeam DECIMAL(6,2) NULL,
        MaxVesselDraft DECIMAL(6,2) NULL,
        TrafficSeparationScheme BIT NULL DEFAULT 0,
        SpeedLimit INT NULL,
        TidalWindowRequired BIT NULL DEFAULT 0,
        PilotageCompulsory BIT NULL DEFAULT 1,
        TugEscortRequired BIT NULL DEFAULT 0,
        DayNightRestrictions NVARCHAR(500) NULL,
        VisibilityMinimum INT NULL,
        WindSpeedLimit INT NULL,
        CurrentSpeedLimit DECIMAL(5,2) NULL,
        ChannelSegments NVARCHAR(MAX) NULL,
        AnchorageAreaId INT NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Channels PRIMARY KEY CLUSTERED (ChannelId),
        CONSTRAINT FK_Channels_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId),
        CONSTRAINT FK_Channels_Anchorages FOREIGN KEY (AnchorageAreaId) REFERENCES dbo.ANCHORAGES(AnchorageId)
    );

    CREATE NONCLUSTERED INDEX IX_Channels_PortId ON dbo.CHANNELS(PortId);
    CREATE NONCLUSTERED INDEX IX_Channels_IsActive ON dbo.CHANNELS(IsActive);
END
GO

-- =============================================
-- 21. PILOTS
-- =============================================
IF OBJECT_ID('dbo.PILOTS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.PILOTS (
        PilotId INT IDENTITY(1,1) NOT NULL,
        PortCode NVARCHAR(10) NOT NULL,
        PortName NVARCHAR(200) NULL,
        PilotName NVARCHAR(200) NOT NULL,
        PilotCode NVARCHAR(20) NULL,
        PilotType NVARCHAR(50) NULL,
        PilotClass NVARCHAR(20) NULL,
        CertificationLevel NVARCHAR(50) NULL,
        ExperienceYears INT NULL,
        MaxVesselGT INT NULL,
        MaxVesselLOA INT NULL,
        NightOperations BIT NULL DEFAULT 1,
        AdverseWeather BIT NULL DEFAULT 0,
        CanTrain BIT NULL DEFAULT 0,
        LicenseIssueDate DATE NULL,
        LicenseExpiryDate DATE NULL,
        Status NVARCHAR(50) NULL DEFAULT 'Active',
        Languages NVARCHAR(500) NULL,
        Certifications NVARCHAR(MAX) NULL,
        CertificationsCount INT NULL,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Pilots PRIMARY KEY CLUSTERED (PilotId),
        CONSTRAINT FK_Pilots_Ports FOREIGN KEY (PortCode) REFERENCES dbo.PORTS(PortCode)
    );

    CREATE NONCLUSTERED INDEX IX_Pilots_PortCode ON dbo.PILOTS(PortCode);
    CREATE NONCLUSTERED INDEX IX_Pilots_PilotType ON dbo.PILOTS(PilotType);
    CREATE NONCLUSTERED INDEX IX_Pilots_Status ON dbo.PILOTS(Status);
    CREATE NONCLUSTERED INDEX IX_Pilots_CertificationLevel ON dbo.PILOTS(CertificationLevel);
END
GO

-- =============================================
-- 22. TUGBOATS
-- =============================================
IF OBJECT_ID('dbo.TUGBOATS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.TUGBOATS (
        TugId INT IDENTITY(1,1) NOT NULL,
        PortCode NVARCHAR(10) NOT NULL,
        TugName NVARCHAR(200) NOT NULL,
        TugCode NVARCHAR(20) NULL,
        IMONumber NVARCHAR(20) NULL,
        MMSI NVARCHAR(20) NULL,
        CallSign NVARCHAR(20) NULL,
        FlagState NVARCHAR(10) NULL,
        PortOfRegistry NVARCHAR(200) NULL,
        TugType NVARCHAR(50) NULL,
        TugTypeFullName NVARCHAR(100) NULL,
        TugClass NVARCHAR(20) NULL,
        Operator NVARCHAR(200) NULL,
        BollardPull INT NULL,
        Length DECIMAL(6,2) NULL,
        Beam DECIMAL(6,2) NULL,
        Draft DECIMAL(6,2) NULL,
        EnginePower INT NULL,
        MaxSpeed DECIMAL(5,2) NULL,
        YearBuilt INT NULL,
        FiFiClass NVARCHAR(20) NULL,
        WinchCapacity INT NULL,
        CrewSize INT NULL,
        [Status] NVARCHAR(50) NULL DEFAULT 'Operational',
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Tugboats PRIMARY KEY CLUSTERED (TugId),
        CONSTRAINT FK_Tugboats_Ports FOREIGN KEY (PortCode) REFERENCES dbo.PORTS(PortCode)
    );

    CREATE NONCLUSTERED INDEX IX_Tugboats_PortCode ON dbo.TUGBOATS(PortCode);
    CREATE NONCLUSTERED INDEX IX_Tugboats_TugType ON dbo.TUGBOATS(TugType);
    CREATE NONCLUSTERED INDEX IX_Tugboats_TugClass ON dbo.TUGBOATS(TugClass);
    CREATE NONCLUSTERED INDEX IX_Tugboats_Status ON dbo.TUGBOATS([Status]);
END
GO

-- =============================================
-- 23. UKC_DATA
-- =============================================
IF OBJECT_ID('dbo.UKC_DATA', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.UKC_DATA (
        UKCId INT IDENTITY(1,1) NOT NULL,
        PortId INT NULL,
        PortCode NVARCHAR(10) NULL,
        VesselType NVARCHAR(50) NULL,
        VesselLOA DECIMAL(8,2) NULL,
        VesselBeam DECIMAL(6,2) NULL,
        VesselDraft DECIMAL(6,2) NULL,
        GrossTonnage INT NULL,
        ChannelDepth DECIMAL(6,2) NULL,
        TidalHeight DECIMAL(5,2) NULL,
        AvailableDepth DECIMAL(6,2) NULL,
        StaticUKC DECIMAL(5,2) NULL,
        Squat DECIMAL(5,2) NULL,
        DynamicUKC DECIMAL(5,2) NULL,
        UKCPercentage DECIMAL(5,2) NULL,
        RequiredUKCPercentage DECIMAL(5,2) NULL,
        IsSafe BIT NULL,
        SpeedKnots DECIMAL(5,2) NULL,
        BlockCoefficient DECIMAL(5,4) NULL,
        WaveAllowance DECIMAL(5,2) NULL,
        HeelAllowance DECIMAL(5,2) NULL,
        NetUKC DECIMAL(5,2) NULL,
        SafetyMargin DECIMAL(5,2) NULL,
        RiskLevel NVARCHAR(20) NULL,
        Recommendation NVARCHAR(500) NULL,
        CalculatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_UKCData PRIMARY KEY CLUSTERED (UKCId),
        CONSTRAINT FK_UKCData_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId)
    );

    CREATE NONCLUSTERED INDEX IX_UKCData_PortCode ON dbo.UKC_DATA(PortCode);
    CREATE NONCLUSTERED INDEX IX_UKCData_VesselType ON dbo.UKC_DATA(VesselType);
    CREATE NONCLUSTERED INDEX IX_UKCData_IsSafe ON dbo.UKC_DATA(IsSafe);
END
GO

-- =============================================
-- SUMMARY
-- =============================================
PRINT '=============================================';
PRINT 'Database schema created successfully!';
PRINT '=============================================';
PRINT 'Tables: 23';
PRINT '  Port Hierarchy: PORTS, TERMINALS, BERTHS';
PRINT '  Core: VESSELS';
PRINT '  Operational: VESSEL_SCHEDULE, RESOURCES, RESOURCE_ALLOCATION';
PRINT '  External Data: WEATHER_DATA, TIDAL_DATA, AIS_DATA';
PRINT '  AI/ML: CONFLICTS, OPTIMIZATION_RUNS, KNOWLEDGE_BASE';
PRINT '  Support: VESSEL_HISTORY, BERTH_MAINTENANCE, ALERTS_NOTIFICATIONS, USER_PREFERENCES, AUDIT_LOG';
PRINT '  Navigation: CHANNELS, ANCHORAGES, PILOTS, TUGBOATS, UKC_DATA';
PRINT '=============================================';
GO
