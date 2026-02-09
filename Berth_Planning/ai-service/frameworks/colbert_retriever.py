"""
Ragatouille ColBERT Retriever - Late Interaction Dense Retrieval
================================================================

Implements ColBERT-style retrieval for SmartBerth:
- Late Interaction: Token-level similarity for precise matching
- Efficient Reranking: MaxSim computation for top-k refinement
- Index Management: Build, update, and query vector indices
- Hybrid Search: Combine with lexical retrieval

ColBERT provides superior retrieval for domain-specific terminology.
"""

import logging
import json
import os
import hashlib
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class ColBERTDocument:
    """Document stored in ColBERT index"""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    tokens: List[str] = field(default_factory=list)
    embeddings: Optional[np.ndarray] = None  # Shape: (num_tokens, embedding_dim)


@dataclass
class ColBERTQuery:
    """Processed query for ColBERT search"""
    text: str
    tokens: List[str] = field(default_factory=list)
    embeddings: Optional[np.ndarray] = None  # Shape: (num_tokens, embedding_dim)


@dataclass
class ColBERTSearchResult:
    """Search result with ColBERT scoring"""
    document: ColBERTDocument
    score: float
    maxsim_scores: List[float] = field(default_factory=list)
    matched_tokens: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class ColBERTIndex:
    """ColBERT index for a collection"""
    name: str
    documents: Dict[str, ColBERTDocument]
    embedding_dim: int = 128
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    doc_embeddings_matrix: Optional[np.ndarray] = None
    doc_token_offsets: Dict[str, Tuple[int, int]] = field(default_factory=dict)


# ============================================================================
# TOKENIZER
# ============================================================================

class SimpleTokenizer:
    """
    Simple tokenizer for ColBERT.
    In production, would use BERT WordPiece tokenizer.
    """
    
    def __init__(self, max_length: int = 512):
        self.max_length = max_length
        
        # Maritime domain special tokens
        self.special_tokens = {
            "VESSEL", "BERTH", "PORT", "TERMINAL", "DRAFT",
            "LOA", "BEAM", "DWT", "TEU", "ETA", "ETD",
            "IMO", "MMSI", "UKC", "HAT", "LAT"
        }
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into tokens
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Simple whitespace + punctuation tokenization
        import re
        
        # Lowercase and split
        text = text.lower()
        tokens = re.findall(r'\b\w+\b|[^\w\s]', text)
        
        # Handle special domain tokens (keep uppercase)
        result = []
        for token in tokens:
            upper = token.upper()
            if upper in self.special_tokens:
                result.append(upper)
            else:
                result.append(token)
        
        return result[:self.max_length]
    
    def tokenize_query(self, query: str) -> List[str]:
        """Tokenize query with special handling"""
        tokens = ["[Q]"] + self.tokenize(query)  # Query marker
        return tokens
    
    def tokenize_document(self, document: str) -> List[str]:
        """Tokenize document with special handling"""
        tokens = ["[D]"] + self.tokenize(document)  # Document marker
        return tokens


# ============================================================================
# EMBEDDING MODEL (SIMULATED)
# ============================================================================

class ColBERTEmbedder:
    """
    ColBERT embedding model.
    In production, would use actual ColBERTv2 model.
    Simulated with random embeddings for demonstration.
    """
    
    def __init__(
        self,
        embedding_dim: int = 128,
        model_name: str = "colbert-simulated"
    ):
        self.embedding_dim = embedding_dim
        self.model_name = model_name
        self.token_cache: Dict[str, np.ndarray] = {}
        
        # Initialize with deterministic "embeddings" based on token hash
        self.initialized = True
        logger.info(f"ColBERT embedder initialized (dim={embedding_dim})")
    
    def _get_token_embedding(self, token: str) -> np.ndarray:
        """Get embedding for single token"""
        if token not in self.token_cache:
            # Deterministic embedding based on token
            seed = int(hashlib.md5(token.encode()).hexdigest()[:8], 16)
            rng = np.random.default_rng(seed)
            embedding = rng.standard_normal(self.embedding_dim).astype(np.float32)
            # Normalize
            embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
            self.token_cache[token] = embedding
        
        return self.token_cache[token]
    
    def embed_tokens(self, tokens: List[str]) -> np.ndarray:
        """
        Embed list of tokens
        
        Args:
            tokens: List of tokens
            
        Returns:
            Embeddings array of shape (num_tokens, embedding_dim)
        """
        embeddings = np.array([self._get_token_embedding(t) for t in tokens])
        return embeddings.astype(np.float32)
    
    def embed_query(self, query: str, tokenizer: SimpleTokenizer) -> ColBERTQuery:
        """Embed query into ColBERT format"""
        tokens = tokenizer.tokenize_query(query)
        embeddings = self.embed_tokens(tokens)
        return ColBERTQuery(text=query, tokens=tokens, embeddings=embeddings)
    
    def embed_document(self, doc_id: str, content: str, tokenizer: SimpleTokenizer) -> ColBERTDocument:
        """Embed document into ColBERT format"""
        tokens = tokenizer.tokenize_document(content)
        embeddings = self.embed_tokens(tokens)
        return ColBERTDocument(
            id=doc_id,
            content=content,
            tokens=tokens,
            embeddings=embeddings
        )


# ============================================================================
# MAXSIM SCORING
# ============================================================================

def maxsim_score(
    query_embeddings: np.ndarray,
    doc_embeddings: np.ndarray
) -> float:
    """
    Compute ColBERT MaxSim score between query and document.
    
    For each query token, find max similarity to any document token.
    Sum these maximum similarities.
    
    Args:
        query_embeddings: Shape (num_query_tokens, dim)
        doc_embeddings: Shape (num_doc_tokens, dim)
        
    Returns:
        MaxSim score
    """
    # Compute similarity matrix: (num_query_tokens, num_doc_tokens)
    similarity_matrix = np.dot(query_embeddings, doc_embeddings.T)
    
    # For each query token, take max similarity across document tokens
    max_similarities = np.max(similarity_matrix, axis=1)
    
    # Sum of max similarities
    return float(np.sum(max_similarities))


def batch_maxsim_scores(
    query_embeddings: np.ndarray,
    doc_embeddings_list: List[np.ndarray]
) -> List[float]:
    """Compute MaxSim scores for multiple documents"""
    scores = []
    for doc_emb in doc_embeddings_list:
        score = maxsim_score(query_embeddings, doc_emb)
        scores.append(score)
    return scores


# ============================================================================
# COLBERT RETRIEVER
# ============================================================================

class ColBERTRetriever:
    """
    ColBERT-style retriever with late interaction.
    
    Features:
    - Token-level similarity for precise matching
    - MaxSim scoring for ranking
    - Efficient index management
    """
    
    def __init__(
        self,
        embedding_dim: int = 128,
        index_path: Optional[str] = None
    ):
        """
        Initialize ColBERT retriever
        
        Args:
            embedding_dim: Embedding dimension
            index_path: Path to save/load index
        """
        self.embedding_dim = embedding_dim
        self.index_path = index_path
        
        self.tokenizer = SimpleTokenizer()
        self.embedder = ColBERTEmbedder(embedding_dim=embedding_dim)
        
        self.index: Optional[ColBERTIndex] = None
        
        logger.info(f"ColBERT retriever initialized (dim={embedding_dim})")
    
    def create_index(self, name: str = "default") -> ColBERTIndex:
        """Create a new index"""
        self.index = ColBERTIndex(
            name=name,
            documents={},
            embedding_dim=self.embedding_dim
        )
        logger.info(f"Created new ColBERT index: {name}")
        return self.index
    
    def add_documents(
        self,
        documents: List[Dict[str, Any]],
        show_progress: bool = True
    ) -> int:
        """
        Add documents to index
        
        Args:
            documents: List of dicts with 'id', 'content', optional 'metadata'
            show_progress: Show progress logging
            
        Returns:
            Number of documents added
        """
        if not self.index:
            self.create_index()
        
        added = 0
        for i, doc in enumerate(documents):
            doc_id = doc.get("id", f"doc_{i}")
            content = doc.get("content", "")
            metadata = doc.get("metadata", {})
            
            if not content:
                continue
            
            # Embed document
            col_doc = self.embedder.embed_document(doc_id, content, self.tokenizer)
            col_doc.metadata = metadata
            
            self.index.documents[doc_id] = col_doc
            added += 1
            
            if show_progress and (i + 1) % 50 == 0:
                logger.info(f"  Added {i+1}/{len(documents)} documents")
        
        logger.info(f"Added {added} documents to index")
        return added
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        min_score: float = 0.0
    ) -> List[ColBERTSearchResult]:
        """
        Search index with ColBERT
        
        Args:
            query: Search query
            top_k: Number of results to return
            min_score: Minimum score threshold
            
        Returns:
            List of search results
        """
        if not self.index or not self.index.documents:
            logger.warning("Index is empty")
            return []
        
        # Embed query
        col_query = self.embedder.embed_query(query, self.tokenizer)
        
        # Score all documents
        results = []
        for doc_id, doc in self.index.documents.items():
            if doc.embeddings is None:
                continue
            
            score = maxsim_score(col_query.embeddings, doc.embeddings)
            
            if score >= min_score:
                result = ColBERTSearchResult(
                    document=doc,
                    score=score
                )
                results.append(result)
        
        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results[:top_k]
    
    def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents using ColBERT scoring.
        
        Use this to rerank results from another retriever.
        
        Args:
            query: Search query
            documents: Documents to rerank (with 'content' key)
            top_k: Number of results to return
            
        Returns:
            Reranked documents with scores
        """
        # Embed query
        col_query = self.embedder.embed_query(query, self.tokenizer)
        
        # Score each document
        scored = []
        for doc in documents:
            content = doc.get("content", "")
            if not content:
                continue
            
            # Embed document (without caching)
            doc_tokens = self.tokenizer.tokenize_document(content)
            doc_embeddings = self.embedder.embed_tokens(doc_tokens)
            
            score = maxsim_score(col_query.embeddings, doc_embeddings)
            
            scored.append({
                **doc,
                "colbert_score": score
            })
        
        # Sort by ColBERT score
        scored.sort(key=lambda d: d["colbert_score"], reverse=True)
        
        return scored[:top_k]
    
    def hybrid_search(
        self,
        query: str,
        lexical_results: List[Dict[str, Any]],
        alpha: float = 0.5,
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining ColBERT with lexical results.
        
        Args:
            query: Search query
            lexical_results: Results from lexical search (BM25, etc.)
            alpha: Weight for ColBERT scores (1-alpha for lexical)
            top_k: Number of results
            
        Returns:
            Hybrid ranked results
        """
        # Get ColBERT scores for lexical results
        reranked = self.rerank(query, lexical_results, top_k=len(lexical_results))
        
        # Normalize scores
        if reranked:
            max_colbert = max(r["colbert_score"] for r in reranked)
            max_lexical = max(r.get("lexical_score", 1.0) for r in reranked)
            
            for r in reranked:
                norm_colbert = r["colbert_score"] / (max_colbert + 1e-8)
                norm_lexical = r.get("lexical_score", 1.0) / (max_lexical + 1e-8)
                r["hybrid_score"] = alpha * norm_colbert + (1 - alpha) * norm_lexical
            
            reranked.sort(key=lambda r: r["hybrid_score"], reverse=True)
        
        return reranked[:top_k]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.index:
            return {"status": "not_created"}
        
        return {
            "status": "ready",
            "name": self.index.name,
            "num_documents": len(self.index.documents),
            "embedding_dim": self.embedding_dim,
            "created_at": self.index.created_at
        }


# ============================================================================
# RAGATOUILLE INTEGRATION
# ============================================================================

class RagatouilleRetriever:
    """
    Ragatouille-style retriever interface.
    
    Wraps ColBERT retriever with additional features:
    - Easy index management
    - Automatic document chunking
    - Query expansion
    - Result caching
    """
    
    def __init__(
        self,
        model_name: str = "colbert-smartberth",
        embedding_dim: int = 128,
        index_path: Optional[str] = None
    ):
        """
        Initialize Ragatouille retriever
        
        Args:
            model_name: Name of the model/index
            embedding_dim: Embedding dimension
            index_path: Path for index persistence
        """
        self.model_name = model_name
        self.colbert = ColBERTRetriever(
            embedding_dim=embedding_dim,
            index_path=index_path
        )
        
        self.query_cache: Dict[str, List[Dict]] = {}
        
        logger.info(f"Ragatouille retriever initialized: {model_name}")
    
    def index(
        self,
        collection: List[str],
        document_ids: Optional[List[str]] = None,
        document_metadatas: Optional[List[Dict]] = None,
        index_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Index a collection of documents
        
        Args:
            collection: List of document texts
            document_ids: Optional document IDs
            document_metadatas: Optional metadata for each document
            index_name: Name for the index
            
        Returns:
            Indexing statistics
        """
        self.colbert.create_index(index_name)
        
        documents = []
        for i, text in enumerate(collection):
            doc_id = document_ids[i] if document_ids else f"doc_{i}"
            metadata = document_metadatas[i] if document_metadatas else {}
            
            documents.append({
                "id": doc_id,
                "content": text,
                "metadata": metadata
            })
        
        added = self.colbert.add_documents(documents)
        
        return {
            "indexed": added,
            "index_name": index_name,
            "model": self.model_name
        }
    
    def search(
        self,
        query: str,
        k: int = 10,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Search the index
        
        Args:
            query: Search query
            k: Number of results
            use_cache: Use query cache
            
        Returns:
            Search results
        """
        cache_key = f"{query}:{k}"
        
        if use_cache and cache_key in self.query_cache:
            return self.query_cache[cache_key]
        
        results = self.colbert.search(query, top_k=k)
        
        formatted = []
        for result in results:
            formatted.append({
                "id": result.document.id,
                "content": result.document.content,
                "score": result.score,
                "metadata": result.document.metadata
            })
        
        if use_cache:
            self.query_cache[cache_key] = formatted
        
        return formatted
    
    def rerank(
        self,
        query: str,
        documents: List[str],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents
        
        Args:
            query: Query for reranking
            documents: Documents to rerank
            k: Number of results
            
        Returns:
            Reranked results
        """
        docs = [{"content": doc} for doc in documents]
        return self.colbert.rerank(query, docs, top_k=k)
    
    def clear_cache(self):
        """Clear query cache"""
        self.query_cache.clear()


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def get_colbert_retriever(
    embedding_dim: int = 128,
    index_path: Optional[str] = None
) -> ColBERTRetriever:
    """Create ColBERT retriever instance"""
    return ColBERTRetriever(
        embedding_dim=embedding_dim,
        index_path=index_path
    )


def get_ragatouille_retriever(
    model_name: str = "colbert-smartberth",
    **kwargs
) -> RagatouilleRetriever:
    """Create Ragatouille retriever instance"""
    return RagatouilleRetriever(model_name=model_name, **kwargs)
