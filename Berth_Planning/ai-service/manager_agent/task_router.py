"""
Task Router for Manager Agent
Routes incoming requests to appropriate handlers/agents
"""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .local_llm import LocalQwenLLM

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks that can be routed"""
    # RAG/Knowledge tasks
    KNOWLEDGE_QUERY = "knowledge_query"  # ChromaDB semantic search
    GRAPH_QUERY = "graph_query"  # Neo4j relationship queries
    HYBRID_QUERY = "hybrid_query"  # Both ChromaDB + Neo4j
    
    # Planning tasks
    BERTH_PLANNING = "berth_planning"
    SCHEDULE_OPTIMIZATION = "schedule_optimization"
    RESOURCE_ALLOCATION = "resource_allocation"
    
    # Analysis tasks
    VESSEL_ANALYSIS = "vessel_analysis"
    PORT_ANALYSIS = "port_analysis"
    CONFLICT_DETECTION = "conflict_detection"
    
    # Agent tasks
    AGENT_DELEGATION = "agent_delegation"  # Delegate to Claude
    MULTI_STEP_TASK = "multi_step_task"
    
    # Simple tasks
    SIMPLE_RESPONSE = "simple_response"
    CLARIFICATION = "clarification"
    
    # System tasks
    SYSTEM_STATUS = "system_status"
    UNKNOWN = "unknown"


class AgentTarget(Enum):
    """Which agent should handle the task"""
    LOCAL_QWEN = "local_qwen"  # Manager Agent (fast orchestration)
    CLAUDE_API = "claude_api"  # Central AI Agent (complex reasoning)
    RAG_ENGINE = "rag_engine"  # ChromaDB retrieval
    GRAPH_ENGINE = "graph_engine"  # Neo4j queries
    HYBRID = "hybrid"  # Multiple systems
    DIRECT = "direct"  # Direct API response


@dataclass
class RoutingDecision:
    """Result of routing decision"""
    task_type: TaskType
    target: AgentTarget
    confidence: float
    reasoning: str
    extracted_entities: Dict[str, List[str]] = field(default_factory=dict)
    suggested_tools: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, higher = more urgent
    estimated_complexity: str = "medium"  # low, medium, high
    requires_context: bool = True
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class TaskRouter:
    """
    Routes incoming tasks to appropriate handlers
    Uses local Qwen3-8B for fast classification
    """
    
    # Keywords for rule-based routing
    GRAPH_KEYWORDS = [
        "relationship", "connected", "path", "cascade", "impact",
        "conflict", "contention", "dependency", "adjacent", "neighbor",
        "why", "explain relationship", "how does", "affect"
    ]
    
    KNOWLEDGE_KEYWORDS = [
        "what is", "define", "explain", "document", "policy",
        "regulation", "guideline", "procedure", "standard", "best practice"
    ]
    
    PLANNING_KEYWORDS = [
        "plan", "schedule", "optimize", "allocate", "assign",
        "book", "reserve", "eta", "etd", "arrival", "departure"
    ]
    
    VESSEL_KEYWORDS = [
        "vessel", "ship", "imo", "mmsi", "cargo", "tanker",
        "bulk", "container", "draft", "loa", "beam", "dwt"
    ]
    
    BERTH_KEYWORDS = [
        "berth", "quay", "pier", "terminal", "dock", "mooring"
    ]
    
    COMPLEX_INDICATORS = [
        "analyze", "compare", "evaluate", "recommend", "suggest",
        "optimize", "comprehensive", "detailed", "multi", "various"
    ]
    
    def __init__(self, llm: Optional[LocalQwenLLM] = None, use_ai_routing: bool = True):
        """
        Initialize TaskRouter
        
        Args:
            llm: Local LLM instance (will create if None)
            use_ai_routing: Whether to use AI for ambiguous queries
        """
        self.llm = llm
        self.use_ai_routing = use_ai_routing
        self._routing_cache: Dict[str, RoutingDecision] = {}
        
    def _get_llm(self) -> LocalQwenLLM:
        """Lazy load LLM"""
        if self.llm is None:
            self.llm = LocalQwenLLM()
        return self.llm
    
    def route(self, query: str, context: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """
        Route a query to the appropriate handler
        
        Args:
            query: User query or task description
            context: Optional context (conversation history, user info, etc.)
            
        Returns:
            RoutingDecision with task type, target, and metadata
        """
        query_lower = query.lower().strip()
        
        # Check cache for identical queries
        cache_key = f"{query_lower}_{hash(str(context) if context else '')}"
        if cache_key in self._routing_cache:
            return self._routing_cache[cache_key]
        
        # Try rule-based routing first (fast)
        rule_result = self._rule_based_routing(query_lower)
        
        if rule_result.confidence >= 0.8:
            # High confidence rule-based decision
            decision = rule_result
        elif self.use_ai_routing and rule_result.confidence < 0.6:
            # Low confidence - use AI routing
            decision = self._ai_routing(query, context)
        else:
            # Medium confidence - use rule result
            decision = rule_result
        
        # Extract entities
        decision.extracted_entities = self._extract_entities(query)
        
        # Determine complexity
        decision.estimated_complexity = self._estimate_complexity(query, decision)
        
        # Cache result
        self._routing_cache[cache_key] = decision
        
        logger.info(f"Routed query to {decision.target.value} ({decision.task_type.value}) "
                   f"with confidence {decision.confidence:.2f}")
        
        return decision
    
    def _rule_based_routing(self, query: str) -> RoutingDecision:
        """Apply rule-based routing logic"""
        # Count keyword matches
        graph_score = sum(1 for kw in self.GRAPH_KEYWORDS if kw in query)
        knowledge_score = sum(1 for kw in self.KNOWLEDGE_KEYWORDS if kw in query)
        planning_score = sum(1 for kw in self.PLANNING_KEYWORDS if kw in query)
        vessel_score = sum(1 for kw in self.VESSEL_KEYWORDS if kw in query)
        berth_score = sum(1 for kw in self.BERTH_KEYWORDS if kw in query)
        complex_score = sum(1 for kw in self.COMPLEX_INDICATORS if kw in query)
        
        # Determine task type and target
        scores = {
            "graph": graph_score,
            "knowledge": knowledge_score,
            "planning": planning_score + berth_score,
            "vessel": vessel_score,
            "complex": complex_score
        }
        
        max_category = max(scores, key=scores.get)
        max_score = scores[max_category]
        
        # Routing logic
        if max_score == 0:
            # No keyword matches - unknown
            return RoutingDecision(
                task_type=TaskType.UNKNOWN,
                target=AgentTarget.LOCAL_QWEN,
                confidence=0.3,
                reasoning="No keyword matches found"
            )
        
        # Calculate confidence based on score
        confidence = min(0.95, 0.5 + (max_score * 0.1))
        
        # Graph queries
        if max_category == "graph":
            return RoutingDecision(
                task_type=TaskType.GRAPH_QUERY,
                target=AgentTarget.GRAPH_ENGINE,
                confidence=confidence,
                reasoning=f"Graph keywords detected: {graph_score} matches",
                suggested_tools=["neo4j_query", "graph_reasoner"]
            )
        
        # Knowledge queries
        if max_category == "knowledge":
            return RoutingDecision(
                task_type=TaskType.KNOWLEDGE_QUERY,
                target=AgentTarget.RAG_ENGINE,
                confidence=confidence,
                reasoning=f"Knowledge keywords detected: {knowledge_score} matches",
                suggested_tools=["chromadb_search", "document_retrieval"]
            )
        
        # Planning queries
        if max_category == "planning":
            # Complex planning goes to Claude
            if complex_score > 0 or planning_score >= 3:
                return RoutingDecision(
                    task_type=TaskType.BERTH_PLANNING,
                    target=AgentTarget.CLAUDE_API,
                    confidence=confidence,
                    reasoning=f"Complex planning task detected",
                    suggested_tools=["berth_optimizer", "schedule_planner"],
                    estimated_complexity="high"
                )
            else:
                return RoutingDecision(
                    task_type=TaskType.BERTH_PLANNING,
                    target=AgentTarget.HYBRID,
                    confidence=confidence,
                    reasoning=f"Planning keywords detected: {planning_score} matches",
                    suggested_tools=["berth_availability", "schedule_check"]
                )
        
        # Vessel-specific queries
        if max_category == "vessel":
            return RoutingDecision(
                task_type=TaskType.VESSEL_ANALYSIS,
                target=AgentTarget.HYBRID,
                confidence=confidence,
                reasoning=f"Vessel keywords detected: {vessel_score} matches",
                suggested_tools=["vessel_lookup", "vessel_history"]
            )
        
        # Complex analysis goes to Claude
        if max_category == "complex":
            return RoutingDecision(
                task_type=TaskType.AGENT_DELEGATION,
                target=AgentTarget.CLAUDE_API,
                confidence=confidence,
                reasoning="Complex analysis indicators detected",
                estimated_complexity="high"
            )
        
        # Default fallback
        return RoutingDecision(
            task_type=TaskType.HYBRID_QUERY,
            target=AgentTarget.HYBRID,
            confidence=0.5,
            reasoning="Mixed signals, using hybrid approach"
        )
    
    def _ai_routing(self, query: str, context: Optional[Dict]) -> RoutingDecision:
        """Use AI for routing decision when rules are uncertain"""
        llm = self._get_llm()
        
        prompt = f"""<|im_start|>system
You are a task router for a maritime berth planning system. Classify the user query into one of these categories:

TASK_TYPES:
- knowledge_query: Questions about definitions, policies, procedures (uses document search)
- graph_query: Questions about relationships, impacts, conflicts between entities (uses graph database)
- berth_planning: Scheduling or allocating berths to vessels
- vessel_analysis: Analysis of specific vessels
- conflict_detection: Finding scheduling conflicts or resource contention
- simple_response: Simple factual questions or greetings
- agent_delegation: Complex tasks requiring detailed analysis

TARGETS:
- rag_engine: Document/knowledge search
- graph_engine: Relationship and conflict queries
- claude_api: Complex reasoning and analysis
- local_qwen: Simple tasks and routing
- hybrid: Multiple systems needed

Respond with JSON only:
{{"task_type": "<type>", "target": "<target>", "confidence": <0.0-1.0>, "reasoning": "<brief reason>"}}
<|im_end|>
<|im_start|>user
Query: {query}
Context: {context if context else 'None'}
<|im_end|>
<|im_start|>assistant
"""
        
        try:
            response = llm.generate(prompt, max_tokens=150, temperature=0.1, stop=["<|im_end|>"])
            import json
            result = json.loads(response)
            
            return RoutingDecision(
                task_type=TaskType[result.get("task_type", "unknown").upper()],
                target=AgentTarget[result.get("target", "hybrid").upper()],
                confidence=result.get("confidence", 0.7),
                reasoning=result.get("reasoning", "AI routing decision")
            )
        except Exception as e:
            logger.warning(f"AI routing failed: {e}, falling back to rule-based")
            return self._rule_based_routing(query.lower())
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract key entities from query"""
        entities = {
            "vessels": [],
            "berths": [],
            "ports": [],
            "dates": [],
            "numbers": []
        }
        
        # Simple regex patterns
        # IMO numbers
        imo_pattern = r'IMO[:\s]?(\d{7})'
        entities["vessels"].extend(re.findall(imo_pattern, query, re.IGNORECASE))
        
        # Berth identifiers (e.g., Berth-01, B1, Terminal A)
        berth_pattern = r'(?:berth|terminal|quay)[\s-]?([A-Z]?\d+|\b[A-Z]\b)'
        entities["berths"].extend(re.findall(berth_pattern, query, re.IGNORECASE))
        
        # Dates
        date_pattern = r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}'
        entities["dates"].extend(re.findall(date_pattern, query))
        
        # Numbers (LOA, draft, etc.)
        number_pattern = r'\b(\d+(?:\.\d+)?)\s*(?:m|meters|ft|feet|tons|dwt)\b'
        entities["numbers"].extend(re.findall(number_pattern, query, re.IGNORECASE))
        
        # Clean up empty lists
        return {k: v for k, v in entities.items() if v}
    
    def _estimate_complexity(self, query: str, decision: RoutingDecision) -> str:
        """Estimate query complexity"""
        query_length = len(query.split())
        entity_count = sum(len(v) for v in decision.extracted_entities.values())
        
        # Complexity factors
        factors = 0
        if query_length > 30:
            factors += 1
        if entity_count > 3:
            factors += 1
        if decision.target in [AgentTarget.CLAUDE_API, AgentTarget.HYBRID]:
            factors += 1
        if any(kw in query.lower() for kw in self.COMPLEX_INDICATORS):
            factors += 1
        if "multi" in query.lower() or "various" in query.lower():
            factors += 1
        
        if factors >= 3:
            return "high"
        elif factors >= 1:
            return "medium"
        return "low"
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about routing decisions"""
        if not self._routing_cache:
            return {"total_cached": 0}
        
        target_counts = {}
        type_counts = {}
        avg_confidence = 0
        
        for decision in self._routing_cache.values():
            target_counts[decision.target.value] = target_counts.get(decision.target.value, 0) + 1
            type_counts[decision.task_type.value] = type_counts.get(decision.task_type.value, 0) + 1
            avg_confidence += decision.confidence
        
        return {
            "total_cached": len(self._routing_cache),
            "target_distribution": target_counts,
            "type_distribution": type_counts,
            "average_confidence": avg_confidence / len(self._routing_cache)
        }
    
    def clear_cache(self):
        """Clear routing cache"""
        self._routing_cache.clear()
