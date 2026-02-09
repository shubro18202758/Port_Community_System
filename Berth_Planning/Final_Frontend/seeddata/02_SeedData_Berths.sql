-- ============================================
-- Berth Planning System - Seed Data: BERTHS
-- 20 Berths linked to Mumbai Port Trust Terminals
-- ============================================

-- Clear existing data
DELETE FROM BERTHS;
DBCC CHECKIDENT ('BERTHS', RESEED, 0);

-- Get Terminal IDs for Mumbai Port Trust
DECLARE @IDCT INT = (SELECT TerminalId FROM TERMINALS WHERE TerminalCode = 'IDCT');  -- Indira Dock Container
DECLARE @BPCT INT = (SELECT TerminalId FROM TERMINALS WHERE TerminalCode = 'BPCT');  -- Ballard Pier Container
DECLARE @MBT INT = (SELECT TerminalId FROM TERMINALS WHERE TerminalCode = 'MBT');    -- Mumbai Bulk Terminal
DECLARE @JDOT INT = (SELECT TerminalId FROM TERMINALS WHERE TerminalCode = 'JDOT');  -- Jawahar Dweep Oil
DECLARE @PPLT INT = (SELECT TerminalId FROM TERMINALS WHERE TerminalCode = 'PPLT');  -- Pir Pau Liquid
DECLARE @VDGC INT = (SELECT TerminalId FROM TERMINALS WHERE TerminalCode = 'VDGC');  -- Victoria Dock General
DECLARE @PDMP INT = (SELECT TerminalId FROM TERMINALS WHERE TerminalCode = 'PDMP');  -- Prince Dock Multi-Purpose
DECLARE @MCT INT = (SELECT TerminalId FROM TERMINALS WHERE TerminalCode = 'MCT');    -- Mumbai Cruise Terminal

-- Insert Berths linked to Mumbai Port Trust Terminals
INSERT INTO BERTHS (TerminalId, BerthName, BerthCode, Length, Depth, MaxDraft, BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude)
VALUES
-- Indira Dock Container Terminal (3 berths)
(@IDCT, 'Indira Dock Berth 1', 'IDCT-01', 300.00, 12.00, 11.00, 'Container', 3, 10, 1, 18.9271, 72.8443),
(@IDCT, 'Indira Dock Berth 2', 'IDCT-02', 280.00, 11.50, 10.50, 'Container', 3, 10, 1, 18.9273, 72.8447),
(@IDCT, 'Indira Dock Berth 3', 'IDCT-03', 250.00, 11.00, 10.00, 'Container', 2, 8, 1, 18.9275, 72.8451),

-- Ballard Pier Container Terminal (3 berths)
(@BPCT, 'Ballard Pier Berth 1', 'BPCT-01', 320.00, 12.50, 11.50, 'Container', 4, 12, 1, 18.9318, 72.8408),
(@BPCT, 'Ballard Pier Berth 2', 'BPCT-02', 300.00, 12.00, 11.00, 'Container', 3, 10, 1, 18.9322, 72.8412),
(@BPCT, 'Ballard Pier Berth 3', 'BPCT-03', 280.00, 11.50, 10.50, 'Container', 3, 10, 1, 18.9326, 72.8416),

-- Mumbai Bulk Terminal (3 berths)
(@MBT, 'Bulk Berth North', 'MBT-N', 350.00, 14.00, 13.00, 'Bulk', 2, 12, 1, 18.9242, 72.8458),
(@MBT, 'Bulk Berth Central', 'MBT-C', 320.00, 13.50, 12.50, 'Bulk', 2, 10, 1, 18.9244, 72.8462),
(@MBT, 'Bulk Berth South', 'MBT-S', 300.00, 13.00, 12.00, 'Bulk', 2, 10, 1, 18.9246, 72.8466),

-- Jawahar Dweep Oil Terminal (3 berths for large tankers)
(@JDOT, 'Jawahar Dweep Berth 1', 'JDOT-01', 380.00, 18.00, 17.00, 'Tanker', 0, 8, 1, 18.9102, 72.8298),
(@JDOT, 'Jawahar Dweep Berth 2', 'JDOT-02', 350.00, 16.50, 15.50, 'Tanker', 0, 8, 1, 18.9105, 72.8302),
(@JDOT, 'Jawahar Dweep Berth 3', 'JDOT-03', 320.00, 15.00, 14.00, 'Tanker', 0, 6, 1, 18.9108, 72.8306),

-- Pir Pau Liquid Terminal (2 berths for smaller tankers)
(@PPLT, 'Pir Pau Berth 1', 'PPLT-01', 250.00, 12.00, 11.00, 'Tanker', 0, 6, 1, 18.9052, 72.8348),
(@PPLT, 'Pir Pau Berth 2', 'PPLT-02', 220.00, 11.00, 10.00, 'Tanker', 0, 6, 1, 18.9055, 72.8352),

-- Victoria Dock General Cargo (2 berths)
(@VDGC, 'Victoria Dock Berth 1', 'VDGC-01', 220.00, 10.00, 9.00, 'General', 2, 8, 1, 18.9348, 72.8418),
(@VDGC, 'Victoria Dock Berth 2', 'VDGC-02', 200.00, 9.50, 8.50, 'General', 2, 8, 1, 18.9352, 72.8422),

-- Prince Dock Multi-Purpose (2 berths)
(@PDMP, 'Prince Dock Berth 1', 'PDMP-01', 240.00, 10.50, 9.50, 'General', 2, 8, 1, 18.9378, 72.8398),
(@PDMP, 'Prince Dock Berth 2', 'PDMP-02', 220.00, 10.00, 9.00, 'General', 2, 8, 1, 18.9382, 72.8402),

-- Mumbai Cruise Terminal (2 berths)
(@MCT, 'Cruise Berth Main', 'MCT-01', 350.00, 11.00, 10.00, 'Passenger', 0, 10, 1, 18.9398, 72.8378),
(@MCT, 'Cruise Berth Secondary', 'MCT-02', 280.00, 10.00, 9.00, 'Passenger', 0, 8, 1, 18.9402, 72.8382);

-- Display count
SELECT 'Berths inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM BERTHS;

-- Show berths with their terminal/port hierarchy
SELECT
    b.BerthCode,
    b.BerthName,
    b.BerthType,
    t.TerminalCode,
    t.TerminalName,
    p.PortCode,
    p.PortName
FROM BERTHS b
LEFT JOIN TERMINALS t ON b.TerminalId = t.TerminalId
LEFT JOIN PORTS p ON t.PortId = p.PortId
ORDER BY t.TerminalCode, b.BerthCode;
