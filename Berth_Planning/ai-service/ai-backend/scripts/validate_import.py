"""
Validate Mundra CSV Import to SQL Server
Checks record counts, data quality, relationships, and calculated fields
"""

import pyodbc
from typing import Dict, List, Tuple
from datetime import datetime

class ImportValidator:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.conn = None
        self.validation_results = []

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

    def add_result(self, test_name: str, passed: bool, message: str, details: str = ""):
        """Record validation result"""
        self.validation_results.append({
            'test': test_name,
            'passed': passed,
            'message': message,
            'details': details
        })

    # ==================== VALIDATION TESTS ====================

    def test_record_counts(self):
        """Verify record counts match expected values"""
        print("\n" + "="*80)
        print("TEST 1: Record Counts")
        print("="*80)

        expected_counts = {
            'VESSELS': 8407,
            'BERTHS': 33,
            'VESSEL_SCHEDULE': 8407,
            'WEATHER_DATA': 8760,
            'TIDAL_DATA': 730,
            'AIS_DATA': 411943,
            'RESOURCES': 67
        }

        cursor = self.conn.cursor()
        all_passed = True

        for table, expected in expected_counts.items():
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            actual = cursor.fetchone()[0]

            passed = (actual == expected)
            all_passed = all_passed and passed

            status = "✓" if passed else "❌"
            print(f"  {status} {table:20s}: {actual:>7,} records (expected {expected:>7,})")

            self.add_result(
                f"Record Count - {table}",
                passed,
                f"{actual:,} records" if passed else f"Expected {expected:,}, got {actual:,}"
            )

        return all_passed

    def test_required_columns_not_null(self):
        """Verify required columns have no NULL values"""
        print("\n" + "="*80)
        print("TEST 2: Required Columns (No NULLs)")
        print("="*80)

        required_checks = [
            ('VESSELS', 'VesselId'),
            ('VESSELS', 'VesselName'),
            ('VESSELS', 'VesselType'),
            ('VESSELS', 'IMO'),
            ('BERTHS', 'BerthId'),
            ('BERTHS', 'BerthName'),
            ('BERTHS', 'BerthType'),
            ('VESSEL_SCHEDULE', 'ScheduleId'),
            ('VESSEL_SCHEDULE', 'VesselId'),
            ('VESSEL_SCHEDULE', 'BerthId'),
            ('VESSEL_SCHEDULE', 'ETA'),
            ('WEATHER_DATA', 'RecordedAt'),
            ('WEATHER_DATA', 'WindSpeed'),
            ('TIDAL_DATA', 'TideDateTime'),
            ('TIDAL_DATA', 'TideHeight'),
            ('AIS_DATA', 'VesselId'),
            ('AIS_DATA', 'RecordedAt'),
            ('RESOURCES', 'ResourceId'),
            ('RESOURCES', 'ResourceType')
        ]

        cursor = self.conn.cursor()
        all_passed = True

        for table, column in required_checks:
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")
            null_count = cursor.fetchone()[0]

            passed = (null_count == 0)
            all_passed = all_passed and passed

            status = "✓" if passed else "❌"
            print(f"  {status} {table}.{column:25s}: {null_count} NULLs")

            if not passed:
                self.add_result(
                    f"NULL Check - {table}.{column}",
                    False,
                    f"{null_count} NULL values found in required column"
                )

        if all_passed:
            print("\n✓ All required columns are populated")
            self.add_result("Required Columns Check", True, "All required columns populated")

        return all_passed

    def test_foreign_key_relationships(self):
        """Verify foreign key relationships are intact"""
        print("\n" + "="*80)
        print("TEST 3: Foreign Key Relationships")
        print("="*80)

        cursor = self.conn.cursor()
        all_passed = True

        # VESSEL_SCHEDULE -> VESSELS
        cursor.execute("""
            SELECT COUNT(*)
            FROM VESSEL_SCHEDULE vs
            LEFT JOIN VESSELS v ON vs.VesselId = v.VesselId
            WHERE v.VesselId IS NULL
        """)
        orphaned_vessel_schedules = cursor.fetchone()[0]
        passed = (orphaned_vessel_schedules == 0)
        all_passed = all_passed and passed
        status = "✓" if passed else "❌"
        print(f"  {status} VESSEL_SCHEDULE -> VESSELS: {orphaned_vessel_schedules} orphaned records")
        self.add_result("FK: VESSEL_SCHEDULE->VESSELS", passed,
                       f"{orphaned_vessel_schedules} orphaned" if not passed else "Valid")

        # VESSEL_SCHEDULE -> BERTHS
        cursor.execute("""
            SELECT COUNT(*)
            FROM VESSEL_SCHEDULE vs
            LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
            WHERE b.BerthId IS NULL
        """)
        orphaned_berth_schedules = cursor.fetchone()[0]
        passed = (orphaned_berth_schedules == 0)
        all_passed = all_passed and passed
        status = "✓" if passed else "❌"
        print(f"  {status} VESSEL_SCHEDULE -> BERTHS: {orphaned_berth_schedules} orphaned records")
        self.add_result("FK: VESSEL_SCHEDULE->BERTHS", passed,
                       f"{orphaned_berth_schedules} orphaned" if not passed else "Valid")

        # AIS_DATA -> VESSELS
        cursor.execute("""
            SELECT COUNT(*)
            FROM AIS_DATA ais
            LEFT JOIN VESSELS v ON ais.VesselId = v.VesselId
            WHERE v.VesselId IS NULL
        """)
        orphaned_ais = cursor.fetchone()[0]
        passed = (orphaned_ais == 0)
        all_passed = all_passed and passed
        status = "✓" if passed else "❌"
        print(f"  {status} AIS_DATA -> VESSELS: {orphaned_ais} orphaned records")
        self.add_result("FK: AIS_DATA->VESSELS", passed,
                       f"{orphaned_ais} orphaned" if not passed else "Valid")

        return all_passed

    def test_calculated_fields(self):
        """Verify calculated fields are realistic"""
        print("\n" + "="*80)
        print("TEST 4: Calculated Fields Validation")
        print("="*80)

        cursor = self.conn.cursor()
        all_passed = True

        # GT (Gross Tonnage) should be > 0 and < 500000
        cursor.execute("SELECT MIN(GT), MAX(GT), AVG(GT) FROM VESSELS WHERE GT IS NOT NULL")
        min_gt, max_gt, avg_gt = cursor.fetchone()
        passed = (min_gt >= 1000 and max_gt <= 500000)
        all_passed = all_passed and passed
        status = "✓" if passed else "❌"
        print(f"  {status} GT (Gross Tonnage): min={min_gt:,.0f}, max={max_gt:,.0f}, avg={avg_gt:,.0f}")
        self.add_result("Calculated Field: GT", passed,
                       f"Range: {min_gt:,.0f} - {max_gt:,.0f}" if passed else "Out of range")

        # DWT should be roughly 1.5-2.5x GT
        cursor.execute("""
            SELECT
                MIN(CAST(DWT AS FLOAT) / NULLIF(GT, 0)) as min_ratio,
                MAX(CAST(DWT AS FLOAT) / NULLIF(GT, 0)) as max_ratio,
                AVG(CAST(DWT AS FLOAT) / NULLIF(GT, 0)) as avg_ratio
            FROM VESSELS
            WHERE GT > 0 AND DWT > 0
        """)
        min_ratio, max_ratio, avg_ratio = cursor.fetchone()
        passed = (1.0 <= avg_ratio <= 3.0)
        all_passed = all_passed and passed
        status = "✓" if passed else "❌"
        print(f"  {status} DWT/GT Ratio: min={min_ratio:.2f}, max={max_ratio:.2f}, avg={avg_ratio:.2f}")
        self.add_result("Calculated Field: DWT/GT Ratio", passed,
                       f"Avg ratio: {avg_ratio:.2f}" if passed else "Unrealistic ratio")

        # Wind speed conversion (should be in knots, reasonable range 0-100)
        cursor.execute("SELECT MIN(WindSpeed), MAX(WindSpeed), AVG(WindSpeed) FROM WEATHER_DATA")
        min_wind, max_wind, avg_wind = cursor.fetchone()
        passed = (0 <= min_wind <= 100 and 0 <= max_wind <= 100)
        all_passed = all_passed and passed
        status = "✓" if passed else "❌"
        print(f"  {status} WindSpeed (knots): min={min_wind:.2f}, max={max_wind:.2f}, avg={avg_wind:.2f}")
        self.add_result("Converted Field: WindSpeed", passed,
                       f"Range: {min_wind:.2f} - {max_wind:.2f} knots" if passed else "Out of range")

        # Wave height (should be estimated, reasonable range 0-10m)
        cursor.execute("SELECT MIN(WaveHeight), MAX(WaveHeight), AVG(WaveHeight) FROM WEATHER_DATA WHERE WaveHeight IS NOT NULL")
        result = cursor.fetchone()
        if result and result[0] is not None:
            min_wave, max_wave, avg_wave = result
            passed = (0 <= min_wave <= 10 and 0 <= max_wave <= 10)
            all_passed = all_passed and passed
            status = "✓" if passed else "❌"
            print(f"  {status} WaveHeight (m): min={min_wave:.2f}, max={max_wave:.2f}, avg={avg_wave:.2f}")
            self.add_result("Calculated Field: WaveHeight", passed,
                           f"Range: {min_wave:.2f} - {max_wave:.2f} m" if passed else "Out of range")

        return all_passed

    def test_derived_fields(self):
        """Verify derived fields are properly set"""
        print("\n" + "="*80)
        print("TEST 5: Derived Fields")
        print("="*80)

        cursor = self.conn.cursor()
        all_passed = True

        # VesselType distribution
        cursor.execute("""
            SELECT VesselType, COUNT(*) as count
            FROM VESSELS
            GROUP BY VesselType
            ORDER BY count DESC
        """)
        vessel_types = cursor.fetchall()
        print("\n  VesselType Distribution:")
        for vtype, count in vessel_types:
            print(f"    {vtype:25s}: {count:>5,} vessels")

        # Check if we have at least 3 different vessel types
        passed = (len(vessel_types) >= 3)
        all_passed = all_passed and passed
        status = "✓" if passed else "❌"
        print(f"\n  {status} VesselType Diversity: {len(vessel_types)} types")
        self.add_result("Derived Field: VesselType", passed,
                       f"{len(vessel_types)} unique types" if passed else "Too few types")

        # BerthType distribution
        cursor.execute("""
            SELECT BerthType, COUNT(*) as count
            FROM BERTHS
            GROUP BY BerthType
            ORDER BY count DESC
        """)
        berth_types = cursor.fetchall()
        print("\n  BerthType Distribution:")
        for btype, count in berth_types:
            print(f"    {btype:25s}: {count:>5,} berths")

        # Priority distribution in schedules
        cursor.execute("""
            SELECT Priority, COUNT(*) as count
            FROM VESSEL_SCHEDULE
            GROUP BY Priority
            ORDER BY Priority
        """)
        priorities = cursor.fetchall()
        print("\n  Priority Distribution:")
        priority_names = {1: 'High', 2: 'Medium', 3: 'Low'}
        for priority, count in priorities:
            print(f"    {priority_names.get(priority, 'Unknown'):10s}: {count:>6,} schedules")

        return all_passed

    def test_data_ranges(self):
        """Verify data ranges are realistic"""
        print("\n" + "="*80)
        print("TEST 6: Data Range Validation")
        print("="*80)

        cursor = self.conn.cursor()
        all_passed = True

        # Vessel dimensions
        checks = [
            ('VESSELS', 'LOA', 50, 500, 'meters'),
            ('VESSELS', 'Beam', 10, 70, 'meters'),
            ('VESSELS', 'Draft', 3, 20, 'meters'),
            ('BERTHS', 'Length', 100, 500, 'meters'),
            ('BERTHS', 'MaxDraft', 8, 25, 'meters'),
            ('TIDAL_DATA', 'TideHeight', 0, 10, 'meters'),
            ('WEATHER_DATA', 'Visibility', 0, 20000, 'meters'),
            ('AIS_DATA', 'Speed', 0, 30, 'knots'),
            ('AIS_DATA', 'Latitude', 20, 26, 'degrees'),
            ('AIS_DATA', 'Longitude', 67, 73, 'degrees')
        ]

        for table, column, min_val, max_val, unit in checks:
            cursor.execute(f"""
                SELECT MIN({column}), MAX({column}), AVG({column})
                FROM {table}
                WHERE {column} IS NOT NULL
            """)
            result = cursor.fetchone()
            if result and result[0] is not None:
                actual_min, actual_max, actual_avg = result
                passed = (min_val <= actual_min <= actual_max <= max_val)
                all_passed = all_passed and passed
                status = "✓" if passed else "❌"
                print(f"  {status} {table}.{column:15s}: {actual_min:>8.2f} - {actual_max:>8.2f} {unit} (avg: {actual_avg:.2f})")

                if not passed:
                    self.add_result(
                        f"Range: {table}.{column}",
                        False,
                        f"Out of expected range {min_val}-{max_val}"
                    )

        return all_passed

    def test_datetime_ranges(self):
        """Verify datetime columns are in reasonable range"""
        print("\n" + "="*80)
        print("TEST 7: DateTime Range Validation")
        print("="*80)

        cursor = self.conn.cursor()
        all_passed = True

        datetime_checks = [
            ('VESSEL_SCHEDULE', 'ETA'),
            ('VESSEL_SCHEDULE', 'ATA'),
            ('WEATHER_DATA', 'RecordedAt'),
            ('TIDAL_DATA', 'TideDateTime'),
            ('AIS_DATA', 'RecordedAt')
        ]

        for table, column in datetime_checks:
            cursor.execute(f"SELECT MIN({column}), MAX({column}) FROM {table}")
            min_date, max_date = cursor.fetchone()

            if min_date and max_date:
                date_range_days = (max_date - min_date).days
                passed = (date_range_days >= 30)  # At least 30 days of data
                all_passed = all_passed and passed
                status = "✓" if passed else "❌"
                print(f"  {status} {table}.{column:20s}: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')} ({date_range_days} days)")

                self.add_result(
                    f"DateTime Range: {table}.{column}",
                    passed,
                    f"{date_range_days} days of data" if passed else "Insufficient date range"
                )

        return all_passed

    # ==================== MAIN VALIDATION ====================

    def run_all_validations(self):
        """Run complete validation suite"""
        print("\n" + "="*80)
        print("MUNDRA IMPORT VALIDATION SUITE")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        self.connect()

        tests = [
            ("Record Counts", self.test_record_counts),
            ("Required Columns", self.test_required_columns_not_null),
            ("Foreign Keys", self.test_foreign_key_relationships),
            ("Calculated Fields", self.test_calculated_fields),
            ("Derived Fields", self.test_derived_fields),
            ("Data Ranges", self.test_data_ranges),
            ("DateTime Ranges", self.test_datetime_ranges)
        ]

        test_results = []
        for test_name, test_func in tests:
            try:
                passed = test_func()
                test_results.append((test_name, passed))
            except Exception as e:
                print(f"\n❌ {test_name} FAILED with exception: {e}")
                test_results.append((test_name, False))
                self.add_result(test_name, False, f"Exception: {e}")

        # Summary
        print("\n\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)

        total_tests = len(test_results)
        passed_tests = sum(1 for _, passed in test_results if passed)
        failed_tests = total_tests - passed_tests

        for test_name, passed in test_results:
            status = "✓ PASS" if passed else "❌ FAIL"
            print(f"  {status}: {test_name}")

        print("\n" + "="*80)
        if failed_tests == 0:
            print("✅ ALL VALIDATIONS PASSED")
            print("="*80)
            print(f"\nDataset is ready for:")
            print("  ✓ ChromaDB knowledge base loading")
            print("  ✓ Neo4j graph database population")
            print("  ✓ ETA Predictor Agent testing")
            print("  ✓ Multi-agent orchestration")
            print("  ✓ Hackathon demo")
        else:
            print(f"⚠️  {failed_tests}/{total_tests} VALIDATIONS FAILED")
            print("="*80)
            print("\nPlease review errors above and re-run import if needed.")

        print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        self.close()

        return failed_tests == 0


if __name__ == "__main__":
    # Configuration
    CONNECTION_STRING = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost;"
        "DATABASE=BerthPlanningDB;"
        "UID=your_username;"
        "PWD=your_password;"
    )

    # Run validation
    validator = ImportValidator(CONNECTION_STRING)
    success = validator.run_all_validations()

    exit(0 if success else 1)
