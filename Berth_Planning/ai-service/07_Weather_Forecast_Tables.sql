-- =============================================
-- WEATHER FORECAST TABLES
-- Real-time weather data integration for ETA prediction
-- Supports port weather + 5-waypoint route weather
-- Version: 1.0
-- Date: 2026-02-05
-- =============================================

USE [BerthPlanning];
GO

-- =============================================
-- WEATHER_FORECAST Table
-- Stores weather forecasts for port locations and vessel route waypoints
-- Updated hourly via WeatherAPI.com integration
-- =============================================
IF OBJECT_ID('dbo.WEATHER_FORECAST', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.WEATHER_FORECAST (
        ForecastId BIGINT IDENTITY(1,1) NOT NULL,

        -- Location Information
        LocationType NVARCHAR(20) NOT NULL,         -- 'PORT', 'WAYPOINT'
        LocationId INT NULL,                        -- PortId if LocationType='PORT'
        LocationName NVARCHAR(100) NULL,            -- Waypoint_1, Waypoint_2, etc.
        Latitude DECIMAL(10,7) NOT NULL,
        Longitude DECIMAL(10,7) NOT NULL,

        -- Vessel/Schedule Association
        VesselId INT NULL,
        ScheduleId INT NULL,
        WaypointSequence INT NULL,                  -- 1-5 for route waypoints, NULL for port

        -- Temporal Information
        ForecastFor DATETIME2 NOT NULL,             -- Target datetime for this forecast
        FetchedAt DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        ExpiresAt DATETIME2 NOT NULL,               -- Cache expiry (typically +1 hour from FetchedAt)

        -- Weather Parameters
        WindSpeed DECIMAL(5,2) NULL,                -- knots
        WindDirection INT NULL,                     -- degrees (0-360)
        WindGust DECIMAL(5,2) NULL,                 -- knots
        Visibility DECIMAL(5,2) NULL,               -- nautical miles
        WaveHeight DECIMAL(4,2) NULL,               -- meters
        Temperature DECIMAL(5,2) NULL,              -- Celsius
        Precipitation DECIMAL(5,2) NULL,            -- mm/hour
        WeatherCondition NVARCHAR(100) NULL,        -- 'Clear', 'Cloudy', 'Rain', 'Storm', etc.

        -- Computed Impact Metrics
        WeatherImpactFactor DECIMAL(5,4) NULL,      -- 0.5-1.0 speed multiplier for ETA calculation
        IsOperationalAlert BIT NOT NULL DEFAULT 0,  -- TRUE if conditions exceed safety thresholds
        AlertLevel NVARCHAR(20) NULL,               -- 'NORMAL', 'WARNING', 'CRITICAL'

        -- Status
        IsActive BIT NOT NULL DEFAULT 1,

        CONSTRAINT PK_WeatherForecast PRIMARY KEY CLUSTERED (ForecastId),
        CONSTRAINT FK_WeatherForecast_Vessels FOREIGN KEY (VesselId) REFERENCES dbo.VESSELS(VesselId) ON DELETE CASCADE,
        CONSTRAINT FK_WeatherForecast_Schedule FOREIGN KEY (ScheduleId) REFERENCES dbo.VESSEL_SCHEDULE(ScheduleId) ON DELETE CASCADE,
        CONSTRAINT CK_WeatherForecast_LocationType CHECK (LocationType IN ('PORT', 'WAYPOINT')),
        CONSTRAINT CK_WeatherForecast_AlertLevel CHECK (AlertLevel IN ('NORMAL', 'WARNING', 'CRITICAL') OR AlertLevel IS NULL),
        CONSTRAINT CK_WeatherForecast_ImpactFactor CHECK (WeatherImpactFactor BETWEEN 0.5 AND 1.0 OR WeatherImpactFactor IS NULL)
    );

    -- Indexes for performance
    CREATE NONCLUSTERED INDEX IX_WeatherForecast_VesselSchedule
        ON dbo.WEATHER_FORECAST(VesselId, ScheduleId)
        INCLUDE (WeatherImpactFactor, AlertLevel);

    CREATE NONCLUSTERED INDEX IX_WeatherForecast_Location
        ON dbo.WEATHER_FORECAST(Latitude, Longitude, FetchedAt)
        WHERE IsActive = 1;

    CREATE NONCLUSTERED INDEX IX_WeatherForecast_Expiry
        ON dbo.WEATHER_FORECAST(ExpiresAt)
        WHERE IsActive = 1;

    CREATE NONCLUSTERED INDEX IX_WeatherForecast_ForecastFor
        ON dbo.WEATHER_FORECAST(ForecastFor, LocationType);

    PRINT 'WEATHER_FORECAST table created successfully';
END
ELSE
BEGIN
    PRINT 'WEATHER_FORECAST table already exists';
END
GO

-- =============================================
-- WEATHER_API_USAGE Table
-- Tracks API calls for monitoring and cost management
-- =============================================
IF OBJECT_ID('dbo.WEATHER_API_USAGE', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.WEATHER_API_USAGE (
        UsageId BIGINT IDENTITY(1,1) NOT NULL,
        CallTimestamp DATETIME2 NOT NULL DEFAULT GETUTCDATE(),
        ApiProvider NVARCHAR(50) NOT NULL,          -- 'WeatherAPI', 'OpenWeatherMap', etc.
        Latitude DECIMAL(10,7) NOT NULL,
        Longitude DECIMAL(10,7) NOT NULL,
        ResponseStatus INT NULL,                    -- HTTP status code (200, 404, 500, etc.)
        CacheHit BIT NOT NULL DEFAULT 0,            -- TRUE if data returned from cache
        ErrorMessage NVARCHAR(500) NULL,

        CONSTRAINT PK_WeatherApiUsage PRIMARY KEY CLUSTERED (UsageId)
    );

    -- Index for daily usage reports
    CREATE NONCLUSTERED INDEX IX_WeatherApiUsage_Timestamp
        ON dbo.WEATHER_API_USAGE(CallTimestamp DESC)
        INCLUDE (ApiProvider, CacheHit);

    CREATE NONCLUSTERED INDEX IX_WeatherApiUsage_Provider
        ON dbo.WEATHER_API_USAGE(ApiProvider, CallTimestamp);

    PRINT 'WEATHER_API_USAGE table created successfully';
END
ELSE
BEGIN
    PRINT 'WEATHER_API_USAGE table already exists';
END
GO

-- =============================================
-- Add columns to VESSEL_SCHEDULE for agent predictions
-- =============================================
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.VESSEL_SCHEDULE') AND name = 'AgentPredictedETA')
BEGIN
    ALTER TABLE dbo.VESSEL_SCHEDULE ADD AgentPredictedETA DATETIME2 NULL;
    PRINT 'Added AgentPredictedETA column to VESSEL_SCHEDULE';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.VESSEL_SCHEDULE') AND name = 'AgentConfidence')
BEGIN
    ALTER TABLE dbo.VESSEL_SCHEDULE ADD AgentConfidence DECIMAL(5,2) NULL;
    PRINT 'Added AgentConfidence column to VESSEL_SCHEDULE';
END

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('dbo.VESSEL_SCHEDULE') AND name = 'WeatherImpactReasoning')
BEGIN
    ALTER TABLE dbo.VESSEL_SCHEDULE ADD WeatherImpactReasoning NVARCHAR(MAX) NULL;
    PRINT 'Added WeatherImpactReasoning column to VESSEL_SCHEDULE';
END
GO

-- =============================================
-- Stored Procedure: Get Active Vessels for Weather Updates
-- =============================================
IF OBJECT_ID('dbo.usp_GetActiveVesselsForWeatherUpdate', 'P') IS NOT NULL
    DROP PROCEDURE dbo.usp_GetActiveVesselsForWeatherUpdate;
GO

CREATE PROCEDURE dbo.usp_GetActiveVesselsForWeatherUpdate
AS
BEGIN
    SET NOCOUNT ON;

    SELECT
        vs.ScheduleId,
        vs.VesselId,
        v.VesselName,
        vs.ETA AS OriginalETA,
        p.PortId,
        p.PortCode,
        p.Latitude AS PortLatitude,
        p.Longitude AS PortLongitude,
        ais.Latitude AS CurrentLatitude,
        ais.Longitude AS CurrentLongitude,
        ais.Speed AS CurrentSpeed,
        ais.Heading AS CurrentHeading,
        vs.Status
    FROM dbo.VESSEL_SCHEDULE vs
    INNER JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
    INNER JOIN dbo.BERTHS b ON vs.BerthId = b.BerthId
    INNER JOIN dbo.TERMINALS t ON b.TerminalId = t.TerminalId
    INNER JOIN dbo.PORTS p ON t.PortId = p.PortId
    OUTER APPLY (
        SELECT TOP 1 a.Latitude, a.Longitude, a.Speed, a.Heading
        FROM dbo.AIS_DATA a
        WHERE a.VesselId = vs.VesselId
        ORDER BY a.RecordedAt DESC
    ) ais
    WHERE vs.Status IN ('Scheduled', 'Approaching')
    ORDER BY vs.ETA;
END
GO

-- =============================================
-- Stored Procedure: Cleanup Expired Weather Forecasts
-- =============================================
IF OBJECT_ID('dbo.usp_CleanupExpiredWeatherForecasts', 'P') IS NOT NULL
    DROP PROCEDURE dbo.usp_CleanupExpiredWeatherForecasts;
GO

CREATE PROCEDURE dbo.usp_CleanupExpiredWeatherForecasts
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @DeletedCount INT;

    DELETE FROM dbo.WEATHER_FORECAST
    WHERE ExpiresAt < DATEADD(HOUR, -6, GETUTCDATE());

    SET @DeletedCount = @@ROWCOUNT;

    PRINT CONCAT('Deleted ', @DeletedCount, ' expired weather forecasts');

    -- Cleanup old API usage logs (keep 30 days)
    DELETE FROM dbo.WEATHER_API_USAGE
    WHERE CallTimestamp < DATEADD(DAY, -30, GETUTCDATE());

    SET @DeletedCount = @@ROWCOUNT;

    PRINT CONCAT('Deleted ', @DeletedCount, ' old API usage records');
END
GO

-- =============================================
-- View: Current Weather Impact by Vessel
-- =============================================
IF OBJECT_ID('dbo.vw_CurrentWeatherImpactByVessel', 'V') IS NOT NULL
    DROP VIEW dbo.vw_CurrentWeatherImpactByVessel;
GO

CREATE VIEW dbo.vw_CurrentWeatherImpactByVessel
AS
SELECT
    vs.ScheduleId,
    vs.VesselId,
    v.VesselName,
    AVG(wf.WeatherImpactFactor) AS AvgRouteImpactFactor,
    MAX(CASE WHEN wf.AlertLevel = 'CRITICAL' THEN 1 ELSE 0 END) AS HasCriticalAlert,
    MAX(CASE WHEN wf.AlertLevel = 'WARNING' THEN 1 ELSE 0 END) AS HasWarningAlert,
    COUNT(wf.ForecastId) AS TotalWaypoints,
    MAX(wf.FetchedAt) AS LastWeatherUpdate
FROM dbo.VESSEL_SCHEDULE vs
INNER JOIN dbo.VESSELS v ON vs.VesselId = v.VesselId
LEFT JOIN dbo.WEATHER_FORECAST wf
    ON wf.VesselId = vs.VesselId
    AND wf.ScheduleId = vs.ScheduleId
    AND wf.ExpiresAt > GETUTCDATE()
    AND wf.IsActive = 1
WHERE vs.Status IN ('Scheduled', 'Approaching')
GROUP BY vs.ScheduleId, vs.VesselId, v.VesselName;
GO

PRINT '==============================================';
PRINT 'Weather Forecast Tables Created Successfully';
PRINT 'Total Objects Created: 2 Tables, 2 Stored Procedures, 1 View';
PRINT '==============================================';
GO
