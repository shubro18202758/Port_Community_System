-- =============================================
-- BERTH PLANNING & ALLOCATION OPTIMIZATION SYSTEM
-- MS-SQL Server Database Schema
-- Version: 2.0
-- Date: 2026-01-31
-- =============================================

-- =============================================
-- DROP EXISTING TABLES (IF ANY) - Use with caution!
-- =============================================
/*
IF OBJECT_ID('dbo.AUDIT_LOG', 'U') IS NOT NULL DROP TABLE dbo.AUDIT_LOG;
IF OBJECT_ID('dbo.USER_PREFERENCES', 'U') IS NOT NULL DROP TABLE dbo.USER_PREFERENCES;
IF OBJECT_ID('dbo.ALERTS_NOTIFICATIONS', 'U') IS NOT NULL DROP TABLE dbo.ALERTS_NOTIFICATIONS;
IF OBJECT_ID('dbo.BERTH_MAINTENANCE', 'U') IS NOT NULL DROP TABLE dbo.BERTH_MAINTENANCE;
IF OBJECT_ID('dbo.VESSEL_HISTORY', 'U') IS NOT NULL DROP TABLE dbo.VESSEL_HISTORY;
IF OBJECT_ID('dbo.KNOWLEDGE_BASE', 'U') IS NOT NULL DROP TABLE dbo.KNOWLEDGE_BASE;
IF OBJECT_ID('dbo.OPTIMIZATION_RUNS', 'U') IS NOT NULL DROP TABLE dbo.OPTIMIZATION_RUNS;
IF OBJECT_ID('dbo.CONFLICTS', 'U') IS NOT NULL DROP TABLE dbo.CONFLICTS;
IF OBJECT_ID('dbo.AIS_DATA', 'U') IS NOT NULL DROP TABLE dbo.AIS_DATA;
IF OBJECT_ID('dbo.TIDAL_DATA', 'U') IS NOT NULL DROP TABLE dbo.TIDAL_DATA;
IF OBJECT_ID('dbo.WEATHER_DATA', 'U') IS NOT NULL DROP TABLE dbo.WEATHER_DATA;
IF OBJECT_ID('dbo.RESOURCE_ALLOCATION', 'U') IS NOT NULL DROP TABLE dbo.RESOURCE_ALLOCATION;
IF OBJECT_ID('dbo.RESOURCES', 'U') IS NOT NULL DROP TABLE dbo.RESOURCES;
IF OBJECT_ID('dbo.VESSEL_SCHEDULE', 'U') IS NOT NULL DROP TABLE dbo.VESSEL_SCHEDULE;
IF OBJECT_ID('dbo.BERTHS', 'U') IS NOT NULL DROP TABLE dbo.BERTHS;
IF OBJECT_ID('dbo.TERMINALS', 'U') IS NOT NULL DROP TABLE dbo.TERMINALS;
IF OBJECT_ID('dbo.PORTS', 'U') IS NOT NULL DROP TABLE dbo.PORTS;
IF OBJECT_ID('dbo.VESSELS', 'U') IS NOT NULL DROP TABLE dbo.VESSELS;
*/

-- =============================================
-- TOP-LEVEL ENTITIES (Port Hierarchy)
-- =============================================

-- ---------------------------------------------
-- Table: PORTS
-- Purpose: Store port information (top level of hierarchy)
-- ---------------------------------------------
CREATE TABLE dbo.PORTS (
    PortId INT IDENTITY(1,1) NOT NULL,
    PortName NVARCHAR(200) NOT NULL,
    PortCode NVARCHAR(10) NOT NULL,  -- UN/LOCODE e.g., INMUN, INBOM
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

-- Create indexes
CREATE NONCLUSTERED INDEX IX_Ports_Country ON dbo.PORTS(Country);
CREATE NONCLUSTERED INDEX IX_Ports_IsActive ON dbo.PORTS(IsActive);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Stores port master data - top level of port hierarchy (Port -> Terminal -> Berth)',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'PORTS';
GO

-- ---------------------------------------------
-- Table: TERMINALS
-- Purpose: Store terminal information (linked to Ports)
-- ---------------------------------------------
CREATE TABLE dbo.TERMINALS (
    TerminalId INT IDENTITY(1,1) NOT NULL,
    PortId INT NOT NULL,
    TerminalName NVARCHAR(200) NOT NULL,
    TerminalCode NVARCHAR(20) NOT NULL,
    TerminalType NVARCHAR(50) NULL,  -- Container, Bulk, Liquid, General
    OperatorName NVARCHAR(200) NULL,
    Latitude DECIMAL(10,7) NULL,
    Longitude DECIMAL(10,7) NULL,
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_Terminals PRIMARY KEY CLUSTERED (TerminalId),
    CONSTRAINT UQ_Terminals_TerminalCode UNIQUE (TerminalCode),
    CONSTRAINT FK_Terminals_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_Terminals_PortId ON dbo.TERMINALS(PortId);
CREATE NONCLUSTERED INDEX IX_Terminals_TerminalType ON dbo.TERMINALS(TerminalType);
CREATE NONCLUSTERED INDEX IX_Terminals_IsActive ON dbo.TERMINALS(IsActive);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Stores terminal information - middle level of port hierarchy (Port -> Terminal -> Berth)',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'TERMINALS';
GO

-- =============================================
-- CORE ENTITIES
-- =============================================

-- ---------------------------------------------
-- Table: VESSELS
-- Purpose: Store vessel (ship) information
-- ---------------------------------------------
CREATE TABLE dbo.VESSELS (
    VesselId INT IDENTITY(1,1) NOT NULL,
    VesselName NVARCHAR(200) NOT NULL,
    IMO NVARCHAR(20) NULL,
    MMSI NVARCHAR(20) NULL,
    VesselType NVARCHAR(50) NULL, -- Container, Bulk, Tanker, RoRo, General
    LOA DECIMAL(8,2) NULL, -- Length Overall in meters
    Beam DECIMAL(6,2) NULL, -- Width in meters
    Draft DECIMAL(6,2) NULL, -- Draft in meters
    GrossTonnage INT NULL,
    CargoType NVARCHAR(100) NULL,
    CargoVolume DECIMAL(12,2) NULL,
    Priority INT NOT NULL DEFAULT 2, -- 1=High, 2=Medium, 3=Low
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_Vessels PRIMARY KEY CLUSTERED (VesselId),
    CONSTRAINT UQ_Vessels_IMO UNIQUE (IMO),
    CONSTRAINT CK_Vessels_Priority CHECK (Priority BETWEEN 1 AND 3),
    CONSTRAINT CK_Vessels_LOA CHECK (LOA > 0),
    CONSTRAINT CK_Vessels_Beam CHECK (Beam > 0),
    CONSTRAINT CK_Vessels_Draft CHECK (Draft > 0)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_Vessels_VesselType ON dbo.VESSELS(VesselType);
CREATE NONCLUSTERED INDEX IX_Vessels_Priority ON dbo.VESSELS(Priority);
CREATE NONCLUSTERED INDEX IX_Vessels_MMSI ON dbo.VESSELS(MMSI);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Stores vessel (ship) master data including physical dimensions and characteristics',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'VESSELS';
GO

-- ---------------------------------------------
-- Table: BERTHS
-- Purpose: Store berth (docking location) information
-- Linked to Terminals (bottom level of hierarchy)
-- ---------------------------------------------
CREATE TABLE dbo.BERTHS (
    BerthId INT IDENTITY(1,1) NOT NULL,
    TerminalId INT NULL, -- Links to Terminal (nullable for backwards compatibility)
    BerthName NVARCHAR(100) NOT NULL,
    BerthCode NVARCHAR(20) NOT NULL,
    Length DECIMAL(8,2) NOT NULL, -- Maximum vessel length in meters
    Depth DECIMAL(6,2) NOT NULL, -- Water depth in meters at high tide
    MaxDraft DECIMAL(6,2) NOT NULL, -- Maximum vessel draft allowed
    BerthType NVARCHAR(50) NULL, -- Container, Bulk, General, Tanker
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
    CONSTRAINT CK_Berths_Length CHECK (Length > 0),
    CONSTRAINT CK_Berths_Depth CHECK (Depth > 0),
    CONSTRAINT CK_Berths_MaxDraft CHECK (MaxDraft > 0)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_Berths_TerminalId ON dbo.BERTHS(TerminalId);
CREATE NONCLUSTERED INDEX IX_Berths_BerthType ON dbo.BERTHS(BerthType);
CREATE NONCLUSTERED INDEX IX_Berths_IsActive ON dbo.BERTHS(IsActive);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Stores berth (docking location) information - bottom level of port hierarchy (Port -> Terminal -> Berth)',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'BERTHS';
GO

-- =============================================
-- OPERATIONAL DATA ENTITIES
-- =============================================

-- ---------------------------------------------
-- Table: VESSEL_SCHEDULE
-- Purpose: Central scheduling table linking vessels to berths
-- ---------------------------------------------
CREATE TABLE dbo.VESSEL_SCHEDULE (
    ScheduleId INT IDENTITY(1,1) NOT NULL,
    VesselId INT NOT NULL,
    BerthId INT NULL, -- Nullable until berth assigned

    -- Estimated Times
    ETA DATETIME2 NULL, -- Estimated Time of Arrival (original)
    PredictedETA DATETIME2 NULL, -- AI-predicted ETA
    ETD DATETIME2 NULL, -- Estimated Time of Departure

    -- Actual Times
    ATA DATETIME2 NULL, -- Actual Time of Arrival
    ATB DATETIME2 NULL, -- Actual Time of Berthing
    ATD DATETIME2 NULL, -- Actual Time of Departure

    -- Status and Metrics
    Status NVARCHAR(50) NOT NULL DEFAULT 'Scheduled', -- Scheduled, Approaching, Berthed, Departed, Cancelled
    DwellTime INT NULL, -- Expected time at berth in minutes
    WaitingTime INT NULL, -- Actual waiting time in minutes

    -- Optimization Metadata
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

-- Create indexes for performance
CREATE NONCLUSTERED INDEX IX_VesselSchedule_VesselId ON dbo.VESSEL_SCHEDULE(VesselId);
CREATE NONCLUSTERED INDEX IX_VesselSchedule_BerthId ON dbo.VESSEL_SCHEDULE(BerthId);
CREATE NONCLUSTERED INDEX IX_VesselSchedule_Status ON dbo.VESSEL_SCHEDULE(Status);
CREATE NONCLUSTERED INDEX IX_VesselSchedule_ETA ON dbo.VESSEL_SCHEDULE(ETA);
CREATE NONCLUSTERED INDEX IX_VesselSchedule_BerthId_ETA ON dbo.VESSEL_SCHEDULE(BerthId, ETA) INCLUDE (ETD, Status);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Central scheduling table linking vessels to berths with timing and optimization metadata',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'VESSEL_SCHEDULE';
GO

-- ---------------------------------------------
-- Table: RESOURCES
-- Purpose: Master data for port resources
-- ---------------------------------------------
CREATE TABLE dbo.RESOURCES (
    ResourceId INT IDENTITY(1,1) NOT NULL,
    ResourceType NVARCHAR(50) NOT NULL, -- Crane, Tugboat, Pilot, Labor
    ResourceName NVARCHAR(100) NOT NULL,
    Capacity INT NOT NULL DEFAULT 1,
    IsAvailable BIT NOT NULL DEFAULT 1,
    MaintenanceSchedule DATETIME2 NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_Resources PRIMARY KEY CLUSTERED (ResourceId),
    CONSTRAINT CK_Resources_Type CHECK (ResourceType IN ('Crane', 'Tugboat', 'Pilot', 'Labor', 'Other')),
    CONSTRAINT CK_Resources_Capacity CHECK (Capacity > 0)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_Resources_Type ON dbo.RESOURCES(ResourceType);
CREATE NONCLUSTERED INDEX IX_Resources_IsAvailable ON dbo.RESOURCES(IsAvailable);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Master data for port resources including cranes, tugboats, pilots, and labor',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'RESOURCES';
GO

-- ---------------------------------------------
-- Table: RESOURCE_ALLOCATION
-- Purpose: Track resource assignments to vessels
-- ---------------------------------------------
CREATE TABLE dbo.RESOURCE_ALLOCATION (
    AllocationId INT IDENTITY(1,1) NOT NULL,
    ScheduleId INT NOT NULL,
    ResourceId INT NOT NULL,
    AllocatedFrom DATETIME2 NOT NULL,
    AllocatedTo DATETIME2 NOT NULL,
    Quantity INT NOT NULL DEFAULT 1,
    Status NVARCHAR(50) NOT NULL DEFAULT 'Allocated', -- Allocated, InUse, Released
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_ResourceAllocation PRIMARY KEY CLUSTERED (AllocationId),
    CONSTRAINT FK_ResourceAllocation_Schedule FOREIGN KEY (ScheduleId) REFERENCES dbo.VESSEL_SCHEDULE(ScheduleId),
    CONSTRAINT FK_ResourceAllocation_Resources FOREIGN KEY (ResourceId) REFERENCES dbo.RESOURCES(ResourceId),
    CONSTRAINT CK_ResourceAllocation_Status CHECK (Status IN ('Allocated', 'InUse', 'Released')),
    CONSTRAINT CK_ResourceAllocation_Quantity CHECK (Quantity > 0),
    CONSTRAINT CK_ResourceAllocation_TimeRange CHECK (AllocatedFrom < AllocatedTo)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_ResourceAllocation_ScheduleId ON dbo.RESOURCE_ALLOCATION(ScheduleId);
CREATE NONCLUSTERED INDEX IX_ResourceAllocation_ResourceId ON dbo.RESOURCE_ALLOCATION(ResourceId);
CREATE NONCLUSTERED INDEX IX_ResourceAllocation_TimeRange ON dbo.RESOURCE_ALLOCATION(ResourceId, AllocatedFrom, AllocatedTo);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Tracks allocation of resources to vessel schedules',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'RESOURCE_ALLOCATION';
GO

-- =============================================
-- EXTERNAL DATA ENTITIES
-- =============================================

-- ---------------------------------------------
-- Table: WEATHER_DATA
-- Purpose: Store weather data from external APIs
-- ---------------------------------------------
CREATE TABLE dbo.WEATHER_DATA (
    WeatherId INT IDENTITY(1,1) NOT NULL,
    RecordedAt DATETIME2 NOT NULL,
    WindSpeed DECIMAL(5,2) NULL, -- km/h
    WindDirection INT NULL, -- degrees 0-360
    Visibility INT NULL, -- meters
    WaveHeight DECIMAL(4,2) NULL, -- meters
    Temperature DECIMAL(5,2) NULL, -- Celsius
    Precipitation DECIMAL(5,2) NULL, -- mm
    WeatherCondition NVARCHAR(100) NULL, -- Clear, Rain, Storm, Fog, etc.
    IsAlert BIT NOT NULL DEFAULT 0,
    FetchedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_WeatherData PRIMARY KEY CLUSTERED (WeatherId),
    CONSTRAINT CK_WeatherData_WindDirection CHECK (WindDirection BETWEEN 0 AND 360)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_WeatherData_RecordedAt ON dbo.WEATHER_DATA(RecordedAt DESC);
CREATE NONCLUSTERED INDEX IX_WeatherData_IsAlert ON dbo.WEATHER_DATA(IsAlert) WHERE IsAlert = 1;
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Weather data from external APIs (OpenWeatherMap, NOAA)',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'WEATHER_DATA';
GO

-- ---------------------------------------------
-- Table: TIDAL_DATA
-- Purpose: Store tidal schedule data
-- ---------------------------------------------
CREATE TABLE dbo.TIDAL_DATA (
    TidalId INT IDENTITY(1,1) NOT NULL,
    TideTime DATETIME2 NOT NULL,
    TideType NVARCHAR(20) NOT NULL, -- HighTide, LowTide
    Height DECIMAL(5,2) NOT NULL, -- meters
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_TidalData PRIMARY KEY CLUSTERED (TidalId),
    CONSTRAINT CK_TidalData_Type CHECK (TideType IN ('HighTide', 'LowTide'))
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_TidalData_TideTime ON dbo.TIDAL_DATA(TideTime);
CREATE NONCLUSTERED INDEX IX_TidalData_TideType ON dbo.TIDAL_DATA(TideType);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Tidal schedule data from NOAA/WorldTides APIs',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'TIDAL_DATA';
GO

-- ---------------------------------------------
-- Table: AIS_DATA
-- Purpose: Store AIS vessel tracking data
-- ---------------------------------------------
CREATE TABLE dbo.AIS_DATA (
    AISId INT IDENTITY(1,1) NOT NULL,
    VesselId INT NOT NULL,
    MMSI NVARCHAR(20) NULL,
    Latitude DECIMAL(10,7) NOT NULL,
    Longitude DECIMAL(10,7) NOT NULL,
    Speed DECIMAL(5,2) NULL, -- knots
    Course DECIMAL(5,2) NULL, -- degrees
    Heading DECIMAL(5,2) NULL, -- degrees
    NavigationStatus NVARCHAR(50) NULL,
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

-- Create indexes
CREATE NONCLUSTERED INDEX IX_AISData_VesselId_RecordedAt ON dbo.AIS_DATA(VesselId, RecordedAt DESC);
CREATE NONCLUSTERED INDEX IX_AISData_MMSI ON dbo.AIS_DATA(MMSI);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'AIS (Automatic Identification System) vessel tracking data',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'AIS_DATA';
GO

-- =============================================
-- AI/ML ENTITIES
-- =============================================

-- ---------------------------------------------
-- Table: CONFLICTS
-- Purpose: Track scheduling conflicts
-- ---------------------------------------------
CREATE TABLE dbo.CONFLICTS (
    ConflictId INT IDENTITY(1,1) NOT NULL,
    ConflictType NVARCHAR(50) NOT NULL, -- BerthOverlap, ResourceUnavailable, TidalConstraint, PriorityViolation
    ScheduleId1 INT NOT NULL,
    ScheduleId2 INT NULL, -- Null for single-schedule conflicts
    Description NVARCHAR(500) NULL,
    Severity INT NOT NULL DEFAULT 2, -- 1=Critical, 2=High, 3=Medium, 4=Low
    Status NVARCHAR(50) NOT NULL DEFAULT 'Detected', -- Detected, Resolved, Ignored
    DetectedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    ResolvedAt DATETIME2 NULL,
    Resolution NVARCHAR(MAX) NULL, -- JSON describing resolution

    CONSTRAINT PK_Conflicts PRIMARY KEY CLUSTERED (ConflictId),
    CONSTRAINT FK_Conflicts_Schedule1 FOREIGN KEY (ScheduleId1) REFERENCES dbo.VESSEL_SCHEDULE(ScheduleId),
    CONSTRAINT FK_Conflicts_Schedule2 FOREIGN KEY (ScheduleId2) REFERENCES dbo.VESSEL_SCHEDULE(ScheduleId),
    CONSTRAINT CK_Conflicts_Type CHECK (ConflictType IN ('BerthOverlap', 'ResourceUnavailable', 'TidalConstraint', 'PriorityViolation')),
    CONSTRAINT CK_Conflicts_Severity CHECK (Severity BETWEEN 1 AND 4),
    CONSTRAINT CK_Conflicts_Status CHECK (Status IN ('Detected', 'Resolved', 'Ignored'))
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_Conflicts_Status ON dbo.CONFLICTS(Status);
CREATE NONCLUSTERED INDEX IX_Conflicts_ScheduleId1 ON dbo.CONFLICTS(ScheduleId1);
CREATE NONCLUSTERED INDEX IX_Conflicts_ScheduleId2 ON dbo.CONFLICTS(ScheduleId2);
CREATE NONCLUSTERED INDEX IX_Conflicts_DetectedAt ON dbo.CONFLICTS(DetectedAt DESC);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Tracks scheduling conflicts detected by the Conflict Resolver Agent',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'CONFLICTS';
GO

-- ---------------------------------------------
-- Table: OPTIMIZATION_RUNS
-- Purpose: Log AI optimization executions
-- ---------------------------------------------
CREATE TABLE dbo.OPTIMIZATION_RUNS (
    RunId INT IDENTITY(1,1) NOT NULL,
    RunType NVARCHAR(50) NOT NULL, -- Initial, ReOptimization, ConflictResolution
    Algorithm NVARCHAR(100) NULL, -- GeneticAlgorithm, ReinforcementLearning, Greedy
    InputParameters NVARCHAR(MAX) NULL, -- JSON
    OutputResults NVARCHAR(MAX) NULL, -- JSON
    ExecutionTime INT NULL, -- milliseconds
    ImprovementScore DECIMAL(5,2) NULL, -- percentage improvement
    Status NVARCHAR(50) NOT NULL DEFAULT 'Running', -- Running, Completed, Failed
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    CompletedAt DATETIME2 NULL,

    CONSTRAINT PK_OptimizationRuns PRIMARY KEY CLUSTERED (RunId),
    CONSTRAINT CK_OptimizationRuns_Type CHECK (RunType IN ('Initial', 'ReOptimization', 'ConflictResolution')),
    CONSTRAINT CK_OptimizationRuns_Status CHECK (Status IN ('Running', 'Completed', 'Failed')),
    CONSTRAINT CK_OptimizationRuns_ExecutionTime CHECK (ExecutionTime >= 0)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_OptimizationRuns_CreatedAt ON dbo.OPTIMIZATION_RUNS(CreatedAt DESC);
CREATE NONCLUSTERED INDEX IX_OptimizationRuns_Status ON dbo.OPTIMIZATION_RUNS(Status);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Logs all optimization runs for performance tracking and analysis',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'OPTIMIZATION_RUNS';
GO

-- ---------------------------------------------
-- Table: KNOWLEDGE_BASE
-- Purpose: Store documents for RAG system
-- ---------------------------------------------
CREATE TABLE dbo.KNOWLEDGE_BASE (
    KnowledgeId INT IDENTITY(1,1) NOT NULL,
    DocumentType NVARCHAR(100) NULL, -- HistoricalLog, PortManual, BestPractice, WeatherPattern
    Title NVARCHAR(500) NOT NULL,
    Content NVARCHAR(MAX) NOT NULL,
    Embedding VARBINARY(MAX) NULL, -- Vector embedding for similarity search
    Metadata NVARCHAR(MAX) NULL, -- JSON
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_KnowledgeBase PRIMARY KEY CLUSTERED (KnowledgeId)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_KnowledgeBase_DocumentType ON dbo.KNOWLEDGE_BASE(DocumentType);
CREATE NONCLUSTERED INDEX IX_KnowledgeBase_CreatedAt ON dbo.KNOWLEDGE_BASE(CreatedAt DESC);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Knowledge base for RAG (Retrieval Augmented Generation) system',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'KNOWLEDGE_BASE';
GO

-- =============================================
-- SUPPORT TABLES
-- =============================================

-- ---------------------------------------------
-- Table: VESSEL_HISTORY
-- Purpose: Track historical vessel visits
-- ---------------------------------------------
CREATE TABLE dbo.VESSEL_HISTORY (
    HistoryId INT IDENTITY(1,1) NOT NULL,
    VesselId INT NOT NULL,
    BerthId INT NOT NULL,
    VisitDate DATETIME2 NOT NULL,
    ActualDwellTime INT NULL, -- minutes
    ActualWaitingTime INT NULL, -- minutes
    ETAAccuracy DECIMAL(5,2) NULL, -- percentage
    Notes NVARCHAR(500) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_VesselHistory PRIMARY KEY CLUSTERED (HistoryId),
    CONSTRAINT FK_VesselHistory_Vessels FOREIGN KEY (VesselId) REFERENCES dbo.VESSELS(VesselId),
    CONSTRAINT FK_VesselHistory_Berths FOREIGN KEY (BerthId) REFERENCES dbo.BERTHS(BerthId),
    CONSTRAINT CK_VesselHistory_DwellTime CHECK (ActualDwellTime > 0),
    CONSTRAINT CK_VesselHistory_WaitingTime CHECK (ActualWaitingTime >= 0)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_VesselHistory_VesselId ON dbo.VESSEL_HISTORY(VesselId);
CREATE NONCLUSTERED INDEX IX_VesselHistory_BerthId ON dbo.VESSEL_HISTORY(BerthId);
CREATE NONCLUSTERED INDEX IX_VesselHistory_VisitDate ON dbo.VESSEL_HISTORY(VisitDate DESC);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Historical record of vessel visits for pattern analysis and ML training',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'VESSEL_HISTORY';
GO

-- ---------------------------------------------
-- Table: BERTH_MAINTENANCE
-- Purpose: Track berth maintenance schedules
-- ---------------------------------------------
CREATE TABLE dbo.BERTH_MAINTENANCE (
    MaintenanceId INT IDENTITY(1,1) NOT NULL,
    BerthId INT NOT NULL,
    StartTime DATETIME2 NOT NULL,
    EndTime DATETIME2 NOT NULL,
    MaintenanceType NVARCHAR(50) NULL, -- Routine, Emergency, CraneRepair, StructuralRepair
    Status NVARCHAR(50) NOT NULL DEFAULT 'Scheduled', -- Scheduled, InProgress, Completed, Cancelled
    Description NVARCHAR(500) NULL,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_BerthMaintenance PRIMARY KEY CLUSTERED (MaintenanceId),
    CONSTRAINT FK_BerthMaintenance_Berths FOREIGN KEY (BerthId) REFERENCES dbo.BERTHS(BerthId),
    CONSTRAINT CK_BerthMaintenance_Status CHECK (Status IN ('Scheduled', 'InProgress', 'Completed', 'Cancelled')),
    CONSTRAINT CK_BerthMaintenance_TimeRange CHECK (StartTime < EndTime)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_BerthMaintenance_BerthId ON dbo.BERTH_MAINTENANCE(BerthId);
CREATE NONCLUSTERED INDEX IX_BerthMaintenance_Status ON dbo.BERTH_MAINTENANCE(Status);
CREATE NONCLUSTERED INDEX IX_BerthMaintenance_TimeRange ON dbo.BERTH_MAINTENANCE(BerthId, StartTime, EndTime);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Berth maintenance schedules to block berth availability',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'BERTH_MAINTENANCE';
GO

-- ---------------------------------------------
-- Table: ALERTS_NOTIFICATIONS
-- Purpose: System alerts and notifications
-- ---------------------------------------------
CREATE TABLE dbo.ALERTS_NOTIFICATIONS (
    AlertId INT IDENTITY(1,1) NOT NULL,
    AlertType NVARCHAR(50) NOT NULL, -- ConflictDetected, WeatherWarning, DelayAlert, ResourceShortage
    RelatedEntityId INT NULL,
    EntityType NVARCHAR(50) NULL, -- Vessel, Berth, Schedule, Resource
    Severity NVARCHAR(20) NOT NULL DEFAULT 'Medium', -- Critical, High, Medium, Low
    Message NVARCHAR(500) NOT NULL,
    IsRead BIT NOT NULL DEFAULT 0,
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
    ReadAt DATETIME2 NULL,

    CONSTRAINT PK_AlertsNotifications PRIMARY KEY CLUSTERED (AlertId),
    CONSTRAINT CK_AlertsNotifications_Severity CHECK (Severity IN ('Critical', 'High', 'Medium', 'Low'))
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_AlertsNotifications_IsRead ON dbo.ALERTS_NOTIFICATIONS(IsRead) WHERE IsRead = 0;
CREATE NONCLUSTERED INDEX IX_AlertsNotifications_CreatedAt ON dbo.ALERTS_NOTIFICATIONS(CreatedAt DESC);
CREATE NONCLUSTERED INDEX IX_AlertsNotifications_Severity ON dbo.ALERTS_NOTIFICATIONS(Severity);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'System alerts and user notifications',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'ALERTS_NOTIFICATIONS';
GO

-- ---------------------------------------------
-- Table: USER_PREFERENCES
-- Purpose: Store user settings
-- ---------------------------------------------
CREATE TABLE dbo.USER_PREFERENCES (
    PreferenceId INT IDENTITY(1,1) NOT NULL,
    UserId NVARCHAR(100) NOT NULL,
    PreferenceKey NVARCHAR(100) NOT NULL,
    PreferenceValue NVARCHAR(MAX) NULL, -- JSON or simple value
    UpdatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_UserPreferences PRIMARY KEY CLUSTERED (PreferenceId),
    CONSTRAINT UQ_UserPreferences_UserKey UNIQUE (UserId, PreferenceKey)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_UserPreferences_UserId ON dbo.USER_PREFERENCES(UserId);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'User-specific preferences and settings',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'USER_PREFERENCES';
GO

-- ---------------------------------------------
-- Table: AUDIT_LOG
-- Purpose: Complete audit trail
-- ---------------------------------------------
CREATE TABLE dbo.AUDIT_LOG (
    LogId BIGINT IDENTITY(1,1) NOT NULL,
    UserId NVARCHAR(100) NULL,
    Action NVARCHAR(50) NOT NULL, -- Created, Updated, Deleted, Optimized
    EntityType NVARCHAR(50) NOT NULL,
    EntityId INT NOT NULL,
    OldValue NVARCHAR(MAX) NULL, -- JSON
    NewValue NVARCHAR(MAX) NULL, -- JSON
    CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

    CONSTRAINT PK_AuditLog PRIMARY KEY CLUSTERED (LogId)
);

-- Create indexes
CREATE NONCLUSTERED INDEX IX_AuditLog_EntityType_EntityId ON dbo.AUDIT_LOG(EntityType, EntityId);
CREATE NONCLUSTERED INDEX IX_AuditLog_CreatedAt ON dbo.AUDIT_LOG(CreatedAt DESC);
CREATE NONCLUSTERED INDEX IX_AuditLog_UserId ON dbo.AUDIT_LOG(UserId);
GO

EXEC sys.sp_addextendedproperty
    @name=N'MS_Description',
    @value=N'Complete audit trail of all system changes for compliance and debugging',
    @level0type=N'SCHEMA', @level0name=N'dbo',
    @level1type=N'TABLE', @level1name=N'AUDIT_LOG';
GO

-- =============================================
-- SUMMARY
-- =============================================
PRINT '=============================================';
PRINT 'Database schema created successfully!';
PRINT '=============================================';
PRINT 'Tables created: 18';
PRINT '  - Port Hierarchy: 3 (PORTS, TERMINALS, BERTHS)';
PRINT '  - Core Entities: 1 (VESSELS)';
PRINT '  - Operational: 3 (VESSEL_SCHEDULE, RESOURCES, RESOURCE_ALLOCATION)';
PRINT '  - External Data: 3 (WEATHER_DATA, TIDAL_DATA, AIS_DATA)';
PRINT '  - AI/ML: 3 (CONFLICTS, OPTIMIZATION_RUNS, KNOWLEDGE_BASE)';
PRINT '  - Support: 5 (VESSEL_HISTORY, BERTH_MAINTENANCE, ALERTS_NOTIFICATIONS, USER_PREFERENCES, AUDIT_LOG)';
PRINT '=============================================';
PRINT 'Next Steps:';
PRINT '  1. Review table structures';
PRINT '  2. Run sample data insert script (02_Insert_Sample_Data.sql)';
PRINT '  3. Create views (03_Create_Views.sql)';
PRINT '  4. Create stored procedures (04_Create_StoredProcedures.sql)';
PRINT '=============================================';
GO
