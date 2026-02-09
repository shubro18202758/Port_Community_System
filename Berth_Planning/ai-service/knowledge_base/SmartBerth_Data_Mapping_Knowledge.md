# SmartBerth AI Data Mapping Knowledge
## Training Data Relationships & Operational Workflow Mapping

This document defines how SmartBerth AI training datasets map to operational phases and ML models.
It serves as the authoritative reference for data-driven decision making in the pipeline.

---

## 1. Training Dataset Inventory

| Dataset | Records | CSV File | Primary Use |
|---------|---------|----------|-------------|
| Port Parameters | 150 | SmartBerth_AI_Port_Parameters_Training_Data.csv | Port identification, location |
| Terminal Parameters | 653 | SmartBerth_AI_Terminal_Parameters_Training_Data.csv | Terminal matching, capacity |
| Berth Parameters | 2,848 | SmartBerth_AI_Berth_Parameters_Training_Data.csv | Berth allocation, compatibility |
| Channel Parameters | 543 | SmartBerth_AI_Channel_Parameters_Training_Data.csv | UKC calculation, navigation |
| Anchorage Parameters | 569 | SmartBerth_AI_Anchorage_Parameters_Training_Data.csv | Waiting management |
| Vessel Parameters | 3,000 | SmartBerth_AI_Vessel_Parameters_Training_Data.csv | Vessel identification, specs |
| UKC Training Data | 2,000 | SmartBerth_AI_UKC_Training_Data.csv | Transit safety calculations |
| Weather Parameters | 52,500 | SmartBerth_AI_Weather_Parameters_Training_Data.csv | ETA adjustment, safety |
| AIS Data | 125,349 | SmartBerth_AI_AIS_Parameters_Training_Data.csv | ETA prediction, tracking |
| Pilotage Parameters | 2,775 | SmartBerth_AI_Pilotage_Parameters_Training_Data.csv | Pilot assignment |
| Tugboat Parameters | 1,011 | SmartBerth_AI_Tugboat_Parameters_Training_Data.csv | Tug assignment |
| Vessel Call Data | 5,000 | SmartBerth_AI_Vessel_Call_Berth_Assignment_Training_Data.csv | ML ground truth |

**Total Records: 196,398**

---

## 2. Entity Relationship Hierarchy

### 2.1 Infrastructure Hierarchy
```
PORT (portId, portCode, portName)
  └── TERMINAL (terminalId, portId, terminalCode)
        └── BERTH (berthId, terminalId, berthCode)
  └── CHANNEL (channelId, portId, channelName)
  └── ANCHORAGE (anchorageId, portId, anchorageName)
  └── PILOT (pilotId, portId)
  └── TUGBOAT (tugId, portId)
```

### 2.2 Join Keys Reference

| Parent Entity | Child Entity | Join Key | Relationship |
|--------------|--------------|----------|--------------|
| Port | Terminal | portId | 1:N |
| Terminal | Berth | terminalId | 1:N |
| Port | Channel | portId | 1:N |
| Port | Anchorage | portId | 1:N |
| Port | Pilot | portId | 1:N |
| Port | Tugboat | portId | 1:N |
| Vessel | Vessel Call | imoNumber | 1:N |
| Vessel | AIS Record | vesselId/imoNumber | 1:N |
| Vessel Call | Pilot | callId | N:N |
| Vessel Call | Tugboat | callId | N:N |
| Vessel Call | Berth | berthId | N:1 |

---

## 3. Operational Phase Data Mapping

### Phase 1: Pre-Arrival Declaration (72-24 hrs before ETA)

**Step 1: Vessel Pre-Arrival Notification**
- Input: Vessel particulars (IMO, type, dimensions), ETA/ETD, Drafts, Voyage details
- Training Data Used:
  - `Vessel Parameters Dataset` → Vessel identification and specifications
  - `Vessel Call Dataset` → Historical call patterns
  - `Port Parameters Dataset` → Port identification and timezone

**Step 2: FAL Form Submission**
- Input: FAL 1-7 forms (General, Cargo, Crew, Dangerous Goods)
- Training Data Used:
  - `Vessel Call Dataset` → Call tracking
  - `Vessel Parameters Dataset` → Vessel validation

**Step 3: Service Requests**
- Input: Pilotage request, Tug assistance, Berth preference
- Training Data Used:
  - `Pilotage Parameters Dataset` → Pilot availability and certification
  - `Tugboat Parameters Dataset` → Tug capacity (bollard pull)
  - `Berth Parameters Dataset` → Berth compatibility check

### Phase 2: SmartBerth AI Processing

**Step 4-5: Data Ingestion (PCS/MSW + AIS)**
- Training Data Used:
  - `AIS Data Parameters Dataset` → Real-time vessel tracking
  - ML Application: ETA prediction refinement

**Step 6: Weather & Environmental Analysis**
- Training Data Used:
  - `Weather Parameters Dataset` → Wind, wave, visibility conditions
  - `UKC Training Dataset` → Tide-dependent clearance

**Step 7: UKC Calculation**
- Training Data Used:
  - `UKC Training Dataset` → Historical UKC calculations
  - `Channel Parameters Dataset` → Channel depth and restrictions
- Formula: UKC = Channel Depth - Vessel Draft - Squat - Tidal Adjustment

**Step 8: Berth Allocation Optimization**
- Training Data Used:
  - `Berth Parameters Dataset` → Physical constraints (length, depth, equipment)
  - `Terminal Parameters Dataset` → Terminal specialization
  - `Vessel Call Dataset` → Historical berth assignments
- ML Application: Optimal berth selection

**Step 9: Resource Scheduling**
- Training Data Used:
  - `Pilotage Parameters Dataset` → Pilot skills and availability
  - `Tugboat Parameters Dataset` → Tug specifications
  - `Vessel Call Dataset` → Historical resource usage
- ML Application: Resource optimization

### Phase 3: Confirmation & Notification
- Output: Berth plan, resource assignments
- Data flows to Terminal Operations System (TOS)

### Phase 4: Vessel Arrival & Operations

**Step 12: ATA Recording (Ground Truth)**
- Training Data Updated:
  - `Vessel Call Dataset` → ATA field
- ML Application: ETA model retraining

**Step 13: Berthing Sequence Recording**
- Training Data Updated:
  - `Vessel Call Dataset` → Berthing timestamps
- ML Application: Berthing duration prediction

**Step 14: Cargo Operations & Departure**
- Training Data Updated:
  - `Vessel Call Dataset` → Dwell time, ATD
- ML Application: Dwell time and ETD prediction

---

## 4. ML Model Data Requirements

### 4.1 ETA Prediction Model
| Input Feature | Source Dataset |
|--------------|----------------|
| Declared ETA | Vessel Call Dataset |
| AIS Position | AIS Data Parameters |
| Weather Conditions | Weather Parameters |
| Port Congestion | Vessel Call Dataset (queue analysis) |
| **Target** | ATA (Actual Time of Arrival) |

### 4.2 Berth Allocation Model
| Input Feature | Source Dataset |
|--------------|----------------|
| Vessel Dimensions | Vessel Parameters |
| Vessel Type | Vessel Parameters |
| Cargo Type | Vessel Call Dataset |
| Berth Availability | Berth Parameters |
| Terminal Capabilities | Terminal Parameters |
| **Target** | Optimal berthCode |

### 4.3 Dwell Time Prediction Model
| Input Feature | Source Dataset |
|--------------|----------------|
| Cargo Volume | Vessel Call Dataset |
| Berth Equipment | Berth Parameters |
| Weather Conditions | Weather Parameters |
| Historical Patterns | Vessel Call Dataset |
| **Target** | dwellTimeHours |

### 4.4 Resource Scheduling Model
| Input Feature | Source Dataset |
|--------------|----------------|
| Vessel Requirements | Vessel Parameters |
| Pilot Certifications | Pilotage Parameters |
| Tug Bollard Pull | Tugboat Parameters |
| Service Requests | Vessel Call Dataset |
| **Target** | Optimal pilot/tug assignment |

---

## 5. Query-to-Dataset Mapping

When processing queries, the AI should consult these datasets:

| Query Type | Primary Datasets | Secondary Datasets |
|-----------|-----------------|-------------------|
| "Find berth for vessel X" | Berth, Vessel, Terminal | Vessel Call (history) |
| "Calculate UKC" | UKC, Channel, Vessel | Weather, Tidal |
| "Pilot availability" | Pilotage, Port | Vessel Call |
| "Tug requirements" | Tugboat, Vessel | Port |
| "Weather impact" | Weather, UKC | Vessel Call |
| "Port resources" | Port, Terminal, Berth, Pilot, Tugboat | Anchorage, Channel |
| "Vessel history" | Vessel Call, AIS | Vessel |
| "ETA prediction" | AIS, Weather, Vessel Call | Port (congestion) |
| "Channel navigation" | Channel, UKC | Weather, Vessel |
| "Anchorage assignment" | Anchorage, Vessel | Weather |

---

## 6. Data Quality & Validation Rules

### Required Fields by Entity

**Vessel**: imoNumber (unique), vesselName, vesselType, loa, beam, draft
**Port**: portId (unique), portCode (5-letter UNLOCODE), portName
**Terminal**: terminalId (unique), portId (FK), terminalType
**Berth**: berthId (unique), terminalId (FK), length, depth, maxLOA, maxDraft
**Channel**: channelId, portId (FK), channelDepth, maxVesselLOA
**Pilot**: pilotId, portId (FK), certificationLevel, status
**Tugboat**: tugId, portId (FK), bollardPull, status

### Cross-Reference Validation
- Every terminalId in Berth must exist in Terminal
- Every portId in Terminal must exist in Port
- Every imoNumber in Vessel Call must exist in Vessel
- Every berthId in Vessel Call must exist in Berth

---

## 7. Real-Time Data Integration

| Data Source | Update Frequency | Integration Point |
|------------|------------------|-------------------|
| AIS Feed | Real-time (seconds) | ETA refinement |
| Weather API | 15 minutes | Safety assessment |
| Tidal Data | Hourly | UKC calculation |
| Vessel Calls | On event | Ground truth capture |
| Resource Status | On change | Availability check |

---

## 8. Summary Statistics

| Category | Record Count |
|----------|-------------|
| Infrastructure Data (Port, Terminal, Berth, Channel, Anchorage) | 4,763 |
| Vessel Data | 3,000 |
| Resource Data (Pilots, Tugboats) | 3,786 |
| Operational Data (UKC) | 2,000 |
| Time Series Data (Weather, AIS) | 177,849 |
| Historical Call Data | 5,000 |
| **TOTAL** | **196,398** |

---

*This document is the authoritative reference for SmartBerth AI data mapping and should be consulted for all data-driven operations.*
