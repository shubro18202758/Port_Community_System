"""
Seed missing tables on remote Azure SQL Server
Tables: CHANNELS, ANCHORAGES, UKC_DATA, PILOTS, TUGBOATS
"""
import pyodbc
import pandas as pd
from datetime import datetime

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "Server=20.204.224.123,1433;"
    "Database=BerthPlanning;"
    "UID=Admin;"
    "PWD=Adm!n#@@7;"
    "TrustServerCertificate=Yes;"
)

CSV_BASE_PATH = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\Test_Data"

def seed_channels(cursor, conn):
    """Seed CHANNELS table"""
    print("\n[1/5] Seeding CHANNELS...")
    df = pd.read_csv(f"{CSV_BASE_PATH}/CHANNELS.csv")
    print(f"  Loaded {len(df)} rows from CSV")
    
    inserted = 0
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO CHANNELS (PortId, ChannelName, ChannelLength, ChannelWidth, 
                    ChannelDepth, ChannelDepthAtChartDatum, OneWayOrTwoWay, MaxVesselLOA, 
                    MaxVesselBeam, MaxVesselDraft, TrafficSeparationScheme, SpeedLimit, 
                    TidalWindowRequired, PilotageCompulsory, TugEscortRequired, DayNightRestrictions, 
                    VisibilityMinimum, WindSpeedLimit, CurrentSpeedLimit, IsActive, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1,  # PortId
                str(row.get('ChannelName', f'Channel {inserted+1}')),
                float(row['ChannelLength']) if pd.notna(row.get('ChannelLength')) else 10.0,
                float(row['ChannelWidth']) if pd.notna(row.get('ChannelWidth')) else 300.0,
                float(row['ChannelDepth']) if pd.notna(row.get('ChannelDepth')) else 15.0,
                float(row['ChannelDepthAtChartDatum']) if pd.notna(row.get('ChannelDepthAtChartDatum')) else 14.0,
                str(row.get('OneWayOrTwoWay', 'Two-Way')),
                float(row['MaxVesselLOA']) if pd.notna(row.get('MaxVesselLOA')) else 400.0,
                float(row['MaxVesselBeam']) if pd.notna(row.get('MaxVesselBeam')) else 60.0,
                float(row['MaxVesselDraft']) if pd.notna(row.get('MaxVesselDraft')) else 15.0,
                bool(int(row['TrafficSeparationScheme'])) if pd.notna(row.get('TrafficSeparationScheme')) else False,
                float(row['SpeedLimit']) if pd.notna(row.get('SpeedLimit')) else 10.0,
                bool(int(row['TidalWindowRequired'])) if pd.notna(row.get('TidalWindowRequired')) else False,
                bool(int(row['PilotageCompulsory'])) if pd.notna(row.get('PilotageCompulsory')) else True,
                bool(int(row['TugEscortRequired'])) if pd.notna(row.get('TugEscortRequired')) else True,
                str(row.get('DayNightRestrictions', 'None')),
                float(row['VisibilityMinimum']) if pd.notna(row.get('VisibilityMinimum')) else 1.0,
                float(row['WindSpeedLimit']) if pd.notna(row.get('WindSpeedLimit')) else 40.0,
                float(row['CurrentSpeedLimit']) if pd.notna(row.get('CurrentSpeedLimit')) else 3.0,
                True,
                datetime.now()
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error: {e}")
    
    conn.commit()
    print(f"  ✅ Inserted {inserted} channels")

def seed_anchorages(cursor, conn):
    """Seed ANCHORAGES table"""
    print("\n[2/5] Seeding ANCHORAGES...")
    df = pd.read_csv(f"{CSV_BASE_PATH}/ANCHORAGES.csv")
    print(f"  Loaded {len(df)} rows from CSV")
    
    inserted = 0
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO ANCHORAGES (PortId, AnchorageName, AnchorageType, Latitude, 
                    Longitude, Depth, MaxVessels, CurrentOccupancy, MaxVesselLOA, MaxVesselDraft, 
                    AverageWaitingTime, STSCargoOpsPermitted, QuarantineAnchorage, IsActive, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1,  # PortId
                str(row.get('AnchorageName', f'Anchorage {inserted+1}')),
                str(row.get('AnchorageType', 'General')),
                float(row['Latitude']) if pd.notna(row.get('Latitude')) else 22.4,
                float(row['Longitude']) if pd.notna(row.get('Longitude')) else 69.7,
                float(row['Depth']) if pd.notna(row.get('Depth')) else 15.0,
                int(row['MaxVessels']) if pd.notna(row.get('MaxVessels')) else 10,
                int(row['CurrentOccupancy']) if pd.notna(row.get('CurrentOccupancy')) else 0,
                float(row['MaxVesselLOA']) if pd.notna(row.get('MaxVesselLOA')) else 400.0,
                float(row['MaxVesselDraft']) if pd.notna(row.get('MaxVesselDraft')) else 15.0,
                float(row['AverageWaitingTime']) if pd.notna(row.get('AverageWaitingTime')) else 4.0,
                bool(int(row['STSCargoOpsPermitted'])) if pd.notna(row.get('STSCargoOpsPermitted')) else False,
                bool(int(row['QuarantineAnchorage'])) if pd.notna(row.get('QuarantineAnchorage')) else False,
                True,
                datetime.now()
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error: {e}")
    
    conn.commit()
    print(f"  ✅ Inserted {inserted} anchorages")

def seed_ukc_data(cursor, conn):
    """Seed UKC_DATA table"""
    print("\n[3/5] Seeding UKC_DATA...")
    df = pd.read_csv(f"{CSV_BASE_PATH}/UKC_DATA.csv")
    print(f"  Loaded {len(df)} rows from CSV")
    
    inserted = 0
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO UKC_DATA (PortId, PortCode, VesselType, VesselLOA, VesselBeam, 
                    VesselDraft, GrossTonnage, ChannelDepth, TidalHeight, AvailableDepth, 
                    StaticUKC, Squat, DynamicUKC, UKCPercentage, RequiredUKCPercentage, 
                    IsSafe, SpeedKnots, BlockCoefficient, WaveAllowance, HeelAllowance, 
                    NetUKC, SafetyMargin, RiskLevel, Recommendation, CalculatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                1,  # PortId
                str(row.get('PortCode', 'INNSA')),
                str(row.get('VesselType', 'Container')),
                float(row['VesselLOA']) if pd.notna(row.get('VesselLOA')) else 300.0,
                float(row['VesselBeam']) if pd.notna(row.get('VesselBeam')) else 45.0,
                float(row['VesselDraft']) if pd.notna(row.get('VesselDraft')) else 14.0,
                int(row['GrossTonnage']) if pd.notna(row.get('GrossTonnage')) else 100000,
                float(row['ChannelDepth']) if pd.notna(row.get('ChannelDepth')) else 16.0,
                float(row['TidalHeight']) if pd.notna(row.get('TidalHeight')) else 2.5,
                float(row['AvailableDepth']) if pd.notna(row.get('AvailableDepth')) else 18.5,
                float(row['StaticUKC']) if pd.notna(row.get('StaticUKC')) else 4.5,
                float(row['Squat']) if pd.notna(row.get('Squat')) else 0.5,
                float(row['DynamicUKC']) if pd.notna(row.get('DynamicUKC')) else 4.0,
                float(row['UKCPercentage']) if pd.notna(row.get('UKCPercentage')) else 25.0,
                float(row['RequiredUKCPercentage']) if pd.notna(row.get('RequiredUKCPercentage')) else 10.0,
                bool(int(row['IsSafe'])) if pd.notna(row.get('IsSafe')) else True,
                float(row['SpeedKnots']) if pd.notna(row.get('SpeedKnots')) else 6.0,
                float(row['BlockCoefficient']) if pd.notna(row.get('BlockCoefficient')) else 0.72,
                float(row['WaveAllowance']) if pd.notna(row.get('WaveAllowance')) else 0.15,
                float(row['HeelAllowance']) if pd.notna(row.get('HeelAllowance')) else 0.10,
                float(row['NetUKC']) if pd.notna(row.get('NetUKC')) else 3.75,
                float(row['SafetyMargin']) if pd.notna(row.get('SafetyMargin')) else 1.5,
                str(row.get('RiskLevel', 'Low')),
                str(row.get('Recommendation', 'Safe to transit'))[:500],
                datetime.now()
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error: {e}")
    
    conn.commit()
    print(f"  ✅ Inserted {inserted} UKC records")

def seed_pilots(cursor, conn):
    """Seed PILOTS table"""
    print("\n[4/5] Seeding PILOTS...")
    df = pd.read_csv(f"{CSV_BASE_PATH}/PILOTS.csv")
    print(f"  Loaded {len(df)} rows from CSV")
    
    inserted = 0
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO PILOTS (PortCode, PortName, PilotName, PilotCode, PilotType, 
                    PilotClass, CertificationLevel, ExperienceYears, MaxVesselGT, MaxVesselLOA, 
                    NightOperations, AdverseWeather, CanTrain, LicenseIssueDate, LicenseExpiryDate, 
                    Status, Languages, Certifications, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row.get('PortCode', 'INNSA')),
                str(row.get('PortName', 'JNPT')),
                str(row.get('PilotName', f'Pilot {inserted+1}')),
                str(row.get('PilotCode', f'PIL-{inserted+1:03d}')),
                str(row.get('PilotType', 'Harbor')),
                str(row.get('PilotClass', 'Class I')),
                str(row.get('CertificationLevel', 'Class A')),
                int(row['ExperienceYears']) if pd.notna(row.get('ExperienceYears')) else 10,
                int(row['MaxVesselGT']) if pd.notna(row.get('MaxVesselGT')) else 200000,
                float(row['MaxVesselLOA']) if pd.notna(row.get('MaxVesselLOA')) else 400.0,
                bool(int(row['NightOperations'])) if pd.notna(row.get('NightOperations')) else True,
                bool(int(row['AdverseWeather'])) if pd.notna(row.get('AdverseWeather')) else True,
                bool(int(row['CanTrain'])) if pd.notna(row.get('CanTrain')) else False,
                pd.to_datetime(row.get('LicenseIssueDate'), errors='coerce') if pd.notna(row.get('LicenseIssueDate')) else datetime.now(),
                pd.to_datetime(row.get('LicenseExpiryDate'), errors='coerce') if pd.notna(row.get('LicenseExpiryDate')) else datetime.now(),
                str(row.get('Status', 'Active')),
                str(row.get('Languages', 'English'))[:200],
                str(row.get('Certifications', 'STCW'))[:500],
                datetime.now()
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error: {e}")
    
    conn.commit()
    print(f"  ✅ Inserted {inserted} pilots")

def seed_tugboats(cursor, conn):
    """Seed TUGBOATS table"""
    print("\n[5/5] Seeding TUGBOATS...")
    df = pd.read_csv(f"{CSV_BASE_PATH}/TUGBOATS.csv")
    print(f"  Loaded {len(df)} rows from CSV")
    
    inserted = 0
    for _, row in df.iterrows():
        try:
            cursor.execute("""
                INSERT INTO TUGBOATS (PortCode, TugName, TugCode, IMONumber, MMSI, CallSign, 
                    FlagState, PortOfRegistry, TugType, TugClass, Operator, BollardPull, 
                    Length, Beam, Draft, EnginePower, MaxSpeed, YearBuilt, FiFiClass, 
                    WinchCapacity, CrewSize, Status, CreatedAt)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(row.get('PortCode', 'INNSA')),
                str(row.get('TugName', f'Tug {inserted+1}')),
                str(row.get('TugCode', f'TUG-{inserted+1:03d}')),
                str(row.get('IMONumber', '')) if pd.notna(row.get('IMONumber')) else None,
                str(row.get('MMSI', '')) if pd.notna(row.get('MMSI')) else None,
                str(row.get('CallSign', '')) if pd.notna(row.get('CallSign')) else None,
                str(row.get('FlagState', 'IN')),
                str(row.get('PortOfRegistry', 'Mumbai')),
                str(row.get('TugType', 'ASD')),
                str(row.get('TugClass', 'A')),
                str(row.get('Operator', 'JNPT')),
                int(row['BollardPull']) if pd.notna(row.get('BollardPull')) else 50,
                float(row['Length']) if pd.notna(row.get('Length')) else 30.0,
                float(row['Beam']) if pd.notna(row.get('Beam')) else 10.0,
                float(row['Draft']) if pd.notna(row.get('Draft')) else 4.5,
                int(row['EnginePower']) if pd.notna(row.get('EnginePower')) else 4000,
                float(row['MaxSpeed']) if pd.notna(row.get('MaxSpeed')) else 12.0,
                int(row['YearBuilt']) if pd.notna(row.get('YearBuilt')) else 2015,
                str(row.get('FiFiClass', 'FiFi 1')) if pd.notna(row.get('FiFiClass')) else None,
                int(row['WinchCapacity']) if pd.notna(row.get('WinchCapacity')) else 40,
                int(row['CrewSize']) if pd.notna(row.get('CrewSize')) else 8,
                str(row.get('Status', 'Operational')),
                datetime.now()
            ))
            inserted += 1
        except Exception as e:
            print(f"  Error: {e}")
    
    conn.commit()
    print(f"  ✅ Inserted {inserted} tugboats")

def verify_counts(cursor):
    """Verify final counts"""
    print("\n" + "="*60)
    print("📊 VERIFICATION - Table Counts")
    print("="*60)
    
    tables = ['CHANNELS', 'ANCHORAGES', 'UKC_DATA', 'PILOTS', 'TUGBOATS']
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
            count = cursor.fetchone()[0]
            print(f"  {table}: {count}")
        except Exception as e:
            print(f"  {table}: Error - {e}")

def main():
    print("="*60)
    print("🚀 SEEDING MISSING TABLES ON REMOTE SERVER")
    print("="*60)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Server: 20.204.224.123,1433")
    print(f"Database: BerthPlanning")
    
    try:
        conn = pyodbc.connect(CONNECTION_STRING, timeout=60)
        cursor = conn.cursor()
        print("✅ Connected to remote server")
        
        # Check current counts
        print("\nCurrent table counts (before seeding):")
        verify_counts(cursor)
        
        # Clear existing data if any
        print("\nClearing existing data...")
        for table in ['CHANNELS', 'ANCHORAGES', 'UKC_DATA']:
            try:
                cursor.execute(f"DELETE FROM [{table}]")
                conn.commit()
                print(f"  Cleared {table}")
            except Exception as e:
                print(f"  Could not clear {table}: {e}")
        
        # Seed tables
        seed_channels(cursor, conn)
        seed_anchorages(cursor, conn)
        seed_ukc_data(cursor, conn)
        seed_pilots(cursor, conn)
        seed_tugboats(cursor, conn)
        
        # Final verification
        verify_counts(cursor)
        
        print("\n" + "="*60)
        print("✅ SEEDING COMPLETED SUCCESSFULLY")
        print("="*60)
        
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
