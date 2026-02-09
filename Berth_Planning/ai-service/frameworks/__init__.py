"""
SmartBerth AI - Advanced RAG Frameworks Integration
====================================================

Architecture Overview:
----------------------
┌─────────────────────────────────────────────────────────────────────┐
│                    MANAGER AGENT (Qwen3-8B GPU)                      │
│                   Autonomous Orchestration Layer                     │
├─────────────────────────────────────────────────────────────────────┤
│  • Task Classification  • Execution Planning  • Agent Coordination   │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
┌───────────────────┐ ┌─────────────────┐ ┌─────────────────────────┐
│   RAG Pipeline    │ │  Graph System   │ │   CENTRAL AI (Claude)   │
│   (6 Frameworks)  │ │    (Neo4j)      │ │   Complex Reasoning     │
└───────────────────┘ └─────────────────┘ └─────────────────────────┘

Framework Tiers:
----------------
TIER 1 - Evaluation & Optimization:
  ├── RAGAS      - RAG evaluation (faithfulness, relevance, precision)
  └── DSPy       - Prompt optimization & automatic tuning

TIER 2 - Advanced Retrieval:
  ├── GraphRAG   - Microsoft's graph-enhanced retrieval
  └── Ragatouille - ColBERT late-interaction dense retrieval

TIER 3 - Real-time & Memory:
  ├── Pathway    - Real-time data synchronization
  └── Mem0       - Persistent conversation memory
"""

# Imports from implemented modules
from .ragas_eval import RagasEvaluator, get_ragas_evaluator
from .dspy_optimizer import DSPyOptimizer, get_dspy_optimizer
from .graphrag_engine import GraphRAGEngine, get_graphrag_engine
from .colbert_retriever import (
    ColBERTRetriever, 
    RagatouilleRetriever, 
    get_colbert_retriever, 
    get_ragatouille_retriever
)
from .pathway_sync import PathwaySyncPipeline, get_pathway_pipeline
from .mem0_memory import Mem0MemoryManager, get_memory_manager

# Framework versions and status
FRAMEWORK_INFO = {
    "ragas": {
        "tier": 1,
        "name": "RAGAS",
        "class": "RagasEvaluator",
        "description": "RAG evaluation metrics",
        "capabilities": ["faithfulness", "relevance", "context_precision", "context_recall"],
        "status": "implemented"
    },
    "dspy": {
        "tier": 1,
        "name": "DSPy",
        "class": "DSPyOptimizer",
        "description": "Prompt optimization framework",
        "capabilities": ["prompt_tuning", "signature_optimization", "chain_of_thought"],
        "status": "implemented"
    },
    "graphrag": {
        "tier": 2,
        "name": "GraphRAG",
        "class": "GraphRAGEngine",
        "description": "Microsoft graph-enhanced RAG",
        "capabilities": ["entity_extraction", "community_detection", "global_search", "local_search"],
        "status": "implemented"
    },
    "ragatouille": {
        "tier": 2,
        "name": "Ragatouille",
        "class": "RagatouilleRetriever",
        "description": "ColBERT-based dense retrieval",
        "capabilities": ["late_interaction", "efficient_reranking", "index_compression"],
        "status": "implemented"
    },
    "pathway": {
        "tier": 3,
        "name": "Pathway",
        "class": "PathwaySyncPipeline",
        "description": "Real-time data pipeline",
        "capabilities": ["live_sync", "incremental_indexing", "change_detection"],
        "status": "implemented"
    },
    "mem0": {
        "tier": 3,
        "name": "Mem0",
        "class": "Mem0MemoryManager",
        "description": "Persistent memory layer",
        "capabilities": ["conversation_memory", "user_context", "long_term_storage"],
        "status": "implemented"
    }
}


def get_framework_info(name: str = None):
    """Get information about available frameworks"""
    if name:
        return FRAMEWORK_INFO.get(name)
    return FRAMEWORK_INFO


def get_tier_frameworks(tier: int):
    """Get all frameworks in a specific tier"""
    return {k: v for k, v in FRAMEWORK_INFO.items() if v["tier"] == tier}


__all__ = [
    # Framework info
    "FRAMEWORK_INFO",
    "get_framework_info",
    "get_tier_frameworks",
    # Tier 1 - Evaluation & Optimization
    "RagasEvaluator", "get_ragas_evaluator",
    "DSPyOptimizer", "get_dspy_optimizer",
    # Tier 2 - Advanced Retrieval
    "GraphRAGEngine", "get_graphrag_engine",
    "ColBERTRetriever", "RagatouilleRetriever", 
    "get_colbert_retriever", "get_ragatouille_retriever",
    # Tier 3 - Real-time & Memory
    "PathwaySyncPipeline", "get_pathway_pipeline",
    "Mem0MemoryManager", "get_memory_manager",
]
