-- =============================================
-- SEED DATA: BERTHS (36 berths)
-- With proper MaxLOA, MaxBeam, MaxDraft limits
-- =============================================

USE [BerthPlanning];
GO

SET NOCOUNT ON;
PRINT '=== SEEDING BERTHS ===';

-- Terminal T1 - Multipurpose (12 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Multipurpose Berth 1', N'T1-MB1', 250, 22, 20, 360, 60, N'Multipurpose', 2, 14, 1, 22.7621, 69.7042 FROM TERMINALS t WHERE t.TerminalCode = 'T1';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Multipurpose Berth 2', N'T1-MB2', 250, 22, 20, 360, 60, N'Multipurpose', 2, 14, 1, 22.7618, 69.7035 FROM TERMINALS t WHERE t.TerminalCode = 'T1';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Dry Bulk Berth 1', N'T1-DB1', 300, 24, 22, 380, 65, N'Dry Bulk', 3, 18, 1, 22.7609, 69.7014 FROM TERMINALS t WHERE t.TerminalCode = 'T1';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Dry Bulk Berth 2', N'T1-DB2', 300, 24, 22, 380, 65, N'Dry Bulk', 3, 18, 1, 22.7606, 69.7007 FROM TERMINALS t WHERE t.TerminalCode = 'T1';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Break Bulk Berth 1', N'T1-BB1', 260, 20, 18, 320, 55, N'Break Bulk', 2, 14, 1, 22.7603, 69.7000 FROM TERMINALS t WHERE t.TerminalCode = 'T1';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Break Bulk Berth 2', N'T1-BB2', 260, 20, 18, 320, 55, N'Break Bulk', 2, 14, 1, 22.7600, 69.6993 FROM TERMINALS t WHERE t.TerminalCode = 'T1';

-- Terminal LT - Liquid (4 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Liquid Berth 1', N'LT-LB1', 280, 27, 25, 380, 70, N'Liquid Bulk', 0, 16, 1, 22.7580, 69.6920 FROM TERMINALS t WHERE t.TerminalCode = 'LT';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Liquid Berth 2', N'LT-LB2', 280, 27, 25, 380, 70, N'Liquid Bulk', 0, 16, 1, 22.7576, 69.6910 FROM TERMINALS t WHERE t.TerminalCode = 'LT';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Liquid Berth 3', N'LT-LB3', 250, 27, 25, 380, 70, N'Liquid Bulk', 0, 14, 1, 22.7572, 69.6900 FROM TERMINALS t WHERE t.TerminalCode = 'LT';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Liquid Berth 4', N'LT-LB4', 290, 27, 25, 380, 70, N'Liquid Bulk', 0, 18, 1, 22.7568, 69.6890 FROM TERMINALS t WHERE t.TerminalCode = 'LT';

-- Terminal CT1 - Container (2 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Container Berth 1', N'CT1-CB1', 350, 20, 18, 420, 65, N'Container', 4, 20, 1, 22.7540, 69.6850 FROM TERMINALS t WHERE t.TerminalCode = 'CT1';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Container Berth 2', N'CT1-CB2', 350, 20, 18, 420, 65, N'Container', 4, 20, 1, 22.7536, 69.6844 FROM TERMINALS t WHERE t.TerminalCode = 'CT1';

-- Terminal CT2 - Container DP World (2 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'DP World Berth 1', N'CT2-CB1', 330, 20, 18, 420, 65, N'Container', 4, 18, 1, 22.7520, 69.6800 FROM TERMINALS t WHERE t.TerminalCode = 'CT2';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'DP World Berth 2', N'CT2-CB2', 330, 20, 18, 420, 65, N'Container', 4, 18, 1, 22.7516, 69.6794 FROM TERMINALS t WHERE t.TerminalCode = 'CT2';

-- Terminal CT3 - Container CMA (3 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'CMA Berth 1', N'CT3-CB1', 400, 20, 18, 420, 65, N'Container', 6, 22, 1, 22.7500, 69.6746 FROM TERMINALS t WHERE t.TerminalCode = 'CT3';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'CMA Berth 2', N'CT3-CB2', 400, 20, 18, 420, 65, N'Container', 6, 22, 1, 22.7496, 69.6740 FROM TERMINALS t WHERE t.TerminalCode = 'CT3';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'CMA Berth 3', N'CT3-CB3', 400, 20, 18, 420, 65, N'Container', 6, 22, 1, 22.7492, 69.6734 FROM TERMINALS t WHERE t.TerminalCode = 'CT3';

-- Terminal CT4 - Container (2 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'CT4 Berth 1', N'CT4-CB1', 410, 20, 18, 420, 65, N'Container', 6, 24, 1, 22.7480, 69.6700 FROM TERMINALS t WHERE t.TerminalCode = 'CT4';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'CT4 Berth 2', N'CT4-CB2', 410, 20, 18, 420, 65, N'Container', 6, 24, 1, 22.7476, 69.6694 FROM TERMINALS t WHERE t.TerminalCode = 'CT4';

-- Terminal WP - West Port Coal (3 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Coal Berth 1', N'WP-CB1', 350, 24, 22, 380, 65, N'Dry Bulk', 3, 20, 1, 22.7450, 69.6376 FROM TERMINALS t WHERE t.TerminalCode = 'WP';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Coal Berth 2', N'WP-CB2', 350, 24, 22, 380, 65, N'Dry Bulk', 3, 20, 1, 22.7446, 69.6370 FROM TERMINALS t WHERE t.TerminalCode = 'WP';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Coal Berth 3', N'WP-CB3', 360, 24, 22, 380, 65, N'Dry Bulk', 3, 20, 1, 22.7442, 69.6364 FROM TERMINALS t WHERE t.TerminalCode = 'WP';

-- Terminal MICT - Mechanised (3 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Mech Berth 1', N'MI-MB1', 340, 24, 22, 380, 65, N'Mechanised Bulk', 2, 18, 1, 22.7430, 69.6336 FROM TERMINALS t WHERE t.TerminalCode = 'MICT';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Mech Berth 2', N'MI-MB2', 340, 24, 22, 380, 65, N'Mechanised Bulk', 2, 18, 1, 22.7426, 69.6330 FROM TERMINALS t WHERE t.TerminalCode = 'MICT';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Mech Berth 3', N'MI-MB3', 340, 24, 22, 380, 65, N'Mechanised Bulk', 2, 18, 1, 22.7422, 69.6324 FROM TERMINALS t WHERE t.TerminalCode = 'MICT';

-- Terminal RORO (1 berth)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'RO-RO Berth', N'RR-RB1', 230, 16, 14, 300, 45, N'RO-RO', 0, 12, 1, 22.7562, 69.6872 FROM TERMINALS t WHERE t.TerminalCode = 'RORO';

-- Terminal SPM (2 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'SPM 1', N'SPM-01', 50, 35, 30, 400, 70, N'SPM', 0, 0, 1, 22.7092, 69.5792 FROM TERMINALS t WHERE t.TerminalCode = 'SPM';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'SPM 2', N'SPM-02', 50, 35, 30, 400, 70, N'SPM', 0, 0, 1, 22.7088, 69.5786 FROM TERMINALS t WHERE t.TerminalCode = 'SPM';

-- Terminal TT - Tuna (2 berths)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Tuna Berth 1', N'TT-TB1', 280, 22, 20, 360, 60, N'Multipurpose', 2, 16, 1, 22.7830, 69.7200 FROM TERMINALS t WHERE t.TerminalCode = 'TT';
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'Tuna Berth 2', N'TT-TB2', 280, 22, 20, 360, 60, N'Multipurpose', 2, 16, 1, 22.7826, 69.7194 FROM TERMINALS t WHERE t.TerminalCode = 'TT';

-- Terminal LNG (1 berth)
INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
SELECT t.TerminalId, t.PortId, 'INMUN', N'LNG Berth', N'LNG-LB1', 300, 17, 15, 380, 60, N'LNG', 0, 18, 1, 22.7562, 69.6432 FROM TERMINALS t WHERE t.TerminalCode = 'LNG';

PRINT 'Inserted: 36 Berths';

-- Verify
SELECT BerthType, COUNT(*) AS Count FROM BERTHS GROUP BY BerthType ORDER BY BerthType;
GO
