# Knowledge Base Documentation - Berth Planning AI System

**Total Documents**: 50
**Last Updated**: 2026-02-04
**For**: Claude Opus 4.5 Multi-Agent RAG System

---

## Document Organization

### Port Operations Manuals (10 documents)
Located in: `port_manuals/`

1. **01_vessel_physical_dimensions_constraints.md** - LOA, beam, draft, air draft constraints
2. **02_cargo_type_compatibility_constraints.md** - Cargo matching, dangerous goods
3. **03_berth_physical_equipment_constraints.md** - Fender capacity, bollard SWL, cranes
4. **04_resource_availability_constraints.md** - Pilots, tugs, labor gangs
5. **05_tidal_weather_constraints.md** - Tidal windows, weather thresholds
6. **06_priority_commercial_constraints.md** - Vessel priorities, demurrage
7. **07_window_vessel_operations.md** - Window vessels, SLA management
8. **08_ukc_navigation_safety.md** - Under keel clearance, navigation safety
9. **09_berth_availability_maintenance.md** - Maintenance windows, buffer times
10. **10_constraint_decision_framework.md** - Master decision flowchart

### Historical Logs (20 documents)
Located in: `historical_logs/`

- Berth allocation patterns (2024 analysis)
- Resource utilization patterns (crane, pilot, tugboat analysis)
- Dwell time analysis by vessel type
- Waiting time patterns (hourly, seasonal)
- Seasonal demand patterns
- Vessel history performance (repeat customers)
- Berth maintenance patterns
- Conflict resolution history
- AIS tracking patterns
- Priority vessel analysis
- Optimization run case studies (8 documents)

### Weather Studies (10 documents)
Located in: `weather_studies/`

- Storm impact analysis (18 storm events, 2023-2024)
- Tidal window analysis (deep draft navigation)
- Fog visibility impact
- Seasonal weather patterns
- Weather factor studies (6 documents covering various severity levels)

### Best Practices (10 documents)
Located in: `best_practices/`

- PortCDM standards (international KPIs)
- Optimization techniques (BAP, OR-Tools, multi-factor scoring)
- Safety management system (hard constraints, UKC, DG segregation)
- Resource allocation strategy (crane, pilot, tugboat assignment)
- Berth assignment checklist (validation steps)
- Industry benchmark studies (5 documents comparing against world-class ports)

---

## Database Tables Referenced

All documents reference actual SQL Server tables from `BerthPlanningDB`:

### Core Tables
- **VESSELS** - Ship master data (VesselId, VesselName, VesselType, LOA, Draft, Beam, GT, DangerousGoods)
- **BERTHS** - Berth specifications (BerthId, BerthName, BerthType, Length, MaxDraft, NumberOfCranes, Exposure)
- **VESSEL_SCHEDULE** - Central scheduling (ScheduleId, VesselId, BerthId, ETA, ETD, ATA, ATB, ATD, Priority, Status, DwellTime, WaitingTime, PredictedETA)

### Operational Tables
- **RESOURCES** - Port resources (ResourceId, ResourceType, ResourceName, Capacity, BollardPull, Certifications, IsAvailable)
- **RESOURCE_ALLOCATION** - Resource assignments (AllocationId, ResourceId, ScheduleId, AllocatedFrom, AllocatedTo, Status)

### External Data Tables
- **WEATHER_DATA** - Weather conditions (WindSpeed, WaveHeight, Visibility, WeatherCondition, RecordedAt)
- **TIDAL_DATA** - Tidal schedules (TideDateTime, TideHeight, TideType)
- **AIS_DATA** - Vessel tracking (VesselId, Latitude, Longitude, Speed, Heading, RecordedAt)

### AI/ML Tables
- **CONFLICTS** - Detected conflicts (ConflictId, ConflictType, Severity, Description, DetectedAt, ResolvedAt)
- **OPTIMIZATION_RUNS** - Optimization history (OptimizationRunId, OptimizationDate, VesselsProcessed, ConflictsDetected)
- **KNOWLEDGE_BASE** - RAG documents (DocumentId, DocumentName, DocumentType, Content, Tags, CreatedAt)

### Support Tables
- **VESSEL_HISTORY** - Historical visits (VisitId, VesselId, BerthId, VisitDate, DwellTime, WaitingTime)
- **BERTH_MAINTENANCE** - Maintenance schedules (MaintenanceId, BerthId, MaintenanceType, ScheduledStart, ScheduledEnd, Status)
- **ALERTS_NOTIFICATIONS** - System alerts (AlertId, AlertType, Severity, Message, CreatedAt, Status)

---

## AI Agent Usage Patterns

### ETA Predictor Agent
**Recommended Documents**:
- storm_impact_analysis.md (weather delay factors)
- tidal_window_analysis.md (deep draft timing)
- ais_tracking_patterns.md (real-time position)
- seasonal_weather_patterns.md (seasonal factors)
- waiting_time_patterns.md (port congestion estimates)

**Query Example**: "What is the expected delay for a container vessel arriving during a storm with 35-knot winds?"

### Berth Optimizer Agent
**Recommended Documents**:
- berth_allocation_patterns_2024.md (historical preferences)
- optimization_techniques.md (scoring algorithms)
- berth_assignment_checklist.md (validation steps)
- port_manuals/10_constraint_decision_framework.md (master decision logic)

**Query Example**: "What is the optimal berth for a 280m container vessel with LOA considering crane availability?"

### Resource Scheduler Agent
**Recommended Documents**:
- resource_utilization_patterns.md (historical allocation data)
- resource_allocation_strategy.md (best practices)
- port_manuals/04_resource_availability_constraints.md (requirements)

**Query Example**: "How many tugboats are required for a 150,000 GT bulk carrier?"

### Conflict Resolver Agent
**Recommended Documents**:
- conflict_resolution_history.md (past resolutions)
- priority_vessel_analysis.md (priority rules)
- port_manuals/07_window_vessel_operations.md (window vessel handling)
- optimization_techniques.md (resolution strategies)

**Query Example**: "How should I resolve a conflict between a Priority 1 window vessel and a Priority 2 vessel at the same berth?"

---

## ChromaDB Collection Structure

**Collection Name**: `berth_knowledge`
**Embedding Model**: `all-MiniLM-L6-v2` (sentence-transformers)
**Chunk Size**: 500 tokens
**Chunk Overlap**: 50 tokens
**Expected Chunks**: ~200 (from 50 documents, ~100KB total)

### Metadata Fields
- `document_name`: Original filename
- `document_type`: Category (Port Manual, Historical Log, Weather Study, Best Practice)
- `source_table`: Primary database table referenced
- `chunk_index`: Position in document
- `created_at`: Timestamp

---

## Neo4j Graph Integration

**Complementary to ChromaDB**: Use Neo4j for relationship queries, ChromaDB for semantic search.

### Graph Schema
- **(Vessel)-[:SCHEDULED_FOR]->(Schedule)**
- **(Schedule)-[:ASSIGNED_TO]->(Berth)**
- **(Berth)-[:HAS_EQUIPMENT]->(Crane)**
- **(Schedule)-[:REQUIRES]->(Resource)**
- **(Schedule)-[:CONFLICTS_WITH]->(Schedule)**

### Query Router Logic
```python
# Route to Neo4j for relationship queries
if "conflict" in query or "cascade" in query or "impact of" in query:
    return neo4j_query_engine

# Route to ChromaDB for semantic search
else:
    return chroma_retriever
```

---

## Document Update Protocol

1. **Add new documents**: Place in appropriate subdirectory
2. **Update KNOWLEDGE_BASE table**: Insert metadata into SQL Server
3. **Re-embed**: Run document loader to regenerate ChromaDB collection
4. **Version control**: Track changes in git

---

## Performance Targets

- **Query latency**: <500ms (ChromaDB retrieval + Claude synthesis)
- **Retrieval accuracy**: Top-5 relevance >90%
- **Coverage**: Answer 95% of operational queries
- **Freshness**: Update weekly with new operational data

---

**For AI Agents**: This knowledge base provides comprehensive context for berth allocation decisions. Always cite specific document names and constraint IDs (e.g., "V-DIM-001 from 01_vessel_physical_dimensions_constraints.md") in responses to users.
