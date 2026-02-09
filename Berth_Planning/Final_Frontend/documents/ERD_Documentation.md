# BERTH PLANNING & ALLOCATION OPTIMIZATION SYSTEM
## Entity Relationship Diagram (ERD) Documentation

---

## DATABASE SCHEMA OVERVIEW

This ERD represents the complete database structure for an AI-powered berth planning and allocation optimization system designed for maritime ports.

---

## ENTITY CATEGORIES

### 🟢 CORE ENTITIES (Green)
These are the fundamental business entities that form the heart of the system.

**1. VESSELS**
- **Purpose:** Store information about ships visiting the port
- **Key Attributes:**
  - VesselId (PK) - Unique identifier
  - VesselName - Name of the ship
  - IMO (UK) - International Maritime Organization number (unique globally)
  - MMSI - Maritime Mobile Service Identity
  - VesselType - Container, Bulk Carrier, Tanker, RoRo, etc.
  - LOA - Length Overall (meters)
  - Beam - Width of vessel (meters)
  - Draft - Depth below waterline (meters)
  - CargoType - Type of cargo being transported
  - CargoVolume - Volume of cargo
  - Priority - 1=High, 2=Medium, 3=Low (for scheduling priority)

**2. BERTHS**
- **Purpose:** Store information about berthing locations at the port
- **Key Attributes:**
  - BerthId (PK) - Unique identifier
  - BerthName - Name/identifier of the berth
  - BerthCode (UK) - Unique code for the berth
  - Length - Maximum vessel length the berth can accommodate
  - Depth - Water depth at berth (at high tide)
  - MaxDraft - Maximum vessel draft allowed
  - BerthType - Container, Bulk, General Cargo, etc.
  - NumberOfCranes - Cranes available at this berth
  - IsActive - Whether berth is currently operational
  - Latitude/Longitude - Geographic coordinates

---

### 🔵 OPERATIONAL DATA (Blue)
These entities manage the day-to-day operations and scheduling.

**3. VESSEL_SCHEDULE**
- **Purpose:** Central scheduling table linking vessels to berths with timing
- **Key Attributes:**
  - ScheduleId (PK) - Unique identifier
  - VesselId (FK) - Which vessel
  - BerthId (FK) - Which berth assigned
  - ETA - Estimated Time of Arrival (original estimate)
  - PredictedETA - AI-predicted ETA (from ETA Predictor Agent)
  - ETD - Estimated Time of Departure
  - ATA - Actual Time of Arrival (when vessel actually arrived)
  - ATB - Actual Time of Berthing (when vessel docked)
  - ATD - Actual Time of Departure (when vessel left)
  - Status - Scheduled, Approaching, Berthed, Departed, Cancelled
  - DwellTime - Expected time at berth in minutes
  - WaitingTime - Actual waiting time before berthing
  - OptimizationScore - Score from AI optimization
  - IsOptimized - Flag indicating if AI-optimized
  - ConflictCount - Number of conflicts detected

**4. RESOURCES**
- **Purpose:** Manage port resources (cranes, pilots, tugboats, labor)
- **Key Attributes:**
  - ResourceId (PK) - Unique identifier
  - ResourceType - Crane, Tugboat, Pilot, Labor
  - ResourceName - Specific name/identifier
  - Capacity - How many units available
  - IsAvailable - Current availability status
  - MaintenanceSchedule - When resource scheduled for maintenance

**5. RESOURCE_ALLOCATION**
- **Purpose:** Track which resources are assigned to which vessels
- **Key Attributes:**
  - AllocationId (PK) - Unique identifier
  - ScheduleId (FK) - Which vessel schedule
  - ResourceId (FK) - Which resource
  - AllocatedFrom - Start time of allocation
  - AllocatedTo - End time of allocation
  - Quantity - Number of units allocated (e.g., 2 cranes)
  - Status - Allocated, InUse, Released

---

### 🟠 EXTERNAL DATA (Orange)
These entities store data fetched from external APIs.

**6. WEATHER_DATA**
- **Purpose:** Store weather conditions from OpenWeatherMap/NOAA APIs
- **Key Attributes:**
  - WeatherId (PK) - Unique identifier
  - RecordedAt - Timestamp of weather reading
  - WindSpeed - km/h
  - WindDirection - Degrees (0-360)
  - Visibility - Meters
  - WaveHeight - Meters
  - Temperature - Celsius
  - Precipitation - Millimeters
  - WeatherCondition - Clear, Rain, Storm, Fog, etc.
  - IsAlert - Flag for severe weather alerts
  - FetchedAt - When data was retrieved from API

**7. TIDAL_DATA**
- **Purpose:** Store tidal information from NOAA/WorldTides APIs
- **Key Attributes:**
  - TidalId (PK) - Unique identifier
  - TideTime - When the tide occurs
  - TideType - HighTide or LowTide
  - Height - Water height in meters
  - **Usage:** Critical for scheduling deep-draft vessels that can only berth during high tide

**8. AIS_DATA**
- **Purpose:** Store vessel tracking data from AIS (Automatic Identification System) APIs
- **Key Attributes:**
  - AISId (PK) - Unique identifier
  - VesselId (FK) - Which vessel this data belongs to
  - MMSI - Maritime identifier
  - Latitude/Longitude - Current position
  - Speed - Knots
  - Course - Degrees (direction of travel)
  - Heading - Degrees (direction vessel is pointing)
  - NavigationStatus - UnderWay, AtAnchor, Moored, etc.
  - RecordedAt - GPS timestamp
  - FetchedAt - When we retrieved this data
  - **Update Frequency:** Every 5-15 minutes for approaching vessels

---

### 🟣 AI/ML ENTITIES (Purple)
These entities support AI agent operations and optimization.

**9. CONFLICTS**
- **Purpose:** Track scheduling conflicts detected by the Conflict Resolver Agent
- **Key Attributes:**
  - ConflictId (PK) - Unique identifier
  - ConflictType - BerthOverlap, ResourceUnavailable, TidalConstraint, PriorityViolation
  - ScheduleId1 (FK) - First conflicting schedule
  - ScheduleId2 (FK) - Second conflicting schedule
  - Description - Human-readable description
  - Severity - 1=Critical, 2=High, 3=Medium, 4=Low
  - Status - Detected, Resolved, Ignored
  - DetectedAt - When conflict was found
  - ResolvedAt - When conflict was resolved
  - Resolution (JSON) - How conflict was resolved

**10. OPTIMIZATION_RUNS**
- **Purpose:** Log all optimization executions for performance tracking
- **Key Attributes:**
  - RunId (PK) - Unique identifier
  - RunType - Initial, ReOptimization, ConflictResolution
  - Algorithm - GeneticAlgorithm, ReinforcementLearning, Greedy, etc.
  - InputParameters (JSON) - Parameters used for optimization
  - OutputResults (JSON) - Results of optimization
  - ExecutionTime - Milliseconds taken
  - ImprovementScore - Percentage improvement achieved
  - Status - Running, Completed, Failed
  - CreatedAt - Start time
  - CompletedAt - End time

**11. KNOWLEDGE_BASE**
- **Purpose:** Store documents for RAG (Retrieval Augmented Generation) system
- **Key Attributes:**
  - KnowledgeId (PK) - Unique identifier
  - DocumentType - HistoricalLog, PortManual, BestPractice, WeatherPattern
  - Title - Document title
  - Content - Full text content
  - Embedding (Vector) - Vector embedding for similarity search
  - Metadata (JSON) - Additional metadata (source, tags, etc.)
  - **Usage:** AI agents query this for historical patterns, rules, best practices

---

### ⚫ SUPPORT TABLES (Gray)
Supporting entities for additional functionality.

**12. VESSEL_HISTORY**
- **Purpose:** Track historical visits for each vessel to improve predictions
- **Key Attributes:**
  - HistoryId (PK) - Unique identifier
  - VesselId (FK) - Which vessel
  - BerthId (FK) - Which berth used
  - VisitDate - When vessel visited
  - ActualDwellTime - How long vessel stayed
  - ActualWaitingTime - How long vessel waited
  - ETAAccuracy - How accurate was the ETA prediction
  - Notes - Any special notes about the visit
  - **Usage:** ETA Predictor Agent uses this to learn patterns

**13. BERTH_MAINTENANCE**
- **Purpose:** Track maintenance schedules for berths
- **Key Attributes:**
  - MaintenanceId (PK) - Unique identifier
  - BerthId (FK) - Which berth
  - StartTime - Maintenance start
  - EndTime - Maintenance end
  - MaintenanceType - Routine, Emergency, Crane Repair, etc.
  - Status - Scheduled, InProgress, Completed, Cancelled
  - Description - Details of maintenance work
  - **Usage:** Berth Optimizer avoids scheduling during maintenance windows

**14. ALERTS_NOTIFICATIONS**
- **Purpose:** Manage system alerts and user notifications
- **Key Attributes:**
  - AlertId (PK) - Unique identifier
  - AlertType - ConflictDetected, WeatherWarning, DelayAlert, etc.
  - RelatedEntityId - ID of related entity (vessel, berth, etc.)
  - EntityType - Vessel, Berth, Schedule, etc.
  - Severity - Critical, High, Medium, Low
  - Message - Alert message
  - IsRead - Has user seen this alert
  - CreatedAt - When alert was created
  - ReadAt - When user acknowledged

**15. USER_PREFERENCES**
- **Purpose:** Store user-specific settings and preferences
- **Key Attributes:**
  - PreferenceId (PK) - Unique identifier
  - UserId - Which user
  - PreferenceKey - e.g., "DefaultView", "NotificationSettings"
  - PreferenceValue - JSON value of the preference
  - UpdatedAt - Last updated timestamp

**16. AUDIT_LOG**
- **Purpose:** Complete audit trail of all system changes
- **Key Attributes:**
  - LogId (PK) - Unique identifier
  - UserId - Who made the change
  - Action - Created, Updated, Deleted, Optimized
  - EntityType - Vessel, Schedule, Berth, etc.
  - EntityId - ID of affected entity
  - OldValue (JSON) - Previous value
  - NewValue (JSON) - New value
  - CreatedAt - When change occurred
  - **Usage:** Compliance, debugging, analytics

---

## KEY RELATIONSHIPS EXPLAINED

### Primary Relationships:

**1. VESSELS ← → VESSEL_SCHEDULE (One-to-Many)**
- One vessel can have multiple schedule entries
- Current schedule entry + historical schedules
- Example: "MV Atlantic Star" has 15 previous visits plus current scheduled visit

**2. BERTHS ← → VESSEL_SCHEDULE (One-to-Many)**
- One berth can host multiple vessels over time
- No time overlap allowed for same berth
- Example: "Berth 1" hosts Vessel A from 10:00-14:00, then Vessel B from 15:00-20:00

**3. VESSEL_SCHEDULE ← → RESOURCE_ALLOCATION (One-to-Many)**
- One vessel schedule requires multiple resources
- Example: Vessel schedule needs 2 cranes + 1 pilot + 2 tugboats

**4. RESOURCES ← → RESOURCE_ALLOCATION (One-to-Many)**
- One resource can be allocated to multiple vessels (at different times)
- Example: "Crane #1" serves Vessel A (10:00-14:00), then Vessel B (15:00-20:00)

**5. VESSELS ← → AIS_DATA (One-to-Many)**
- One vessel has many AIS position updates
- Creates a tracking history of vessel movement
- Example: "MV Pacific" has 288 AIS updates over last 24 hours (every 5 min)

**6. VESSEL_SCHEDULE ← → CONFLICTS (Many-to-Many via junction)**
- Schedule entries can be involved in conflicts
- Self-referencing relationship (Schedule conflicts with other Schedules)
- Example: Schedule #123 conflicts with Schedule #124 (berth overlap)

**7. VESSELS/BERTHS ← → VESSEL_HISTORY (Many-to-Many via junction)**
- Tracks which vessels visited which berths historically
- Used by AI for pattern learning
- Example: "MV Atlantic" has visited "Berth 2" 12 times in past year

**8. BERTHS ← → BERTH_MAINTENANCE (One-to-Many)**
- Track all maintenance events for each berth
- Example: "Berth 1" has 3 scheduled maintenance windows this month

### Standalone Tables (No Direct Relationships):

**WEATHER_DATA**
- Time-series data
- Queried by timestamp ranges
- No FK relationships

**TIDAL_DATA**
- Time-series data
- Queried by timestamp ranges
- No FK relationships

**OPTIMIZATION_RUNS**
- Historical log table
- References schedules via JSON, not FK
- No FK relationships

**KNOWLEDGE_BASE**
- Document storage for RAG
- Searched via vector similarity, not joins
- No FK relationships

---

## INDEXES REQUIRED FOR PERFORMANCE

### Critical Indexes:

**VESSELS:**
- PRIMARY KEY on VesselId
- UNIQUE INDEX on IMO
- INDEX on VesselType
- INDEX on Priority

**BERTHS:**
- PRIMARY KEY on BerthId
- UNIQUE INDEX on BerthCode
- INDEX on BerthType
- INDEX on IsActive

**VESSEL_SCHEDULE:**
- PRIMARY KEY on ScheduleId
- INDEX on VesselId (FK)
- INDEX on BerthId (FK)
- INDEX on Status
- COMPOSITE INDEX on (BerthId, ETA) - for timeline queries
- INDEX on ETA for date range queries

**RESOURCE_ALLOCATION:**
- PRIMARY KEY on AllocationId
- INDEX on ScheduleId (FK)
- INDEX on ResourceId (FK)
- COMPOSITE INDEX on (ResourceId, AllocatedFrom, AllocatedTo)

**AIS_DATA:**
- PRIMARY KEY on AISId
- COMPOSITE INDEX on (VesselId, RecordedAt DESC) - for latest position queries

**WEATHER_DATA:**
- PRIMARY KEY on WeatherId
- INDEX on RecordedAt DESC - for latest weather

**TIDAL_DATA:**
- PRIMARY KEY on TidalId
- INDEX on TideTime - for finding next high/low tide

**CONFLICTS:**
- PRIMARY KEY on ConflictId
- INDEX on Status
- INDEX on ScheduleId1 (FK)
- INDEX on ScheduleId2 (FK)

---

## DATA FLOW EXAMPLES

### Example 1: Vessel Arrival Process

1. **AIS_DATA** receives position updates every 5 minutes
2. **ETA Predictor Agent** queries:
   - AIS_DATA for current position/speed
   - WEATHER_DATA for weather conditions
   - VESSEL_HISTORY for this vessel's past performance
3. **Predicted ETA** saved to VESSEL_SCHEDULE.PredictedETA
4. **Berth Optimizer Agent** queries:
   - VESSEL_SCHEDULE for all pending vessels
   - BERTHS for available berths
   - TIDAL_DATA for tidal windows
   - BERTH_MAINTENANCE for unavailable berths
5. **Optimization result** creates/updates VESSEL_SCHEDULE entries
6. **OPTIMIZATION_RUNS** logs the optimization execution
7. **Resource Scheduler Agent** queries:
   - VESSEL_SCHEDULE for berth assignments
   - RESOURCES for available resources
8. **Resource allocations** saved to RESOURCE_ALLOCATION
9. **Conflict Resolver Agent** continuously monitors VESSEL_SCHEDULE
10. Any **conflicts detected** saved to CONFLICTS
11. **Alerts** created in ALERTS_NOTIFICATIONS
12. All **changes logged** to AUDIT_LOG

### Example 2: Knowledge Base Query (RAG)

User asks: "Which berths can handle Vessel X?"

1. Query **VESSELS** to get vessel dimensions (LOA, Beam, Draft)
2. Query **BERTHS** to find compatible berths (Length ≥ LOA, MaxDraft ≥ Draft)
3. Query **KNOWLEDGE_BASE** with vector similarity:
   - Find similar historical scenarios
   - Retrieve best practices for this vessel type
4. Query **TIDAL_DATA** to determine safe berthing windows
5. Query **VESSEL_SCHEDULE** to check berth availability
6. Query **RESOURCE_ALLOCATION** to verify resource availability
7. Return ranked list of suitable berths with reasoning

---

## DATABASE SIZE ESTIMATES (For Capacity Planning)

### Expected Data Volumes:

**VESSELS:** ~500-1,000 records (active vessels visiting port)
**BERTHS:** ~10-20 records (number of berths at port)
**VESSEL_SCHEDULE:** ~50,000-100,000 records/year
**RESOURCES:** ~50-100 records (cranes, pilots, tugboats)
**RESOURCE_ALLOCATION:** ~200,000-500,000 records/year
**AIS_DATA:** ~5-10 million records/year (high frequency updates)
**WEATHER_DATA:** ~35,000 records/year (hourly updates)
**TIDAL_DATA:** ~700 records/year (2 tides per day)
**CONFLICTS:** ~10,000-20,000 records/year
**OPTIMIZATION_RUNS:** ~3,000-5,000 records/year
**KNOWLEDGE_BASE:** ~1,000-5,000 documents
**VESSEL_HISTORY:** ~50,000 records/year
**AUDIT_LOG:** ~500,000-1,000,000 records/year (depending on audit scope)

### Storage Estimates:
- **Small Port:** 5-10 GB/year
- **Medium Port:** 20-50 GB/year
- **Large Port:** 100-200 GB/year

### Retention Policies:
- **AIS_DATA:** Keep 90 days, archive to cold storage
- **WEATHER_DATA:** Keep 1 year, archive to cold storage
- **AUDIT_LOG:** Keep 7 years (compliance)
- **VESSEL_SCHEDULE:** Keep all historical data
- **OPTIMIZATION_RUNS:** Keep 1 year active, archive older

---

## SECURITY CONSIDERATIONS

### Sensitive Data:
- **VESSELS:** Business-sensitive (cargo type, priority)
- **VESSEL_SCHEDULE:** Commercially sensitive (ETAs, berth assignments)
- **AUDIT_LOG:** Contains all system changes

### Access Control Recommendations:
- **Port Operators:** Full read/write on operational tables
- **Vessel Agents:** Read-only on their vessels
- **Analytics Team:** Read-only on all tables
- **AI Services:** Specific table access for each agent
- **Auditors:** Read-only on AUDIT_LOG

### Encryption:
- Encrypt at rest: AUDIT_LOG, USER_PREFERENCES
- Encrypt in transit: All API communications
- Hash sensitive fields: User passwords, API keys

---

## BACKUP & DISASTER RECOVERY

### Critical Tables (Priority 1 - Backup every hour):
- VESSEL_SCHEDULE
- RESOURCE_ALLOCATION
- CONFLICTS

### Important Tables (Priority 2 - Backup every 4 hours):
- VESSELS
- BERTHS
- RESOURCES
- AIS_DATA

### Historical Tables (Priority 3 - Daily backup):
- VESSEL_HISTORY
- OPTIMIZATION_RUNS
- AUDIT_LOG

### External Data (Priority 4 - Can be re-fetched):
- WEATHER_DATA
- TIDAL_DATA

---

## FUTURE ENHANCEMENTS

### Potential Additional Tables:

**BERTH_EQUIPMENT:**
- Track individual cranes, bollards, fenders
- Maintenance history per equipment
- Performance metrics

**CARGO_MANIFEST:**
- Detailed cargo information
- Container numbers
- Hazmat indicators

**PILOT_SCHEDULES:**
- Pilot assignments and availability
- Pilot certifications and restrictions

**PORT_CHARGES:**
- Billing information
- Berth usage fees
- Resource usage fees

**PERFORMANCE_METRICS:**
- Daily/weekly/monthly KPIs
- Berth efficiency scores
- Vessel turnaround times

**ML_MODELS:**
- Track different model versions
- A/B testing results
- Model performance metrics

---

## CONCLUSION

This ERD provides a comprehensive foundation for the Berth Planning & Allocation Optimization System with:

✅ Complete vessel and berth management
✅ Real-time scheduling and resource allocation
✅ External data integration (Weather, AIS, Tidal)
✅ AI/ML agent support (Optimization, Conflicts, Knowledge Base)
✅ Audit trail and historical analysis
✅ Scalability for small to large ports
✅ Performance-optimized with proper indexing

The schema balances normalization (reducing redundancy) with query performance (strategic denormalization where needed) to support both operational efficiency and analytical capabilities.
