"""
SmartBerth AI - Unified Pipeline API
====================================

This module provides the API endpoints for the unified RAG pipeline that integrates:
- Knowledge Base Index (ChromaDB with training data)
- Neo4j Graph Operations
- Manager Agent (Qwen3-8B)
- Central AI (Claude Opus 4)
- 6 SOTA RAG Frameworks

Milestone 4 & 5: Connect Claude API and Create API Endpoints
"""

import os
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ============================================================================
# PYDANTIC MODELS FOR API
# ============================================================================

class QueryIntent(str, Enum):
    """Query intent classification"""
    BERTH_ALLOCATION = "berth_allocation"
    VESSEL_INFO = "vessel_info"
    PORT_OPERATIONS = "port_operations"
    RESOURCE_QUERY = "resource_query"  # Pilots, Tugs
    UKC_CALCULATION = "ukc_calculation"
    WEATHER_ANALYSIS = "weather_analysis"
    CONSTRAINT_CHECK = "constraint_check"
    OPTIMIZATION = "optimization"
    GENERAL = "general"


class PipelineQueryRequest(BaseModel):
    """Request model for unified pipeline query"""
    query: str = Field(..., description="Natural language query")
    user_id: Optional[str] = Field(None, description="User ID for memory personalization")
    session_id: Optional[str] = Field(None, description="Session ID for context")
    use_memory: bool = Field(True, description="Use memory for context")
    use_graph: bool = Field(True, description="Use Neo4j graph retrieval")
    use_rag: bool = Field(True, description="Use vector store retrieval")
    evaluate: bool = Field(False, description="Evaluate response with RAGAS")
    max_context_chunks: int = Field(5, ge=1, le=20, description="Max context chunks to retrieve")


class RetrievalResult(BaseModel):
    """Result from a retrieval source"""
    source: str
    content: str
    score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineQueryResponse(BaseModel):
    """Response from unified pipeline query"""
    query: str
    intent: str
    answer: str
    
    # Retrieval info
    context_used: List[RetrievalResult] = Field(default_factory=list)
    graph_context: Optional[str] = None
    
    # Evaluation (if enabled)
    evaluation_scores: Dict[str, float] = Field(default_factory=dict)
    
    # Metadata
    memory_used: bool = False
    graph_used: bool = False
    latency_ms: float = 0.0
    model_used: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class KnowledgeSearchRequest(BaseModel):
    """Request for knowledge base search"""
    query: str
    top_k: int = Field(5, ge=1, le=20)
    knowledge_type: Optional[str] = Field(None, description="Filter by type: domain_rule, domain_concept, operational_data, entity_profile, historical")
    source_filter: Optional[str] = Field(None, description="Filter by source file")


class KnowledgeSearchResponse(BaseModel):
    """Response from knowledge search"""
    query: str
    results: List[Dict[str, Any]]
    total_found: int


class GraphQueryRequest(BaseModel):
    """Request for graph query"""
    query: str
    query_type: str = Field("natural_language", description="natural_language, cypher, or pattern")
    cypher: Optional[str] = Field(None, description="Direct Cypher query (if query_type=cypher)")


class GraphQueryResponse(BaseModel):
    """Response from graph query"""
    query: str
    query_type: str
    cypher_executed: Optional[str] = None
    results: List[Dict[str, Any]]
    total_results: int


class IngestDocumentRequest(BaseModel):
    """Request to ingest a document"""
    content: str
    source: str = "api"
    knowledge_type: str = Field("domain_concept", description="Type of knowledge")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineStatsResponse(BaseModel):
    """Pipeline statistics"""
    knowledge_index: Dict[str, Any]
    graph_stats: Dict[str, Any]
    pipeline_stats: Dict[str, Any]


# ============================================================================
# UNIFIED PIPELINE CLASS
# ============================================================================

class UnifiedSmartBerthPipeline:
    """
    Unified pipeline that orchestrates all SmartBerth AI components.
    """
    
    def __init__(self):
        self._initialized = False
        self._knowledge_collection = None
        self._graph_engine = None
        self._manager_agent = None
        self._central_llm = None
        
        # Stats
        self._stats = {
            "queries_processed": 0,
            "avg_latency_ms": 0.0,
            "cache_hits": 0,
            "errors": 0
        }
    
    def initialize(self) -> bool:
        """Initialize all pipeline components"""
        try:
            logger.info("Initializing Unified SmartBerth Pipeline...")
            
            # 1. Initialize Knowledge Index (ChromaDB)
            self._init_knowledge_index()
            
            # 2. Initialize Graph Engine (Neo4j)
            self._init_graph_engine()
            
            # 3. Initialize Manager Agent (Qwen3-8B)
            self._init_manager_agent()
            
            # 4. Initialize Central LLM (Claude)
            self._init_central_llm()
            
            self._initialized = True
            logger.info("✓ Unified Pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}")
            return False
    
    def _init_knowledge_index(self):
        """Initialize ChromaDB knowledge index"""
        try:
            import chromadb
            
            script_dir = os.path.dirname(os.path.abspath(__file__))
            chroma_path = os.path.join(script_dir, "chroma_db_unified")
            
            if os.path.exists(chroma_path):
                client = chromadb.PersistentClient(path=chroma_path)
                self._knowledge_collection = client.get_collection("smartberth_unified")
                logger.info(f"  ✓ Knowledge index loaded: {self._knowledge_collection.count()} chunks")
            else:
                logger.warning(f"  ⚠ Knowledge index not found at {chroma_path}")
                logger.info("    Run: python build_knowledge_index.py")
                
        except Exception as e:
            logger.error(f"  ✗ Knowledge index initialization failed: {e}")
    
    def _init_graph_engine(self):
        """Initialize Graph Engine - In-Memory (primary) or Neo4j (fallback)"""
        try:
            # Primary: In-Memory Knowledge Graph (100% available)
            from inmemory_graph import get_knowledge_graph, initialize_graph
            
            self._graph_engine = get_knowledge_graph()
            if self._graph_engine.load():
                stats = self._graph_engine.get_stats()
                logger.info(f"  ✓ In-Memory Graph loaded: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
                logger.info(f"    Ports: {stats['counts']['ports']}, Terminals: {stats['counts']['terminals']}, Berths: {stats['counts']['berths']}")
                logger.info(f"    Vessels: {stats['counts']['vessels']}, Pilots: {stats['counts']['pilots']}, Tugs: {stats['counts']['tugboats']}")
                return
            
        except Exception as e:
            logger.warning(f"  ⚠ In-memory graph failed: {e}")
        
        # Fallback: Try Neo4j if available
        try:
            from neo4j_integration import Neo4jQueryEngine
            
            neo4j_engine = Neo4jQueryEngine()
            if neo4j_engine.driver:
                self._graph_engine = neo4j_engine
                logger.info("  ✓ Neo4j graph engine connected (fallback)")
                return
                
        except Exception as e:
            logger.debug(f"Neo4j not available: {e}")
        
        logger.error("  ✗ No graph engine available!")
        self._graph_engine = None
    
    def _init_manager_agent(self):
        """Initialize Enhanced Manager Agent (Qwen3-8B via Ollama)"""
        try:
            # Try enhanced manager first (training data aware)
            try:
                from manager_agent.enhanced_manager import get_enhanced_manager_agent
                self._manager_agent = get_enhanced_manager_agent()
                if self._manager_agent.is_ready():
                    logger.info("  ✓ Enhanced Manager Agent (Qwen3-8B) connected")
                    return
            except Exception as e:
                logger.debug(f"Enhanced manager not available, falling back: {e}")
            
            # Fallback to basic local LLM
            from manager_agent.local_llm import get_local_llm
            
            self._manager_agent = get_local_llm()
            # Test connection
            test = self._manager_agent.generate("Hi", max_tokens=5)
            if test:
                logger.info("  ✓ Manager Agent (Qwen3-8B) connected (basic mode)")
            else:
                logger.warning("  ⚠ Manager Agent not responsive")
                
        except Exception as e:
            logger.warning(f"  ⚠ Manager Agent not available: {e}")
            self._manager_agent = None
    
    def _init_central_llm(self):
        """Initialize Central LLM (Claude)"""
        try:
            from model import get_model
            
            self._central_llm = get_model()
            if not self._central_llm._model_loaded:
                self._central_llm.initialize()
            
            if self._central_llm._model_loaded:
                logger.info("  ✓ Central AI (Claude Opus 4) connected")
            else:
                logger.warning("  ⚠ Claude API not available")
                
        except Exception as e:
            logger.warning(f"  ⚠ Central LLM not available: {e}")
            self._central_llm = None
    
    def classify_intent(self, query: str) -> QueryIntent:
        """Classify query intent using Enhanced Manager Agent"""
        
        # Try enhanced manager first (if available)
        if self._manager_agent and hasattr(self._manager_agent, 'classify_intent'):
            try:
                task_type, confidence = self._manager_agent.classify_intent(query)
                
                # Map enhanced task types to query intents
                enhanced_mapping = {
                    "BERTH_ALLOCATION": QueryIntent.BERTH_ALLOCATION,
                    "BERTH_COMPATIBILITY": QueryIntent.BERTH_ALLOCATION,
                    "VESSEL_INFO": QueryIntent.VESSEL_INFO,
                    "VESSEL_SCHEDULING": QueryIntent.VESSEL_INFO,
                    "VESSEL_HISTORY": QueryIntent.VESSEL_INFO,
                    "PORT_RESOURCES": QueryIntent.PORT_OPERATIONS,
                    "TERMINAL_OPERATIONS": QueryIntent.PORT_OPERATIONS,
                    "CHANNEL_NAVIGATION": QueryIntent.PORT_OPERATIONS,
                    "ANCHORAGE_MANAGEMENT": QueryIntent.PORT_OPERATIONS,
                    "UKC_CALCULATION": QueryIntent.UKC_CALCULATION,
                    "CONSTRAINT_CHECK": QueryIntent.CONSTRAINT_CHECK,
                    "SAFETY_ASSESSMENT": QueryIntent.CONSTRAINT_CHECK,
                    "PILOT_AVAILABILITY": QueryIntent.RESOURCE_QUERY,
                    "TUG_AVAILABILITY": QueryIntent.RESOURCE_QUERY,
                    "RESOURCE_PLANNING": QueryIntent.RESOURCE_QUERY,
                    "WEATHER_ANALYSIS": QueryIntent.WEATHER_ANALYSIS,
                    "TIDAL_ANALYSIS": QueryIntent.WEATHER_ANALYSIS,
                    "OPTIMIZATION": QueryIntent.OPTIMIZATION,
                    "ANALYTICS": QueryIntent.PORT_OPERATIONS,
                    "PREDICTION": QueryIntent.PORT_OPERATIONS,
                    "EXPLANATION": QueryIntent.GENERAL,
                }
                
                return enhanced_mapping.get(task_type.value, QueryIntent.GENERAL)
            except Exception as e:
                logger.debug(f"Enhanced classification failed: {e}")
        
        # Fallback: Rule-based classification (fast path)
        # Order matters - more specific matches first
        query_lower = query.lower()
        
        # Most specific first: Resources (pilot, tug)
        if any(word in query_lower for word in ["pilot", "tug", "tugboat", "resource availab"]):
            return QueryIntent.RESOURCE_QUERY
        
        # Weather conditions
        if any(word in query_lower for word in ["weather", "wind", "wave", "visibility", "storm"]):
            return QueryIntent.WEATHER_ANALYSIS
        
        # UKC calculations
        if any(word in query_lower for word in ["ukc", "keel", "clearance"]) or \
           ("depth" in query_lower and ("channel" in query_lower or "calculate" in query_lower)):
            return QueryIntent.UKC_CALCULATION
        
        # Constraints and rules
        if any(word in query_lower for word in ["constraint", "rule", "restrict", "limit", "violat"]):
            return QueryIntent.CONSTRAINT_CHECK
        
        # Optimization requests
        if any(word in query_lower for word in ["optim", "best", "recommend", "suggest", "minimize", "maximize"]):
            return QueryIntent.OPTIMIZATION
        
        # Berth allocation
        if any(word in query_lower for word in ["berth", "allocat", "assign", "dock"]):
            return QueryIntent.BERTH_ALLOCATION
        
        # Vessel information
        if any(word in query_lower for word in ["vessel", "ship", "imo", "loa", "draft", "beam"]):
            return QueryIntent.VESSEL_INFO
        
        # Port/terminal operations (general)
        if any(word in query_lower for word in ["port", "terminal", "quay", "wharf"]):
            return QueryIntent.PORT_OPERATIONS
        
        # Fallback: Use basic Manager Agent for classification
        if self._manager_agent and hasattr(self._manager_agent, 'classify_task'):
            try:
                result = self._manager_agent.classify_task(query)
                task_type = result.get("task_type", "GENERAL")
                
                mapping = {
                    "BERTH_QUERY": QueryIntent.BERTH_ALLOCATION,
                    "VESSEL_QUERY": QueryIntent.VESSEL_INFO,
                    "OPTIMIZATION": QueryIntent.OPTIMIZATION,
                    "ANALYTICS": QueryIntent.PORT_OPERATIONS,
                    "GRAPH_QUERY": QueryIntent.PORT_OPERATIONS,
                }
                return mapping.get(task_type, QueryIntent.GENERAL)
            except:
                pass
        
        return QueryIntent.GENERAL
    
    def retrieve_knowledge(
        self,
        query: str,
        top_k: int = 5,
        knowledge_type: str = None
    ) -> List[Dict]:
        """Retrieve relevant knowledge from ChromaDB"""
        if not self._knowledge_collection:
            return []
        
        try:
            # Build where clause
            where = None
            if knowledge_type:
                where = {"knowledge_type": knowledge_type}
            
            results = self._knowledge_collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where
            )
            
            docs = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
                    distance = results.get("distances", [[]])[0][i] if results.get("distances") else 0
                    
                    docs.append({
                        "content": doc,
                        "score": 1.0 - distance,  # Convert distance to similarity
                        "source": metadata.get("source", "unknown"),
                        "knowledge_type": metadata.get("knowledge_type", "unknown"),
                        "metadata": metadata
                    })
            
            return docs
            
        except Exception as e:
            logger.error(f"Knowledge retrieval failed: {e}")
            return []
    
    def query_graph(
        self,
        query: str,
        query_type: str = "natural_language"
    ) -> Dict:
        """Query the knowledge graph (in-memory or Neo4j)"""
        if not self._graph_engine:
            return {"results": [], "query_method": None}
        
        try:
            query_lower = query.lower()
            
            # Check if using in-memory graph
            is_inmemory = hasattr(self._graph_engine, 'is_loaded') and self._graph_engine.is_loaded()
            
            # Berth compatibility queries
            if "berth" in query_lower and ("compatible" in query_lower or "suitable" in query_lower or "find" in query_lower):
                # Extract vessel type if mentioned
                vessel_type = None
                for vt in ['container', 'tanker', 'bulk', 'ro-ro', 'lng', 'lpg', 'cruise']:
                    if vt in query_lower:
                        vessel_type = vt.title()
                        break
                
                # Extract LOA if mentioned
                import re
                loa_match = re.search(r'(\d+(?:\.\d+)?)\s*m?\s*loa', query_lower)
                min_loa = float(loa_match.group(1)) if loa_match else None
                
                # Extract draft if mentioned
                draft_match = re.search(r'draft\s*(?:of\s*)?(\d+(?:\.\d+)?)\s*m?', query_lower)
                min_depth = float(draft_match.group(1)) if draft_match else None
                
                results = self._graph_engine.find_compatible_berths(
                    vessel_type=vessel_type,
                    min_loa=min_loa,
                    min_depth=min_depth
                )
                return {
                    "results": results[:20],
                    "query_method": f"find_compatible_berths(type={vessel_type}, loa={min_loa}, depth={min_depth})",
                    "total_found": len(results)
                }
            
            # Port resources queries
            if "resource" in query_lower or "available" in query_lower or "port" in query_lower:
                # Try to extract port code (5-letter uppercase)
                port_code = None
                for word in query.upper().split():
                    if len(word) == 5 and word.isalpha():
                        port_code = word
                        break
                
                if port_code:
                    results = self._graph_engine.get_port_resources(port_code)
                    return {
                        "results": [results] if results else [],
                        "query_method": f"get_port_resources({port_code})"
                    }
            
            # Vessel history queries
            if "vessel" in query_lower and ("history" in query_lower or "calls" in query_lower or "visits" in query_lower):
                # Try to extract vessel name or IMO
                vessel_name = None
                imo_match = re.search(r'imo\s*[:\-]?\s*(\d{7})', query_lower)
                if imo_match:
                    results = self._graph_engine.find_vessel_history(imo_number=imo_match.group(1))
                else:
                    # Look for quoted vessel name or capitalized words
                    name_match = re.search(r'"([^"]+)"', query)
                    if name_match:
                        vessel_name = name_match.group(1)
                    results = self._graph_engine.find_vessel_history(vessel_name=vessel_name)
                
                return {
                    "results": results[:20],
                    "query_method": f"find_vessel_history(name={vessel_name}, imo={imo_match.group(1) if imo_match else None})"
                }
            
            # Port hierarchy queries
            if "hierarchy" in query_lower or ("terminal" in query_lower and "berth" in query_lower):
                port_code = None
                for word in query.upper().split():
                    if len(word) == 5 and word.isalpha():
                        port_code = word
                        break
                
                if port_code and hasattr(self._graph_engine, 'get_port_hierarchy'):
                    results = self._graph_engine.get_port_hierarchy(port_code)
                    return {
                        "results": [results] if results else [],
                        "query_method": f"get_port_hierarchy({port_code})"
                    }
            
            # Get general graph context
            if is_inmemory:
                context = self._graph_engine.get_graph_context(query)
                return {
                    "results": [{"context": context}],
                    "query_method": "get_graph_context"
                }
            
            return {"results": [], "query_method": None}
            
        except Exception as e:
            logger.error(f"Graph query failed: {e}")
            return {"results": [], "query_method": None, "error": str(e)}
    
    def generate_response(
        self,
        query: str,
        context: str,
        intent: QueryIntent
    ) -> str:
        """Generate response using Central AI (Claude)"""
        if not self._central_llm or not self._central_llm._model_loaded:
            # Fallback to Manager Agent
            if self._manager_agent:
                prompt = f"""Based on this context, answer the query.

Context:
{context[:3000]}

Query: {query}

Answer:"""
                return self._manager_agent.generate(prompt, max_tokens=500)
            return "AI models not available. Please check configuration."
        
        # Build system prompt based on intent
        system_prompts = {
            QueryIntent.BERTH_ALLOCATION: """You are SmartBerth AI, specialized in berth allocation optimization.
Analyze vessel requirements against berth capabilities. Consider:
- Dimensional constraints (LOA, beam, draft)
- Cargo compatibility
- Equipment availability
- Scheduling conflicts""",
            
            QueryIntent.UKC_CALCULATION: """You are SmartBerth AI, specialized in UKC (Under Keel Clearance) calculations.
UKC = Channel/Berth Depth - (Static Draft + Squat + Heel Allowance + Wave Response + Safety Margin)
Ensure safe passage with adequate clearance.""",
            
            QueryIntent.RESOURCE_QUERY: """You are SmartBerth AI, specialized in port resource management.
Analyze pilot and tugboat availability, certifications, and scheduling.
Consider weather conditions and vessel size for resource requirements.""",
            
            QueryIntent.OPTIMIZATION: """You are SmartBerth AI, specialized in port operations optimization.
Provide data-driven recommendations to minimize waiting time,
maximize berth utilization, and optimize resource allocation.""",
        }
        
        system_prompt = system_prompts.get(intent, """You are SmartBerth AI, an intelligent assistant for port berth planning.
Provide accurate, data-driven answers based on the provided context.""")
        
        prompt = f"""Context from SmartBerth Knowledge Base:
{context[:4000]}

User Query: {query}

Provide a comprehensive, accurate answer based on the context above."""
        
        try:
            result = self._central_llm.generate_text(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=1024,
                temperature=0.7
            )
            return result.get("text", "Failed to generate response")
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return f"Error generating response: {e}"
    
    async def process_query(self, request: PipelineQueryRequest) -> PipelineQueryResponse:
        """Process a query through the unified pipeline with data flow awareness"""
        start_time = datetime.now()
        
        # 1. Classify intent and get data flow context from Enhanced Manager
        intent = self.classify_intent(request.query)
        logger.info(f"Query intent: {intent.value}")
        
        # Get data flow context from enhanced manager (operational phase, ML model, datasets)
        data_flow_context = None
        if self._manager_agent and hasattr(self._manager_agent, 'process_query'):
            try:
                manager_result = self._manager_agent.process_query(request.query)
                data_flow_context = manager_result.get("data_flow_context")
                if data_flow_context:
                    logger.info(f"Data flow phase: {data_flow_context.get('operational_phase', 'unknown')}")
            except Exception as e:
                logger.debug(f"Enhanced manager data flow context failed: {e}")
        
        # 2. Retrieve context from knowledge base (with data flow awareness)
        context_chunks = []
        if request.use_rag:
            # If we have data flow context, prioritize relevant knowledge types
            knowledge_type_filter = None
            if data_flow_context:
                phase = data_flow_context.get("operational_phase")
                if phase in ["pre_arrival", "ai_processing"]:
                    knowledge_type_filter = "operational_data"  # Prioritize operational data
                elif phase == "confirmation":
                    knowledge_type_filter = "domain_rule"  # Prioritize rules/constraints
            
            knowledge_results = self.retrieve_knowledge(
                request.query,
                top_k=request.max_context_chunks,
                knowledge_type=knowledge_type_filter
            )
            
            # If filter returned few results, also get general results
            if len(knowledge_results) < 3 and knowledge_type_filter:
                general_results = self.retrieve_knowledge(
                    request.query,
                    top_k=request.max_context_chunks - len(knowledge_results)
                )
                knowledge_results.extend(general_results)
            
            context_chunks = [
                RetrievalResult(
                    source=r.get("source", "unknown"),
                    content=r.get("content", ""),
                    score=r.get("score", 0),
                    metadata=r.get("metadata", {})
                )
                for r in knowledge_results
            ]
        
        # 3. Query graph if needed
        graph_context = None
        if request.use_graph and self._graph_engine:
            graph_result = self.query_graph(request.query)
            if graph_result.get("results"):
                graph_context = json.dumps(graph_result["results"][:5], indent=2, default=str)
        
        # 4. Build context with data flow awareness
        context_parts = []
        
        # Add data flow context header if available
        if data_flow_context:
            phase_info = data_flow_context.get("operational_phase", "unknown")
            datasets = data_flow_context.get("datasets", [])
            ml_model = data_flow_context.get("ml_model")
            
            flow_header = f"[Data Flow: {phase_info} phase]"
            if datasets:
                flow_header += f"\n[Relevant datasets: {', '.join(datasets[:5])}]"
            if ml_model:
                flow_header += f"\n[ML Model: {ml_model}]"
            context_parts.append(flow_header)
        
        for chunk in context_chunks:
            context_parts.append(f"[{chunk.source}] {chunk.content}")
        
        if graph_context:
            context_parts.append(f"\n[Graph Data]\n{graph_context}")
        
        full_context = "\n\n".join(context_parts)
        
        # 5. Generate response
        answer = self.generate_response(request.query, full_context, intent)
        
        # 6. Calculate latency
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # 7. Update stats
        self._stats["queries_processed"] += 1
        n = self._stats["queries_processed"]
        self._stats["avg_latency_ms"] = (self._stats["avg_latency_ms"] * (n-1) + latency_ms) / n
        
        return PipelineQueryResponse(
            query=request.query,
            intent=intent.value,
            answer=answer,
            context_used=context_chunks,
            graph_context=graph_context,
            memory_used=request.use_memory,
            graph_used=bool(graph_context),
            latency_ms=latency_ms,
            model_used="claude-opus-4" if self._central_llm and self._central_llm._model_loaded else "qwen3-8b"
        )
    
    def get_stats(self) -> Dict:
        """Get pipeline statistics"""
        knowledge_stats = {}
        if self._knowledge_collection:
            knowledge_stats = {
                "total_chunks": self._knowledge_collection.count(),
                "collection_name": "smartberth_unified"
            }
        
        # Check graph engine status
        graph_stats = {"status": "disconnected"}
        graph_engine_available = False
        
        if self._graph_engine:
            # Check if it's the in-memory graph
            if hasattr(self._graph_engine, 'is_loaded') and self._graph_engine.is_loaded():
                graph_stats = self._graph_engine.get_stats()
                graph_stats["engine_type"] = "in-memory (NetworkX)"
                graph_engine_available = True
            # Check if it's Neo4j
            elif hasattr(self._graph_engine, 'driver') and self._graph_engine.driver:
                graph_stats = {"status": "connected", "engine_type": "neo4j"}
                graph_engine_available = True
        
        return {
            "knowledge_index": knowledge_stats,
            "graph_stats": graph_stats,
            "pipeline_stats": self._stats,
            "components": {
                "knowledge_index": self._knowledge_collection is not None,
                "graph_engine": graph_engine_available,
                "manager_agent": self._manager_agent is not None,
                "central_llm": self._central_llm is not None and self._central_llm._model_loaded
            }
        }


# ============================================================================
# GLOBAL PIPELINE INSTANCE
# ============================================================================

_pipeline_instance: Optional[UnifiedSmartBerthPipeline] = None


def get_pipeline() -> UnifiedSmartBerthPipeline:
    """Get or create the unified pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = UnifiedSmartBerthPipeline()
    return _pipeline_instance


# ============================================================================
# API ROUTER
# ============================================================================

router = APIRouter(prefix="/pipeline", tags=["Unified Pipeline"])


@router.on_event("startup")
async def startup_event():
    """Initialize pipeline on startup"""
    pipeline = get_pipeline()
    pipeline.initialize()


@router.post("/query", response_model=PipelineQueryResponse)
async def query_pipeline(request: PipelineQueryRequest):
    """
    Query the unified SmartBerth AI pipeline.
    
    This endpoint orchestrates:
    - Intent classification (Manager Agent)
    - Knowledge retrieval (ChromaDB)
    - Graph queries (Neo4j)
    - Response generation (Claude AI)
    """
    pipeline = get_pipeline()
    
    if not pipeline._initialized:
        pipeline.initialize()
    
    return await pipeline.process_query(request)


@router.get("/stats", response_model=PipelineStatsResponse)
async def get_pipeline_stats():
    """Get pipeline statistics and component status"""
    pipeline = get_pipeline()
    stats = pipeline.get_stats()
    return PipelineStatsResponse(**stats)


@router.post("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    """Search the knowledge base directly"""
    pipeline = get_pipeline()
    
    if not pipeline._knowledge_collection:
        raise HTTPException(status_code=503, detail="Knowledge index not available")
    
    results = pipeline.retrieve_knowledge(
        request.query,
        top_k=request.top_k,
        knowledge_type=request.knowledge_type
    )
    
    return KnowledgeSearchResponse(
        query=request.query,
        results=results,
        total_found=len(results)
    )


@router.post("/graph/query", response_model=GraphQueryResponse)
async def query_graph(request: GraphQueryRequest):
    """Query the Neo4j knowledge graph"""
    pipeline = get_pipeline()
    
    if not pipeline._graph_engine:
        raise HTTPException(status_code=503, detail="Graph engine not available")
    
    cypher_to_execute = request.cypher if request.query_type == "cypher" else request.query
    result = pipeline.query_graph(cypher_to_execute, request.query_type)
    
    return GraphQueryResponse(
        query=request.query,
        query_type=request.query_type,
        cypher_executed=result.get("cypher"),
        results=result.get("results", []),
        total_results=len(result.get("results", []))
    )


@router.post("/ingest")
async def ingest_document(request: IngestDocumentRequest):
    """Ingest a new document into the knowledge base"""
    pipeline = get_pipeline()
    
    if not pipeline._knowledge_collection:
        raise HTTPException(status_code=503, detail="Knowledge index not available")
    
    try:
        # Generate ID
        import hashlib
        doc_id = f"api_{hashlib.md5(request.content[:100].encode()).hexdigest()[:12]}"
        
        # Add to collection
        pipeline._knowledge_collection.add(
            ids=[doc_id],
            documents=[request.content],
            metadatas=[{
                "source": request.source,
                "knowledge_type": request.knowledge_type,
                "ingested_at": datetime.now().isoformat(),
                **request.metadata
            }]
        )
        
        return {
            "success": True,
            "document_id": doc_id,
            "message": "Document ingested successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {e}")


@router.get("/health")
async def pipeline_health():
    """Check pipeline health status"""
    pipeline = get_pipeline()
    
    return {
        "status": "healthy" if pipeline._initialized else "initializing",
        "components": {
            "knowledge_index": pipeline._knowledge_collection is not None,
            "graph_engine": pipeline._graph_engine is not None,
            "manager_agent": pipeline._manager_agent is not None,
            "central_llm": pipeline._central_llm is not None and pipeline._central_llm._model_loaded
        },
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# SPECIALIZED QUERY ENDPOINTS
# ============================================================================

@router.get("/berth/compatible")
async def find_compatible_berths(
    vessel_type: Optional[str] = Query(None, description="Vessel type filter"),
    min_loa: Optional[float] = Query(None, description="Minimum LOA in meters"),
    min_depth: Optional[float] = Query(None, description="Minimum depth in meters"),
    port_code: Optional[str] = Query(None, description="Port code filter")
):
    """Find berths compatible with vessel requirements"""
    pipeline = get_pipeline()
    
    if not pipeline._graph_engine:
        raise HTTPException(status_code=503, detail="Graph engine not available")
    
    results = pipeline._graph_engine.find_compatible_berths(
        vessel_type=vessel_type,
        min_loa=min_loa,
        min_depth=min_depth,
        port_code=port_code
    )
    
    return {
        "filters": {
            "vessel_type": vessel_type,
            "min_loa": min_loa,
            "min_depth": min_depth,
            "port_code": port_code
        },
        "results": results,
        "count": len(results)
    }


@router.get("/port/{port_code}/resources")
async def get_port_resources(port_code: str):
    """Get all resources available at a port"""
    pipeline = get_pipeline()
    
    if not pipeline._graph_engine:
        raise HTTPException(status_code=503, detail="Graph engine not available")
    
    resources = pipeline._graph_engine.get_port_resources(port_code)
    
    if not resources:
        raise HTTPException(status_code=404, detail=f"Port {port_code} not found")
    
    return resources


@router.get("/vessel/history")
async def get_vessel_history(
    vessel_name: Optional[str] = Query(None, description="Vessel name search"),
    imo_number: Optional[str] = Query(None, description="IMO number"),
    limit: int = Query(10, ge=1, le=50)
):
    """Get vessel call history"""
    pipeline = get_pipeline()
    
    if not pipeline._graph_engine:
        raise HTTPException(status_code=503, detail="Graph engine not available")
    
    if not vessel_name and not imo_number:
        raise HTTPException(status_code=400, detail="Provide vessel_name or imo_number")
    
    results = pipeline._graph_engine.find_vessel_history(
        vessel_name=vessel_name,
        imo_number=imo_number,
        limit=limit
    )
    
    return {
        "search": {"vessel_name": vessel_name, "imo_number": imo_number},
        "results": results,
        "count": len(results)
    }
