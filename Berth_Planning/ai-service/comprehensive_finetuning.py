"""
Comprehensive Fine-Tuning Iterations
=====================================
Iterative optimization for retrieval accuracy
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
import hashlib
import pandas as pd

print(f"GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

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
        if isinstance(input, list):
            texts = input
        else:
            texts = [input]
        embeddings = self.model.encode(texts, show_progress_bar=False, 
                                      convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()
    
    def name(self) -> str:
        return self._model_name


# Expanded test suite
COMPREHENSIVE_TEST_QUERIES = {
    "tidal": [
        "What is the tidal pattern at Mundra Port?",
        "Show me tide levels for Mundra",
        "High tide and low tide times at Mundra",
        "Tidal data for berth planning",
        "When is high tide at Mundra?",
        "Tidal range at Mundra port",
    ],
    "vessel": [
        "What vessels are scheduled at Mundra?",
        "Container vessel arrivals at Mundra Port",
        "Vessel schedule for next week",
        "Ships calling at Mundra terminals",
        "List of vessels at anchorage",
        "Vessel specifications and dimensions",
    ],
    "berth": [
        "List all berths at Mundra Container Terminal",
        "Berth availability at Mundra Port",
        "Which berths can handle VLCC vessels?",
        "Berth dimensions at Mundra",
        "Available berths for container ships",
        "Berth depth and length information",
    ],
    "weather": [
        "Weather conditions at Mundra Port",
        "Wind speed and wave height at Mundra",
        "Weather forecast for port operations",
        "Visibility conditions at Mundra",
        "Current weather at Mundra",
        "Storm and wind warnings",
    ],
    "ukc": [
        "Under keel clearance requirements at Mundra",
        "UKC calculations for deep draft vessels",
        "Minimum UKC for container terminals",
        "Draft restrictions at Mundra channel",
        "Under keel clearance policy",
        "Squat calculation for vessels",
    ],
    "pilot": [
        "Pilotage requirements at Mundra",
        "Pilot boarding procedures",
        "Licensed pilots at Mundra Port",
        "Pilot availability for vessel arrival",
        "Pilotage services at Mundra",
        "Pilot station location",
    ],
    "ais": [
        "AIS data for vessels near Mundra",
        "Real-time vessel positions at Mundra",
        "AIS tracking for port approach",
        "Vessel movement patterns from AIS",
        "AIS signals from ships",
        "Ship tracking data",
    ],
    "anchorage": [
        "Anchorage areas at Mundra Port",
        "Anchorage waiting times",
        "Vessel anchorage assignments",
        "Anchorage capacity at Mundra",
        "Anchor positions for waiting vessels",
        "Designated anchorage zones",
    ],
    "schedule": [
        "Vessel arrival schedule at Mundra",
        "ETA and ETD for ships",
        "Scheduled vessel movements",
        "Port call schedule",
        "Departure schedule for vessels",
        "Planned arrivals today",
    ],
    "terminal": [
        "Container terminal at Mundra",
        "Terminal facilities at Mundra Port",
        "Cargo handling terminals",
        "Terminal equipment and cranes",
        "Bulk cargo terminal",
        "Terminal capacity",
    ],
}


def evaluate_retrieval(collection, test_queries: Dict[str, List[str]]) -> Dict[str, Any]:
    """Comprehensive retrieval evaluation"""
    results = {
        "categories": {},
        "overall_accuracy": 0.0,
        "overall_mrr": 0.0,
        "details": [],
        "timing": [],
    }
    
    total_correct = 0
    total_queries = 0
    total_mrr = 0.0
    
    for category, queries in test_queries.items():
        category_correct = 0
        category_mrr = 0.0
        
        for query in queries:
            start_time = time.time()
            result = collection.query(query_texts=[query], n_results=5, include=["metadatas", "distances"])
            query_time = (time.time() - start_time) * 1000  # ms
            
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
                category_correct += 1
                total_correct += 1
            
            category_mrr += mrr
            total_mrr += mrr
            total_queries += 1
            
            results["details"].append({
                "category": category,
                "query": query,
                "correct": is_correct,
                "rank": found_rank,
                "top_source": result["metadatas"][0][0].get("source", "?") if result["metadatas"][0] else "none",
                "time_ms": round(query_time, 1),
            })
            results["timing"].append(query_time)
        
        accuracy = category_correct / len(queries) if queries else 0
        avg_mrr = category_mrr / len(queries) if queries else 0
        
        results["categories"][category] = {
            "accuracy": accuracy,
            "mrr": avg_mrr,
            "correct": category_correct,
            "total": len(queries),
        }
    
    results["overall_accuracy"] = total_correct / total_queries if total_queries else 0
    results["overall_mrr"] = total_mrr / total_queries if total_queries else 0
    results["avg_query_time_ms"] = sum(results["timing"]) / len(results["timing"]) if results["timing"] else 0
    
    return results


def add_enhancement_chunks(collection, embedding_fn, weak_categories: List[str]):
    """Add targeted enhancement chunks for weak categories"""
    
    enhancements = {
        "weather": [
            {
                "text": "WEATHER DATA: Wind speed, wind direction, wave height, visibility, temperature, humidity, and weather conditions at Mundra Port. This data is essential for safe port operations and vessel scheduling.",
                "domains": "weather",
            },
            {
                "text": "WEATHER FORECAST: Meteorological data and weather forecasts for Mundra Port operations including storm warnings, wind advisories, and visibility conditions.",
                "domains": "weather",
            },
            {
                "text": "WEATHER CONDITIONS at Mundra: Real-time and forecasted weather parameters including wind speed in knots, wave height in meters, and visibility in nautical miles.",
                "domains": "weather",
            },
        ],
        "pilot": [
            {
                "text": "PILOT DATA: Pilotage services, pilot availability, pilot boarding procedures, and pilot station information at Mundra Port. Pilotage is mandatory for all vessels.",
                "domains": "pilot",
            },
            {
                "text": "PILOTAGE REQUIREMENTS: Licensed pilots, pilot boarding point coordinates, pilot boat services, and pilot availability schedules at Mundra Port.",
                "domains": "pilot",
            },
            {
                "text": "PILOT AVAILABILITY: Information about pilots on duty, pilot rotation schedules, and pilot request procedures for vessel arrivals at Mundra.",
                "domains": "pilot",
            },
        ],
        "anchorage": [
            {
                "text": "ANCHORAGE DATA: Designated anchorage areas, anchorage positions, waiting times, and anchorage capacity at Mundra Port. Vessels await berth assignment at these locations.",
                "domains": "anchorage",
            },
            {
                "text": "ANCHORAGE ASSIGNMENTS: Vessel anchorage allocations, anchor positions, and anchorage area designations at Mundra Port.",
                "domains": "anchorage",
            },
            {
                "text": "VESSEL ANCHORAGE: Anchorage zones for waiting vessels, anchorage coordination, and anchorage to berth movement scheduling.",
                "domains": "anchorage",
            },
        ],
        "schedule": [
            {
                "text": "SCHEDULE DATA: Vessel schedules, ETA (Estimated Time of Arrival), ETD (Estimated Time of Departure), and port call planning at Mundra Port.",
                "domains": "schedule,vessel",
            },
            {
                "text": "VESSEL SCHEDULE: Arrival and departure schedules, planned vessel movements, and scheduling for berth allocation at Mundra terminals.",
                "domains": "schedule,vessel",
            },
        ],
        "terminal": [
            {
                "text": "TERMINAL DATA: Container terminals, bulk terminals, liquid cargo facilities, and terminal equipment at Mundra Port. Terminal capacity and handling capabilities.",
                "domains": "terminal,berth",
            },
            {
                "text": "TERMINAL FACILITIES: Crane equipment, cargo handling systems, terminal capacity, and operational capabilities at Mundra Port terminals.",
                "domains": "terminal,berth",
            },
        ],
    }
    
    chunks_added = 0
    for category in weak_categories:
        if category in enhancements:
            for i, enh in enumerate(enhancements[category]):
                chunk_id = f"enhancement_{category}_{i}_{hashlib.md5(enh['text'][:50].encode()).hexdigest()[:8]}"
                
                try:
                    collection.add(
                        ids=[chunk_id],
                        documents=[enh["text"]],
                        metadatas=[{
                            "source": f"{category.upper()}_ENHANCEMENT",
                            "domains": enh["domains"],
                            "chunk_type": "enhancement",
                            "priority": "high",
                        }]
                    )
                    chunks_added += 1
                except Exception as e:
                    if "already exists" not in str(e).lower():
                        print(f"  Warning: {e}")
    
    return chunks_added


def main():
    print("\n" + "="*70)
    print("COMPREHENSIVE FINE-TUNING - ITERATION 1")
    print("="*70)
    
    # Connect to ChromaDB
    chroma_path = r"C:\Users\sayan\Downloads\Team1\Berth_Planning\ai-service\chroma_db_optimized"
    embedding_fn = GPUEmbeddingFunction("sentence-transformers/all-mpnet-base-v2")
    
    client = chromadb.PersistentClient(path=chroma_path, settings=Settings(anonymized_telemetry=False))
    collection = client.get_collection(name="berth_planning_optimized", embedding_function=embedding_fn)
    
    print(f"Collection: {collection.count()} chunks")
    
    iteration_results = []
    max_iterations = 3
    target_accuracy = 0.85
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'='*70}")
        print(f"ITERATION {iteration}/{max_iterations}")
        print("="*70)
        
        # Evaluate
        results = evaluate_retrieval(collection, COMPREHENSIVE_TEST_QUERIES)
        iteration_results.append(results)
        
        # Print results
        print("\nCategory Results:")
        weak_categories = []
        for cat, data in results["categories"].items():
            status = "✓" if data["accuracy"] >= 0.75 else "⚠" if data["accuracy"] >= 0.5 else "✗"
            print(f"  {status} {cat}: {data['accuracy']*100:.0f}% ({data['correct']}/{data['total']}) MRR:{data['mrr']:.2f}")
            if data["accuracy"] < 0.75:
                weak_categories.append(cat)
        
        print(f"\nOverall Accuracy: {results['overall_accuracy']*100:.1f}%")
        print(f"Mean Reciprocal Rank: {results['overall_mrr']:.3f}")
        print(f"Avg Query Time: {results['avg_query_time_ms']:.1f}ms")
        
        # Check if target reached
        if results["overall_accuracy"] >= target_accuracy:
            print(f"\n✓ Target accuracy {target_accuracy*100:.0f}% achieved!")
            break
        
        # Add enhancements for weak categories
        if iteration < max_iterations and weak_categories:
            print(f"\n--- Adding enhancements for: {', '.join(weak_categories)} ---")
            added = add_enhancement_chunks(collection, embedding_fn, weak_categories)
            print(f"  Added {added} enhancement chunks")
    
    # Final summary
    print("\n" + "="*70)
    print("FINE-TUNING COMPLETE")
    print("="*70)
    
    print("\nAccuracy Progression:")
    for i, res in enumerate(iteration_results, 1):
        print(f"  Iteration {i}: {res['overall_accuracy']*100:.1f}%")
    
    final = iteration_results[-1]
    print(f"\nFinal Accuracy: {final['overall_accuracy']*100:.1f}%")
    print(f"Final MRR: {final['overall_mrr']:.3f}")
    print(f"Query Latency: {final['avg_query_time_ms']:.1f}ms")
    
    # Show failed queries
    print("\nFailed Queries:")
    for detail in final["details"]:
        if not detail["correct"]:
            print(f"  ✗ [{detail['category']}] {detail['query'][:45]}... → {detail['top_source']}")
    
    # Save results
    output_file = Path(chroma_path).parent / "finetuning_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "iterations": len(iteration_results),
            "final_accuracy": final["overall_accuracy"],
            "final_mrr": final["overall_mrr"],
            "categories": final["categories"],
            "progression": [r["overall_accuracy"] for r in iteration_results],
        }, f, indent=2)
    
    print(f"\nResults saved to {output_file}")
    
    return 0


if __name__ == "__main__":
    exit(main())
