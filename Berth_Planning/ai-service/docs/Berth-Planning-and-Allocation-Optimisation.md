# PRODUCT REQUIREMENT DOCUMENT

# BERTH PLANNING AND ALLOCATION OPTIMISATION

| Date | Author | Version | Affected Module |
|------|--------|---------|-----------------|
| 29/01/26 | Niraj Kumar | 1.0 | Berthing |

## Team Member(s)

| Name | Role |
|------|------|
| Dipesh Pansuriya | Team Lead -- Developer |
| Ankur Rai | Developer |
| Sayandeep Haldar | Developer |
| Niraj Kumar | Product Manager |

## Reviewer(s)

| Name | Role | Sign Off Date |
|------|------|---------------|
| Shruti Pandit | Mentor -- AI/ML | |

---

## PROBLEM DEFINITION

Ports handle multiple vessel calls each day, with every vessel having unique characteristics such as estimated arrival time, cargo volume, service priority, and berth requirements. Current berth planning practices are often **manual or rule-based**, making them highly sensitive to delays caused by weather conditions, tidal variations, or operational constraints.

Even minor deviations in vessel arrival times can result in:

- Berth congestion
- Increased vessel waiting and idling time
- Sub-optimal utilization of berth infrastructure
- Reduced port throughput and operational inefficiencies

There is a need for an **intelligent, data-driven berth planning system** that can accurately predict vessel arrival times and dynamically optimize berth allocation to ensure efficient port operations.

## PROBLEM STATEMENT

How can Artificial Intelligence be used to **predict vessel arrival times** and **optimise berth allocation** in order to:

- Minimise vessel waiting time at anchorage
- Improve vessel turnaround time (TAT)
- Increase overall port throughput and berth utilisation?

## OBJECTIVE OF SMARTBERTH AI

**SmartBerth AI** is an AI-powered berth planning and allocation system that enables Terminal Operators to:

- Proactively plan berth schedules based on predicted ETAs
- Dynamically re-optimise berth allocation in response to delays and disruptions
- Improve operational efficiency and decision-making through data-driven recommendations

| Supporting Document | URL |
|---------------------|-----|
| Data_Flow_Architecture | [SmartBerth_Data_Flow_Architecture.docx](https://kalelogistics-my.sharepoint.com/:w:/g/personal/niraj_kumar_kalelogistics_com1/IQBpH4fY84g0SosIfjMnxZ6yASHuXPVadGuA1YxPgSGy7N0?e=f0NW5z) |
| Synthetic Data | [SmartBerth AI - Synthetic Data (1).xlsx](https://kalelogistics-my.sharepoint.com/:x:/g/personal/niraj_kumar_kalelogistics_com1/IQDg3V_82FFUTLcTsMT0VsTAAZye8FTnR1wXrOyVpptJfu4?e=YIteuI) |

---

## SmartBerth AI -- AI Use Cases

### 1. Vessel Arrival & Readiness Intelligence

#### 1.1 Predictive ETA Calculation

AI predicts actual vessel arrival time instead of relying on declared ETA.

**Data Points**

- Historical arrival/departure data
- AIS movement patterns
- Weather & tidal data
- Port congestion patterns

#### 1.2 Arrival Deviation Detection

AI continuously compares:

Planned ETA vs Predicted ETA vs Actual movement

**Use Case**

- Early detection of delays (6--24 hrs before arrival)
- Automatic alert to planners

#### 1.3 Vessel Readiness Prediction

AI predicts whether a vessel is *berth ready*.

**Factors**

- Pilot/Tug availability
- Tidal window
- Previous port departure delays
- Regulatory clearance readiness (high-level)

### 2. Berth Allocation, Dynamic Re-Planning

#### 2.1 Constraint-Based Berth Allocation

AI matches vessels to berths using operational constraints:

**Constraints**

- Vessel LOA / beam / draft
- Cargo type compatibility
- Berth equipment availability
- Tidal restrictions

#### 2.2 Real-Time Re-Optimisation

When delays occur, AI:

- Re-calculates berth schedules
- Minimizes cascading impact on other vessels

#### 2.3 Conflict Detection & Resolution

AI detects:

- Berth overlaps
- Resource clashes
- Tidal window conflicts

Then auto-suggests resolutions, not just alerts.

### 3. What-If Simulation & Decision Support

#### 3.1 Delay Impact

Planner asks:

"What happens if Vessel AAA arrives 8 hours late?"

AI simulates:

- Impact on waiting times
- Berth utilisation
- Downstream vessel delays

#### 3.2 Capacity Management

AI simulates:

- Surge in arrivals
- Berth closure (maintenance)
- Weather disruption scenarios

---

## USERS & PERSONAS

### Primary User(s)

**Terminal Operator(s)**

- Responsible for berth scheduling and vessel sequencing
- Needs advance visibility and quick re-planning during disruptions

### Secondary User(s)

- Port Operator(s) -- monitors throughput & KPIs

---

## SmartBerth AI -- UML, ERD, RAG Mapping Diagrams

*Note: The document contains multiple diagrams (image1.png through image11.png) showing UML, ERD, and RAG mapping visualizations.*

---

## FUNCTIONAL REQUIREMENTS

### 1. Predictive ETA Model

**FR-ETA-01**  
System shall compute Predicted ETA for each vessel call using:

- Historical arrival/departure data
- AIS movement data
- Weather & tidal data
- Port congestion indicators

**FR-ETA-02**  
System shall update Predicted ETA dynamically as new AIS or weather data arrives.

**FR-ETA-03**  
System shall calculate and expose:

- Expected delay (minutes)
- ETA confidence score (0--100%)

**FR-ETA-04**  
System shall store both planned ETA and predicted ETA for comparison and audit.

#### UI Requirements

**FR-ETA-UI-01**  
UI shall display Planned ETA vs Predicted ETA side by side per vessel.

**FR-ETA-UI-02**  
UI shall visually highlight ETA deviation using:

- Green: < 1 day
- Amber: 1--4 days
- Red: > 4 days

**FR-ETA-UI-03**  
UI shall show confidence indicator (progress bar or badge).

**FR-ETA-UI-04**  
UI shall provide a hover/click explanation:

"ETA adjusted due to congestion and adverse tidal window."

#### Accuracy & Acceptance Criteria

- ETA prediction accuracy within ±10--15% acceptable (hackathon benchmark)
- Directional correctness (early/late) > 80%
- Confidence score must correlate with historical variance

### 2. Arrival Deviation Detection

**FR-DEV-01**  
System shall continuously compare:

- Planned ETA
- Predicted ETA
- AIS-based ETA

**FR-DEV-02**  
System shall detect ETA deviation at least 24 hours in advance.

**FR-DEV-03**  
System shall classify deviation severity:

- Low
- Medium
- High

**FR-DEV-04**  
System shall trigger alerts when deviation exceeds configured thresholds.

#### UI Requirements

**FR-DEV-UI-01**  
UI shall show **deviation alerts** in a real-time notification panel.

**FR-DEV-UI-02**  
UI shall show:

- Deviation magnitude
- Affected downstream vessels count

**FR-DEV-UI-03**  
Alerts shall be actionable (click → jump to berth plan impact).

#### Accuracy & Acceptance Criteria

- False positive rate < **20%**
- Detection lead time ≥ **6 hours**
- Severity classification matches delay magnitude ≥ **85%**

### 3. Vessel Readiness Prediction

**FR-READY-01**  
System shall predict whether a vessel is berth-ready at predicted ETA.

**FR-READY-02**  
Readiness decision shall consider:

- Pilot availability
- Tug availability
- Tidal window
- High-level regulatory readiness

**FR-READY-03**  
System shall output readiness reason codes.

#### UI Requirements

**FR-READY-UI-01**  
UI shall show readiness status using:

- Ready
- At Risk
- Not Ready

**FR-READY-UI-02**  
UI shall list readiness blockers (e.g., "Pilot unavailable").

**FR-READY-UI-03**  
Readiness status shall be visible **before berth allocation**.

#### Accuracy & Acceptance Criteria

- Readiness prediction precision ≥ **80%**
- False "Ready" predictions < **10%**
- Explanations mandatory for "Not Ready"

### 4. Constraint Model

**FR-CON-01**  
System shall validate **hard constraints** before optimization:

- LOA / beam / draft
- Cargo compatibility
- Equipment availability
- Tidal restrictions

**FR-CON-02**  
System shall identify and log constraint violations.

**FR-CON-03**  
System shall output **feasible berth--vessel combinations** only.

#### UI Requirements

**FR-CON-UI-01**  
UI shall visually block invalid berth selections.

**FR-CON-UI-02**  
UI shall show constraint failure reasons on hover:

"Draft exceeds berth limit."

**FR-CON-UI-03**  
Constraint validation results shall be shown before optimization.

#### Accuracy & Acceptance Criteria

- Zero invalid berth assignments allowed
- 100% hard constraint enforcement
- Soft constraints must be clearly labelled

> Refer to this for details of Constraints: [SmartBerth AI -- Berth Allocation Constraint Framework.docx](https://kalelogistics-my.sharepoint.com/:w:/g/personal/niraj_kumar_kalelogistics_com1/IQAtlHN2bk1ISrkfMI9tfWEgAeSTs7RV-CpAsFeMEP9MPlw?e=AkxPsO)

### 5. Berth Allocation Optimisation

**FR-ALLOC-01**  
System shall assign berths only from constraint-approved options.

**FR-ALLOC-02**  
System shall optimize for:

- Minimal vessel waiting time
- Maximum berth utilization
- Reduced idle time

**FR-ALLOC-03**  
System shall generate ranked alternative allocations.

#### UI Requirements

**FR-ALLOC-UI-01**  
UI shall display berth schedule as:

- Timeline / Gantt view

**FR-ALLOC-UI-02**  
UI shall allow manual override with impact preview.

**FR-ALLOC-UI-03**  
UI shall show optimization rationale on selection.

#### Accuracy & Acceptance Criteria

- Waiting time reduction ≥ **15--25%** (demo target)
- No constraint violations
- Optimisation runs < **5 seconds** (demo-scale)

### 6. Real-Time Re-Optimisation

**FR-REOPT-01**  
System shall trigger re-optimization on:

- ETA deviation
- Resource unavailability
- Weather restriction

**FR-REOPT-02**  
System shall minimize cascading impact on other vessels.

#### Frontend / UI Functional Requirements

**FR-REOPT-UI-01**  
UI shall show **Before vs After** berth plans.

**FR-REOPT-UI-02**  
UI shall highlight changed vessels only.

**FR-REOPT-UI-03**  
Operator approval shall be required before applying changes.

#### Accuracy & Acceptance Criteria

- Cascading delays reduced ≥ **20%**
- Re-optimization response time < **10 seconds**
- Operators override supported

### 7. Conflict Detection & Resolution

**FR-CONF-01**  
System shall detect:

- Berth overlaps
- Resource clashes
- Tidal window conflicts

**FR-CONF-02**  
System shall generate multiple resolution options.

#### Frontend / UI Functional Requirements

**FR-CONF-UI-01**  
UI shall visually mark conflicts on berth timeline.

**FR-CONF-UI-02**  
UI shall show ranked resolution options with trade-offs.

**FR-CONF-UI-03**  
Resolution explanation must be visible.

#### Accuracy & Acceptance Criteria

- 100% conflict detection
- At least 2 valid resolution options per conflict
- Ranking logic transparent

### 8. Capacity Impact Forecast

**FR-CAP-01**  
System shall calculate throughput and utilization from current plan.

**FR-CAP-02**  
System shall expose congestion risk indicators.

#### UI Requirements

**FR-CAP-UI-01**  
UI shall show KPIs:

- Throughput
- Avg waiting time
- Berth utilization %

**FR-CAP-UI-02**  
UI shall display trend indicators (↑ ↓).

#### Accuracy & Acceptance Criteria

- KPI calculations consistent with berth assignments
- No manual data correction required

### 9. RAG Explainability

**FR-RAG-01**  
System shall generate natural-language explanations for:

- ETA changes
- Allocation decisions
- Conflict resolutions

**FR-RAG-02**  
RAG shall only explain, never decide.

#### UI Requirements

**FR-RAG-UI-01**  
UI shall display explanations inline or via tooltip.

**FR-RAG-UI-02**  
UI shall show source reference (policy / history).

#### Acceptance Criteria

- Every AI decision must have an explanation
- Explanation latency < **2 seconds**

### 10. SmartBerth AI Conversational Assistant

#### Chatbot Scope & Purpose

The SmartBerth AI Chatbot acts as a conversational interface for terminal and port operators to:

- Query vessel queue status based on ETA
- Retrieve real-time vessels, berth, and readiness information
- Understand AI-driven berth allocation decisions
- Assess impact of delays and re-optimization outcomes
- Reduce dependency on manual dashboard navigation

#### FR-BOT-01: Vessel Queue Intelligence

System shall allow querying vessel queue ordered by:

- Predicted ETA
- Berth readiness
- Allocation status

**Example Queries**

- "Which vessels are arriving in the next 12 hours?"
- "Show vessels waiting for berth allocation."

**Data Sources**

- Predictive ETA Model
- Readiness Model
- Allocation Engine

#### FR-BOT-02: Vessel-Centric Query Resolution

System shall provide full vessel-level details:

- Planned ETA vs Predicted ETA
- Assigned berth (if any)
- Readiness status and blockers
- Expected berthing time

**Example Queries**

- "Tell me the status of Vessel MAERSK X."
- "Why is Vessel ABC still waiting?"

#### FR-BOT-03: Berth-Centric Query Resolution

System shall answer berth-related questions:

- Current berth occupancy
- Upcoming vessel assignments
- Idle time windows

**Example Queries**

- "Which vessel is at Berth 3 right now?"
- "When will Berth 5 be free?"

#### FR-BOT-04: AI Decision Explainability via RAG

System shall generate natural-language explanations using RAG for:

- ETA adjustments
- Berth assignment decisions
- Conflict resolution actions

**Example Queries**

- "Why was Vessel XYZ moved to Berth 2?"
- "Why did the ETA change?"

**RAG Sources**

- Historical berth plans
- Port operating rules
- Model output logs
- Domain knowledge corpus

#### FR-BOT-05: Delay Impact & Re-Optimisation Insights

System shall answer impact-related questions derived from:

- Real-time re-optimization results
- Cascading impact analysis

**Example Queries**

- "What is the impact if Vessel AAA is delayed by 6 hours?"
- "Which vessels are affected by today's weather delay?"

#### FR-BOT-06: Constraint Awareness in Responses

System shall ensure chatbot responses respect:

- Physical constraints
- Operational constraints

**Example**

"Vessel cannot be moved to Berth 4 due to draft limitation."

Bot must never suggest infeasible options.

#### FR-BOT-07: Confidence & Accuracy Disclosure

System shall provide:

- ETA confidence score
- Readiness and confidence
- Optimisation confidence (where applicable)

**Example**

"Predicted ETA confidence: 87%."

#### UI Requirements

**FR-BOT-UI-01: Context-Aware Chat Interface**

UI shall provide:

- Docked chatbot panel within SmartBerth UI
- Access to current port context (selected date, terminal)

**FR-BOT-UI-02: Structured + Conversational Responses**

Chatbot responses shall include:

- Human-readable text
- Structured cards (vessel summary, berth card)
- Action buttons (View in Timeline, Open Vessel Details)

**FR-BOT-UI-03: Click-Through Navigation**

User shall be able to:

- Click vessel name → open vessel detail page
- Click berth → jump to berth schedule view

**FR-BOT-UI-04: Alert-Aware Conversations**

When critical alerts exist:

- Bot shall proactively surface them in responses

**Example**

"2 vessels arriving in the next day are not berth-ready."

**FR-BOT-UI-05: Role-Based Response Depth**

- Terminal Operator → operational details
- Port Operator → summary & KPIs

#### NLP & Query Handling Requirements

**FR-BOT-NLP-01**

System shall support:

- Natural language queries
- Partial vessel names
- Time-relative queries ("next 6 hours", "today")

**FR-BOT-NLP-02**

System shall handle ambiguity by:

- Asking clarifying follow-up questions
- Presenting top-matched vessels

#### RAG Architecture -- Chatbot Specific

**Context Sources**

- Vessel master data
- Real-time model outputs (ETA, readiness, allocation)
- Constraint rules
- Historical decisions
- Port SOPs

**RAG Flow**

1. User query parsed
2. Relevant entities identified (vessel, berth, time window)
3. Context retrieved from structured DB + vector store
4. Response generated with factual grounding
5. Explanation attached where applicable

#### SmartBerth AI Chatbot -- Plot & Monitoring

**PLOT-01: Demand Over Time**

**Purpose**

- Monitoring incoming vessel demand
- Identify peak arrival windows
- Support berth capacity planning

**Derived From**

- Predicted ETA Model
- Vessel queue data
- Historical arrival patterns

**User Queries**

- "Show vessel demand for the next 48 hours."
- "Arrival trend for today vs yesterday."

**Visual**

- Time-series line / area chart
- X-axis: Time
- Y-axis: Number of vessels / GT / LOA aggregate

**Frontend Behavior**

- Clickable data points → open vessel list
- Toggle: Planned vs Predicted arrivals

**PLOT-02: Latency (Operational & System)**

**Purpose**

- Detect delays between prediction and action
- Monitor system responsiveness

**Types of Latency**

1. **Operational latency**
   - ETA prediction → actual arrival delta

2. **System latency**
   - Model inference time
   - Optimisation runtime
   - Chatbot response time

**User Queries**

- "Show ETA prediction latency."
- "System latency in the last 24 hours."

**Visual**

- Line chart or histogram
- Threshold markers (SLA breaches)

**PLOT-03: Traffic Load Patterns**

**Purpose**

- Monitor congestion trends
- Identify stress points across berths and time windows

**Derived From**

- Berth assignments
- Vessel queue length
- Utilization metrics

**User Queries**

- "Traffic load by berth."
- "Congestion pattern for night shifts."

**Visual**

- Heatmap
- X-axis: Time slots
- Y-axis: Berths
- Color intensity: Load / occupancy

**PLOT-04: Model Performance Drift**

**Purpose**

- Detect AI degradation early
- Maintain trust in predictions

**Models Covered**

- ETA Prediction Model
- Readiness Prediction Model
- Constraint Feasibility Model

**Metrics**

- Prediction error (MAE / RMSE)
- Confidence calibration drift
- Feature distribution drift

**User Queries**

- "Is the ETA model performing well?"
- "Any drift detected this week?"

**Visual**

- Trend lines with baseline
- Alert markers for drift thresholds

#### Chatbot Interaction Pattern for Plots

**FR-BOT-PLOT-01: Natural Language Plot Requests**

Chatbot shall accept:

- "Show me..."
- "Plot..."
- "Visualize..."

**FR-BOT-PLOT-02: Context-Aware Plot Generation**

Plots shall respect:

- Selected terminal
- Time Window
- User role

**FR-BOT-PLOT-03: Drill-Down Capability**

User can:

- Click chart segment → see vessels / berths
- Ask follow-up: "Why is this spike happening?"

**FR-BOT-PLOT-04: Narrative + Visual Hybrid**

Each plot shall include:

- Chart
- Auto-generated explanation

**Example**

"Traffic load peaked at 14:00 due to simultaneous arrivals of 4 large vessels and a tidal restriction."

---

*End of Document*
