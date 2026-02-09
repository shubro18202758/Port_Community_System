-- =============================================
-- SEED DATA: PORT & TERMINALS
-- Mundra Port, India
-- =============================================

USE [BerthPlanning];
GO

SET NOCOUNT ON;
PRINT '=== SEEDING PORT & TERMINALS ===';

-- PORT
INSERT INTO PORTS (PortName, PortCode, Country, City, TimeZone, Latitude, Longitude, IsActive)
VALUES (N'Mundra Port', N'INMUN', N'India', N'Mundra', N'Asia/Kolkata', 22.756, 69.636, 1);

PRINT 'Inserted: 1 Port';

-- TERMINALS (12 terminals)
INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'Terminal 1 - Multipurpose', N'T1', N'Multipurpose', N'APSEZ', 12, 22.761, 69.701, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'Liquid Terminal', N'LT', N'Liquid Bulk', N'APSEZ', 4, 22.7576, 69.691, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'Container Terminal 1', N'CT1', N'Container', N'APSEZ', 2, 22.7538, 69.6847, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'Container Terminal 2 - DP World', N'CT2', N'Container', N'DP World', 2, 22.7518, 69.6797, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'Container Terminal 3 - Adani CMA', N'CT3', N'Container', N'APSEZ / CMA CGM', 3, 22.7497, 69.6743, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'Container Terminal 4', N'CT4', N'Container', N'APSEZ', 2, 22.7478, 69.6697, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'West Port - Coal Terminal', N'WP', N'Dry Bulk', N'APSEZ', 3, 22.7447, 69.6373, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'Mechanised Import Terminal', N'MICT', N'Mechanised Bulk', N'APSEZ', 3, 22.7427, 69.6333, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'RO-RO Terminal', N'RORO', N'RO-RO', N'APSEZ', 1, 22.756, 69.687, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'SPM Facility', N'SPM', N'SPM', N'APSEZ / IOCL', 2, 22.709, 69.579, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'Tuna Terminal', N'TT', N'Multipurpose', N'APSEZ', 2, 22.7828, 69.7197, 1 FROM PORTS WHERE PortCode = 'INMUN';

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, TotalBerths, Latitude, Longitude, IsActive)
SELECT PortId, N'LNG Terminal', N'LNG', N'LNG', N'APSEZ', 1, 22.756, 69.643, 1 FROM PORTS WHERE PortCode = 'INMUN';

PRINT 'Inserted: 12 Terminals';

-- Verify
SELECT 'PORTS' AS [Table], COUNT(*) AS Records FROM PORTS
UNION ALL SELECT 'TERMINALS', COUNT(*) FROM TERMINALS;
GO
