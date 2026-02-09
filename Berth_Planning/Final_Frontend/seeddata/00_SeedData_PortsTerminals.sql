-- ============================================
-- Berth Planning System - Seed Data: PORTS & TERMINALS
-- Single Port: Mumbai Port Trust (INBOM)
-- Must run BEFORE Berths seed data
-- ============================================

-- Clear existing data (in correct order due to FK constraints)
DELETE FROM TERMINALS;
DELETE FROM PORTS;
DBCC CHECKIDENT ('TERMINALS', RESEED, 0);
DBCC CHECKIDENT ('PORTS', RESEED, 0);

-- ============================================
-- Insert Port: Mumbai Port Trust (INBOM)
-- ============================================
INSERT INTO PORTS (PortName, PortCode, Country, City, TimeZone, Latitude, Longitude, ContactEmail, ContactPhone, IsActive)
VALUES
('Mumbai Port Trust', 'INBOM', 'India', 'Mumbai', 'Asia/Kolkata', 18.9260, 72.8438, 'info@mumbaiport.gov.in', '+91-22-22617712', 1);

-- Display count
SELECT 'Ports inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM PORTS;

-- ============================================
-- Insert Terminals for Mumbai Port Trust
-- ============================================
DECLARE @MumbaiPortId INT = (SELECT PortId FROM PORTS WHERE PortCode = 'INBOM');

INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, Latitude, Longitude, IsActive)
VALUES
-- Container Terminals
(@MumbaiPortId, 'Indira Dock Container Terminal', 'IDCT', 'Container', 'Mumbai Port Trust', 18.9270, 72.8445, 1),
(@MumbaiPortId, 'Ballard Pier Container Terminal', 'BPCT', 'Container', 'Mumbai Port Trust', 18.9320, 72.8410, 1),

-- Bulk Terminal
(@MumbaiPortId, 'Mumbai Bulk Terminal', 'MBT', 'Bulk', 'Mumbai Port Trust', 18.9240, 72.8460, 1),

-- Liquid/Tanker Terminal
(@MumbaiPortId, 'Jawahar Dweep Oil Terminal', 'JDOT', 'Liquid', 'BPCL/HPCL/IOC', 18.9100, 72.8300, 1),
(@MumbaiPortId, 'Pir Pau Liquid Terminal', 'PPLT', 'Liquid', 'Mumbai Port Trust', 18.9050, 72.8350, 1),

-- General Cargo Terminal
(@MumbaiPortId, 'Victoria Dock General Cargo', 'VDGC', 'General', 'Mumbai Port Trust', 18.9350, 72.8420, 1),
(@MumbaiPortId, 'Prince Dock Multi-Purpose', 'PDMP', 'General', 'Mumbai Port Trust', 18.9380, 72.8400, 1),

-- Passenger Terminal
(@MumbaiPortId, 'Mumbai Cruise Terminal', 'MCT', 'Passenger', 'Mumbai Port Trust', 18.9400, 72.8380, 1);

-- Display count
SELECT 'Terminals inserted: ' + CAST(COUNT(*) AS VARCHAR) FROM TERMINALS;

-- ============================================
-- Show Terminal IDs for reference (used in Berths seeding)
-- ============================================
SELECT TerminalId, TerminalCode, TerminalName, TerminalType FROM TERMINALS ORDER BY TerminalId;
