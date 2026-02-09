-- ============================================
-- Berth Planning System - Seed Data: WEATHER & TIDAL
-- Weather and Tidal Data for 45 days
-- Matches table schema exactly
-- ============================================

-- Clear existing data
DELETE FROM WEATHER_DATA;
DELETE FROM TIDAL_DATA;
DBCC CHECKIDENT ('WEATHER_DATA', RESEED, 0);
DBCC CHECKIDENT ('TIDAL_DATA', RESEED, 0);

-- ============================================
-- WEATHER DATA (Every 3 hours for 45 days)
-- Schema: RecordedAt, WindSpeed, WindDirection (INT 0-360), Visibility (INT meters),
--         WaveHeight, Temperature, Precipitation, WeatherCondition, IsAlert
-- ============================================

DECLARE @StartDate DATETIME = DATEADD(DAY, -30, GETDATE());
DECLARE @EndDate DATETIME = DATEADD(DAY, 15, GETDATE());
DECLARE @CurrentTime DATETIME = @StartDate;
DECLARE @Temperature DECIMAL(5,2);
DECLARE @WindSpeed DECIMAL(5,2);
DECLARE @WindDirection INT; -- degrees 0-360
DECLARE @WaveHeight DECIMAL(4,2);
DECLARE @Visibility INT; -- meters
DECLARE @Precipitation DECIMAL(5,2);
DECLARE @WeatherCondition NVARCHAR(100);
DECLARE @IsAlert BIT;

-- Create temp table for weather
CREATE TABLE #WeatherTemp (
    RecordedAt DATETIME,
    WindSpeed DECIMAL(5,2),
    WindDirection INT,
    Visibility INT,
    WaveHeight DECIMAL(4,2),
    Temperature DECIMAL(5,2),
    Precipitation DECIMAL(5,2),
    WeatherCondition NVARCHAR(100),
    IsAlert BIT
);

WHILE @CurrentTime < @EndDate
BEGIN
    -- Base temperature (25-32°C typical for tropical port)
    SET @Temperature = 25.0 + (ABS(CHECKSUM(NEWID())) % 80) / 10.0;

    -- Wind speed (0-35 km/h, occasionally higher)
    SET @WindSpeed = (ABS(CHECKSUM(NEWID())) % 350) / 10.0;

    -- Wind direction (0-360 degrees)
    SET @WindDirection = ABS(CHECKSUM(NEWID())) % 360;

    -- Wave height (0.5-3.5m)
    SET @WaveHeight = 0.5 + (ABS(CHECKSUM(NEWID())) % 30) / 10.0;

    -- Visibility (5000-20000 meters)
    SET @Visibility = 5000 + (ABS(CHECKSUM(NEWID())) % 15000);

    -- Precipitation (mostly 0, occasional rain)
    SET @Precipitation = CASE
        WHEN ABS(CHECKSUM(NEWID())) % 100 < 70 THEN 0
        ELSE (ABS(CHECKSUM(NEWID())) % 500) / 10.0
    END;

    -- Weather condition based on conditions
    SET @WeatherCondition = CASE
        WHEN @Precipitation > 20 THEN 'Rain'
        WHEN @WindSpeed > 25 THEN 'Windy'
        WHEN @Visibility < 5000 THEN 'Fog'
        WHEN @WaveHeight > 2.5 THEN 'Rough Seas'
        ELSE 'Clear'
    END;

    -- Alert conditions
    SET @IsAlert = CASE
        WHEN @WindSpeed > 30 OR @WaveHeight > 2.5 OR @Visibility < 2000 OR @Precipitation > 30 THEN 1
        ELSE 0
    END;

    INSERT INTO #WeatherTemp VALUES (
        @CurrentTime, @WindSpeed, @WindDirection, @Visibility,
        @WaveHeight, @Temperature, @Precipitation,
        @WeatherCondition, @IsAlert
    );

    SET @CurrentTime = DATEADD(HOUR, 3, @CurrentTime);
END

-- Insert weather data
INSERT INTO WEATHER_DATA (RecordedAt, WindSpeed, WindDirection, Visibility, WaveHeight, Temperature, Precipitation, WeatherCondition, IsAlert)
SELECT * FROM #WeatherTemp;

-- Add some severe weather events
UPDATE WEATHER_DATA
SET WindSpeed = 45 + (ABS(CHECKSUM(NEWID())) % 20),
    WaveHeight = 3.5 + (ABS(CHECKSUM(NEWID())) % 15) / 10.0,
    WeatherCondition = 'Storm',
    IsAlert = 1
WHERE WeatherId IN (
    SELECT TOP 10 WeatherId
    FROM WEATHER_DATA
    WHERE RecordedAt < GETDATE()
    ORDER BY NEWID()
);

DROP TABLE #WeatherTemp;

-- ============================================
-- TIDAL DATA (High and Low tides for 45 days)
-- Schema: TidalId, TideTime, TideType ('HighTide'/'LowTide'), Height
-- ============================================

DECLARE @TideDate DATETIME = DATEADD(DAY, -30, CAST(GETDATE() AS DATE));
DECLARE @TideTime DATETIME;
DECLARE @TideHeight DECIMAL(5,2);
DECLARE @TideType VARCHAR(10);
DECLARE @BaseTideHour INT;

-- Create temp table for tidal data
CREATE TABLE #TidalTemp (
    TideTime DATETIME,
    TideType VARCHAR(20),
    Height DECIMAL(5,2)
);

WHILE @TideDate < DATEADD(DAY, 15, GETDATE())
BEGIN
    -- First High Tide (early morning, around 2-5 AM)
    SET @BaseTideHour = 2 + (ABS(CHECKSUM(NEWID())) % 4);
    SET @TideTime = DATEADD(HOUR, @BaseTideHour, @TideDate);
    SET @TideTime = DATEADD(MINUTE, ABS(CHECKSUM(NEWID())) % 60, @TideTime);
    SET @TideHeight = 4.5 + (ABS(CHECKSUM(NEWID())) % 30) / 10.0; -- 4.5-7.5m high tide

    INSERT INTO #TidalTemp VALUES (@TideTime, 'HighTide', @TideHeight);

    -- First Low Tide (morning, around 8-11 AM)
    SET @BaseTideHour = 8 + (ABS(CHECKSUM(NEWID())) % 4);
    SET @TideTime = DATEADD(HOUR, @BaseTideHour, @TideDate);
    SET @TideTime = DATEADD(MINUTE, ABS(CHECKSUM(NEWID())) % 60, @TideTime);
    SET @TideHeight = 0.5 + (ABS(CHECKSUM(NEWID())) % 20) / 10.0; -- 0.5-2.5m low tide

    INSERT INTO #TidalTemp VALUES (@TideTime, 'LowTide', @TideHeight);

    -- Second High Tide (afternoon, around 2-5 PM)
    SET @BaseTideHour = 14 + (ABS(CHECKSUM(NEWID())) % 4);
    SET @TideTime = DATEADD(HOUR, @BaseTideHour, @TideDate);
    SET @TideTime = DATEADD(MINUTE, ABS(CHECKSUM(NEWID())) % 60, @TideTime);
    SET @TideHeight = 4.2 + (ABS(CHECKSUM(NEWID())) % 35) / 10.0; -- 4.2-7.7m high tide

    INSERT INTO #TidalTemp VALUES (@TideTime, 'HighTide', @TideHeight);

    -- Second Low Tide (evening, around 8-11 PM)
    SET @BaseTideHour = 20 + (ABS(CHECKSUM(NEWID())) % 4);
    SET @TideTime = DATEADD(HOUR, @BaseTideHour, @TideDate);
    SET @TideTime = DATEADD(MINUTE, ABS(CHECKSUM(NEWID())) % 60, @TideTime);
    SET @TideHeight = 0.8 + (ABS(CHECKSUM(NEWID())) % 20) / 10.0; -- 0.8-2.8m low tide

    INSERT INTO #TidalTemp VALUES (@TideTime, 'LowTide', @TideHeight);

    SET @TideDate = DATEADD(DAY, 1, @TideDate);
END

-- Insert tidal data
INSERT INTO TIDAL_DATA (TideTime, TideType, Height)
SELECT * FROM #TidalTemp
ORDER BY TideTime;

DROP TABLE #TidalTemp;

-- Display counts
SELECT 'Weather records inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM WEATHER_DATA;
SELECT 'Tidal records inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM TIDAL_DATA;
SELECT 'Weather alerts: ' + CAST(COUNT(*) AS VARCHAR) FROM WEATHER_DATA WHERE IsAlert = 1;
