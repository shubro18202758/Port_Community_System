-- =============================================
-- SMARTBERTH AI - SEED DATA FOR MSSQL (FIXED)
-- Matches actual database schema
-- =============================================

USE BerthPlanning;
GO

-- Clear existing data (in correct order due to foreign keys)
DELETE FROM dbo.KNOWLEDGE_BASE;
DELETE FROM dbo.AIS_DATA;
DELETE FROM dbo.RESOURCE_ALLOCATION;
DELETE FROM dbo.CONFLICTS;
DELETE FROM dbo.VESSEL_SCHEDULE;
DELETE FROM dbo.TIDAL_DATA;
DELETE FROM dbo.WEATHER_DATA;
DELETE FROM dbo.RESOURCES;
DELETE FROM dbo.VESSELS;
DELETE FROM dbo.BERTHS;
DELETE FROM dbo.TERMINALS;
DELETE FROM dbo.PORTS;
GO

-- Reset identity seeds
DBCC CHECKIDENT ('PORTS', RESEED, 0);
DBCC CHECKIDENT ('TERMINALS', RESEED, 0);
DBCC CHECKIDENT ('BERTHS', RESEED, 0);
DBCC CHECKIDENT ('VESSELS', RESEED, 0);
DBCC CHECKIDENT ('RESOURCES', RESEED, 0);
DBCC CHECKIDENT ('VESSEL_SCHEDULE', RESEED, 0);
GO

-- Insert Port
SET IDENTITY_INSERT dbo.PORTS ON;
INSERT INTO dbo.PORTS (PortId, PortCode, PortName, Country, City, TimeZone, Latitude, Longitude, ContactEmail, ContactPhone, IsActive)
VALUES (1, 'INBOM', 'Mumbai Port Trust', 'India', 'Mumbai', 'Asia/Kolkata', 18.926, 72.8438, 'info@mumbaiport.gov.in', '+91-22-22617712', 1);
SET IDENTITY_INSERT dbo.PORTS OFF;
GO

-- Insert Terminals
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

-- Insert Berths (corrected column names: Length, Depth, MaxDraft, NumberOfCranes, BollardCount)
SET IDENTITY_INSERT dbo.BERTHS ON;
INSERT INTO dbo.BERTHS (BerthId, TerminalId, BerthCode, BerthName, Length, Depth, MaxDraft, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude) VALUES
(1, 1, 'IDCT-01', 'Indira Dock Berth 1', 300.0, 12.0, 11.0, 'Container', 3, 12, 1, 18.9271, 72.8446),
(2, 1, 'IDCT-02', 'Indira Dock Berth 2', 280.0, 11.5, 10.5, 'Container', 3, 10, 1, 18.9273, 72.8448),
(3, 1, 'IDCT-03', 'Indira Dock Berth 3', 250.0, 11.0, 10.0, 'Container', 2, 8, 1, 18.9275, 72.8450),
(4, 2, 'BPCT-01', 'Ballard Pier Berth 1', 320.0, 13.0, 12.0, 'Container', 4, 14, 1, 18.9321, 72.8411),
(5, 2, 'BPCT-02', 'Ballard Pier Berth 2', 290.0, 12.0, 11.0, 'Container', 3, 12, 1, 18.9323, 72.8413),
(6, 3, 'MBT-01', 'Bulk Berth 1', 280.0, 15.0, 14.0, 'Bulk', 2, 10, 1, 18.9241, 72.8461),
(7, 3, 'MBT-02', 'Bulk Berth 2', 250.0, 13.5, 12.5, 'Bulk', 2, 8, 1, 18.9243, 72.8463),
(8, 3, 'MBT-03', 'Bulk Berth 3', 220.0, 12.0, 11.0, 'Bulk', 1, 6, 1, 18.9245, 72.8465),
(9, 4, 'JDOT-01', 'Oil Jetty 1', 330.0, 20.0, 18.0, 'Liquid', 0, 8, 1, 18.9101, 72.8301),
(10, 4, 'JDOT-02', 'Oil Jetty 2', 300.0, 18.0, 16.0, 'Liquid', 0, 8, 1, 18.9103, 72.8303),
(11, 5, 'PPLT-01', 'Pir Pau Jetty 1', 200.0, 11.0, 10.0, 'Liquid', 0, 6, 1, 18.9051, 72.8351),
(12, 5, 'PPLT-02', 'Pir Pau Jetty 2', 180.0, 10.0, 9.0, 'Liquid', 0, 6, 1, 18.9053, 72.8353),
(13, 6, 'VDGC-01', 'Victoria Berth 1', 200.0, 10.5, 9.5, 'General', 2, 8, 1, 18.9351, 72.8421),
(14, 6, 'VDGC-02', 'Victoria Berth 2', 180.0, 10.0, 9.0, 'General', 1, 6, 1, 18.9353, 72.8423),
(15, 7, 'PDMP-01', 'Prince Dock Berth 1', 220.0, 11.0, 10.0, 'General', 2, 8, 1, 18.9381, 72.8401),
(16, 7, 'PDMP-02', 'Prince Dock Berth 2', 200.0, 10.5, 9.5, 'General', 2, 6, 1, 18.9383, 72.8403),
(17, 7, 'PDMP-03', 'Prince Dock Berth 3', 180.0, 10.0, 9.0, 'General', 1, 6, 1, 18.9385, 72.8405),
(18, 8, 'MCT-01', 'Cruise Terminal Berth 1', 350.0, 11.0, 10.0, 'Passenger', 0, 12, 1, 18.9401, 72.8381),
(19, 8, 'MCT-02', 'Cruise Terminal Berth 2', 280.0, 10.0, 9.0, 'Passenger', 0, 10, 1, 18.9403, 72.8383),
(20, 8, 'MCT-03', 'Ferry Terminal', 150.0, 7.0, 6.0, 'Passenger', 0, 4, 1, 18.9405, 72.8385);
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
(20, 'COASTAL TRADER', 'IMO9234567', '419345678', 'General', 120.0, 20.0, 7.5, 6000, 'General Cargo', 4500, 3),
(21, 'YANG MING VICTORY', 'IMO9345678', '416678901', 'Container', 324.0, 42.8, 14.0, 99000, 'Container', 8500, 2),
(22, 'ONE INDIA', 'IMO9456790', '431789012', 'Container', 336.0, 45.8, 14.5, 108000, 'Container', 10000, 2),
(23, 'HYUNDAI PIONEER', 'IMO9567892', '440890123', 'Container', 294.0, 32.3, 13.2, 75000, 'Container', 6500, 2),
(24, 'PIL MUMBAI', 'IMO9678903', '563901234', 'Container', 260.0, 32.3, 12.5, 55000, 'Container', 4800, 3),
(25, 'SINOKOR STAR', 'IMO9789014', '440012345', 'Container', 222.0, 30.0, 11.0, 35000, 'Container', 2800, 3),
(26, 'CAPE FORTUNE', 'IMO9890125', '538123456', 'Bulk', 299.0, 50.0, 18.5, 200000, 'Iron Ore', 195000, 1),
(27, 'MINERAL PRIDE', 'IMO9901236', '477234568', 'Bulk', 260.0, 43.0, 16.5, 120000, 'Coal', 115000, 2),
(28, 'GRAIN HARVEST', 'IMO9012347', '636345679', 'Bulk', 190.0, 32.3, 12.8, 45000, 'Grain', 42000, 2),
(29, 'BAUXITE EXPRESS', 'IMO9123458', '353456790', 'Bulk', 230.0, 38.0, 14.0, 75000, 'Bauxite', 72000, 2),
(30, 'COASTAL BULKER', 'IMO9234569', '419567891', 'Bulk', 140.0, 22.0, 8.5, 12000, 'Fertilizer', 10000, 3),
(31, 'VLCC INDIA', 'IMO9345680', '249678902', 'Tanker', 350.0, 60.0, 23.0, 320000, 'Crude Oil', 2500000, 1),
(32, 'AFRAMAX STAR', 'IMO9456791', '538789013', 'Tanker', 244.0, 42.0, 14.9, 105000, 'Crude Oil', 750000, 2),
(33, 'MR TANKER MUMBAI', 'IMO9567893', '477890124', 'Tanker', 183.0, 32.2, 12.5, 45000, 'Clean Products', 50000, 2),
(34, 'CHEMICAL PIONEER', 'IMO9678904', '636901235', 'Tanker', 175.0, 30.0, 11.8, 32000, 'Chemicals', 35000, 2),
(35, 'LNG MUMBAI', 'IMO9789015', '353012346', 'Tanker', 290.0, 46.0, 12.0, 95000, 'LNG', 170000, 1),
(36, 'MULTIPURPOSE INDIA', 'IMO9890126', '419123457', 'General', 175.0, 27.5, 10.8, 20000, 'Breakbulk', 16000, 2),
(37, 'RORO PIONEER', 'IMO9901237', '538234568', 'RoRo', 200.0, 32.0, 9.5, 35000, 'Vehicles', 5000, 2),
(38, 'CAR CARRIER INDIA', 'IMO9012348', '477345679', 'RoRo', 199.0, 36.5, 10.2, 55000, 'Vehicles', 6500, 2),
(39, 'REEFER EXPRESS', 'IMO9123459', '636456790', 'Reefer', 160.0, 25.0, 9.0, 15000, 'Perishables', 12000, 1),
(40, 'FROZEN MUMBAI', 'IMO9234570', '353567891', 'Reefer', 145.0, 22.0, 8.5, 10000, 'Frozen Goods', 8000, 2),
(41, 'OFFSHORE SUPPLY 1', 'IMO9345681', '419678902', 'Offshore', 85.0, 20.0, 6.5, 4500, 'Supplies', 3000, 2),
(42, 'TUG MUMBAI', 'IMO9456792', '538789013', 'Tug', 35.0, 12.0, 5.0, 800, 'N/A', 0, 3),
(43, 'CRUISE INDIA', 'IMO9567894', '249890124', 'Passenger', 330.0, 38.0, 8.5, 140000, 'Passengers', 4000, 1),
(44, 'FERRY GATEWAY', 'IMO9678905', '477901235', 'Passenger', 120.0, 22.0, 5.5, 8000, 'Passengers', 800, 2),
(45, 'DREDGER MUMBAI', 'IMO9789016', '419012346', 'Dredger', 120.0, 24.0, 7.5, 10000, 'Dredging', 8000, 3),
(46, 'CEMENT CARRIER 1', 'IMO9890127', '538123457', 'Bulk', 180.0, 28.0, 10.5, 30000, 'Cement', 28000, 2),
(47, 'TIMBER TRADER', 'IMO9901238', '636234568', 'General', 140.0, 22.0, 8.0, 8000, 'Timber', 6000, 3),
(48, 'CONTAINER FEEDER 1', 'IMO9012349', '353345679', 'Container', 180.0, 28.0, 10.0, 18000, 'Container', 1800, 3),
(49, 'BITUMEN TANKER', 'IMO9123460', '477456790', 'Tanker', 155.0, 26.0, 9.5, 12000, 'Bitumen', 14000, 2),
(50, 'MOLASSES CARRIER', 'IMO9234571', '419567892', 'Tanker', 145.0, 24.0, 8.5, 9000, 'Molasses', 10000, 3);
SET IDENTITY_INSERT dbo.VESSELS OFF;
GO

-- Insert Resources (corrected: IsAvailable instead of Status)
SET IDENTITY_INSERT dbo.RESOURCES ON;
INSERT INTO dbo.RESOURCES (ResourceId, ResourceName, ResourceType, Capacity, IsAvailable) VALUES
(1, 'Pilot Team Alpha', 'Pilot', 1, 1),
(2, 'Pilot Team Beta', 'Pilot', 1, 1),
(3, 'Pilot Team Gamma', 'Pilot', 1, 1),
(4, 'Senior Pilot - Deep Draft', 'Pilot', 1, 1),
(5, 'Pilot Team Delta', 'Pilot', 1, 1),
(6, 'Night Pilot Team', 'Pilot', 1, 1),
(7, 'TUG Mahul', 'Tugboat', 60, 1),
(8, 'TUG Prabodhan', 'Tugboat', 50, 1),
(9, 'TUG Jawahar', 'Tugboat', 55, 1),
(10, 'TUG Pragati', 'Tugboat', 45, 1),
(11, 'TUG Mumbai', 'Tugboat', 70, 1),
(12, 'TUG Gateway', 'Tugboat', 65, 1),
(13, 'TUG Coastal', 'Tugboat', 40, 1),
(14, 'TUG Harbor', 'Tugboat', 35, 1),
(15, 'Gantry Crane GC-01', 'Crane', 65, 1),
(16, 'Gantry Crane GC-02', 'Crane', 65, 1),
(17, 'Gantry Crane GC-03', 'Crane', 50, 1),
(18, 'Gantry Crane GC-04', 'Crane', 70, 1),
(19, 'Mobile Crane MC-01', 'Crane', 100, 1),
(20, 'Mobile Crane MC-02', 'Crane', 80, 1),
(21, 'Mobile Crane MC-03', 'Crane', 60, 1),
(22, 'Grab Unloader GU-01', 'Crane', 2000, 1),
(23, 'Grab Unloader GU-02', 'Crane', 1800, 1),
(24, 'Ship Unloader SU-01', 'Crane', 2500, 1),
(25, 'Labor Gang A', 'Labor', 25, 1),
(26, 'Labor Gang B', 'Labor', 25, 1),
(27, 'Labor Gang C', 'Labor', 20, 1),
(28, 'Labor Gang D', 'Labor', 20, 1),
(29, 'Night Shift Gang 1', 'Labor', 18, 1),
(30, 'Night Shift Gang 2', 'Labor', 18, 1),
(31, 'Specialized Tank Gang', 'Labor', 12, 1),
(32, 'Hazmat Handling Team', 'Labor', 10, 1),
(33, 'Mooring Team Alpha', 'Mooring', 6, 1),
(34, 'Mooring Team Beta', 'Mooring', 6, 1),
(35, 'Mooring Team Gamma', 'Mooring', 6, 1);
SET IDENTITY_INSERT dbo.RESOURCES OFF;
GO

-- Insert Weather Data (corrected: WeatherCondition instead of Conditions)
INSERT INTO dbo.WEATHER_DATA (WindSpeed, WindDirection, Visibility, WaveHeight, Temperature, Precipitation, WeatherCondition, IsAlert, RecordedAt) VALUES
(12.5, 225.0, 8.5, 0.8, 28.5, 0.0, 'Clear', 0, DATEADD(HOUR, -1, GETUTCDATE())),
(15.0, 230.0, 7.0, 1.0, 27.8, 0.0, 'Partly Cloudy', 0, GETUTCDATE());
GO

-- Insert Tidal Data (corrected: Height instead of TideHeight, removed DraftRestriction)
DECLARE @BaseTime DATETIME2 = GETUTCDATE();
INSERT INTO dbo.TIDAL_DATA (TideType, Height, TideTime) VALUES
('High', 4.5, DATEADD(HOUR, 2, @BaseTime)),
('Low', 1.2, DATEADD(HOUR, 8, @BaseTime)),
('High', 4.8, DATEADD(HOUR, 14, @BaseTime)),
('Low', 1.0, DATEADD(HOUR, 20, @BaseTime)),
('High', 4.6, DATEADD(HOUR, 26, @BaseTime)),
('Low', 1.3, DATEADD(HOUR, 32, @BaseTime)),
('High', 4.7, DATEADD(HOUR, 38, @BaseTime)),
('Low', 1.1, DATEADD(HOUR, 44, @BaseTime));
GO

-- Insert Vessel Schedules (removed Priority column)
DECLARE @Now DATETIME2 = GETUTCDATE();
SET IDENTITY_INSERT dbo.VESSEL_SCHEDULE ON;
INSERT INTO dbo.VESSEL_SCHEDULE (ScheduleId, VesselId, BerthId, ETA, PredictedETA, Status) VALUES
(1, 1, 4, DATEADD(HOUR, 4, @Now), DATEADD(MINUTE, 270, @Now), 'Approaching'),
(2, 2, NULL, DATEADD(HOUR, 8, @Now), DATEADD(MINUTE, 492, @Now), 'Scheduled'),
(3, 3, NULL, DATEADD(HOUR, 12, @Now), NULL, 'Scheduled'),
(4, 7, 6, DATEADD(HOUR, 6, @Now), DATEADD(MINUTE, 348, @Now), 'Approaching'),
(5, 11, 9, DATEADD(HOUR, 10, @Now), DATEADD(MINUTE, 630, @Now), 'Scheduled'),
(6, 13, NULL, DATEADD(HOUR, 16, @Now), NULL, 'Scheduled'),
(7, 16, 13, DATEADD(HOUR, 3, @Now), DATEADD(HOUR, 3, @Now), 'Approaching'),
(8, 21, NULL, DATEADD(HOUR, 20, @Now), NULL, 'Scheduled'),
(9, 26, NULL, DATEADD(HOUR, 24, @Now), NULL, 'Scheduled'),
(10, 39, NULL, DATEADD(HOUR, 14, @Now), NULL, 'Scheduled');
SET IDENTITY_INSERT dbo.VESSEL_SCHEDULE OFF;
GO

-- Insert AIS Data
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
(39, '636456790', 18.40, 72.30, 12.0, 46.0, 48.0, 'Under way using engine', @AISTime);
GO

-- Insert Knowledge Base entries (corrected: DocumentType, Metadata instead of Category, Tags)
INSERT INTO dbo.KNOWLEDGE_BASE (DocumentType, Title, Content, Metadata) VALUES
('Operations', 'Berth Allocation Rules', 'Physical constraints: LOA <= max_loa, Beam <= max_beam, Draft <= max_draft. Cargo compatibility must match berth type. Priority order: Government > Liner > Perishable > Standard.', '{"tags": ["berth","allocation","constraints"]}'),
('Prediction', 'ETA Prediction Factors', 'Factors affecting ETA: AIS position and speed, weather conditions, tidal windows, port congestion, historical patterns. Weather impact can reduce speed by 5-15%.', '{"tags": ["eta","prediction","factors"]}'),
('Conflicts', 'Conflict Resolution', 'Conflict types: Berth overlap, Resource clash, Tidal conflict. Resolution options: Delay incoming, Shift berth, Adjust resources. Priority: Safety > High priority > Time-sensitive.', '{"tags": ["conflict","resolution","priority"]}'),
('Operations', 'Tidal Operations', 'Deep draft vessels (>14m) require high tide windows. Channel navigation restricted during low tide. Daylight operations required for certain berths.', '{"tags": ["tidal","draft","navigation"]}'),
('Weather', 'Weather Restrictions', 'Wind >25 knots: Suspend crane ops for large vessels. Visibility <0.5 NM: Delay pilot boarding. Wave >1.5m: Caution for berthing.', '{"tags": ["weather","wind","visibility"]}'),
('Procedures', 'Pilotage Requirements', 'Vessels >200m LOA require two pilots. Deep draft vessels >18m require senior pilot. Night pilotage restricted for first-time callers.', '{"tags": ["pilot","requirements","safety"]}'),
('Resources', 'Tugboat Requirements', 'Container vessels >300m: 2 tugs required. VLCC/ULCC: 3 tugs required. All tankers: Fire tug standby mandatory.', '{"tags": ["tugboat","requirements","safety"]}'),
('Operations', 'Cargo Handling', 'Container discharge rate: 25-35 moves/hour. Bulk discharge: 1500-2500 TPH. Liquid cargo: Flow rate based on pipeline specs.', '{"tags": ["cargo","handling","productivity"]}');
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
PRINT '  - Knowledge Base: 8';
PRINT '=============================================';
GO
