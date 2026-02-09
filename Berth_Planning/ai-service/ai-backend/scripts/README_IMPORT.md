# Mundra CSV Data Import Guide

## Quick Start

### Prerequisites
```bash
# Install required Python packages
pip install pandas pyodbc

# Verify SQL Server ODBC Driver installed
# macOS: brew install msodbcsql17
# Linux: See Microsoft docs
# Windows: Usually pre-installed
```

### Configuration

1. **Edit connection string** in `import_mundra_to_sql.py` (line 529):
```python
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"              # Change to your server
    "DATABASE=BerthPlanningDB;"
    "UID=your_username;"             # Change to your username
    "PWD=your_password;"             # Change to your password
)
```

2. **Verify CSV path** (line 537):
```python
CSV_BASE_PATH = "../../documents/Data/Mundra"  # Adjust if different
```

### Run Import

```bash
cd /Users/ankurrai/IdeaProjects/Berth_Planning/ai-backend/scripts
python3 import_mundra_to_sql.py
```

**Expected Duration**: 5-10 minutes (AIS_DATA is large with 411K records)

### Output Example

```
================================================================================
MUNDRA CSV TO SQL SERVER IMPORT
================================================================================
CSV Path: ../../documents/Data/Mundra
Started: 2025-02-05 10:30:00

✓ Connected to SQL Server

================================================================================
IMPORTING VESSELS
================================================================================
✓ Loaded 8407 vessels from CSV
  Progress: 1000/8407 vessels inserted...
  Progress: 2000/8407 vessels inserted...
  ...
✓ Imported 8407 vessels successfully

[Similar output for BERTHS, VESSEL_SCHEDULE, WEATHER_DATA, TIDAL_DATA, AIS_DATA, RESOURCES]

================================================================================
✅ IMPORT COMPLETED SUCCESSFULLY
================================================================================
Finished: 2025-02-05 10:38:42
```

---

## What Gets Imported

### 7 Tables, 438,347 Total Records

| Table | Records | Key Features |
|-------|---------|-------------|
| **VESSELS** | 8,407 | Derived: VesselType, GT, DWT, IMO extraction |
| **BERTHS** | 33 | Derived: BerthType, NumberOfCranes |
| **VESSEL_SCHEDULE** | 8,407 | Derived: Priority, Status mapping |
| **WEATHER_DATA** | 8,760 | Converted: m/s→knots, km→meters, calculated WaveHeight |
| **TIDAL_DATA** | 730 | Direct mapping |
| **AIS_DATA** | 411,943 | Batch processed (10K chunks) |
| **RESOURCES** | 67 | Derived: ResourceType, ResourceName, IsAvailable |

---

## Data Transformations

### Unit Conversions
- **Wind Speed**: m/s → knots (× 1.94384)
- **Visibility**: km → meters (× 1000)

### Calculated Fields
- **GT (Gross Tonnage)**: `(LOA × Beam × Draft × 0.70) × 0.30`
- **DWT (Deadweight)**: `GT × 1.7`
- **Wave Height**: `0.21 × (avg_wind^1.5) / 10`

### Derived Fields
- **VesselType**: From cargo_type (container, bulk, tanker, etc.)
- **IMO**: Extracted from "IMO9225772|MMSI761415646" format
- **Priority**: Container/Crude Oil = High(1), Others = Medium(2)
- **WeatherCondition**: Based on storm_flag, rain_mm, visibility
- **NumberOfCranes**: Extracted from equipment description

See [CSV_COLUMN_MAPPING.md](CSV_COLUMN_MAPPING.md) for complete mapping details.

---

## Post-Import Validation

### Run Validation Script
```bash
python3 validate_import.py
```

This will check:
- ✅ Record counts match expected values
- ✅ No NULL values in required columns
- ✅ Foreign key relationships intact
- ✅ Data ranges are realistic
- ✅ Calculated fields are correct

### Manual SQL Verification
```sql
-- Quick record count check
SELECT
    'VESSELS' AS TableName, COUNT(*) AS Records FROM VESSELS
UNION ALL
SELECT 'BERTHS', COUNT(*) FROM BERTHS
UNION ALL
SELECT 'VESSEL_SCHEDULE', COUNT(*) FROM VESSEL_SCHEDULE
UNION ALL
SELECT 'WEATHER_DATA', COUNT(*) FROM WEATHER_DATA
UNION ALL
SELECT 'TIDAL_DATA', COUNT(*) FROM TIDAL_DATA
UNION ALL
SELECT 'AIS_DATA', COUNT(*) FROM AIS_DATA
UNION ALL
SELECT 'RESOURCES', COUNT(*) FROM RESOURCES;

-- Expected:
-- VESSELS: 8407
-- BERTHS: 33
-- VESSEL_SCHEDULE: 8407
-- WEATHER_DATA: 8760
-- TIDAL_DATA: 730
-- AIS_DATA: 411943
-- RESOURCES: 67
```

```sql
-- Verify foreign key relationships
SELECT 'Orphaned Schedules' AS Issue, COUNT(*) AS Count
FROM VESSEL_SCHEDULE vs
LEFT JOIN VESSELS v ON vs.VesselId = v.VesselId
WHERE v.VesselId IS NULL

UNION ALL

SELECT 'Orphaned Schedules (Berth)', COUNT(*)
FROM VESSEL_SCHEDULE vs
LEFT JOIN BERTHS b ON vs.BerthId = b.BerthId
WHERE b.BerthId IS NULL;

-- Expected: Both should be 0
```

```sql
-- Sample data quality check
SELECT TOP 5
    v.VesselId,
    v.VesselName,
    v.VesselType,
    v.LOA,
    v.GT,
    v.IMO
FROM VESSELS v
ORDER BY v.GT DESC;

-- Should see Ultra Large Container vessels with GT > 50000
```

---

## Troubleshooting

### Error: "pyodbc.Error: ('01000', ...)"
**Solution**: ODBC Driver not installed or wrong driver name
```bash
# macOS
brew install msodbcsql17

# Check available drivers
odbcinst -q -d
```

### Error: "Login failed for user"
**Solution**: Wrong credentials in CONNECTION_STRING
- Verify username/password
- Check SQL Server allows mixed authentication
- Ensure user has INSERT permissions on BerthPlanningDB

### Error: "Cannot insert duplicate key"
**Solution**: Tables already have data
```sql
-- Clear existing data first (CAREFUL!)
DELETE FROM RESOURCE_ALLOCATION;
DELETE FROM AIS_DATA;
DELETE FROM TIDAL_DATA;
DELETE FROM WEATHER_DATA;
DELETE FROM VESSEL_SCHEDULE;
DELETE FROM RESOURCES;
DELETE FROM BERTHS;
DELETE FROM VESSELS;
```

Or modify script to skip duplicates (add `IF NOT EXISTS` checks)

### Error: "Memory error" during AIS_DATA import
**Solution**: Reduce chunk size in `import_ais_data()` method
```python
chunk_size = 5000  # Instead of 10000
```

### Warning: "165 vessels have NULL dimensions"
**Expected**: CSV has 2% NULL values in loa_m, beam_m, draft_m
- GT will be calculated as 1000 (minimum) for these vessels
- Still functional for demo purposes

---

## Performance Tips

### Speed Up Import
1. **Disable foreign key checks temporarily** (if safe):
```sql
ALTER TABLE VESSEL_SCHEDULE NOCHECK CONSTRAINT ALL;
ALTER TABLE RESOURCES NOCHECK CONSTRAINT ALL;
-- Import data
ALTER TABLE VESSEL_SCHEDULE CHECK CONSTRAINT ALL;
ALTER TABLE RESOURCES CHECK CONSTRAINT ALL;
```

2. **Increase batch size** for AIS_DATA:
```python
chunk_size = 20000  # If you have enough RAM
```

3. **Use bulk insert** instead of row-by-row:
```python
# Future enhancement: Use cursor.fast_executemany = True
```

### Monitor Progress
The script prints progress every 1000 records for large tables:
```
Progress: 1000/8407 vessels inserted...
Progress: 2000/8407 vessels inserted...
```

---

## Next Steps After Import

### 1. Load Data into ChromaDB
```bash
cd /Users/ankurrai/IdeaProjects/Berth_Planning/ai-backend/rag
python3 document_loader.py
```

### 2. Load Data into Neo4j
```bash
cd /Users/ankurrai/IdeaProjects/Berth_Planning/ai-backend/graph
python3 data_loader.py
```

### 3. Test ETA Predictor Agent
```bash
cd /Users/ankurrai/IdeaProjects/Berth_Planning/ai-backend
python3 -m agents.eta_predictor
```

### 4. Verify in .NET API
```bash
cd /Users/ankurrai/IdeaProjects/Berth_Planning/src/BerthPlanning.API
dotnet run

# Test endpoint
curl http://localhost:5000/api/vessels
```

---

## Files in This Directory

| File | Purpose |
|------|---------|
| `import_mundra_to_sql.py` | **Main import script** (run this) |
| `CSV_COLUMN_MAPPING.md` | Complete column mapping reference |
| `analyze_mundra_csv_files.py` | CSV analysis and validation tool |
| `validate_import.py` | Post-import validation script |
| `README_IMPORT.md` | This file |

---

## Support

**Issues?** Check:
1. Connection string is correct
2. SQL Server is running and accessible
3. CSV files exist in correct path
4. Python packages are installed
5. ODBC driver is installed

**Still stuck?** Review error messages - most are self-explanatory (e.g., "Column 'VesselId' does not allow NULL" → check CSV has vessel_id values)
