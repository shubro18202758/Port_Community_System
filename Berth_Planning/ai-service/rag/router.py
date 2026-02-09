"""
SmartBerth AI - Query Router
Routes queries to appropriate engine: ChromaDB (semantic) or Neo4j (relationship)
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryEngine(Enum):
    """Available query engines"""
    CHROMADB = "chromadb"      # Semantic search for documentation/knowledge
    NEO4J = "neo4j"            # Graph queries for relationships
    HYBRID = "hybrid"          # Use both and combine results


@dataclass
class RoutingDecision:
    """Result of query routing decision"""
    primary_engine: QueryEngine
    secondary_engine: Optional[QueryEngine]
    confidence: float
    reasoning: str
    detected_entities: Dict[str, List[str]]
    query_intent: str


@dataclass
class CombinedResult:
    """Combined result from multiple engines"""
    query: str
    routing: RoutingDecision
    chromadb_results: Optional[List[Dict[str, Any]]]
    neo4j_results: Optional[List[Dict[str, Any]]]
    combined_explanation: str
    sources: List[str]


class QueryRouter:
    """
    Routes queries to appropriate backend:
    - ChromaDB: Documentation lookups, policy questions, "what is", "how to"
    - Neo4j: Relationship queries, "find berths for vessel X", conflicts, alternatives
    - Hybrid: Complex queries requiring both knowledge and graph reasoning
    """
    
    # Keywords indicating semantic/documentation queries (ChromaDB)
    SEMANTIC_KEYWORDS = [
        "what is", "what are", "explain", "describe", "definition",
        "how to", "how does", "procedure", "policy", "guideline",
        "regulation", "requirement", "standard", "best practice",
        "documentation", "manual", "constraint", "rule"
    ]
    
    # Keywords indicating relationship/graph queries (Neo4j)
    RELATIONSHIP_KEYWORDS = [
        "find berth", "suitable berth", "which berth", "available berth",
        "vessel", "schedule", "conflict", "overlap", "alternative",
        "compatible", "assign", "allocate", "recommend berth",
        "resource", "pilot", "tug", "contention", "shortage",
        "historical", "preference", "cascade", "impact"
    ]
    
    # Entity patterns for extraction
    ENTITY_PATTERNS = {
        "vessel_name": r"(?:vessel|ship)\s+([A-Z][A-Za-z\s]+?)(?:\s*\(|\s+with|\s+LOA|\s*,|$)",
        "imo_number": r"IMO[\s:-]*(\d{7})",
        "loa": r"LOA[\s:]*(\d+(?:\.\d+)?)\s*m",
        "beam": r"(?:beam|width)[\s:]*(\d+(?:\.\d+)?)\s*m",
        "draft": r"draft[\s:]*(\d+(?:\.\d+)?)\s*m",
        "berth_name": r"berth\s+([A-Z]?\d+[A-Za-z]*)",
        "port_name": r"(?:port|terminal)\s+(?:of\s+)?([A-Z][A-Za-z\s]+?)(?:\s*\(|\s*,|$)",
        "date_time": r"(\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2})?)",
        "vessel_type": r"(container|tanker|bulk|lng|lpg|ro-ro|cruise|general cargo)\s*(?:vessel|ship|carrier)?",
        "cargo_type": r"(?:cargo|carrying)\s+(container|oil|lng|lpg|bulk|grain|coal)"
    }
    
    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        model: str = "claude-opus-4-20250514",
        use_ai_routing: bool = True
    ):
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.use_ai_routing = use_ai_routing
        self._client: Optional[anthropic.Anthropic] = None
    
    @property
    def client(self) -> Optional[anthropic.Anthropic]:
        """Lazy initialization of Anthropic client"""
        if not ANTHROPIC_AVAILABLE:
            return None
        if self._client is None and self.api_key:
            self._client = anthropic.Anthropic(api_key=self.api_key)
        return self._client
    
    def _extract_entities(self, query: str) -> Dict[str, List[str]]:
        """Extract entities from query using regex patterns"""
        entities = {}
        query_lower = query.lower()
        
        for entity_type, pattern in self.ENTITY_PATTERNS.items():
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                entities[entity_type] = [m.strip() for m in matches]
        
        return entities
    
    def _rule_based_routing(self, query: str) -> Tuple[QueryEngine, float, str]:
        """
        Simple rule-based routing using keyword matching
        Returns: (engine, confidence, reasoning)
        """
        query_lower = query.lower()
        
        # Count keyword matches
        semantic_score = sum(1 for kw in self.SEMANTIC_KEYWORDS if kw in query_lower)
        relationship_score = sum(1 for kw in self.RELATIONSHIP_KEYWORDS if kw in query_lower)
        
        # Extract entities - presence of specific entities suggests graph query
        entities = self._extract_entities(query)
        entity_bonus = len(entities) * 0.5
        
        # Adjust scores
        relationship_score += entity_bonus
        
        # Determine routing
        if semantic_score > 0 and relationship_score > 0:
            # Both types detected - use hybrid
            if relationship_score > semantic_score:
                return (
                    QueryEngine.HYBRID,
                    0.7,
                    f"Hybrid query detected: semantic keywords ({semantic_score}) + "
                    f"relationship keywords ({relationship_score}) + entities ({len(entities)})"
                )
            else:
                return (
                    QueryEngine.HYBRID,
                    0.7,
                    f"Hybrid query detected: semantic keywords ({semantic_score}) + "
                    f"relationship keywords ({relationship_score})"
                )
        
        if relationship_score > semantic_score:
            confidence = min(0.9, 0.5 + relationship_score * 0.1)
            return (
                QueryEngine.NEO4J,
                confidence,
                f"Graph query detected: relationship keywords ({relationship_score}), "
                f"entities ({len(entities)})"
            )
        
        if semantic_score > 0:
            confidence = min(0.9, 0.5 + semantic_score * 0.1)
            return (
                QueryEngine.CHROMADB,
                confidence,
                f"Semantic query detected: documentation keywords ({semantic_score})"
            )
        
        # Default to ChromaDB for general questions
        return (
            QueryEngine.CHROMADB,
            0.5,
            "No specific keywords detected, defaulting to semantic search"
        )
    
    def _ai_routing(self, query: str) -> Tuple[QueryEngine, float, str]:
        """
        Use Claude to determine optimal routing
        Returns: (engine, confidence, reasoning)
        """
        if not self.client:
            return self._rule_based_routing(query)
        
        system_prompt = """You are a query router for SmartBerth AI, a maritime logistics system.
        
Your job is to determine which backend should handle a user's query:

1. CHROMADB (Semantic Search):
   - Documentation lookups
   - Policy and procedure questions
   - "What is X?" / "How does Y work?" questions
   - General knowledge about port operations
   - Constraint explanations

2. NEO4J (Graph Database):
   - Finding specific berths for specific vessels
   - Checking schedules and conflicts
   - Resource availability (pilots, tugs)
   - Historical usage patterns
   - Alternative recommendations
   - Relationship-based queries

3. HYBRID (Both):
   - Complex queries needing both knowledge context AND specific data
   - "Find berths for vessel X and explain the constraints"
   - Questions combining policy with specific vessel/berth data

Respond with JSON only:
{
    "engine": "chromadb" | "neo4j" | "hybrid",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation",
    "intent": "what the user wants to accomplish"
}"""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Route this query: {query}"}
                ]
            )
            
            response_text = response.content[0].text
            
            # Parse JSON response
            import json
            try:
                if "```json" in response_text:
                    json_start = response_text.find("```json") + 7
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                elif "```" in response_text:
                    json_start = response_text.find("```") + 3
                    json_end = response_text.find("```", json_start)
                    response_text = response_text[json_start:json_end].strip()
                
                parsed = json.loads(response_text)
                engine_str = parsed.get("engine", "chromadb").lower()
                engine = QueryEngine(engine_str)
                
                return (
                    engine,
                    float(parsed.get("confidence", 0.8)),
                    parsed.get("reasoning", "AI routing decision")
                )
            except (json.JSONDecodeError, ValueError):
                # Fallback to rule-based
                return self._rule_based_routing(query)
                
        except Exception as e:
            logger.warning(f"AI routing failed, using rule-based: {e}")
            return self._rule_based_routing(query)
    
    def route(self, query: str) -> RoutingDecision:
        """
        Route a query to the appropriate engine(s)
        
        Args:
            query: User's natural language query
            
        Returns:
            RoutingDecision with engine selection and reasoning
        """
        # Extract entities first
        entities = self._extract_entities(query)
        
        # Get routing decision
        if self.use_ai_routing and self.client:
            engine, confidence, reasoning = self._ai_routing(query)
        else:
            engine, confidence, reasoning = self._rule_based_routing(query)
        
        # Determine secondary engine for hybrid queries
        secondary = None
        if engine == QueryEngine.HYBRID:
            # For hybrid, determine which is primary based on entity presence
            if entities:
                primary = QueryEngine.NEO4J
                secondary = QueryEngine.CHROMADB
            else:
                primary = QueryEngine.CHROMADB
                secondary = QueryEngine.NEO4J
            engine = primary
        
        # Determine query intent
        intent = self._determine_intent(query, engine)
        
        return RoutingDecision(
            primary_engine=engine,
            secondary_engine=secondary,
            confidence=confidence,
            reasoning=reasoning,
            detected_entities=entities,
            query_intent=intent
        )
    
    def _determine_intent(self, query: str, engine: QueryEngine) -> str:
        """Determine the specific intent of the query"""
        query_lower = query.lower()
        
        if engine == QueryEngine.NEO4J:
            if "suitable" in query_lower or "find berth" in query_lower:
                return "find_suitable_berths"
            if "conflict" in query_lower or "overlap" in query_lower:
                return "analyze_conflicts"
            if "alternative" in query_lower:
                return "find_alternatives"
            if "resource" in query_lower or "pilot" in query_lower or "tug" in query_lower:
                return "check_resources"
            if "explain" in query_lower and ("berth" in query_lower or "recommendation" in query_lower):
                return "explain_recommendation"
            return "graph_query"
        
        if engine == QueryEngine.CHROMADB:
            if "what is" in query_lower or "what are" in query_lower:
                return "definition_lookup"
            if "how to" in query_lower or "procedure" in query_lower:
                return "procedure_lookup"
            if "policy" in query_lower or "rule" in query_lower:
                return "policy_lookup"
            if "constraint" in query_lower or "requirement" in query_lower:
                return "constraint_lookup"
            return "semantic_search"
        
        return "general_query"


class QueryOrchestrator:
    """
    Orchestrates query execution across multiple engines
    """
    
    def __init__(
        self,
        router: Optional[QueryRouter] = None,
        chromadb_retriever=None,
        neo4j_reasoner=None
    ):
        self.router = router or QueryRouter()
        self._chromadb_retriever = chromadb_retriever
        self._neo4j_reasoner = neo4j_reasoner
    
    @property
    def chromadb_retriever(self):
        """Lazy load ChromaDB retriever"""
        if self._chromadb_retriever is None:
            try:
                from rag_hybrid import get_retriever
                self._chromadb_retriever = get_retriever()
            except ImportError:
                logger.warning("Could not import rag_hybrid retriever")
        return self._chromadb_retriever
    
    @property
    def neo4j_reasoner(self):
        """Lazy load Neo4j reasoner"""
        if self._neo4j_reasoner is None:
            try:
                from graph import get_graph_reasoner
                self._neo4j_reasoner = get_graph_reasoner()
            except ImportError:
                logger.warning("Could not import graph reasoner")
        return self._neo4j_reasoner
    
    def execute(self, query: str) -> CombinedResult:
        """
        Route and execute query, combining results if needed
        
        Args:
            query: User's natural language query
            
        Returns:
            CombinedResult with data from all relevant engines
        """
        # Route the query
        routing = self.router.route(query)
        
        chromadb_results = None
        neo4j_results = None
        sources = []
        
        # Execute on primary engine
        if routing.primary_engine == QueryEngine.CHROMADB:
            chromadb_results = self._execute_chromadb(query)
            sources.append("ChromaDB (Knowledge Base)")
        elif routing.primary_engine == QueryEngine.NEO4J:
            neo4j_results = self._execute_neo4j(query, routing)
            sources.append("Neo4j (Graph Database)")
        
        # Execute on secondary engine if hybrid
        if routing.secondary_engine:
            if routing.secondary_engine == QueryEngine.CHROMADB:
                chromadb_results = self._execute_chromadb(query)
                sources.append("ChromaDB (Knowledge Base)")
            elif routing.secondary_engine == QueryEngine.NEO4J:
                neo4j_results = self._execute_neo4j(query, routing)
                sources.append("Neo4j (Graph Database)")
        
        # Combine results into explanation
        explanation = self._combine_results(
            query, routing, chromadb_results, neo4j_results
        )
        
        return CombinedResult(
            query=query,
            routing=routing,
            chromadb_results=chromadb_results,
            neo4j_results=neo4j_results,
            combined_explanation=explanation,
            sources=sources
        )
    
    def _execute_chromadb(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Execute query on ChromaDB"""
        if not self.chromadb_retriever:
            return None
        
        try:
            docs = self.chromadb_retriever.hybrid_search(query, top_k=5)
            return [
                {
                    "source": doc.source,
                    "content": doc.content,
                    "score": doc.score,
                    "method": doc.retrieval_method,
                    "category": doc.category
                }
                for doc in docs
            ]
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return None
    
    def _execute_neo4j(
        self, 
        query: str, 
        routing: RoutingDecision
    ) -> Optional[List[Dict[str, Any]]]:
        """Execute query on Neo4j"""
        if not self.neo4j_reasoner:
            return None
        
        try:
            # Determine which graph query to run based on intent
            intent = routing.query_intent
            entities = routing.detected_entities
            
            # For now, return status - actual execution requires entity IDs
            return [{
                "intent": intent,
                "entities": entities,
                "status": "requires_entity_resolution",
                "message": "Entity IDs need to be resolved from names before graph query"
            }]
        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return None
    
    def _combine_results(
        self,
        query: str,
        routing: RoutingDecision,
        chromadb_results: Optional[List[Dict[str, Any]]],
        neo4j_results: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Combine results from multiple engines into explanation"""
        parts = []
        
        parts.append(f"**Query Analysis**")
        parts.append(f"- Intent: {routing.query_intent}")
        parts.append(f"- Primary Engine: {routing.primary_engine.value}")
        parts.append(f"- Confidence: {routing.confidence:.0%}")
        
        if routing.detected_entities:
            parts.append(f"\n**Detected Entities**")
            for entity_type, values in routing.detected_entities.items():
                parts.append(f"- {entity_type}: {', '.join(values)}")
        
        if chromadb_results:
            parts.append(f"\n**Knowledge Base Results** ({len(chromadb_results)} documents)")
            for i, doc in enumerate(chromadb_results[:3], 1):
                parts.append(f"{i}. {doc['source']} (score: {doc['score']:.3f})")
                content_preview = doc['content'][:200] + "..." if len(doc['content']) > 200 else doc['content']
                parts.append(f"   {content_preview}")
        
        if neo4j_results:
            parts.append(f"\n**Graph Database Results**")
            for result in neo4j_results:
                if result.get("status") == "requires_entity_resolution":
                    parts.append(f"- {result['message']}")
                else:
                    parts.append(f"- {result}")
        
        return "\n".join(parts)


@lru_cache()
def get_query_router() -> QueryRouter:
    """Get cached query router instance"""
    return QueryRouter(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        model=os.getenv("ANTHROPIC_MODEL", "claude-opus-4-20250514"),
        use_ai_routing=True
    )


@lru_cache()
def get_query_orchestrator() -> QueryOrchestrator:
    """Get cached query orchestrator instance"""
    return QueryOrchestrator(
        router=get_query_router()
    )


if __name__ == "__main__":
    print("=" * 60)
    print("SmartBerth AI - Query Router")
    print("=" * 60)
    
    router = get_query_router()
    
    # Test queries
    test_queries = [
        "What are the UKC requirements for large vessels?",
        "Find a suitable berth for vessel MSC AURORA with LOA 340m and draft 14.2m",
        "Which berths are available at JNPT terminal tomorrow?",
        "What is the policy for LNG vessel operations?",
        "Are there any scheduling conflicts for Berth 5 next week?",
        "Explain the berth allocation constraints for container vessels",
        "Find alternative berths for vessel IMO 9876543 at port Mumbai",
        "What pilots are certified for vessels over 300m LOA?"
    ]
    
    print("\n📋 Testing Query Routing:")
    print("-" * 60)
    
    for query in test_queries:
        decision = router.route(query)
        print(f"\n📝 Query: {query[:50]}...")
        print(f"   Engine: {decision.primary_engine.value}", end="")
        if decision.secondary_engine:
            print(f" + {decision.secondary_engine.value}", end="")
        print(f" ({decision.confidence:.0%})")
        print(f"   Intent: {decision.query_intent}")
        print(f"   Reason: {decision.reasoning[:60]}...")
        if decision.detected_entities:
            print(f"   Entities: {decision.detected_entities}")
    
    print("\n" + "=" * 60)
    print("✅ Query Router Test Complete")
