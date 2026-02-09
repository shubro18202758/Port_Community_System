# SmartBerth AI  
## Berth Planning & Optimization Module  

### Data Flow Architecture  
**PCS/MSW Integration & Training Data Mapping**

---

**Document Version:** 1.0  
**Date:** February 2026  
**Classification:** Technical Architecture Document  

**Prepared For:**  
Terminal Operators, Port Authorities, Shipping Agents  

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)  
   1.1 [Key Stakeholders](#11-key-stakeholders)  
2. [System Architecture Overview](#2-system-architecture-overview)  
   2.1 [System Components](#21-system-components)  
3. [Complete Data Flow Sequence](#3-complete-data-flow-sequence)  
   - 3.1 Phase 1: Pre-Arrival Declaration  
   - 3.2 Phase 2: SmartBerth AI Processing & Optimization  
   - 3.3 Phase 3: Confirmation & Notification to Terminal  
   - 3.4 Phase 4: Vessel Arrival & Operations  
   - 3.5 Phase 5: Status Display to Shipping Agent  
4. [Complete Training Dataset Summary](#4-complete-training-dataset-summary)  
5. [Data Relationships & Entity Mapping](#5-data-relationships--entity-mapping)  
6. [ML Model Data Requirements](#6-ml-model-data-requirements)  
7. [Conclusion](#7-conclusion)  

---

## 1. Executive Summary

This document describes the complete data flow architecture for the **SmartBerth AI Berth Planning and Optimization Module**. It explains how data moves from **Port Community Systems (PCS)** and **Maritime Single Window (MSW)** platforms to terminal operators and back to shipping agents.

SmartBerth integrates with existing port digital infrastructure to optimize berth allocation, predict vessel arrival times, and streamline cargo operations. The document maps relationships between all training datasets and their role in the operational workflow.

---

## 1.1 Key Stakeholders

| Stakeholder | Role | System Interaction |
|------------|-----|-------------------|
| Shipping Agent | Declares vessel ETA, cargo, crew details | PCS/MSW data entry & status viewing |
| Terminal Operator | Manages berths, cranes, cargo operations | SmartBerth planning interface |
| Port Authority | Oversees port ops, VTS, pilotage | PCS admin & resource allocation |
| Pilot Service | Vessel navigation | Pilot scheduling system |
| Tug Operator | Berthing assistance | Tug dispatch system |
| Customs / Immigration | Clearance processing | MSW integration |

---

## 2. System Architecture Overview

SmartBerth operates as an intelligent AI layer between PCS/MSW platforms and terminal operations, consuming multi-source data and producing optimized berth and resource plans.

### 2.1 System Components

| Component | Description |
|---------|-------------|
| PCS | Stakeholder communication & vessel declarations |
| MSW | Regulatory submissions (FAL forms, customs) |
| SmartBerth Core | AI-powered berth planning & optimization |
| AIS Integration | Real-time vessel tracking |
| VTS | Traffic & channel management |
| TOS | Terminal-level cargo and yard operations |

---

## 3. Complete Data Flow Sequence

### 3.1 Phase 1: Pre-Arrival Declaration (72–24 hrs before ETA)

**Initiated by:** Shipping Agent  

#### Step 1: Vessel Pre-Arrival Notification
Declared via PCS/MSW:
- Vessel particulars (IMO, type, dimensions)
- ETA / ETD
- Drafts
- Voyage & port details

**Training Data Mapping**
- Vessel Parameters Dataset  
- Vessel Call Dataset  
- Port Parameters Dataset  

---

#### Step 2: FAL Form Submission
FAL 1–7 via MSW (General, Cargo, Crew, DG, etc.)

**Training Data Mapping**
- Vessel Call Dataset  
- Vessel Parameters Dataset  

---

#### Step 3: Service Requests
- Pilotage
- Tug assistance
- Berth preference
- Special requirements

**Training Data Mapping**
- Pilotage Parameters Dataset  
- Tugboat Parameters Dataset  
- Berth Parameters Dataset  

---

### 3.2 Phase 2: SmartBerth AI Processing & Optimization

#### Step 4: PCS/MSW Data Ingestion  
#### Step 5: AIS Data Integration  

**Training Data Mapping**
- AIS Data Parameters Dataset  
- *ML:* ETA prediction refinement  

---

#### Step 6: Weather & Environmental Data

**Training Data Mapping**
- Weather Parameters Dataset  
- UKC Training Dataset  

---

#### Step 7: UKC Calculation

**Training Data Mapping**
- UKC Training Dataset  
- Channel Parameters Dataset  

---

#### Step 8: Berth Allocation Optimization

**Training Data Mapping**
- Berth Parameters Dataset  
- Terminal Parameters Dataset  
- Vessel Call Dataset  

---

#### Step 9: Resource Scheduling (Pilots & Tugs)

**Training Data Mapping**
- Pilotage Parameters Dataset  
- Tugboat Parameters Dataset  
- Vessel Call Dataset  

---

### 3.3 Phase 3: Confirmation & Notification to Terminal

#### Step 10: Berth Plan Publication  
#### Step 11: Terminal Operations Preparation  

---

### 3.4 Phase 4: Vessel Arrival & Operations

#### Step 12: ATA Recording (Ground Truth)

**Training Data Mapping**
- Vessel Call Dataset  
- *ML:* ETA model retraining  

---

#### Step 13: Berthing Sequence Recording

**Training Data Mapping**
- Vessel Call Dataset  
- *ML:* Berthing duration prediction  

---

#### Step 14: Cargo Operations & Departure

**Training Data Mapping**
- Vessel Call Dataset  
- *ML:* Dwell time & ETD prediction  

---

### 3.5 Phase 5: Status Display to Shipping Agent

| Category | Information | Update Frequency |
|--------|------------|------------------|
| Vessel Position | AIS map view | Real-time |
| ETA Status | Predicted ATA & variance | 15 mins |
| Berth Allocation | Assigned berth | On change |
| Service Status | Pilot/tugs | On change |
| Operations | Cargo progress | 30 mins |
| Alerts | Delays, weather | Immediate |

---

## 4. Complete Training Dataset Summary

| Dataset | Records | Primary Use |
|-------|--------|------------|
| Port Parameters | 150 | Port identification |
| Terminal Parameters | 653 | Terminal matching |
| Berth Parameters | 2,848 | Berth allocation |
| Channel Parameters | 543 | UKC calculation |
| Anchorage Parameters | 569 | Waiting management |
| Vessel Parameters | 3,000 | Vessel ID |
| UKC Training Data | 2,000 | Transit safety |
| Weather Parameters | 52,500 | ETA adjustment |
| AIS Data | 125,349 | ETA prediction |
| Pilotage Parameters | 2,775 | Pilot assignment |
| Tugboat Parameters | 1,011 | Tug assignment |
| Vessel Call Data | 5,000 | ML ground truth |

---

## 5. Data Relationships & Entity Mapping

| Parent | Relationship | Child | Join Key |
|------|--------------|------|---------|
| Port | 1:N | Terminal | portId |
| Terminal | 1:N | Berth | terminalId |
| Vessel | 1:N | Vessel Call | imoNumber |
| Vessel | 1:N | AIS Record | vesselId |
| Vessel Call | N:N | Pilot | callId |
| Vessel Call | N:N | Tugboat | callId |

---

## 6. ML Model Data Requirements

### 6.1 ETA Prediction Model
- **Inputs:** ETA, AIS, weather, congestion  
- **Target:** ATA  
- **Training Data:** AIS + Vessel Calls + Weather  

### 6.2 Berth Allocation Model
- **Target:** Optimal berthCode  
- **Training Data:** Berth + Vessel + Calls  

### 6.3 Dwell Time Prediction
- **Target:** dwellTimeHours  
- **Training Data:** Calls + Berths + Weather  

### 6.4 Resource Scheduling Model
- **Target:** Optimal pilot/tug assignment  
- **Training Data:** Pilot + Tug + Calls  

---

## 7. Conclusion

SmartBerth AI delivers an end-to-end intelligent berth planning system by:

1. Ingesting declarations from PCS/MSW  
2. Enhancing predictions using AIS & weather  
3. Optimizing berth and resource allocation  
4. Providing real-time operational visibility  
5. Capturing ground truth for continuous ML improvement  

### 7.1 Total Training Data Generated

| Category | Records |
|-------|--------|
| Infrastructure Data | 4,763 |
| Vessel Data | 3,000 |
| Resource Data | 3,786 |
| Operational Data | 2,000 |
| Time Series Data | 177,849 |
| Historical Call Data | 5,000 |
| **TOTAL** | **196,398** |

---

**— End of Document —**
