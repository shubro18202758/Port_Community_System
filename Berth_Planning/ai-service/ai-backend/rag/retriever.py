"""
Hybrid Retriever for Berth Planning Knowledge Base
Combines vector similarity search (ChromaDB) with keyword search (BM25)
"""

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import numpy as np
from rank_bm25 import BM25Okapi
import re


class HybridRetriever:
    """
    Hybrid retrieval combining:
    - Vector similarity search (70% weight) via ChromaDB
    - Keyword BM25 search (30% weight) for exact term matching
    """

    def __init__(
        self,
        chroma_persist_dir: str = "./chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2",
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3
    ):
        self.chroma_persist_dir = chroma_persist_dir
        self.embedding_model_name = embedding_model
        self.vector_weight = vector_weight
        self.keyword_weight = keyword_weight

        # Initialize sentence transformer
        print(f"Loading embedding model: {embedding_model}...")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Initialize ChromaDB client
        print(f"Connecting to ChromaDB at {chroma_persist_dir}...")
        self.chroma_client = chromadb.PersistentClient(path=chroma_persist_dir)

        # Get collection
        try:
            self.collection = self.chroma_client.get_collection(name="berth_knowledge")
            print(f"Connected to collection 'berth_knowledge' ({self.collection.count()} chunks)")
        except:
            raise ValueError(
                "Collection 'berth_knowledge' not found. "
                "Run document_loader.py first to populate the knowledge base."
            )

        # Cache for BM25 (will be built on first retrieval)
        self.bm25_index = None
        self.bm25_documents = None
        self.bm25_metadatas = None
        self.bm25_ids = None

    def _build_bm25_index(self):
        """
        Build BM25 index from all documents in collection
        """
        if self.bm25_index is not None:
            return  # Already built

        print("Building BM25 index...")
        # Fetch all documents from ChromaDB
        all_data = self.collection.get()

        self.bm25_documents = all_data['documents']
        self.bm25_metadatas = all_data['metadatas']
        self.bm25_ids = all_data['ids']

        # Tokenize documents for BM25
        tokenized_corpus = [self._tokenize(doc) for doc in self.bm25_documents]

        # Build BM25 index
        self.bm25_index = BM25Okapi(tokenized_corpus)
        print(f"BM25 index built with {len(self.bm25_documents)} documents")

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for BM25
        """
        # Lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens

    def retrieve_vector(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Vector similarity search using ChromaDB
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])[0].tolist()

        # Search in ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        # Format results
        retrieved = []
        for i in range(len(results['ids'][0])):
            retrieved.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "distance": results['distances'][0][i] if 'distances' in results else None,
                "vector_score": 1.0 / (1.0 + results['distances'][0][i]) if 'distances' in results else 1.0
            })

        return retrieved

    def retrieve_keyword(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Keyword BM25 search
        """
        # Build index if not already built
        if self.bm25_index is None:
            self._build_bm25_index()

        # Tokenize query
        query_tokens = self._tokenize(query)

        # Get BM25 scores
        bm25_scores = self.bm25_index.get_scores(query_tokens)

        # Get top-k indices
        top_indices = np.argsort(bm25_scores)[::-1][:top_k]

        # Format results
        retrieved = []
        for idx in top_indices:
            if bm25_scores[idx] > 0:  # Only include docs with positive scores
                retrieved.append({
                    "id": self.bm25_ids[idx],
                    "content": self.bm25_documents[idx],
                    "metadata": self.bm25_metadatas[idx],
                    "bm25_score": float(bm25_scores[idx]),
                    "keyword_score": float(bm25_scores[idx])
                })

        return retrieved

    def retrieve_hybrid(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining vector and keyword search

        Args:
            query: Search query
            top_k: Number of results to return
            filters: Optional metadata filters (e.g., {"document_type": "Port Manual"})

        Returns:
            List of top_k results with combined scores
        """
        # Retrieve from both methods (get 2x top_k to ensure enough after merging)
        vector_results = self.retrieve_vector(query, top_k * 2)
        keyword_results = self.retrieve_keyword(query, top_k * 2)

        # Normalize scores to 0-1 range
        if vector_results:
            max_vector_score = max(r['vector_score'] for r in vector_results)
            for r in vector_results:
                r['vector_score_norm'] = r['vector_score'] / max_vector_score if max_vector_score > 0 else 0

        if keyword_results:
            max_keyword_score = max(r['keyword_score'] for r in keyword_results)
            for r in keyword_results:
                r['keyword_score_norm'] = r['keyword_score'] / max_keyword_score if max_keyword_score > 0 else 0

        # Merge results by ID
        merged = {}
        for result in vector_results:
            chunk_id = result['id']
            merged[chunk_id] = result
            merged[chunk_id]['keyword_score_norm'] = 0  # Default if not in keyword results

        for result in keyword_results:
            chunk_id = result['id']
            if chunk_id in merged:
                merged[chunk_id]['keyword_score_norm'] = result['keyword_score_norm']
            else:
                merged[chunk_id] = result
                merged[chunk_id]['vector_score_norm'] = 0  # Default if not in vector results

        # Calculate hybrid scores
        for chunk_id, result in merged.items():
            vector_score = result.get('vector_score_norm', 0)
            keyword_score = result.get('keyword_score_norm', 0)

            # Weighted combination
            result['hybrid_score'] = (
                self.vector_weight * vector_score +
                self.keyword_weight * keyword_score
            )

        # Apply filters if provided
        if filters:
            filtered = {}
            for chunk_id, result in merged.items():
                metadata = result['metadata']
                match = all(
                    metadata.get(key) == value
                    for key, value in filters.items()
                )
                if match:
                    filtered[chunk_id] = result
            merged = filtered

        # Sort by hybrid score and return top_k
        sorted_results = sorted(
            merged.values(),
            key=lambda x: x['hybrid_score'],
            reverse=True
        )[:top_k]

        return sorted_results

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        method: str = "hybrid",
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Main retrieval method with multiple strategies

        Args:
            query: Search query
            top_k: Number of results to return
            method: "hybrid", "vector", or "keyword"
            filters: Optional metadata filters

        Returns:
            List of top_k results
        """
        if method == "vector":
            return self.retrieve_vector(query, top_k)
        elif method == "keyword":
            return self.retrieve_keyword(query, top_k)
        else:  # hybrid
            return self.retrieve_hybrid(query, top_k, filters)

    def format_context(self, results: List[Dict[str, Any]], max_length: int = 4000) -> str:
        """
        Format retrieved results as context for LLM

        Args:
            results: Retrieved chunks
            max_length: Maximum character length

        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0

        for i, result in enumerate(results):
            # Format source citation
            doc_name = result['metadata'].get('document_name', 'Unknown')
            doc_type = result['metadata'].get('document_type', 'Unknown')
            chunk_idx = result['metadata'].get('chunk_index', 0)

            header = f"\n[Source {i+1}: {doc_name} ({doc_type}), Chunk {chunk_idx}]\n"
            content = result['content']

            part = header + content + "\n"

            # Check length
            if current_length + len(part) > max_length:
                context_parts.append("\n[Additional context truncated due to length...]")
                break

            context_parts.append(part)
            current_length += len(part)

        return "".join(context_parts)


def main():
    """
    Test the retriever with sample queries
    """
    print("=" * 70)
    print("HYBRID RETRIEVER TEST")
    print("=" * 70)

    # Initialize retriever
    retriever = HybridRetriever(
        chroma_persist_dir="./chroma_db",
        vector_weight=0.7,
        keyword_weight=0.3
    )

    # Sample queries
    test_queries = [
        "What is the minimum UKC for deep draft vessels?",
        "Window vessel SLA penalty structure",
        "Crane capacity requirements for container vessels",
        "Storm impact on vessel delays",
        "Berth allocation optimization techniques"
    ]

    print("\nRunning test queries...\n")

    for query in test_queries:
        print(f"Query: \"{query}\"")
        print("-" * 70)

        # Retrieve
        results = retriever.retrieve(query, top_k=3, method="hybrid")

        # Display results
        for i, result in enumerate(results):
            print(f"\n[Result {i+1}] Score: {result['hybrid_score']:.3f}")
            print(f"Document: {result['metadata'].get('document_name', 'Unknown')}")
            print(f"Type: {result['metadata'].get('document_type', 'Unknown')}")
            print(f"Preview: {result['content'][:200]}...")

        print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
