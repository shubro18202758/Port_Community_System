"""
Fast Local Database Import for Berth Planning Demo
Imports Mundra port data into LocalDB for rapid prototyping
"""
import pyodbc
import pandas as pd
from datetime import datetime
import os
import re
import random

# LOCAL DB CONNECTION - Much faster than remote!
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "Server=(localdb)\\MSSQLLocalDB;"
    "Database=BerthPlanning;"
    "Trusted_Connection=yes;"
)

# Data sources
MUNDRA_PATH = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\documents\Data\Mundra"
TEST_DATA_PATH = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\Test_Data"
PORT_CODE = "INMUN"


class LocalDataImporter:
    def __init__(self):
        self.conn = None
        self.cursor = None
        
    def connect(self):
        print("Connecting to LocalDB...")
        self.conn = pyodbc.connect(CONNECTION_STRING)
        self.cursor = self.conn.cursor()
        # Enable fast inserts
        self.cursor.fast_executemany = True
        print("✅ Connected to LocalDB")
        
    def close(self):
        if self.conn:
            self.conn.close()
            print("Connection closed")

    def clear_tables(self):
        """Clear existing data for fresh import"""
        print("\n🗑️  Clearing existing data...")
        tables = ['AIS_DATA', 'VESSEL_SCHEDULE', 'WEATHER_DATA', 'TIDAL_DATA', 
                  'RESOURCES', 'VESSELS', 'BERTHS', 'UKC_DATA', 'VESSEL_HISTORY',
                  'ALERTS_NOTIFICATIONS', 'BERTH_MAINTENANCE', 'CONFLICTS']
        for table in tables:
            try:
                self.cursor.execute(f"DELETE FROM [{table}]")
                self.conn.commit()
                print(f"   ✓ Cleared {table}")
            except Exception as e:
                pass  # Table might not exist or have FK constraints

    def derive_vessel_type(self, cargo_type):
        """Derive vessel type from cargo"""
        if not cargo_type or pd.isna(cargo_type):
            return 'Cargo'
        cargo = str(cargo_type).lower()
        if 'container' in cargo:
            return 'Container'
        elif 'tanker' in cargo or 'oil' in cargo or 'crude' in cargo:
            return 'Tanker'
        elif 'bulk' in cargo or 'coal' in cargo or 'iron' in cargo:
            return 'Bulk Carrier'
        elif 'lng' in cargo or 'lpg' in cargo or 'gas' in cargo:
            return 'LNG Carrier'
        else:
            return 'Cargo'

    def derive_berth_type(self, cargo_allowed):
        """Derive berth type from cargo"""
        if not cargo_allowed or pd.isna(cargo_allowed):
            return 'Cargo'
        cargo = str(cargo_allowed).lower()
        if 'container' in cargo:
            return 'Container'
        elif 'tanker' in cargo or 'liquid' in cargo:
            return 'Tanker'
        elif 'bulk' in cargo:
            return 'Bulk'
        else:
            return 'Cargo'

    def import_vessels(self):
        """Import VESSELS from Mundra data"""
        print("\n" + "="*60)
        print("IMPORTING VESSELS")
        print("="*60)
        
        csv_path = os.path.join(MUNDRA_PATH, "VESSELS.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")
        
        now = datetime.now()
        inserted = 0
        
        for _, row in df.iterrows():
            try:
                vessel_name = str(row.get('vessel_name', f'Vessel_{inserted}'))[:100]
                imo = str(row.get('imo', ''))
                imo_number = re.sub(r'\D', '', imo)[:10] if imo else None
                mmsi = str(row.get('mmsi', ''))
                mmsi_number = re.sub(r'\D', '', mmsi)[:20] if mmsi else None
                vessel_type = self.derive_vessel_type(row.get('cargo_type'))
                
                self.cursor.execute("""
                    INSERT INTO VESSELS (VesselName, IMONumber, MMSI, CallSign, FlagState,
                                        VesselType, LOA, Beam, Draft, GrossTonnage, NetTonnage,
                                        DeadweightTonnage, YearBuilt, Status, CurrentPhase,
                                        CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vessel_name, imo_number, mmsi_number,
                    str(row.get('call_sign', ''))[:20] if pd.notna(row.get('call_sign')) else None,
                    str(row.get('flag', 'Unknown'))[:50],
                    vessel_type,
                    float(row['loa_m']) if pd.notna(row.get('loa_m')) else 200.0,
                    float(row['beam_m']) if pd.notna(row.get('beam_m')) else 32.0,
                    float(row['draft_m']) if pd.notna(row.get('draft_m')) else 12.0,
                    int(row['gt']) if pd.notna(row.get('gt')) else 50000,
                    int(row['gt'] * 0.6) if pd.notna(row.get('gt')) else 30000,
                    int(row['dwt']) if pd.notna(row.get('dwt')) else 60000,
                    int(row['year_built']) if pd.notna(row.get('year_built')) else 2015,
                    'Active', 'Scheduled', now, now
                ))
                inserted += 1
            except Exception as e:
                if inserted < 3:
                    print(f"  ⚠️  Error: {e}")
        
        self.conn.commit()
        print(f"  ✅ Inserted {inserted} vessels")
        return inserted

    def import_berths(self):
        """Import BERTHS from Mundra data"""
        print("\n" + "="*60)
        print("IMPORTING BERTHS")
        print("="*60)
        
        csv_path = os.path.join(MUNDRA_PATH, "BERTHS.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")
        
        now = datetime.now()
        inserted = 0
        
        for idx, row in df.iterrows():
            try:
                equipment = str(row.get('equipment', ''))
                cranes = 0
                crane_match = re.search(r'(\d+)', equipment)
                if crane_match and 'crane' in equipment.lower():
                    cranes = int(crane_match.group(1))
                berth_type = self.derive_berth_type(row.get('cargo_allowed'))
                
                self.cursor.execute("""
                    INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode,
                                       Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType,
                                       NumberOfCranes, BollardCount, IsActive, Latitude, Longitude,
                                       CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    1, 1, PORT_CODE,
                    f"Berth {idx+1}",
                    str(row['berth_id']),
                    float(row['max_loa_m']) if pd.notna(row.get('max_loa_m')) else 300.0,
                    float(row['max_draft_m']) if pd.notna(row.get('max_draft_m')) else 15.0,
                    float(row['max_draft_m']) if pd.notna(row.get('max_draft_m')) else 15.0,
                    float(row['max_loa_m']) if pd.notna(row.get('max_loa_m')) else 300.0,
                    float(row['max_beam_m']) if pd.notna(row.get('max_beam_m')) else 50.0,
                    berth_type, cranes, 10, True,
                    22.4 + random.uniform(-0.01, 0.01),
                    69.7 + random.uniform(-0.01, 0.01),
                    now, now
                ))
                inserted += 1
            except Exception as e:
                if inserted < 3:
                    print(f"  ⚠️  Error: {e}")
        
        self.conn.commit()
        print(f"  ✅ Inserted {inserted} berths")
        return inserted

    def import_vessel_schedule(self):
        """Import VESSEL_SCHEDULE with constraint fixes"""
        print("\n" + "="*60)
        print("IMPORTING VESSEL_SCHEDULE")
        print("="*60)
        
        csv_path = os.path.join(MUNDRA_PATH, "VESSEL_SCHEDULE.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")
        
        # Get mappings
        self.cursor.execute("SELECT VesselId, VesselName FROM VESSELS")
        vessel_map = {row[1]: row[0] for row in self.cursor.fetchall()}
        self.cursor.execute("SELECT BerthId, BerthCode FROM BERTHS")
        berth_map = {row[1]: row[0] for row in self.cursor.fetchall()}
        
        now = datetime.now()
        inserted = 0
        
        status_map = {
            'completed': 'Departed', 'in_progress': 'Berthed', 'berthed': 'Berthed',
            'scheduled': 'Scheduled', 'waiting': 'Approaching', 'departed': 'Departed',
            'cancelled': 'Cancelled'
        }
        
        for _, row in df.iterrows():
            try:
                vessel_name = str(row.get('vessel_name', ''))
                vessel_id = vessel_map.get(vessel_name, 1)
                berth_code = str(row.get('berth_id', ''))
                berth_id = berth_map.get(berth_code, 1)
                
                eta = pd.to_datetime(row.get('eta'), errors='coerce')
                atb = pd.to_datetime(row.get('atb'), errors='coerce')
                atd = pd.to_datetime(row.get('atd'), errors='coerce')
                
                status_raw = str(row.get('status', 'scheduled')).lower().strip()
                status = status_map.get(status_raw, 'Scheduled')
                dwell_time = max(1, int(row['dwell_hours'])) if pd.notna(row.get('dwell_hours')) else 1
                waiting_time = max(0, int(row['waiting_hours'])) if pd.notna(row.get('waiting_hours')) else 0
                
                self.cursor.execute("""
                    INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD,
                                                ATA, ATB, ATD, Status, DwellTime, WaitingTime,
                                                CargoType, CargoQuantity, CargoUnit, CargoOperation,
                                                PortCode, VoyageNumber, ShippingLine, TerminalType,
                                                TugsAssigned, PilotsAssigned, WaitingTimeHours,
                                                DwellTimeHours, IsOptimized, ConflictCount,
                                                CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vessel_id, berth_id, 
                    eta if pd.notna(eta) else None, eta if pd.notna(eta) else None, 
                    atd if pd.notna(atd) else None,
                    atb if pd.notna(atb) else None, atb if pd.notna(atb) else None, 
                    atd if pd.notna(atd) else None,
                    status, dwell_time, waiting_time,
                    str(row.get('cargo_type', 'general'))[:50],
                    float(row['cargo_volume_cbm']) if pd.notna(row.get('cargo_volume_cbm')) else None,
                    'CBM', 'Loading', PORT_CODE,
                    f"VOY{inserted+1:05d}",
                    str(row.get('line_operator', 'Unknown'))[:50],
                    str(row.get('terminal_code', 'General'))[:50],
                    int(row['tugs_assigned']) if pd.notna(row.get('tugs_assigned')) else 1,
                    int(row['pilots_assigned']) if pd.notna(row.get('pilots_assigned')) else 1,
                    float(row['waiting_hours']) if pd.notna(row.get('waiting_hours')) else None,
                    float(row['dwell_hours']) if pd.notna(row.get('dwell_hours')) else None,
                    False, 0, now, now
                ))
                inserted += 1
                
                if inserted % 2000 == 0:
                    self.conn.commit()
                    print(f"    ... {inserted} records")
                    
            except Exception as e:
                if inserted < 3:
                    print(f"  ⚠️  Error: {e}")
        
        self.conn.commit()
        print(f"  ✅ Inserted {inserted} schedules")
        return inserted

    def import_weather_data(self):
        """Import WEATHER_DATA"""
        print("\n" + "="*60)
        print("IMPORTING WEATHER_DATA")
        print("="*60)
        
        csv_path = os.path.join(MUNDRA_PATH, "WEATHER_DATA.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")
        
        now = datetime.now()
        inserted = 0
        
        for _, row in df.iterrows():
            try:
                recorded_at = pd.to_datetime(row.get('ts_hour'), errors='coerce')
                recorded_at = recorded_at if pd.notna(recorded_at) else now
                
                wind_speed_mps = float(row['wind_speed_mps']) if pd.notna(row.get('wind_speed_mps')) else 5.0
                wind_gust_mps = float(row['wind_gust_mps']) if pd.notna(row.get('wind_gust_mps')) else 8.0
                rain_mm = float(row['rain_mm']) if pd.notna(row.get('rain_mm')) else 0.0
                visibility_km = float(row['visibility_km']) if pd.notna(row.get('visibility_km')) else 10.0
                storm_flag = int(row['storm_flag']) if pd.notna(row.get('storm_flag')) else 0
                
                wind_speed_knots = wind_speed_mps * 1.94384
                wave_height = 0.21 * ((wind_speed_mps + wind_gust_mps) / 2) ** 1.5 / 10
                
                if storm_flag:
                    condition = 'Storm'
                elif rain_mm > 10:
                    condition = 'Rainy'
                elif wind_speed_mps > 15:
                    condition = 'Windy'
                elif visibility_km < 2:
                    condition = 'Foggy'
                else:
                    condition = 'Clear'
                
                self.cursor.execute("""
                    INSERT INTO WEATHER_DATA (PortId, PortCode, RecordedAt, WindSpeed,
                                             WindDirection, WindDirectionText, Visibility,
                                             WaveHeight, Temperature, Precipitation,
                                             WeatherCondition, Climate, Season, IsAlert, FetchedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    1, PORT_CODE, recorded_at, round(wind_speed_knots, 2),
                    random.randint(0, 359), 'N', int(visibility_km * 1000),
                    round(wave_height, 2), 28.0, rain_mm, condition,
                    'Tropical',
                    'Monsoon' if recorded_at.month in [6, 7, 8, 9] else 'Dry',
                    storm_flag == 1, now
                ))
                inserted += 1
                
                if inserted % 2000 == 0:
                    self.conn.commit()
                    print(f"    ... {inserted} records")
                    
            except Exception as e:
                if inserted < 3:
                    print(f"  ⚠️  Error: {e}")
        
        self.conn.commit()
        print(f"  ✅ Inserted {inserted} weather records")
        return inserted

    def import_tidal_data(self):
        """Import TIDAL_DATA"""
        print("\n" + "="*60)
        print("IMPORTING TIDAL_DATA")
        print("="*60)
        
        csv_path = os.path.join(MUNDRA_PATH, "TIDAL_DATA.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")
        
        now = datetime.now()
        inserted = 0
        
        for _, row in df.iterrows():
            try:
                tide_time = pd.to_datetime(row.get('ts'), errors='coerce')
                tide_time = tide_time if pd.notna(tide_time) else now
                phase = str(row.get('tide_phase', 'ebb')).lower()
                tide_type = 'HighTide' if phase == 'flood' else 'LowTide'
                height = float(row['tide_height_m']) if pd.notna(row.get('tide_height_m')) else 2.0
                
                self.cursor.execute("""
                    INSERT INTO TIDAL_DATA (TideTime, TideType, Height, CreatedAt)
                    VALUES (?, ?, ?, ?)
                """, (tide_time, tide_type, height, now))
                inserted += 1
            except Exception as e:
                if inserted < 3:
                    print(f"  ⚠️  Error: {e}")
        
        self.conn.commit()
        print(f"  ✅ Inserted {inserted} tidal records")
        return inserted

    def import_ais_data(self, limit=None):
        """Import AIS_DATA in chunks - FAST local import"""
        print("\n" + "="*60)
        print("IMPORTING AIS_DATA (Local - FAST)")
        print("="*60)
        
        csv_path = os.path.join(MUNDRA_PATH, "AIS_DATA.csv")
        
        # Get vessel IDs
        self.cursor.execute("SELECT VesselId FROM VESSELS")
        vessel_ids = [row[0] for row in self.cursor.fetchall()]
        if not vessel_ids:
            vessel_ids = [1]
        print(f"  Distributing across {len(vessel_ids)} vessels")
        
        chunk_size = 50000  # Bigger chunks for local
        total_inserted = 0
        now = datetime.now()
        
        for chunk_num, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
            if limit and total_inserted >= limit:
                break
                
            print(f"  📦 Chunk {chunk_num + 1} ({len(chunk)} rows)...")
            
            batch_data = []
            for idx, row in chunk.iterrows():
                if limit and total_inserted >= limit:
                    break
                    
                vessel_id = vessel_ids[total_inserted % len(vessel_ids)]
                
                try:
                    recorded_at = pd.to_datetime(row.get('ts'), errors='coerce')
                    if pd.isna(recorded_at):
                        recorded_at = now
                except:
                    recorded_at = now
                
                lat = max(-90, min(90, float(row['lat']) if pd.notna(row.get('lat')) else 22.4))
                lon = max(-180, min(180, float(row['lon']) if pd.notna(row.get('lon')) else 69.7))
                speed = max(0, float(row['sog_kn']) if pd.notna(row.get('sog_kn')) else 0.0)
                course = max(0, min(360, float(row['cog_deg']) if pd.notna(row.get('cog_deg')) else 0.0))
                
                nav_status = str(row.get('nav_status', 'under_way')).lower()
                nav_map = {'at_anchor': 'At Anchor', 'under_way': 'Under Way', 'moored': 'Moored'}
                nav_text = nav_map.get(nav_status, 'Under Way')
                
                batch_data.append((
                    vessel_id, None, PORT_CODE, 'Cargo',
                    lat, lon, speed, course, course,
                    nav_text, 0, 'Approaching', recorded_at, now
                ))
                total_inserted += 1
            
            # Batch insert
            self.cursor.executemany("""
                INSERT INTO AIS_DATA (VesselId, MMSI, PortCode, VesselType,
                                     Latitude, Longitude, Speed, Course, Heading,
                                     NavigationStatus, NavigationStatusCode,
                                     Phase, RecordedAt, FetchedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch_data)
            
            self.conn.commit()
            print(f"    ✓ Total: {total_inserted:,}")
        
        print(f"  ✅ Inserted {total_inserted:,} AIS records")
        return total_inserted

    def import_resources(self):
        """Import RESOURCES"""
        print("\n" + "="*60)
        print("IMPORTING RESOURCES")
        print("="*60)
        
        csv_path = os.path.join(MUNDRA_PATH, "RESOURCES.csv")
        if not os.path.exists(csv_path):
            print("  ⚠️  No RESOURCES.csv found, creating default resources")
            now = datetime.now()
            resources = [
                ('Crane', 'Mobile Crane 1', 5),
                ('Crane', 'Mobile Crane 2', 5),
                ('Tugboat', 'Harbor Tug 1', 3),
                ('Tugboat', 'Harbor Tug 2', 3),
                ('Pilot', 'Pilot Team A', 4),
                ('Pilot', 'Pilot Team B', 4),
                ('Labor', 'Dock Workers', 50),
                ('Mooring', 'Mooring Team', 10),
            ]
            for rtype, rname, cap in resources:
                self.cursor.execute("""
                    INSERT INTO RESOURCES (ResourceType, ResourceName, Capacity, IsAvailable, CreatedAt)
                    VALUES (?, ?, ?, ?, ?)
                """, (rtype, rname, cap, True, now))
            self.conn.commit()
            print(f"  ✅ Inserted {len(resources)} default resources")
            return len(resources)
        
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")
        
        now = datetime.now()
        inserted = 0
        type_map = {'crane': 'Crane', 'tugboat': 'Tugboat', 'tug': 'Tugboat',
                    'pilot': 'Pilot', 'labor': 'Labor', 'mooring': 'Mooring', 'other': 'Other'}
        
        for idx, row in df.iterrows():
            try:
                raw_type = str(row.get('resource_type', 'Other')).lower().strip()
                resource_type = type_map.get(raw_type, 'Other')
                capacity = max(1, int(row['count'])) if pd.notna(row.get('count')) else 1
                
                self.cursor.execute("""
                    INSERT INTO RESOURCES (ResourceType, ResourceName, Capacity, IsAvailable, CreatedAt)
                    VALUES (?, ?, ?, ?, ?)
                """, (resource_type, f"{resource_type} {idx+1}", capacity, True, now))
                inserted += 1
            except Exception as e:
                if inserted < 3:
                    print(f"  ⚠️  Error: {e}")
        
        self.conn.commit()
        print(f"  ✅ Inserted {inserted} resources")
        return inserted

    def seed_supporting_tables(self):
        """Seed CHANNELS, ANCHORAGES, UKC_DATA, PILOTS, TUGBOATS from Test_Data"""
        print("\n" + "="*60)
        print("SEEDING SUPPORTING TABLES")
        print("="*60)
        
        now = datetime.now()
        
        # CHANNELS
        csv_path = os.path.join(TEST_DATA_PATH, "CHANNELS.csv")
        if os.path.exists(csv_path):
            self.cursor.execute("DELETE FROM CHANNELS")
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                try:
                    self.cursor.execute("""
                        INSERT INTO CHANNELS (PortId, ChannelName, ChannelLength, ChannelWidth, 
                            ChannelDepth, ChannelDepthAtChartDatum, OneWayOrTwoWay, MaxVesselLOA, 
                            MaxVesselBeam, MaxVesselDraft, TrafficSeparationScheme, SpeedLimit, 
                            TidalWindowRequired, PilotageCompulsory, TugEscortRequired, DayNightRestrictions, 
                            VisibilityMinimum, WindSpeedLimit, CurrentSpeedLimit, IsActive, CreatedAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (1, row.get('ChannelName'), row.get('ChannelLength'), row.get('ChannelWidth'),
                          row.get('ChannelDepth'), row.get('ChannelDepthAtChartDatum'), 
                          row.get('OneWayOrTwoWay'), row.get('MaxVesselLOA'), row.get('MaxVesselBeam'),
                          row.get('MaxVesselDraft'), bool(row.get('TrafficSeparationScheme')),
                          row.get('SpeedLimit'), bool(row.get('TidalWindowRequired')),
                          bool(row.get('PilotageCompulsory')), bool(row.get('TugEscortRequired')),
                          row.get('DayNightRestrictions'), row.get('VisibilityMinimum'),
                          row.get('WindSpeedLimit'), row.get('CurrentSpeedLimit'), True, now))
                except:
                    pass
            self.conn.commit()
            print(f"  ✅ CHANNELS: {len(df)} records")
        
        # ANCHORAGES
        csv_path = os.path.join(TEST_DATA_PATH, "ANCHORAGES.csv")
        if os.path.exists(csv_path):
            self.cursor.execute("DELETE FROM ANCHORAGES")
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                try:
                    self.cursor.execute("""
                        INSERT INTO ANCHORAGES (PortId, AnchorageName, AnchorageType, Latitude, 
                            Longitude, Depth, MaxVessels, CurrentOccupancy, MaxVesselLOA, MaxVesselDraft, 
                            AverageWaitingTime, STSCargoOpsPermitted, QuarantineAnchorage, IsActive, CreatedAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (1, row.get('AnchorageName'), row.get('AnchorageType'), row.get('Latitude'),
                          row.get('Longitude'), row.get('Depth'), row.get('MaxVessels'),
                          row.get('CurrentOccupancy'), row.get('MaxVesselLOA'), row.get('MaxVesselDraft'),
                          row.get('AverageWaitingTime'), bool(row.get('STSCargoOpsPermitted')),
                          bool(row.get('QuarantineAnchorage')), True, now))
                except:
                    pass
            self.conn.commit()
            print(f"  ✅ ANCHORAGES: {len(df)} records")
        
        # UKC_DATA
        csv_path = os.path.join(TEST_DATA_PATH, "UKC_DATA.csv")
        if os.path.exists(csv_path):
            self.cursor.execute("DELETE FROM UKC_DATA")
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                try:
                    self.cursor.execute("""
                        INSERT INTO UKC_DATA (PortId, PortCode, VesselType, VesselLOA, VesselBeam, 
                            VesselDraft, GrossTonnage, ChannelDepth, TidalHeight, AvailableDepth, 
                            StaticUKC, Squat, DynamicUKC, UKCPercentage, RequiredUKCPercentage, 
                            IsSafe, SpeedKnots, BlockCoefficient, WaveAllowance, HeelAllowance, 
                            NetUKC, SafetyMargin, RiskLevel, Recommendation, CalculatedAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (1, row.get('PortCode'), row.get('VesselType'), row.get('VesselLOA'),
                          row.get('VesselBeam'), row.get('VesselDraft'), row.get('GrossTonnage'),
                          row.get('ChannelDepth'), row.get('TidalHeight'), row.get('AvailableDepth'),
                          row.get('StaticUKC'), row.get('Squat'), row.get('DynamicUKC'),
                          row.get('UKCPercentage'), row.get('RequiredUKCPercentage'),
                          bool(row.get('IsSafe')), row.get('SpeedKnots'), row.get('BlockCoefficient'),
                          row.get('WaveAllowance'), row.get('HeelAllowance'), row.get('NetUKC'),
                          row.get('SafetyMargin'), row.get('RiskLevel'), 
                          str(row.get('Recommendation'))[:500], now))
                except:
                    pass
            self.conn.commit()
            print(f"  ✅ UKC_DATA: {len(df)} records")
        
        # PILOTS
        csv_path = os.path.join(TEST_DATA_PATH, "PILOTS.csv")
        if os.path.exists(csv_path):
            self.cursor.execute("DELETE FROM PILOTS")
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                try:
                    self.cursor.execute("""
                        INSERT INTO PILOTS (PortCode, PortName, PilotName, PilotCode, PilotType, 
                            PilotClass, CertificationLevel, ExperienceYears, MaxVesselGT, MaxVesselLOA, 
                            NightOperations, AdverseWeather, CanTrain, LicenseIssueDate, LicenseExpiryDate, 
                            Status, Languages, Certifications, CreatedAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (row.get('PortCode'), row.get('PortName'), row.get('PilotName'),
                          row.get('PilotCode'), row.get('PilotType'), row.get('PilotClass'),
                          row.get('CertificationLevel'), row.get('ExperienceYears'),
                          row.get('MaxVesselGT'), row.get('MaxVesselLOA'),
                          bool(row.get('NightOperations')), bool(row.get('AdverseWeather')),
                          bool(row.get('CanTrain')), 
                          pd.to_datetime(row.get('LicenseIssueDate'), errors='coerce'),
                          pd.to_datetime(row.get('LicenseExpiryDate'), errors='coerce'),
                          row.get('Status'), str(row.get('Languages'))[:200],
                          str(row.get('Certifications'))[:500], now))
                except:
                    pass
            self.conn.commit()
            print(f"  ✅ PILOTS: {len(df)} records")
        
        # TUGBOATS
        csv_path = os.path.join(TEST_DATA_PATH, "TUGBOATS.csv")
        if os.path.exists(csv_path):
            self.cursor.execute("DELETE FROM TUGBOATS")
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                try:
                    self.cursor.execute("""
                        INSERT INTO TUGBOATS (PortCode, TugName, TugCode, IMONumber, MMSI, CallSign, 
                            FlagState, PortOfRegistry, TugType, TugClass, Operator, BollardPull, 
                            Length, Beam, Draft, EnginePower, MaxSpeed, YearBuilt, FiFiClass, 
                            WinchCapacity, CrewSize, Status, CreatedAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (row.get('PortCode'), row.get('TugName'), row.get('TugCode'),
                          row.get('IMONumber'), row.get('MMSI'), row.get('CallSign'),
                          row.get('FlagState'), row.get('PortOfRegistry'), row.get('TugType'),
                          row.get('TugClass'), row.get('Operator'), row.get('BollardPull'),
                          row.get('Length'), row.get('Beam'), row.get('Draft'),
                          row.get('EnginePower'), row.get('MaxSpeed'), row.get('YearBuilt'),
                          row.get('FiFiClass'), row.get('WinchCapacity'), row.get('CrewSize'),
                          row.get('Status'), now))
                except:
                    pass
            self.conn.commit()
            print(f"  ✅ TUGBOATS: {len(df)} records")

    def import_all(self, ais_limit=None):
        """Run complete local import"""
        print("\n" + "="*70)
        print("🚀 LOCAL DATABASE IMPORT - FAST PROTOTYPING MODE")
        print("="*70)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: LocalDB (localdb)\\MSSQLLocalDB")
        print(f"AIS Limit: {ais_limit if ais_limit else 'ALL records'}")
        
        try:
            self.connect()
            self.clear_tables()
            
            print("\n[1/8] Vessels...")
            self.import_vessels()
            
            print("\n[2/8] Berths...")
            self.import_berths()
            
            print("\n[3/8] Vessel Schedule...")
            self.import_vessel_schedule()
            
            print("\n[4/8] Weather Data...")
            self.import_weather_data()
            
            print("\n[5/8] Tidal Data...")
            self.import_tidal_data()
            
            print("\n[6/8] AIS Data...")
            self.import_ais_data(limit=ais_limit)
            
            print("\n[7/8] Resources...")
            self.import_resources()
            
            print("\n[8/8] Supporting Tables...")
            self.seed_supporting_tables()
            
            # Final verification
            print("\n" + "="*70)
            print("📊 FINAL TABLE COUNTS")
            print("="*70)
            tables = ['PORTS', 'TERMINALS', 'VESSELS', 'BERTHS', 'VESSEL_SCHEDULE',
                     'WEATHER_DATA', 'TIDAL_DATA', 'AIS_DATA', 'RESOURCES',
                     'CHANNELS', 'ANCHORAGES', 'UKC_DATA', 'PILOTS', 'TUGBOATS']
            total = 0
            for table in tables:
                try:
                    self.cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                    count = self.cursor.fetchone()[0]
                    total += count
                    print(f"   {table:20s}: {count:>10,}")
                except:
                    print(f"   {table:20s}: ERROR")
            print(f"   {'TOTAL':20s}: {total:>10,}")
            
            print("\n" + "="*70)
            print("✅ LOCAL IMPORT COMPLETED SUCCESSFULLY!")
            print("="*70)
            print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("\nYour LocalDB is now ready for prototyping!")
            print("Connection: (localdb)\\MSSQLLocalDB / BerthPlanning")
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()


if __name__ == "__main__":
    import sys
    
    # Optional: limit AIS records for faster import
    # Use None for all ~412K records, or a number like 100000 for faster testing
    ais_limit = None
    
    if len(sys.argv) > 1:
        try:
            ais_limit = int(sys.argv[1])
            print(f"AIS limit set to: {ais_limit:,}")
        except:
            pass
    
    importer = LocalDataImporter()
    importer.import_all(ais_limit=ais_limit)
