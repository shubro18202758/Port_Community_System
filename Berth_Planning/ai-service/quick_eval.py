"""
Quick Evaluation Test for Optimized ChromaDB
Tests retrieval accuracy without re-indexing
"""

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List
from pathlib import Path
import json

print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

# Custom embedding function matching what was used
class GPUEmbeddingFunction:
    def __init__(self, model_name: str):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = SentenceTransformer(model_name, device=self.device)
        self.model.max_seq_length = 512
        self._model_name = model_name
        
    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(input, batch_size=64, show_progress_bar=False, 
                                       convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()
    
    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return self.__call__(input)
    
    def embed_query(self, input) -> List[List[float]]:
        # Handle both string and list inputs
        if isinstance(input, list):
            texts = input
        else:
            texts = [input]
        embeddings = self.model.encode(texts, show_progress_bar=False, 
                                      convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()
    
    def name(self) -> str:
        return self._model_name

# Connect to existing ChromaDB
chroma_path = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\chroma_db_optimized"

print(f"\nLoading ChromaDB from {chroma_path}")
embedding_fn = GPUEmbeddingFunction("sentence-transformers/all-mpnet-base-v2")

client = chromadb.PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False))
collection = client.get_collection(name="berth_planning_optimized", embedding_function=embedding_fn)

print(f"Collection has {collection.count()} chunks")

# Test queries
test_queries = {
    "tidal": [
        "What is the tidal pattern at Mundra Port?",
        "Show me tide levels for Mundra",
        "High tide and low tide times at Mundra",
    ],
    "vessel": [
        "What vessels are scheduled at Mundra?",
        "Container vessel arrivals at Mundra Port",
    ],
    "berth": [
        "List all berths at Mundra Container Terminal",
        "Berth availability at Mundra Port",
    ],
    "weather": [
        "Weather conditions at Mundra Port",
        "Wind speed and wave height at Mundra",
    ],
    "ukc": [
        "Under keel clearance requirements at Mundra",
        "UKC calculations for deep draft vessels",
    ],
    "pilot": [
        "Pilotage requirements at Mundra",
        "Pilot availability for vessel arrival",
    ],
    "ais": [
        "AIS data for vessels near Mundra",
        "Real-time vessel positions at Mundra",
    ],
    "anchorage": [
        "Anchorage areas at Mundra Port",
        "Vessel anchorage assignments",
    ],
}

print("\n" + "="*70)
print("RETRIEVAL ACCURACY TEST")
print("="*70)

total_correct = 0
total_queries = 0
results_detail = []

for category, queries in test_queries.items():
    category_correct = 0
    
    for query in queries:
        result = collection.query(query_texts=[query], n_results=5, include=["metadatas", "distances"])
        
        # Check if correct domain in top 3
        found_rank = None
        for rank, meta in enumerate(result["metadatas"][0]):
            domains = meta.get("domains", "").split(",")
            source = meta.get("source", "").lower()
            
            if category in domains or category in source:
                found_rank = rank + 1
                break
        
        is_correct = found_rank is not None and found_rank <= 3
        top_source = result["metadatas"][0][0].get("source", "?") if result["metadatas"][0] else "none"
        
        if is_correct:
            category_correct += 1
            total_correct += 1
        total_queries += 1
        
        results_detail.append({
            "category": category,
            "query": query[:50],
            "correct": is_correct,
            "rank": found_rank,
            "top_source": top_source,
        })
    
    accuracy = category_correct / len(queries) * 100
    status = "✓" if accuracy >= 75 else "⚠" if accuracy >= 50 else "✗"
    print(f"{status} {category}: {accuracy:.0f}% ({category_correct}/{len(queries)})")

overall = total_correct / total_queries * 100
print(f"\n{'='*70}")
print(f"OVERALL ACCURACY: {overall:.1f}% ({total_correct}/{total_queries})")
print("="*70)

# Show details for failed queries
print("\nQuery Details:")
for r in results_detail:
    status = "✓" if r["correct"] else "✗"
    print(f"  {status} [{r['category']}] {r['query'][:40]}... → {r['top_source']}")

# Save results
results_file = Path(chroma_path).parent / "evaluation_results.json"
with open(results_file, 'w') as f:
    json.dump({"accuracy": overall, "details": results_detail}, f, indent=2)
print(f"\nResults saved to {results_file}")
