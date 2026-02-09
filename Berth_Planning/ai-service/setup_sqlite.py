"""
SmartBerth AI Service - SQLite Database Setup
For local development when SQL Server is not available
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

# Database file path
DB_PATH = Path(__file__).parent / "smartberth.db"


def create_tables(conn):
    """Create all required tables"""
    cursor = conn.cursor()
    
    # PORTS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PORTS (
            PortId INTEGER PRIMARY KEY AUTOINCREMENT,
            PortName TEXT NOT NULL,
            PortCode TEXT NOT NULL UNIQUE,
            Country TEXT,
            City TEXT,
            TimeZone TEXT,
            Latitude REAL,
            Longitude REAL,
            ContactEmail TEXT,
            ContactPhone TEXT,
            IsActive INTEGER DEFAULT 1,
            CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # TERMINALS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS TERMINALS (
            TerminalId INTEGER PRIMARY KEY AUTOINCREMENT,
            PortId INTEGER NOT NULL,
            TerminalName TEXT NOT NULL,
            TerminalCode TEXT NOT NULL UNIQUE,
            TerminalType TEXT,
            OperatorName TEXT,
            Latitude REAL,
            Longitude REAL,
            IsActive INTEGER DEFAULT 1,
            CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (PortId) REFERENCES PORTS(PortId)
        )
    ''')
    
    # BERTHS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS BERTHS (
            BerthId INTEGER PRIMARY KEY AUTOINCREMENT,
            TerminalId INTEGER NOT NULL,
            BerthName TEXT NOT NULL,
            BerthCode TEXT NOT NULL UNIQUE,
            BerthType TEXT,
            MaxLOA REAL,
            MaxBeam REAL,
            MaxDraft REAL,
            Equipment TEXT,
            IsActive INTEGER DEFAULT 1,
            CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (TerminalId) REFERENCES TERMINALS(TerminalId)
        )
    ''')
    
    # VESSELS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS VESSELS (
            VesselId INTEGER PRIMARY KEY AUTOINCREMENT,
            VesselName TEXT NOT NULL,
            IMO TEXT UNIQUE,
            MMSI TEXT,
            VesselType TEXT,
            LOA REAL,
            Beam REAL,
            Draft REAL,
            GrossTonnage INTEGER,
            CargoType TEXT,
            CargoVolume REAL,
            Priority INTEGER DEFAULT 2,
            CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # VESSEL_SCHEDULE table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS VESSEL_SCHEDULE (
            ScheduleId INTEGER PRIMARY KEY AUTOINCREMENT,
            VesselId INTEGER NOT NULL,
            BerthId INTEGER,
            ETA TEXT,
            PredictedETA TEXT,
            ATA TEXT,
            ETD TEXT,
            ATD TEXT,
            Status TEXT DEFAULT 'Scheduled',
            Priority INTEGER DEFAULT 2,
            CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (VesselId) REFERENCES VESSELS(VesselId),
            FOREIGN KEY (BerthId) REFERENCES BERTHS(BerthId)
        )
    ''')
    
    # RESOURCES table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RESOURCES (
            ResourceId INTEGER PRIMARY KEY AUTOINCREMENT,
            ResourceName TEXT NOT NULL,
            ResourceType TEXT NOT NULL,
            Capacity INTEGER,
            IsAvailable INTEGER DEFAULT 1,
            MaintenanceSchedule TEXT,
            CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # RESOURCE_ALLOCATION table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS RESOURCE_ALLOCATION (
            AllocationId INTEGER PRIMARY KEY AUTOINCREMENT,
            ResourceId INTEGER NOT NULL,
            ScheduleId INTEGER NOT NULL,
            AllocatedFrom TEXT,
            AllocatedTo TEXT,
            Quantity INTEGER DEFAULT 1,
            Status TEXT DEFAULT 'Allocated',
            FOREIGN KEY (ResourceId) REFERENCES RESOURCES(ResourceId),
            FOREIGN KEY (ScheduleId) REFERENCES VESSEL_SCHEDULE(ScheduleId)
        )
    ''')
    
    # WEATHER_DATA table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS WEATHER_DATA (
            WeatherId INTEGER PRIMARY KEY AUTOINCREMENT,
            WindSpeed REAL,
            WindDirection REAL,
            Visibility REAL,
            WaveHeight REAL,
            Temperature REAL,
            Conditions TEXT,
            RecordedAt TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # TIDAL_DATA table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS TIDAL_DATA (
            TidalId INTEGER PRIMARY KEY AUTOINCREMENT,
            TideType TEXT,
            TideHeight REAL,
            TideTime TEXT,
            DraftRestriction REAL,
            RecordedAt TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # AIS_DATA table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS AIS_DATA (
            AISId INTEGER PRIMARY KEY AUTOINCREMENT,
            VesselId INTEGER,
            MMSI TEXT,
            Latitude REAL,
            Longitude REAL,
            Speed REAL,
            Course REAL,
            Heading REAL,
            NavigationStatus TEXT,
            RecordedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (VesselId) REFERENCES VESSELS(VesselId)
        )
    ''')
    
    # CONFLICTS table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS CONFLICTS (
            ConflictId INTEGER PRIMARY KEY AUTOINCREMENT,
            ConflictType TEXT,
            Severity TEXT,
            Description TEXT,
            ScheduleId1 INTEGER,
            ScheduleId2 INTEGER,
            DetectedAt TEXT DEFAULT CURRENT_TIMESTAMP,
            Status TEXT DEFAULT 'Detected',
            FOREIGN KEY (ScheduleId1) REFERENCES VESSEL_SCHEDULE(ScheduleId),
            FOREIGN KEY (ScheduleId2) REFERENCES VESSEL_SCHEDULE(ScheduleId)
        )
    ''')
    
    # KNOWLEDGE_BASE table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS KNOWLEDGE_BASE (
            KBId INTEGER PRIMARY KEY AUTOINCREMENT,
            Title TEXT NOT NULL,
            Content TEXT NOT NULL,
            Category TEXT,
            Tags TEXT,
            CreatedAt TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    print("✅ All tables created successfully")


def load_seed_data(conn):
    """Load seed data from seed-data.json"""
    cursor = conn.cursor()
    
    # Find seed data file
    seed_file = Path(__file__).parent.parent.parent / "seed-data.json"
    if not seed_file.exists():
        seed_file = Path(__file__).parent.parent.parent.parent / "seed-data.json"
    
    if not seed_file.exists():
        print(f"⚠️ Seed data file not found at {seed_file}")
        # Create minimal seed data
        create_minimal_seed_data(conn)
        return
    
    print(f"Loading seed data from: {seed_file}")
    
    with open(seed_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Load ports
    if 'ports' in data:
        for port in data['ports']:
            cursor.execute('''
                INSERT OR IGNORE INTO PORTS (PortName, PortCode, Country, City, TimeZone, Latitude, Longitude, IsActive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                port.get('portName'),
                port.get('portCode'),
                port.get('country'),
                port.get('city'),
                port.get('timeZone'),
                port.get('latitude'),
                port.get('longitude'),
                1
            ))
    
    # Load terminals
    if 'terminals' in data:
        for terminal in data['terminals']:
            cursor.execute('''
                INSERT OR IGNORE INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, IsActive)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                terminal.get('portId', 1),
                terminal.get('terminalName'),
                terminal.get('terminalCode'),
                terminal.get('terminalType'),
                terminal.get('operatorName'),
                1
            ))
    
    # Load berths
    if 'berths' in data:
        for berth in data['berths']:
            cursor.execute('''
                INSERT OR IGNORE INTO BERTHS (TerminalId, BerthName, BerthCode, BerthType, MaxLOA, MaxBeam, MaxDraft, Equipment, IsActive)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                berth.get('terminalId', 1),
                berth.get('berthName'),
                berth.get('berthCode'),
                berth.get('berthType'),
                berth.get('maxLOA'),
                berth.get('maxBeam'),
                berth.get('maxDraft'),
                json.dumps(berth.get('equipment', [])),
                1
            ))
    
    # Load vessels
    if 'vessels' in data:
        for vessel in data['vessels']:
            cursor.execute('''
                INSERT OR IGNORE INTO VESSELS (VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, Priority)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                vessel.get('vesselName'),
                vessel.get('imo'),
                vessel.get('mmsi'),
                vessel.get('vesselType'),
                vessel.get('loa'),
                vessel.get('beam'),
                vessel.get('draft'),
                vessel.get('grossTonnage'),
                vessel.get('cargoType'),
                vessel.get('cargoVolume'),
                vessel.get('priority', 2)
            ))
    
    # Load resources
    if 'resources' in data:
        for resource in data['resources']:
            cursor.execute('''
                INSERT OR IGNORE INTO RESOURCES (ResourceName, ResourceType, Capacity, IsAvailable)
                VALUES (?, ?, ?, ?)
            ''', (
                resource.get('resourceName'),
                resource.get('resourceType'),
                resource.get('capacity'),
                1 if resource.get('status', 'Available') == 'Available' else 0
            ))
    
    # Load weather data
    if 'weatherData' in data:
        for weather in data['weatherData']:
            cursor.execute('''
                INSERT INTO WEATHER_DATA (WindSpeed, WindDirection, Visibility, WaveHeight, Temperature, Conditions, RecordedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                weather.get('windSpeed'),
                weather.get('windDirection'),
                weather.get('visibility'),
                weather.get('waveHeight'),
                weather.get('temperature'),
                weather.get('conditions'),
                weather.get('recordedAt', datetime.utcnow().isoformat())
            ))
    
    # Load tidal data
    if 'tidalData' in data:
        for tidal in data['tidalData']:
            cursor.execute('''
                INSERT INTO TIDAL_DATA (TideType, TideHeight, TideTime, DraftRestriction)
                VALUES (?, ?, ?, ?)
            ''', (
                tidal.get('tideType'),
                tidal.get('tideHeight'),
                tidal.get('tideTime'),
                tidal.get('draftRestriction')
            ))
    
    # Load AIS data
    if 'aisData' in data:
        for ais in data['aisData']:
            cursor.execute('''
                INSERT INTO AIS_DATA (VesselId, MMSI, Latitude, Longitude, Speed, Course, Heading, NavigationStatus, RecordedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                ais.get('vesselId'),
                ais.get('mmsi'),
                ais.get('latitude'),
                ais.get('longitude'),
                ais.get('speed'),
                ais.get('course'),
                ais.get('heading'),
                ais.get('navigationStatus'),
                ais.get('recordedAt', datetime.utcnow().isoformat())
            ))
    
    conn.commit()
    print("✅ Seed data loaded successfully")


def create_minimal_seed_data(conn):
    """Create minimal seed data if seed-data.json not found"""
    cursor = conn.cursor()
    
    # Create Mumbai Port
    cursor.execute('''
        INSERT INTO PORTS (PortName, PortCode, Country, City, Latitude, Longitude, IsActive)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', ('Mumbai Port Trust', 'INMUN', 'India', 'Mumbai', 18.9388, 72.8354, 1))
    
    # Create terminals
    terminals = [
        (1, 'JN Container Terminal', 'JNCT', 'Container', 'JNPT'),
        (1, 'Bulk Terminal 1', 'BT1', 'Bulk', 'Mumbai Port'),
        (1, 'Liquid Cargo Terminal', 'LCT', 'Liquid', 'Mumbai Port'),
    ]
    for t in terminals:
        cursor.execute('''
            INSERT INTO TERMINALS (PortId, TerminalName, TerminalCode, TerminalType, OperatorName, IsActive)
            VALUES (?, ?, ?, ?, ?, 1)
        ''', t)
    
    # Create berths
    berths = [
        (1, 'Berth 1', 'B1', 'Container', 350, 50, 14.5),
        (1, 'Berth 2', 'B2', 'Container', 300, 45, 12.0),
        (2, 'Berth 3', 'B3', 'Bulk', 250, 40, 11.0),
        (3, 'Berth 4', 'B4', 'Liquid', 200, 35, 10.0),
    ]
    for b in berths:
        cursor.execute('''
            INSERT INTO BERTHS (TerminalId, BerthName, BerthCode, BerthType, MaxLOA, MaxBeam, MaxDraft, IsActive)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', b)
    
    # Create sample vessels
    vessels = [
        ('MAERSK AURORA', 'IMO9876543', '477123456', 'Container', 330, 48, 13.5, 120000, 'Container', 5000, 1),
        ('MSC HARMONY', 'IMO9876544', '477123457', 'Container', 290, 43, 11.5, 80000, 'Container', 3500, 2),
        ('CAPE FORTUNE', 'IMO9876545', '477123458', 'Bulk', 240, 38, 10.5, 50000, 'Iron Ore', 45000, 2),
        ('PACIFIC STAR', 'IMO9876546', '477123459', 'Tanker', 180, 32, 9.5, 35000, 'Crude Oil', 30000, 3),
    ]
    for v in vessels:
        cursor.execute('''
            INSERT INTO VESSELS (VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft, GrossTonnage, CargoType, CargoVolume, Priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', v)
    
    # Create schedules with future ETAs
    now = datetime.utcnow()
    schedules = [
        (1, 1, (now + timedelta(hours=6)).isoformat(), None, 'Approaching', 1),
        (2, None, (now + timedelta(hours=12)).isoformat(), None, 'Scheduled', 2),
        (3, None, (now + timedelta(hours=18)).isoformat(), None, 'Scheduled', 2),
        (4, None, (now + timedelta(hours=24)).isoformat(), None, 'Scheduled', 3),
    ]
    for s in schedules:
        cursor.execute('''
            INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, Status, Priority)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', s)
    
    # Create resources
    resources = [
        ('Pilot 1', 'Pilot', 1, 1),
        ('Pilot 2', 'Pilot', 1, 1),
        ('Tug Mahul', 'Tugboat', 40, 1),
        ('Tug Prabodhan', 'Tugboat', 50, 1),
        ('Gang A', 'Labor', 20, 1),
        ('Gang B', 'Labor', 20, 1),
    ]
    for r in resources:
        cursor.execute('''
            INSERT INTO RESOURCES (ResourceName, ResourceType, Capacity, IsAvailable)
            VALUES (?, ?, ?, ?)
        ''', r)
    
    # Create current weather
    cursor.execute('''
        INSERT INTO WEATHER_DATA (WindSpeed, WindDirection, Visibility, WaveHeight, Temperature, Conditions, RecordedAt)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (15, 180, 5.0, 0.8, 28, 'Clear', now.isoformat()))
    
    # Create AIS positions
    ais_positions = [
        (1, '477123456', 18.7, 72.5, 12.5, 45, 45, 'Under way using engine', now.isoformat()),
        (2, '477123457', 18.5, 72.3, 11.0, 50, 50, 'Under way using engine', now.isoformat()),
        (3, '477123458', 18.3, 72.1, 10.0, 55, 55, 'Under way using engine', now.isoformat()),
    ]
    for a in ais_positions:
        cursor.execute('''
            INSERT INTO AIS_DATA (VesselId, MMSI, Latitude, Longitude, Speed, Course, Heading, NavigationStatus, RecordedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', a)
    
    conn.commit()
    print("✅ Minimal seed data created")


def create_sample_schedules(conn):
    """Create sample vessel schedules for testing"""
    cursor = conn.cursor()
    now = datetime.utcnow()
    
    # Get vessel and berth counts
    cursor.execute("SELECT COUNT(*) FROM VESSELS")
    vessel_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM VESSEL_SCHEDULE")
    schedule_count = cursor.fetchone()[0]
    
    if schedule_count > 0:
        print(f"ℹ️ {schedule_count} schedules already exist")
        return
    
    if vessel_count == 0:
        print("⚠️ No vessels in database")
        return
    
    # Create schedules for first few vessels
    for i in range(1, min(5, vessel_count + 1)):
        eta = now + timedelta(hours=6 * i)
        status = 'Approaching' if i == 1 else 'Scheduled'
        berth_id = 1 if i == 1 else None
        
        cursor.execute('''
            INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, Status, Priority)
            VALUES (?, ?, ?, ?, ?)
        ''', (i, berth_id, eta.isoformat(), status, 2))
    
    conn.commit()
    print(f"✅ Created {min(4, vessel_count)} sample schedules")


def init_database():
    """Initialize the SQLite database"""
    print(f"Initializing SQLite database at: {DB_PATH}")
    
    # Remove existing database if needed
    if DB_PATH.exists():
        print("Existing database found")
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    
    try:
        create_tables(conn)
        load_seed_data(conn)
        create_sample_schedules(conn)
        
        # Verify data
        cursor = conn.cursor()
        tables = ['PORTS', 'TERMINALS', 'BERTHS', 'VESSELS', 'VESSEL_SCHEDULE', 'RESOURCES', 'WEATHER_DATA', 'AIS_DATA']
        print("\n📊 Database Summary:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count} records")
        
        print("\n✅ Database initialization complete!")
        
    finally:
        conn.close()
    
    return str(DB_PATH)


if __name__ == "__main__":
    init_database()
