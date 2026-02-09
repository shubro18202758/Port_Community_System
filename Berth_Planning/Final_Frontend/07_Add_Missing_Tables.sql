-- =============================================
-- BERTH PLANNING - ADD MISSING TABLES
-- Creates CHANNELS, ANCHORAGES, UKC_DATA tables
-- =============================================

USE BerthPlanning;
GO

-- =============================================
-- Table: CHANNELS
-- Purpose: Store navigation channel information
-- =============================================
IF OBJECT_ID('dbo.CHANNELS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.CHANNELS (
        ChannelId INT IDENTITY(1,1) NOT NULL,
        PortId INT NOT NULL,
        ChannelName NVARCHAR(200) NOT NULL,
        ChannelLength DECIMAL(10,2) NULL,           -- km
        ChannelWidth DECIMAL(10,2) NULL,            -- meters
        ChannelDepth DECIMAL(6,2) NULL,             -- meters
        ChannelDepthAtChartDatum DECIMAL(6,2) NULL, -- meters
        OneWayOrTwoWay NVARCHAR(20) NULL,           -- One-Way, Two-Way
        MaxVesselLOA DECIMAL(8,2) NULL,             -- meters
        MaxVesselBeam DECIMAL(6,2) NULL,            -- meters
        MaxVesselDraft DECIMAL(6,2) NULL,           -- meters
        TrafficSeparationScheme BIT NOT NULL DEFAULT 0,
        SpeedLimit INT NULL,                        -- knots
        TidalWindowRequired BIT NOT NULL DEFAULT 0,
        PilotageCompulsory BIT NOT NULL DEFAULT 1,
        TugEscortRequired BIT NOT NULL DEFAULT 0,
        DayNightRestrictions NVARCHAR(100) NULL,
        VisibilityMinimum DECIMAL(5,2) NULL,        -- NM
        WindSpeedLimit INT NULL,                    -- knots
        CurrentSpeedLimit DECIMAL(5,2) NULL,        -- knots
        ChannelSegments NVARCHAR(MAX) NULL,
        AnchorageAreaId INT NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Channels PRIMARY KEY CLUSTERED (ChannelId),
        CONSTRAINT FK_Channels_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId)
    );

    CREATE NONCLUSTERED INDEX IX_Channels_PortId ON dbo.CHANNELS(PortId);
    CREATE NONCLUSTERED INDEX IX_Channels_IsActive ON dbo.CHANNELS(IsActive);
    
    PRINT 'CHANNELS table created successfully.';
END
ELSE
    PRINT 'CHANNELS table already exists.';
GO

-- =============================================
-- Table: ANCHORAGES
-- Purpose: Store anchorage area information
-- =============================================
IF OBJECT_ID('dbo.ANCHORAGES', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ANCHORAGES (
        AnchorageId INT IDENTITY(1,1) NOT NULL,
        PortId INT NOT NULL,
        AnchorageName NVARCHAR(200) NOT NULL,
        AnchorageType NVARCHAR(50) NULL,            -- General, Deep Water, Quarantine
        Latitude DECIMAL(10,7) NULL,
        Longitude DECIMAL(10,7) NULL,
        Depth DECIMAL(6,2) NULL,                    -- meters
        MaxVessels INT NULL,
        CurrentOccupancy INT NOT NULL DEFAULT 0,
        MaxVesselLOA DECIMAL(8,2) NULL,             -- meters
        MaxVesselDraft DECIMAL(6,2) NULL,           -- meters
        AverageWaitingTime DECIMAL(8,2) NULL,       -- hours
        STSCargoOpsPermitted BIT NOT NULL DEFAULT 0,
        QuarantineAnchorage BIT NOT NULL DEFAULT 0,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Anchorages PRIMARY KEY CLUSTERED (AnchorageId),
        CONSTRAINT FK_Anchorages_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId)
    );

    CREATE NONCLUSTERED INDEX IX_Anchorages_PortId ON dbo.ANCHORAGES(PortId);
    CREATE NONCLUSTERED INDEX IX_Anchorages_Type ON dbo.ANCHORAGES(AnchorageType);
    CREATE NONCLUSTERED INDEX IX_Anchorages_IsActive ON dbo.ANCHORAGES(IsActive);
    
    PRINT 'ANCHORAGES table created successfully.';
END
ELSE
    PRINT 'ANCHORAGES table already exists.';
GO

-- =============================================
-- Table: UKC_DATA
-- Purpose: Store Under Keel Clearance calculations
-- =============================================
IF OBJECT_ID('dbo.UKC_DATA', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.UKC_DATA (
        UKCId INT IDENTITY(1,1) NOT NULL,
        PortId INT NOT NULL,
        PortCode NVARCHAR(10) NULL,
        VesselType NVARCHAR(50) NULL,
        VesselLOA DECIMAL(8,2) NULL,
        VesselBeam DECIMAL(6,2) NULL,
        VesselDraft DECIMAL(6,2) NULL,
        GrossTonnage INT NULL,
        ChannelDepth DECIMAL(6,2) NULL,
        TidalHeight DECIMAL(6,2) NULL,
        AvailableDepth DECIMAL(6,2) NULL,
        StaticUKC DECIMAL(6,2) NULL,
        Squat DECIMAL(6,2) NULL,
        DynamicUKC DECIMAL(6,2) NULL,
        UKCPercentage DECIMAL(8,2) NULL,
        RequiredUKCPercentage DECIMAL(8,2) NULL,
        IsSafe BIT NOT NULL DEFAULT 1,
        SpeedKnots DECIMAL(6,2) NULL,
        BlockCoefficient DECIMAL(6,4) NULL,
        WaveAllowance DECIMAL(6,2) NULL,
        HeelAllowance DECIMAL(6,2) NULL,
        NetUKC DECIMAL(6,2) NULL,
        SafetyMargin DECIMAL(6,2) NULL,
        RiskLevel NVARCHAR(50) NULL,                -- Low, Medium, High, Critical
        Recommendation NVARCHAR(500) NULL,
        CalculatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_UKC_DATA PRIMARY KEY CLUSTERED (UKCId),
        CONSTRAINT FK_UKC_DATA_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId)
    );

    CREATE NONCLUSTERED INDEX IX_UKC_DATA_PortId ON dbo.UKC_DATA(PortId);
    CREATE NONCLUSTERED INDEX IX_UKC_DATA_VesselType ON dbo.UKC_DATA(VesselType);
    CREATE NONCLUSTERED INDEX IX_UKC_DATA_IsSafe ON dbo.UKC_DATA(IsSafe);
    CREATE NONCLUSTERED INDEX IX_UKC_DATA_CalculatedAt ON dbo.UKC_DATA(CalculatedAt);
    
    PRINT 'UKC_DATA table created successfully.';
END
ELSE
    PRINT 'UKC_DATA table already exists.';
GO

-- =============================================
-- Table: PILOTS (Separate from Resources for detailed data)
-- Purpose: Store pilot-specific information
-- =============================================
IF OBJECT_ID('dbo.PILOTS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.PILOTS (
        PilotId INT IDENTITY(1,1) NOT NULL,
        PortId INT NOT NULL,
        PilotName NVARCHAR(200) NOT NULL,
        LicenseNumber NVARCHAR(50) NULL,
        LicenseClass NVARCHAR(50) NULL,             -- Class A, B, C
        VesselTypeRestrictions NVARCHAR(200) NULL,
        MaxVesselLOA DECIMAL(8,2) NULL,
        MaxVesselDraft DECIMAL(6,2) NULL,
        MaxVesselGT INT NULL,
        NightPilotage BIT NOT NULL DEFAULT 1,
        DeepDraftCertified BIT NOT NULL DEFAULT 0,
        TankerEndorsement BIT NOT NULL DEFAULT 0,
        LNGEndorsement BIT NOT NULL DEFAULT 0,
        Status NVARCHAR(50) NOT NULL DEFAULT 'Available', -- Available, On Duty, Off Duty, Leave
        ContactNumber NVARCHAR(50) NULL,
        ExperienceYears INT NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Pilots PRIMARY KEY CLUSTERED (PilotId),
        CONSTRAINT FK_Pilots_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId)
    );

    CREATE NONCLUSTERED INDEX IX_Pilots_PortId ON dbo.PILOTS(PortId);
    CREATE NONCLUSTERED INDEX IX_Pilots_Status ON dbo.PILOTS(Status);
    CREATE NONCLUSTERED INDEX IX_Pilots_LicenseClass ON dbo.PILOTS(LicenseClass);
    
    PRINT 'PILOTS table created successfully.';
END
ELSE
    PRINT 'PILOTS table already exists.';
GO

-- =============================================
-- Table: TUGBOATS (Separate from Resources for detailed data)
-- Purpose: Store tugboat-specific information
-- =============================================
IF OBJECT_ID('dbo.TUGBOATS', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.TUGBOATS (
        TugboatId INT IDENTITY(1,1) NOT NULL,
        PortId INT NOT NULL,
        TugboatName NVARCHAR(200) NOT NULL,
        IMO NVARCHAR(20) NULL,
        TugType NVARCHAR(50) NULL,                  -- ASD, Conventional, Voith, Azimuth
        BollardPull DECIMAL(8,2) NULL,              -- tonnes
        EnginePower INT NULL,                       -- kW
        LOA DECIMAL(6,2) NULL,
        Beam DECIMAL(6,2) NULL,
        Draft DECIMAL(6,2) NULL,
        YearBuilt INT NULL,
        FirefightingCapability BIT NOT NULL DEFAULT 0,
        OilSpillResponse BIT NOT NULL DEFAULT 0,
        SalvageCapable BIT NOT NULL DEFAULT 0,
        Status NVARCHAR(50) NOT NULL DEFAULT 'Available', -- Available, On Duty, Maintenance
        CurrentLocation NVARCHAR(200) NULL,
        FuelCapacity DECIMAL(10,2) NULL,
        CrewCapacity INT NULL,
        IsActive BIT NOT NULL DEFAULT 1,
        CreatedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),

        CONSTRAINT PK_Tugboats PRIMARY KEY CLUSTERED (TugboatId),
        CONSTRAINT FK_Tugboats_Ports FOREIGN KEY (PortId) REFERENCES dbo.PORTS(PortId)
    );

    CREATE NONCLUSTERED INDEX IX_Tugboats_PortId ON dbo.TUGBOATS(PortId);
    CREATE NONCLUSTERED INDEX IX_Tugboats_Status ON dbo.TUGBOATS(Status);
    CREATE NONCLUSTERED INDEX IX_Tugboats_TugType ON dbo.TUGBOATS(TugType);
    
    PRINT 'TUGBOATS table created successfully.';
END
ELSE
    PRINT 'TUGBOATS table already exists.';
GO

PRINT '=============================================';
PRINT 'Missing tables creation complete!';
PRINT '=============================================';
GO
