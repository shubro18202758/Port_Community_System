"""
GPU-Accelerated RAG Service for Berth Planning AI
==================================================
Optimized retrieval with GPU acceleration
Uses the fine-tuned ChromaDB collection
"""

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import time
from dataclasses import dataclass

# ============================================================================
# GPU-OPTIMIZED EMBEDDING FUNCTION
# ============================================================================

class GPUEmbeddingFunction:
    """GPU-accelerated embedding function for ChromaDB"""
    
    _instance = None
    _model = None
    
    def __new__(cls, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(model_name)
        return cls._instance
    
    def _initialize(self, model_name: str):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._model_name = model_name
        
        print(f"Initializing GPU Embedding Function on {self.device.upper()}")
        self.model = SentenceTransformer(model_name, device=self.device)
        self.model.max_seq_length = 512
        
        # Warmup
        _ = self.model.encode(["warmup"], convert_to_numpy=True)
        print(f"✓ Embedding model loaded: {model_name}")
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(
            input,
            batch_size=64,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings.tolist()
    
    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return self.__call__(input)
    
    def embed_query(self, input) -> List[List[float]]:
        if isinstance(input, list):
            texts = input
        else:
            texts = [input]
        embeddings = self.model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True
        )
        return embeddings.tolist()
    
    def name(self) -> str:
        return self._model_name


# ============================================================================
# OPTIMIZED RAG SERVICE
# ============================================================================

@dataclass
class RetrievalResult:
    """Single retrieval result"""
    text: str
    source: str
    domains: str
    score: float
    metadata: Dict[str, Any]


class OptimizedRAGService:
    """GPU-accelerated RAG service for Berth Planning AI"""
    
    def __init__(
        self,
        chroma_path: str = None,
        collection_name: str = "berth_planning_optimized",
        model_name: str = "sentence-transformers/all-mpnet-base-v2"
    ):
        self.chroma_path = chroma_path or str(
            Path(__file__).parent / "chroma_db_optimized"
        )
        self.collection_name = collection_name
        self.model_name = model_name
        
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._initialized = False
    
    def initialize(self):
        """Initialize the RAG service"""
        if self._initialized:
            return
        
        print(f"Initializing Optimized RAG Service...")
        print(f"  ChromaDB: {self.chroma_path}")
        print(f"  Collection: {self.collection_name}")
        
        # Initialize embedding function (singleton)
        self._embedding_fn = GPUEmbeddingFunction(self.model_name)
        
        # Initialize ChromaDB client
        self._client = chromadb.PersistentClient(
            path=self.chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get collection
        self._collection = self._client.get_collection(
            name=self.collection_name,
            embedding_function=self._embedding_fn
        )
        
        print(f"✓ RAG Service initialized with {self._collection.count()} chunks")
        self._initialized = True
    
    def retrieve(
        self,
        query: str,
        n_results: int = 5,
        filter_domains: Optional[List[str]] = None
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: The search query
            n_results: Number of results to return
            filter_domains: Optional list of domains to filter by
            
        Returns:
            List of RetrievalResult objects
        """
        if not self._initialized:
            self.initialize()
        
        start_time = time.time()
        
        # Build filter if domains specified
        where_filter = None
        if filter_domains:
            # ChromaDB doesn't support $contains, use alternative approach
            pass  # Skip filtering for now, post-filter instead
        
        # Query ChromaDB
        results = self._collection.query(
            query_texts=[query],
            n_results=n_results * 2 if filter_domains else n_results,  # Get more for filtering
            include=["documents", "metadatas", "distances"]
        )
        
        # Process results
        retrieval_results = []
        
        for i, (doc, meta, dist) in enumerate(zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        )):
            # Post-filter by domain if specified
            if filter_domains:
                doc_domains = meta.get("domains", "").split(",")
                if not any(d in doc_domains for d in filter_domains):
                    continue
            
            # Convert distance to score (cosine similarity)
            score = 1 - dist  # ChromaDB returns distance, not similarity
            
            retrieval_results.append(RetrievalResult(
                text=doc,
                source=meta.get("source", "unknown"),
                domains=meta.get("domains", ""),
                score=score,
                metadata=meta
            ))
            
            if len(retrieval_results) >= n_results:
                break
        
        elapsed = (time.time() - start_time) * 1000
        
        return retrieval_results
    
    def query_with_context(
        self,
        query: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Query and return structured context for AI
        
        Args:
            query: The user query
            n_results: Number of context chunks to retrieve
            
        Returns:
            Dictionary with query, context, and metadata
        """
        results = self.retrieve(query, n_results)
        
        # Build context string
        context_parts = []
        sources = set()
        
        for i, result in enumerate(results, 1):
            context_parts.append(f"[{i}] {result.text[:500]}...")
            sources.add(result.source)
        
        return {
            "query": query,
            "context": "\n\n".join(context_parts),
            "sources": list(sources),
            "results": [
                {
                    "source": r.source,
                    "domains": r.domains,
                    "score": round(r.score, 3),
                    "text_preview": r.text[:200]
                }
                for r in results
            ],
            "num_results": len(results)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        if not self._initialized:
            self.initialize()
        
        return {
            "collection_name": self.collection_name,
            "total_chunks": self._collection.count(),
            "chroma_path": self.chroma_path,
            "model": self.model_name,
            "device": self._embedding_fn.device if self._embedding_fn else "unknown"
        }


# ============================================================================
# GLOBAL SERVICE INSTANCE
# ============================================================================

_rag_service: Optional[OptimizedRAGService] = None


def get_rag_service() -> OptimizedRAGService:
    """Get the global RAG service instance"""
    global _rag_service
    if _rag_service is None:
        _rag_service = OptimizedRAGService()
        _rag_service.initialize()
    return _rag_service


def retrieve_context(query: str, n_results: int = 5) -> Dict[str, Any]:
    """
    Convenience function to retrieve context for a query
    
    Args:
        query: The user query
        n_results: Number of results
        
    Returns:
        Dictionary with context and metadata
    """
    service = get_rag_service()
    return service.query_with_context(query, n_results)


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("OPTIMIZED RAG SERVICE TEST")
    print("="*70)
    
    service = get_rag_service()
    
    print(f"\nService Stats: {json.dumps(service.get_stats(), indent=2)}")
    
    # Test queries
    test_queries = [
        "What is the tidal pattern at Mundra Port?",
        "List berths at Mundra Container Terminal",
        "Vessel schedule for Mundra Port",
        "UKC requirements for deep draft vessels",
        "Weather conditions at Mundra",
    ]
    
    print("\n" + "-"*70)
    print("TEST QUERIES")
    print("-"*70)
    
    for query in test_queries:
        start = time.time()
        result = service.query_with_context(query, n_results=3)
        elapsed = (time.time() - start) * 1000
        
        print(f"\n Query: {query}")
        print(f"   Time: {elapsed:.1f}ms")
        print(f"   Sources: {', '.join(result['sources'][:3])}")
        print(f"   Top Score: {result['results'][0]['score']:.3f}")
    
    print("\n" + "="*70)
    print("✓ RAG Service Test Complete")
    print("="*70)
