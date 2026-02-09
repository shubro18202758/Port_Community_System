"""
Hybrid Retriever for SmartBerth AI
Combines vector similarity search with BM25 keyword search
Adapted from Azure DevOps ai-backend/rag/retriever.py
"""

import os
import sys
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np

import chromadb
from sentence_transformers import SentenceTransformer

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import get_settings

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("Warning: rank_bm25 not installed. BM25 search disabled.")


@dataclass
class RetrievedDocument:
    """Represents a retrieved document with metadata"""
    content: str
    source: str
    category: str
    score: float
    metadata: Dict[str, Any]
    retrieval_method: str  # 'vector', 'bm25', or 'hybrid'


class HybridRetriever:
    """
    Hybrid retriever combining vector similarity and BM25 keyword search
    
    Retrieval Strategy:
    - Vector search: Semantic similarity using sentence embeddings
    - BM25 search: Keyword/term frequency based ranking
    - Hybrid: Weighted combination (default 70% vector, 30% BM25)
    """

    def __init__(
        self,
        collection_name: str = "smartberth_knowledge",
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3
    ):
        """
        Initialize the hybrid retriever
        
        Args:
            collection_name: ChromaDB collection name
            embedding_model: Sentence transformer model name
            vector_weight: Weight for vector search results (0-1)
            bm25_weight: Weight for BM25 search results (0-1)
        """
        self.settings = get_settings()
        self.collection_name = collection_name
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        persist_dir = self.settings.chroma_persist_dir
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)
        
        try:
            self.collection = self.chroma_client.get_collection(
                name=collection_name
            )
            print(f"Loaded ChromaDB collection: {collection_name}")
            print(f"Documents in collection: {self.collection.count()}")
        except Exception as e:
            print(f"Warning: Could not load collection {collection_name}: {e}")
            self.collection = None
        
        # Initialize BM25 index
        self.bm25_index = None
        self.document_corpus = []
        self.document_ids = []
        
        if BM25_AVAILABLE and self.collection:
            self._build_bm25_index()

    def _build_bm25_index(self):
        """Build BM25 index from all documents in collection"""
        if not self.collection:
            return
            
        try:
            # Get all documents
            all_docs = self.collection.get(
                include=["documents", "metadatas"]
            )
            
            if not all_docs["documents"]:
                print("No documents found for BM25 indexing")
                return
            
            self.document_ids = all_docs["ids"]
            self.document_corpus = all_docs["documents"]
            self.document_metadata = all_docs["metadatas"]
            
            # Tokenize documents for BM25
            tokenized_corpus = [
                doc.lower().split() for doc in self.document_corpus
            ]
            
            self.bm25_index = BM25Okapi(tokenized_corpus)
            print(f"Built BM25 index with {len(self.document_corpus)} documents")
            
        except Exception as e:
            print(f"Error building BM25 index: {e}")
            self.bm25_index = None

    def vector_search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[RetrievedDocument]:
        """
        Perform vector similarity search
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            List of retrieved documents
        """
        if not self.collection:
            return []
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query).tolist()
        
        # Query ChromaDB
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["documents", "metadatas", "distances"]
        }
        
        if filter_dict:
            kwargs["where"] = filter_dict
        
        results = self.collection.query(**kwargs)
        
        # Convert to RetrievedDocument objects
        documents = []
        for i, doc in enumerate(results["documents"][0]):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0
            
            # Convert distance to similarity score (ChromaDB uses L2)
            score = 1 / (1 + distance)
            
            documents.append(RetrievedDocument(
                content=doc,
                source=metadata.get("source", "unknown"),
                category=metadata.get("category", "unknown"),
                score=score,
                metadata=metadata,
                retrieval_method="vector"
            ))
        
        return documents

    def bm25_search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[RetrievedDocument]:
        """
        Perform BM25 keyword search
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of retrieved documents
        """
        if not BM25_AVAILABLE or not self.bm25_index:
            return []
        
        # Tokenize query
        tokenized_query = query.lower().split()
        
        # Get BM25 scores
        scores = self.bm25_index.get_scores(tokenized_query)
        
        # Get top-k indices
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        # Build results
        documents = []
        max_score = max(scores) if max(scores) > 0 else 1
        
        for idx in top_indices:
            if scores[idx] > 0:  # Only include documents with positive scores
                metadata = self.document_metadata[idx] if self.document_metadata else {}
                
                documents.append(RetrievedDocument(
                    content=self.document_corpus[idx],
                    source=metadata.get("source", "unknown"),
                    category=metadata.get("category", "unknown"),
                    score=scores[idx] / max_score,  # Normalize to 0-1
                    metadata=metadata,
                    retrieval_method="bm25"
                ))
        
        return documents

    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        filter_dict: Optional[Dict] = None,
        vector_weight: Optional[float] = None,
        bm25_weight: Optional[float] = None
    ) -> List[RetrievedDocument]:
        """
        Perform hybrid search combining vector and BM25
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_dict: Optional metadata filter (vector search only)
            vector_weight: Override default vector weight
            bm25_weight: Override default BM25 weight
            
        Returns:
            List of retrieved documents with combined scores
        """
        v_weight = vector_weight if vector_weight is not None else self.vector_weight
        b_weight = bm25_weight if bm25_weight is not None else self.bm25_weight
        
        # Normalize weights
        total_weight = v_weight + b_weight
        v_weight = v_weight / total_weight
        b_weight = b_weight / total_weight
        
        # Get results from both methods
        vector_results = self.vector_search(query, top_k * 2, filter_dict)
        bm25_results = self.bm25_search(query, top_k * 2)
        
        # Combine results using content as key
        combined_scores = {}
        combined_docs = {}
        
        # Add vector results
        for doc in vector_results:
            key = doc.content[:100]  # Use first 100 chars as key
            combined_scores[key] = doc.score * v_weight
            combined_docs[key] = doc
        
        # Add BM25 results
        for doc in bm25_results:
            key = doc.content[:100]
            if key in combined_scores:
                combined_scores[key] += doc.score * b_weight
                combined_docs[key].retrieval_method = "hybrid"
            else:
                combined_scores[key] = doc.score * b_weight
                combined_docs[key] = doc
        
        # Sort by combined score
        sorted_keys = sorted(
            combined_scores.keys(),
            key=lambda k: combined_scores[k],
            reverse=True
        )[:top_k]
        
        # Build final results
        results = []
        for key in sorted_keys:
            doc = combined_docs[key]
            doc.score = combined_scores[key]
            results.append(doc)
        
        return results

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        method: str = "hybrid",
        filter_dict: Optional[Dict] = None
    ) -> List[RetrievedDocument]:
        """
        Main retrieval method
        
        Args:
            query: Search query
            top_k: Number of results to return
            method: 'vector', 'bm25', or 'hybrid'
            filter_dict: Optional metadata filter
            
        Returns:
            List of retrieved documents
        """
        if method == "vector":
            return self.vector_search(query, top_k, filter_dict)
        elif method == "bm25":
            return self.bm25_search(query, top_k)
        else:  # hybrid
            return self.hybrid_search(query, top_k, filter_dict)

    def retrieve_for_context(
        self,
        query: str,
        top_k: int = 5,
        max_context_length: int = 4000
    ) -> str:
        """
        Retrieve documents and format as context string for LLM
        
        Args:
            query: Search query
            top_k: Number of results to return
            max_context_length: Maximum context length in characters
            
        Returns:
            Formatted context string
        """
        documents = self.hybrid_search(query, top_k)
        
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(documents):
            doc_text = f"[Source: {doc.source} | Category: {doc.category} | Score: {doc.score:.2f}]\n{doc.content}\n"
            
            if current_length + len(doc_text) > max_context_length:
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        return "\n---\n".join(context_parts)

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the retriever's collection"""
        if not self.collection:
            return {"error": "No collection loaded"}
        
        return {
            "collection_name": self.collection_name,
            "total_documents": self.collection.count(),
            "bm25_indexed": self.bm25_index is not None,
            "bm25_documents": len(self.document_corpus) if self.document_corpus else 0,
            "vector_weight": self.vector_weight,
            "bm25_weight": self.bm25_weight
        }


# Singleton instance
_retriever_instance: Optional[HybridRetriever] = None


def get_retriever() -> HybridRetriever:
    """Get or create singleton retriever instance"""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever()
    return _retriever_instance
