# Mundra CSV to SQL Server Column Mapping Reference

## Overview
This document provides the complete mapping between Mundra CSV files (snake_case) and SQL Server BerthPlanningDB schema (PascalCase), including all transformations, calculations, and data enrichment.

---

## 1. VESSELS Mapping

### Direct Column Mappings
| CSV Column | SQL Server Column | Transformation |
|------------|------------------|----------------|
| `vessel_id` | `VesselId` | Direct mapping |
| `vessel_name` | `VesselName` | Direct mapping |
| `loa_m` | `LOA` | Direct mapping (meters) |
| `beam_m` | `Beam` | Direct mapping (meters) |
| `draft_m` | `Draft` | Direct mapping (meters) |

### Derived/Calculated Columns
| SQL Server Column | Source | Calculation/Derivation |
|------------------|--------|------------------------|
| `VesselType` | `cargo_type` (from VESSEL_SCHEDULE) | Mapped: container→Container, bulk→Bulk Carrier, crude_oil→Tanker, etc. Size-based refinement for large containers (LOA>350m = Ultra Large Container) |
| `IMO` | `imo_mmsi` | Regex extraction: `IMO(\d+)` from "IMO9225772\|MMSI761415646" format |
| `GT` (Gross Tonnage) | `loa_m`, `beam_m`, `draft_m` | **Formula**: `GT = (LOA × Beam × Draft × 0.70) × 0.30`<br>Block coefficient = 0.7, K-factor = 0.3<br>Minimum: 1000 GT |
| `DWT` (Deadweight Tonnage) | `GT` | **Formula**: `DWT = GT × 1.7`<br>Typical ratio for cargo vessels |
| `Flag` | `line_operator` | Using line operator as proxy for flag state |
| `IsActive` | - | Default: `1` (all vessels active) |
| `PrimaryCargo` | `cargo_type` (from VESSEL_SCHEDULE) | Direct mapping from schedule |
| `DangerousGoods` | - | Default: `0` (false) |

### Extra CSV Columns (Not imported)
- `line_operator` (used for Flag derivation)

---

## 2. BERTHS Mapping

### Direct Column Mappings
| CSV Column | SQL Server Column | Transformation |
|------------|------------------|----------------|
| `berth_id` | `BerthId` | Direct mapping |
| `berth_id` | `BerthName` | Same as BerthId (no separate name in CSV) |
| `max_loa_m` | `Length` | Direct mapping (max LOA accepted) |
| `max_draft_m` | `MaxDraft` | Direct mapping |
| `max_beam_m` | `MaxBeam` | Direct mapping |
| `max_draft_m` | `BerthDepth` | Same as MaxDraft |
| `cargo_allowed` | `BerthSpecialization` | Direct mapping |

### Derived/Calculated Columns
| SQL Server Column | Source | Calculation/Derivation |
|------------------|--------|------------------------|
| `BerthType` | `cargo_allowed`, `equipment` | Mapped: container→Container, bulk→Bulk, crude/oil→Tanker, roro→RoRo, else→General |
| `NumberOfCranes` | `equipment` | **Extraction**: Regex `(\d+)\s*crane` from equipment string. If "STS" or "crane" mentioned but no number: default = 2 |
| `IsActive` | - | Default: `1` (all berths active) |
| `Exposure` | - | Default: `'Sheltered'` (harbor assumption) |

### Extra CSV Columns (Not imported)
- `terminal_code` (reference only)
- `max_displacement_t` (not in SQL schema)
- `priority_rules` (could be used for knowledge base)
- `equipment` (used for NumberOfCranes derivation)

---

## 3. VESSEL_SCHEDULE Mapping

### Direct Column Mappings
| CSV Column | SQL Server Column | Transformation |
|------------|------------------|----------------|
| `schedule_id` | `ScheduleId` | Direct mapping |
| `vessel_id` | `VesselId` | Direct mapping |
| `berth_id` | `BerthId` | Direct mapping |
| `eta_ts` | `ETA` | Datetime parsing |
| `etc_ts` | `ETD` | Datetime parsing (ETC = Estimated Time of Completion) |
| `ata_ts` | `ATA` | Datetime parsing |
| `atb_ts` | `ATB` | Datetime parsing |
| `atd_ts` | `ATD` | Datetime parsing |
| `waiting_time_hours` | `WaitingTime` | Direct mapping (hours) |
| `service_time_hours` | `DwellTime` | Direct mapping (hours) |
| `cargo_type` | `CargoType` | Direct mapping |
| `quantity` | `CargoQuantity` | Direct mapping (string with units: "5851 TEU", "39310 tonnes") |

### Derived/Calculated Columns
| SQL Server Column | Source | Calculation/Derivation |
|------------------|--------|------------------------|
| `Status` | `status` | Mapped: completed→Completed, in_progress→In Progress, scheduled→Scheduled, cancelled→Cancelled |
| `Priority` | `cargo_type` | **Logic**: Container or Crude Oil → 1 (High), else → 2 (Medium) |

### Extra CSV Columns (Not imported to VESSEL_SCHEDULE)
- `vessel_name` (redundant - in VESSELS table)
- `imo_mmsi` (redundant - in VESSELS table)
- `line_operator` (redundant - in VESSELS table)
- `terminal_code` (reference only)
- `anchorage_ts` (35% nulls - optional field, could add if needed)
- `eta_error_hours` (useful for analysis - could add as PredictedETA validation)

**Recommendation**: Add `eta_error_hours` to knowledge base documents for ETA prediction accuracy analysis.

---

## 4. WEATHER_DATA Mapping

### Direct Column Mappings with Unit Conversions
| CSV Column | SQL Server Column | Transformation |
|------------|------------------|----------------|
| `ts_hour` | `RecordedAt` | Datetime parsing |
| `wind_speed_mps` | `WindSpeed` | **Unit conversion**: `WindSpeed (knots) = wind_speed_mps × 1.94384`<br>(1 m/s = 1.94384 knots) |
| `visibility_km` | `Visibility` | **Unit conversion**: `Visibility (meters) = visibility_km × 1000` |

### Derived/Calculated Columns
| SQL Server Column | Source | Calculation/Derivation |
|------------------|--------|------------------------|
| `WaveHeight` | `wind_speed_mps`, `wind_gust_mps` | **Empirical Formula**:<br>`avg_wind = (wind_speed_mps + wind_gust_mps) / 2`<br>`WaveHeight (m) = 0.21 × (avg_wind^1.5) / 10`<br>(Dampened for harbor conditions) |
| `WeatherCondition` | `storm_flag`, `rain_mm`, `visibility_km` | **Logic**:<br>- storm_flag=1 → "Storm"<br>- rain_mm > 10 → "Heavy Rain"<br>- rain_mm > 0 → "Rain"<br>- visibility_km < 1 → "Fog"<br>- else → "Clear" |
| `WindDirection` | - | NULL (not in CSV) |
| `Temperature` | - | NULL (not in CSV) |
| `Pressure` | - | NULL (not in CSV) |

### Extra CSV Columns (Used for derivations)
- `wind_gust_mps` (used in WaveHeight calculation)
- `rain_mm` (used in WeatherCondition derivation)
- `storm_flag` (used in WeatherCondition derivation)

**Note**: Weather data is complete with 8,760 hourly records (365 days × 24 hours) covering full year.

---

## 5. TIDAL_DATA Mapping

### Direct Column Mappings
| CSV Column | SQL Server Column | Transformation |
|------------|------------------|----------------|
| `ts` | `TideDateTime` | Datetime parsing |
| `tide_height_m` | `TideHeight` | Direct mapping (meters) |
| `tide_phase` | `TideType` | Direct mapping (HIGH/LOW) |

### Extra CSV Columns (Not imported)
- `cycle_id` (reference only, auto-generated in SQL)

**Note**: Tidal data has 730 records (365 days × 2 tides/day = 2 tides per day for full year).

---

## 6. AIS_DATA Mapping

### Direct Column Mappings
| CSV Column | SQL Server Column | Transformation |
|------------|------------------|----------------|
| `vessel_id` | `VesselId` | Direct mapping |
| `ts` | `RecordedAt` | Datetime parsing |
| `lat` | `Latitude` | Direct mapping (decimal degrees) |
| `lon` | `Longitude` | Direct mapping (decimal degrees) |
| `sog_kn` | `Speed` | Direct mapping (knots) |
| `cog_deg` | `Heading` | Direct mapping (COG used as Heading proxy) |
| `cog_deg` | `COG` | Direct mapping (degrees) |
| `sog_kn` | `SOG` | Direct mapping (knots) |
| `nav_status` | `Status` | Direct mapping (UNDERWAY/MOORED) |

### Extra CSV Columns (Not imported)
- `schedule_id` (reference - links AIS track to specific voyage)

**Note**: AIS_DATA is the largest file with 411,943 records (~49 tracking points per vessel). Import uses **batch processing** (10,000 records per batch) for performance.

---

## 7. RESOURCES Mapping

### Direct Column Mappings
| CSV Column | SQL Server Column | Transformation |
|------------|------------------|----------------|
| `resource_id` | `ResourceId` | Direct mapping |
| `capacity_per_hr` | `Capacity` | Direct mapping |
| `berth_id` | `BerthId` | Direct mapping (NULL for shared resources) |

### Derived/Calculated Columns
| SQL Server Column | Source | Calculation/Derivation |
|------------------|--------|------------------------|
| `ResourceType` | `resource_type` | **Mapped**:<br>- sts_crane → Crane<br>- rtg → Crane<br>- yard_tractor → Yard Equipment<br>- pilot → Pilot<br>- tugboat → Tugboat<br>- mooring_gang → Labor<br>- customs/security → Administrative |
| `ResourceName` | `resource_type`, `terminal_code`, `berth_id` | **Logic**: If berth_id exists: `"{type} - {berth_id}"`<br>Else: `"{type} - {terminal_code}"` |
| `IsAvailable` | `availability_pct` | **Logic**: `1` if availability_pct > 0.80, else `0` |
| `ShiftPattern` | - | Default: `'24/7'` |

### Extra CSV Columns (Used for derivations)
- `terminal_code` (used in ResourceName generation)
- `count` (number of resources - informational)
- `availability_pct` (used in IsAvailable calculation)

---

## Data Quality Summary

### Records per Table
| Table | CSV Records | Notes |
|-------|-------------|-------|
| VESSELS | 8,407 | 2% nulls in dimensions (LOA/Beam/Draft) |
| BERTHS | 33 | Complete, no nulls |
| VESSEL_SCHEDULE | 8,407 | 35% nulls in anchorage_ts (optional) |
| WEATHER_DATA | 8,760 | Full year hourly data, no nulls |
| TIDAL_DATA | 730 | Full year 2 tides/day, no nulls |
| AIS_DATA | 411,943 | Dense tracking, no nulls |
| RESOURCES | 67 | 3% nulls in berth_id (shared resources) |
| **TOTAL** | **438,347** | **Excellent quality** |

### Key Improvements in Import Script
1. ✅ **Column name normalization**: snake_case → PascalCase
2. ✅ **Unit conversions**: m/s → knots, km → meters
3. ✅ **Derived fields**: VesselType, GT, DWT, IMO extraction
4. ✅ **Data enrichment**: WeatherCondition, Priority, ResourceName
5. ✅ **Calculated fields**: WaveHeight from wind speed
6. ✅ **Batch processing**: AIS_DATA chunked for performance
7. ✅ **Error handling**: Graceful failures with error reporting

---

## Missing Data (Not in CSV)

### VESSELS
- `AirDraft` (not critical for hackathon)
- Accurate `Flag` country codes (using line_operator as proxy)

### BERTHS
- `HasRoRoRamp` (could derive from cargo_allowed if "roro" present)

### VESSEL_SCHEDULE
- `PredictedETA` (will be generated by ETA Predictor Agent)

### WEATHER_DATA
- `WindDirection` (degrees)
- `Temperature` (Celsius)
- `Pressure` (hPa)

### RESOURCES
- `BollardPull` (for tugboats - could calculate from capacity)
- `Certifications` (optional metadata)

**Recommendation**: These missing fields are not critical for the hackathon demo. The derived and calculated fields provide excellent coverage for all AI agent requirements.

---

## Usage Instructions

### Step 1: Configure Connection
Edit `import_mundra_to_sql.py` line 529:
```python
CONNECTION_STRING = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=your_server;"
    "DATABASE=BerthPlanningDB;"
    "UID=your_username;"
    "PWD=your_password;"
)
```

### Step 2: Verify CSV Path
Ensure CSV files are in: `../../documents/Data/Mundra/`

### Step 3: Run Import
```bash
cd /Users/ankurrai/IdeaProjects/Berth_Planning/ai-backend/scripts
python3 import_mundra_to_sql.py
```

### Step 4: Verify Import
Check SQL Server:
```sql
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
```

Expected results:
- VESSELS: 8,407
- BERTHS: 33
- VESSEL_SCHEDULE: 8,407
- WEATHER_DATA: 8,760
- TIDAL_DATA: 730
- AIS_DATA: 411,943
- RESOURCES: 67

---

## Knowledge Base Enhancement Opportunities

The CSV files contain rich metadata that can enhance the knowledge base:

### From BERTHS.csv
- `priority_rules`: "Container windowing; minimize rehandles; prefer same terminal continuity"
- `equipment`: Detailed equipment specifications per berth

### From VESSEL_SCHEDULE.csv
- `eta_error_hours`: Historical ETA prediction accuracy data
- `line_operator` patterns: Operator-specific preferences and patterns

### From RESOURCES.csv
- `availability_pct`: Resource utilization patterns
- `capacity_per_hr`: Productivity metrics per resource type

**Action**: Create additional knowledge base documents from this metadata (estimated 2 hours).
