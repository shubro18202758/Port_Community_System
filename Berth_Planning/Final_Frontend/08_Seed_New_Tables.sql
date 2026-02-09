-- =============================================
-- BERTH PLANNING - SEED DATA FOR NEW TABLES
-- Populates CHANNELS, ANCHORAGES, UKC_DATA, PILOTS, TUGBOATS
-- =============================================

USE BerthPlanning;
GO

-- =============================================
-- SEED CHANNELS
-- =============================================
SET IDENTITY_INSERT dbo.CHANNELS ON;
INSERT INTO dbo.CHANNELS (ChannelId, PortId, ChannelName, ChannelLength, ChannelWidth, ChannelDepth, ChannelDepthAtChartDatum, OneWayOrTwoWay, MaxVesselLOA, MaxVesselBeam, MaxVesselDraft, TrafficSeparationScheme, SpeedLimit, TidalWindowRequired, PilotageCompulsory, TugEscortRequired, DayNightRestrictions, VisibilityMinimum, WindSpeedLimit, CurrentSpeedLimit, IsActive) VALUES
(1, 1, 'Mumbai Main Approach Channel', 35.00, 600.00, 15.00, 14.50, 'Two-Way', 400.00, 59.00, 15.00, 1, 10, 0, 1, 1, 'Night Restricted', 1, 40, 3.50, 1),
(2, 1, 'Mumbai Inner Harbour Channel', 8.00, 350.00, 13.10, 12.50, 'Two-Way', 350.00, 52.00, 13.00, 0, 8, 0, 1, 1, 'None', 1, 35, 3.00, 1),
(3, 1, 'Jawahar Dweep Approach', 12.00, 400.00, 20.00, 18.50, 'One-Way', 350.00, 60.00, 18.00, 1, 8, 1, 1, 1, 'Daylight Only', 2, 30, 2.50, 1),
(4, 1, 'Pir Pau Approach Channel', 5.00, 200.00, 11.00, 10.00, 'Two-Way', 200.00, 35.00, 10.00, 0, 6, 1, 1, 0, 'None', 0.5, 25, 2.00, 1);
SET IDENTITY_INSERT dbo.CHANNELS OFF;
PRINT 'Channels data inserted: 4 records';
GO

-- =============================================
-- SEED ANCHORAGES
-- =============================================
SET IDENTITY_INSERT dbo.ANCHORAGES ON;
INSERT INTO dbo.ANCHORAGES (AnchorageId, PortId, AnchorageName, AnchorageType, Latitude, Longitude, Depth, MaxVessels, CurrentOccupancy, MaxVesselLOA, MaxVesselDraft, AverageWaitingTime, STSCargoOpsPermitted, QuarantineAnchorage, IsActive) VALUES
(1, 1, 'Mumbai Anchorage Alpha', 'General', 18.9200, 72.9100, 13, 15, 5, 400, 14.00, 3.50, 0, 0, 1),
(2, 1, 'Mumbai Anchorage Bravo', 'General', 18.9150, 72.9050, 12, 12, 3, 350, 13.00, 4.00, 0, 0, 1),
(3, 1, 'Mumbai Deep Water Anchorage', 'Deep Water', 18.9000, 72.9200, 20, 8, 2, 400, 22.00, 6.00, 1, 0, 1),
(4, 1, 'Mumbai VLCC Anchorage', 'Deep Water', 18.8800, 72.9300, 25, 5, 1, 400, 25.00, 8.00, 1, 0, 1),
(5, 1, 'Mumbai Quarantine Anchorage', 'Quarantine', 18.9300, 72.9150, 11, 10, 0, 300, 12.00, 2.00, 0, 1, 1),
(6, 1, 'Mumbai Explosives Anchorage', 'Special', 18.8700, 72.9400, 15, 3, 0, 250, 14.00, 12.00, 0, 0, 1),
(7, 1, 'Mumbai Waiting Anchorage', 'General', 18.9350, 72.8900, 10, 20, 8, 300, 11.00, 2.50, 0, 0, 1);
SET IDENTITY_INSERT dbo.ANCHORAGES OFF;
PRINT 'Anchorages data inserted: 7 records';
GO

-- =============================================
-- SEED PILOTS
-- =============================================
SET IDENTITY_INSERT dbo.PILOTS ON;
INSERT INTO dbo.PILOTS (PilotId, PortId, PilotName, LicenseNumber, LicenseClass, VesselTypeRestrictions, MaxVesselLOA, MaxVesselDraft, MaxVesselGT, NightPilotage, DeepDraftCertified, TankerEndorsement, LNGEndorsement, Status, ContactNumber, ExperienceYears, IsActive) VALUES
(1, 1, 'Capt. Rajesh Sharma', 'MBP001', 'Class A', 'None', 400.00, 22.00, 350000, 1, 1, 1, 1, 'Available', '+91-9876543210', 25, 1),
(2, 1, 'Capt. Mohammed Khan', 'MBP002', 'Class A', 'None', 400.00, 20.00, 300000, 1, 1, 1, 0, 'Available', '+91-9876543211', 22, 1),
(3, 1, 'Capt. Priya Menon', 'MBP003', 'Class A', 'None', 350.00, 18.00, 250000, 1, 1, 0, 0, 'On Duty', '+91-9876543212', 18, 1),
(4, 1, 'Capt. Suresh Patel', 'MBP004', 'Class B', 'Container Only', 350.00, 16.00, 200000, 1, 0, 0, 0, 'Available', '+91-9876543213', 15, 1),
(5, 1, 'Capt. Anita Desai', 'MBP005', 'Class B', 'None', 300.00, 14.00, 150000, 1, 0, 1, 0, 'Available', '+91-9876543214', 12, 1),
(6, 1, 'Capt. Vikram Singh', 'MBP006', 'Class A', 'Tanker Specialist', 400.00, 25.00, 400000, 1, 1, 1, 1, 'On Duty', '+91-9876543215', 28, 1),
(7, 1, 'Capt. Ravi Kumar', 'MBP007', 'Class B', 'None', 280.00, 14.00, 120000, 0, 0, 0, 0, 'Available', '+91-9876543216', 10, 1),
(8, 1, 'Capt. Deepak Joshi', 'MBP008', 'Class C', 'Coastal Only', 200.00, 10.00, 50000, 0, 0, 0, 0, 'Available', '+91-9876543217', 6, 1),
(9, 1, 'Capt. Meera Nair', 'MBP009', 'Class B', 'None', 320.00, 15.00, 180000, 1, 0, 1, 0, 'Off Duty', '+91-9876543218', 14, 1),
(10, 1, 'Capt. Amit Verma', 'MBP010', 'Class A', 'None', 380.00, 20.00, 280000, 1, 1, 1, 0, 'Available', '+91-9876543219', 20, 1),
(11, 1, 'Capt. Sanjay Rao', 'MBP011', 'Class C', 'Coastal Only', 180.00, 9.00, 40000, 0, 0, 0, 0, 'Leave', '+91-9876543220', 5, 1),
(12, 1, 'Capt. Nisha Kulkarni', 'MBP012', 'Class B', 'General Cargo', 260.00, 12.00, 100000, 1, 0, 0, 0, 'Available', '+91-9876543221', 8, 1);
SET IDENTITY_INSERT dbo.PILOTS OFF;
PRINT 'Pilots data inserted: 12 records';
GO

-- =============================================
-- SEED TUGBOATS
-- =============================================
SET IDENTITY_INSERT dbo.TUGBOATS ON;
INSERT INTO dbo.TUGBOATS (TugboatId, PortId, TugboatName, IMO, TugType, BollardPull, EnginePower, LOA, Beam, Draft, YearBuilt, FirefightingCapability, OilSpillResponse, SalvageCapable, Status, CurrentLocation, FuelCapacity, CrewCapacity, IsActive) VALUES
(1, 1, 'TUG MAHUL', 'IMO9812345', 'ASD', 60.00, 4500, 32.0, 12.5, 5.5, 2018, 1, 1, 0, 'Available', 'Inner Harbour', 150.00, 8, 1),
(2, 1, 'TUG PRABODHAN', 'IMO9812346', 'ASD', 55.00, 4200, 30.0, 12.0, 5.2, 2016, 1, 0, 0, 'On Duty', 'Approaching BPCT', 140.00, 8, 1),
(3, 1, 'TUG JAWAHAR', 'IMO9812347', 'Voith', 70.00, 5500, 35.0, 13.0, 5.8, 2020, 1, 1, 1, 'Available', 'JDOT Station', 180.00, 10, 1),
(4, 1, 'TUG PRAGATI', 'IMO9812348', 'Conventional', 45.00, 3200, 28.0, 10.5, 4.8, 2012, 0, 0, 0, 'Available', 'Inner Harbour', 120.00, 6, 1),
(5, 1, 'TUG MUMBAI', 'IMO9812349', 'ASD', 75.00, 6000, 38.0, 14.0, 6.2, 2022, 1, 1, 1, 'Available', 'Deep Water Zone', 200.00, 10, 1),
(6, 1, 'TUG GATEWAY', 'IMO9812350', 'Azimuth', 65.00, 5000, 34.0, 12.8, 5.6, 2019, 1, 1, 0, 'On Duty', 'Channel Patrol', 160.00, 8, 1),
(7, 1, 'TUG COASTAL', 'IMO9812351', 'Conventional', 40.00, 2800, 26.0, 10.0, 4.5, 2010, 0, 0, 0, 'Maintenance', 'Repair Dock', 100.00, 6, 1),
(8, 1, 'TUG HARBOR', 'IMO9812352', 'ASD', 50.00, 3800, 29.0, 11.5, 5.0, 2015, 1, 0, 0, 'Available', 'Victoria Dock', 130.00, 7, 1),
(9, 1, 'TUG PIONEER', 'IMO9812353', 'ASD', 80.00, 6500, 40.0, 14.5, 6.5, 2023, 1, 1, 1, 'Available', 'VLCC Anchorage', 220.00, 12, 1),
(10, 1, 'TUG ENDEAVOR', 'IMO9812354', 'Voith', 68.00, 5200, 33.0, 12.5, 5.5, 2017, 1, 1, 0, 'On Duty', 'Bulk Terminal', 165.00, 9, 1),
(11, 1, 'TUG DOLPHIN', 'IMO9812355', 'Conventional', 35.00, 2400, 24.0, 9.5, 4.2, 2008, 0, 0, 0, 'Available', 'Cruise Terminal', 90.00, 5, 1),
(12, 1, 'TUG ANCHOR', 'IMO9812356', 'ASD', 58.00, 4400, 31.0, 12.2, 5.3, 2021, 1, 0, 0, 'Available', 'Anchorage Alpha', 145.00, 8, 1);
SET IDENTITY_INSERT dbo.TUGBOATS OFF;
PRINT 'Tugboats data inserted: 12 records';
GO

-- =============================================
-- SEED UKC_DATA (Sample calculations)
-- =============================================
INSERT INTO dbo.UKC_DATA (PortId, PortCode, VesselType, VesselLOA, VesselBeam, VesselDraft, GrossTonnage, ChannelDepth, TidalHeight, AvailableDepth, StaticUKC, Squat, DynamicUKC, UKCPercentage, RequiredUKCPercentage, IsSafe, SpeedKnots, BlockCoefficient, WaveAllowance, HeelAllowance, NetUKC, SafetyMargin, RiskLevel, Recommendation) VALUES
(1, 'INMUN', 'Container', 400.00, 61.50, 16.35, 233534, 16.50, 3.80, 20.30, 3.95, 0.62, 3.33, 20.40, 10.00, 1, 6.00, 0.72, 0.15, 0.10, 3.08, 1.43, 'Low', 'Safe to transit. Adequate UKC with current tide. Proceed via Main Channel.'),
(1, 'INMUN', 'Container', 400.00, 61.50, 16.35, 233534, 16.50, 0.60, 17.10, 0.75, 0.58, 0.17, 1.00, 10.00, 0, 4.00, 0.72, 0.15, 0.10, -0.08, -1.73, 'Critical', 'UNSAFE: Insufficient UKC at low tide. Delay transit until tide reaches 2.5m minimum.'),
(1, 'INMUN', 'Tanker', 333.00, 60.00, 22.50, 300000, 25.00, 4.20, 29.20, 6.70, 0.85, 5.85, 26.00, 15.00, 1, 5.00, 0.85, 0.20, 0.15, 5.50, 2.00, 'Low', 'Safe for VLCC transit via Deep Water Channel. Maintain 5 knots maximum speed.'),
(1, 'INMUN', 'Bulk', 289.00, 45.00, 18.20, 180000, 20.00, 3.50, 23.50, 5.30, 0.70, 4.60, 25.27, 10.00, 1, 6.00, 0.80, 0.15, 0.12, 4.33, 1.98, 'Low', 'Cape size bulk carrier cleared for transit. Use Bulk Terminal approach.'),
(1, 'INMUN', 'Tanker', 274.00, 48.00, 17.00, 160000, 18.00, 2.80, 20.80, 3.80, 0.55, 3.25, 19.12, 10.00, 1, 6.00, 0.78, 0.12, 0.10, 3.03, 1.48, 'Low', 'Aframax tanker cleared. Standard approach via JDOT channel.'),
(1, 'INMUN', 'Container', 334.80, 48.40, 14.20, 112000, 15.00, 1.50, 16.50, 2.30, 0.48, 1.82, 12.82, 10.00, 1, 7.00, 0.70, 0.10, 0.08, 1.64, 0.29, 'Medium', 'Marginal UKC. Reduce speed to 6 knots and await better tide if possible.'),
(1, 'INMUN', 'General', 169.00, 27.40, 10.50, 22000, 13.00, 2.20, 15.20, 4.70, 0.35, 4.35, 41.43, 10.00, 1, 8.00, 0.65, 0.08, 0.05, 4.22, 3.07, 'Low', 'General cargo vessel has excellent UKC margin. Clear for transit.'),
(1, 'INMUN', 'Passenger', 330.00, 38.00, 8.50, 140000, 11.00, 3.00, 14.00, 5.50, 0.30, 5.20, 61.18, 10.00, 1, 10.00, 0.60, 0.05, 0.05, 5.10, 4.08, 'Low', 'Cruise ship cleared for Cruise Terminal berth. Excellent UKC.'),
(1, 'INMUN', 'Tanker', 230.00, 36.60, 13.50, 55000, 14.00, 1.80, 15.80, 2.30, 0.42, 1.88, 13.93, 10.00, 1, 6.00, 0.75, 0.10, 0.08, 1.70, 0.54, 'Medium', 'LPG carrier - adequate UKC but recommend speed reduction in channel.'),
(1, 'INMUN', 'Bulk', 225.00, 32.30, 14.20, 82000, 15.00, 0.90, 15.90, 1.70, 0.45, 1.25, 8.81, 10.00, 0, 7.00, 0.78, 0.12, 0.08, 1.05, -0.08, 'High', 'UKC below safe threshold. Wait for tide > 1.5m before proceeding.');
PRINT 'UKC_DATA data inserted: 10 records';
GO

-- =============================================
-- ADD MORE VESSEL_SCHEDULE DATA (expand from 10 to 36)
-- =============================================
DECLARE @Now DATETIME2 = GETUTCDATE();

-- Add schedules for more vessels
INSERT INTO dbo.VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, Status) VALUES
(4, NULL, DATEADD(HOUR, 18, @Now), NULL, 'Scheduled'),
(5, NULL, DATEADD(HOUR, 22, @Now), NULL, 'Scheduled'),
(6, NULL, DATEADD(HOUR, 28, @Now), NULL, 'Scheduled'),
(8, NULL, DATEADD(HOUR, 32, @Now), NULL, 'Scheduled'),
(9, NULL, DATEADD(HOUR, 36, @Now), NULL, 'Scheduled'),
(10, 8, DATEADD(HOUR, 5, @Now), DATEADD(MINUTE, 310, @Now), 'Approaching'),
(12, NULL, DATEADD(HOUR, 40, @Now), NULL, 'Scheduled'),
(14, 10, DATEADD(HOUR, 7, @Now), DATEADD(MINUTE, 385, @Now), 'Approaching'),
(15, NULL, DATEADD(HOUR, 44, @Now), NULL, 'Scheduled'),
(17, NULL, DATEADD(HOUR, 15, @Now), NULL, 'Scheduled'),
(18, 15, DATEADD(HOUR, 9, @Now), DATEADD(MINUTE, 520, @Now), 'Approaching'),
(19, NULL, DATEADD(HOUR, 48, @Now), NULL, 'Scheduled'),
(20, 13, DATEADD(HOUR, 2, @Now), DATEADD(HOUR, 2, @Now), 'Approaching'),
(22, NULL, DATEADD(HOUR, 52, @Now), NULL, 'Scheduled'),
(23, NULL, DATEADD(HOUR, 26, @Now), NULL, 'Scheduled'),
(24, NULL, DATEADD(HOUR, 30, @Now), NULL, 'Scheduled'),
(25, NULL, DATEADD(HOUR, 56, @Now), NULL, 'Scheduled'),
(27, NULL, DATEADD(HOUR, 60, @Now), NULL, 'Scheduled'),
(28, 7, DATEADD(HOUR, 11, @Now), DATEADD(MINUTE, 650, @Now), 'Approaching'),
(29, NULL, DATEADD(HOUR, 64, @Now), NULL, 'Scheduled'),
(30, 16, DATEADD(HOUR, 13, @Now), DATEADD(MINUTE, 750, @Now), 'Approaching'),
(31, 9, DATEADD(HOUR, 17, @Now), NULL, 'Scheduled'),
(32, NULL, DATEADD(HOUR, 68, @Now), NULL, 'Scheduled'),
(33, NULL, DATEADD(HOUR, 72, @Now), NULL, 'Scheduled'),
(34, NULL, DATEADD(HOUR, 76, @Now), NULL, 'Scheduled');
PRINT 'Additional Vessel Schedules inserted: 25 records (total ~35)';
GO

-- =============================================
-- ADD MORE WEATHER DATA (48 hours forecast)
-- =============================================
DECLARE @BaseTime DATETIME2 = GETUTCDATE();
INSERT INTO dbo.WEATHER_DATA (WindSpeed, WindDirection, Visibility, WaveHeight, Temperature, Precipitation, WeatherCondition, IsAlert, RecordedAt) VALUES
(14.5, 215.0, 9.0, 0.9, 29.2, 0.0, 'Clear', 0, DATEADD(HOUR, 3, @BaseTime)),
(16.0, 220.0, 8.0, 1.1, 28.5, 0.0, 'Partly Cloudy', 0, DATEADD(HOUR, 6, @BaseTime)),
(18.5, 225.0, 7.5, 1.3, 27.8, 0.5, 'Cloudy', 0, DATEADD(HOUR, 9, @BaseTime)),
(20.0, 230.0, 6.0, 1.5, 27.2, 2.0, 'Light Rain', 0, DATEADD(HOUR, 12, @BaseTime)),
(22.5, 235.0, 5.0, 1.8, 26.5, 5.0, 'Rain', 0, DATEADD(HOUR, 15, @BaseTime)),
(25.0, 240.0, 4.0, 2.0, 26.0, 8.0, 'Heavy Rain', 1, DATEADD(HOUR, 18, @BaseTime)),
(20.0, 235.0, 5.5, 1.6, 26.8, 3.0, 'Rain', 0, DATEADD(HOUR, 21, @BaseTime)),
(16.5, 225.0, 7.0, 1.2, 27.5, 0.5, 'Cloudy', 0, DATEADD(HOUR, 24, @BaseTime));
PRINT 'Additional Weather Data inserted: 8 records';
GO

-- =============================================
-- ADD MORE TIDAL DATA (next 7 days)
-- =============================================
DECLARE @TideBase DATETIME2 = DATEADD(HOUR, 48, GETUTCDATE());
INSERT INTO dbo.TIDAL_DATA (TideType, Height, TideTime) VALUES
('High', 4.9, DATEADD(HOUR, 2, @TideBase)),
('Low', 0.9, DATEADD(HOUR, 8, @TideBase)),
('High', 5.1, DATEADD(HOUR, 14, @TideBase)),
('Low', 0.8, DATEADD(HOUR, 20, @TideBase)),
('High', 5.0, DATEADD(HOUR, 26, @TideBase)),
('Low', 1.0, DATEADD(HOUR, 32, @TideBase)),
('High', 4.8, DATEADD(HOUR, 38, @TideBase)),
('Low', 1.2, DATEADD(HOUR, 44, @TideBase)),
('High', 4.6, DATEADD(HOUR, 50, @TideBase)),
('Low', 1.4, DATEADD(HOUR, 56, @TideBase)),
('High', 4.5, DATEADD(HOUR, 62, @TideBase)),
('Low', 1.5, DATEADD(HOUR, 68, @TideBase));
PRINT 'Additional Tidal Data inserted: 12 records';
GO

PRINT '=============================================';
PRINT 'SEED DATA FOR NEW TABLES COMPLETE!';
PRINT '=============================================';
PRINT 'Records inserted:';
PRINT '  - Channels: 4';
PRINT '  - Anchorages: 7';
PRINT '  - Pilots: 12';
PRINT '  - Tugboats: 12';
PRINT '  - UKC Data: 10';
PRINT '  - Additional Schedules: 25';
PRINT '  - Additional Weather: 8';
PRINT '  - Additional Tides: 12';
PRINT '=============================================';
GO
