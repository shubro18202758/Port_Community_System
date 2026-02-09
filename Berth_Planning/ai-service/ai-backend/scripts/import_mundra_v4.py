"""
Import Mundra CSV Files to SQL Server BerthPlanning Database
V4 - Fixed for CHECK constraints
"""

import pandas as pd
import pyodbc
import os
import re
from datetime import datetime
from typing import Optional
import random

class MundraDataImporterV4:
    def __init__(self, connection_string: str, csv_base_path: str):
        self.connection_string = connection_string
        self.csv_base_path = csv_base_path
        self.conn = None
        self.port_code = "INMUN"

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
        """Clear existing data"""
        print("\n🗑️  Clearing existing data...")
        cursor = self.conn.cursor()
        
        tables = ['AIS_DATA', 'VESSEL_SCHEDULE', 'WEATHER_DATA', 'TIDAL_DATA', 
                  'RESOURCES', 'VESSELS', 'BERTHS']
        
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM [{table}]")
                cursor.execute(f"DBCC CHECKIDENT ('{table}', RESEED, 0)")
                self.conn.commit()
                print(f"   ✓ Cleared {table}")
            except Exception as e:
                self.conn.rollback()
                print(f"   ⚠️  {table}: {str(e)[:60]}")

    # ==================== HELPER FUNCTIONS ====================
    def extract_imo(self, imo_mmsi: str) -> Optional[str]:
        if not imo_mmsi or pd.isna(imo_mmsi):
            return None
        match = re.search(r'IMO(\d+)', str(imo_mmsi))
        return match.group(1) if match else None

    def extract_mmsi(self, imo_mmsi: str) -> Optional[str]:
        if not imo_mmsi or pd.isna(imo_mmsi):
            return None
        match = re.search(r'MMSI(\d+)', str(imo_mmsi))
        return match.group(1) if match else None

    def derive_vessel_type(self, cargo_type: str) -> str:
        cargo_map = {
            'container': 'Container Ship', 'bulk': 'Bulk Carrier',
            'general_bulk': 'General Cargo', 'coal': 'Bulk Carrier',
            'iron_ore': 'Bulk Carrier', 'crude_oil': 'Tanker',
            'lng': 'LNG Carrier', 'chemicals': 'Chemical Tanker',
            'roro': 'RoRo', 'project_cargo': 'General Cargo'
        }
        return cargo_map.get(str(cargo_type).lower(), 'General Cargo') if cargo_type else 'General Cargo'

    def calculate_gt(self, loa: float, beam: float, draft: float) -> int:
        if pd.isna(loa) or pd.isna(beam) or pd.isna(draft):
            return 10000
        return max(int(loa * beam * draft * 0.7 * 0.3), 1000)

    def derive_priority(self, cargo_type: str) -> int:
        return 1 if str(cargo_type).lower() in ['container', 'crude_oil', 'lng'] else 2

    def derive_berth_type(self, cargo_allowed: str) -> str:
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

    def derive_weather_condition(self, wind_speed, rain, visibility, storm_flag):
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
        """Import VESSELS"""
        print("\n" + "="*60)
        print("IMPORTING VESSELS")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "VESSELS.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")

        cursor = self.conn.cursor()
        now = datetime.now()
        inserted = 0

        for _, row in df.iterrows():
            try:
                imo = self.extract_imo(row.get('imo_mmsi'))
                mmsi = self.extract_mmsi(row.get('imo_mmsi'))
                cargo_type = row.get('cargo_type', 'general')
                vessel_type = self.derive_vessel_type(cargo_type)
                loa = float(row['loa_m']) if pd.notna(row.get('loa_m')) else 200.0
                beam = float(row['beam_m']) if pd.notna(row.get('beam_m')) else 32.0
                draft = float(row['draft_m']) if pd.notna(row.get('draft_m')) else 12.0
                gt = self.calculate_gt(loa, beam, draft)
                priority = self.derive_priority(cargo_type)

                cursor.execute("""
                    INSERT INTO VESSELS (VesselName, IMO, MMSI, VesselType, LOA, Beam, Draft,
                                        GrossTonnage, CargoType, CargoVolume, CargoUnit, Priority,
                                        FlagState, FlagStateName, CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(row['vessel_name'])[:100],
                    imo, mmsi, vessel_type, loa, beam, draft, gt,
                    str(cargo_type)[:50] if cargo_type else 'General',
                    None, None, priority, 'IN', 'India', now, now
                ))
                inserted += 1
            except Exception as e:
                if inserted < 5:
                    print(f"  ⚠️  Error: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} vessels")

    def import_berths(self):
        """Import BERTHS"""
        print("\n" + "="*60)
        print("IMPORTING BERTHS")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "BERTHS.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")

        cursor = self.conn.cursor()
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

                cursor.execute("""
                    INSERT INTO BERTHS (TerminalId, PortId, PortCode, BerthName, BerthCode,
                                       Length, Depth, MaxDraft, MaxLOA, MaxBeam, BerthType,
                                       NumberOfCranes, BollardCount, IsActive, Latitude, Longitude,
                                       CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    1, 1, self.port_code,
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
                if inserted < 5:
                    print(f"  ⚠️  Error: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} berths")

    def import_vessel_schedule(self):
        """Import VESSEL_SCHEDULE with corrected Status values"""
        print("\n" + "="*60)
        print("IMPORTING VESSEL_SCHEDULE")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "VESSEL_SCHEDULE.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")

        # Get vessel ID mapping
        cursor = self.conn.cursor()
        cursor.execute("SELECT VesselId, VesselName FROM VESSELS")
        vessel_map = {row[1]: row[0] for row in cursor.fetchall()}
        
        # Get berth ID mapping
        cursor.execute("SELECT BerthId, BerthCode FROM BERTHS")
        berth_map = {row[1]: row[0] for row in cursor.fetchall()}

        now = datetime.now()
        inserted = 0
        errors = 0

        # Valid Status values: 'Scheduled', 'Approaching', 'Berthed', 'Departed', 'Cancelled'
        status_map = {
            'completed': 'Departed',  # Map completed to Departed
            'in_progress': 'Berthed',
            'berthed': 'Berthed',
            'scheduled': 'Scheduled',
            'waiting': 'Approaching',
            'departed': 'Departed',
            'cancelled': 'Cancelled'
        }

        for _, row in df.iterrows():
            try:
                # Map vessel
                vessel_name = str(row.get('vessel_name', ''))
                vessel_id = vessel_map.get(vessel_name)
                if not vessel_id:
                    for name, vid in vessel_map.items():
                        if vessel_name in name or name in vessel_name:
                            vessel_id = vid
                            break
                if not vessel_id:
                    vessel_id = 1

                # Map berth
                berth_code = str(row.get('berth_id', ''))
                berth_id = berth_map.get(berth_code)
                if not berth_id:
                    berth_id = 1

                # Parse dates
                eta = pd.to_datetime(row.get('eta'), errors='coerce')
                atb = pd.to_datetime(row.get('atb'), errors='coerce')
                atd = pd.to_datetime(row.get('atd'), errors='coerce')
                
                eta = eta if pd.notna(eta) else None
                atb = atb if pd.notna(atb) else None
                atd = atd if pd.notna(atd) else None

                # Map status - CRITICAL FIX
                status_raw = str(row.get('status', 'scheduled')).lower().strip()
                status = status_map.get(status_raw, 'Scheduled')

                # Handle dwell and waiting time - must be > 0 for DwellTime
                dwell_time = int(row['dwell_hours']) if pd.notna(row.get('dwell_hours')) and int(row['dwell_hours']) > 0 else 1
                waiting_time = int(row['waiting_hours']) if pd.notna(row.get('waiting_hours')) and int(row['waiting_hours']) >= 0 else 0

                cursor.execute("""
                    INSERT INTO VESSEL_SCHEDULE (VesselId, BerthId, ETA, PredictedETA, ETD,
                                                ATA, ATB, ATD, Status, DwellTime, WaitingTime,
                                                CargoType, CargoQuantity, CargoUnit, CargoOperation,
                                                PortCode, VoyageNumber, ShippingLine, TerminalType,
                                                TugsAssigned, PilotsAssigned, WaitingTimeHours,
                                                DwellTimeHours, IsOptimized, ConflictCount,
                                                CreatedAt, UpdatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vessel_id, berth_id, eta, eta, atd, atb, atb, atd, status,
                    dwell_time, waiting_time,
                    str(row.get('cargo_type', 'general'))[:50],
                    float(row['cargo_volume_cbm']) if pd.notna(row.get('cargo_volume_cbm')) else None,
                    'CBM', 'Loading', self.port_code,
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
                
                if inserted % 1000 == 0:
                    self.conn.commit()
                    print(f"    ... {inserted} records")

            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  ⚠️  Error: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} schedules, {errors} errors")

    def import_weather_data(self):
        """Import WEATHER_DATA"""
        print("\n" + "="*60)
        print("IMPORTING WEATHER_DATA")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "WEATHER_DATA.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")

        cursor = self.conn.cursor()
        now = datetime.now()
        inserted = 0

        for idx, row in df.iterrows():
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
                condition = self.derive_weather_condition(wind_speed_mps, rain_mm, visibility_km, storm_flag)

                # WindDirection must be 0-360
                wind_dir = random.randint(0, 359)

                cursor.execute("""
                    INSERT INTO WEATHER_DATA (PortId, PortCode, RecordedAt, WindSpeed,
                                             WindDirection, WindDirectionText, Visibility,
                                             WaveHeight, Temperature, Precipitation,
                                             WeatherCondition, Climate, Season, IsAlert, FetchedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    1, self.port_code, recorded_at, round(wind_speed_knots, 2),
                    wind_dir, 'N', int(visibility_km * 1000),
                    round(wave_height, 2), 28.0, rain_mm, condition,
                    'Tropical',
                    'Monsoon' if recorded_at.month in [6, 7, 8, 9] else 'Dry',
                    storm_flag == 1, now
                ))
                inserted += 1

                if inserted % 1000 == 0:
                    self.conn.commit()
                    print(f"    ... {inserted} records")

            except Exception as e:
                if inserted < 5:
                    print(f"  ⚠️  Error: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} weather records")

    def import_tidal_data(self):
        """Import TIDAL_DATA with corrected TideType values"""
        print("\n" + "="*60)
        print("IMPORTING TIDAL_DATA")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "TIDAL_DATA.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")

        cursor = self.conn.cursor()
        now = datetime.now()
        inserted = 0

        for idx, row in df.iterrows():
            try:
                tide_time = pd.to_datetime(row.get('ts'), errors='coerce')
                tide_time = tide_time if pd.notna(tide_time) else now

                # Valid TideType values: 'HighTide', 'LowTide'
                phase = str(row.get('tide_phase', 'ebb')).lower()
                tide_type = 'HighTide' if phase == 'flood' else 'LowTide'
                
                height = float(row['tide_height_m']) if pd.notna(row.get('tide_height_m')) else 2.0

                cursor.execute("""
                    INSERT INTO TIDAL_DATA (TideTime, TideType, Height, CreatedAt)
                    VALUES (?, ?, ?, ?)
                """, (tide_time, tide_type, height, now))
                inserted += 1
            except Exception as e:
                if inserted < 5:
                    print(f"  ⚠️  Error: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} tidal records")

    def import_ais_data(self):
        """Import AIS_DATA with proper constraint validation"""
        print("\n" + "="*60)
        print("IMPORTING AIS_DATA (this may take several minutes)")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "AIS_DATA.csv")
        
        # Get vessel ID mapping
        cursor = self.conn.cursor()
        cursor.execute("SELECT VesselId FROM VESSELS")
        vessel_ids = [row[0] for row in cursor.fetchall()]
        if not vessel_ids:
            vessel_ids = [1]

        chunk_size = 10000
        total_inserted = 0
        now = datetime.now()

        for chunk_num, chunk in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
            print(f"  📦 Processing chunk {chunk_num + 1} ({len(chunk)} rows)...")
            
            inserted = 0
            for idx, row in chunk.iterrows():
                try:
                    vessel_id = vessel_ids[total_inserted % len(vessel_ids)]
                    
                    recorded_at = pd.to_datetime(row.get('ts'), errors='coerce')
                    recorded_at = recorded_at if pd.notna(recorded_at) else now

                    # Validate latitude: -90 to 90
                    lat = float(row['lat']) if pd.notna(row.get('lat')) else 22.4
                    lat = max(-90, min(90, lat))

                    # Validate longitude: -180 to 180
                    lon = float(row['lon']) if pd.notna(row.get('lon')) else 69.7
                    lon = max(-180, min(180, lon))

                    # Speed must be >= 0
                    speed = float(row['sog_kn']) if pd.notna(row.get('sog_kn')) else 0.0
                    speed = max(0, speed)

                    # Course must be 0-360
                    course = float(row['cog_deg']) if pd.notna(row.get('cog_deg')) else 0.0
                    course = max(0, min(360, course))

                    # Heading must be 0-360
                    heading = course

                    nav_status = str(row.get('nav_status', 'under_way')).lower()
                    nav_status_map = {
                        'at_anchor': 'At Anchor', 'under_way': 'Under Way',
                        'moored': 'Moored', 'restricted': 'Restricted Maneuverability'
                    }
                    nav_status_text = nav_status_map.get(nav_status, 'Under Way')

                    cursor.execute("""
                        INSERT INTO AIS_DATA (VesselId, MMSI, PortCode, VesselType,
                                             Latitude, Longitude, Speed, Course, Heading,
                                             NavigationStatus, NavigationStatusCode,
                                             Phase, RecordedAt, FetchedAt)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        vessel_id, None, self.port_code, 'Cargo',
                        lat, lon, speed, course, heading,
                        nav_status_text, 0, 'Approaching', recorded_at, now
                    ))
                    inserted += 1
                    total_inserted += 1
                except Exception as e:
                    if total_inserted < 5:
                        print(f"    ⚠️  Error: {e}")

            self.conn.commit()
            print(f"    ✓ Inserted {inserted} (total: {total_inserted})")

        print(f"  ✅ Total AIS: {total_inserted}")

    def import_resources(self):
        """Import RESOURCES with valid ResourceType"""
        print("\n" + "="*60)
        print("IMPORTING RESOURCES")
        print("="*60)

        csv_path = os.path.join(self.csv_base_path, "RESOURCES.csv")
        df = pd.read_csv(csv_path)
        print(f"  📄 Loaded {len(df)} rows")

        cursor = self.conn.cursor()
        now = datetime.now()
        inserted = 0

        # Valid ResourceType: 'Crane', 'Tugboat', 'Pilot', 'Labor', 'Mooring', 'Other'
        type_map = {
            'crane': 'Crane', 'tugboat': 'Tugboat', 'tug': 'Tugboat',
            'pilot': 'Pilot', 'labor': 'Labor', 'mooring': 'Mooring',
            'equipment': 'Other', 'other': 'Other'
        }

        for idx, row in df.iterrows():
            try:
                raw_type = str(row.get('resource_type', 'Other')).lower().strip()
                resource_type = type_map.get(raw_type, 'Other')
                
                # Capacity must be > 0
                capacity = int(row['count']) if pd.notna(row.get('count')) and int(row['count']) > 0 else 1
                
                cursor.execute("""
                    INSERT INTO RESOURCES (ResourceType, ResourceName, Capacity,
                                          IsAvailable, MaintenanceSchedule, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    resource_type,
                    f"{resource_type} {idx+1}",
                    capacity,
                    True, None, now
                ))
                inserted += 1
            except Exception as e:
                if inserted < 5:
                    print(f"  ⚠️  Error: {e}")

        self.conn.commit()
        print(f"  ✅ Inserted {inserted} resources")

    def import_all(self):
        """Run complete import"""
        print("\n" + "="*60)
        print("🚀 MUNDRA DATA IMPORT V4 (CHECK CONSTRAINTS FIXED)")
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

            # Final verification
            print("\n" + "="*60)
            print("📊 FINAL VERIFICATION")
            print("="*60)
            cursor = self.conn.cursor()
            tables = ['VESSELS', 'BERTHS', 'VESSEL_SCHEDULE', 'WEATHER_DATA', 
                     'TIDAL_DATA', 'AIS_DATA', 'RESOURCES']
            total = 0
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
                count = cursor.fetchone()[0]
                total += count
                print(f"   {table}: {count:,} rows")
            print(f"   TOTAL: {total:,} rows")

            print("\n" + "="*60)
            print("✅ IMPORT COMPLETED SUCCESSFULLY")
            print("="*60)
            print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        except Exception as e:
            print(f"\n❌ IMPORT FAILED: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()


if __name__ == "__main__":
    CONNECTION_STRING = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "Server=20.204.224.123,1433;"
        "Database=BerthPlanning;"
        "UID=Admin;"
        "PWD=Adm!n#@@7;"
        "TrustServerCertificate=Yes;"
    )

    CSV_BASE_PATH = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\documents\Data\Mundra"

    importer = MundraDataImporterV4(CONNECTION_STRING, CSV_BASE_PATH)
    importer.import_all()
