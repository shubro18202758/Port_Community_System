-- ============================================
-- Berth Planning System - Seed Data: VESSELS
-- 50 Realistic Vessel Records for Mumbai Port
-- ============================================

-- Clear existing data
DELETE FROM VESSELS;
DBCC CHECKIDENT ('VESSELS', RESEED, 0);

-- Insert Vessels
INSERT INTO VESSELS (VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, Priority)
VALUES
-- Container Vessels (Large)
('MSC MUMBAI', 'IMO9703291', '353136000', 'Container', 295.00, 42.00, 11.00, 95000, 'Containers', 8500.00, 1),
('MAERSK INDIA', 'IMO9778791', '219123456', 'Container', 280.00, 40.00, 10.50, 85000, 'Containers', 7800.00, 1),
('CMA CGM GANGES', 'IMO9839179', '228123456', 'Container', 275.00, 42.00, 10.00, 82000, 'Containers', 7500.00, 1),

-- Container Vessels (Medium)
('EVERGREEN ARABIAN', 'IMO9811000', '416234567', 'Container', 250.00, 35.00, 10.00, 65000, 'Containers', 5500.00, 2),
('HAPAG GATEWAY', 'IMO9776163', '218123456', 'Container', 245.00, 34.00, 9.80, 60000, 'Containers', 5200.00, 2),
('ONE COMPETENCE', 'IMO9806163', '351123456', 'Container', 240.00, 34.00, 9.50, 58000, 'Containers', 5000.00, 2),
('ZIM PACIFIC', 'IMO9813348', '428123456', 'Container', 235.00, 33.00, 9.50, 55000, 'Containers', 4800.00, 2),
('PIL MUMBAI', 'IMO9410727', '564123456', 'Container', 220.00, 32.00, 9.00, 48000, 'Containers', 4200.00, 2),

-- Container Vessels (Small/Feeder)
('COASTAL FEEDER I', 'IMO9100001', '215123456', 'Container', 170.00, 27.00, 8.50, 18000, 'Containers', 1700.00, 3),
('COASTAL FEEDER II', 'IMO9100002', '224123456', 'Container', 155.00, 25.00, 8.00, 12500, 'Containers', 1100.00, 3),
('GUJARAT EXPRESS', 'IMO9100003', '235123456', 'Container', 145.00, 22.00, 7.50, 9500, 'Containers', 850.00, 3),
('ARABIAN TRADER', 'IMO9100004', '246123456', 'Container', 130.00, 20.00, 7.00, 7000, 'Containers', 600.00, 3),

-- Bulk Carriers (Large)
('INDIAN GLORY', 'IMO9478762', '538123456', 'Bulk', 280.00, 45.00, 12.50, 95000, 'Iron Ore', 95000.00, 1),
('MUMBAI BULKER', 'IMO8404654', '538234567', 'Bulk', 265.00, 43.00, 12.00, 85000, 'Coal', 85000.00, 1),
('WESTERN CAPE', 'IMO9761640', '477345678', 'Bulk', 250.00, 40.00, 11.50, 75000, 'Iron Ore', 75000.00, 1),

-- Bulk Carriers (Medium)
('GRAIN STAR', 'IMO9200003', '352123456', 'Bulk', 225.00, 32.00, 11.00, 65000, 'Grain', 65000.00, 2),
('COAL CARRIER I', 'IMO9200004', '477456789', 'Bulk', 220.00, 32.00, 10.80, 60000, 'Coal', 60000.00, 2),
('BAUXITE EXPRESS', 'IMO9200005', '538456789', 'Bulk', 215.00, 31.00, 10.50, 55000, 'Bauxite', 55000.00, 2),
('FERTILIZER KING', 'IMO9200006', '352345678', 'Bulk', 210.00, 30.00, 10.20, 50000, 'Fertilizer', 50000.00, 2),

-- Bulk Carriers (Small)
('COASTAL BULK', 'IMO9200008', '538567890', 'Bulk', 180.00, 28.00, 9.50, 35000, 'Steel Products', 35000.00, 3),
('MINI BULKER', 'IMO9200009', '352456789', 'Bulk', 165.00, 25.00, 9.00, 25000, 'Cement', 25000.00, 3),

-- Tankers (VLCC/Suezmax)
('ARABIAN CRUDE', 'IMO9806182', '538789012', 'Tanker', 333.00, 60.00, 17.00, 159000, 'Crude Oil', 280000.00, 1),
('PERSIAN STAR', 'IMO9399082', '538890123', 'Tanker', 320.00, 56.00, 16.00, 145000, 'Crude Oil', 250000.00, 1),
('GULF CARRIER', 'IMO9484300', '205123456', 'Tanker', 300.00, 50.00, 15.00, 120000, 'Crude Oil', 200000.00, 1),

-- Tankers (Aframax/Product)
('INDIAN TANKER', 'IMO9595511', '352678901', 'Tanker', 250.00, 44.00, 13.00, 95000, 'Crude Oil', 100000.00, 2),
('DIESEL CARRIER', 'IMO9706622', '538901234', 'Tanker', 230.00, 40.00, 12.00, 75000, 'Refined Products', 75000.00, 2),
('CHEMICAL PIONEER', 'IMO9300001', '477789012', 'Tanker', 183.00, 32.00, 11.00, 45000, 'Chemicals', 45000.00, 2),
('PRODUCT CARRIER', 'IMO9300002', '352789012', 'Tanker', 170.00, 30.00, 10.50, 38000, 'Refined Products', 38000.00, 2),

-- Tankers (Small/LPG)
('LPG MUMBAI', 'IMO9300005', '352890123', 'Tanker', 200.00, 35.00, 10.00, 45000, 'LPG', 65000.00, 2),
('BUNKER SUPPLIER', 'IMO9300007', '477901234', 'Tanker', 120.00, 20.00, 7.50, 8000, 'Marine Fuel', 10000.00, 3),
('COASTAL TANKER', 'IMO9300006', '538123457', 'Tanker', 140.00, 24.00, 8.50, 15000, 'Refined Products', 18000.00, 3),

-- General Cargo
('MULTI PURPOSE I', 'IMO9500001', '209123456', 'General', 150.00, 24.00, 8.50, 18000, 'Mixed Cargo', 15000.00, 3),
('BREAKBULK INDIA', 'IMO9500002', '210123456', 'General', 160.00, 26.00, 9.00, 22000, 'Steel/Machinery', 18000.00, 2),
('PROJECT CARRIER', 'IMO9500003', '211123456', 'General', 175.00, 30.00, 9.50, 32000, 'Heavy Lift', 25000.00, 2),
('MUMBAI TRADER', 'IMO9500004', '212123456', 'General', 140.00, 22.00, 8.00, 12000, 'Mixed Cargo', 10000.00, 3),
('HEAVY LIFT STAR', 'IMO9500005', '213123456', 'General', 165.00, 38.00, 8.50, 40000, 'Heavy Lift', 50000.00, 1),
('REEFER EXPRESS', 'IMO9500006', '214123456', 'General', 145.00, 21.00, 8.00, 13000, 'Refrigerated', 350000.00, 2),

-- RoRo / Car Carriers
('AUTO INDIA', 'IMO9884400', '257234567', 'RoRo', 195.00, 32.00, 9.00, 55000, 'Vehicles', 6500.00, 2),
('CAR CARRIER I', 'IMO9995511', '265123456', 'RoRo', 185.00, 32.00, 8.80, 48000, 'Vehicles', 5500.00, 2),
('VEHICLE EXPRESS', 'IMO9400001', '440234567', 'RoRo', 180.00, 31.00, 8.50, 42000, 'Vehicles', 5000.00, 3),
('RORO MUMBAI', 'IMO9400002', '440345678', 'RoRo', 170.00, 30.00, 8.20, 38000, 'Vehicles', 4500.00, 3),

-- Passenger/Cruise
('MUMBAI QUEEN', 'IMO9600050', '310123456', 'Passenger', 300.00, 35.00, 8.00, 90000, 'Passengers', 2500.00, 1),
('ARABIAN STAR CRUISE', 'IMO9600051', '311123456', 'Passenger', 280.00, 32.00, 7.80, 75000, 'Passengers', 2000.00, 1),
('COASTAL CRUISE', 'IMO9600052', '312123456', 'Passenger', 200.00, 28.00, 7.00, 40000, 'Passengers', 1200.00, 2),

-- Additional Vessels for variety
('SINGAPORE BRIDGE', 'IMO9600029', '563123456', 'Container', 270.00, 40.00, 10.20, 78000, 'Containers', 7200.00, 1),
('HONG KONG TRADER', 'IMO9600030', '477012345', 'Container', 265.00, 38.00, 10.00, 72000, 'Containers', 6800.00, 2),
('DUBAI EXPRESS', 'IMO9600031', '413123456', 'Container', 255.00, 37.00, 9.80, 68000, 'Containers', 6200.00, 2),
('ARABIAN BULK', 'IMO9600009', '229123456', 'Bulk', 230.00, 35.00, 11.20, 70000, 'Coal', 70000.00, 2),
('IRON ORE CARRIER', 'IMO9600010', '230123456', 'Bulk', 235.00, 36.00, 11.50, 72000, 'Iron Ore', 72000.00, 2),
('CRUDE TANKER II', 'IMO9600014', '234123456', 'Tanker', 270.00, 46.00, 14.00, 100000, 'Crude Oil', 150000.00, 2);

-- Display count
SELECT 'Vessels inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM VESSELS;

-- Display by type
SELECT VesselType, COUNT(*) AS Count FROM VESSELS GROUP BY VesselType ORDER BY Count DESC;
