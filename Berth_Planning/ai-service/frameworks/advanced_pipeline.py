"""
Advanced RAG Pipeline - Unified Integration of All 6 Frameworks
================================================================

This module provides a unified pipeline that integrates all implemented
frameworks into a cohesive RAG system:

- Manager Agent (Qwen3-8B via Ollama) orchestrates all operations
- Central AI (Claude Opus 4) handles complex reasoning
- ChromaDB for vector storage
- Neo4j for knowledge graph
- All 6 SOTA frameworks working together

Flow:
1. Query → Manager Agent classifies intent
2. Memory retrieval (Mem0) for context
3. Parallel retrieval (ChromaDB + ColBERT + GraphRAG)
4. Reranking with ColBERT
5. DSPy-optimized prompts for generation
6. Central AI generates response
7. RAGAS evaluation of quality
8. Memory update (Mem0)
9. Real-time sync (Pathway) for updates
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Framework imports
from .ragas_eval import RagasEvaluator, get_ragas_evaluator
from .dspy_optimizer import DSPyOptimizer, get_dspy_optimizer
from .graphrag_engine import GraphRAGEngine, get_graphrag_engine
from .colbert_retriever import ColBERTRetriever, RagatouilleRetriever, get_ragatouille_retriever
from .pathway_sync import PathwaySyncPipeline, get_pathway_pipeline, SourceType
from .mem0_memory import Mem0MemoryManager, get_memory_manager, MemoryType

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA STRUCTURES
# ============================================================================

class QueryIntent(Enum):
    """Types of query intents"""
    RETRIEVAL = "retrieval"          # Need to retrieve information
    REASONING = "reasoning"          # Complex reasoning needed
    GRAPH_QUERY = "graph_query"      # Graph traversal needed
    MEMORY_RECALL = "memory_recall"  # User context recall
    GENERATION = "generation"        # Content generation
    HYBRID = "hybrid"                # Multiple needs


class RetrievalSource(Enum):
    """Sources for retrieval"""
    CHROMADB = "chromadb"
    COLBERT = "colbert"
    GRAPHRAG = "graphrag"
    MEMORY = "memory"


@dataclass
class RetrievalResult:
    """Result from a retrieval source"""
    source: RetrievalSource
    documents: List[Dict[str, Any]]
    scores: List[float]
    latency_ms: float


@dataclass
class PipelineResponse:
    """Complete pipeline response"""
    query: str
    intent: QueryIntent
    answer: str
    
    # Retrieval info
    retrieval_results: Dict[str, RetrievalResult] = field(default_factory=dict)
    merged_context: str = ""
    
    # Evaluation
    evaluation_scores: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    memory_used: bool = False
    graph_used: bool = False
    latency_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# ADVANCED RAG PIPELINE
# ============================================================================

class AdvancedRAGPipeline:
    """
    Unified RAG pipeline integrating all 6 frameworks.
    
    Components:
    - Qwen3-8B (Ollama): Manager Agent for orchestration
    - Claude Opus 4: Central AI for generation
    - ChromaDB: Vector storage
    - Neo4j: Knowledge graph
    - RAGAS: Evaluation
    - DSPy: Prompt optimization
    - GraphRAG: Graph-enhanced retrieval
    - ColBERT: Late interaction reranking
    - Pathway: Real-time sync
    - Mem0: Memory layer
    """
    
    def __init__(
        self,
        manager_llm_caller,        # Qwen3-8B via Ollama
        central_llm_caller,        # Claude Opus 4
        embedder,                  # Embedding function
        vector_store=None,         # ChromaDB instance
        neo4j_driver=None,         # Neo4j driver
        enable_evaluation: bool = True,
        enable_memory: bool = True,
        enable_realtime_sync: bool = False
    ):
        """
        Initialize the advanced RAG pipeline
        
        Args:
            manager_llm_caller: Function to call Manager Agent (Qwen3)
            central_llm_caller: Function to call Central AI (Claude)
            embedder: Function to generate embeddings
            vector_store: ChromaDB collection instance
            neo4j_driver: Neo4j driver for graph operations
            enable_evaluation: Enable RAGAS evaluation
            enable_memory: Enable Mem0 memory
            enable_realtime_sync: Enable Pathway real-time sync
        """
        self.manager_llm = manager_llm_caller
        self.central_llm = central_llm_caller
        self.embedder = embedder
        self.vector_store = vector_store
        self.neo4j_driver = neo4j_driver
        
        # Initialize frameworks
        logger.info("Initializing Advanced RAG Pipeline frameworks...")
        
        # Tier 1: Evaluation & Optimization
        self.ragas = get_ragas_evaluator(central_llm_caller) if enable_evaluation else None
        self.dspy = get_dspy_optimizer(manager_llm_caller)
        
        # Tier 2: Advanced Retrieval
        self.graphrag = get_graphrag_engine(manager_llm_caller, embedder, neo4j_driver)
        self.colbert = get_ragatouille_retriever(model_name="smartberth-colbert")
        
        # Tier 3: Real-time & Memory
        self.pathway = get_pathway_pipeline(embedder, vector_store) if enable_realtime_sync else None
        self.memory = get_memory_manager(manager_llm_caller, embedder) if enable_memory else None
        
        # Stats tracking
        self.stats = {
            "queries_processed": 0,
            "avg_latency_ms": 0.0,
            "avg_ragas_score": 0.0,
            "cache_hits": 0
        }
        
        logger.info("Advanced RAG Pipeline initialized successfully")
    
    async def process(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        use_memory: bool = True,
        use_graph: bool = True,
        evaluate: bool = True
    ) -> PipelineResponse:
        """
        Process a query through the full pipeline
        
        Args:
            query: User query
            user_id: User ID for memory personalization
            session_id: Session ID for context
            use_memory: Use memory for context
            use_graph: Use graph retrieval
            evaluate: Evaluate response quality
            
        Returns:
            Complete pipeline response
        """
        start_time = datetime.now()
        
        # Step 1: Classify query intent with Manager Agent
        intent = await self._classify_intent(query)
        logger.info(f"Query intent: {intent.value}")
        
        # Step 2: Retrieve memory context (Mem0)
        memory_context = ""
        if use_memory and self.memory:
            memory_context = self.memory.get_context(query, user_id)
        
        # Step 3: Parallel retrieval from multiple sources
        retrieval_results = await self._parallel_retrieval(
            query, 
            use_graph=use_graph,
            intent=intent
        )
        
        # Step 4: Merge and rerank with ColBERT
        merged_context = self._merge_and_rerank(query, retrieval_results)
        
        # Step 5: Get optimized prompt from DSPy
        optimized_prompt = self._get_optimized_prompt(query, merged_context, memory_context)
        
        # Step 6: Generate response with Central AI (Claude)
        answer = await self._generate_response(optimized_prompt)
        
        # Step 7: Evaluate with RAGAS
        evaluation_scores = {}
        if evaluate and self.ragas:
            evaluation_scores = await self._evaluate_response(
                query, answer, merged_context
            )
        
        # Step 8: Update memory
        if use_memory and self.memory and user_id:
            self.memory.add_from_conversation(query, answer, user_id, session_id)
        
        # Calculate latency
        latency_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Update stats
        self._update_stats(latency_ms, evaluation_scores)
        
        return PipelineResponse(
            query=query,
            intent=intent,
            answer=answer,
            retrieval_results=retrieval_results,
            merged_context=merged_context[:1000],  # Truncate for response
            evaluation_scores=evaluation_scores,
            memory_used=bool(memory_context),
            graph_used=use_graph,
            latency_ms=latency_ms
        )
    
    async def _classify_intent(self, query: str) -> QueryIntent:
        """Classify query intent using Manager Agent"""
        prompt = f"""/no_think
Classify this query into one category:
- retrieval: Need to find specific information
- reasoning: Need complex analysis or explanation
- graph_query: Need to explore relationships
- memory_recall: Asking about past context
- generation: Need to create new content
- hybrid: Multiple of the above

Query: {query}

Output JSON: {{"intent": "category"}}"""
        
        response = self.manager_llm(prompt)
        
        # Parse response
        import json
        try:
            if "{" in response:
                data = json.loads(response[response.index("{"):response.rindex("}")+1])
                intent_str = data.get("intent", "retrieval")
                return QueryIntent(intent_str)
        except (json.JSONDecodeError, ValueError):
            pass
        
        return QueryIntent.RETRIEVAL
    
    async def _parallel_retrieval(
        self,
        query: str,
        use_graph: bool,
        intent: QueryIntent
    ) -> Dict[str, RetrievalResult]:
        """Perform parallel retrieval from multiple sources"""
        results = {}
        
        # ChromaDB retrieval
        if self.vector_store:
            chroma_start = datetime.now()
            try:
                chroma_results = self.vector_store.query(
                    query_texts=[query],
                    n_results=5
                )
                chroma_docs = []
                chroma_scores = []
                
                if chroma_results and chroma_results.get("documents"):
                    for i, doc in enumerate(chroma_results["documents"][0]):
                        chroma_docs.append({
                            "content": doc,
                            "metadata": chroma_results.get("metadatas", [[]])[0][i] if chroma_results.get("metadatas") else {}
                        })
                        chroma_scores.append(1.0 - (chroma_results.get("distances", [[]])[0][i] if chroma_results.get("distances") else 0))
                
                results["chromadb"] = RetrievalResult(
                    source=RetrievalSource.CHROMADB,
                    documents=chroma_docs,
                    scores=chroma_scores,
                    latency_ms=(datetime.now() - chroma_start).total_seconds() * 1000
                )
            except Exception as e:
                logger.error(f"ChromaDB retrieval failed: {e}")
        
        # GraphRAG retrieval
        if use_graph and self.graphrag and self.graphrag.index:
            graph_start = datetime.now()
            try:
                if intent == QueryIntent.GRAPH_QUERY:
                    graph_result = self.graphrag.local_search(query)
                else:
                    graph_result = self.graphrag.global_search(query)
                
                results["graphrag"] = RetrievalResult(
                    source=RetrievalSource.GRAPHRAG,
                    documents=[{"content": graph_result.get("context", ""), "answer": graph_result.get("answer", "")}],
                    scores=[1.0],
                    latency_ms=(datetime.now() - graph_start).total_seconds() * 1000
                )
            except Exception as e:
                logger.error(f"GraphRAG retrieval failed: {e}")
        
        # ColBERT retrieval (if index exists)
        colbert_stats = self.colbert.colbert.get_stats() if hasattr(self.colbert, 'colbert') else {}
        if colbert_stats.get("status") == "ready":
            colbert_start = datetime.now()
            try:
                colbert_results = self.colbert.search(query, k=5)
                results["colbert"] = RetrievalResult(
                    source=RetrievalSource.COLBERT,
                    documents=colbert_results,
                    scores=[r.get("score", 0) for r in colbert_results],
                    latency_ms=(datetime.now() - colbert_start).total_seconds() * 1000
                )
            except Exception as e:
                logger.error(f"ColBERT retrieval failed: {e}")
        
        return results
    
    def _merge_and_rerank(
        self,
        query: str,
        retrieval_results: Dict[str, RetrievalResult]
    ) -> str:
        """Merge results from all sources and rerank with ColBERT"""
        all_docs = []
        
        # Collect all documents
        for source_name, result in retrieval_results.items():
            for i, doc in enumerate(result.documents):
                content = doc.get("content", "") if isinstance(doc, dict) else str(doc)
                score = result.scores[i] if i < len(result.scores) else 0.5
                all_docs.append({
                    "content": content,
                    "source": source_name,
                    "original_score": score
                })
        
        # Rerank with ColBERT if we have documents
        if all_docs:
            try:
                reranked = self.colbert.rerank(
                    query,
                    [d["content"] for d in all_docs],
                    k=10
                )
                # Build merged context from reranked results
                context_parts = []
                for r in reranked[:5]:
                    context_parts.append(r.get("content", ""))
                return "\n\n---\n\n".join(context_parts)
            except Exception as e:
                logger.warning(f"Reranking failed, using original order: {e}")
        
        # Fallback: concatenate top results
        context_parts = [d["content"] for d in all_docs[:5] if d.get("content")]
        return "\n\n---\n\n".join(context_parts)
    
    def _get_optimized_prompt(
        self,
        query: str,
        context: str,
        memory_context: str
    ) -> str:
        """Get optimized prompt using DSPy"""
        # Use DSPy RAG signature
        try:
            from .dspy_optimizer import RAG_RESPONSE_SIG
            
            # Build optimized prompt
            prompt = f"""You are an expert assistant for SmartBerth port operations.

{f"User Context (from memory):{chr(10)}{memory_context}{chr(10)}" if memory_context else ""}

Retrieved Information:
{context}

User Question: {query}

Provide a helpful, accurate response based on the retrieved information.
If the information is insufficient, acknowledge what you know and what's missing.
"""
            return prompt
        except Exception as e:
            logger.warning(f"DSPy prompt optimization failed: {e}")
            return f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
    
    async def _generate_response(self, prompt: str) -> str:
        """Generate response using Central AI (Claude)"""
        try:
            # Check if central_llm is async
            if asyncio.iscoroutinefunction(self.central_llm):
                return await self.central_llm(prompt)
            else:
                return self.central_llm(prompt)
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I apologize, but I encountered an error generating the response."
    
    async def _evaluate_response(
        self,
        query: str,
        answer: str,
        context: str
    ) -> Dict[str, float]:
        """Evaluate response quality using RAGAS"""
        try:
            result = await self.ragas.aevaluate(
                query=query,
                answer=answer,
                contexts=[context]
            )
            return {
                "faithfulness": result.faithfulness,
                "relevance": result.answer_relevance,
                "precision": result.context_precision,
                "recall": result.context_recall,
                "overall": result.overall_score
            }
        except Exception as e:
            logger.warning(f"RAGAS evaluation failed: {e}")
            return {}
    
    def _update_stats(self, latency_ms: float, evaluation_scores: Dict[str, float]):
        """Update pipeline statistics"""
        n = self.stats["queries_processed"]
        self.stats["queries_processed"] = n + 1
        self.stats["avg_latency_ms"] = (self.stats["avg_latency_ms"] * n + latency_ms) / (n + 1)
        
        if evaluation_scores.get("overall"):
            self.stats["avg_ragas_score"] = (
                self.stats["avg_ragas_score"] * n + evaluation_scores["overall"]
            ) / (n + 1)
    
    # ========================================================================
    # INDEX MANAGEMENT
    # ========================================================================
    
    def build_indices(self, documents: List[Dict[str, Any]]):
        """Build all retrieval indices"""
        logger.info(f"Building indices from {len(documents)} documents")
        
        # Build ColBERT index
        texts = [d.get("content", "") for d in documents]
        ids = [d.get("id", f"doc_{i}") for i, d in enumerate(documents)]
        self.colbert.index(texts, document_ids=ids)
        
        # Build GraphRAG index
        self.graphrag.build_index(documents)
        
        logger.info("All indices built successfully")
    
    def setup_realtime_sync(self, sources: List[Dict[str, Any]]):
        """Setup real-time data synchronization"""
        if not self.pathway:
            logger.warning("Pathway not enabled")
            return
        
        for source in sources:
            self.pathway.add_source(
                name=source.get("name"),
                source_type=SourceType(source.get("type", "file")),
                config=source.get("config", {}),
                poll_interval=source.get("poll_interval", 60.0)
            )
        
        self.pathway.start_background_sync()
    
    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status and statistics"""
        return {
            "pipeline_status": "ready",
            "stats": self.stats,
            "components": {
                "ragas": "enabled" if self.ragas else "disabled",
                "dspy": "enabled",
                "graphrag": self.graphrag.get_stats() if self.graphrag else "disabled",
                "colbert": self.colbert.colbert.get_stats() if hasattr(self.colbert, 'colbert') else "unknown",
                "pathway": self.pathway.get_status() if self.pathway else "disabled",
                "memory": self.memory.get_stats() if self.memory else "disabled"
            }
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_advanced_pipeline(
    manager_llm_caller,
    central_llm_caller,
    embedder,
    **kwargs
) -> AdvancedRAGPipeline:
    """
    Create an advanced RAG pipeline instance
    
    Args:
        manager_llm_caller: Qwen3-8B via Ollama
        central_llm_caller: Claude Opus 4 via Anthropic
        embedder: Embedding function
        **kwargs: Additional configuration
        
    Returns:
        Configured AdvancedRAGPipeline instance
    """
    return AdvancedRAGPipeline(
        manager_llm_caller=manager_llm_caller,
        central_llm_caller=central_llm_caller,
        embedder=embedder,
        **kwargs
    )
