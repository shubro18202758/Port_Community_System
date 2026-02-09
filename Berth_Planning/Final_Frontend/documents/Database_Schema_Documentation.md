# BERTH PLANNING & ALLOCATION OPTIMIZATION SYSTEM
## Complete Database Schema Documentation
### Version: 4.0 | Database: BerthPlanning | Engine: MS-SQL Server

---

## SCHEMA SUMMARY

| Property | Value |
|----------|-------|
| **Database** | BerthPlanning |
| **Schema** | dbo |
| **Total Tables** | 23 |
| **Total Foreign Keys** | 18 |
| **Total Indexes** | 48 |
| **Total CHECK Constraints** | 25 |
| **Total UNIQUE Constraints** | 6 |

---

## TABLE OF CONTENTS

| # | Table | Category | Tier |
|---|-------|----------|------|
| 1 | [PORTS](#1-ports) | Port Hierarchy | 1 |
| 2 | [TERMINALS](#2-terminals) | Port Hierarchy | 2 |
| 3 | [VESSELS](#3-vessels) | Core | 1 |
| 4 | [BERTHS](#4-berths) | Port Hierarchy | 3 |
| 5 | [VESSEL_SCHEDULE](#5-vessel_schedule) | Operational | 4 |
| 6 | [RESOURCES](#6-resources) | Operational | 1 |
| 7 | [RESOURCE_ALLOCATION](#7-resource_allocation) | Operational | 5 |
| 8 | [WEATHER_DATA](#8-weather_data) | External Data | 2 |
| 9 | [TIDAL_DATA](#9-tidal_data) | External Data | 1 |
| 10 | [AIS_DATA](#10-ais_data) | External Data | 2 |
| 11 | [CONFLICTS](#11-conflicts) | AI/ML | 5 |
| 12 | [OPTIMIZATION_RUNS](#12-optimization_runs) | AI/ML | 1 |
| 13 | [KNOWLEDGE_BASE](#13-knowledge_base) | AI/ML | 1 |
| 14 | [VESSEL_HISTORY](#14-vessel_history) | Support | 4 |
| 15 | [BERTH_MAINTENANCE](#15-berth_maintenance) | Support | 4 |
| 16 | [ALERTS_NOTIFICATIONS](#16-alerts_notifications) | Support | 1 |
| 17 | [USER_PREFERENCES](#17-user_preferences) | Support | 1 |
| 18 | [AUDIT_LOG](#18-audit_log) | Support | 1 |
| 19 | [ANCHORAGES](#19-anchorages) | Navigation | 2 |
| 20 | [CHANNELS](#20-channels) | Navigation | 3 |
| 21 | [PILOTS](#21-pilots) | Navigation | 2 |
| 22 | [TUGBOATS](#22-tugboats) | Navigation | 2 |
| 23 | [UKC_DATA](#23-ukc_data) | Navigation | 2 |

---

## CREATION SEQUENCE (Dependency Tiers)

```
Tier 1 (Independent)  : PORTS, VESSELS, RESOURCES, TIDAL_DATA, OPTIMIZATION_RUNS,
                         KNOWLEDGE_BASE, ALERTS_NOTIFICATIONS, USER_PREFERENCES, AUDIT_LOG

Tier 2 (Depends on 1) : TERMINALS, WEATHER_DATA, ANCHORAGES, PILOTS, TUGBOATS, UKC_DATA, AIS_DATA

Tier 3 (Depends on 2) : BERTHS, CHANNELS

Tier 4 (Depends on 3) : VESSEL_SCHEDULE, VESSEL_HISTORY, BERTH_MAINTENANCE

Tier 5 (Depends on 4) : RESOURCE_ALLOCATION, CONFLICTS
```

**Drop Order:** Reverse of above (Tier 5 first, Tier 1 last).

---

## DETAILED TABLE & COLUMN DEFINITIONS

---

### 1. PORTS
**Purpose:** Master registry of all ports managed by the system.
**Category:** Port Hierarchy | **Tier:** 1 (Independent)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **PortId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | PortName | NVARCHAR(200) | NOT NULL | -- | Full name of the port |
| 3 | PortCode | NVARCHAR(10) | NOT NULL | -- | UN/LOCODE or short code (unique) |
| 4 | Country | NVARCHAR(100) | NULL | -- | Country where port is located |
| 5 | City | NVARCHAR(100) | NULL | -- | City where port is located |
| 6 | TimeZone | NVARCHAR(50) | NULL | -- | IANA timezone identifier |
| 7 | Latitude | DECIMAL(10,7) | NULL | -- | Geographic latitude |
| 8 | Longitude | DECIMAL(10,7) | NULL | -- | Geographic longitude |
| 9 | ContactEmail | NVARCHAR(200) | NULL | -- | Port authority contact email |
| 10 | ContactPhone | NVARCHAR(50) | NULL | -- | Port authority contact phone |
| 11 | IsActive | BIT | NOT NULL | 1 | Whether port is active |
| 12 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |
| 13 | UpdatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record last update timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Ports | PRIMARY KEY CLUSTERED (PortId) |
| UK | UQ_Ports_PortCode | UNIQUE (PortCode) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Ports_Country | Country | NONCLUSTERED |
| IX_Ports_IsActive | IsActive | NONCLUSTERED |

---

### 2. TERMINALS
**Purpose:** Terminals within a port (e.g., Container Terminal, Bulk Terminal).
**Category:** Port Hierarchy | **Tier:** 2 (Depends on PORTS)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **TerminalId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | PortId | INT | NOT NULL | -- | FK to PORTS |
| 3 | TerminalName | NVARCHAR(200) | NOT NULL | -- | Full terminal name |
| 4 | TerminalCode | NVARCHAR(20) | NOT NULL | -- | Short code (unique) |
| 5 | TerminalType | NVARCHAR(50) | NULL | -- | Container, Bulk, Liquid, Multi-purpose, etc. |
| 6 | OperatorName | NVARCHAR(200) | NULL | -- | Terminal operator company |
| 7 | TotalBerths | INT | NULL | 0 | Number of berths in terminal |
| 8 | Latitude | DECIMAL(10,7) | NULL | -- | Terminal latitude |
| 9 | Longitude | DECIMAL(10,7) | NULL | -- | Terminal longitude |
| 10 | IsActive | BIT | NOT NULL | 1 | Whether terminal is active |
| 11 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |
| 12 | UpdatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record last update timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Terminals | PRIMARY KEY CLUSTERED (TerminalId) |
| UK | UQ_Terminals_TerminalCode | UNIQUE (TerminalCode) |
| FK | FK_Terminals_Ports | PortId REFERENCES PORTS(PortId) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Terminals_PortId | PortId | NONCLUSTERED |
| IX_Terminals_TerminalType | TerminalType | NONCLUSTERED |
| IX_Terminals_IsActive | IsActive | NONCLUSTERED |

---

### 3. VESSELS
**Purpose:** Master data for all vessels (ships) that visit or are expected at the port.
**Category:** Core | **Tier:** 1 (Independent)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **VesselId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | VesselName | NVARCHAR(200) | NOT NULL | -- | Name of the vessel |
| 3 | IMO | NVARCHAR(20) | NULL | -- | IMO number (globally unique) |
| 4 | MMSI | NVARCHAR(20) | NULL | -- | Maritime Mobile Service Identity |
| 5 | VesselType | NVARCHAR(50) | NULL | -- | Container, Bulk Carrier, Tanker, RoRo, etc. |
| 6 | LOA | DECIMAL(8,2) | NULL | -- | Length Overall in meters |
| 7 | Beam | DECIMAL(6,2) | NULL | -- | Width of vessel in meters |
| 8 | Draft | DECIMAL(6,2) | NULL | -- | Depth below waterline in meters |
| 9 | GrossTonnage | INT | NULL | -- | Gross tonnage of vessel |
| 10 | CargoType | NVARCHAR(100) | NULL | -- | Type of cargo carried |
| 11 | CargoVolume | DECIMAL(12,2) | NULL | -- | Volume of cargo |
| 12 | CargoUnit | NVARCHAR(20) | NULL | -- | Unit of measurement (TEU, MT, CBM) |
| 13 | Priority | INT | NOT NULL | 2 | Scheduling priority: 1=High, 2=Medium, 3=Low |
| 14 | FlagState | NVARCHAR(10) | NULL | -- | Country code of vessel registration |
| 15 | FlagStateName | NVARCHAR(100) | NULL | -- | Full name of flag state country |
| 16 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |
| 17 | UpdatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record last update timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Vessels | PRIMARY KEY CLUSTERED (VesselId) |
| UK | UQ_Vessels_IMO | UNIQUE (IMO) |
| CK | CK_Vessels_Priority | Priority BETWEEN 1 AND 3 |
| CK | CK_Vessels_LOA | LOA > 0 |
| CK | CK_Vessels_Beam | Beam > 0 |
| CK | CK_Vessels_Draft | Draft > 0 |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Vessels_VesselType | VesselType | NONCLUSTERED |
| IX_Vessels_Priority | Priority | NONCLUSTERED |
| IX_Vessels_MMSI | MMSI | NONCLUSTERED |

---

### 4. BERTHS
**Purpose:** Physical berth slots where vessels dock. Each berth belongs to a terminal and port.
**Category:** Port Hierarchy | **Tier:** 3 (Depends on TERMINALS, PORTS)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **BerthId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | TerminalId | INT | NULL | -- | FK to TERMINALS (nullable for port-level berths) |
| 3 | PortId | INT | NULL | -- | FK to PORTS |
| 4 | PortCode | NVARCHAR(10) | NULL | -- | Denormalized port code for quick reference |
| 5 | BerthName | NVARCHAR(100) | NOT NULL | -- | Name of the berth |
| 6 | BerthCode | NVARCHAR(20) | NOT NULL | -- | Short code (unique) |
| 7 | Length | DECIMAL(8,2) | NOT NULL | -- | Berth length in meters |
| 8 | Depth | DECIMAL(6,2) | NOT NULL | -- | Water depth at berth in meters |
| 9 | MaxDraft | DECIMAL(6,2) | NOT NULL | -- | Maximum vessel draft allowed |
| 10 | MaxLOA | DECIMAL(8,2) | NULL | -- | Maximum vessel LOA allowed |
| 11 | MaxBeam | DECIMAL(6,2) | NULL | -- | Maximum vessel beam allowed |
| 12 | BerthType | NVARCHAR(50) | NULL | -- | Container, Bulk, Liquid, Multi-purpose |
| 13 | NumberOfCranes | INT | NOT NULL | 0 | Cranes available at berth |
| 14 | BollardCount | INT | NOT NULL | 0 | Number of bollards |
| 15 | IsActive | BIT | NOT NULL | 1 | Whether berth is active |
| 16 | Latitude | DECIMAL(10,7) | NULL | -- | Berth latitude |
| 17 | Longitude | DECIMAL(10,7) | NULL | -- | Berth longitude |
| 18 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |
| 19 | UpdatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record last update timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Berths | PRIMARY KEY CLUSTERED (BerthId) |
| UK | UQ_Berths_BerthCode | UNIQUE (BerthCode) |
| FK | FK_Berths_Terminals | TerminalId REFERENCES TERMINALS(TerminalId) |
| FK | FK_Berths_Ports | PortId REFERENCES PORTS(PortId) |
| CK | CK_Berths_Length | Length > 0 |
| CK | CK_Berths_Depth | Depth > 0 |
| CK | CK_Berths_MaxDraft | MaxDraft > 0 |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Berths_TerminalId | TerminalId | NONCLUSTERED |
| IX_Berths_BerthType | BerthType | NONCLUSTERED |
| IX_Berths_IsActive | IsActive | NONCLUSTERED |

---

### 5. VESSEL_SCHEDULE
**Purpose:** Core scheduling table tracking vessel visits from ETA through departure, including all lifecycle timestamps, cargo info, performance metrics, and optimization data.
**Category:** Operational | **Tier:** 4 (Depends on VESSELS, BERTHS)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| | **-- Identifiers --** | | | | |
| 1 | **ScheduleId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | VesselId | INT | NOT NULL | -- | FK to VESSELS |
| 3 | BerthId | INT | NULL | -- | FK to BERTHS (null if not yet assigned) |
| | **-- Estimated Times --** | | | | |
| 4 | ETA | DATETIME2 | NULL | -- | Estimated Time of Arrival |
| 5 | PredictedETA | DATETIME2 | NULL | -- | AI-predicted ETA |
| 6 | ETD | DATETIME2 | NULL | -- | Estimated Time of Departure |
| | **-- Actual Times --** | | | | |
| 7 | ATA | DATETIME2 | NULL | -- | Actual Time of Arrival (port) |
| 8 | ATB | DATETIME2 | NULL | -- | Actual Time of Berthing |
| 9 | ATD | DATETIME2 | NULL | -- | Actual Time of Departure |
| | **-- Lifecycle Timestamps --** | | | | |
| 10 | AnchorageArrival | DATETIME2 | NULL | -- | When vessel arrived at anchorage |
| 11 | PilotBoardingTime | DATETIME2 | NULL | -- | When pilot boarded vessel |
| 12 | BerthArrivalTime | DATETIME2 | NULL | -- | When vessel reached berth area |
| 13 | FirstLineTime | DATETIME2 | NULL | -- | First mooring line ashore |
| 14 | AllFastTime | DATETIME2 | NULL | -- | All lines secured |
| 15 | CargoStartTime | DATETIME2 | NULL | -- | Cargo operations began |
| 16 | CargoCompleteTime | DATETIME2 | NULL | -- | Cargo operations completed |
| | **-- Status & Metrics --** | | | | |
| 17 | Status | NVARCHAR(50) | NOT NULL | 'Scheduled' | Scheduled/Approaching/Berthed/Departed/Cancelled |
| 18 | DwellTime | INT | NULL | -- | Total time at berth (minutes) |
| 19 | WaitingTime | INT | NULL | -- | Time waiting before berthing (minutes) |
| | **-- Cargo Info --** | | | | |
| 20 | CargoType | NVARCHAR(100) | NULL | -- | Type of cargo for this visit |
| 21 | CargoQuantity | DECIMAL(12,2) | NULL | -- | Amount of cargo |
| 22 | CargoUnit | NVARCHAR(20) | NULL | -- | Unit: TEU, MT, CBM, etc. |
| 23 | CargoOperation | NVARCHAR(50) | NULL | -- | Loading, Unloading, Both |
| | **-- Voyage Info --** | | | | |
| 24 | PortCode | NVARCHAR(10) | NULL | -- | Port code for this schedule |
| 25 | VoyageNumber | NVARCHAR(50) | NULL | -- | Voyage reference number |
| 26 | ShippingLine | NVARCHAR(200) | NULL | -- | Shipping line / operator |
| 27 | TerminalType | NVARCHAR(50) | NULL | -- | Terminal type requested |
| | **-- Resource Assignments --** | | | | |
| 28 | TugsAssigned | INT | NULL | -- | Number of tugs assigned |
| 29 | PilotsAssigned | INT | NULL | -- | Number of pilots assigned |
| | **-- Performance Metrics --** | | | | |
| 30 | WaitingTimeHours | DECIMAL(8,2) | NULL | -- | Waiting time in hours |
| 31 | DwellTimeHours | DECIMAL(8,2) | NULL | -- | Dwell time in hours |
| 32 | ETAVarianceHours | DECIMAL(8,2) | NULL | -- | Difference between ETA and ATA |
| 33 | BerthingDelayMins | INT | NULL | -- | Delay in berthing (minutes) |
| 34 | ArrivalDraft | DECIMAL(6,2) | NULL | -- | Vessel draft on arrival |
| 35 | DepartureDraft | DECIMAL(6,2) | NULL | -- | Vessel draft on departure |
| | **-- Optimization --** | | | | |
| 36 | OptimizationScore | DECIMAL(5,2) | NULL | -- | AI optimization score |
| 37 | IsOptimized | BIT | NOT NULL | 0 | Whether schedule was optimized |
| 38 | ConflictCount | INT | NOT NULL | 0 | Number of detected conflicts |
| | **-- Audit --** | | | | |
| 39 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |
| 40 | UpdatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record last update timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_VesselSchedule | PRIMARY KEY CLUSTERED (ScheduleId) |
| FK | FK_VesselSchedule_Vessels | VesselId REFERENCES VESSELS(VesselId) |
| FK | FK_VesselSchedule_Berths | BerthId REFERENCES BERTHS(BerthId) |
| CK | CK_VesselSchedule_Status | Status IN ('Scheduled','Approaching','Berthed','Departed','Cancelled') |
| CK | CK_VesselSchedule_DwellTime | DwellTime > 0 |
| CK | CK_VesselSchedule_WaitingTime | WaitingTime >= 0 |

#### Indexes

| Name | Columns | Type | Notes |
|------|---------|------|-------|
| IX_VesselSchedule_VesselId | VesselId | NONCLUSTERED | |
| IX_VesselSchedule_BerthId | BerthId | NONCLUSTERED | |
| IX_VesselSchedule_Status | Status | NONCLUSTERED | |
| IX_VesselSchedule_ETA | ETA | NONCLUSTERED | |
| IX_VesselSchedule_BerthId_ETA | BerthId, ETA | NONCLUSTERED | INCLUDE (ETD, Status) - Covering index |

---

### 6. RESOURCES
**Purpose:** Master list of port resources (cranes, tugboats, pilots, labor, mooring teams).
**Category:** Operational | **Tier:** 1 (Independent)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **ResourceId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | ResourceType | NVARCHAR(50) | NOT NULL | -- | Crane, Tugboat, Pilot, Labor, Mooring, Other |
| 3 | ResourceName | NVARCHAR(100) | NOT NULL | -- | Name/identifier of the resource |
| 4 | Capacity | INT | NOT NULL | 1 | Resource capacity units |
| 5 | IsAvailable | BIT | NOT NULL | 1 | Current availability status |
| 6 | MaintenanceSchedule | DATETIME2 | NULL | -- | Next scheduled maintenance |
| 7 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Resources | PRIMARY KEY CLUSTERED (ResourceId) |
| CK | CK_Resources_Type | ResourceType IN ('Crane','Tugboat','Pilot','Labor','Mooring','Other') |
| CK | CK_Resources_Capacity | Capacity > 0 |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Resources_Type | ResourceType | NONCLUSTERED |
| IX_Resources_IsAvailable | IsAvailable | NONCLUSTERED |

---

### 7. RESOURCE_ALLOCATION
**Purpose:** Links resources to vessel schedules with time-bound allocations.
**Category:** Operational | **Tier:** 5 (Depends on VESSEL_SCHEDULE, RESOURCES)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **AllocationId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | ScheduleId | INT | NOT NULL | -- | FK to VESSEL_SCHEDULE |
| 3 | ResourceId | INT | NOT NULL | -- | FK to RESOURCES |
| 4 | AllocatedFrom | DATETIME2 | NOT NULL | -- | Allocation start time |
| 5 | AllocatedTo | DATETIME2 | NOT NULL | -- | Allocation end time |
| 6 | Quantity | INT | NOT NULL | 1 | Number of resource units allocated |
| 7 | Status | NVARCHAR(50) | NOT NULL | 'Allocated' | Allocated, InUse, Released |
| 8 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_ResourceAllocation | PRIMARY KEY CLUSTERED (AllocationId) |
| FK | FK_ResourceAllocation_Schedule | ScheduleId REFERENCES VESSEL_SCHEDULE(ScheduleId) |
| FK | FK_ResourceAllocation_Resources | ResourceId REFERENCES RESOURCES(ResourceId) |
| CK | CK_ResourceAllocation_Status | Status IN ('Allocated','InUse','Released') |
| CK | CK_ResourceAllocation_Quantity | Quantity > 0 |
| CK | CK_ResourceAllocation_TimeRange | AllocatedFrom < AllocatedTo |

#### Indexes

| Name | Columns | Type | Notes |
|------|---------|------|-------|
| IX_ResourceAllocation_ScheduleId | ScheduleId | NONCLUSTERED | |
| IX_ResourceAllocation_ResourceId | ResourceId | NONCLUSTERED | |
| IX_ResourceAllocation_TimeRange | ResourceId, AllocatedFrom, AllocatedTo | NONCLUSTERED | Overlap detection |

---

### 8. WEATHER_DATA
**Purpose:** Weather observations per port used for operational decisions and safety alerts.
**Category:** External Data | **Tier:** 2 (Depends on PORTS)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **WeatherId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | PortId | INT | NULL | -- | FK to PORTS |
| 3 | PortCode | NVARCHAR(10) | NULL | -- | Denormalized port code |
| 4 | RecordedAt | DATETIME2 | NOT NULL | -- | When observation was taken |
| 5 | WindSpeed | DECIMAL(5,2) | NULL | -- | Wind speed in knots |
| 6 | WindDirection | INT | NULL | -- | Wind direction in degrees (0-360) |
| 7 | WindDirectionText | NVARCHAR(10) | NULL | -- | Wind direction label (N, NE, E, etc.) |
| 8 | Visibility | INT | NULL | -- | Visibility in meters |
| 9 | WaveHeight | DECIMAL(4,2) | NULL | -- | Wave height in meters |
| 10 | Temperature | DECIMAL(5,2) | NULL | -- | Temperature in Celsius |
| 11 | Precipitation | DECIMAL(5,2) | NULL | -- | Precipitation in mm |
| 12 | WeatherCondition | NVARCHAR(100) | NULL | -- | Clear, Rainy, Stormy, Foggy, etc. |
| 13 | Climate | NVARCHAR(50) | NULL | -- | Climate classification |
| 14 | Season | NVARCHAR(20) | NULL | -- | Season at time of recording |
| 15 | IsAlert | BIT | NOT NULL | 0 | Whether this triggers a weather alert |
| 16 | FetchedAt | DATETIME2 | NOT NULL | GETUTCDATE() | When data was fetched from source |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_WeatherData | PRIMARY KEY CLUSTERED (WeatherId) |
| FK | FK_WeatherData_Ports | PortId REFERENCES PORTS(PortId) |
| CK | CK_WeatherData_WindDirection | WindDirection BETWEEN 0 AND 360 |

#### Indexes

| Name | Columns | Type | Notes |
|------|---------|------|-------|
| IX_WeatherData_RecordedAt | RecordedAt DESC | NONCLUSTERED | |
| IX_WeatherData_IsAlert | IsAlert | NONCLUSTERED | Filtered: WHERE IsAlert = 1 |

---

### 9. TIDAL_DATA
**Purpose:** High/Low tide records used for UKC calculations and berth planning.
**Category:** External Data | **Tier:** 1 (Independent)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **TidalId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | TideTime | DATETIME2 | NOT NULL | -- | Date/time of tide event |
| 3 | TideType | NVARCHAR(20) | NOT NULL | -- | HighTide or LowTide |
| 4 | Height | DECIMAL(5,2) | NOT NULL | -- | Tide height in meters |
| 5 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_TidalData | PRIMARY KEY CLUSTERED (TidalId) |
| CK | CK_TidalData_Type | TideType IN ('HighTide','LowTide') |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_TidalData_TideTime | TideTime | NONCLUSTERED |
| IX_TidalData_TideType | TideType | NONCLUSTERED |

---

### 10. AIS_DATA
**Purpose:** Real-time AIS (Automatic Identification System) vessel tracking positions.
**Category:** External Data | **Tier:** 2 (Depends on VESSELS)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **AISId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | VesselId | INT | NOT NULL | -- | FK to VESSELS |
| 3 | MMSI | NVARCHAR(20) | NULL | -- | Vessel MMSI identifier |
| 4 | PortCode | NVARCHAR(10) | NULL | -- | Destination port code |
| 5 | VesselType | NVARCHAR(50) | NULL | -- | Vessel type from AIS signal |
| 6 | Latitude | DECIMAL(10,7) | NOT NULL | -- | Current latitude (-90 to 90) |
| 7 | Longitude | DECIMAL(10,7) | NOT NULL | -- | Current longitude (-180 to 180) |
| 8 | Speed | DECIMAL(5,2) | NULL | -- | Speed over ground in knots |
| 9 | Course | DECIMAL(5,2) | NULL | -- | Course over ground in degrees |
| 10 | Heading | DECIMAL(5,2) | NULL | -- | True heading in degrees |
| 11 | NavigationStatus | NVARCHAR(50) | NULL | -- | AIS navigation status text |
| 12 | NavigationStatusCode | INT | NULL | -- | AIS navigation status code |
| 13 | ETA | DATETIME2 | NULL | -- | AIS-reported ETA |
| 14 | TimeToPort | INT | NULL | -- | Estimated time to port (minutes) |
| 15 | Phase | NVARCHAR(50) | NULL | -- | Transit phase (e.g., Approaching, At Anchor) |
| 16 | DistanceToPort | DECIMAL(10,2) | NULL | -- | Distance to port in nautical miles |
| 17 | RecordedAt | DATETIME2 | NOT NULL | -- | Timestamp of AIS signal |
| 18 | FetchedAt | DATETIME2 | NOT NULL | GETUTCDATE() | When data was fetched |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_AISData | PRIMARY KEY CLUSTERED (AISId) |
| FK | FK_AISData_Vessels | VesselId REFERENCES VESSELS(VesselId) |
| CK | CK_AISData_Latitude | Latitude BETWEEN -90 AND 90 |
| CK | CK_AISData_Longitude | Longitude BETWEEN -180 AND 180 |
| CK | CK_AISData_Speed | Speed >= 0 |
| CK | CK_AISData_Course | Course BETWEEN 0 AND 360 |
| CK | CK_AISData_Heading | Heading BETWEEN 0 AND 360 |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_AISData_VesselId_RecordedAt | VesselId, RecordedAt DESC | NONCLUSTERED |
| IX_AISData_MMSI | MMSI | NONCLUSTERED |

---

### 11. CONFLICTS
**Purpose:** Detected scheduling conflicts (berth overlaps, resource issues, tidal/priority violations).
**Category:** AI/ML | **Tier:** 5 (Depends on VESSEL_SCHEDULE)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **ConflictId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | ConflictType | NVARCHAR(50) | NOT NULL | -- | BerthOverlap, ResourceUnavailable, TidalConstraint, PriorityViolation |
| 3 | ScheduleId1 | INT | NOT NULL | -- | FK to first conflicting schedule |
| 4 | ScheduleId2 | INT | NULL | -- | FK to second conflicting schedule |
| 5 | Description | NVARCHAR(500) | NULL | -- | Human-readable conflict description |
| 6 | Severity | INT | NOT NULL | 2 | 1=Low, 2=Medium, 3=High, 4=Critical |
| 7 | Status | NVARCHAR(50) | NOT NULL | 'Detected' | Detected, Resolved, Ignored |
| 8 | DetectedAt | DATETIME2 | NOT NULL | GETUTCDATE() | When conflict was detected |
| 9 | ResolvedAt | DATETIME2 | NULL | -- | When conflict was resolved |
| 10 | Resolution | NVARCHAR(MAX) | NULL | -- | How the conflict was resolved |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Conflicts | PRIMARY KEY CLUSTERED (ConflictId) |
| FK | FK_Conflicts_Schedule1 | ScheduleId1 REFERENCES VESSEL_SCHEDULE(ScheduleId) |
| FK | FK_Conflicts_Schedule2 | ScheduleId2 REFERENCES VESSEL_SCHEDULE(ScheduleId) |
| CK | CK_Conflicts_Type | ConflictType IN ('BerthOverlap','ResourceUnavailable','TidalConstraint','PriorityViolation') |
| CK | CK_Conflicts_Severity | Severity BETWEEN 1 AND 4 |
| CK | CK_Conflicts_Status | Status IN ('Detected','Resolved','Ignored') |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Conflicts_Status | Status | NONCLUSTERED |
| IX_Conflicts_ScheduleId1 | ScheduleId1 | NONCLUSTERED |
| IX_Conflicts_ScheduleId2 | ScheduleId2 | NONCLUSTERED |
| IX_Conflicts_DetectedAt | DetectedAt DESC | NONCLUSTERED |

---

### 12. OPTIMIZATION_RUNS
**Purpose:** Logs of AI/ML optimization runs for berth allocation.
**Category:** AI/ML | **Tier:** 1 (Independent)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **RunId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | RunType | NVARCHAR(50) | NOT NULL | -- | Initial, ReOptimization, ConflictResolution |
| 3 | Algorithm | NVARCHAR(100) | NULL | -- | Algorithm used (e.g., Genetic, Simulated Annealing) |
| 4 | InputParameters | NVARCHAR(MAX) | NULL | -- | JSON input parameters |
| 5 | OutputResults | NVARCHAR(MAX) | NULL | -- | JSON output results |
| 6 | ExecutionTime | INT | NULL | -- | Run duration in milliseconds |
| 7 | ImprovementScore | DECIMAL(5,2) | NULL | -- | Percentage improvement achieved |
| 8 | Status | NVARCHAR(50) | NOT NULL | 'Running' | Running, Completed, Failed |
| 9 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Run start timestamp |
| 10 | CompletedAt | DATETIME2 | NULL | -- | Run completion timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_OptimizationRuns | PRIMARY KEY CLUSTERED (RunId) |
| CK | CK_OptimizationRuns_Type | RunType IN ('Initial','ReOptimization','ConflictResolution') |
| CK | CK_OptimizationRuns_Status | Status IN ('Running','Completed','Failed') |
| CK | CK_OptimizationRuns_ExecutionTime | ExecutionTime >= 0 |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_OptimizationRuns_CreatedAt | CreatedAt DESC | NONCLUSTERED |
| IX_OptimizationRuns_Status | Status | NONCLUSTERED |

---

### 13. KNOWLEDGE_BASE
**Purpose:** Document store with embeddings for AI-powered RAG (Retrieval Augmented Generation).
**Category:** AI/ML | **Tier:** 1 (Independent)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **KnowledgeId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | DocumentType | NVARCHAR(100) | NULL | -- | Type of document (Policy, SOP, Regulation, etc.) |
| 3 | Title | NVARCHAR(500) | NOT NULL | -- | Document title |
| 4 | Content | NVARCHAR(MAX) | NOT NULL | -- | Full text content |
| 5 | Embedding | VARBINARY(MAX) | NULL | -- | Vector embedding for similarity search |
| 6 | Metadata | NVARCHAR(MAX) | NULL | -- | JSON metadata |
| 7 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_KnowledgeBase | PRIMARY KEY CLUSTERED (KnowledgeId) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_KnowledgeBase_DocumentType | DocumentType | NONCLUSTERED |
| IX_KnowledgeBase_CreatedAt | CreatedAt DESC | NONCLUSTERED |

---

### 14. VESSEL_HISTORY
**Purpose:** Historical record of completed vessel visits for analytics and AI training.
**Category:** Support | **Tier:** 4 (Depends on VESSELS, BERTHS)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **HistoryId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | VesselId | INT | NOT NULL | -- | FK to VESSELS |
| 3 | BerthId | INT | NOT NULL | -- | FK to BERTHS |
| 4 | VisitDate | DATETIME2 | NOT NULL | -- | Date of the visit |
| 5 | ActualDwellTime | INT | NULL | -- | Actual time at berth (minutes) |
| 6 | ActualWaitingTime | INT | NULL | -- | Actual waiting time (minutes) |
| 7 | ETAAccuracy | DECIMAL(5,2) | NULL | -- | ETA accuracy percentage |
| 8 | Notes | NVARCHAR(500) | NULL | -- | Additional notes |
| 9 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_VesselHistory | PRIMARY KEY CLUSTERED (HistoryId) |
| FK | FK_VesselHistory_Vessels | VesselId REFERENCES VESSELS(VesselId) |
| FK | FK_VesselHistory_Berths | BerthId REFERENCES BERTHS(BerthId) |
| CK | CK_VesselHistory_DwellTime | ActualDwellTime > 0 |
| CK | CK_VesselHistory_WaitingTime | ActualWaitingTime >= 0 |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_VesselHistory_VesselId | VesselId | NONCLUSTERED |
| IX_VesselHistory_BerthId | BerthId | NONCLUSTERED |
| IX_VesselHistory_VisitDate | VisitDate DESC | NONCLUSTERED |

---

### 15. BERTH_MAINTENANCE
**Purpose:** Tracks berth maintenance windows when berths are unavailable for scheduling.
**Category:** Support | **Tier:** 4 (Depends on BERTHS)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **MaintenanceId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | BerthId | INT | NOT NULL | -- | FK to BERTHS |
| 3 | StartTime | DATETIME2 | NOT NULL | -- | Maintenance start time |
| 4 | EndTime | DATETIME2 | NOT NULL | -- | Maintenance end time |
| 5 | MaintenanceType | NVARCHAR(50) | NULL | -- | Type of maintenance |
| 6 | Status | NVARCHAR(50) | NOT NULL | 'Scheduled' | Scheduled, InProgress, Completed, Cancelled |
| 7 | Description | NVARCHAR(500) | NULL | -- | Description of work |
| 8 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_BerthMaintenance | PRIMARY KEY CLUSTERED (MaintenanceId) |
| FK | FK_BerthMaintenance_Berths | BerthId REFERENCES BERTHS(BerthId) |
| CK | CK_BerthMaintenance_Status | Status IN ('Scheduled','InProgress','Completed','Cancelled') |
| CK | CK_BerthMaintenance_TimeRange | StartTime < EndTime |

#### Indexes

| Name | Columns | Type | Notes |
|------|---------|------|-------|
| IX_BerthMaintenance_BerthId | BerthId | NONCLUSTERED | |
| IX_BerthMaintenance_Status | Status | NONCLUSTERED | |
| IX_BerthMaintenance_TimeRange | BerthId, StartTime, EndTime | NONCLUSTERED | Overlap detection |

---

### 16. ALERTS_NOTIFICATIONS
**Purpose:** System-generated alerts for weather, conflicts, delays, and other events.
**Category:** Support | **Tier:** 1 (Independent)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **AlertId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | AlertType | NVARCHAR(50) | NOT NULL | -- | Type of alert |
| 3 | RelatedEntityId | INT | NULL | -- | ID of related entity (vessel, schedule, etc.) |
| 4 | EntityType | NVARCHAR(50) | NULL | -- | Type of related entity |
| 5 | Severity | NVARCHAR(20) | NOT NULL | 'Medium' | Critical, High, Medium, Low |
| 6 | Message | NVARCHAR(500) | NOT NULL | -- | Alert message text |
| 7 | IsRead | BIT | NOT NULL | 0 | Whether alert has been read |
| 8 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Alert creation timestamp |
| 9 | ReadAt | DATETIME2 | NULL | -- | When alert was read |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_AlertsNotifications | PRIMARY KEY CLUSTERED (AlertId) |
| CK | CK_AlertsNotifications_Severity | Severity IN ('Critical','High','Medium','Low') |

#### Indexes

| Name | Columns | Type | Notes |
|------|---------|------|-------|
| IX_AlertsNotifications_IsRead | IsRead | NONCLUSTERED | Filtered: WHERE IsRead = 0 |
| IX_AlertsNotifications_CreatedAt | CreatedAt DESC | NONCLUSTERED | |
| IX_AlertsNotifications_Severity | Severity | NONCLUSTERED | |

---

### 17. USER_PREFERENCES
**Purpose:** Stores per-user application settings as key-value pairs.
**Category:** Support | **Tier:** 1 (Independent)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **PreferenceId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | UserId | NVARCHAR(100) | NOT NULL | -- | User identifier |
| 3 | PreferenceKey | NVARCHAR(100) | NOT NULL | -- | Setting key name |
| 4 | PreferenceValue | NVARCHAR(MAX) | NULL | -- | Setting value (JSON or string) |
| 5 | UpdatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Last update timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_UserPreferences | PRIMARY KEY CLUSTERED (PreferenceId) |
| UK | UQ_UserPreferences_UserKey | UNIQUE (UserId, PreferenceKey) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_UserPreferences_UserId | UserId | NONCLUSTERED |

---

### 18. AUDIT_LOG
**Purpose:** Tracks all data changes across the system for compliance and debugging.
**Category:** Support | **Tier:** 1 (Independent)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **LogId** | BIGINT IDENTITY(1,1) | NOT NULL | Auto | Primary key (BIGINT for high volume) |
| 2 | UserId | NVARCHAR(100) | NULL | -- | User who made the change |
| 3 | Action | NVARCHAR(50) | NOT NULL | -- | INSERT, UPDATE, DELETE |
| 4 | EntityType | NVARCHAR(50) | NOT NULL | -- | Table/entity that was modified |
| 5 | EntityId | INT | NOT NULL | -- | ID of the modified record |
| 6 | OldValue | NVARCHAR(MAX) | NULL | -- | JSON of old values |
| 7 | NewValue | NVARCHAR(MAX) | NULL | -- | JSON of new values |
| 8 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Change timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_AuditLog | PRIMARY KEY CLUSTERED (LogId) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_AuditLog_EntityType_EntityId | EntityType, EntityId | NONCLUSTERED |
| IX_AuditLog_CreatedAt | CreatedAt DESC | NONCLUSTERED |
| IX_AuditLog_UserId | UserId | NONCLUSTERED |

---

### 19. ANCHORAGES
**Purpose:** Anchorage areas where vessels wait before berthing.
**Category:** Navigation | **Tier:** 2 (Depends on PORTS)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **AnchorageId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | PortId | INT | NOT NULL | -- | FK to PORTS |
| 3 | AnchorageName | NVARCHAR(200) | NOT NULL | -- | Name of anchorage area |
| 4 | AnchorageType | NVARCHAR(50) | NULL | -- | General, Deep Water, Quarantine, etc. |
| 5 | Latitude | DECIMAL(10,7) | NULL | -- | Center latitude |
| 6 | Longitude | DECIMAL(10,7) | NULL | -- | Center longitude |
| 7 | Depth | INT | NULL | -- | Water depth in meters |
| 8 | MaxVessels | INT | NULL | -- | Maximum vessels allowed |
| 9 | CurrentOccupancy | INT | NULL | 0 | Current number of vessels |
| 10 | MaxVesselLOA | INT | NULL | -- | Maximum vessel LOA allowed |
| 11 | MaxVesselDraft | DECIMAL(6,2) | NULL | -- | Maximum vessel draft allowed |
| 12 | AverageWaitingTime | DECIMAL(8,2) | NULL | -- | Average waiting time in hours |
| 13 | STSCargoOpsPermitted | BIT | NULL | 0 | Ship-to-Ship transfer allowed |
| 14 | QuarantineAnchorage | BIT | NULL | 0 | Used for quarantine purposes |
| 15 | IsActive | BIT | NOT NULL | 1 | Whether anchorage is active |
| 16 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Anchorages | PRIMARY KEY CLUSTERED (AnchorageId) |
| FK | FK_Anchorages_Ports | PortId REFERENCES PORTS(PortId) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Anchorages_PortId | PortId | NONCLUSTERED |
| IX_Anchorages_AnchorageType | AnchorageType | NONCLUSTERED |

---

### 20. CHANNELS
**Purpose:** Navigation channels connecting open sea to port berths, with restrictions and safety rules.
**Category:** Navigation | **Tier:** 3 (Depends on PORTS, ANCHORAGES)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **ChannelId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | PortId | INT | NOT NULL | -- | FK to PORTS |
| 3 | ChannelName | NVARCHAR(200) | NOT NULL | -- | Channel name |
| 4 | ChannelLength | DECIMAL(10,2) | NULL | -- | Length in meters |
| 5 | ChannelWidth | DECIMAL(8,2) | NULL | -- | Width in meters |
| 6 | ChannelDepth | DECIMAL(6,2) | NULL | -- | Maintained depth in meters |
| 7 | ChannelDepthAtChartDatum | DECIMAL(6,2) | NULL | -- | Depth at chart datum |
| 8 | OneWayOrTwoWay | NVARCHAR(20) | NULL | -- | Traffic direction (OneWay / TwoWay) |
| 9 | MaxVesselLOA | DECIMAL(8,2) | NULL | -- | Max vessel LOA allowed |
| 10 | MaxVesselBeam | DECIMAL(6,2) | NULL | -- | Max vessel beam allowed |
| 11 | MaxVesselDraft | DECIMAL(6,2) | NULL | -- | Max vessel draft allowed |
| 12 | TrafficSeparationScheme | BIT | NULL | 0 | TSS in effect |
| 13 | SpeedLimit | INT | NULL | -- | Speed limit in knots |
| 14 | TidalWindowRequired | BIT | NULL | 0 | Must transit during tidal window |
| 15 | PilotageCompulsory | BIT | NULL | 1 | Pilot mandatory |
| 16 | TugEscortRequired | BIT | NULL | 0 | Tug escort mandatory |
| 17 | DayNightRestrictions | NVARCHAR(500) | NULL | -- | Day/night transit restrictions |
| 18 | VisibilityMinimum | INT | NULL | -- | Minimum visibility in meters |
| 19 | WindSpeedLimit | INT | NULL | -- | Max wind speed for transit (knots) |
| 20 | CurrentSpeedLimit | DECIMAL(5,2) | NULL | -- | Max current speed (knots) |
| 21 | ChannelSegments | NVARCHAR(MAX) | NULL | -- | JSON array of channel segments |
| 22 | AnchorageAreaId | INT | NULL | -- | FK to ANCHORAGES |
| 23 | IsActive | BIT | NOT NULL | 1 | Whether channel is active |
| 24 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Channels | PRIMARY KEY CLUSTERED (ChannelId) |
| FK | FK_Channels_Ports | PortId REFERENCES PORTS(PortId) |
| FK | FK_Channels_Anchorages | AnchorageAreaId REFERENCES ANCHORAGES(AnchorageId) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Channels_PortId | PortId | NONCLUSTERED |
| IX_Channels_IsActive | IsActive | NONCLUSTERED |

---

### 21. PILOTS
**Purpose:** Pilot personnel records including certifications, capabilities, and license details.
**Category:** Navigation | **Tier:** 2 (Depends on PORTS via PortCode)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **PilotId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | PortCode | NVARCHAR(10) | NOT NULL | -- | FK to PORTS(PortCode) |
| 3 | PortName | NVARCHAR(200) | NULL | -- | Denormalized port name |
| 4 | PilotName | NVARCHAR(200) | NOT NULL | -- | Full name of pilot |
| 5 | PilotCode | NVARCHAR(20) | NULL | -- | Pilot identification code |
| 6 | PilotType | NVARCHAR(50) | NULL | -- | Harbour, River, Sea, etc. |
| 7 | PilotClass | NVARCHAR(20) | NULL | -- | Class rating (A, B, C) |
| 8 | CertificationLevel | NVARCHAR(50) | NULL | -- | Certification level |
| 9 | ExperienceYears | INT | NULL | -- | Years of experience |
| 10 | MaxVesselGT | INT | NULL | -- | Max gross tonnage certified for |
| 11 | MaxVesselLOA | INT | NULL | -- | Max LOA certified for (meters) |
| 12 | NightOperations | BIT | NULL | 1 | Certified for night operations |
| 13 | AdverseWeather | BIT | NULL | 0 | Certified for adverse weather |
| 14 | CanTrain | BIT | NULL | 0 | Authorized to train junior pilots |
| 15 | LicenseIssueDate | DATE | NULL | -- | License issue date |
| 16 | LicenseExpiryDate | DATE | NULL | -- | License expiry date |
| 17 | Status | NVARCHAR(50) | NULL | 'Active' | Active, OnLeave, Retired, Suspended |
| 18 | Languages | NVARCHAR(500) | NULL | -- | Languages spoken |
| 19 | Certifications | NVARCHAR(MAX) | NULL | -- | JSON array of certifications |
| 20 | CertificationsCount | INT | NULL | -- | Total number of certifications |
| 21 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Pilots | PRIMARY KEY CLUSTERED (PilotId) |
| FK | FK_Pilots_Ports | PortCode REFERENCES PORTS(PortCode) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Pilots_PortCode | PortCode | NONCLUSTERED |
| IX_Pilots_PilotType | PilotType | NONCLUSTERED |
| IX_Pilots_Status | Status | NONCLUSTERED |
| IX_Pilots_CertificationLevel | CertificationLevel | NONCLUSTERED |

---

### 22. TUGBOATS
**Purpose:** Tugboat fleet records with specifications, capabilities, and operational status.
**Category:** Navigation | **Tier:** 2 (Depends on PORTS via PortCode)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **TugId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | PortCode | NVARCHAR(10) | NOT NULL | -- | FK to PORTS(PortCode) |
| 3 | TugName | NVARCHAR(200) | NOT NULL | -- | Tugboat name |
| 4 | TugCode | NVARCHAR(20) | NULL | -- | Tugboat identification code |
| 5 | IMONumber | NVARCHAR(20) | NULL | -- | IMO number |
| 6 | MMSI | NVARCHAR(20) | NULL | -- | MMSI identifier |
| 7 | CallSign | NVARCHAR(20) | NULL | -- | Radio call sign |
| 8 | FlagState | NVARCHAR(10) | NULL | -- | Country of registration |
| 9 | PortOfRegistry | NVARCHAR(200) | NULL | -- | Port of registration |
| 10 | TugType | NVARCHAR(50) | NULL | -- | ASD, Voith, Conventional, etc. |
| 11 | TugTypeFullName | NVARCHAR(100) | NULL | -- | Full name of tug type |
| 12 | TugClass | NVARCHAR(20) | NULL | -- | Classification (A, B, C) |
| 13 | Operator | NVARCHAR(200) | NULL | -- | Operating company |
| 14 | BollardPull | INT | NULL | -- | Bollard pull in tonnes |
| 15 | Length | DECIMAL(6,2) | NULL | -- | Tug length in meters |
| 16 | Beam | DECIMAL(6,2) | NULL | -- | Tug beam in meters |
| 17 | Draft | DECIMAL(6,2) | NULL | -- | Tug draft in meters |
| 18 | EnginePower | INT | NULL | -- | Engine power in kW |
| 19 | MaxSpeed | DECIMAL(5,2) | NULL | -- | Maximum speed in knots |
| 20 | YearBuilt | INT | NULL | -- | Year of construction |
| 21 | FiFiClass | NVARCHAR(20) | NULL | -- | Fire-fighting class rating |
| 22 | WinchCapacity | INT | NULL | -- | Winch capacity in tonnes |
| 23 | CrewSize | INT | NULL | -- | Number of crew members |
| 24 | Status | NVARCHAR(50) | NULL | 'Operational' | Operational, Under Repair, Dry Dock, Decommissioned |
| 25 | CreatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Record creation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_Tugboats | PRIMARY KEY CLUSTERED (TugId) |
| FK | FK_Tugboats_Ports | PortCode REFERENCES PORTS(PortCode) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_Tugboats_PortCode | PortCode | NONCLUSTERED |
| IX_Tugboats_TugType | TugType | NONCLUSTERED |
| IX_Tugboats_TugClass | TugClass | NONCLUSTERED |
| IX_Tugboats_Status | [Status] | NONCLUSTERED |

---

### 23. UKC_DATA
**Purpose:** Under Keel Clearance (UKC) calculation records for vessel safety assessment in channels.
**Category:** Navigation | **Tier:** 2 (Depends on PORTS)

#### Columns

| # | Column | Data Type | Nullable | Default | Description |
|---|--------|-----------|----------|---------|-------------|
| 1 | **UKCId** | INT IDENTITY(1,1) | NOT NULL | Auto | Primary key |
| 2 | PortId | INT | NULL | -- | FK to PORTS |
| 3 | PortCode | NVARCHAR(10) | NULL | -- | Denormalized port code |
| 4 | VesselType | NVARCHAR(50) | NULL | -- | Type of vessel assessed |
| 5 | VesselLOA | DECIMAL(8,2) | NULL | -- | Vessel LOA in meters |
| 6 | VesselBeam | DECIMAL(6,2) | NULL | -- | Vessel beam in meters |
| 7 | VesselDraft | DECIMAL(6,2) | NULL | -- | Vessel draft in meters |
| 8 | GrossTonnage | INT | NULL | -- | Vessel gross tonnage |
| 9 | ChannelDepth | DECIMAL(6,2) | NULL | -- | Channel depth in meters |
| 10 | TidalHeight | DECIMAL(5,2) | NULL | -- | Tidal height at time of transit |
| 11 | AvailableDepth | DECIMAL(6,2) | NULL | -- | ChannelDepth + TidalHeight |
| 12 | StaticUKC | DECIMAL(5,2) | NULL | -- | UKC at rest (AvailableDepth - Draft) |
| 13 | Squat | DECIMAL(5,2) | NULL | -- | Squat effect at speed |
| 14 | DynamicUKC | DECIMAL(5,2) | NULL | -- | UKC while moving |
| 15 | UKCPercentage | DECIMAL(5,2) | NULL | -- | UKC as % of draft |
| 16 | RequiredUKCPercentage | DECIMAL(5,2) | NULL | -- | Minimum required UKC % |
| 17 | IsSafe | BIT | NULL | -- | Whether transit is safe |
| 18 | SpeedKnots | DECIMAL(5,2) | NULL | -- | Vessel speed for calculation |
| 19 | BlockCoefficient | DECIMAL(5,4) | NULL | -- | Hull block coefficient (Cb) |
| 20 | WaveAllowance | DECIMAL(5,2) | NULL | -- | Wave-induced motion allowance |
| 21 | HeelAllowance | DECIMAL(5,2) | NULL | -- | Heel/list allowance |
| 22 | NetUKC | DECIMAL(5,2) | NULL | -- | Net UKC after all deductions |
| 23 | SafetyMargin | DECIMAL(5,2) | NULL | -- | Additional safety margin |
| 24 | RiskLevel | NVARCHAR(20) | NULL | -- | Low, Medium, High, Critical |
| 25 | Recommendation | NVARCHAR(500) | NULL | -- | AI-generated recommendation |
| 26 | CalculatedAt | DATETIME2 | NOT NULL | GETUTCDATE() | Calculation timestamp |

#### Constraints

| Type | Name | Definition |
|------|------|------------|
| PK | PK_UKCData | PRIMARY KEY CLUSTERED (UKCId) |
| FK | FK_UKCData_Ports | PortId REFERENCES PORTS(PortId) |

#### Indexes

| Name | Columns | Type |
|------|---------|------|
| IX_UKCData_PortCode | PortCode | NONCLUSTERED |
| IX_UKCData_VesselType | VesselType | NONCLUSTERED |
| IX_UKCData_IsSafe | IsSafe | NONCLUSTERED |

---

## FOREIGN KEY RELATIONSHIP MAP

```
PORTS (PortId PK, PortCode UK)
  |
  |-- [PortId] --> TERMINALS
  |                   |
  |                   |-- [TerminalId] --> BERTHS
  |                                         |
  |-- [PortId] -----------------------> BERTHS
  |                                         |
  |                                         |-- [BerthId] --> VESSEL_SCHEDULE
  |                                         |                    |
  |                                         |                    |-- [ScheduleId] --> RESOURCE_ALLOCATION
  |                                         |                    |-- [ScheduleId] --> CONFLICTS (x2)
  |                                         |
  |                                         |-- [BerthId] --> VESSEL_HISTORY
  |                                         |-- [BerthId] --> BERTH_MAINTENANCE
  |
  |-- [PortId] --> WEATHER_DATA
  |-- [PortId] --> ANCHORAGES
  |                   |
  |                   |-- [AnchorageId] --> CHANNELS
  |
  |-- [PortId] --> CHANNELS
  |-- [PortCode] --> PILOTS
  |-- [PortCode] --> TUGBOATS
  |-- [PortId] --> UKC_DATA

VESSELS (VesselId PK, IMO UK)
  |
  |-- [VesselId] --> VESSEL_SCHEDULE
  |-- [VesselId] --> AIS_DATA
  |-- [VesselId] --> VESSEL_HISTORY

RESOURCES (ResourceId PK)
  |
  |-- [ResourceId] --> RESOURCE_ALLOCATION

STANDALONE (No FK references):
  TIDAL_DATA, OPTIMIZATION_RUNS, KNOWLEDGE_BASE,
  ALERTS_NOTIFICATIONS, USER_PREFERENCES, AUDIT_LOG
```

---

## CONSTRAINT SUMMARY BY TYPE

### Primary Keys (23)
All tables use INT IDENTITY(1,1) except AUDIT_LOG which uses BIGINT IDENTITY(1,1).

### Unique Constraints (6)
| Table | Constraint | Column(s) |
|-------|-----------|-----------|
| PORTS | UQ_Ports_PortCode | PortCode |
| TERMINALS | UQ_Terminals_TerminalCode | TerminalCode |
| VESSELS | UQ_Vessels_IMO | IMO |
| BERTHS | UQ_Berths_BerthCode | BerthCode |
| USER_PREFERENCES | UQ_UserPreferences_UserKey | UserId, PreferenceKey |

### Foreign Keys (18)
| FK Name | From Table.Column | To Table.Column |
|---------|-------------------|-----------------|
| FK_Terminals_Ports | TERMINALS.PortId | PORTS.PortId |
| FK_Berths_Terminals | BERTHS.TerminalId | TERMINALS.TerminalId |
| FK_Berths_Ports | BERTHS.PortId | PORTS.PortId |
| FK_VesselSchedule_Vessels | VESSEL_SCHEDULE.VesselId | VESSELS.VesselId |
| FK_VesselSchedule_Berths | VESSEL_SCHEDULE.BerthId | BERTHS.BerthId |
| FK_ResourceAllocation_Schedule | RESOURCE_ALLOCATION.ScheduleId | VESSEL_SCHEDULE.ScheduleId |
| FK_ResourceAllocation_Resources | RESOURCE_ALLOCATION.ResourceId | RESOURCES.ResourceId |
| FK_WeatherData_Ports | WEATHER_DATA.PortId | PORTS.PortId |
| FK_AISData_Vessels | AIS_DATA.VesselId | VESSELS.VesselId |
| FK_Conflicts_Schedule1 | CONFLICTS.ScheduleId1 | VESSEL_SCHEDULE.ScheduleId |
| FK_Conflicts_Schedule2 | CONFLICTS.ScheduleId2 | VESSEL_SCHEDULE.ScheduleId |
| FK_VesselHistory_Vessels | VESSEL_HISTORY.VesselId | VESSELS.VesselId |
| FK_VesselHistory_Berths | VESSEL_HISTORY.BerthId | BERTHS.BerthId |
| FK_BerthMaintenance_Berths | BERTH_MAINTENANCE.BerthId | BERTHS.BerthId |
| FK_Anchorages_Ports | ANCHORAGES.PortId | PORTS.PortId |
| FK_Channels_Ports | CHANNELS.PortId | PORTS.PortId |
| FK_Channels_Anchorages | CHANNELS.AnchorageAreaId | ANCHORAGES.AnchorageId |
| FK_Pilots_Ports | PILOTS.PortCode | PORTS.PortCode |
| FK_Tugboats_Ports | TUGBOATS.PortCode | PORTS.PortCode |
| FK_UKCData_Ports | UKC_DATA.PortId | PORTS.PortId |

### CHECK Constraints (25)
| Table | Constraint | Rule |
|-------|-----------|------|
| VESSELS | CK_Vessels_Priority | BETWEEN 1 AND 3 |
| VESSELS | CK_Vessels_LOA | > 0 |
| VESSELS | CK_Vessels_Beam | > 0 |
| VESSELS | CK_Vessels_Draft | > 0 |
| BERTHS | CK_Berths_Length | > 0 |
| BERTHS | CK_Berths_Depth | > 0 |
| BERTHS | CK_Berths_MaxDraft | > 0 |
| VESSEL_SCHEDULE | CK_VesselSchedule_Status | IN ('Scheduled','Approaching','Berthed','Departed','Cancelled') |
| VESSEL_SCHEDULE | CK_VesselSchedule_DwellTime | > 0 |
| VESSEL_SCHEDULE | CK_VesselSchedule_WaitingTime | >= 0 |
| RESOURCES | CK_Resources_Type | IN ('Crane','Tugboat','Pilot','Labor','Mooring','Other') |
| RESOURCES | CK_Resources_Capacity | > 0 |
| RESOURCE_ALLOCATION | CK_ResourceAllocation_Status | IN ('Allocated','InUse','Released') |
| RESOURCE_ALLOCATION | CK_ResourceAllocation_Quantity | > 0 |
| RESOURCE_ALLOCATION | CK_ResourceAllocation_TimeRange | AllocatedFrom < AllocatedTo |
| WEATHER_DATA | CK_WeatherData_WindDirection | BETWEEN 0 AND 360 |
| TIDAL_DATA | CK_TidalData_Type | IN ('HighTide','LowTide') |
| AIS_DATA | CK_AISData_Latitude | BETWEEN -90 AND 90 |
| AIS_DATA | CK_AISData_Longitude | BETWEEN -180 AND 180 |
| AIS_DATA | CK_AISData_Speed | >= 0 |
| AIS_DATA | CK_AISData_Course | BETWEEN 0 AND 360 |
| AIS_DATA | CK_AISData_Heading | BETWEEN 0 AND 360 |
| CONFLICTS | CK_Conflicts_Type | IN ('BerthOverlap','ResourceUnavailable','TidalConstraint','PriorityViolation') |
| CONFLICTS | CK_Conflicts_Severity | BETWEEN 1 AND 4 |
| CONFLICTS | CK_Conflicts_Status | IN ('Detected','Resolved','Ignored') |
| OPTIMIZATION_RUNS | CK_OptimizationRuns_Type | IN ('Initial','ReOptimization','ConflictResolution') |
| OPTIMIZATION_RUNS | CK_OptimizationRuns_Status | IN ('Running','Completed','Failed') |
| OPTIMIZATION_RUNS | CK_OptimizationRuns_ExecutionTime | >= 0 |
| VESSEL_HISTORY | CK_VesselHistory_DwellTime | > 0 |
| VESSEL_HISTORY | CK_VesselHistory_WaitingTime | >= 0 |
| BERTH_MAINTENANCE | CK_BerthMaintenance_Status | IN ('Scheduled','InProgress','Completed','Cancelled') |
| BERTH_MAINTENANCE | CK_BerthMaintenance_TimeRange | StartTime < EndTime |
| ALERTS_NOTIFICATIONS | CK_AlertsNotifications_Severity | IN ('Critical','High','Medium','Low') |

---

*Document generated: 2026-02-04 | Schema Version: 4.0*
