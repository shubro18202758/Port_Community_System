-- =============================================
-- SEED DATA: SUPPORTING DATA
-- Weather, Tidal, AIS, Pilots, Tugboats, Resources
-- =============================================

USE [BerthPlanning];
GO

SET NOCOUNT ON;
DECLARE @Now DATETIME2 = GETUTCDATE();

PRINT '=== SEEDING SUPPORTING DATA ===';

-- =============================================
-- WEATHER DATA (20 records)
-- =============================================
PRINT 'Inserting Weather Data...';

INSERT INTO WEATHER_DATA (PortId, PortCode, RecordedAt, WindSpeed, WindDirection, WindDirectionText, Visibility, WaveHeight, Temperature, Precipitation, WeatherCondition, Climate, Season, IsAlert, FetchedAt)
SELECT PortId, 'INMUN', DATEADD(HOUR, -1, @Now), 12.5, 45, 'NE', 10000, 0.8, 28.5, 0, N'Clear', N'Tropical', N'Winter', 0, @Now FROM PORTS WHERE PortCode = 'INMUN';
INSERT INTO WEATHER_DATA (PortId, PortCode, RecordedAt, WindSpeed, WindDirection, WindDirectionText, Visibility, WaveHeight, Temperature, Precipitation, WeatherCondition, Climate, Season, IsAlert, FetchedAt)
SELECT PortId, 'INMUN', DATEADD(HOUR, -2, @Now), 14.2, 90, 'E', 9500, 1.0, 29.0, 0, N'Partly Cloudy', N'Tropical', N'Winter', 0, @Now FROM PORTS WHERE PortCode = 'INMUN';
INSERT INTO WEATHER_DATA (PortId, PortCode, RecordedAt, WindSpeed, WindDirection, WindDirectionText, Visibility, WaveHeight, Temperature, Precipitation, WeatherCondition, Climate, Season, IsAlert, FetchedAt)
SELECT PortId, 'INMUN', DATEADD(HOUR, -4, @Now), 18.0, 135, 'SE', 8000, 1.2, 27.5, 0, N'Cloudy', N'Tropical', N'Winter', 0, @Now FROM PORTS WHERE PortCode = 'INMUN';
INSERT INTO WEATHER_DATA (PortId, PortCode, RecordedAt, WindSpeed, WindDirection, WindDirectionText, Visibility, WaveHeight, Temperature, Precipitation, WeatherCondition, Climate, Season, IsAlert, FetchedAt)
SELECT PortId, 'INMUN', DATEADD(HOUR, -6, @Now), 10.0, 180, 'S', 10000, 0.6, 30.0, 0, N'Sunny', N'Tropical', N'Winter', 0, @Now FROM PORTS WHERE PortCode = 'INMUN';
INSERT INTO WEATHER_DATA (PortId, PortCode, RecordedAt, WindSpeed, WindDirection, WindDirectionText, Visibility, WaveHeight, Temperature, Precipitation, WeatherCondition, Climate, Season, IsAlert, FetchedAt)
SELECT PortId, 'INMUN', DATEADD(HOUR, -8, @Now), 8.5, 225, 'SW', 10000, 0.5, 31.0, 0, N'Clear', N'Tropical', N'Winter', 0, @Now FROM PORTS WHERE PortCode = 'INMUN';

PRINT 'Inserted: 5 Weather Records';

-- =============================================
-- TIDAL DATA (20 records)
-- =============================================
PRINT 'Inserting Tidal Data...';

INSERT INTO TIDAL_DATA (TideTime, TideType, Height) VALUES (DATEADD(HOUR, -12, @Now), 'HighTide', 4.8);
INSERT INTO TIDAL_DATA (TideTime, TideType, Height) VALUES (DATEADD(HOUR, -6, @Now), 'LowTide', 1.2);
INSERT INTO TIDAL_DATA (TideTime, TideType, Height) VALUES (@Now, 'HighTide', 5.0);
INSERT INTO TIDAL_DATA (TideTime, TideType, Height) VALUES (DATEADD(HOUR, 6, @Now), 'LowTide', 0.9);
INSERT INTO TIDAL_DATA (TideTime, TideType, Height) VALUES (DATEADD(HOUR, 12, @Now), 'HighTide', 4.6);
INSERT INTO TIDAL_DATA (TideTime, TideType, Height) VALUES (DATEADD(HOUR, 18, @Now), 'LowTide', 1.1);
INSERT INTO TIDAL_DATA (TideTime, TideType, Height) VALUES (DATEADD(HOUR, 24, @Now), 'HighTide', 4.9);
INSERT INTO TIDAL_DATA (TideTime, TideType, Height) VALUES (DATEADD(HOUR, 30, @Now), 'LowTide', 1.0);

PRINT 'Inserted: 8 Tidal Records';

-- =============================================
-- PILOTS (15 pilots)
-- =============================================
PRINT 'Inserting Pilots...';

INSERT INTO PILOTS (PortCode, PortName, PilotName, PilotCode, PilotType, PilotClass, CertificationLevel, ExperienceYears, MaxVesselGT, MaxVesselLOA, NightOperations, AdverseWeather, CanTrain, Status)
VALUES
('INMUN', N'Mundra Port', N'Capt. Rajesh Saxena', N'PLT-001', N'Marine Pilot', N'Class A', N'Master', 25, 200000, 400, 1, 1, 1, N'Active'),
('INMUN', N'Mundra Port', N'Capt. Vikram Chauhan', N'PLT-002', N'Marine Pilot', N'Class A', N'Senior', 18, 150000, 350, 1, 1, 0, N'Active'),
('INMUN', N'Mundra Port', N'Capt. Suresh Yadav', N'PLT-003', N'Marine Pilot', N'Class A', N'Senior', 15, 150000, 350, 1, 0, 0, N'Active'),
('INMUN', N'Mundra Port', N'Capt. Amit Shah', N'PLT-004', N'Marine Pilot', N'Class B', N'Junior', 8, 100000, 300, 1, 0, 0, N'Active'),
('INMUN', N'Mundra Port', N'Capt. Prakash Patel', N'PLT-005', N'Deep Sea Pilot', N'Class A', N'Master', 22, 250000, 400, 1, 1, 1, N'Active'),
('INMUN', N'Mundra Port', N'Capt. Hemant Joshi', N'PLT-006', N'River Pilot', N'Class B', N'Senior', 12, 80000, 250, 1, 0, 0, N'Active'),
('INMUN', N'Mundra Port', N'Capt. Dinesh Kumar', N'PLT-007', N'Marine Pilot', N'Class A', N'Senior', 16, 150000, 350, 1, 1, 0, N'Active'),
('INMUN', N'Mundra Port', N'Capt. Ramesh Verma', N'PLT-008', N'Marine Pilot', N'Class B', N'Junior', 6, 80000, 280, 0, 0, 0, N'Active'),
('INMUN', N'Mundra Port', N'Capt. Ajay Singh', N'PLT-009', N'Marine Pilot', N'Class A', N'Senior', 14, 120000, 320, 1, 1, 0, N'Active'),
('INMUN', N'Mundra Port', N'Capt. Vijay Sharma', N'PLT-010', N'Marine Pilot', N'Class B', N'Junior', 5, 70000, 260, 0, 0, 0, N'Active');

PRINT 'Inserted: 10 Pilots';

-- =============================================
-- TUGBOATS (12 tugs)
-- =============================================
PRINT 'Inserting Tugboats...';

INSERT INTO TUGBOATS (PortCode, TugName, TugCode, TugType, TugClass, Operator, BollardPull, Length, Beam, Draft, EnginePower, MaxSpeed, Status)
VALUES
('INMUN', N'Mundra Shakti', N'TUG-001', N'ASD', N'Class A', N'APSEZ', 65, 32.0, 11.5, 5.5, 5000, 13.5, N'Active'),
('INMUN', N'Mundra Tej', N'TUG-002', N'VSP', N'Class A', N'APSEZ', 60, 30.0, 10.5, 5.0, 4500, 13.0, N'Active'),
('INMUN', N'Mundra Veera', N'TUG-003', N'ASD', N'Class A', N'APSEZ', 70, 34.0, 12.0, 5.8, 5500, 14.0, N'Active'),
('INMUN', N'Mundra Prabha', N'TUG-004', N'Conventional', N'Class B', N'APSEZ', 45, 28.0, 9.0, 4.5, 3500, 12.0, N'Active'),
('INMUN', N'Mundra Tara', N'TUG-005', N'VSP', N'Class A', N'APSEZ', 85, 38.0, 13.0, 6.0, 7000, 15.0, N'Active'),
('INMUN', N'Mundra Raja', N'TUG-006', N'ASD', N'Class B', N'APSEZ', 50, 29.0, 10.0, 4.8, 4000, 12.5, N'Active'),
('INMUN', N'Mundra Rani', N'TUG-007', N'ASD', N'Class A', N'APSEZ', 68, 33.0, 11.8, 5.6, 5200, 13.8, N'Active'),
('INMUN', N'Mundra Yodha', N'TUG-008', N'VSP', N'Class A', N'APSEZ', 75, 35.0, 12.5, 5.9, 6000, 14.5, N'Active');

PRINT 'Inserted: 8 Tugboats';

-- =============================================
-- RESOURCES
-- =============================================
PRINT 'Inserting Resources...';

INSERT INTO RESOURCES (ResourceType, ResourceName, Capacity, IsAvailable) VALUES
('Crane', N'Gantry Crane 1', 1, 1),
('Crane', N'Gantry Crane 2', 1, 1),
('Crane', N'Mobile Crane 1', 1, 1),
('Crane', N'Mobile Crane 2', 1, 1),
('Tugboat', N'Tug Service', 8, 1),
('Pilot', N'Pilot Service', 10, 1),
('Labor', N'Dock Workers Team A', 20, 1),
('Labor', N'Dock Workers Team B', 20, 1),
('Mooring', N'Mooring Team', 6, 1);

PRINT 'Inserted: 9 Resources';

-- =============================================
-- AIS DATA (for scheduled vessels)
-- =============================================
PRINT 'Inserting AIS Data...';

INSERT INTO AIS_DATA (VesselId, PortCode, VesselType, Latitude, Longitude, Speed, Course, Heading, NavigationStatus, Phase, DistanceToPort, RecordedAt, FetchedAt)
SELECT TOP 30
    vs.VesselId, 'INMUN', v.VesselType,
    22.756 + (RAND(CHECKSUM(NEWID())) - 0.5) * 0.1,
    69.636 + (RAND(CHECKSUM(NEWID())) - 0.5) * 0.1,
    CASE vs.Status WHEN 'Berthed' THEN 0 WHEN 'Approaching' THEN 5.5 ELSE 12.0 END,
    RAND(CHECKSUM(NEWID())) * 360,
    RAND(CHECKSUM(NEWID())) * 360,
    CASE vs.Status WHEN 'Berthed' THEN 'Moored' WHEN 'Approaching' THEN 'Under way using engine' ELSE 'Under way using engine' END,
    CASE vs.Status WHEN 'Berthed' THEN 'At Berth' WHEN 'Approaching' THEN 'In Port' ELSE 'Approaching' END,
    CASE vs.Status WHEN 'Berthed' THEN 0 WHEN 'Approaching' THEN 2.5 ELSE 15.0 END,
    DATEADD(MINUTE, -5, @Now),
    @Now
FROM VESSEL_SCHEDULE vs
INNER JOIN VESSELS v ON v.VesselId = vs.VesselId;

PRINT 'Inserted AIS Data: ' + CAST(@@ROWCOUNT AS VARCHAR);

-- =============================================
-- VERIFY
-- =============================================
PRINT '';
PRINT '=== SUPPORTING DATA SUMMARY ===';

SELECT 'WEATHER_DATA' AS [Table], COUNT(*) AS Records FROM WEATHER_DATA
UNION ALL SELECT 'TIDAL_DATA', COUNT(*) FROM TIDAL_DATA
UNION ALL SELECT 'PILOTS', COUNT(*) FROM PILOTS
UNION ALL SELECT 'TUGBOATS', COUNT(*) FROM TUGBOATS
UNION ALL SELECT 'RESOURCES', COUNT(*) FROM RESOURCES
UNION ALL SELECT 'AIS_DATA', COUNT(*) FROM AIS_DATA;
GO
