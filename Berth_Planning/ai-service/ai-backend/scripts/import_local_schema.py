"""
Local Database Import Script - Matches actual LocalDB schema
Schema based on actual INFORMATION_SCHEMA.COLUMNS inspection
"""

import pyodbc
import pandas as pd
import sys
import os
from datetime import datetime, timedelta
import random

class LocalSchemaImporter:
    def __init__(self):
        # LocalDB connection
        self.conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=(localdb)\\MSSQLLocalDB;"
            "DATABASE=BerthPlanning;"
            "Trusted_Connection=yes;"
        )
        self.conn = None
        self.cursor = None
        
        # CSV data paths
        self.mundra_data = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\documents\Data\Mundra"
        self.test_data = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\Test_Data"
        
    def connect(self):
        print("Connecting to LocalDB...")
        self.conn = pyodbc.connect(self.conn_str)
        self.cursor = self.conn.cursor()
        # Enable fast executemany for batch inserts
        self.cursor.fast_executemany = True
        print("✅ Connected to (localdb)\\MSSQLLocalDB - BerthPlanning")
        
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        print("Connection closed")
        
    def clear_table(self, table_name):
        """Clear table data before import"""
        try:
            self.cursor.execute(f"DELETE FROM {table_name}")
            self.conn.commit()
            print(f"  🗑️  Cleared {table_name}")
        except Exception as e:
            print(f"  ⚠️  Could not clear {table_name} (FK constraint likely)")
            self.conn.rollback()
            
    def clear_all_tables(self):
        """Clear all tables in correct order to handle FK constraints"""
        # Order: child tables first, then parent tables
        tables_to_clear = [
            'AIS_DATA', 'VESSEL_SCHEDULE', 'VESSEL_HISTORY',
            'WEATHER_DATA', 'TIDAL_DATA', 'UKC_DATA',
            'ALERTS_NOTIFICATIONS', 'BERTH_MAINTENANCE',
            'TUGBOATS', 'PILOTS', 'BERTHS',
            'ANCHORAGES', 'CHANNELS',
            'TERMINALS', 'VESSELS', 'PORTS'
        ]
        
        print("\n  Clearing tables in FK-safe order...")
        for table in tables_to_clear:
            try:
                self.cursor.execute(f"DELETE FROM {table}")
                self.conn.commit()
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                if self.cursor.fetchone()[0] == 0:
                    print(f"  🗑️  Cleared {table}")
            except Exception as e:
                self.conn.rollback()
                pass  # Table might not exist or other issue
        print("  ✅ Tables cleared")
            
    def import_ports(self):
        """Import PORTS data"""
        print("\n" + "="*60)
        print("IMPORTING PORTS")
        print("="*60)
        
        # Schema: PortId, PortName, PortCode, Country, City, TimeZone, 
        #         Latitude, Longitude, ContactEmail, ContactPhone, IsActive, CreatedAt, UpdatedAt
        ports = [
            (1, 'Mundra Port', 'INMUN', 'India', 'Mundra', 'Asia/Kolkata', 
             22.7411, 69.7060, 'port@mundra.com', '+91-2838-123456', True, datetime.now(), datetime.now()),
        ]
        
        self.cursor.execute("SET IDENTITY_INSERT PORTS ON")
        self.cursor.executemany("""
            INSERT INTO PORTS (PortId, PortName, PortCode, Country, City, TimeZone, 
                              Latitude, Longitude, ContactEmail, ContactPhone, IsActive, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ports)
        self.cursor.execute("SET IDENTITY_INSERT PORTS OFF")
        self.conn.commit()
        print(f"  ✅ Inserted {len(ports)} ports")
        
    def import_terminals(self):
        """Import TERMINALS data"""
        print("\n" + "="*60)
        print("IMPORTING TERMINALS")
        print("="*60)
        
        # Schema: TerminalId, PortId, TerminalName, TerminalCode, TerminalType,
        #         OperatorName, Latitude, Longitude, IsActive, CreatedAt, UpdatedAt
        terminals = [
            (1, 1, 'CT1 - Container Terminal 1', 'CT1', 'Container', 'APSEZ', 22.7411, 69.7060, True, datetime.now(), datetime.now()),
            (2, 1, 'CT2 - Container Terminal 2', 'CT2', 'Container', 'APSEZ', 22.7450, 69.7100, True, datetime.now(), datetime.now()),
            (3, 1, 'Coal Terminal', 'COAL', 'Bulk', 'APSEZ', 22.7500, 69.7150, True, datetime.now(), datetime.now()),
            (4, 1, 'Liquid Terminal', 'LIQ', 'Liquid', 'APSEZ', 22.7350, 69.7000, True, datetime.now(), datetime.now()),
        ]
        
        self.cursor.execute("SET IDENTITY_INSERT TERMINALS ON")
        self.cursor.executemany("""
            INSERT INTO TERMINALS (TerminalId, PortId, TerminalName, TerminalCode, TerminalType,
                                  OperatorName, Latitude, Longitude, IsActive, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, terminals)
        self.cursor.execute("SET IDENTITY_INSERT TERMINALS OFF")
        self.conn.commit()
        print(f"  ✅ Inserted {len(terminals)} terminals")
        
    def import_berths(self):
        """Import BERTHS data from CSV"""
        print("\n" + "="*60)
        print("IMPORTING BERTHS")
        print("="*60)
        
        csv_path = os.path.join(self.mundra_data, "Mundra_Port_Berth_Details.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  CSV not found: {csv_path}")
            return
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")
        
        # Schema: BerthId, TerminalId, BerthName, BerthCode, Length, Depth, MaxDraft,
        #         BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude, CreatedAt, UpdatedAt
        berths = []
        for i, row in df.iterrows():
            berths.append((
                i + 1,  # BerthId
                ((i % 4) + 1),  # TerminalId (distribute across terminals)
                row.get('Berth_Name', f'Berth {i+1}'),
                row.get('Berth_Code', f'B{i+1:03d}'),
                float(row.get('Berth_Length', row.get('Length', 300))),
                float(row.get('Berth_Depth', row.get('Depth', 15))),
                float(row.get('Max_Draft', row.get('Depth', 14))),
                row.get('Berth_Type', 'General'),
                int(row.get('Number_of_Cranes', row.get('Cranes', 0))),
                int(row.get('Bollard_Count', 10)),
                True,
                22.7411 + random.uniform(-0.01, 0.01),
                69.7060 + random.uniform(-0.01, 0.01),
                datetime.now(),
                datetime.now()
            ))
        
        self.cursor.execute("SET IDENTITY_INSERT BERTHS ON")
        self.cursor.executemany("""
            INSERT INTO BERTHS (BerthId, TerminalId, BerthName, BerthCode, Length, Depth, MaxDraft,
                               BerthType, NumberOfCranes, BollardCount, IsActive, Latitude, Longitude, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, berths)
        self.cursor.execute("SET IDENTITY_INSERT BERTHS OFF")
        self.conn.commit()
        print(f"  ✅ Inserted {len(berths)} berths")
        
    def import_vessels(self):
        """Import VESSELS data from CSV"""
        print("\n" + "="*60)
        print("IMPORTING VESSELS")
        print("="*60)
        
        csv_path = os.path.join(self.mundra_data, "Mundra_Port_Vessels.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  CSV not found: {csv_path}")
            return
            
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")
        
        # Schema: VesselId, VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft,
        #         GrossTonnage, CargoType, CargoVolume, Priority, CreatedAt, UpdatedAt
        
        # Sample: take first 500 vessels to start (can be increased)
        df_sample = df.head(500)
        
        vessels = []
        for i, row in df_sample.iterrows():
            vessels.append((
                i + 1,  # VesselId
                row.get('Vessel_Name', row.get('VesselName', f'Vessel {i+1}')),
                str(row.get('IMO', row.get('IMO_Number', f'IMO{9000000+i}'))),
                str(row.get('MMSI', f'{200000000+i}')),
                row.get('Vessel_Type', row.get('VesselType', 'Cargo')),
                float(row.get('LOA', row.get('Length', 200))),
                float(row.get('Beam', row.get('Width', 30))),
                float(row.get('Draft', row.get('Current_Draft', 10))),
                int(row.get('Gross_Tonnage', row.get('GrossTonnage', 50000))),
                row.get('Cargo_Type', row.get('CargoType', 'General')),
                float(row.get('Cargo_Volume', row.get('CargoVolume', 10000))),
                min(max(int(row.get('Priority', 2)), 1), 3),  # Priority must be 1-3
                datetime.now(),
                datetime.now()
            ))
        
        self.cursor.execute("SET IDENTITY_INSERT VESSELS ON")
        self.cursor.executemany("""
            INSERT INTO VESSELS (VesselId, VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft,
                                GrossTonnage, CargoType, CargoVolume, Priority, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, vessels)
        self.cursor.execute("SET IDENTITY_INSERT VESSELS OFF")
        self.conn.commit()
        print(f"  ✅ Inserted {len(vessels)} vessels")
        return len(vessels)
        
    def import_vessel_schedule(self):
        """Import VESSEL_SCHEDULE data from CSV"""
        print("\n" + "="*60)
        print("IMPORTING VESSEL_SCHEDULE")
        print("="*60)
        
        csv_path = os.path.join(self.mundra_data, "Mundra_Port_Vessel_Schedules.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  CSV not found: {csv_path}")
            return
            
        df = pd.read_csv(csv_path, low_memory=False)
        print(f"  📄 Loaded {len(df)} rows from CSV")
        
        self.cursor.execute("SET IDENTITY_INSERT VESSEL_SCHEDULE ON")
        
        # Schema: ScheduleId, VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, ATD,
        #         Status, DwellTime, WaitingTime, OptimizationScore, IsOptimized, ConflictCount, CreatedAt, UpdatedAt
        
        # Get berth count
        self.cursor.execute("SELECT COUNT(*) FROM BERTHS")
        berth_count = self.cursor.fetchone()[0] or 20
        
        # Get vessel count
        self.cursor.execute("SELECT COUNT(*) FROM VESSELS")
        vessel_count = self.cursor.fetchone()[0] or 100
        
        schedules = []
        now = datetime.now()
        
        for i, row in df.head(500).iterrows():  # Limit to 500 schedules initially
            vessel_id = (i % vessel_count) + 1
            berth_id = (i % berth_count) + 1
            
            # Parse dates
            eta = now + timedelta(hours=random.randint(-48, 168))
            etd = eta + timedelta(hours=random.randint(12, 72))
            predicted_eta = eta + timedelta(minutes=random.randint(-60, 60))
            
            schedules.append((
                i + 1,  # ScheduleId
                vessel_id,
                berth_id,
                eta,  # ETA
                predicted_eta,  # PredictedETA
                etd,  # ETD
                None,  # ATA
                None,  # ATB
                None,  # ATD
                random.choice(['Scheduled', 'Approaching', 'Berthed', 'Departed', 'Cancelled']),
                random.randint(12, 72),  # DwellTime (hours)
                random.randint(0, 12),  # WaitingTime (hours)
                random.uniform(0.5, 1.0),  # OptimizationScore
                random.choice([True, False]),  # IsOptimized
                random.randint(0, 3),  # ConflictCount
                now,
                now
            ))
        
        self.cursor.executemany("""
            INSERT INTO VESSEL_SCHEDULE (ScheduleId, VesselId, BerthId, ETA, PredictedETA, ETD, ATA, ATB, ATD,
                                        Status, DwellTime, WaitingTime, OptimizationScore, IsOptimized, ConflictCount, CreatedAt, UpdatedAt)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, schedules)
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT VESSEL_SCHEDULE OFF")
        print(f"  ✅ Inserted {len(schedules)} vessel schedules")
        
    def import_weather_data(self):
        """Import WEATHER_DATA - generate realistic data"""
        print("\n" + "="*60)
        print("IMPORTING WEATHER_DATA")
        print("="*60)
        
        self.cursor.execute("SET IDENTITY_INSERT WEATHER_DATA ON")
        
        # Schema: WeatherId, RecordedAt, WindSpeed, WindDirection, Visibility,
        #         WaveHeight, Temperature, Precipitation, WeatherCondition, IsAlert, FetchedAt
        
        weather_data = []
        now = datetime.now()
        
        # Generate 1 year of hourly weather data
        for i in range(8760):  # 365 days * 24 hours
            recorded_at = now - timedelta(hours=8760-i)
            
            # Seasonal temperature variation
            day_of_year = recorded_at.timetuple().tm_yday
            base_temp = 25 + 10 * (1 - abs(day_of_year - 180) / 180)  # Peak in summer
            temp = base_temp + random.uniform(-5, 5)
            
            wind_speed = random.uniform(5, 25)
            wind_dir = random.randint(0, 360)
            visibility = random.randint(5, 20)  # km
            wave_height = random.uniform(0.5, 3.0)
            precip = 0 if random.random() > 0.2 else random.uniform(0, 10)
            
            conditions = ['Clear', 'Cloudy', 'Partly Cloudy', 'Overcast', 'Rain', 'Drizzle', 'Fog']
            condition = random.choice(conditions)
            
            is_alert = wind_speed > 20 or wave_height > 2.5 or visibility < 5
            
            weather_data.append((
                i + 1,
                recorded_at,
                wind_speed,
                wind_dir,
                visibility,
                wave_height,
                temp,
                precip,
                condition,
                is_alert,
                recorded_at
            ))
        
        # Insert in chunks
        chunk_size = 1000
        for j in range(0, len(weather_data), chunk_size):
            chunk = weather_data[j:j+chunk_size]
            self.cursor.executemany("""
                INSERT INTO WEATHER_DATA (WeatherId, RecordedAt, WindSpeed, WindDirection, Visibility,
                                         WaveHeight, Temperature, Precipitation, WeatherCondition, IsAlert, FetchedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, chunk)
            self.conn.commit()
            print(f"  📦 Inserted {j+len(chunk)}/{len(weather_data)} weather records", end='\r')
        
        self.cursor.execute("SET IDENTITY_INSERT WEATHER_DATA OFF")
        print(f"\n  ✅ Inserted {len(weather_data)} weather records")
        
    def import_tidal_data(self):
        """Import TIDAL_DATA - generate realistic tidal patterns"""
        print("\n" + "="*60)
        print("IMPORTING TIDAL_DATA")
        print("="*60)
        
        self.cursor.execute("SET IDENTITY_INSERT TIDAL_DATA ON")
        
        # Schema: TidalId, TideTime, TideType, Height, CreatedAt
        
        tidal_data = []
        now = datetime.now()
        
        # Generate 1 year of tidal data (2 high/2 low tides per day)
        for day in range(365):
            base_date = now - timedelta(days=365-day)
            
            # 4 tides per day approximately
            for tide_num in range(4):
                tide_time = base_date + timedelta(hours=tide_num * 6 + random.uniform(-0.5, 0.5))
                tide_type = 'HighTide' if tide_num % 2 == 0 else 'LowTide'
                
                # Spring/neap tide variation
                lunar_day = (day % 14)
                spring_factor = 1 + 0.3 * (1 - abs(lunar_day - 7) / 7)
                
                if tide_type == 'High':
                    height = 4.0 * spring_factor + random.uniform(-0.3, 0.3)
                else:
                    height = 1.5 / spring_factor + random.uniform(-0.2, 0.2)
                
                tidal_data.append((
                    len(tidal_data) + 1,
                    tide_time,
                    tide_type,
                    height,
                    now
                ))
        
        self.cursor.executemany("""
            INSERT INTO TIDAL_DATA (TidalId, TideTime, TideType, Height, CreatedAt)
            VALUES (?, ?, ?, ?, ?)
        """, tidal_data)
        self.conn.commit()
        self.cursor.execute("SET IDENTITY_INSERT TIDAL_DATA OFF")
        print(f"  ✅ Inserted {len(tidal_data)} tidal records")
        
    def import_ais_data(self, limit=50000):
        """Import AIS_DATA from CSV"""
        print("\n" + "="*60)
        print("IMPORTING AIS_DATA")
        print("="*60)
        
        csv_path = os.path.join(self.mundra_data, "Mundra_Port_AIS_Data.csv")
        if not os.path.exists(csv_path):
            print(f"  ⚠️  CSV not found: {csv_path}")
            return
        
        # Get vessel count for distributing AIS records
        self.cursor.execute("SELECT COUNT(*) FROM VESSELS")
        vessel_count = self.cursor.fetchone()[0] or 100
        
        self.cursor.execute("SET IDENTITY_INSERT AIS_DATA ON")
        
        # Schema: AISId, VesselId, MMSI, Latitude, Longitude, Speed, Course, Heading,
        #         NavigationStatus, RecordedAt, FetchedAt
        
        print(f"  📄 Reading CSV in chunks (limit: {limit})...")
        
        total_inserted = 0
        chunk_size = 10000
        
        for chunk_df in pd.read_csv(csv_path, chunksize=chunk_size, low_memory=False):
            if total_inserted >= limit:
                break
                
            rows_to_insert = min(len(chunk_df), limit - total_inserted)
            chunk_df = chunk_df.head(rows_to_insert)
            
            ais_records = []
            for i, row in chunk_df.iterrows():
                vessel_id = (total_inserted + len(ais_records)) % vessel_count + 1
                
                # Parse timestamp
                try:
                    recorded_at = pd.to_datetime(row.get('Timestamp', row.get('timestamp', datetime.now())))
                    if pd.isna(recorded_at):
                        recorded_at = datetime.now() - timedelta(hours=random.randint(0, 8760))
                except:
                    recorded_at = datetime.now() - timedelta(hours=random.randint(0, 8760))
                
                ais_records.append((
                    total_inserted + len(ais_records) + 1,  # AISId
                    vessel_id,
                    str(row.get('MMSI', f'{200000000 + vessel_id}')),
                    float(row.get('Latitude', row.get('LAT', 22.7411 + random.uniform(-0.1, 0.1)))),
                    float(row.get('Longitude', row.get('LON', 69.7060 + random.uniform(-0.1, 0.1)))),
                    float(row.get('Speed', row.get('SOG', random.uniform(0, 15)))),
                    float(row.get('Course', row.get('COG', random.uniform(0, 360)))),
                    float(row.get('Heading', row.get('HDG', random.uniform(0, 360)))),
                    str(row.get('Navigation_Status', row.get('NavStatus', 'Under way using engine')))[:50],
                    recorded_at,
                    datetime.now()
                ))
            
            try:
                self.cursor.executemany("""
                    INSERT INTO AIS_DATA (AISId, VesselId, MMSI, Latitude, Longitude, Speed, Course, Heading,
                                         NavigationStatus, RecordedAt, FetchedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, ais_records)
                self.conn.commit()
                total_inserted += len(ais_records)
                print(f"  📦 Inserted {total_inserted}/{limit} AIS records", end='\r')
            except Exception as e:
                print(f"\n  ⚠️  Chunk error: {e}")
                continue
        
        self.cursor.execute("SET IDENTITY_INSERT AIS_DATA OFF")
        print(f"\n  ✅ Inserted {total_inserted} AIS records")
        
    def seed_supporting_tables(self):
        """Seed supporting tables: CHANNELS, ANCHORAGES, UKC_DATA, PILOTS, TUGBOATS"""
        print("\n" + "="*60)
        print("SEEDING SUPPORTING TABLES")
        print("="*60)
        
        # Check if these tables exist
        self.cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_NAME IN ('CHANNELS', 'ANCHORAGES', 'UKC_DATA', 'PILOTS', 'TUGBOATS')
        """)
        existing_tables = [row[0] for row in self.cursor.fetchall()]
        
        if 'CHANNELS' in existing_tables:
            try:
                self.clear_table("CHANNELS")
                self.cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'CHANNELS'")
                cols = [r[0] for r in self.cursor.fetchall()]
                print(f"  CHANNELS columns: {cols}")
            except Exception as e:
                print(f"  ⚠️  CHANNELS error: {e}")
                
        if 'PILOTS' in existing_tables:
            try:
                self.clear_table("PILOTS")
                self.cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'PILOTS'")
                cols = [r[0] for r in self.cursor.fetchall()]
                print(f"  PILOTS columns: {cols}")
            except Exception as e:
                print(f"  ⚠️  PILOTS error: {e}")
                
        if 'TUGBOATS' in existing_tables:
            try:
                self.clear_table("TUGBOATS")
                self.cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'TUGBOATS'")
                cols = [r[0] for r in self.cursor.fetchall()]
                print(f"  TUGBOATS columns: {cols}")
            except Exception as e:
                print(f"  ⚠️  TUGBOATS error: {e}")
        
        print(f"  ✅ Supporting tables prepared")
        
    def get_table_counts(self):
        """Get current table counts"""
        tables = ['PORTS', 'TERMINALS', 'BERTHS', 'VESSELS', 'VESSEL_SCHEDULE', 
                  'WEATHER_DATA', 'TIDAL_DATA', 'AIS_DATA']
        
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
            print("STARTING LOCAL DATABASE IMPORT")
            print(f"AIS Limit: {ais_limit:,}")
            print("="*60)
            
            # Clear all tables first (in FK-safe order)
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
            self.seed_supporting_tables()
            
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
    
    importer = LocalSchemaImporter()
    importer.import_all(ais_limit=ais_limit)
