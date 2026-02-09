"""
FINAL BENCHMARK TEST
====================
Comprehensive evaluation of the optimized retrieval system
Tests all categories with multiple queries and calculates final metrics
"""

import os
os.environ['CUDA_VISIBLE_DEVICES'] = '0'

import torch
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from pathlib import Path
import json
import time

print("="*70)
print("BERTH PLANNING AI - FINAL BENCHMARK")
print("="*70)
print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

class GPUEmbeddingFunction:
    def __init__(self, model_name: str):
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"Loading model on {self.device.upper()}...")
        self.model = SentenceTransformer(model_name, device=self.device)
        self.model.max_seq_length = 512
        self._model_name = model_name
        print("✓ Model loaded")
        
    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(input, batch_size=64, show_progress_bar=False, 
                                       convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()
    
    def embed_documents(self, input: List[str]) -> List[List[float]]:
        return self.__call__(input)
    
    def embed_query(self, input) -> List[List[float]]:
        if isinstance(input, list):
            texts = input
        else:
            texts = [input]
        embeddings = self.model.encode(texts, show_progress_bar=False, 
                                      convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()
    
    def name(self) -> str:
        return self._model_name


# Extended test suite - 5 queries per category
BENCHMARK_QUERIES = {
    "tidal": [
        "What is the tidal pattern at Mundra Port?",
        "High tide and low tide times at Mundra",
        "Tidal range at Mundra port",
        "Show me tide levels for Mundra",
        "Tidal data for berth planning at Mundra",
    ],
    "vessel": [
        "What vessels are scheduled at Mundra?",
        "Container vessel arrivals at Mundra Port",
        "Vessel schedule for next week",
        "Ships calling at Mundra terminals",
        "List of vessels at anchorage",
    ],
    "berth": [
        "List all berths at Mundra Container Terminal",
        "Berth availability at Mundra Port",
        "Which berths can handle VLCC vessels?",
        "Berth dimensions at Mundra",
        "Available berths for container ships",
    ],
    "weather": [
        "Weather conditions at Mundra Port",
        "Wind speed and wave height at Mundra",
        "Weather forecast for port operations",
        "Visibility conditions at Mundra",
        "Current weather at Mundra",
    ],
    "ukc": [
        "Under keel clearance requirements at Mundra",
        "UKC calculations for deep draft vessels",
        "Minimum UKC for container terminals",
        "Draft restrictions at Mundra channel",
        "Squat calculation for vessels",
    ],
    "pilot": [
        "Pilotage requirements at Mundra",
        "Pilot boarding procedures",
        "Licensed pilots at Mundra Port",
        "Pilot availability for vessel arrival",
        "Pilotage services at Mundra",
    ],
    "ais": [
        "AIS data for vessels near Mundra",
        "Real-time vessel positions at Mundra",
        "AIS tracking for port approach",
        "Vessel movement patterns from AIS",
        "Ship tracking data",
    ],
    "anchorage": [
        "Anchorage areas at Mundra Port",
        "Anchorage waiting times",
        "Vessel anchorage assignments",
        "Anchorage capacity at Mundra",
        "Anchor positions for waiting vessels",
    ],
    "schedule": [
        "Vessel arrival schedule at Mundra",
        "ETA and ETD for ships",
        "Scheduled vessel movements",
        "Port call schedule",
        "Departure schedule for vessels",
    ],
    "terminal": [
        "Container terminal at Mundra",
        "Terminal facilities at Mundra Port",
        "Cargo handling terminals",
        "Terminal equipment and cranes",
        "Terminal capacity",
    ],
}


def run_benchmark(collection, queries: Dict[str, List[str]]) -> Dict[str, Any]:
    """Run comprehensive benchmark"""
    results = {
        "categories": {},
        "query_details": [],
        "timing": [],
    }
    
    total_correct = 0
    total_queries = 0
    total_mrr = 0.0
    
    for category, query_list in queries.items():
        cat_correct = 0
        cat_mrr = 0.0
        
        for query in query_list:
            start = time.time()
            result = collection.query(
                query_texts=[query], 
                n_results=5, 
                include=["metadatas", "documents", "distances"]
            )
            elapsed = (time.time() - start) * 1000
            results["timing"].append(elapsed)
            
            # Check relevance
            found_rank = None
            for rank, meta in enumerate(result["metadatas"][0]):
                domains = meta.get("domains", "").split(",")
                source = meta.get("source", "").lower()
                
                if category in domains or category in source:
                    found_rank = rank + 1
                    break
            
            is_correct = found_rank is not None and found_rank <= 3
            mrr = 1.0 / found_rank if found_rank else 0.0
            
            if is_correct:
                cat_correct += 1
                total_correct += 1
            
            cat_mrr += mrr
            total_mrr += mrr
            total_queries += 1
            
            top_source = result["metadatas"][0][0].get("source", "unknown") if result["metadatas"][0] else "none"
            top_domains = result["metadatas"][0][0].get("domains", "") if result["metadatas"][0] else ""
            
            results["query_details"].append({
                "category": category,
                "query": query,
                "correct": is_correct,
                "rank": found_rank,
                "top_source": top_source,
                "top_domains": top_domains,
                "time_ms": round(elapsed, 1),
            })
        
        cat_accuracy = cat_correct / len(query_list) if query_list else 0
        cat_avg_mrr = cat_mrr / len(query_list) if query_list else 0
        
        results["categories"][category] = {
            "accuracy": cat_accuracy,
            "mrr": cat_avg_mrr,
            "correct": cat_correct,
            "total": len(query_list),
        }
    
    results["overall_accuracy"] = total_correct / total_queries
    results["overall_mrr"] = total_mrr / total_queries
    results["total_queries"] = total_queries
    results["total_correct"] = total_correct
    results["avg_latency_ms"] = sum(results["timing"]) / len(results["timing"])
    results["p95_latency_ms"] = sorted(results["timing"])[int(len(results["timing"]) * 0.95)]
    
    return results


def print_results(results: Dict[str, Any], chunk_count: int):
    """Print formatted results"""
    print("\n" + "="*70)
    print("BENCHMARK RESULTS")
    print("="*70)
    
    print("\n┌─────────────┬──────────┬──────────┬───────────┐")
    print("│ Category    │ Accuracy │   MRR    │ Correct   │")
    print("├─────────────┼──────────┼──────────┼───────────┤")
    
    for cat, data in results["categories"].items():
        acc_str = f"{data['accuracy']*100:5.1f}%"
        mrr_str = f"{data['mrr']:6.3f}"
        correct_str = f"{data['correct']}/{data['total']}"
        
        status = "✓" if data["accuracy"] >= 0.8 else "⚠" if data["accuracy"] >= 0.6 else "✗"
        print(f"│ {status} {cat:9s} │ {acc_str:8s} │ {mrr_str:8s} │ {correct_str:9s} │")
    
    print("├─────────────┼──────────┼──────────┼───────────┤")
    overall_acc = f"{results['overall_accuracy']*100:5.1f}%"
    overall_mrr = f"{results['overall_mrr']:6.3f}"
    overall_correct = f"{results['total_correct']}/{results['total_queries']}"
    print(f"│ {'OVERALL':11s} │ {overall_acc:8s} │ {overall_mrr:8s} │ {overall_correct:9s} │")
    print("└─────────────┴──────────┴──────────┴───────────┘")
    
    print(f"\n Performance Metrics:")
    print(f"  Average Latency: {results['avg_latency_ms']:.1f}ms")
    print(f"  P95 Latency: {results['p95_latency_ms']:.1f}ms")
    print(f"  Total Chunks: {chunk_count}")
    
    # Show failed queries
    failed = [d for d in results["query_details"] if not d["correct"]]
    if failed:
        print(f"\n⚠ Failed Queries ({len(failed)}):")
        for f in failed[:10]:  # Show first 10
            print(f"  ✗ [{f['category']}] {f['query'][:40]}... → {f['top_source']}")


def main():
    # Connect to ChromaDB
    chroma_path = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\chroma_db_optimized"
    embedding_fn = GPUEmbeddingFunction("sentence-transformers/all-mpnet-base-v2")
    
    client = chromadb.PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False))
    collection = client.get_collection(name="berth_planning_optimized", embedding_function=embedding_fn)
    
    print(f"\nCollection: {collection.count()} chunks")
    
    # Run benchmark
    print("\nRunning benchmark...")
    results = run_benchmark(collection, BENCHMARK_QUERIES)
    
    # Print results
    chunk_count = collection.count()
    print_results(results, chunk_count)
    
    # Grade
    print("\n" + "="*70)
    acc = results["overall_accuracy"]
    if acc >= 0.90:
        grade = "A - EXCELLENT"
    elif acc >= 0.85:
        grade = "A- - VERY GOOD"
    elif acc >= 0.80:
        grade = "B+ - GOOD"
    elif acc >= 0.75:
        grade = "B - SATISFACTORY"
    elif acc >= 0.70:
        grade = "B- - ACCEPTABLE"
    else:
        grade = "C - NEEDS IMPROVEMENT"
    
    print(f"FINAL GRADE: {grade}")
    print(f"Accuracy: {acc*100:.1f}%")
    print("="*70)
    
    # Save results
    output_file = Path(chroma_path).parent / "benchmark_results.json"
    with open(output_file, 'w') as f:
        # Convert for JSON serialization
        json_results = {
            "overall_accuracy": results["overall_accuracy"],
            "overall_mrr": results["overall_mrr"],
            "total_queries": results["total_queries"],
            "total_correct": results["total_correct"],
            "avg_latency_ms": results["avg_latency_ms"],
            "p95_latency_ms": results["p95_latency_ms"],
            "categories": results["categories"],
            "failed_queries": [d for d in results["query_details"] if not d["correct"]],
        }
        json.dump(json_results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())
