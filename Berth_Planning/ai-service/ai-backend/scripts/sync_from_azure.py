"""
Sync LocalDB from Azure SQL Server (Backup_BerthPlanning)
Pulls all data from Azure and replaces LocalDB data
"""

import pyodbc
import sys
from datetime import datetime

class AzureToLocalSync:
    def __init__(self):
        # Azure SQL Server connection
        self.azure_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=20.204.224.123,1433;"
            "DATABASE=Backup_BerthPlanning;"
            "UID=Admin;"
            "PWD=Adm!n#@@7;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=60;"
        )
        
        # LocalDB connection
        self.local_conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            "SERVER=(localdb)\\MSSQLLocalDB;"
            "DATABASE=BerthPlanning;"
            "Trusted_Connection=yes;"
        )
        
        self.azure_conn = None
        self.local_conn = None
        
        # Tables in dependency order (for insert)
        self.tables_insert_order = [
            'PORTS',
            'TERMINALS', 
            'BERTHS',
            'VESSELS',
            'ANCHORAGES',
            'CHANNELS',
            'PILOTS',
            'TUGBOATS',
            'WEATHER_DATA',
            'TIDAL_DATA',
            'VESSEL_SCHEDULE',
            'AIS_DATA',
            'UKC_DATA',
            'VESSEL_HISTORY',
            'BERTH_MAINTENANCE',
            'ALERTS_NOTIFICATIONS'
        ]
        
        # Delete order is reverse
        self.tables_delete_order = list(reversed(self.tables_insert_order))
        
    def connect(self):
        print("="*70)
        print("CONNECTING TO DATABASES")
        print("="*70)
        
        print("\n  Connecting to Azure SQL Server (Backup_BerthPlanning)...")
        self.azure_conn = pyodbc.connect(self.azure_conn_str, timeout=60)
        print("  ✅ Connected to Azure SQL Server")
        
        print("\n  Connecting to LocalDB (BerthPlanning)...")
        self.local_conn = pyodbc.connect(self.local_conn_str, timeout=30)
        print("  ✅ Connected to LocalDB")
        
    def close(self):
        if self.azure_conn:
            self.azure_conn.close()
        if self.local_conn:
            self.local_conn.close()
        print("\nConnections closed")
        
    def get_table_columns(self, cursor, table_name):
        """Get column names for a table"""
        cursor.execute(f"""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
        """)
        return [row[0] for row in cursor.fetchall()]
        
    def has_identity_column(self, cursor, table_name):
        """Check if table has an identity column"""
        cursor.execute(f"""
            SELECT COUNT(*) FROM sys.identity_columns ic
            JOIN sys.tables t ON ic.object_id = t.object_id
            WHERE t.name = '{table_name}'
        """)
        return cursor.fetchone()[0] > 0
        
    def clear_local_tables(self):
        """Clear all tables in LocalDB in FK-safe order"""
        print("\n" + "="*70)
        print("CLEARING LOCAL TABLES")
        print("="*70)
        
        cursor = self.local_conn.cursor()
        
        for table in self.tables_delete_order:
            try:
                cursor.execute(f"DELETE FROM {table}")
                self.local_conn.commit()
                print(f"  🗑️  Cleared {table}")
            except Exception as e:
                if "Invalid object name" not in str(e):
                    print(f"  ⚠️  {table}: {str(e)[:60]}")
                    
        print("  ✅ All tables cleared")
        
    def sync_table(self, table_name, batch_size=1000):
        """Sync a single table from Azure to LocalDB"""
        print(f"\n{'='*70}")
        print(f"SYNCING: {table_name}")
        print("="*70)
        
        azure_cursor = self.azure_conn.cursor()
        local_cursor = self.local_conn.cursor()
        
        # Get columns from Azure
        try:
            azure_columns = self.get_table_columns(azure_cursor, table_name)
            if not azure_columns:
                print(f"  ⚠️  Table {table_name} not found in Azure")
                return 0
        except Exception as e:
            print(f"  ⚠️  Error getting Azure columns: {e}")
            return 0
            
        # Get columns from LocalDB
        try:
            local_columns = self.get_table_columns(local_cursor, table_name)
            if not local_columns:
                print(f"  ⚠️  Table {table_name} not found in LocalDB")
                return 0
        except Exception as e:
            print(f"  ⚠️  Error getting Local columns: {e}")
            return 0
            
        # Find common columns
        common_columns = [c for c in azure_columns if c in local_columns]
        print(f"  📋 Columns: {len(common_columns)} common ({len(azure_columns)} Azure, {len(local_columns)} Local)")
        
        if not common_columns:
            print(f"  ⚠️  No common columns!")
            return 0
            
        # Get row count from Azure
        azure_cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_rows = azure_cursor.fetchone()[0]
        print(f"  📊 Azure rows: {total_rows:,}")
        
        if total_rows == 0:
            print(f"  ⏭️  Skipping - no data")
            return 0
            
        # Check for identity column
        has_identity = self.has_identity_column(local_cursor, table_name)
        
        # Enable IDENTITY_INSERT if needed
        if has_identity:
            try:
                local_cursor.execute(f"SET IDENTITY_INSERT {table_name} ON")
            except:
                pass
                
        # Build SELECT and INSERT statements
        col_list = ", ".join(common_columns)
        placeholders = ", ".join(["?" for _ in common_columns])
        
        select_sql = f"SELECT {col_list} FROM {table_name}"
        insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"
        
        # Fetch and insert in batches
        azure_cursor.execute(select_sql)
        
        inserted = 0
        errors = 0
        batch = []
        
        while True:
            rows = azure_cursor.fetchmany(batch_size)
            if not rows:
                break
                
            for row in rows:
                try:
                    local_cursor.execute(insert_sql, row)
                    inserted += 1
                except Exception as e:
                    errors += 1
                    if errors <= 3:
                        print(f"  ⚠️  Insert error: {str(e)[:80]}")
                        
            self.local_conn.commit()
            print(f"  📦 Inserted {inserted:,}/{total_rows:,} ({100*inserted//total_rows}%)", end='\r')
            
        # Disable IDENTITY_INSERT
        if has_identity:
            try:
                local_cursor.execute(f"SET IDENTITY_INSERT {table_name} OFF")
                self.local_conn.commit()
            except:
                pass
                
        print(f"\n  ✅ Inserted {inserted:,} rows ({errors} errors)")
        return inserted
        
    def sync_pilots_custom(self):
        """Custom sync for PILOTS - Azure has PortCode, LocalDB needs PortId"""
        print(f"\n{'='*70}")
        print(f"SYNCING: PILOTS (custom mapping)")
        print("="*70)
        
        azure_cursor = self.azure_conn.cursor()
        local_cursor = self.local_conn.cursor()
        
        # Build PortCode -> PortId lookup
        local_cursor.execute("SELECT PortId, PortCode FROM PORTS")
        port_lookup = {row[1]: row[0] for row in local_cursor.fetchall()}
        print(f"  📋 Port lookup: {port_lookup}")
        
        # Get Azure data
        azure_cursor.execute("""
            SELECT PilotId, PortCode, PilotName, PilotCode, PilotClass, MaxVesselLOA, 
                   MaxVesselGT, NightOperations, AdverseWeather, Status, ExperienceYears, CreatedAt
            FROM PILOTS
        """)
        rows = azure_cursor.fetchall()
        print(f"  📊 Azure rows: {len(rows)}")
        
        local_cursor.execute("SET IDENTITY_INSERT PILOTS ON")
        
        inserted = 0
        for row in rows:
            try:
                pilot_id, port_code, pilot_name, pilot_code, pilot_class, max_loa, max_gt, night_ops, adverse, status, exp_years, created = row
                port_id = port_lookup.get(port_code, 1)
                
                local_cursor.execute("""
                    INSERT INTO PILOTS (PilotId, PortId, PilotName, LicenseNumber, LicenseClass, 
                                       VesselTypeRestrictions, MaxVesselLOA, MaxVesselDraft, MaxVesselGT,
                                       NightPilotage, DeepDraftCertified, TankerEndorsement, LNGEndorsement,
                                       Status, ContactNumber, ExperienceYears, IsActive, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pilot_id,
                    port_id,
                    pilot_name,
                    pilot_code or f'LIC{pilot_id:04d}',  # LicenseNumber from PilotCode
                    pilot_class or 'Class A',
                    'None',  # VesselTypeRestrictions
                    max_loa or 400,
                    15,  # MaxVesselDraft default
                    max_gt or 200000,
                    bool(night_ops),
                    bool(adverse),  # DeepDraftCertified from AdverseWeather
                    True,  # TankerEndorsement
                    False,  # LNGEndorsement
                    status or 'Available',
                    '+91-9900000000',  # ContactNumber
                    exp_years or 10,
                    1,
                    created
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Pilot {row[0]}: {str(e)[:60]}")
                
        self.local_conn.commit()
        local_cursor.execute("SET IDENTITY_INSERT PILOTS OFF")
        print(f"  ✅ Inserted {inserted} pilots")
        return inserted
        
    def sync_tugboats_custom(self):
        """Custom sync for TUGBOATS - Azure has PortCode, LocalDB needs PortId"""
        print(f"\n{'='*70}")
        print(f"SYNCING: TUGBOATS (custom mapping)")
        print("="*70)
        
        azure_cursor = self.azure_conn.cursor()
        local_cursor = self.local_conn.cursor()
        
        # Build PortCode -> PortId lookup
        local_cursor.execute("SELECT PortId, PortCode FROM PORTS")
        port_lookup = {row[1]: row[0] for row in local_cursor.fetchall()}
        print(f"  📋 Port lookup: {port_lookup}")
        
        # Get Azure data
        azure_cursor.execute("""
            SELECT TugId, PortCode, TugName, IMONumber, TugType, BollardPull, EnginePower,
                   Length, Beam, Draft, YearBuilt, FiFiClass, Status, CrewSize, CreatedAt
            FROM TUGBOATS
        """)
        rows = azure_cursor.fetchall()
        print(f"  📊 Azure rows: {len(rows)}")
        
        local_cursor.execute("SET IDENTITY_INSERT TUGBOATS ON")
        
        inserted = 0
        for row in rows:
            try:
                tug_id, port_code, tug_name, imo, tug_type, bollard, engine, length, beam, draft, year, fifi, status, crew, created = row
                port_id = port_lookup.get(port_code, 1)
                
                local_cursor.execute("""
                    INSERT INTO TUGBOATS (TugboatId, PortId, TugboatName, IMO, TugType, BollardPull, 
                                         EnginePower, LOA, Beam, Draft, YearBuilt, FirefightingCapability,
                                         OilSpillResponse, SalvageCapable, Status, CurrentLocation,
                                         FuelCapacity, CrewCapacity, IsActive, CreatedAt)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tug_id,
                    port_id,
                    tug_name,
                    str(imo) if imo else f'TUG{tug_id:04d}',
                    tug_type or 'ASD',
                    bollard or 60,
                    engine or 4000,
                    length or 30,
                    beam or 12,
                    draft or 5,
                    year or 2020,
                    bool(fifi) if fifi else True,
                    True,  # OilSpillResponse
                    False,  # SalvageCapable
                    status or 'Available',
                    'Port',  # CurrentLocation
                    100,  # FuelCapacity
                    crew or 6,
                    1,
                    created
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Tug {row[0]}: {str(e)[:60]}")
                
        self.local_conn.commit()
        local_cursor.execute("SET IDENTITY_INSERT TUGBOATS OFF")
        print(f"  ✅ Inserted {inserted} tugboats")
        return inserted

    def verify_sync(self):
        """Compare counts between Azure and LocalDB"""
        print("\n" + "="*70)
        print("VERIFICATION - TABLE COUNTS")
        print("="*70)
        print(f"  {'Table':<20} {'Azure':>12} {'LocalDB':>12} {'Match':>8}")
        print("  " + "-"*54)
        
        azure_cursor = self.azure_conn.cursor()
        local_cursor = self.local_conn.cursor()
        
        all_match = True
        for table in self.tables_insert_order:
            try:
                azure_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                azure_count = azure_cursor.fetchone()[0]
            except:
                azure_count = "N/A"
                
            try:
                local_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                local_count = local_cursor.fetchone()[0]
            except:
                local_count = "N/A"
                
            if azure_count == local_count:
                match = "✅"
            else:
                match = "❌"
                all_match = False
                
            azure_str = f"{azure_count:,}" if isinstance(azure_count, int) else azure_count
            local_str = f"{local_count:,}" if isinstance(local_count, int) else local_count
            print(f"  {table:<20} {azure_str:>12} {local_str:>12} {match:>8}")
            
        return all_match
        
    def run_sync(self):
        """Run the full sync process"""
        start_time = datetime.now()
        
        try:
            self.connect()
            
            print("\n" + "="*70)
            print("STARTING AZURE → LOCALDB SYNC")
            print(f"Source: Backup_BerthPlanning @ 20.204.224.123")
            print(f"Target: BerthPlanning @ (localdb)\\MSSQLLocalDB")
            print(f"Started: {start_time}")
            print("="*70)
            
            # Clear local tables first
            self.clear_local_tables()
            
            # Sync each table
            total_inserted = 0
            for table in self.tables_insert_order:
                try:
                    # Use custom sync for tables with schema differences
                    if table == 'PILOTS':
                        count = self.sync_pilots_custom()
                    elif table == 'TUGBOATS':
                        count = self.sync_tugboats_custom()
                    else:
                        count = self.sync_table(table)
                    total_inserted += count
                except Exception as e:
                    print(f"  ❌ Error syncing {table}: {e}")
                    
            # Verify
            all_match = self.verify_sync()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            print("\n" + "="*70)
            print("SYNC COMPLETE")
            print("="*70)
            print(f"  Total rows synced: {total_inserted:,}")
            print(f"  Duration: {duration}")
            print(f"  Status: {'✅ All tables match!' if all_match else '⚠️ Some tables differ'}")
            print("="*70)
            
        except Exception as e:
            print(f"\n❌ SYNC FAILED: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.close()


if __name__ == "__main__":
    syncer = AzureToLocalSync()
    syncer.run_sync()
