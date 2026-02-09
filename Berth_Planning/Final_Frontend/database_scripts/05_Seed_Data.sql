-- =============================================
-- SMARTBERTH AI - SEED DATA FOR MSSQL
-- Generated from seed-data.json
-- =============================================

USE BerthPlanning;
GO

SET IDENTITY_INSERT dbo.PORTS ON;
INSERT INTO dbo.PORTS (PortId, PortCode, PortName, Country, City, TimeZone, Latitude, Longitude, ContactEmail, ContactPhone, IsActive)
VALUES (1, 'INBOM', 'Mumbai Port Trust', 'India', 'Mumbai', 'Asia/Kolkata', 18.926, 72.8438, 'info@mumbaiport.gov.in', '+91-22-22617712', 1);
SET IDENTITY_INSERT dbo.PORTS OFF;
GO

SET IDENTITY_INSERT dbo.TERMINALS ON;
INSERT INTO dbo.TERMINALS (TerminalId, PortId, TerminalCode, TerminalName, TerminalType, OperatorName, Latitude, Longitude, IsActive) VALUES
(1, 1, 'IDCT', 'Indira Dock Container Terminal', 'Container', 'Mumbai Port Trust', 18.927, 72.8445, 1),
(2, 1, 'BPCT', 'Ballard Pier Container Terminal', 'Container', 'Mumbai Port Trust', 18.932, 72.841, 1),
(3, 1, 'MBT', 'Mumbai Bulk Terminal', 'Bulk', 'Mumbai Port Trust', 18.924, 72.846, 1),
(4, 1, 'JDOT', 'Jawahar Dweep Oil Terminal', 'Liquid', 'BPCL/HPCL/IOC', 18.91, 72.83, 1),
(5, 1, 'PPLT', 'Pir Pau Liquid Terminal', 'Liquid', 'Mumbai Port Trust', 18.905, 72.835, 1),
(6, 1, 'VDGC', 'Victoria Dock General Cargo', 'General', 'Mumbai Port Trust', 18.935, 72.842, 1),
(7, 1, 'PDMP', 'Prince Dock Multi-Purpose', 'General', 'Mumbai Port Trust', 18.938, 72.84, 1),
(8, 1, 'MCT', 'Mumbai Cruise Terminal', 'Passenger', 'Mumbai Port Trust', 18.94, 72.838, 1);
SET IDENTITY_INSERT dbo.TERMINALS OFF;
GO

SET IDENTITY_INSERT dbo.BERTHS ON;
INSERT INTO dbo.BERTHS (BerthId, TerminalId, BerthCode, BerthName, MaxLOA, MaxBeam, MaxDraft, BerthType, Equipment, IsActive) VALUES
(1, 1, 'IDCT-01', 'Indira Dock Berth 1', 300.0, 45.0, 11.0, 'Container', '3 Gantry Cranes', 1),
(2, 1, 'IDCT-02', 'Indira Dock Berth 2', 280.0, 42.0, 10.5, 'Container', '3 Gantry Cranes', 1),
(3, 1, 'IDCT-03', 'Indira Dock Berth 3', 250.0, 40.0, 10.0, 'Container', '2 Gantry Cranes', 1),
(4, 2, 'BPCT-01', 'Ballard Pier Berth 1', 320.0, 48.0, 12.0, 'Container', '4 Gantry Cranes', 1),
(5, 2, 'BPCT-02', 'Ballard Pier Berth 2', 290.0, 44.0, 11.0, 'Container', '3 Gantry Cranes', 1),
(6, 3, 'MBT-01', 'Bulk Berth 1', 280.0, 45.0, 14.0, 'Bulk', 'Grab Unloaders', 1),
(7, 3, 'MBT-02', 'Bulk Berth 2', 250.0, 42.0, 12.5, 'Bulk', 'Conveyor Systems', 1),
(8, 3, 'MBT-03', 'Bulk Berth 3', 220.0, 38.0, 11.0, 'Bulk', 'Mobile Cranes', 1),
(9, 4, 'JDOT-01', 'Oil Jetty 1', 330.0, 55.0, 18.0, 'Liquid', 'Loading Arms, Fire Safety', 1),
(10, 4, 'JDOT-02', 'Oil Jetty 2', 300.0, 50.0, 16.0, 'Liquid', 'Loading Arms, Fire Safety', 1),
(11, 5, 'PPLT-01', 'Pir Pau Jetty 1', 200.0, 35.0, 10.0, 'Liquid', 'Chemical Handling', 1),
(12, 5, 'PPLT-02', 'Pir Pau Jetty 2', 180.0, 32.0, 9.0, 'Liquid', 'Chemical Handling', 1),
(13, 6, 'VDGC-01', 'Victoria Berth 1', 200.0, 35.0, 9.5, 'General', 'Mobile Cranes', 1),
(14, 6, 'VDGC-02', 'Victoria Berth 2', 180.0, 32.0, 9.0, 'General', 'Forklifts', 1),
(15, 7, 'PDMP-01', 'Prince Dock Berth 1', 220.0, 38.0, 10.0, 'General', 'Multi-purpose Cranes', 1),
(16, 7, 'PDMP-02', 'Prince Dock Berth 2', 200.0, 35.0, 9.5, 'General', 'Multi-purpose Cranes', 1),
(17, 7, 'PDMP-03', 'Prince Dock Berth 3', 180.0, 32.0, 9.0, 'General', 'Forklifts', 1),
(18, 8, 'MCT-01', 'Cruise Terminal Berth 1', 350.0, 45.0, 10.0, 'Passenger', 'Passenger Gangways', 1),
(19, 8, 'MCT-02', 'Cruise Terminal Berth 2', 280.0, 40.0, 9.0, 'Passenger', 'Passenger Gangways', 1),
(20, 8, 'MCT-03', 'Ferry Terminal', 150.0, 25.0, 6.0, 'Passenger', 'Ferry Ramps', 1);
SET IDENTITY_INSERT dbo.BERTHS OFF;
GO

-- Insert Vessels
SET IDENTITY_INSERT dbo.VESSELS ON;
INSERT INTO dbo.VESSELS (VesselId, VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, Priority) VALUES
(1, 'MAERSK MUMBAI', 'IMO9778791', '219018000', 'Container', 366.0, 48.2, 14.5, 141000, 'Container', 13500, 1),
(2, 'MSC INDIA', 'IMO9839284', '353128000', 'Container', 399.9, 61.5, 16.0, 228000, 'Container', 23000, 1),
(3, 'EVERGREEN FORTUNE', 'IMO9893890', '416529000', 'Container', 334.8, 48.4, 14.2, 112000, 'Container', 11000, 2),
(4, 'CMA CGM GATEWAY', 'IMO9745729', '228391000', 'Container', 363.0, 45.6, 15.5, 131000, 'Container', 14500, 1),
(5, 'HAPAG EXPRESS', 'IMO9782619', '218567000', 'Container', 332.0, 48.2, 13.8, 115000, 'Container', 10500, 2),
(6, 'COSCO SHIPPING STAR', 'IMO9785817', '477234500', 'Container', 399.0, 58.6, 16.0, 197000, 'Container', 21000, 1),
(7, 'CAPE MUMBAI', 'IMO9456123', '538005678', 'Bulk', 289.0, 45.0, 18.2, 180000, 'Iron Ore', 175000, 2),
(8, 'IRON PIONEER', 'IMO9512345', '636019234', 'Bulk', 280.0, 45.0, 17.8, 170000, 'Iron Ore', 165000, 2),
(9, 'PACIFIC GRAIN', 'IMO9634567', '353987654', 'Bulk', 225.0, 32.3, 14.2, 82000, 'Grain', 78000, 2),
(10, 'COAL TRANSPORTER', 'IMO9723456', '477567890', 'Bulk', 249.9, 43.0, 14.5, 95000, 'Coal', 92000, 2),
(11, 'CRUDE VOYAGER', 'IMO9845678', '249345678', 'Tanker', 333.0, 60.0, 22.5, 300000, 'Crude Oil', 2000000, 1),
(12, 'ARABIAN SPIRIT', 'IMO9756789', '538234567', 'Tanker', 274.0, 48.0, 17.0, 160000, 'Crude Oil', 1200000, 1),
(13, 'CHEMICAL STAR', 'IMO9567890', '636456789', 'Tanker', 183.0, 32.2, 12.8, 40000, 'Chemicals', 45000, 2),
(14, 'LPG CARRIER INDIA', 'IMO9678901', '477890123', 'Tanker', 230.0, 36.6, 13.5, 55000, 'LPG', 84000, 1),
(15, 'PRODUCT TANKER MUMBAI', 'IMO9789012', '353123456', 'Tanker', 185.0, 32.2, 12.5, 42000, 'Petroleum Products', 50000, 2),
(16, 'INDIA GENERAL', 'IMO9890123', '419234567', 'General', 169.0, 27.4, 10.5, 22000, 'General Cargo', 18000, 3),
(17, 'MUMBAI CARRIER', 'IMO9901234', '538567890', 'General', 145.0, 23.0, 8.8, 12000, 'General Cargo', 9500, 3),
(18, 'STEEL EXPRESS', 'IMO9012345', '249678901', 'General', 185.0, 28.4, 11.2, 28000, 'Steel Products', 24000, 2),
(19, 'PROJECT CARGO INDIA', 'IMO9123456', '477012345', 'General', 155.0, 25.0, 9.5, 15000, 'Project Cargo', 12000, 2),
(20, 'COASTAL TRADER', 'IMO9234567', '419345678', 'General', 120.0, 20.0, 7.5, 6000, 'General Cargo', 4500, 3);
SET IDENTITY_INSERT dbo.VESSELS OFF;
GO

-- Insert more vessels (21-50)
SET IDENTITY_INSERT dbo.VESSELS ON;
INSERT INTO dbo.VESSELS (VesselId, VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, Priority) VALUES
(21, 'YANG MING VICTORY', 'IMO9345678', '416678901', 'Container', 324.0, 42.8, 14.0, 99000, 'Container', 8500, 2),
(22, 'ONE INDIA', 'IMO9456789', '431789012', 'Container', 336.0, 45.8, 14.5, 108000, 'Container', 10000, 2),
(23, 'HYUNDAI PIONEER', 'IMO9567891', '440890123', 'Container', 294.0, 32.3, 13.2, 75000, 'Container', 6500, 2),
(24, 'PIL MUMBAI', 'IMO9678902', '563901234', 'Container', 260.0, 32.3, 12.5, 55000, 'Container', 4800, 3),
(25, 'SINOKOR STAR', 'IMO9789013', '440012345', 'Container', 222.0, 30.0, 11.0, 35000, 'Container', 2800, 3),
(26, 'CAPE FORTUNE', 'IMO9890124', '538123456', 'Bulk', 299.0, 50.0, 18.5, 200000, 'Iron Ore', 195000, 1),
(27, 'MINERAL PRIDE', 'IMO9901235', '477234567', 'Bulk', 260.0, 43.0, 16.5, 120000, 'Coal', 115000, 2),
(28, 'GRAIN HARVEST', 'IMO9012346', '636345678', 'Bulk', 190.0, 32.3, 12.8, 45000, 'Grain', 42000, 2),
(29, 'BAUXITE EXPRESS', 'IMO9123457', '353456789', 'Bulk', 230.0, 38.0, 14.0, 75000, 'Bauxite', 72000, 2),
(30, 'COASTAL BULKER', 'IMO9234568', '419567890', 'Bulk', 140.0, 22.0, 8.5, 12000, 'Fertilizer', 10000, 3),
(31, 'VLCC INDIA', 'IMO9345679', '249678901', 'Tanker', 350.0, 60.0, 23.0, 320000, 'Crude Oil', 2500000, 1),
(32, 'AFRAMAX STAR', 'IMO9456780', '538789012', 'Tanker', 244.0, 42.0, 14.9, 105000, 'Crude Oil', 750000, 2),
(33, 'MR TANKER MUMBAI', 'IMO9567891', '477890123', 'Tanker', 183.0, 32.2, 12.5, 45000, 'Clean Products', 50000, 2),
(34, 'CHEMICAL PIONEER', 'IMO9678902', '636901234', 'Tanker', 175.0, 30.0, 11.8, 32000, 'Chemicals', 35000, 2),
(35, 'LNG MUMBAI', 'IMO9789013', '353012345', 'Tanker', 290.0, 46.0, 12.0, 95000, 'LNG', 170000, 1),
(36, 'MULTIPURPOSE INDIA', 'IMO9890124', '419123456', 'General', 175.0, 27.5, 10.8, 20000, 'Breakbulk', 16000, 2),
(37, 'RORO PIONEER', 'IMO9901235', '538234567', 'RoRo', 200.0, 32.0, 9.5, 35000, 'Vehicles', 5000, 2),
(38, 'CAR CARRIER INDIA', 'IMO9012346', '477345678', 'RoRo', 199.0, 36.5, 10.2, 55000, 'Vehicles', 6500, 2),
(39, 'REEFER EXPRESS', 'IMO9123457', '636456789', 'Reefer', 160.0, 25.0, 9.0, 15000, 'Perishables', 12000, 1),
(40, 'FROZEN MUMBAI', 'IMO9234568', '353567890', 'Reefer', 145.0, 22.0, 8.5, 10000, 'Frozen Goods', 8000, 2),
(41, 'OFFSHORE SUPPLY 1', 'IMO9345679', '419678901', 'Offshore', 85.0, 20.0, 6.5, 4500, 'Supplies', 3000, 2),
(42, 'TUG MUMBAI', 'IMO9456780', '538789012', 'Tug', 35.0, 12.0, 5.0, 800, 'N/A', 0, 3),
(43, 'CRUISE INDIA', 'IMO9567891', '249890123', 'Passenger', 330.0, 38.0, 8.5, 140000, 'Passengers', 4000, 1),
(44, 'FERRY GATEWAY', 'IMO9678902', '477901234', 'Passenger', 120.0, 22.0, 5.5, 8000, 'Passengers', 800, 2),
(45, 'DREDGER MUMBAI', 'IMO9789013', '419012345', 'Dredger', 120.0, 24.0, 7.5, 10000, 'Dredging', 8000, 3),
(46, 'CEMENT CARRIER 1', 'IMO9890124', '538123456', 'Bulk', 180.0, 28.0, 10.5, 30000, 'Cement', 28000, 2),
(47, 'TIMBER TRADER', 'IMO9901235', '636234567', 'General', 140.0, 22.0, 8.0, 8000, 'Timber', 6000, 3),
(48, 'CONTAINER FEEDER 1', 'IMO9012346', '353345678', 'Container', 180.0, 28.0, 10.0, 18000, 'Container', 1800, 3),
(49, 'BITUMEN TANKER', 'IMO9123457', '477456789', 'Tanker', 155.0, 26.0, 9.5, 12000, 'Bitumen', 14000, 2),
(50, 'MOLASSES CARRIER', 'IMO9234568', '419567890', 'Tanker', 145.0, 24.0, 8.5, 9000, 'Molasses', 10000, 3);
SET IDENTITY_INSERT dbo.VESSELS OFF;
GO

-- Insert Resources
SET IDENTITY_INSERT dbo.RESOURCES ON;
INSERT INTO dbo.RESOURCES (ResourceId, ResourceName, ResourceType, Capacity, Status) VALUES
(1, 'Pilot Team Alpha', 'Pilot', 1, 'Available'),
(2, 'Pilot Team Beta', 'Pilot', 1, 'Available'),
(3, 'Pilot Team Gamma', 'Pilot', 1, 'Available'),
(4, 'Senior Pilot - Deep Draft', 'Pilot', 1, 'Available'),
(5, 'Pilot Team Delta', 'Pilot', 1, 'Available'),
(6, 'Night Pilot Team', 'Pilot', 1, 'Available'),
(7, 'TUG Mahul', 'Tugboat', 60, 'Available'),
(8, 'TUG Prabodhan', 'Tugboat', 50, 'Available'),
(9, 'TUG Jawahar', 'Tugboat', 55, 'Available'),
(10, 'TUG Pragati', 'Tugboat', 45, 'Available'),
(11, 'TUG Mumbai', 'Tugboat', 70, 'Available'),
(12, 'TUG Gateway', 'Tugboat', 65, 'Available'),
(13, 'TUG Coastal', 'Tugboat', 40, 'Available'),
(14, 'TUG Harbor', 'Tugboat', 35, 'Available'),
(15, 'Gantry Crane GC-01', 'Crane', 65, 'Available'),
(16, 'Gantry Crane GC-02', 'Crane', 65, 'Available'),
(17, 'Gantry Crane GC-03', 'Crane', 50, 'Available'),
(18, 'Gantry Crane GC-04', 'Crane', 70, 'Available'),
(19, 'Mobile Crane MC-01', 'Crane', 100, 'Available'),
(20, 'Mobile Crane MC-02', 'Crane', 80, 'Available'),
(21, 'Mobile Crane MC-03', 'Crane', 60, 'Available'),
(22, 'Grab Unloader GU-01', 'Crane', 2000, 'Available'),
(23, 'Grab Unloader GU-02', 'Crane', 1800, 'Available'),
(24, 'Ship Unloader SU-01', 'Crane', 2500, 'Available'),
(25, 'Labor Gang A', 'Labor', 25, 'Available'),
(26, 'Labor Gang B', 'Labor', 25, 'Available'),
(27, 'Labor Gang C', 'Labor', 20, 'Available'),
(28, 'Labor Gang D', 'Labor', 20, 'Available'),
(29, 'Night Shift Gang 1', 'Labor', 18, 'Available'),
(30, 'Night Shift Gang 2', 'Labor', 18, 'Available'),
(31, 'Specialized Tank Gang', 'Labor', 12, 'Available'),
(32, 'Hazmat Handling Team', 'Labor', 10, 'Available'),
(33, 'Mooring Team Alpha', 'Mooring', 6, 'Available'),
(34, 'Mooring Team Beta', 'Mooring', 6, 'Available'),
(35, 'Mooring Team Gamma', 'Mooring', 6, 'Available');
SET IDENTITY_INSERT dbo.RESOURCES OFF;
GO

-- Insert Weather Data
INSERT INTO dbo.WEATHER_DATA (WindSpeed, WindDirection, Visibility, WaveHeight, Temperature, Conditions, RecordedAt) VALUES
(12.5, 225.0, 8.5, 0.8, 28.5, 'Clear', DATEADD(HOUR, -1, GETUTCDATE())),
(15.0, 230.0, 7.0, 1.0, 27.8, 'Partly Cloudy', GETUTCDATE());
GO

-- Insert Tidal Data (next 48 hours)
DECLARE @BaseTime DATETIME2 = GETUTCDATE();
INSERT INTO dbo.TIDAL_DATA (TideType, TideHeight, TideTime, DraftRestriction) VALUES
('High', 4.5, DATEADD(HOUR, 2, @BaseTime), 18.0),
('Low', 1.2, DATEADD(HOUR, 8, @BaseTime), 11.5),
('High', 4.8, DATEADD(HOUR, 14, @BaseTime), 18.5),
('Low', 1.0, DATEADD(HOUR, 20, @BaseTime), 11.0),
('High', 4.6, DATEADD(HOUR, 26, @BaseTime), 18.2),
('Low', 1.3, DATEADD(HOUR, 32, @BaseTime), 11.8),
('High', 4.7, DATEADD(HOUR, 38, @BaseTime), 18.3),
('Low', 1.1, DATEADD(HOUR, 44, @BaseTime), 11.2);
GO

-- Insert Vessel Schedules (future arrivals)
DECLARE @Now DATETIME2 = GETUTCDATE();
SET IDENTITY_INSERT dbo.VESSEL_SCHEDULE ON;
INSERT INTO dbo.VESSEL_SCHEDULE (ScheduleId, VesselId, BerthId, ETA, PredictedETA, Status, Priority) VALUES
(1, 1, 4, DATEADD(HOUR, 4, @Now), DATEADD(HOUR, 4.5, @Now), 'Approaching', 1),
(2, 2, NULL, DATEADD(HOUR, 8, @Now), DATEADD(HOUR, 8.2, @Now), 'Scheduled', 1),
(3, 3, NULL, DATEADD(HOUR, 12, @Now), NULL, 'Scheduled', 2),
(4, 7, 6, DATEADD(HOUR, 6, @Now), DATEADD(HOUR, 5.8, @Now), 'Approaching', 2),
(5, 11, 9, DATEADD(HOUR, 10, @Now), DATEADD(HOUR, 10.5, @Now), 'Scheduled', 1),
(6, 13, NULL, DATEADD(HOUR, 16, @Now), NULL, 'Scheduled', 2),
(7, 16, 13, DATEADD(HOUR, 3, @Now), DATEADD(HOUR, 3, @Now), 'Approaching', 3),
(8, 21, NULL, DATEADD(HOUR, 20, @Now), NULL, 'Scheduled', 2),
(9, 26, NULL, DATEADD(HOUR, 24, @Now), NULL, 'Scheduled', 1),
(10, 39, NULL, DATEADD(HOUR, 14, @Now), NULL, 'Scheduled', 1);
SET IDENTITY_INSERT dbo.VESSEL_SCHEDULE OFF;
GO

-- Insert AIS Data (current positions)
DECLARE @AISTime DATETIME2 = GETUTCDATE();
INSERT INTO dbo.AIS_DATA (VesselId, MMSI, Latitude, Longitude, Speed, Course, Heading, NavigationStatus, RecordedAt) VALUES
(1, '219018000', 18.75, 72.65, 12.5, 45.0, 47.0, 'Under way using engine', @AISTime),
(2, '353128000', 18.50, 72.40, 14.0, 50.0, 52.0, 'Under way using engine', @AISTime),
(3, '416529000', 18.30, 72.20, 11.5, 48.0, 50.0, 'Under way using engine', @AISTime),
(7, '538005678', 18.80, 72.70, 10.0, 42.0, 44.0, 'Under way using engine', @AISTime),
(11, '249345678', 18.60, 72.50, 8.5, 55.0, 57.0, 'Under way using engine', @AISTime),
(16, '419234567', 18.88, 72.78, 9.0, 40.0, 42.0, 'Under way using engine', @AISTime),
(21, '416678901', 17.90, 71.80, 13.0, 52.0, 54.0, 'Under way using engine', @AISTime),
(26, '538123456', 17.50, 71.50, 11.0, 48.0, 50.0, 'Under way using engine', @AISTime),
(39, '636456789', 18.40, 72.30, 12.0, 46.0, 48.0, 'Under way using engine', @AISTime);
GO

-- Insert Knowledge Base entries
INSERT INTO dbo.KNOWLEDGE_BASE (Title, Content, Category, Tags) VALUES
('Berth Allocation Rules', 'Physical constraints: LOA <= max_loa, Beam <= max_beam, Draft <= max_draft. Cargo compatibility must match berth type. Priority order: Government > Liner > Perishable > Standard.', 'Operations', 'berth,allocation,constraints'),
('ETA Prediction Factors', 'Factors affecting ETA: AIS position and speed, weather conditions, tidal windows, port congestion, historical patterns. Weather impact can reduce speed by 5-15%.', 'Prediction', 'eta,prediction,factors'),
('Conflict Resolution', 'Conflict types: Berth overlap, Resource clash, Tidal conflict. Resolution options: Delay incoming, Shift berth, Adjust resources. Priority: Safety > High priority > Time-sensitive.', 'Conflicts', 'conflict,resolution,priority'),
('Tidal Operations', 'Deep draft vessels (>14m) require high tide windows. Channel navigation restricted during low tide. Daylight operations required for certain berths.', 'Operations', 'tidal,draft,navigation'),
('Weather Restrictions', 'Wind >25 knots: Suspend crane ops for large vessels. Visibility <0.5 NM: Delay pilot boarding. Wave >1.5m: Caution for berthing.', 'Weather', 'weather,wind,visibility');
GO

PRINT '=============================================';
PRINT 'SEED DATA LOADED SUCCESSFULLY!';
PRINT '=============================================';
PRINT 'Records inserted:';
PRINT '  - Ports: 1';
PRINT '  - Terminals: 8';
PRINT '  - Berths: 20';
PRINT '  - Vessels: 50';
PRINT '  - Resources: 35';
PRINT '  - Weather Data: 2';
PRINT '  - Tidal Data: 8';
PRINT '  - Vessel Schedules: 10';
PRINT '  - AIS Data: 9';
PRINT '  - Knowledge Base: 5';
PRINT '=============================================';
GO
