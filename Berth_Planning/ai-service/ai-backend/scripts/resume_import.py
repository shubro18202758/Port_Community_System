"""
Resume AIS data import and seed RESOURCES
Resumes from where the previous import left off
"""
import pyodbc
import pandas as pd
from datetime import datetime
import os

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "Server=20.204.224.123,1433;"
    "Database=BerthPlanning;"
    "UID=Admin;"
    "PWD=Adm!n#@@7;"
    "TrustServerCertificate=Yes;"
    "Connection Timeout=60;"
)

CSV_BASE_PATH = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\documents\Data\Mundra"
PORT_CODE = "INMUN"  # Mundra port code

def import_resources(cursor, conn):
    """Import RESOURCES table"""
    print("\n" + "="*60)
    print("IMPORTING RESOURCES")
    print("="*60)

    csv_path = os.path.join(CSV_BASE_PATH, "RESOURCES.csv")
    if not os.path.exists(csv_path):
        print(f"  ⚠️  File not found: {csv_path}")
        return
        
    df = pd.read_csv(csv_path)
    print(f"  📄 Loaded {len(df)} rows")

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

    conn.commit()
    print(f"  ✅ Inserted {inserted} resources")

def resume_ais_import(cursor, conn, skip_rows=20000, batch_size=10000):
    """Resume AIS data import from offset"""
    print("\n" + "="*60)
    print(f"RESUMING AIS_DATA IMPORT (skipping first {skip_rows:,} records)")
    print("="*60)

    csv_path = os.path.join(CSV_BASE_PATH, "AIS_DATA.csv")
    
    # Get vessel IDs for cycling
    cursor.execute("SELECT VesselId FROM VESSELS")
    vessel_ids = [row[0] for row in cursor.fetchall()]
    if not vessel_ids:
        vessel_ids = [1]
    print(f"  Found {len(vessel_ids)} vessel IDs for distribution")

    now = datetime.now()
    total_inserted = skip_rows  # Start counting from where we left off
    chunk_num = skip_rows // batch_size

    for chunk in pd.read_csv(csv_path, chunksize=batch_size, skiprows=range(1, skip_rows + 1)):
        chunk_num += 1
        print(f"  📦 Processing chunk {chunk_num} ({len(chunk)} rows)...")
        
        inserted = 0
        errors = 0
        
        for idx, row in chunk.iterrows():
            try:
                vessel_id = vessel_ids[total_inserted % len(vessel_ids)]
                
                # Parse timestamp with error handling
                try:
                    ts_val = row.get('ts')
                    if pd.notna(ts_val):
                        recorded_at = pd.to_datetime(ts_val, errors='coerce')
                        if pd.isna(recorded_at):
                            recorded_at = now
                    else:
                        recorded_at = now
                except:
                    recorded_at = now

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
                    vessel_id, None, PORT_CODE, 'Cargo',
                    lat, lon, speed, course, heading,
                    nav_status_text, 0, 'Approaching', recorded_at, now
                ))
                inserted += 1
                total_inserted += 1
            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"    ⚠️  Error row {idx}: {e}")

        conn.commit()
        print(f"    ✓ Inserted {inserted} (total: {total_inserted:,}, errors: {errors})")

    print(f"\n  ✅ Total AIS records: {total_inserted:,}")

def main():
    print("="*60)
    print("🚀 RESUMING DATA IMPORT")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        conn = pyodbc.connect(CONNECTION_STRING, timeout=120)
        cursor = conn.cursor()
        print("✅ Connected to remote server")
        
        # Check current AIS count
        cursor.execute("SELECT COUNT(*) FROM AIS_DATA")
        current_ais = cursor.fetchone()[0]
        print(f"\nCurrent AIS_DATA count: {current_ais:,}")
        
        # Check if RESOURCES needs importing
        cursor.execute("SELECT COUNT(*) FROM RESOURCES")
        if cursor.fetchone()[0] == 0:
            import_resources(cursor, conn)
        else:
            print("\n⏭️  RESOURCES already has data, skipping...")
        
        # Resume AIS import
        if current_ais < 400000:
            resume_ais_import(cursor, conn, skip_rows=current_ais)
        else:
            print("\n⏭️  AIS_DATA appears complete, skipping...")
        
        # Final counts
        print("\n" + "="*60)
        print("📊 FINAL COUNTS")
        print("="*60)
        tables = ['VESSELS', 'BERTHS', 'VESSEL_SCHEDULE', 'WEATHER_DATA', 
                 'TIDAL_DATA', 'AIS_DATA', 'RESOURCES']
        total = 0
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = cursor.fetchone()[0]
            total += count
            print(f"   {table}: {count:,}")
        print(f"   TOTAL: {total:,}")
        
        print("\n✅ IMPORT COMPLETED")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'conn' in locals():
            conn.close()
            print("Connection closed")

if __name__ == "__main__":
    main()
