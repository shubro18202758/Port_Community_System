# SmartBerth AI Architecture Deep Dive

This document provides a comprehensive technical breakdown of the SmartBerth AI system, detailing the deep architecture of the unified pipeline, the hierarchical agent management system, the AI core, and the supporting backend components.

## 1. High-Level Architecture

The SmartBerth AI ecosystem is built on a **Hybrid Agentic Neuro-Symbolic Architecture**. It combines the reasoning capabilities of Large Language Models (LLMs) with the precision of symbolic AI (Knowledge Graphs, Constraint Solvers) and the predictive power of traditional Machine Learning.

### System Topology
```mermaid
graph TD
    Client[Frontend / API Client] -->|REST / WebSocket| Gateway[FastAPI Gateway]
    
    subgraph "Unified Intelligence Pipeline"
        Gateway --> Pipeline[UnifiedSmartBerthPipeline]
        Pipeline --> Intent[Intent Classifier]
        
        Intent -->|Complex Task| Manager[Manager Agent (Qwen3-8B)]
        Intent -->|Direct Query| Core[SmartBerth Core (Claude Opus 4)]
        Intent -->|Auto Task| Browser[Browser Agent]
    end
    
    subgraph "Knowledge Layer"
        Core --> RAG[RAG Engine (ChromaDB)]
        Core --> Graph[In-Memory Graph (NetworkX)]
        Graph <--> SQL[SQL Database]
    end
    
    subgraph "Predictive & Operational Layer"
        Core --> ML[ML Service (XGBoost/LGBM)]
        Core --> Heuristics[Constraint Solver]
        Core --> Features[Feature Engineering]
        Core --> Alerts[Alert Service]
    end
    
    subgraph "Execution Layer"
        Browser --> Web[Web Automation]
        Browser --> InternalTools[Internal Tool Registry]
    end
```

---

## 2. Unified Pipeline Architecture (`pipeline_api.py`)

The **Unified Pipeline** is the central nervous system of the application. Instead of isolated endpoints, all intelligent requests flow through this orchestration layer, ensuring consistent context sharing and memory management.

### Key Components

1.  **Orchestrator (`UnifiedSmartBerthPipeline`)**:
    -   **Singleton Pattern**: Ensures a single stateful instance manages all AI components.
    -   **Initialization Sequence**:
        1.  Loads **Knowledge Index** (ChromaDB) for semantic retrieval.
        2.  Builds **In-Memory Graph** (NetworkX) from training data for relational queries.
        3.  Wakes up **Manager Agent** (Local Qwen3-8B via Ollama).
        4.  Connects to **Central AI** (Claude Opus 4) for high-level reasoning.

2.  **Request Flow**:
    -   **Input**: Natural language query + Context (User ID, Session ID).
    -   **Intent Classification**: Routing logic determines if the request is a simple lookup, a complex reasoning task, or an action requiring the browser agent.
    -   **Context Aggregation**: Retrieves relevant history, graph sub-graphs, and RAG documents.
    -   **Synthesis**: The Central LLM synthesizes a response using the aggregated context.
    -   **Evaluation**: Optional RAGAS-based evaluation loop to score response quality.

---

## 3. The Agent Manager System (`manager_agent/`)

The **Manager Agent** acts as the local, privacy-preserving "frontal cortex" of the system. It handles task routing, intent classification, and basic planning without constant cloud API calls.

### Architecture (`enhanced_manager.py` & `local_llm.py`)

*   **Model**: **Qwen3-8B-Instruct** running locally via Ollama.
*   **Hardware Acceleration**: Optimized for RTX 4070 Laptop GPU (~6GB VRAM utilized).
*   **Capabilities**:
    *   **Offline Classification**: Can classify 20+ specific domain intents (e.g., `BERTH_ALLOCATION`, `UKC_CALCULATION`) without internet access.
    *   **Entity Extraction**: Uses regex and pattern matching (`DOMAIN_PATTERNS`) to identify vessel names (IMO), port codes, and operational metrics before LLM processing.
    *   **Task Routing**: Decides whether to invoke the expensive Cloud LLM (Claude) or handle the query locally using cached data or SQL lookups.

---

## 4. The AI Core (`smartberth_core.py` & `model.py`)

The **AI Core** is the reasoning engine powered by **Anthropic's Claude Opus 4**. It handles the most complex cognitive tasks that require deep domain understanding and logic.

### Core Capabilities

1.  **Reasoning Engine (`SmartBerthCore`)**:
    -   Integrates multi-modal data: SQL records, Graph relationships, and Vector embeddings.
    -   **System Prompt**: A rigorously engineered prompt in `model.py` that defines the persona, operational constraints (hard/soft), and safety protocols of a Port operations expert.

2.  **Inference Abstraction (`SmartBerthLLM`)**:
    -   Wraps the Anthropic API to provide a unified interface (`generate_text`, `generate_stream`).
    -   Handles token management, context window optimization, and error recovery (rate limits).

---

## 5. AI Backend Components

The backend is composed of specialized modules that provide specific cognitive or computational services to the Core and Pipeline.

### A. Data & Knowledge Layer
1.  **In-Memory Knowledge Graph (`inmemory_graph.py`)**:
    -   **Technology**: NetworkX (Python).
    -   **Nodes**: 16,000+ entities (Ports, Terminals, Berths, Vessels, Pilots).
    -   **Edges**: 18,000+ relationships (HAS_BERTH, IS_TYPE, AT_PORT).
    -   **Advantage**: Provides millisecond-latency relationship traversal (e.g., "Find all suitable berths for a Panamax vessel") without external DB overhead.

2.  **RAG Engine (`rag.py`)**:
    -   **Vector Store**: ChromaDB (Persistent).
    -   **Embeddings**: `all-MiniLM-L6-v2` (Local inference).
    -   **Content**: Indexes training manuals, port regulations, and historical operational logs.

3.  **Database Service (`database.py`)**:
    -   **Technology**: SQL Server via `pyodbc`.
    -   **Role**: The "Source of Truth" for transactional data (Live vessel positions, schedules).

### B. Intelligence & Predictive Layer
1.  **Machine Learning Service (`ml_models.py`)**:
    -   **ETA Prediction**: Hybrid stacking ensemble (XGBoost + LightGBM + Random Forest).
    -   **Dwell Time**: Gradient Boosting Regressor.
    -   **Anomaly Detection**: Isolation Forest to detect unusual vessel behaviors.
    -   **Performance**: Models are pre-trained and loaded from `models/` directory for fast inference.

2.  **Feature Engineering (`feature_engineering.py`)**:
    -   **Pipelines**: Transforms raw AIS/Weather data into ML-ready tensors.
    -   **Encodings**: Cyclical encoding for time (Hour/Day/Month sin/cos), spatial vectors for vessel movement.
    -   **Calculations**: Specialized logic for Under Keel Clearance (UKC) based on tide and draft.

3.  **Heuristics Engine (`heuristics.py`)**:
    -   **Constraint Solver**: Validates Hard Constraints (Physical dimensions, Depth) and optimizes Soft Constraints (Wait time, Priority).
    -   **Algorithms**:
        -   **Genetic Algorithm**: For complex schedule optimization (Pop: 50, Gen: 100).
        -   **Hungarian Algorithm**: For optimal resource (Pilot/Tug) assignment.
        -   **Greedy Strategies**: For rapid first-fit allocation.

### C. Agentic & Execution Layer
1.  **Browser Agent (`browser_agent/`)**:
    -   **Controller**: `AgenticBrowserController` manages the Observe-Decide-Act loop.
    -   **Tool Registry**: `AgentToolRegistry` exposes internal API functions (DB lookups, ML predictions) as tools the agent can invoke instead of using the browser UI.
    -   **Hybrid Execution**: Can "see" the web page (DOM analysis) via Playwright OR call backend tools directly for speed.

2.  **Alert Service (`alert_service.py`)**:
    -   **Monitoring**: Real-time watchdog for 20+ event types (ETA delay, Weather warning, Conflict).
    -   **Confidence Scoring**: Dynamic scoring based on data freshness, source reliability, and weather certainty.
    -   **Explainability**: Generates natural language explanations for *why* an alert was raised.

---

## 6. Data Integration Flow

### Scenario: "Allocate a berth for vessel MAERSK ALABAMA arriving tomorrow"

1.  **Ingestion**: Request enters `UnifiedSmartBerthPipeline`.
2.  **Understanding**: `Manager Agent` classifies intent as `BERTH_ALLOCATION` and extracts entities (`MAERSK ALABAMA`, `tomorrow`).
3.  **Retrieval**:
    -   `DatabaseService` fetches vessel dimensions (LOA, Draft).
    -   `RAGPipeline` retrieves specific handling rules for Maersk vessels.
    -   `InMemoryGraph` identifies compatible terminals.
4.  **Prediction**:
    -   `FeatureExtractor` prepares data.
    -   `MLService` predicts actual ETA and likelihood of delays.
5.  **Optimization**:
    -   `HeuristicsEngine` filters berths (Hard Constraints).
    -   Constraint Solver scores valid berths (Soft Constraints).
6.  **Reasoning**: `SmartBerthCore` (Claude) reviews top candidates, checks RAG rules, and selects the best option.
7.  **Response**: JSON payload with `BerthRecommendation`, `ConfidenceScore`, and `AI_Explanation` is returned to frontend.
