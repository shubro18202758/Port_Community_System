"""
Import Mundra CSV Files to SQL Server BerthPlanning Database
Corrected version with proper column mapping to match SQL Server schema
"""

import pandas as pd
import pyodbc
import os
import re
from datetime import datetime, timedelta
from typing import Optional
import random

class MundraDataImporterV2:
    def __init__(self, connection_string: str, csv_base_path: str):
        self.connection_string = connection_string
        self.csv_base_path = csv_base_path
        self.conn = None
        self.port_code = "INMUN"  # Mundra Port code

    def connect(self):
        try:
            self.conn = pyodbc.connect(self.connection_string)
            print("✓ Connected to SQL Server")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            print("✓ Connection closed")

    def clear_tables(self):
        """Clear existing data from tables in reverse dependency order"""
        print("\n🗑️  Clearing existing data...")
        cursor = self.conn.cursor()
        tables = ['AIS_DATA', 'VESSEL_SCHEDULE', 'WEATHER_DATA', 'TIDAL_DATA', 
                  'RESOURCES', 'VESSELS', 'BERTHS']
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM [{table}]")
                self.conn.commit()
                print(f"   ✓ Cleared {table}")
            except Exception as e:
                print(f"   ⚠️  Could not clear {table}: {e}")

    # ==================== HELPER FUNCTIONS ====================

    def extract_imo(self, imo_mmsi: str) -> Optional[str]:
        """Extract IMO from 'IMO9225772|MMSI761415646' format"""
        if not imo_mmsi or pd.isna(imo_mmsi):
            return None
        match = re.search(r'IMO(\d+)', str(imo_mmsi))
        return match.group(1) if match else None

    def extract_mmsi(self, imo_mmsi: str) -> Optional[str]:
        """Extract MMSI from 'IMO9225772|MMSI761415646' format"""
        if not imo_mmsi or pd.isna(imo_mmsi):
            return None
        match = re.search(r'MMSI(\d+)', str(imo_mmsi))
        return match.group(1) if match else None

    def derive_vessel_type(self, cargo_type: str) -> str:
        """Map cargo type to vessel type"""
        cargo_map = {
            'container': 'Container Ship',
            'bulk': 'Bulk Carrier',
            'general_bulk': 'General Cargo',
            'coal': 'Bulk Carrier',
            'iron_ore': 'Bulk Carrier',
            'crude_oil': 'Tanker',
            'lng': 'LNG Carrier',
            'chemicals': 'Chemical Tanker',
            'roro': 'RoRo',
            'project_cargo': 'General Cargo'
        }
        return cargo_map.get(str(cargo_type).lower(), 'General Cargo') if cargo_type else 'General Cargo'

    def calculate_gt(self, loa: float, beam: float, draft: float) -> int:
        """Estimate Gross Tonnage"""
        if pd.isna(loa) or pd.isna(beam) or pd.isna(draft):
            return 10000  # Default
        return max(int(loa * beam * draft * 0.7 * 0.3), 1000)

    def derive_priority(self, cargo_type: str) -> int:
        """Derive priority from cargo type"""
        high_priority = ['container', 'crude_oil', 'lng']
        return 1 if str(cargo_type).lower() in high_priority else 2

    def derive_berth_type(self, cargo_allowed: str) -> str:
        """Map cargo_allowed to berth type"""
        if not cargo_allowed:
            return 'General'
        cargo = str(cargo_allowed).lower()
        if 'container' in cargo:
            return 'Container'
        elif any(x in cargo for x in ['bulk', 'coal', 'iron']):
            return 'Bulk'
        elif any(x in cargo for x in ['oil', 'crude', 'lng', 'chemical']):
            return 'Liquid'
        return 'General'

    def derive_weather_condition(self, wind_speed: float, rain: float, visibility: float, storm_flag: int) -> str:
        """Derive weather condition"""
        if storm_flag:
            return 'Storm'
        if rain and rain > 10:
            return 'Heavy Rain'
        if rain and rain > 2:
            return 'Rain'
        if visibility and visibility < 1:
            return 'Fog'
        if wind_speed and wind_speed > 15:
            return 'Windy'
        return 'Clear'

    # ==================== IMPORT FUNCTIONS ====================

    def import_vessels(self):
        """Import VESSELS.csv → VESSELS table"""
        print("\n" + "="*60)
        print("IMPORTING VESSELS")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "VESSELS.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")

        cursor = self.conn.cursor()
        inserted = 0
        now = datetime.now()

        for _, row in df.iterrows():
            try:
                # Extract vessel_id as integer
                vessel_id = int(str(row['vessel_id']).replace('VES-', '').replace('VES', ''))
                
                imo = self.extract_imo(row.get('imo_mmsi'))
                mmsi = self.extract_mmsi(row.get('imo_mmsi'))
                
                # Get cargo type from schedule if available
                cargo_type = row.get('cargo_type', 'general')
                vessel_type = self.derive_vessel_type(cargo_type)
                
                loa = float(row['loa_m']) if pd.notna(row.get('loa_m')) else 200.0
                beam = float(row['beam_m']) if pd.notna(row.get('beam_m')) else 32.0
                draft = float(row['draft_m']) if pd.notna(row.get('draft_m')) else 12.0
                gt = self.calculate_gt(loa, beam, draft)
                priority = self.derive_priority(cargo_type)

                cursor.execute("""
                    INSERT INTO VESSELS (VesselId, VesselName, IMO, MMSI, VesselType, 
                                         LOA, Beam, Draft, GrossTonnage, CargoType,
                                         CargoVolume, CargoUnit, Priority, FlagState,
                                         FlagStateName, CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vessel_id,
                    str(row['vessel_name'])[:100],
                    imo,
                    mmsi,
                    vessel_type,
                    loa,
                    beam,
                    draft,
                    gt,
                    str(cargo_type)[:50] if cargo_type else 'General',
                    None,  # CargoVolume
                    None,  # CargoUnit
                    priority,
                    'IN',  # FlagState
                    'India',  # FlagStateName
                    now,
                    now
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Error inserting vessel {row.get('vessel_id')}: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} vessels")

    def import_berths(self):
        """Import BERTHS.csv → BERTHS table"""
        print("\n" + "="*60)
        print("IMPORTING BERTHS")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "BERTHS.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")

        cursor = self.conn.cursor()
        inserted = 0
        now = datetime.now()

        for _, row in df.iterrows():
            try:
                berth_id = int(str(row['berth_id']).replace('B-', '').replace('B', ''))
                
                # Extract number of cranes from equipment field
                equipment = str(row.get('equipment', ''))
                cranes = 0
                crane_match = re.search(r'(\d+)', equipment)
                if crane_match and 'crane' in equipment.lower():
                    cranes = int(crane_match.group(1))

                berth_type = self.derive_berth_type(row.get('cargo_allowed'))
                
                cursor.execute("""
                    INSERT INTO BERTHS (BerthId, TerminalId, PortId, PortCode, BerthName,
                                       BerthCode, Length, Depth, MaxDraft, MaxLOA, MaxBeam,
                                       BerthType, NumberOfCranes, BollardCount, IsActive,
                                       Latitude, Longitude, CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    berth_id,
                    1,  # TerminalId
                    1,  # PortId
                    self.port_code,
                    f"Berth {berth_id}",
                    str(row['berth_id']),
                    float(row['max_loa_m']) if pd.notna(row.get('max_loa_m')) else 300.0,  # Length
                    float(row['max_draft_m']) if pd.notna(row.get('max_draft_m')) else 15.0,  # Depth
                    float(row['max_draft_m']) if pd.notna(row.get('max_draft_m')) else 15.0,
                    float(row['max_loa_m']) if pd.notna(row.get('max_loa_m')) else 300.0,
                    float(row['max_beam_m']) if pd.notna(row.get('max_beam_m')) else 50.0,
                    berth_type,
                    cranes,
                    10,  # BollardCount default
                    True,  # IsActive
                    22.4 + random.uniform(-0.01, 0.01),  # Mundra lat
                    69.7 + random.uniform(-0.01, 0.01),  # Mundra lon
                    now,
                    now
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Error inserting berth {row.get('berth_id')}: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} berths")

    def import_vessel_schedule(self):
        """Import VESSEL_SCHEDULE.csv → VESSEL_SCHEDULE table"""
        print("\n" + "="*60)
        print("IMPORTING VESSEL_SCHEDULE")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "VESSEL_SCHEDULE.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")

        cursor = self.conn.cursor()
        inserted = 0
        now = datetime.now()

        for _, row in df.iterrows():
            try:
                schedule_id = int(str(row['schedule_id']).replace('SCH-', '').replace('SCH', ''))
                vessel_id = int(str(row['vessel_id']).replace('VES-', '').replace('VES', ''))
                berth_id = int(str(row['berth_id']).replace('B-', '').replace('B', '')) if pd.notna(row.get('berth_id')) else None

                # Parse dates
                eta = pd.to_datetime(row.get('eta')) if pd.notna(row.get('eta')) else None
                atb = pd.to_datetime(row.get('atb')) if pd.notna(row.get('atb')) else None
                atd = pd.to_datetime(row.get('atd')) if pd.notna(row.get('atd')) else None

                # Map status
                status_raw = str(row.get('status', 'scheduled')).lower()
                status_map = {
                    'completed': 'Completed',
                    'in_progress': 'In Progress',
                    'berthed': 'Berthed',
                    'scheduled': 'Scheduled',
                    'waiting': 'Waiting',
                    'departed': 'Departed'
                }
                status = status_map.get(status_raw, 'Scheduled')

                cursor.execute("""
                    INSERT INTO VESSEL_SCHEDULE (ScheduleId, VesselId, BerthId, ETA, PredictedETA,
                                                 ETD, ATA, ATB, ATD, AnchorageArrival,
                                                 PilotBoardingTime, BerthArrivalTime, FirstLineTime,
                                                 AllFastTime, CargoStartTime, CargoCompleteTime,
                                                 Status, DwellTime, WaitingTime, CargoType,
                                                 CargoQuantity, CargoUnit, CargoOperation, PortCode,
                                                 VoyageNumber, ShippingLine, TerminalType, TugsAssigned,
                                                 PilotsAssigned, WaitingTimeHours, DwellTimeHours,
                                                 ETAVarianceHours, BerthingDelayMins, ArrivalDraft,
                                                 DepartureDraft, OptimizationScore, IsOptimized,
                                                 ConflictCount, CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    schedule_id,
                    vessel_id,
                    berth_id,
                    eta,
                    eta,  # PredictedETA
                    atd,  # ETD
                    atb,  # ATA
                    atb,  # ATB
                    atd,  # ATD
                    None,  # AnchorageArrival
                    None,  # PilotBoardingTime
                    atb,   # BerthArrivalTime
                    None,  # FirstLineTime
                    None,  # AllFastTime
                    None,  # CargoStartTime
                    None,  # CargoCompleteTime
                    status,
                    int(row['dwell_hours']) if pd.notna(row.get('dwell_hours')) else None,
                    int(row['waiting_hours']) if pd.notna(row.get('waiting_hours')) else None,
                    str(row.get('cargo_type', 'general'))[:50],
                    float(row['cargo_volume_cbm']) if pd.notna(row.get('cargo_volume_cbm')) else None,
                    'CBM',  # CargoUnit
                    'Loading',  # CargoOperation
                    self.port_code,
                    f"VOY{schedule_id:05d}",
                    str(row.get('line_operator', 'Unknown'))[:50],
                    str(row.get('terminal_code', 'General'))[:50],
                    int(row['tugs_assigned']) if pd.notna(row.get('tugs_assigned')) else 1,
                    int(row['pilots_assigned']) if pd.notna(row.get('pilots_assigned')) else 1,
                    float(row['waiting_hours']) if pd.notna(row.get('waiting_hours')) else None,
                    float(row['dwell_hours']) if pd.notna(row.get('dwell_hours')) else None,
                    None,  # ETAVarianceHours
                    None,  # BerthingDelayMins
                    None,  # ArrivalDraft
                    None,  # DepartureDraft
                    None,  # OptimizationScore
                    False,  # IsOptimized
                    0,  # ConflictCount
                    now,
                    now
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Error inserting schedule {row.get('schedule_id')}: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} vessel schedules")

    def import_weather_data(self):
        """Import WEATHER_DATA.csv → WEATHER_DATA table"""
        print("\n" + "="*60)
        print("IMPORTING WEATHER_DATA")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "WEATHER_DATA.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")

        cursor = self.conn.cursor()
        inserted = 0
        now = datetime.now()

        for idx, row in df.iterrows():
            try:
                weather_id = idx + 1
                recorded_at = pd.to_datetime(row.get('ts_hour')) if pd.notna(row.get('ts_hour')) else now

                wind_speed_mps = float(row['wind_speed_mps']) if pd.notna(row.get('wind_speed_mps')) else 5.0
                wind_gust_mps = float(row['wind_gust_mps']) if pd.notna(row.get('wind_gust_mps')) else 8.0
                rain_mm = float(row['rain_mm']) if pd.notna(row.get('rain_mm')) else 0.0
                visibility_km = float(row['visibility_km']) if pd.notna(row.get('visibility_km')) else 10.0
                storm_flag = int(row['storm_flag']) if pd.notna(row.get('storm_flag')) else 0

                # Convert wind speed to knots
                wind_speed_knots = wind_speed_mps * 1.94384

                # Estimate wave height from wind
                wave_height = 0.21 * ((wind_speed_mps + wind_gust_mps) / 2) ** 1.5 / 10

                # Derive weather condition
                condition = self.derive_weather_condition(wind_speed_mps, rain_mm, visibility_km, storm_flag)

                cursor.execute("""
                    INSERT INTO WEATHER_DATA (WeatherId, PortId, PortCode, RecordedAt,
                                             WindSpeed, WindDirection, WindDirectionText,
                                             Visibility, WaveHeight, Temperature, Precipitation,
                                             WeatherCondition, Climate, Season, IsAlert, FetchedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    weather_id,
                    1,  # PortId
                    self.port_code,
                    recorded_at,
                    round(wind_speed_knots, 2),
                    random.randint(0, 359),  # WindDirection
                    'N',  # WindDirectionText
                    int(visibility_km * 1000),  # Convert km to meters
                    round(wave_height, 2),
                    28.0,  # Temperature (tropical default)
                    rain_mm,
                    condition,
                    'Tropical',
                    'Monsoon' if recorded_at.month in [6, 7, 8, 9] else 'Dry',
                    storm_flag == 1,
                    now
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Error inserting weather {idx}: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} weather records")

    def import_tidal_data(self):
        """Import TIDAL_DATA.csv → TIDAL_DATA table"""
        print("\n" + "="*60)
        print("IMPORTING TIDAL_DATA")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "TIDAL_DATA.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")

        cursor = self.conn.cursor()
        inserted = 0
        now = datetime.now()

        for idx, row in df.iterrows():
            try:
                tidal_id = idx + 1
                tide_time = pd.to_datetime(row.get('ts')) if pd.notna(row.get('ts')) else now

                # Map tide phase
                phase = str(row.get('tide_phase', 'ebb')).lower()
                tide_type = 'High' if phase == 'flood' else 'Low'

                height = float(row['tide_height_m']) if pd.notna(row.get('tide_height_m')) else 2.0

                cursor.execute("""
                    INSERT INTO TIDAL_DATA (TidalId, TideTime, TideType, Height, CreatedAt)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    tidal_id,
                    tide_time,
                    tide_type,
                    height,
                    now
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Error inserting tidal {idx}: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} tidal records")

    def import_ais_data(self):
        """Import AIS_DATA.csv → AIS_DATA table (batch processing)"""
        print("\n" + "="*60)
        print("IMPORTING AIS_DATA (this may take several minutes)")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "AIS_DATA.csv")
        
        # Read in chunks
        chunk_size = 10000
        total_inserted = 0
        now = datetime.now()

        for chunk_num, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
            print(f"  📦 Processing chunk {chunk_num + 1} ({len(chunk)} rows)...")
            
            cursor = self.conn.cursor()
            inserted = 0

            for idx, row in chunk.iterrows():
                try:
                    ais_id = total_inserted + inserted + 1
                    vessel_id = int(str(row['vessel_id']).replace('VES-', '').replace('VES', ''))
                    
                    recorded_at = pd.to_datetime(row.get('ts')) if pd.notna(row.get('ts')) else now

                    # Map navigation status
                    nav_status = str(row.get('nav_status', 'under_way')).lower()
                    nav_status_map = {
                        'at_anchor': 'At Anchor',
                        'under_way': 'Under Way',
                        'moored': 'Moored',
                        'restricted': 'Restricted Maneuverability',
                        'not_under_command': 'Not Under Command'
                    }
                    nav_status_text = nav_status_map.get(nav_status, 'Under Way')

                    cursor.execute("""
                        INSERT INTO AIS_DATA (AISId, VesselId, MMSI, PortCode, VesselType,
                                             Latitude, Longitude, Speed, Course, Heading,
                                             NavigationStatus, NavigationStatusCode, ETA,
                                             TimeToPort, Phase, DistanceToPort, RecordedAt, FetchedAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ais_id,
                        vessel_id,
                        None,  # MMSI
                        self.port_code,
                        'Cargo',  # VesselType
                        float(row['lat']) if pd.notna(row.get('lat')) else 22.4,
                        float(row['lon']) if pd.notna(row.get('lon')) else 69.7,
                        float(row['sog_kn']) if pd.notna(row.get('sog_kn')) else 0.0,  # Speed (SOG)
                        float(row['cog_deg']) if pd.notna(row.get('cog_deg')) else 0.0,  # Course (COG)
                        float(row['cog_deg']) if pd.notna(row.get('cog_deg')) else 0.0,  # Heading
                        nav_status_text,
                        0,  # NavigationStatusCode
                        None,  # ETA
                        None,  # TimeToPort
                        'Approaching',  # Phase
                        None,  # DistanceToPort
                        recorded_at,
                        now
                    ))
                    inserted += 1
                except Exception as e:
                    if inserted == 0:  # Only print first error per chunk
                        print(f"    ⚠️  Error sample: {e}")

            self.conn.commit()
            total_inserted += inserted
            print(f"    ✓ Inserted {inserted} AIS records (total: {total_inserted})")

        print(f"  ✅ Total AIS records inserted: {total_inserted}")

    def import_resources(self):
        """Import RESOURCES.csv → RESOURCES table"""
        print("\n" + "="*60)
        print("IMPORTING RESOURCES")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "RESOURCES.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows from CSV")

        cursor = self.conn.cursor()
        inserted = 0
        now = datetime.now()

        for idx, row in df.iterrows():
            try:
                resource_id = idx + 1
                resource_type = str(row.get('resource_type', 'Equipment'))[:50]
                
                cursor.execute("""
                    INSERT INTO RESOURCES (ResourceId, ResourceType, ResourceName, 
                                          Capacity, IsAvailable, MaintenanceSchedule, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    resource_id,
                    resource_type,
                    f"{resource_type} {resource_id}",
                    int(row['count']) if pd.notna(row.get('count')) else 1,
                    True,
                    None,
                    now
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Error inserting resource {idx}: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} resources")

    def import_all(self):
        """Run complete import process"""
        print("\n" + "="*60)
        print("🚀 MUNDRA DATA IMPORT TO SQL SERVER")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Source: {self.csv_base_path}")

        try:
            self.connect()
            self.clear_tables()

            print("\n[1/7] Importing VESSELS...")
            self.import_vessels()

            print("\n[2/7] Importing BERTHS...")
            self.import_berths()

            print("\n[3/7] Importing VESSEL_SCHEDULE...")
            self.import_vessel_schedule()

            print("\n[4/7] Importing WEATHER_DATA...")
            self.import_weather_data()

            print("\n[5/7] Importing TIDAL_DATA...")
            self.import_tidal_data()

            print("\n[6/7] Importing AIS_DATA...")
            self.import_ais_data()

            print("\n[7/7] Importing RESOURCES...")
            self.import_resources()

            print("\n" + "="*60)
            print("✅ IMPORT COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"\n❌ IMPORT FAILED: {e}")
            raise
        finally:
            self.close()


if __name__ == "__main__":
    # Configuration
    CONNECTION_STRING = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "Server=20.204.224.123,1433;"
        "Database=BerthPlanning;"
        "UID=Admin;"
        "PWD=Adm!n#@@7;"
        "TrustServerCertificate=Yes;"
    )

    CSV_BASE_PATH = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\documents\Data\Mundra"

    # Run import
    importer = MundraDataImporterV2(CONNECTION_STRING, CSV_BASE_PATH)
    importer.import_all()
