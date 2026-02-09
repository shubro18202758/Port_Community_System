-- =============================================
-- SEED DATA: VESSELS (60 vessels)
-- All vessels fit within berth limits
-- =============================================

USE [BerthPlanning];
GO

SET NOCOUNT ON;
PRINT '=== SEEDING VESSELS ===';

-- Container Ships (15 vessels) - fit Container berths (MaxLOA=420, MaxBeam=65, MaxDraft=18)
INSERT INTO VESSELS (VesselName, IMO, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, CargoUnit, Priority, FlagState, FlagStateName) VALUES
(N'Maersk Horizon', N'9621546', N'Container Ship', 325.6, 53.3, 13.25, 86421, N'Containers', 4180, N'TEU', 1, N'DK', N'Denmark'),
(N'COSCO Fortune', N'9557925', N'Container Ship', 350.7, 50.4, 12.78, 80668, N'Containers', 5219, N'TEU', 1, N'CN', N'China'),
(N'CMA CGM Pride', N'9385320', N'Container Ship', 352.8, 48.6, 11.97, 107154, N'Containers', 4864, N'TEU', 1, N'FR', N'France'),
(N'HMM Marvel', N'9878001', N'Container Ship', 282.0, 50.2, 12.09, 75000, N'Containers', 3800, N'TEU', 1, N'KR', N'South Korea'),
(N'Yang Ming Spirit', N'9462058', N'Container Ship', 346.5, 48.2, 13.12, 90000, N'Containers', 4500, N'TEU', 1, N'TW', N'Taiwan'),
(N'MSC Oscar', N'9703291', N'Container Ship', 395.4, 59.0, 16.00, 192237, N'Containers', 8500, N'TEU', 1, N'PA', N'Panama'),
(N'ONE Innovation', N'9806043', N'Container Ship', 364.0, 51.0, 14.50, 140000, N'Containers', 6000, N'TEU', 1, N'JP', N'Japan'),
(N'Evergreen Ever', N'9811000', N'Container Ship', 400.0, 58.8, 14.50, 170000, N'Containers', 7500, N'TEU', 1, N'PA', N'Panama'),
(N'Hapag Express', N'9706891', N'Container Ship', 368.0, 51.0, 14.00, 142000, N'Containers', 6500, N'TEU', 1, N'DE', N'Germany'),
(N'PIL Voyage', N'9450611', N'Container Ship', 275.0, 40.0, 12.00, 52000, N'Containers', 2800, N'TEU', 2, N'SG', N'Singapore'),
(N'ZIM Trader', N'9517764', N'Container Ship', 294.0, 32.3, 11.50, 41000, N'Containers', 2500, N'TEU', 2, N'IL', N'Israel'),
(N'Wan Hai Fortune', N'9461900', N'Container Ship', 255.0, 37.0, 10.50, 35000, N'Containers', 2000, N'TEU', 2, N'TW', N'Taiwan'),
(N'TS Lines Glory', N'9300881', N'Container Ship', 222.0, 30.0, 10.00, 25000, N'Containers', 1500, N'TEU', 2, N'TW', N'Taiwan'),
(N'SITC Pioneer', N'9402512', N'Container Ship', 182.0, 28.0, 9.50, 18000, N'Containers', 1200, N'TEU', 2, N'HK', N'Hong Kong'),
(N'Sinokor Seoul', N'9521890', N'Container Ship', 175.0, 27.0, 9.00, 16000, N'Containers', 1000, N'TEU', 2, N'KR', N'South Korea');

PRINT 'Inserted: 15 Container Ships';

-- Tankers/VLCC (12 vessels) - fit Liquid Bulk berths (MaxLOA=380, MaxBeam=70, MaxDraft=25)
INSERT INTO VESSELS (VesselName, IMO, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, CargoUnit, Priority, FlagState, FlagStateName) VALUES
(N'MT Arabian Glory', N'9468074', N'Tanker', 279.3, 49.2, 13.42, 112991, N'Crude Oil', 98107, N'MT', 1, N'SG', N'Singapore'),
(N'MT Delta Spirit', N'9157443', N'Tanker', 333.0, 60.0, 21.00, 160000, N'Crude Oil', 200000, N'MT', 1, N'LR', N'Liberia'),
(N'MT Navigator', N'9550797', N'Tanker', 295.0, 50.8, 18.67, 85000, N'Vegetable Oil', 90000, N'MT', 1, N'PA', N'Panama'),
(N'MT Pioneer', N'9312505', N'Tanker', 248.3, 55.2, 18.28, 75000, N'Chemicals', 80000, N'MT', 1, N'MH', N'Marshall Islands'),
(N'MT Valor Eagle', N'9299055', N'Tanker', 265.4, 57.8, 16.97, 95000, N'Crude Oil', 100000, N'MT', 1, N'BS', N'Bahamas'),
(N'MT Gulf Falcon', N'9770532', N'Tanker', 289.3, 48.5, 20.01, 110000, N'LPG', 120000, N'MT', 1, N'PA', N'Panama'),
(N'MT Endurance', N'9843201', N'Tanker', 326.8, 58.4, 20.88, 150000, N'Crude Oil', 180000, N'MT', 1, N'GR', N'Greece'),
(N'MT Horizon Star', N'9621789', N'Tanker', 274.0, 48.0, 16.00, 80000, N'Petroleum', 85000, N'MT', 2, N'MT', N'Malta'),
(N'MT Ocean Pride', N'9445123', N'Tanker', 250.0, 44.0, 14.50, 60000, N'Diesel', 65000, N'MT', 2, N'CY', N'Cyprus'),
(N'MT Sea Venture', N'9398765', N'Tanker', 228.0, 42.0, 13.00, 45000, N'Chemicals', 50000, N'MT', 2, N'NL', N'Netherlands'),
(N'MT Coastal Star', N'9287654', N'Tanker', 185.0, 32.0, 11.50, 30000, N'Bitumen', 35000, N'MT', 2, N'IN', N'India'),
(N'MT River Queen', N'9176543', N'Tanker', 145.0, 23.0, 9.00, 12000, N'Vegetable Oil', 15000, N'MT', 2, N'IN', N'India');

PRINT 'Inserted: 12 Tankers';

-- Bulk Carriers (12 vessels) - fit Dry Bulk berths (MaxLOA=380, MaxBeam=65, MaxDraft=22)
INSERT INTO VESSELS (VesselName, IMO, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, CargoUnit, Priority, FlagState, FlagStateName) VALUES
(N'MV Iron Carrier', N'9932250', N'Bulk Carrier', 279.7, 45.0, 17.74, 92000, N'Iron Ore', 180000, N'MT', 1, N'CN', N'China'),
(N'MV Coal Express', N'9851001', N'Bulk Carrier', 299.0, 50.0, 18.50, 95000, N'Coal', 175000, N'MT', 1, N'PA', N'Panama'),
(N'MV Grain Glory', N'9765432', N'Bulk Carrier', 225.0, 32.2, 14.20, 55000, N'Grain', 65000, N'MT', 1, N'LR', N'Liberia'),
(N'MV Steel Pioneer', N'9654321', N'Bulk Carrier', 260.0, 43.0, 16.00, 75000, N'Steel Coils', 80000, N'MT', 1, N'MH', N'Marshall Islands'),
(N'MV Cement Star', N'9543210', N'Bulk Carrier', 180.0, 30.0, 11.00, 28000, N'Cement', 35000, N'MT', 2, N'IN', N'India'),
(N'MV Fertilizer King', N'9432109', N'Bulk Carrier', 200.0, 32.0, 12.50, 40000, N'Fertilizer', 50000, N'MT', 2, N'BS', N'Bahamas'),
(N'MV Bauxite Trader', N'9321098', N'Bulk Carrier', 250.0, 43.0, 15.00, 70000, N'Bauxite', 85000, N'MT', 1, N'HK', N'Hong Kong'),
(N'MV Copper Queen', N'9210987', N'Bulk Carrier', 235.0, 38.0, 14.00, 58000, N'Copper Ore', 70000, N'MT', 2, N'CY', N'Cyprus'),
(N'MV Manganese Express', N'9109876', N'Bulk Carrier', 220.0, 36.0, 13.50, 52000, N'Manganese', 60000, N'MT', 2, N'SG', N'Singapore'),
(N'MV Limestone Majesty', N'9008765', N'Bulk Carrier', 190.0, 32.0, 11.50, 35000, N'Limestone', 42000, N'MT', 2, N'IN', N'India'),
(N'MV Salt Carrier', N'8907654', N'Bulk Carrier', 160.0, 26.0, 9.50, 18000, N'Salt', 22000, N'MT', 2, N'IN', N'India'),
(N'MV Clinker Star', N'8806543', N'Bulk Carrier', 175.0, 28.0, 10.50, 25000, N'Clinker', 30000, N'MT', 2, N'BD', N'Bangladesh');

PRINT 'Inserted: 12 Bulk Carriers';

-- LNG Carriers (6 vessels) - fit LNG berths (MaxLOA=380, MaxBeam=60, MaxDraft=15)
INSERT INTO VESSELS (VesselName, IMO, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, CargoUnit, Priority, FlagState, FlagStateName) VALUES
(N'LNG Simaisma', N'9656251', N'LNG Carrier', 288.9, 45.4, 10.93, 127290, N'LNG', 102517, N'CBM', 1, N'MH', N'Marshall Islands'),
(N'LNG Mundra', N'9958729', N'LNG Carrier', 295.2, 50.0, 11.20, 140000, N'LNG', 170000, N'CBM', 1, N'IN', N'India'),
(N'LNG Dahej', N'9878086', N'LNG Carrier', 284.8, 46.9, 10.97, 130000, N'LNG', 155000, N'CBM', 1, N'IN', N'India'),
(N'LNG Hazira', N'9777654', N'LNG Carrier', 296.8, 49.6, 10.77, 135000, N'LNG', 160000, N'CBM', 1, N'QA', N'Qatar'),
(N'LNG Kochi', N'9666543', N'LNG Carrier', 280.0, 43.4, 11.50, 115000, N'LNG', 140000, N'CBM', 1, N'KR', N'South Korea'),
(N'LNG Dabhol', N'9555432', N'LNG Carrier', 288.0, 44.0, 10.50, 120000, N'LNG', 145000, N'CBM', 1, N'JP', N'Japan');

PRINT 'Inserted: 6 LNG Carriers';

-- General Cargo / Break Bulk (9 vessels) - fit Multipurpose/Break Bulk berths
INSERT INTO VESSELS (VesselName, IMO, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, CargoUnit, Priority, FlagState, FlagStateName) VALUES
(N'MV Indo Pioneer', N'9878087', N'General Cargo', 146.0, 19.1, 7.57, 19066, N'Break Bulk', 21789, N'MT', 2, N'SG', N'Singapore'),
(N'MV Trans Pioneer', N'9843963', N'General Cargo', 140.5, 31.5, 6.86, 20076, N'Break Bulk', 14857, N'MT', 2, N'BS', N'Bahamas'),
(N'MV Global Explorer', N'9301332', N'General Cargo', 180.0, 28.0, 9.50, 25000, N'Project Cargo', 30000, N'MT', 2, N'PA', N'Panama'),
(N'MV Atlantic Trader', N'9512042', N'General Cargo', 165.0, 25.0, 8.50, 18000, N'Steel', 22000, N'MT', 2, N'NL', N'Netherlands'),
(N'MV Asia Link', N'9851759', N'General Cargo', 155.0, 23.0, 8.00, 15000, N'Machinery', 18000, N'MT', 2, N'SG', N'Singapore'),
(N'MV Pacific Star', N'9423156', N'General Cargo', 170.0, 26.0, 9.00, 20000, N'Timber', 24000, N'MT', 2, N'MY', N'Malaysia'),
(N'MV Ocean Bridge', N'9312045', N'General Cargo', 158.0, 24.0, 8.20, 16000, N'Bagged Cargo', 19000, N'MT', 2, N'IN', N'India'),
(N'MV Coastal Trader', N'9201934', N'General Cargo', 145.0, 22.0, 7.50, 12000, N'General', 14000, N'MT', 2, N'IN', N'India'),
(N'MV River Express', N'9090823', N'General Cargo', 120.0, 18.0, 6.00, 8000, N'Mixed Cargo', 9500, N'MT', 2, N'BD', N'Bangladesh');

PRINT 'Inserted: 9 General Cargo';

-- Car Carriers / RO-RO (6 vessels) - fit RO-RO berths (MaxLOA=300, MaxBeam=45, MaxDraft=14)
INSERT INTO VESSELS (VesselName, IMO, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, CargoUnit, Priority, FlagState, FlagStateName) VALUES
(N'MV Auto Highway', N'9695164', N'Car Carrier', 224.2, 29.1, 9.89, 33261, N'Automobiles', 7521, N'Units', 1, N'CY', N'Cyprus'),
(N'MV Auto Express', N'9584053', N'Car Carrier', 199.9, 32.3, 9.20, 57000, N'Automobiles', 6500, N'Units', 1, N'NO', N'Norway'),
(N'MV Car Transporter', N'9473942', N'Car Carrier', 180.0, 30.0, 8.50, 45000, N'Automobiles', 5000, N'Units', 2, N'JP', N'Japan'),
(N'MV Vehicle Pride', N'9362831', N'Car Carrier', 170.0, 28.0, 8.00, 38000, N'Automobiles', 4200, N'Units', 2, N'PA', N'Panama'),
(N'MV Auto Star', N'9251720', N'Car Carrier', 160.0, 26.0, 7.50, 32000, N'Automobiles', 3500, N'Units', 2, N'SG', N'Singapore'),
(N'MV RoRo King', N'9140609', N'Car Carrier', 150.0, 24.0, 7.00, 25000, N'Automobiles', 2800, N'Units', 2, N'KR', N'South Korea');

PRINT 'Inserted: 6 Car Carriers';

-- Verify
SELECT VesselType, COUNT(*) AS Count, MIN(LOA) AS MinLOA, MAX(LOA) AS MaxLOA, MIN(Draft) AS MinDraft, MAX(Draft) AS MaxDraft
FROM VESSELS GROUP BY VesselType ORDER BY VesselType;

SELECT 'Total Vessels: ' + CAST(COUNT(*) AS VARCHAR) FROM VESSELS;
GO
