# Berth Planning & Allocation Optimization System

An AI-powered full-stack application for maritime port berth planning, vessel scheduling, and resource optimization.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | .NET 10.0 (C#), Clean Architecture |
| **Frontend** | React 19, TypeScript, Tailwind CSS |
| **Database** | MS-SQL Server |
| **Charts** | Recharts |
| **HTTP Client** | Axios + TanStack React Query |
| **Real-time** | SignalR |
| **Icons** | Lucide React |

---

## Project Structure

```
Berth_Planning/
|
|-- src/                              # Backend (.NET)
|   |-- BerthPlanning.sln             # Solution file
|   |-- BerthPlanning.API/            # API layer (Controllers, Program.cs)
|   |-- BerthPlanning.Core/           # Domain layer (Models, Interfaces, DTOs, Services)
|   |-- BerthPlanning.Infrastructure/ # Data layer (Repositories, Services)
|
|-- frontend-react/                   # Frontend (React + TypeScript)
|   |-- src/
|       |-- pages/                    # 14 page components
|       |-- components/               # Shared UI components
|       |-- api/                      # API service layer (Axios)
|       |-- types/                    # TypeScript interfaces
|       |-- context/                  # React context providers
|       |-- hooks/                    # Custom React hooks
|
|-- database_scripts/                 # SQL Server scripts
|   |-- 01_Create_Tables.sql          # 23 tables
|   |-- 03_Create_Views.sql           # 11 views
|   |-- 04_Create_StoredProcedures.sql# 8 stored procedures
|   |-- 05_Create_SqlJobs.sql         # SQL Agent jobs
|   |-- seeddata/                     # 12 seed data scripts
|
|-- documents/                        # Specifications, ERD, training data
|-- frontend/                         # Legacy HTML prototypes
```

---

## Architecture

The backend follows **Clean Architecture** with 3 layers:

```
BerthPlanning.API          --> Controllers (17), Program.cs, Configuration
       |
BerthPlanning.Core         --> Models (18), Interfaces (12), DTOs (6), Service Contracts (11)
       |
BerthPlanning.Infrastructure --> Repositories (11), Services (10), DbConnectionFactory
```

---

## Backend API

### Controllers (17)

| Controller | Endpoint Prefix | Purpose |
|-----------|----------------|---------|
| PortsController | `/api/ports` | Port master data CRUD |
| TerminalsController | `/api/terminals` | Terminal management |
| BerthsController | `/api/berths` | Berth configuration and status |
| VesselsController | `/api/vessels` | Vessel master data |
| SchedulesController | `/api/schedules` | Vessel schedule CRUD |
| ResourcesController | `/api/resources` | Resource management |
| DashboardController | `/api/dashboard` | Dashboard KPIs and metrics |
| AISController | `/api/ais` | AIS vessel tracking data |
| WhatIfController | `/api/whatif` | What-if scenario analysis |
| OptimizationController | `/api/optimization` | Berth optimization (OR-Tools) |
| PredictionsController | `/api/predictions` | ETA and dwell time predictions |
| SuggestionsController | `/api/suggestions` | AI-powered suggestions |
| AnalyticsController | `/api/analytics` | Performance analytics |
| ChannelsController | `/api/channels` | Navigation channel data |
| AnchoragesController | `/api/anchorages` | Anchorage area data |
| PilotsController | `/api/pilots` | Pilot personnel data |
| TugboatsController | `/api/tugboats` | Tugboat fleet data |

### Core Models (18)

Port, Terminal, Vessel, Berth, VesselSchedule, Resource, ResourceAllocation, WeatherData, TidalData, AISData, Conflict, AlertNotification, BerthMaintenance, Pilot, Tugboat, Channel, Anchorage, UKCData

### Service Contracts (11)

| Service | Purpose |
|---------|---------|
| IOptimizationService | Berth allocation optimization |
| IBerthOptimizationOrToolsService | Google OR-Tools based optimization |
| IConflictDetectionService | Schedule conflict detection |
| IConstraintValidator | Berth-vessel compatibility validation |
| IPredictionService | ETA and dwell time prediction |
| IReoptimizationService | Dynamic re-optimization triggers |
| IResourceOptimizationService | Resource allocation optimization |
| IScoringEngine | Schedule scoring and ranking |
| ISuggestionService | AI-powered operational suggestions |
| IWhatIfService | What-if scenario simulation |
| IAnalyticsService | Analytics and reporting |

---

## Frontend (React)

### Pages (14)

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | KPIs, berth timeline, vessel queue, alerts |
| Ports | `/ports` | Port master data management |
| Berths | `/berths` | Berth configuration and real-time status |
| Vessels | `/vessels` | Vessel registry and details |
| Schedules | `/schedules` | Vessel schedule management |
| ScheduleGantt | `/schedule-gantt` | Gantt chart berth timeline |
| Resources | `/resources` | Resource allocation management |
| LiveTracking | `/live-tracking` | Real-time AIS vessel positions |
| WeatherTidal | `/weather-tidal` | Weather and tidal conditions |
| Analytics | `/analytics` | Performance metrics and charts |
| AISuggestions | `/ai-suggestions` | AI-powered recommendations |
| OrToolsOptimization | `/optimization` | OR-Tools optimization engine |
| WhatIf | `/what-if` | What-if scenario analysis |
| ThreeDView | `/3d-view` | 3D port visualization |

### Shared Components

| Component | Purpose |
|-----------|---------|
| Layout | Main layout with header and sidebar |
| Header | Top navigation bar |
| Sidebar | Navigation menu with page links |
| DataTable | Reusable data table component |
| MetricCard | KPI card with gradient styling |
| StatusBadge | Color-coded status indicators |
| LoadingSpinner | Loading state indicator |

---

## Database Schema

**Database:** BerthPlanning | **Engine:** MS-SQL Server | **Tables:** 23

### Table Categories

| Category | Tables | Count |
|----------|--------|-------|
| **Port Hierarchy** | PORTS, TERMINALS, BERTHS | 3 |
| **Core** | VESSELS | 1 |
| **Operational** | VESSEL_SCHEDULE, RESOURCES, RESOURCE_ALLOCATION | 3 |
| **External Data** | WEATHER_DATA, TIDAL_DATA, AIS_DATA | 3 |
| **AI/ML** | CONFLICTS, OPTIMIZATION_RUNS, KNOWLEDGE_BASE | 3 |
| **Support** | VESSEL_HISTORY, BERTH_MAINTENANCE, ALERTS_NOTIFICATIONS, USER_PREFERENCES, AUDIT_LOG | 5 |
| **Navigation** | CHANNELS, ANCHORAGES, PILOTS, TUGBOATS, UKC_DATA | 5 |

### Creation Sequence (Dependency Tiers)

```
Tier 1 (Independent)  : PORTS, VESSELS, RESOURCES, TIDAL_DATA, OPTIMIZATION_RUNS,
                         KNOWLEDGE_BASE, ALERTS_NOTIFICATIONS, USER_PREFERENCES, AUDIT_LOG

Tier 2 (Depends on 1) : TERMINALS, WEATHER_DATA, ANCHORAGES, PILOTS, TUGBOATS, UKC_DATA, AIS_DATA

Tier 3 (Depends on 2) : BERTHS, CHANNELS

Tier 4 (Depends on 3) : VESSEL_SCHEDULE, VESSEL_HISTORY, BERTH_MAINTENANCE

Tier 5 (Depends on 4) : RESOURCE_ALLOCATION, CONFLICTS
```

### Foreign Key Map

```
PORTS (PortId, PortCode)
  |-- TERMINALS --> BERTHS --> VESSEL_SCHEDULE --> RESOURCE_ALLOCATION
  |                   |                       |-> CONFLICTS
  |                   |-- VESSEL_HISTORY
  |                   |-- BERTH_MAINTENANCE
  |-- WEATHER_DATA
  |-- ANCHORAGES --> CHANNELS
  |-- PILOTS (via PortCode)
  |-- TUGBOATS (via PortCode)
  |-- UKC_DATA

VESSELS
  |-- VESSEL_SCHEDULE
  |-- AIS_DATA
  |-- VESSEL_HISTORY

RESOURCES --> RESOURCE_ALLOCATION
```

### Schema Statistics

| Property | Count |
|----------|-------|
| Tables | 23 |
| Foreign Keys | 20 |
| Unique Constraints | 6 |
| CHECK Constraints | 25+ |
| Indexes | 48 |
| Views | 11 |
| Stored Procedures | 8 |

For full column-level documentation, see [Database_Schema_Documentation.md](documents/Database_Schema_Documentation.md).

### Seed Data Scripts (12 files)

| Order | Script | Data |
|-------|--------|------|
| 00 | 00_Cleanup.sql | Reset/cleanup |
| 01 | 01_SeedData_Port_Terminals.sql | Ports and terminals |
| 02 | 02_SeedData_Berths.sql | Berth configurations |
| 03 | 03_SeedData_Vessels.sql | Vessel master data |
| 04 | 04_SeedData_Channels_Anchorages.sql | Channels and anchorages |
| 05 | 05_SeedData_Pilots_Tugboats.sql | Pilots and tugboats |
| 06 | 06_SeedData_Resources.sql | Cranes, labor, mooring |
| 07 | 07_SeedData_Schedules.sql | Vessel schedules |
| 08 | 08_SeedData_Weather_Tidal.sql | Weather and tide data |
| 09 | 09_SeedData_History_Maintenance.sql | Historical visits, maintenance |
| 10 | 10_SeedData_UKC.sql | UKC calculations |
| -- | seed-data.json | JSON format seed data |

---

## Getting Started

### Prerequisites

- .NET 10.0 SDK
- Node.js 18+ and npm
- SQL Server (Express or higher)

### Step 1: Database Setup

```sql
-- Create database in SSMS
CREATE DATABASE BerthPlanning;
GO
```

Run scripts in order:
```
database_scripts/01_Create_Tables.sql
database_scripts/seeddata/00_Cleanup.sql
database_scripts/seeddata/01 through 10 (in order)
database_scripts/03_Create_Views.sql
database_scripts/04_Create_StoredProcedures.sql
```

### Step 2: Install Dependencies

```bash
install-dependencies.bat
```

Or manually:
```bash
# Backend
cd src/BerthPlanning.API
dotnet restore

# Frontend
cd frontend-react
npm install
```

### Step 3: Configure Connection String

Update `src/BerthPlanning.API/appsettings.json`:
```json
{
  "ConnectionStrings": {
    "BerthPlanningDb": "Server=localhost;Database=BerthPlanning;Trusted_Connection=True;TrustServerCertificate=True;"
  }
}
```

### Step 4: Run

```bash
# Both API and frontend
run.bat

# Or separately
run-api.bat        # API on https://localhost:5001
run-frontend.bat   # React on http://localhost:3000
```

### Step 5: Build & Publish

```bash
build.bat           # Build both
publish.bat         # Publish both
publish-api.bat     # Publish API only
publish-frontend.bat # Publish frontend only
```

---

## Batch Scripts

| Script | Purpose |
|--------|---------|
| `build.bat` | Builds API and React frontend |
| `run.bat` | Runs both API and frontend concurrently |
| `run-api.bat` | Runs API only |
| `run-frontend.bat` | Runs React frontend only |
| `install-dependencies.bat` | Installs npm and dotnet dependencies |
| `publish.bat` | Publishes both API and frontend |
| `publish-api.bat` | Publishes API only |
| `publish-frontend.bat` | Publishes React frontend only |

---

## Documentation

| Document | Location | Description |
|----------|----------|-------------|
| Project Specification | [documents/](documents/) | .docx and .pdf specification |
| ERD Documentation | [documents/ERD_Documentation.md](documents/ERD_Documentation.md) | Entity relationship details |
| Schema Documentation | [documents/Database_Schema_Documentation.md](documents/Database_Schema_Documentation.md) | Full column-level schema docs |
| ERD Diagram | [documents/berth_planning_erd.html](documents/berth_planning_erd.html) | Interactive ERD (open in browser) |
| SQL Scripts Guide | [database_scripts/README_SQL_Scripts.md](database_scripts/README_SQL_Scripts.md) | Database setup guide |
| AI Training Data | [documents/Data/](documents/Data/) | 12 Excel training datasets |

---

## Key Features

- **Real-time Dashboard** - KPIs, berth timeline, vessel queue, weather alerts
- **Vessel Scheduling** - ETA/ETD management with Gantt chart visualization
- **Berth Optimization** - Google OR-Tools based allocation optimization
- **Resource Management** - Pilots, tugboats, cranes, labor allocation
- **AIS Integration** - Real-time vessel tracking and position data
- **Weather & Tidal** - Condition monitoring with safety alerts
- **UKC Calculation** - Under Keel Clearance safety assessment
- **Conflict Detection** - Berth overlap, resource, tidal, and priority conflicts
- **What-If Analysis** - Scenario simulation for planning decisions
- **AI Suggestions** - ML-powered operational recommendations
- **Analytics** - Performance metrics, utilization reports, delay analysis
- **3D Port View** - Interactive 3D port visualization

---

**Project:** Berth Planning & Allocation Optimization
**For:** Kale Logistics Solutions Private Limited
**Version:** 4.0 | **Date:** February 2026
