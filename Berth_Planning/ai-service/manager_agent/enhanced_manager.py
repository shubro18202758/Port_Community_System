"""
Enhanced Manager Agent - Training Data Aware Orchestrator
=========================================================

This module extends the Manager Agent with:
- Training data awareness (knowledge from 14 CSV files)
- Better intent classification using domain entities
- Enhanced routing with unified pipeline integration
- Context-aware task decomposition

Milestone 7: Polish Manager Agent Integration
"""

import logging
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .local_llm import OllamaLLM, get_local_llm

logger = logging.getLogger(__name__)


# ============================================================================
# DOMAIN-SPECIFIC TASK TYPES
# ============================================================================

class EnhancedTaskType(Enum):
    """Extended task types with training data awareness"""
    
    # Berth & Vessel Operations
    BERTH_ALLOCATION = "BERTH_ALLOCATION"
    BERTH_COMPATIBILITY = "BERTH_COMPATIBILITY"
    VESSEL_INFO = "VESSEL_INFO"
    VESSEL_SCHEDULING = "VESSEL_SCHEDULING"
    VESSEL_HISTORY = "VESSEL_HISTORY"
    
    # Port Operations
    PORT_RESOURCES = "PORT_RESOURCES"
    TERMINAL_OPERATIONS = "TERMINAL_OPERATIONS"
    CHANNEL_NAVIGATION = "CHANNEL_NAVIGATION"
    ANCHORAGE_MANAGEMENT = "ANCHORAGE_MANAGEMENT"
    
    # Safety & Compliance
    UKC_CALCULATION = "UKC_CALCULATION"
    CONSTRAINT_CHECK = "CONSTRAINT_CHECK"
    SAFETY_ASSESSMENT = "SAFETY_ASSESSMENT"
    
    # Resources
    PILOT_AVAILABILITY = "PILOT_AVAILABILITY"
    TUG_AVAILABILITY = "TUG_AVAILABILITY"
    RESOURCE_PLANNING = "RESOURCE_PLANNING"
    
    # Weather & Conditions
    WEATHER_ANALYSIS = "WEATHER_ANALYSIS"
    TIDAL_ANALYSIS = "TIDAL_ANALYSIS"
    
    # Analytics & Optimization
    OPTIMIZATION = "OPTIMIZATION"
    ANALYTICS = "ANALYTICS"
    PREDICTION = "PREDICTION"
    
    # General
    GENERAL = "GENERAL"
    EXPLANATION = "EXPLANATION"


# ============================================================================
# DOMAIN ENTITY PATTERNS
# ============================================================================

DOMAIN_PATTERNS = {
    # Vessel patterns from training data
    "vessel_name": r"\b(MAERSK|EVERGREEN|MSC|COSCO|CMA CGM|HAPAG|ONE|ZIM|HMM|YANG MING|PIL|WANHAI)\s+[A-Z]+\b",
    "imo_number": r"\bIMO\s*[:\-]?\s*(\d{7})\b|\b\d{7}\b",
    "vessel_type": r"\b(container|tanker|bulk carrier|VLCC|ULCC|LNG|LPG|ro-ro|roro|cruise|ferry|general cargo)\b",
    
    # Port patterns from training data  
    "port_code": r"\b([A-Z]{5})\b",  # 5-letter port codes like INMUN
    "port_name": r"\b(Mumbai|Singapore|Rotterdam|Shanghai|Dubai|Hong Kong|Antwerp|Los Angeles|Hamburg|Busan)\s+Port\b",
    
    # Berth patterns
    "berth_id": r"\b(BRT|BERTH)[_-]?\d{3,4}\b",
    "terminal_id": r"\b(TRM|TERMINAL)[_-]?\d{3,4}\b",
    
    # Dimensional patterns
    "loa": r"\bLOA\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*m?\b",
    "draft": r"\bdraft\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*m?\b",
    "beam": r"\bbeam\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*m?\b",
    
    # UKC patterns
    "ukc": r"\bUKC\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*m?\b",
    "depth": r"\bdepth\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*m?\b",
    
    # Weather patterns
    "wind_speed": r"\bwind\s*(?:speed)?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:knots?|m/s|kn)\b",
    "wave_height": r"\bwave\s*(?:height)?\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*m?\b",
    "visibility": r"\bvisibility\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(?:km|nm|m)\b",
    
    # Resource patterns
    "pilot": r"\b(pilot|pilotage)\b",
    "tugboat": r"\b(tug|tugboat|tow)\b",
}


# ============================================================================
# INTENT CLASSIFICATION RULES
# ============================================================================

INTENT_KEYWORDS = {
    EnhancedTaskType.BERTH_ALLOCATION: ["allocate", "assign", "book", "reserve", "berth for", "dock at"],
    EnhancedTaskType.BERTH_COMPATIBILITY: ["compatible", "suitable", "fit", "can dock", "accept vessel"],
    EnhancedTaskType.VESSEL_INFO: ["vessel details", "ship info", "vessel specs", "imo number"],
    EnhancedTaskType.VESSEL_SCHEDULING: ["schedule", "eta", "etd", "arrival", "departure"],
    EnhancedTaskType.VESSEL_HISTORY: ["history", "previous calls", "past visits", "track record"],
    
    EnhancedTaskType.PORT_RESOURCES: ["port resources", "available at port", "port capacity"],
    EnhancedTaskType.TERMINAL_OPERATIONS: ["terminal", "quay", "wharf"],
    EnhancedTaskType.CHANNEL_NAVIGATION: ["channel", "fairway", "passage", "navigation"],
    EnhancedTaskType.ANCHORAGE_MANAGEMENT: ["anchorage", "anchor", "waiting area", "holding"],
    
    EnhancedTaskType.UKC_CALCULATION: ["ukc", "under keel", "clearance", "depth check"],
    EnhancedTaskType.CONSTRAINT_CHECK: ["constraint", "violation", "rule check", "validate"],
    EnhancedTaskType.SAFETY_ASSESSMENT: ["safe", "risk", "hazard", "danger"],
    
    EnhancedTaskType.PILOT_AVAILABILITY: ["pilot", "pilotage"],
    EnhancedTaskType.TUG_AVAILABILITY: ["tug", "tugboat", "tow", "bollard pull"],
    EnhancedTaskType.RESOURCE_PLANNING: ["resource planning", "crew", "equipment"],
    
    EnhancedTaskType.WEATHER_ANALYSIS: ["weather", "wind", "wave", "storm", "visibility"],
    EnhancedTaskType.TIDAL_ANALYSIS: ["tide", "tidal", "high water", "low water"],
    
    EnhancedTaskType.OPTIMIZATION: ["optimize", "best", "recommend", "minimize", "maximize"],
    EnhancedTaskType.ANALYTICS: ["analyze", "statistics", "metrics", "utilization", "performance"],
    EnhancedTaskType.PREDICTION: ["predict", "forecast", "estimate"],
    
    EnhancedTaskType.EXPLANATION: ["explain", "why", "how does", "what is"],
}


# ============================================================================
# DATA FLOW MAPPING (from SmartBerth_Data_Flow_Architecture.md)
# ============================================================================

# Maps operational phases to required datasets
OPERATIONAL_PHASE_DATA_MAPPING = {
    "pre_arrival": {
        "description": "Pre-Arrival Declaration (72-24 hrs before ETA)",
        "steps": ["vessel_notification", "fal_forms", "service_requests"],
        "datasets": ["Vessel_Parameters", "Vessel_Call", "Port_Parameters", "Pilotage_Parameters", "Tugboat_Parameters", "Berth_Parameters"],
    },
    "ai_processing": {
        "description": "SmartBerth AI Processing & Optimization",
        "steps": ["data_ingestion", "ais_integration", "weather_analysis", "ukc_calculation", "berth_allocation", "resource_scheduling"],
        "datasets": ["AIS_Parameters", "Weather_Parameters", "UKC", "Berth_Parameters", "Terminal_Parameters", "Vessel_Call", "Pilotage_Parameters", "Tugboat_Parameters", "Channel_Parameters"],
    },
    "confirmation": {
        "description": "Confirmation & Notification to Terminal",
        "steps": ["berth_plan_publication", "terminal_preparation"],
        "datasets": ["Berth_Parameters", "Terminal_Parameters"],
    },
    "operations": {
        "description": "Vessel Arrival & Operations",
        "steps": ["ata_recording", "berthing_sequence", "cargo_operations", "departure"],
        "datasets": ["Vessel_Call"],
    },
    "status_display": {
        "description": "Status Display to Shipping Agent",
        "steps": ["vessel_position", "eta_status", "berth_allocation", "service_status", "operations", "alerts"],
        "datasets": ["AIS_Parameters", "Vessel_Call", "Weather_Parameters"],
    },
}

# Maps ML models to their training data requirements
ML_MODEL_DATA_MAPPING = {
    "eta_prediction": {
        "inputs": ["Declared ETA", "AIS Position", "Weather Conditions", "Port Congestion"],
        "target": "ATA (Actual Time of Arrival)",
        "datasets": ["AIS_Parameters", "Vessel_Call", "Weather_Parameters"],
    },
    "berth_allocation": {
        "inputs": ["Vessel Dimensions", "Vessel Type", "Cargo Type", "Berth Availability", "Terminal Capabilities"],
        "target": "Optimal berthCode",
        "datasets": ["Berth_Parameters", "Vessel_Parameters", "Vessel_Call", "Terminal_Parameters"],
    },
    "dwell_time_prediction": {
        "inputs": ["Cargo Volume", "Berth Equipment", "Weather Conditions", "Historical Patterns"],
        "target": "dwellTimeHours",
        "datasets": ["Vessel_Call", "Berth_Parameters", "Weather_Parameters"],
    },
    "resource_scheduling": {
        "inputs": ["Vessel Requirements", "Pilot Certifications", "Tug Bollard Pull", "Service Requests"],
        "target": "Optimal pilot/tug assignment",
        "datasets": ["Pilotage_Parameters", "Tugboat_Parameters", "Vessel_Call", "Vessel_Parameters"],
    },
}

# Entity relationship hierarchy with join keys
ENTITY_RELATIONSHIPS = {
    "Port": {"children": ["Terminal", "Channel", "Anchorage", "Pilot", "Tugboat"], "key": "portId"},
    "Terminal": {"parent": "Port", "children": ["Berth"], "key": "terminalId", "fk": "portId"},
    "Berth": {"parent": "Terminal", "children": [], "key": "berthId", "fk": "terminalId"},
    "Vessel": {"children": ["Vessel_Call", "AIS_Record"], "key": "imoNumber"},
    "Vessel_Call": {"parent": "Vessel", "relations": ["Pilot", "Tugboat", "Berth"], "key": "callId", "fk": "imoNumber"},
}

# Query-to-dataset mapping for quick lookup
QUERY_DATASET_MAPPING = {
    "find_berth": {"primary": ["Berth_Parameters", "Vessel_Parameters", "Terminal_Parameters"], "secondary": ["Vessel_Call"]},
    "calculate_ukc": {"primary": ["UKC", "Channel_Parameters", "Vessel_Parameters"], "secondary": ["Weather_Parameters"]},
    "pilot_availability": {"primary": ["Pilotage_Parameters", "Port_Parameters"], "secondary": ["Vessel_Call"]},
    "tug_requirements": {"primary": ["Tugboat_Parameters", "Vessel_Parameters"], "secondary": ["Port_Parameters"]},
    "weather_impact": {"primary": ["Weather_Parameters", "UKC"], "secondary": ["Vessel_Call"]},
    "port_resources": {"primary": ["Port_Parameters", "Terminal_Parameters", "Berth_Parameters", "Pilotage_Parameters", "Tugboat_Parameters"], "secondary": ["Anchorage_Parameters", "Channel_Parameters"]},
    "vessel_history": {"primary": ["Vessel_Call", "AIS_Parameters"], "secondary": ["Vessel_Parameters"]},
    "eta_prediction": {"primary": ["AIS_Parameters", "Weather_Parameters", "Vessel_Call"], "secondary": ["Port_Parameters"]},
    "channel_navigation": {"primary": ["Channel_Parameters", "UKC"], "secondary": ["Weather_Parameters", "Vessel_Parameters"]},
    "anchorage_assignment": {"primary": ["Anchorage_Parameters", "Vessel_Parameters"], "secondary": ["Weather_Parameters"]},
}


# ============================================================================
# ENHANCED TASK DATA STRUCTURE
# ============================================================================

@dataclass
class EnhancedTask:
    """Enhanced task with training data awareness"""
    id: str
    query: str
    task_type: EnhancedTaskType
    confidence: float
    
    # Extracted entities
    entities: Dict[str, List[str]] = field(default_factory=dict)
    
    # Domain context from training data
    domain_context: Dict[str, Any] = field(default_factory=dict)
    
    # Routing decisions
    requires_rag: bool = True
    requires_graph: bool = False
    requires_central_ai: bool = False
    
    # Execution
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[Any] = None


@dataclass
class EnhancedPlan:
    """Enhanced execution plan"""
    steps: List[Dict[str, str]]
    estimated_time_ms: float = 0.0
    
    # Pipeline components needed
    use_knowledge_index: bool = True
    use_graph_db: bool = False
    use_manager_llm: bool = True
    use_central_ai: bool = True
    
    # Data sources to query
    data_sources: List[str] = field(default_factory=list)
    
    # Expected output
    output_format: str = "text"


# ============================================================================
# ENHANCED MANAGER AGENT
# ============================================================================

class EnhancedManagerAgent:
    """
    Enhanced Manager Agent with training data awareness.
    
    Improvements over base ManagerAgent:
    - Domain-specific entity extraction using training data patterns
    - Better intent classification with keyword matching
    - Training data aware context enrichment
    - Unified pipeline integration
    """
    
    def __init__(
        self,
        model: str = "qwen3-8b-instruct:latest",
        enable_thinking: bool = False
    ):
        """
        Initialize Enhanced Manager Agent
        
        Args:
            model: Ollama model to use
            enable_thinking: Enable extended thinking mode
        """
        self.llm = get_local_llm(model=model, enable_thinking=enable_thinking)
        self.task_history: List[EnhancedTask] = []
        self._context_cache: Dict[str, Any] = {}
        
        # Compile regex patterns
        self._patterns = {
            name: re.compile(pattern, re.IGNORECASE)
            for name, pattern in DOMAIN_PATTERNS.items()
        }
        
        logger.info(f"EnhancedManagerAgent initialized with model: {model}")
    
    def extract_domain_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract domain-specific entities using compiled patterns
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dict mapping entity types to lists of extracted values
        """
        entities = {}
        
        for entity_type, pattern in self._patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Flatten if nested groups
                flat_matches = []
                for m in matches:
                    if isinstance(m, tuple):
                        flat_matches.extend([x for x in m if x])
                    else:
                        flat_matches.append(m)
                
                entities[entity_type] = list(set(flat_matches))
        
        return entities
    
    def classify_intent(self, query: str) -> Tuple[EnhancedTaskType, float]:
        """
        Classify query intent using keyword matching and entity analysis
        
        Args:
            query: User query
            
        Returns:
            Tuple of (TaskType, confidence score)
        """
        query_lower = query.lower()
        
        # Score each task type based on keyword matches
        scores = {}
        
        for task_type, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[task_type] = score
        
        if not scores:
            return EnhancedTaskType.GENERAL, 0.5
        
        # Get best match
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Normalize confidence
        confidence = min(0.9, 0.5 + (best_score * 0.15))
        
        # Boost confidence if entities match the task type
        entities = self.extract_domain_entities(query)
        
        if best_type in [EnhancedTaskType.BERTH_ALLOCATION, EnhancedTaskType.BERTH_COMPATIBILITY]:
            if "berth_id" in entities or "vessel_name" in entities:
                confidence = min(0.95, confidence + 0.1)
        
        if best_type == EnhancedTaskType.UKC_CALCULATION:
            if "ukc" in entities or "draft" in entities or "depth" in entities:
                confidence = min(0.95, confidence + 0.1)
        
        if best_type in [EnhancedTaskType.PILOT_AVAILABILITY, EnhancedTaskType.TUG_AVAILABILITY]:
            if "pilot" in entities or "tugboat" in entities:
                confidence = min(0.95, confidence + 0.1)
        
        return best_type, confidence
    
    def determine_routing(self, task_type: EnhancedTaskType, entities: Dict) -> Dict[str, bool]:
        """
        Determine which pipeline components are needed
        
        Args:
            task_type: Classified task type
            entities: Extracted entities
            
        Returns:
            Dict with routing flags
        """
        routing = {
            "requires_rag": True,  # Default: use knowledge base
            "requires_graph": False,
            "requires_central_ai": True  # Default: use Claude for generation
        }
        
        # Graph-heavy tasks
        graph_tasks = [
            EnhancedTaskType.PORT_RESOURCES,
            EnhancedTaskType.TERMINAL_OPERATIONS,
            EnhancedTaskType.VESSEL_HISTORY,
            EnhancedTaskType.BERTH_COMPATIBILITY,
        ]
        
        if task_type in graph_tasks:
            routing["requires_graph"] = True
        
        # If we have specific entity IDs, graph might help
        if any(k in entities for k in ["berth_id", "terminal_id", "port_code", "imo_number"]):
            routing["requires_graph"] = True
        
        # Simple lookups might not need Central AI
        simple_tasks = [
            EnhancedTaskType.VESSEL_INFO,
            EnhancedTaskType.EXPLANATION,
        ]
        
        if task_type in simple_tasks and len(entities) > 0:
            routing["requires_central_ai"] = False  # Manager LLM sufficient
        
        # Complex reasoning definitely needs Central AI
        complex_tasks = [
            EnhancedTaskType.OPTIMIZATION,
            EnhancedTaskType.ANALYTICS,
            EnhancedTaskType.SAFETY_ASSESSMENT,
            EnhancedTaskType.UKC_CALCULATION,
        ]
        
        if task_type in complex_tasks:
            routing["requires_central_ai"] = True
        
        return routing
    
    def identify_data_sources(self, task_type: EnhancedTaskType, entities: Dict) -> List[str]:
        """
        Identify which training data sources are relevant using data flow mapping.
        
        This method uses the QUERY_DATASET_MAPPING and ML_MODEL_DATA_MAPPING
        derived from SmartBerth_Data_Flow_Architecture.md
        
        Args:
            task_type: Task type
            entities: Extracted entities
            
        Returns:
            List of relevant data source names
        """
        sources = []
        
        # Map task types to query categories for QUERY_DATASET_MAPPING lookup
        task_to_query_map = {
            EnhancedTaskType.BERTH_ALLOCATION: "find_berth",
            EnhancedTaskType.BERTH_COMPATIBILITY: "find_berth",
            EnhancedTaskType.VESSEL_INFO: "vessel_history",
            EnhancedTaskType.VESSEL_SCHEDULING: "eta_prediction",
            EnhancedTaskType.VESSEL_HISTORY: "vessel_history",
            
            EnhancedTaskType.PORT_RESOURCES: "port_resources",
            EnhancedTaskType.TERMINAL_OPERATIONS: "port_resources",
            EnhancedTaskType.CHANNEL_NAVIGATION: "channel_navigation",
            EnhancedTaskType.ANCHORAGE_MANAGEMENT: "anchorage_assignment",
            
            EnhancedTaskType.UKC_CALCULATION: "calculate_ukc",
            EnhancedTaskType.CONSTRAINT_CHECK: "calculate_ukc",
            EnhancedTaskType.SAFETY_ASSESSMENT: "weather_impact",
            
            EnhancedTaskType.PILOT_AVAILABILITY: "pilot_availability",
            EnhancedTaskType.TUG_AVAILABILITY: "tug_requirements",
            EnhancedTaskType.RESOURCE_PLANNING: "port_resources",
            
            EnhancedTaskType.WEATHER_ANALYSIS: "weather_impact",
            EnhancedTaskType.TIDAL_ANALYSIS: "calculate_ukc",
            
            EnhancedTaskType.OPTIMIZATION: "find_berth",
            EnhancedTaskType.ANALYTICS: "vessel_history",
            EnhancedTaskType.PREDICTION: "eta_prediction",
        }
        
        query_key = task_to_query_map.get(task_type)
        
        if query_key and query_key in QUERY_DATASET_MAPPING:
            mapping = QUERY_DATASET_MAPPING[query_key]
            sources.extend(mapping.get("primary", []))
            # Add secondary sources for complex tasks
            if task_type in [EnhancedTaskType.OPTIMIZATION, EnhancedTaskType.ANALYTICS, 
                            EnhancedTaskType.SAFETY_ASSESSMENT, EnhancedTaskType.UKC_CALCULATION]:
                sources.extend(mapping.get("secondary", []))
        else:
            sources = ["General Knowledge"]
        
        # Add entity-specific sources based on ENTITY_RELATIONSHIPS
        if "vessel_name" in entities or "imo_number" in entities:
            if "Vessel_Parameters" not in sources:
                sources.append("Vessel_Parameters")
            # Vessel has children: Vessel_Call, AIS_Record
            if "Vessel_Call" not in sources:
                sources.append("Vessel_Call")
        
        if "port_code" in entities:
            if "Port_Parameters" not in sources:
                sources.append("Port_Parameters")
            # Port hierarchy: Terminal, Channel, Anchorage, Pilot, Tugboat
        
        if "berth_id" in entities:
            if "Berth_Parameters" not in sources:
                sources.append("Berth_Parameters")
        
        if "terminal_id" in entities:
            if "Terminal_Parameters" not in sources:
                sources.append("Terminal_Parameters")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_sources = []
        for s in sources:
            if s not in seen:
                seen.add(s)
                unique_sources.append(s)
        
        return unique_sources
    
    def get_operational_phase(self, task_type: EnhancedTaskType) -> Optional[Dict[str, Any]]:
        """
        Identify which operational phase a task belongs to.
        
        Uses OPERATIONAL_PHASE_DATA_MAPPING from Data Flow Architecture.
        
        Args:
            task_type: The task type
            
        Returns:
            Phase information dict or None
        """
        phase_task_map = {
            # Pre-arrival phase
            EnhancedTaskType.VESSEL_INFO: "pre_arrival",
            EnhancedTaskType.VESSEL_SCHEDULING: "pre_arrival",
            
            # AI Processing phase
            EnhancedTaskType.BERTH_ALLOCATION: "ai_processing",
            EnhancedTaskType.BERTH_COMPATIBILITY: "ai_processing",
            EnhancedTaskType.UKC_CALCULATION: "ai_processing",
            EnhancedTaskType.WEATHER_ANALYSIS: "ai_processing",
            EnhancedTaskType.PILOT_AVAILABILITY: "ai_processing",
            EnhancedTaskType.TUG_AVAILABILITY: "ai_processing",
            EnhancedTaskType.RESOURCE_PLANNING: "ai_processing",
            EnhancedTaskType.OPTIMIZATION: "ai_processing",
            EnhancedTaskType.CHANNEL_NAVIGATION: "ai_processing",
            
            # Operations phase
            EnhancedTaskType.VESSEL_HISTORY: "operations",
            
            # Status display phase
            EnhancedTaskType.PORT_RESOURCES: "status_display",
            EnhancedTaskType.PREDICTION: "status_display",
        }
        
        phase_key = phase_task_map.get(task_type)
        if phase_key and phase_key in OPERATIONAL_PHASE_DATA_MAPPING:
            return {
                "phase": phase_key,
                **OPERATIONAL_PHASE_DATA_MAPPING[phase_key]
            }
        return None
    
    def get_ml_model_context(self, task_type: EnhancedTaskType) -> Optional[Dict[str, Any]]:
        """
        Get relevant ML model context for a task.
        
        Uses ML_MODEL_DATA_MAPPING from Data Flow Architecture.
        
        Args:
            task_type: The task type
            
        Returns:
            ML model info dict or None
        """
        model_task_map = {
            EnhancedTaskType.VESSEL_SCHEDULING: "eta_prediction",
            EnhancedTaskType.PREDICTION: "eta_prediction",
            EnhancedTaskType.BERTH_ALLOCATION: "berth_allocation",
            EnhancedTaskType.BERTH_COMPATIBILITY: "berth_allocation",
            EnhancedTaskType.OPTIMIZATION: "berth_allocation",
            EnhancedTaskType.PILOT_AVAILABILITY: "resource_scheduling",
            EnhancedTaskType.TUG_AVAILABILITY: "resource_scheduling",
            EnhancedTaskType.RESOURCE_PLANNING: "resource_scheduling",
        }
        
        model_key = model_task_map.get(task_type)
        if model_key and model_key in ML_MODEL_DATA_MAPPING:
            return {
                "model": model_key,
                **ML_MODEL_DATA_MAPPING[model_key]
            }
        return None
    
    def create_task(self, query: str) -> EnhancedTask:
        """
        Create an enhanced task from a query with data flow awareness.
        
        Args:
            query: User query
            
        Returns:
            EnhancedTask object with operational phase and ML context
        """
        # Extract entities
        entities = self.extract_domain_entities(query)
        
        # Classify intent
        task_type, confidence = self.classify_intent(query)
        
        # Determine routing
        routing = self.determine_routing(task_type, entities)
        
        # Get operational phase context
        phase_context = self.get_operational_phase(task_type)
        
        # Get ML model context
        ml_context = self.get_ml_model_context(task_type)
        
        # Build domain context with data flow awareness
        domain_context = {
            "operational_phase": phase_context,
            "ml_model": ml_context,
            "data_sources": self.identify_data_sources(task_type, entities),
            "entity_relationships": self._get_relevant_relationships(entities),
        }
        
        # Create task
        task = EnhancedTask(
            id=f"etask_{len(self.task_history) + 1}_{datetime.now().strftime('%H%M%S')}",
            query=query,
            task_type=task_type,
            confidence=confidence,
            entities=entities,
            domain_context=domain_context,
            requires_rag=routing["requires_rag"],
            requires_graph=routing["requires_graph"],
            requires_central_ai=routing["requires_central_ai"]
        )
        
        self.task_history.append(task)
        
        logger.info(f"Created enhanced task {task.id}: {task_type.value} (conf={confidence:.2f})")
        logger.debug(f"  Entities: {entities}")
        logger.debug(f"  Routing: RAG={routing['requires_rag']}, Graph={routing['requires_graph']}, Central={routing['requires_central_ai']}")
        if phase_context:
            logger.debug(f"  Operational Phase: {phase_context.get('phase')}")
        if ml_context:
            logger.debug(f"  ML Model: {ml_context.get('model')}")
        
        return task
    
    def _get_relevant_relationships(self, entities: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Get relevant entity relationships based on extracted entities.
        
        Args:
            entities: Extracted entities
            
        Returns:
            Dict with relationship info
        """
        relationships = {}
        
        if "port_code" in entities:
            relationships["port_hierarchy"] = {
                "from": "Port",
                "children": ENTITY_RELATIONSHIPS["Port"]["children"],
                "key": ENTITY_RELATIONSHIPS["Port"]["key"]
            }
        
        if "terminal_id" in entities:
            relationships["terminal_hierarchy"] = {
                "from": "Terminal",
                "parent": ENTITY_RELATIONSHIPS["Terminal"]["parent"],
                "children": ENTITY_RELATIONSHIPS["Terminal"]["children"],
                "key": ENTITY_RELATIONSHIPS["Terminal"]["key"],
                "fk": ENTITY_RELATIONSHIPS["Terminal"]["fk"]
            }
        
        if "berth_id" in entities:
            relationships["berth_hierarchy"] = {
                "from": "Berth",
                "parent": ENTITY_RELATIONSHIPS["Berth"]["parent"],
                "key": ENTITY_RELATIONSHIPS["Berth"]["key"],
                "fk": ENTITY_RELATIONSHIPS["Berth"]["fk"]
            }
        
        if "imo_number" in entities or "vessel_name" in entities:
            relationships["vessel_relationships"] = {
                "from": "Vessel",
                "children": ENTITY_RELATIONSHIPS["Vessel"]["children"],
                "key": ENTITY_RELATIONSHIPS["Vessel"]["key"]
            }
        
        return relationships
    
    def create_plan(self, task: EnhancedTask) -> EnhancedPlan:
        """
        Create execution plan for a task
        
        Args:
            task: EnhancedTask to plan for
            
        Returns:
            EnhancedPlan object
        """
        steps = []
        
        # Step 1: Retrieve from knowledge base (if needed)
        if task.requires_rag:
            steps.append({
                "step": 1,
                "action": "QUERY_KNOWLEDGE_BASE",
                "description": f"Search knowledge index for: {task.task_type.value}",
                "component": "chromadb"
            })
        
        # Step 2: Query graph (if needed)
        if task.requires_graph:
            steps.append({
                "step": len(steps) + 1,
                "action": "QUERY_GRAPH",
                "description": f"Query Neo4j for entity relationships",
                "component": "neo4j"
            })
        
        # Step 3: Generate response
        if task.requires_central_ai:
            steps.append({
                "step": len(steps) + 1,
                "action": "GENERATE_RESPONSE",
                "description": "Generate response with Claude AI",
                "component": "claude"
            })
        else:
            steps.append({
                "step": len(steps) + 1,
                "action": "GENERATE_RESPONSE",
                "description": "Generate response with Manager LLM",
                "component": "qwen3"
            })
        
        # Identify data sources
        data_sources = self.identify_data_sources(task.task_type, task.entities)
        
        # Estimate time (rough heuristics)
        estimated_time = 100  # Base ms
        if task.requires_rag:
            estimated_time += 50
        if task.requires_graph:
            estimated_time += 200
        if task.requires_central_ai:
            estimated_time += 2000
        else:
            estimated_time += 500
        
        plan = EnhancedPlan(
            steps=steps,
            estimated_time_ms=estimated_time,
            use_knowledge_index=task.requires_rag,
            use_graph_db=task.requires_graph,
            use_manager_llm=True,
            use_central_ai=task.requires_central_ai,
            data_sources=data_sources,
            output_format="json" if task.task_type in [EnhancedTaskType.ANALYTICS, EnhancedTaskType.OPTIMIZATION] else "text"
        )
        
        return plan
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Full pipeline: create task -> plan -> return routing info with data flow context.
        
        Args:
            query: User query
            
        Returns:
            Dict with task, plan, routing, and data flow context
        """
        # Create enhanced task
        task = self.create_task(query)
        
        # Create execution plan
        plan = self.create_plan(task)
        
        return {
            "task": {
                "id": task.id,
                "type": task.task_type.value,
                "confidence": task.confidence,
                "entities": task.entities,
                "routing": {
                    "requires_rag": task.requires_rag,
                    "requires_graph": task.requires_graph,
                    "requires_central_ai": task.requires_central_ai
                }
            },
            "plan": {
                "steps": plan.steps,
                "estimated_time_ms": plan.estimated_time_ms,
                "data_sources": plan.data_sources,
                "output_format": plan.output_format
            },
            "data_flow_context": {
                "operational_phase": task.domain_context.get("operational_phase"),
                "ml_model": task.domain_context.get("ml_model"),
                "entity_relationships": task.domain_context.get("entity_relationships"),
            },
            "query": query
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager agent statistics"""
        type_counts = {}
        for task in self.task_history:
            t = task.task_type.value
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "llm_stats": self.llm.get_stats() if hasattr(self.llm, "get_stats") else {},
            "tasks_processed": len(self.task_history),
            "task_type_distribution": type_counts,
            "avg_confidence": sum(t.confidence for t in self.task_history) / max(1, len(self.task_history))
        }
    
    def is_ready(self) -> bool:
        """Check if manager agent is ready"""
        return self.llm.is_loaded() if hasattr(self.llm, "is_loaded") else True


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

_enhanced_manager: Optional[EnhancedManagerAgent] = None


def get_enhanced_manager_agent(**kwargs) -> EnhancedManagerAgent:
    """Get or create the enhanced manager agent"""
    global _enhanced_manager
    if _enhanced_manager is None:
        _enhanced_manager = EnhancedManagerAgent(**kwargs)
    return _enhanced_manager
