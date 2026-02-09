"""
Import Mundra CSV Files to SQL Server BerthPlanningDB
Handles column mapping, unit conversions, and data enrichment
"""

import pandas as pd
import pyodbc
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional

class MundraDataImporter:
    def __init__(self, connection_string: str, csv_base_path: str):
        """
        Initialize importer with database connection and CSV file path

        Args:
            connection_string: SQL Server connection string
            csv_base_path: Path to directory containing CSV files
        """
        self.connection_string = connection_string
        self.csv_base_path = csv_base_path
        self.conn = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = pyodbc.connect(self.connection_string)
            print("✓ Connected to SQL Server")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Connection closed")

    # ==================== VESSELS TABLE ====================

    def extract_imo_from_field(self, imo_mmsi: str) -> Optional[str]:
        """Extract IMO number from 'IMO9225772|MMSI761415646' format"""
        if not imo_mmsi or pd.isna(imo_mmsi):
            return None
        match = re.search(r'IMO(\d+)', str(imo_mmsi))
        return match.group(1) if match else None

    def derive_vessel_type(self, cargo_type: str, loa: float) -> str:
        """
        Derive VesselType from cargo_type and vessel dimensions
        """
        cargo_map = {
            'container': 'Container',
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

        vessel_type = cargo_map.get(cargo_type.lower() if cargo_type else '', 'General Cargo')

        # Size-based refinement for containers
        if vessel_type == 'Container' and loa:
            if loa > 350:
                vessel_type = 'Ultra Large Container'
            elif loa > 300:
                vessel_type = 'Large Container'

        return vessel_type

    def calculate_gross_tonnage(self, loa: float, beam: float, draft: float) -> int:
        """
        Estimate GT using simplified formula
        GT ≈ (LOA × Beam × Draft × Block Coefficient) × K
        Block coefficient ~0.7 for container ships, K ~0.3
        """
        if pd.isna(loa) or pd.isna(beam) or pd.isna(draft):
            return 0

        block_coefficient = 0.70  # Typical for container ships
        k_factor = 0.30

        volume = loa * beam * draft * block_coefficient
        gt = int(volume * k_factor)

        return max(gt, 1000)  # Minimum 1000 GT

    def import_vessels(self):
        """Import VESSELS.csv with column mapping and data enrichment"""
        print("\n" + "="*80)
        print("IMPORTING VESSELS")
        print("="*80)

        # Read CSV
        csv_path = os.path.join(self.csv_base_path, 'VESSELS.csv')
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} vessels from CSV")

        # Load cargo type from schedule to derive vessel type
        schedule_df = pd.read_csv(os.path.join(self.csv_base_path, 'VESSEL_SCHEDULE.csv'))
        vessel_cargo_map = schedule_df.groupby('vessel_id')['cargo_type'].first().to_dict()

        cursor = self.conn.cursor()

        # Clear existing data (optional - comment out if appending)
        # cursor.execute("DELETE FROM VESSELS")
        # print("  Cleared existing VESSELS data")

        insert_sql = """
        INSERT INTO VESSELS (
            VesselId, VesselName, VesselType, IMO, LOA, Beam, Draft, GT,
            Flag, IsActive, DWT, PrimaryCargo, DangerousGoods
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        inserted = 0
        errors = 0

        for idx, row in df.iterrows():
            try:
                # Extract IMO from combined field
                imo = self.extract_imo_from_field(row['imo_mmsi'])

                # Get cargo type for this vessel
                cargo_type = vessel_cargo_map.get(row['vessel_id'], 'container')

                # Derive vessel type
                vessel_type = self.derive_vessel_type(cargo_type, row.get('loa_m'))

                # Calculate GT
                gt = self.calculate_gross_tonnage(
                    row.get('loa_m', 0),
                    row.get('beam_m', 0),
                    row.get('draft_m', 0)
                )

                # DWT approximation (typically 1.5-2x GT for cargo vessels)
                dwt = int(gt * 1.7) if gt > 0 else 0

                cursor.execute(insert_sql, (
                    row['vessel_id'],                    # VesselId
                    row['vessel_name'],                  # VesselName
                    vessel_type,                         # VesselType (derived)
                    imo or 'IMO0000000',                # IMO (extracted)
                    row.get('loa_m'),                   # LOA
                    row.get('beam_m'),                  # Beam
                    row.get('draft_m'),                 # Draft
                    gt,                                  # GT (calculated)
                    row.get('line_operator', 'Unknown'), # Flag (using operator as proxy)
                    1,                                   # IsActive
                    dwt,                                 # DWT (calculated)
                    cargo_type,                          # PrimaryCargo
                    0                                    # DangerousGoods (default false)
                ))
                inserted += 1

                if (inserted % 1000) == 0:
                    print(f"  Progress: {inserted}/{len(df)} vessels inserted...")

            except Exception as e:
                errors += 1
                if errors <= 5:  # Show first 5 errors only
                    print(f"  ⚠️  Error on row {idx}: {e}")

        self.conn.commit()
        print(f"\n✓ Imported {inserted} vessels successfully")
        if errors > 0:
            print(f"⚠️  {errors} rows failed")

    # ==================== BERTHS TABLE ====================

    def derive_berth_type(self, cargo_allowed: str, equipment: str) -> str:
        """Derive BerthType from cargo and equipment"""
        if 'container' in cargo_allowed.lower():
            return 'Container'
        elif 'bulk' in cargo_allowed.lower():
            return 'Bulk'
        elif 'crude' in cargo_allowed.lower() or 'oil' in cargo_allowed.lower():
            return 'Tanker'
        elif 'roro' in cargo_allowed.lower():
            return 'RoRo'
        else:
            return 'General'

    def count_cranes(self, equipment: str) -> int:
        """Extract number of cranes from equipment description"""
        if not equipment or pd.isna(equipment):
            return 0

        equipment_lower = equipment.lower()
        if 'sts' in equipment_lower or 'crane' in equipment_lower:
            # Try to find number in equipment string
            match = re.search(r'(\d+)\s*crane', equipment_lower)
            if match:
                return int(match.group(1))
            return 2  # Default assumption if STS mentioned
        return 0

    def import_berths(self):
        """Import BERTHS.csv with column mapping"""
        print("\n" + "="*80)
        print("IMPORTING BERTHS")
        print("="*80)

        csv_path = os.path.join(self.csv_base_path, 'BERTHS.csv')
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} berths from CSV")

        cursor = self.conn.cursor()

        insert_sql = """
        INSERT INTO BERTHS (
            BerthId, BerthName, BerthType, Length, MaxDraft, MaxBeam,
            NumberOfCranes, IsActive, BerthDepth, Exposure, BerthSpecialization
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        inserted = 0

        for idx, row in df.iterrows():
            try:
                berth_type = self.derive_berth_type(row['cargo_allowed'], row.get('equipment', ''))
                num_cranes = self.count_cranes(row.get('equipment', ''))

                cursor.execute(insert_sql, (
                    row['berth_id'],                     # BerthId
                    row['berth_id'],                     # BerthName (same as ID)
                    berth_type,                          # BerthType (derived)
                    row['max_loa_m'],                   # Length (max LOA accepted)
                    row['max_draft_m'],                 # MaxDraft
                    row['max_beam_m'],                  # MaxBeam
                    num_cranes,                          # NumberOfCranes (extracted)
                    1,                                   # IsActive
                    row['max_draft_m'],                 # BerthDepth (same as max draft)
                    'Sheltered',                         # Exposure (default)
                    row['cargo_allowed']                 # BerthSpecialization
                ))
                inserted += 1

            except Exception as e:
                print(f"  ⚠️  Error on row {idx}: {e}")

        self.conn.commit()
        print(f"✓ Imported {inserted} berths successfully")

    # ==================== VESSEL_SCHEDULE TABLE ====================

    def map_schedule_status(self, status: str) -> str:
        """Map CSV status to SQL Server status values"""
        status_map = {
            'completed': 'Completed',
            'in_progress': 'In Progress',
            'scheduled': 'Scheduled',
            'cancelled': 'Cancelled'
        }
        return status_map.get(status.lower() if status else 'scheduled', 'Scheduled')

    def import_vessel_schedule(self):
        """Import VESSEL_SCHEDULE.csv with datetime parsing"""
        print("\n" + "="*80)
        print("IMPORTING VESSEL_SCHEDULE")
        print("="*80)

        csv_path = os.path.join(self.csv_base_path, 'VESSEL_SCHEDULE.csv')
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} schedules from CSV")

        # Parse datetime columns
        datetime_cols = ['eta_ts', 'ata_ts', 'atb_ts', 'atd_ts', 'etc_ts', 'anchorage_ts']
        for col in datetime_cols:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        cursor = self.conn.cursor()

        insert_sql = """
        INSERT INTO VESSEL_SCHEDULE (
            ScheduleId, VesselId, BerthId, ETA, ETD, Status, Priority,
            ATA, ATB, ATD, DwellTime, WaitingTime, CargoType, CargoQuantity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        inserted = 0

        for idx, row in df.iterrows():
            try:
                # Derive priority from cargo type and vessel size
                priority = 2  # Default: Medium
                if 'container' in row.get('cargo_type', '').lower():
                    priority = 1  # High for containers
                elif 'crude' in row.get('cargo_type', '').lower():
                    priority = 1  # High for crude oil

                cursor.execute(insert_sql, (
                    row['schedule_id'],                  # ScheduleId
                    row['vessel_id'],                    # VesselId
                    row['berth_id'],                     # BerthId
                    row['eta_ts'],                       # ETA
                    row['etc_ts'],                       # ETD (using ETC)
                    self.map_schedule_status(row['status']), # Status
                    priority,                            # Priority (derived)
                    row['ata_ts'],                       # ATA
                    row['atb_ts'],                       # ATB
                    row['atd_ts'],                       # ATD
                    row.get('service_time_hours'),      # DwellTime
                    row.get('waiting_time_hours'),      # WaitingTime
                    row.get('cargo_type'),              # CargoType
                    row.get('quantity')                  # CargoQuantity
                ))
                inserted += 1

                if (inserted % 1000) == 0:
                    print(f"  Progress: {inserted}/{len(df)} schedules inserted...")

            except Exception as e:
                print(f"  ⚠️  Error on row {idx}: {e}")

        self.conn.commit()
        print(f"✓ Imported {inserted} schedules successfully")

    # ==================== WEATHER_DATA TABLE ====================

    def convert_wind_speed(self, mps: float) -> float:
        """Convert wind speed from m/s to knots"""
        return mps * 1.94384  # 1 m/s = 1.94384 knots

    def convert_visibility(self, km: float) -> float:
        """Convert visibility from km to meters"""
        return km * 1000

    def calculate_wave_height(self, wind_speed_mps: float, wind_gust_mps: float) -> float:
        """
        Estimate wave height from wind speed using empirical formula
        Significant Wave Height (m) ≈ 0.21 × (Wind Speed in m/s)²
        """
        avg_wind = (wind_speed_mps + wind_gust_mps) / 2
        wave_height = 0.21 * (avg_wind ** 1.5) / 10  # Dampened for harbor conditions
        return round(wave_height, 2)

    def import_weather_data(self):
        """Import WEATHER_DATA.csv with unit conversions"""
        print("\n" + "="*80)
        print("IMPORTING WEATHER_DATA")
        print("="*80)

        csv_path = os.path.join(self.csv_base_path, 'WEATHER_DATA.csv')
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} weather records from CSV")

        # Parse datetime
        df['ts_hour'] = pd.to_datetime(df['ts_hour'])

        cursor = self.conn.cursor()

        insert_sql = """
        INSERT INTO WEATHER_DATA (
            RecordedAt, WindSpeed, WaveHeight, Visibility, WeatherCondition,
            WindDirection, Temperature, Pressure
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """

        inserted = 0

        for idx, row in df.iterrows():
            try:
                # Convert units
                wind_speed_knots = self.convert_wind_speed(row['wind_speed_mps'])
                visibility_meters = self.convert_visibility(row['visibility_km'])
                wave_height = self.calculate_wave_height(row['wind_speed_mps'], row['wind_gust_mps'])

                # Determine weather condition
                if row.get('storm_flag', 0) == 1:
                    weather_condition = 'Storm'
                elif row.get('rain_mm', 0) > 10:
                    weather_condition = 'Heavy Rain'
                elif row.get('rain_mm', 0) > 0:
                    weather_condition = 'Rain'
                elif visibility_meters < 1000:
                    weather_condition = 'Fog'
                else:
                    weather_condition = 'Clear'

                cursor.execute(insert_sql, (
                    row['ts_hour'],                      # RecordedAt
                    wind_speed_knots,                    # WindSpeed (converted to knots)
                    wave_height,                         # WaveHeight (estimated)
                    visibility_meters,                   # Visibility (converted to meters)
                    weather_condition,                   # WeatherCondition (derived)
                    None,                                # WindDirection (not in CSV)
                    None,                                # Temperature (not in CSV)
                    None                                 # Pressure (not in CSV)
                ))
                inserted += 1

                if (inserted % 1000) == 0:
                    print(f"  Progress: {inserted}/{len(df)} weather records inserted...")

            except Exception as e:
                print(f"  ⚠️  Error on row {idx}: {e}")

        self.conn.commit()
        print(f"✓ Imported {inserted} weather records successfully")

    # ==================== TIDAL_DATA TABLE ====================

    def import_tidal_data(self):
        """Import TIDAL_DATA.csv"""
        print("\n" + "="*80)
        print("IMPORTING TIDAL_DATA")
        print("="*80)

        csv_path = os.path.join(self.csv_base_path, 'TIDAL_DATA.csv')
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} tidal records from CSV")

        # Parse datetime
        df['ts'] = pd.to_datetime(df['ts'])

        cursor = self.conn.cursor()

        insert_sql = """
        INSERT INTO TIDAL_DATA (
            TideDateTime, TideHeight, TideType
        ) VALUES (?, ?, ?)
        """

        inserted = 0

        for idx, row in df.iterrows():
            try:
                cursor.execute(insert_sql, (
                    row['ts'],                           # TideDateTime
                    row['tide_height_m'],               # TideHeight
                    row['tide_phase']                    # TideType (HIGH/LOW)
                ))
                inserted += 1

            except Exception as e:
                print(f"  ⚠️  Error on row {idx}: {e}")

        self.conn.commit()
        print(f"✓ Imported {inserted} tidal records successfully")

    # ==================== AIS_DATA TABLE ====================

    def import_ais_data(self):
        """Import AIS_DATA.csv (large file - batch processing)"""
        print("\n" + "="*80)
        print("IMPORTING AIS_DATA")
        print("="*80)

        csv_path = os.path.join(self.csv_base_path, 'AIS_DATA.csv')

        # Read in chunks to handle large file
        chunk_size = 10000
        total_inserted = 0

        cursor = self.conn.cursor()

        insert_sql = """
        INSERT INTO AIS_DATA (
            VesselId, RecordedAt, Latitude, Longitude, Speed,
            Heading, COG, SOG, Status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        for chunk_num, chunk_df in enumerate(pd.read_csv(csv_path, chunksize=chunk_size)):
            # Parse datetime
            chunk_df['ts'] = pd.to_datetime(chunk_df['ts'])

            inserted = 0

            for idx, row in chunk_df.iterrows():
                try:
                    cursor.execute(insert_sql, (
                        row['vessel_id'],                # VesselId
                        row['ts'],                       # RecordedAt
                        row['lat'],                      # Latitude
                        row['lon'],                      # Longitude
                        row['sog_kn'],                  # Speed (SOG)
                        row['cog_deg'],                 # Heading (using COG as proxy)
                        row['cog_deg'],                 # COG
                        row['sog_kn'],                  # SOG
                        row['nav_status']                # Status
                    ))
                    inserted += 1
                    total_inserted += 1

                except Exception as e:
                    if inserted == 0:  # Show first error only per chunk
                        print(f"  ⚠️  Error in chunk {chunk_num}: {e}")

            self.conn.commit()
            print(f"  Chunk {chunk_num + 1}: {inserted} records inserted (Total: {total_inserted})")

        print(f"✓ Imported {total_inserted} AIS records successfully")

    # ==================== RESOURCES TABLE ====================

    def map_resource_type(self, resource_type: str) -> str:
        """Map CSV resource types to SQL Server types"""
        type_map = {
            'sts_crane': 'Crane',
            'rtg': 'Crane',
            'yard_tractor': 'Yard Equipment',
            'pilot': 'Pilot',
            'tugboat': 'Tugboat',
            'mooring_gang': 'Labor',
            'customs': 'Administrative',
            'security': 'Administrative'
        }
        return type_map.get(resource_type.lower() if resource_type else '', 'Other')

    def import_resources(self):
        """Import RESOURCES.csv"""
        print("\n" + "="*80)
        print("IMPORTING RESOURCES")
        print("="*80)

        csv_path = os.path.join(self.csv_base_path, 'RESOURCES.csv')
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} resources from CSV")

        cursor = self.conn.cursor()

        insert_sql = """
        INSERT INTO RESOURCES (
            ResourceId, ResourceType, ResourceName, IsAvailable,
            Capacity, BerthId, ShiftPattern
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        inserted = 0

        for idx, row in df.iterrows():
            try:
                # Determine availability (1 if availability > 80%)
                is_available = 1 if row.get('availability_pct', 0) > 0.80 else 0

                # Generate resource name
                resource_name = f"{row['resource_type']} - {row['terminal_code']}"
                if not pd.isna(row.get('berth_id')):
                    resource_name = f"{row['resource_type']} - {row['berth_id']}"

                cursor.execute(insert_sql, (
                    row['resource_id'],                  # ResourceId
                    self.map_resource_type(row['resource_type']), # ResourceType
                    resource_name,                       # ResourceName
                    is_available,                        # IsAvailable
                    row.get('capacity_per_hr'),         # Capacity
                    row.get('berth_id'),                # BerthId
                    '24/7'                               # ShiftPattern (default)
                ))
                inserted += 1

            except Exception as e:
                print(f"  ⚠️  Error on row {idx}: {e}")

        self.conn.commit()
        print(f"✓ Imported {inserted} resources successfully")

    # ==================== MAIN IMPORT WORKFLOW ====================

    def import_all(self):
        """Import all CSV files in order"""
        print("\n" + "="*80)
        print("MUNDRA CSV TO SQL SERVER IMPORT")
        print("="*80)
        print(f"CSV Path: {self.csv_base_path}")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            self.connect()

            # Import in dependency order
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

            print("\n[6/7] Importing AIS_DATA (this may take several minutes)...")
            self.import_ais_data()

            print("\n[7/7] Importing RESOURCES...")
            self.import_resources()

            print("\n" + "="*80)
            print("✅ IMPORT COMPLETED SUCCESSFULLY")
            print("="*80)
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
    importer = MundraDataImporter(CONNECTION_STRING, CSV_BASE_PATH)
    importer.import_all()
