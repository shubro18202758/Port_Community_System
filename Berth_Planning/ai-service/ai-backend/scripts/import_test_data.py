"""
Import Test_Data CSVs directly into LocalDB
These CSVs already have proper column names matching the database schema
"""

import pyodbc
import pandas as pd
import os
import sys
from datetime import datetime

class TestDataImporter:
    def __init__(self):
        self.conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=(localdb)\\MSSQLLocalDB;"
            "DATABASE=BerthPlanning;"
            "Trusted_Connection=yes;"
        )
        self.test_data_path = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\Test_Data"
        self.conn = None
        self.cursor = None
        
    def connect(self):
        print("Connecting to LocalDB...")
        self.conn = pyodbc.connect(self.conn_str, timeout=30)
        self.cursor = self.conn.cursor()
        print("✅ Connected to LocalDB - BerthPlanning")
        
    def close(self):
        if self.conn:
            self.conn.close()
            print("Connection closed")
            
    def clear_all_tables(self):
        """Clear tables in FK-safe order"""
        print("\n  Clearing tables in FK-safe order...")
        
        delete_order = [
            'AIS_DATA', 'VESSEL_SCHEDULE', 'VESSEL_HISTORY', 'WEATHER_DATA', 'TIDAL_DATA',
            'UKC_DATA', 'ALERTS_NOTIFICATIONS', 'BERTH_MAINTENANCE', 'TUGBOATS', 'PILOTS',
            'BERTHS', 'ANCHORAGES', 'CHANNELS', 'TERMINALS', 'VESSELS', 'PORTS'
        ]
        
        for table in delete_order:
            try:
                self.cursor.execute(f"DELETE FROM {table}")
                self.conn.commit()
                print(f"  🗑️  Cleared {table}")
            except Exception as e:
                if "Invalid object name" not in str(e):
                    print(f"  ⚠️  Could not clear {table}: {e}")
                    
        print("  ✅ Tables cleared")
        
    def import_ports(self):
        """Import PORTS from CSV"""
        print("\n" + "="*60)
        print("IMPORTING PORTS")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "PORTS.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        self.cursor.execute("SET IDENTITY_INSERT PORTS ON")
        
        for _, row in df.iterrows():
            self.cursor.execute("""
                INSERT INTO PORTS (PortId, PortName, PortCode, Country, City, TimeZone, 
                                   Latitude, Longitude, ContactEmail, ContactPhone, IsActive, CreatedAt, UpdatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                int(row['PortId']),
                row['PortName'],
                row['PortCode'],
                row.get('Country', 'India'),
                row.get('City', 'Mumbai'),
                row.get('TimeZone', 'Asia/Kolkata'),
                float(row.get('Latitude', 18.94)) if pd.notna(row.get('Latitude')) else 18.94,
                float(row.get('Longitude', 72.84)) if pd.notna(row.get('Longitude')) else 72.84,
                row.get('ContactEmail', 'info@port.in'),
                row.get('ContactPhone', '+91-22-12345678'),
                1
            ))
            
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT PORTS OFF")
        print(f"  ✅ Inserted {len(df)} ports")
        return len(df)
        
    def import_terminals(self):
        """Import TERMINALS from CSV"""
        print("\n" + "="*60)
        print("IMPORTING TERMINALS")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "TERMINALS.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        self.cursor.execute("SET IDENTITY_INSERT TERMINALS ON")
        
        for _, row in df.iterrows():
            self.cursor.execute("""
                INSERT INTO TERMINALS (TerminalId, PortId, TerminalName, TerminalCode, TerminalType,
                                       OperatorName, Latitude, Longitude, IsActive, CreatedAt, UpdatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                int(row['TerminalId']),
                int(row['PortId']),
                row['TerminalName'],
                row['TerminalCode'],
                row.get('TerminalType', 'Container'),
                row.get('OperatorName', 'Port Authority'),
                float(row.get('Latitude', 18.94)) if pd.notna(row.get('Latitude')) else 18.94,
                float(row.get('Longitude', 72.84)) if pd.notna(row.get('Longitude')) else 72.84,
                1
            ))
            
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT TERMINALS OFF")
        print(f"  ✅ Inserted {len(df)} terminals")
        return len(df)
        
    def import_berths(self):
        """Import BERTHS from CSV"""
        print("\n" + "="*60)
        print("IMPORTING BERTHS")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "BERTHS.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        self.cursor.execute("SET IDENTITY_INSERT BERTHS ON")
        
        for _, row in df.iterrows():
            # Ensure values > 0 for constraints
            length = max(float(row.get('Length', 200)), 1)
            depth = max(float(row.get('Depth', 15)), 1)
            max_draft = max(float(row.get('MaxDraft', 14)), 1)
            
            self.cursor.execute("""
                INSERT INTO BERTHS (BerthId, TerminalId, BerthName, BerthCode, Length, Depth, MaxDraft,
                                   BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude, CreatedAt, UpdatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                int(row['BerthId']),
                int(row['TerminalId']),
                row['BerthName'],
                row['BerthCode'],
                length,
                depth,
                max_draft,
                row.get('BerthType', 'General'),
                int(row.get('NumberOfCranes', 0)),
                int(row.get('BollardCount', 10)),
                1,
                float(row.get('Latitude', 18.94)) if pd.notna(row.get('Latitude')) else 18.94,
                float(row.get('Longitude', 72.84)) if pd.notna(row.get('Longitude')) else 72.84
            ))
            
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT BERTHS OFF")
        print(f"  ✅ Inserted {len(df)} berths")
        return len(df)
        
    def import_vessels(self):
        """Import VESSELS from CSV"""
        print("\n" + "="*60)
        print("IMPORTING VESSELS")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "VESSELS.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        self.cursor.execute("SET IDENTITY_INSERT VESSELS ON")
        
        for _, row in df.iterrows():
            # Ensure values > 0 for constraints and Priority 1-3
            loa = max(float(row.get('LOA', 200)), 1)
            beam = max(float(row.get('Beam', 30)), 1)
            draft = max(float(row.get('Draft', 10)), 1)
            priority = min(max(int(row.get('Priority', 2)), 1), 3)
            
            self.cursor.execute("""
                INSERT INTO VESSELS (VesselId, VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft,
                                    GrossTonnage, CargoType, CargoVolume, Priority, CreatedAt, UpdatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
            """, (
                int(row['VesselId']),
                row['VesselName'],
                str(row['IMO']),
                str(row['MMSI']),
                row.get('VesselType', 'Cargo'),
                loa,
                beam,
                draft,
                int(row.get('GrossTonnage', 50000)),
                row.get('CargoType', 'General'),
                float(row.get('CargoVolume', 10000)) if pd.notna(row.get('CargoVolume')) else 10000,
                priority
            ))
            
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT VESSELS OFF")
        print(f"  ✅ Inserted {len(df)} vessels")
        return len(df)
        
    def import_vessel_schedule(self):
        """Import VESSEL_SCHEDULE from CSV"""
        print("\n" + "="*60)
        print("IMPORTING VESSEL_SCHEDULE")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "VESSEL_SCHEDULE.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        # Valid status values
        valid_statuses = ['Scheduled', 'Approaching', 'Berthed', 'Departed', 'Cancelled']
        
        self.cursor.execute("SET IDENTITY_INSERT VESSEL_SCHEDULE ON")
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                # Map status to valid values
                status = str(row.get('Status', 'Scheduled'))
                if status not in valid_statuses:
                    status_map = {
                        'En Route': 'Approaching',
                        'Arriving': 'Approaching',
                        'At Berth': 'Berthed',
                        'Left': 'Departed'
                    }
                    status = status_map.get(status, 'Scheduled')
                
                # Ensure DwellTime > 0, WaitingTime >= 0
                dwell_time = max(float(row.get('DwellTime', 24)), 1) if pd.notna(row.get('DwellTime')) else 24
                waiting_time = max(float(row.get('WaitingTime', 0)), 0) if pd.notna(row.get('WaitingTime')) else 0
                
                self.cursor.execute("""
                    INSERT INTO VESSEL_SCHEDULE (ScheduleId, VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, ATD,
                                                Status, DwellTime, WaitingTime, OptimizationScore, IsOptimized, ConflictCount, CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), GETDATE())
                """, (
                    int(row['ScheduleId']),
                    int(row['VesselId']),
                    int(row['BerthId']),
                    pd.to_datetime(row.get('ETA')) if pd.notna(row.get('ETA')) else None,
                    pd.to_datetime(row.get('PredictedETA')) if pd.notna(row.get('PredictedETA')) else None,
                    pd.to_datetime(row.get('ETD')) if pd.notna(row.get('ETD')) else None,
                    pd.to_datetime(row.get('ATA')) if pd.notna(row.get('ATA')) else None,
                    pd.to_datetime(row.get('ATB')) if pd.notna(row.get('ATB')) else None,
                    pd.to_datetime(row.get('ATD')) if pd.notna(row.get('ATD')) else None,
                    status,
                    dwell_time,
                    waiting_time,
                    float(row.get('OptimizationScore', 0.8)) if pd.notna(row.get('OptimizationScore')) else 0.8,
                    bool(row.get('IsOptimized', False)),
                    int(row.get('ConflictCount', 0)) if pd.notna(row.get('ConflictCount')) else 0
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Row {row.get('ScheduleId')}: {e}")
                continue
                
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT VESSEL_SCHEDULE OFF")
        print(f"  ✅ Inserted {inserted} vessel schedules")
        return inserted
        
    def import_weather_data(self):
        """Import WEATHER_DATA from CSV"""
        print("\n" + "="*60)
        print("IMPORTING WEATHER_DATA")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "WEATHER_DATA.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        self.cursor.execute("SET IDENTITY_INSERT WEATHER_DATA ON")
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                self.cursor.execute("""
                    INSERT INTO WEATHER_DATA (WeatherId, RecordedAt, WindSpeed, WindDirection, Visibility,
                                             WaveHeight, Temperature, Precipitation, WeatherCondition, IsAlert, FetchedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    int(row['WeatherId']),
                    pd.to_datetime(row.get('RecordedAt')) if pd.notna(row.get('RecordedAt')) else datetime.now(),
                    float(row.get('WindSpeed', 10)) if pd.notna(row.get('WindSpeed')) else 10,
                    int(row.get('WindDirection', 180)) if pd.notna(row.get('WindDirection')) else 180,
                    float(row.get('Visibility', 10)) if pd.notna(row.get('Visibility')) else 10,
                    float(row.get('WaveHeight', 1)) if pd.notna(row.get('WaveHeight')) else 1,
                    float(row.get('Temperature', 25)) if pd.notna(row.get('Temperature')) else 25,
                    float(row.get('Precipitation', 0)) if pd.notna(row.get('Precipitation')) else 0,
                    str(row.get('WeatherCondition', 'Clear'))[:50],
                    bool(row.get('IsAlert', False))
                ))
                inserted += 1
            except Exception as e:
                if inserted < 5:  # Only show first few errors
                    print(f"  ⚠️  Row {row.get('WeatherId')}: {e}")
                continue
                
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT WEATHER_DATA OFF")
        print(f"  ✅ Inserted {inserted} weather records")
        return inserted
        
    def import_tidal_data(self):
        """Import TIDAL_DATA from CSV"""
        print("\n" + "="*60)
        print("IMPORTING TIDAL_DATA")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "TIDAL_DATA.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        self.cursor.execute("SET IDENTITY_INSERT TIDAL_DATA ON")
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                # Map tide type to valid values
                tide_type = str(row.get('TideType', 'HighTide'))
                if tide_type not in ['HighTide', 'LowTide']:
                    tide_type = 'HighTide' if 'high' in tide_type.lower() else 'LowTide'
                
                self.cursor.execute("""
                    INSERT INTO TIDAL_DATA (TidalId, TideTime, TideType, Height, CreatedAt)
                    VALUES (?, ?, ?, ?, GETDATE())
                """, (
                    int(row['TidalId']),
                    pd.to_datetime(row.get('TideTime')) if pd.notna(row.get('TideTime')) else datetime.now(),
                    tide_type,
                    float(row.get('Height', 3)) if pd.notna(row.get('Height')) else 3
                ))
                inserted += 1
            except Exception as e:
                if inserted < 5:
                    print(f"  ⚠️  Row {row.get('TidalId')}: {e}")
                continue
                
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT TIDAL_DATA OFF")
        print(f"  ✅ Inserted {inserted} tidal records")
        return inserted
        
    def import_ais_data(self, limit=50000):
        """Import AIS_DATA from CSV"""
        print("\n" + "="*60)
        print("IMPORTING AIS_DATA")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "AIS_DATA.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path, nrows=limit)
        print(f"  📄 Loaded {len(df)} rows (limit: {limit})")
        
        self.cursor.execute("SET IDENTITY_INSERT AIS_DATA ON")
        
        inserted = 0
        batch = []
        batch_size = 1000
        
        for _, row in df.iterrows():
            try:
                batch.append((
                    int(row['AISId']),
                    int(row['VesselId']),
                    str(row['MMSI']),
                    float(row.get('Latitude', 18.94)),
                    float(row.get('Longitude', 72.84)),
                    float(row.get('Speed', 0)) if pd.notna(row.get('Speed')) else 0,
                    float(row.get('Course', 0)) if pd.notna(row.get('Course')) else 0,
                    float(row.get('Heading', 0)) if pd.notna(row.get('Heading')) else 0,
                    str(row.get('NavigationStatus', 'Under way using engine'))[:50],
                    pd.to_datetime(row.get('RecordedAt')) if pd.notna(row.get('RecordedAt')) else datetime.now(),
                    datetime.now()
                ))
                
                if len(batch) >= batch_size:
                    self.cursor.executemany("""
                        INSERT INTO AIS_DATA (AISId, VesselId, MMSI, Latitude, Longitude, Speed, Course, Heading,
                                             NavigationStatus, RecordedAt, FetchedAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, batch)
                    self.conn.commit()
                    inserted += len(batch)
                    print(f"  📦 Inserted {inserted}/{len(df)} AIS records", end='\r')
                    batch = []
                    
            except Exception as e:
                continue
                
        # Insert remaining
        if batch:
            try:
                self.cursor.executemany("""
                    INSERT INTO AIS_DATA (AISId, VesselId, MMSI, Latitude, Longitude, Speed, Course, Heading,
                                         NavigationStatus, RecordedAt, FetchedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch)
                self.conn.commit()
                inserted += len(batch)
            except Exception as e:
                print(f"  ⚠️  Final batch error: {e}")
                
        self.cursor.execute("SET IDENTITY_INSERT AIS_DATA OFF")
        print(f"\n  ✅ Inserted {inserted} AIS records")
        return inserted
        
    def import_channels(self):
        """Import CHANNELS from CSV"""
        print("\n" + "="*60)
        print("IMPORTING CHANNELS")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "CHANNELS.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        # Check column names
        print(f"  Columns: {list(df.columns)}")
        
        self.cursor.execute("SET IDENTITY_INSERT CHANNELS ON")
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                self.cursor.execute("""
                    INSERT INTO CHANNELS (ChannelId, PortId, ChannelName, ChannelLength, ChannelWidth, ChannelDepth,
                                         ChannelDepthAtChartDatum, OneWayOrTwoWay, MaxVesselLOA, MaxVesselBeam, MaxVesselDraft,
                                         TrafficSeparationScheme, SpeedLimit, TidalWindowRequired, PilotageCompulsory,
                                         TugEscortRequired, DayNightRestrictions, VisibilityMinimum, WindSpeedLimit,
                                         CurrentSpeedLimit, ChannelSegments, AnchorageAreaId, IsActive, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    int(row['ChannelId']),
                    int(row['PortId']),
                    row['ChannelName'],
                    float(row.get('ChannelLength', 5)) if pd.notna(row.get('ChannelLength')) else 5,
                    float(row.get('ChannelWidth', 200)) if pd.notna(row.get('ChannelWidth')) else 200,
                    float(row.get('ChannelDepth', 15)) if pd.notna(row.get('ChannelDepth')) else 15,
                    float(row.get('ChannelDepthAtChartDatum', 12)) if pd.notna(row.get('ChannelDepthAtChartDatum')) else 12,
                    row.get('OneWayOrTwoWay', 'TwoWay'),
                    float(row.get('MaxVesselLOA', 400)) if pd.notna(row.get('MaxVesselLOA')) else 400,
                    float(row.get('MaxVesselBeam', 65)) if pd.notna(row.get('MaxVesselBeam')) else 65,
                    float(row.get('MaxVesselDraft', 14)) if pd.notna(row.get('MaxVesselDraft')) else 14,
                    row.get('TrafficSeparationScheme', 'Yes'),
                    float(row.get('SpeedLimit', 12)) if pd.notna(row.get('SpeedLimit')) else 12,
                    bool(row.get('TidalWindowRequired', True)),
                    bool(row.get('PilotageCompulsory', True)),
                    bool(row.get('TugEscortRequired', False)),
                    row.get('DayNightRestrictions', 'None'),
                    float(row.get('VisibilityMinimum', 2)) if pd.notna(row.get('VisibilityMinimum')) else 2,
                    float(row.get('WindSpeedLimit', 25)) if pd.notna(row.get('WindSpeedLimit')) else 25,
                    float(row.get('CurrentSpeedLimit', 3)) if pd.notna(row.get('CurrentSpeedLimit')) else 3,
                    int(row.get('ChannelSegments', 1)) if pd.notna(row.get('ChannelSegments')) else 1,
                    int(row.get('AnchorageAreaId', 1)) if pd.notna(row.get('AnchorageAreaId')) else None,
                    1
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Row {row.get('ChannelId')}: {e}")
                continue
                
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT CHANNELS OFF")
        print(f"  ✅ Inserted {inserted} channels")
        return inserted
        
    def import_anchorages(self):
        """Import ANCHORAGES from CSV - matches actual DB schema"""
        print("\n" + "="*60)
        print("IMPORTING ANCHORAGES")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "ANCHORAGES.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        self.cursor.execute("SET IDENTITY_INSERT ANCHORAGES ON")
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                # CSV columns match DB: Depth, MaxVessels, CurrentOccupancy, AverageWaitingTime, STSCargoOpsPermitted, QuarantineAnchorage
                self.cursor.execute("""
                    INSERT INTO ANCHORAGES (AnchorageId, PortId, AnchorageName, AnchorageType, Latitude, Longitude,
                                           Depth, MaxVessels, CurrentOccupancy, MaxVesselLOA, MaxVesselDraft, 
                                           AverageWaitingTime, STSCargoOpsPermitted, QuarantineAnchorage, IsActive, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    int(row['AnchorageId']),
                    int(row['PortId']),
                    row['AnchorageName'],
                    row.get('AnchorageType', 'General'),
                    float(row.get('Latitude', 18.94)),
                    float(row.get('Longitude', 72.84)),
                    float(row.get('Depth', 15)) if pd.notna(row.get('Depth')) else 15,
                    int(row.get('MaxVessels', 10)) if pd.notna(row.get('MaxVessels')) else 10,
                    int(row.get('CurrentOccupancy', 0)) if pd.notna(row.get('CurrentOccupancy')) else 0,
                    float(row.get('MaxVesselLOA', 400)) if pd.notna(row.get('MaxVesselLOA')) else 400,
                    float(row.get('MaxVesselDraft', 15)) if pd.notna(row.get('MaxVesselDraft')) else 15,
                    float(row.get('AverageWaitingTime', 0)) if pd.notna(row.get('AverageWaitingTime')) else 0,
                    bool(row.get('STSCargoOpsPermitted', False)),
                    bool(row.get('QuarantineAnchorage', False)),
                    1
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Row {row.get('AnchorageId')}: {e}")
                continue
                
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT ANCHORAGES OFF")
        print(f"  ✅ Inserted {inserted} anchorages")
        return inserted
        
    def import_pilots(self):
        """Import PILOTS from CSV - CSV has PortCode, DB needs PortId"""
        print("\n" + "="*60)
        print("IMPORTING PILOTS")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "PILOTS.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        
        # Get PortId lookup
        self.cursor.execute("SELECT PortId, PortCode FROM PORTS")
        port_lookup = {r[1]: r[0] for r in self.cursor.fetchall()}
        print(f"  Port lookup: {port_lookup}")
        
        self.cursor.execute("SET IDENTITY_INSERT PILOTS ON")
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                port_code = row.get('PortCode', 'INNSA')
                port_id = port_lookup.get(port_code, 1)  # Default to 1 if not found
                
                self.cursor.execute("""
                    INSERT INTO PILOTS (PilotId, PortId, PilotName, LicenseNumber, LicenseClass, VesselTypeRestrictions,
                                       MaxVesselLOA, MaxVesselDraft, MaxVesselGT, NightPilotage, DeepDraftCertified,
                                       TankerEndorsement, LNGEndorsement, Status, ContactNumber, ExperienceYears, IsActive, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    int(row['PilotId']),
                    port_id,
                    row['PilotName'],
                    row.get('PilotCode', f'LIC{row["PilotId"]:04d}'),  # Use PilotCode as license
                    row.get('PilotClass', 'Class A'),
                    row.get('VesselTypeRestrictions', 'None'),
                    float(row.get('MaxVesselLOA', 400)) if pd.notna(row.get('MaxVesselLOA')) else 400,
                    float(row.get('MaxVesselDraft', 15)) if pd.notna(row.get('MaxVesselDraft')) else 15,
                    int(row.get('MaxVesselGT', 200000)) if pd.notna(row.get('MaxVesselGT')) else 200000,
                    bool(row.get('NightOperations', True)),  # CSV has NightOperations
                    bool(row.get('AdverseWeather', True)),   # Use AdverseWeather for DeepDraftCertified
                    bool(row.get('TankerEndorsement', True)),
                    bool(row.get('LNGEndorsement', False)),
                    row.get('Status', 'Available'),
                    row.get('ContactNumber', '+91-9900000000'),
                    int(row.get('ExperienceYears', 10)) if pd.notna(row.get('ExperienceYears')) else 10,
                    1
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Row {row.get('PilotId')}: {e}")
                continue
                
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT PILOTS OFF")
        print(f"  ✅ Inserted {inserted} pilots")
        return inserted
        
    def import_tugboats(self):
        """Import TUGBOATS from CSV - CSV has TugId and PortCode, DB needs TugboatId and PortId"""
        print("\n" + "="*60)
        print("IMPORTING TUGBOATS")
        print("="*60)
        
        csv_path = os.path.join(self.test_data_path, "TUGBOATS.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  Not found: {csv_path}")
            return 0
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")
        print(f"  CSV columns: {list(df.columns)}")
        
        # Get PortId lookup
        self.cursor.execute("SELECT PortId, PortCode FROM PORTS")
        port_lookup = {r[1]: r[0] for r in self.cursor.fetchall()}
        print(f"  Port lookup: {port_lookup}")
        
        self.cursor.execute("SET IDENTITY_INSERT TUGBOATS ON")
        
        inserted = 0
        for _, row in df.iterrows():
            try:
                port_code = row.get('PortCode', 'INNSA')
                port_id = port_lookup.get(port_code, 1)
                tug_id = int(row['TugId'])  # CSV has TugId not TugboatId
                
                self.cursor.execute("""
                    INSERT INTO TUGBOATS (TugboatId, PortId, TugboatName, IMO, TugType, BollardPull, EnginePower,
                                         LOA, Beam, Draft, YearBuilt, FirefightingCapability, OilSpillResponse,
                                         SalvageCapable, Status, CurrentLocation, FuelCapacity, CrewCapacity, IsActive, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
                """, (
                    tug_id,
                    port_id,
                    row['TugName'],  # CSV has TugName not TugboatName
                    str(row.get('IMONumber', f'TUG{tug_id:04d}')),  # CSV has IMONumber
                    row.get('TugType', 'ASD'),
                    float(row.get('BollardPull', 60)) if pd.notna(row.get('BollardPull')) else 60,
                    int(row.get('EnginePower', 4000)) if pd.notna(row.get('EnginePower')) else 4000,
                    float(row.get('Length', 30)) if pd.notna(row.get('Length')) else 30,  # CSV has Length not LOA
                    float(row.get('Beam', 12)) if pd.notna(row.get('Beam')) else 12,
                    float(row.get('Draft', 5)) if pd.notna(row.get('Draft')) else 5,
                    int(row.get('YearBuilt', 2020)) if pd.notna(row.get('YearBuilt')) else 2020,
                    bool(row.get('FiFiClass', True)),  # Use FiFiClass for firefighting
                    bool(row.get('OilSpillResponse', True)),
                    bool(row.get('SalvageCapable', False)),
                    row.get('Status', 'Available'),
                    row.get('CurrentLocation', 'Port'),
                    int(row.get('FuelCapacity', 100)) if pd.notna(row.get('FuelCapacity')) else 100,
                    int(row.get('CrewSize', 6)) if pd.notna(row.get('CrewSize')) else 6,  # CSV has CrewSize
                    1
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Row {row.get('TugId')}: {e}")
                continue
                
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT TUGBOATS OFF")
        print(f"  ✅ Inserted {inserted} tugboats")
        return inserted
        
    def get_table_counts(self):
        """Get current table counts"""
        tables = ['PORTS', 'TERMINALS', 'BERTHS', 'VESSELS', 'VESSEL_SCHEDULE', 
                  'WEATHER_DATA', 'TIDAL_DATA', 'AIS_DATA', 'CHANNELS', 'ANCHORAGES',
                  'PILOTS', 'TUGBOATS']
        
        print("\n" + "="*60)
        print("FINAL TABLE COUNTS")
        print("="*60)
        
        for table in tables:
            try:
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = self.cursor.fetchone()[0]
                print(f"  {table}: {count:,}")
            except Exception as e:
                print(f"  {table}: Error - {e}")
                
    def import_all(self, ais_limit=50000):
        """Run full import"""
        try:
            self.connect()
            
            print("\n" + "="*60)
            print("STARTING LOCAL DATABASE IMPORT FROM TEST_DATA")
            print(f"AIS Limit: {ais_limit:,}")
            print(f"Data Source: {self.test_data_path}")
            print("="*60)
            
            # Clear all tables first
            self.clear_all_tables()
            
            # Import in dependency order
            self.import_ports()
            self.import_terminals()
            self.import_berths()
            self.import_vessels()
            self.import_vessel_schedule()
            self.import_weather_data()
            self.import_tidal_data()
            self.import_ais_data(limit=ais_limit)
            self.import_channels()
            self.import_anchorages()
            self.import_pilots()
            self.import_tugboats()
            
            self.get_table_counts()
            
            print("\n" + "="*60)
            print("✅ IMPORT COMPLETE")
            print("="*60)
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()


if __name__ == "__main__":
    ais_limit = int(sys.argv[1]) if len(sys.argv) > 1 else 50000
    
    importer = TestDataImporter()
    importer.import_all(ais_limit=ais_limit)
