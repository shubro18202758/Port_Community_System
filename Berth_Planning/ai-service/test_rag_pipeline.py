"""
SmartBerth AI - RAG Pipeline Test Suite
Tests ChromaDB retrieval with 20 comprehensive sample queries
"""

import sys
import time
from datetime import datetime
from typing import List, Dict, Any

# Test queries covering different aspects of berth planning
TEST_QUERIES = [
    # Physical Constraints (1-4)
    {
        "id": 1,
        "category": "Physical Constraints",
        "query": "What are the LOA constraints for berth allocation?",
        "expected_topics": ["LOA", "length", "berth", "constraint"]
    },
    {
        "id": 2,
        "category": "Physical Constraints",
        "query": "How does vessel draft affect berth selection?",
        "expected_topics": ["draft", "depth", "UKC", "water"]
    },
    {
        "id": 3,
        "category": "Physical Constraints",
        "query": "What beam restrictions apply to container vessels?",
        "expected_topics": ["beam", "width", "container"]
    },
    {
        "id": 4,
        "category": "Physical Constraints", 
        "query": "Explain under-keel clearance requirements for deep draft vessels",
        "expected_topics": ["UKC", "clearance", "draft", "safety"]
    },
    
    # Cargo & Terminal Matching (5-8)
    {
        "id": 5,
        "category": "Cargo Matching",
        "query": "Which terminals can handle LNG cargo?",
        "expected_topics": ["LNG", "terminal", "gas", "specialized"]
    },
    {
        "id": 6,
        "category": "Cargo Matching",
        "query": "What equipment is needed for container vessel operations?",
        "expected_topics": ["container", "crane", "equipment", "gantry"]
    },
    {
        "id": 7,
        "category": "Cargo Matching",
        "query": "How are hazardous cargo vessels handled at port?",
        "expected_topics": ["hazardous", "dangerous", "cargo", "safety"]
    },
    {
        "id": 8,
        "category": "Cargo Matching",
        "query": "What are the berth requirements for bulk carriers?",
        "expected_topics": ["bulk", "carrier", "berth", "terminal"]
    },
    
    # Window Vessel Operations (9-11)
    {
        "id": 9,
        "category": "Window Vessel",
        "query": "What is a window vessel and what policies apply?",
        "expected_topics": ["window", "vessel", "policy", "hazardous"]
    },
    {
        "id": 10,
        "category": "Window Vessel",
        "query": "What are the daylight operation restrictions for dangerous cargo?",
        "expected_topics": ["daylight", "dangerous", "operation", "restriction"]
    },
    {
        "id": 11,
        "category": "Window Vessel",
        "query": "Explain exclusion zones for LNG vessel operations",
        "expected_topics": ["exclusion", "zone", "LNG", "safety"]
    },
    
    # Weather & Tidal (12-14)
    {
        "id": 12,
        "category": "Weather Impact",
        "query": "How does wind speed affect berthing operations?",
        "expected_topics": ["wind", "speed", "berthing", "operation"]
    },
    {
        "id": 13,
        "category": "Weather Impact",
        "query": "What are the tidal window requirements for large vessels?",
        "expected_topics": ["tidal", "window", "tide", "vessel"]
    },
    {
        "id": 14,
        "category": "Weather Impact",
        "query": "How does visibility affect pilotage operations?",
        "expected_topics": ["visibility", "pilot", "fog", "navigation"]
    },
    
    # ETA Prediction (15-16)
    {
        "id": 15,
        "category": "ETA Prediction",
        "query": "What factors affect vessel ETA prediction accuracy?",
        "expected_topics": ["ETA", "prediction", "factor", "accuracy"]
    },
    {
        "id": 16,
        "category": "ETA Prediction",
        "query": "How do weather conditions impact vessel arrival times?",
        "expected_topics": ["weather", "arrival", "delay", "impact"]
    },
    
    # Resource Management (17-18)
    {
        "id": 17,
        "category": "Resources",
        "query": "What pilot and tug requirements exist for large tankers?",
        "expected_topics": ["pilot", "tug", "tanker", "requirement"]
    },
    {
        "id": 18,
        "category": "Resources",
        "query": "How are berth maintenance schedules managed?",
        "expected_topics": ["maintenance", "berth", "schedule", "availability"]
    },
    
    # Conflict Resolution (19-20)
    {
        "id": 19,
        "category": "Conflict Resolution",
        "query": "How are scheduling conflicts between vessels resolved?",
        "expected_topics": ["conflict", "scheduling", "resolution", "priority"]
    },
    {
        "id": 20,
        "category": "Conflict Resolution",
        "query": "What priority rules apply when multiple vessels need the same berth?",
        "expected_topics": ["priority", "berth", "allocation", "rule"]
    }
]


def test_rag_pipeline():
    """Test the RAG pipeline with all sample queries"""
    print("=" * 70)
    print("SmartBerth AI - RAG Pipeline Test Suite")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Queries: {len(TEST_QUERIES)}")
    print("=" * 70)
    
    # Initialize RAG components
    print("\n📚 Initializing RAG components...")
    
    try:
        from rag_hybrid import get_retriever
        retriever = get_retriever()
        stats = retriever.get_collection_stats()
        print(f"   ✓ Hybrid Retriever initialized")
        print(f"   ✓ Documents in collection: {stats['total_documents']}")
        print(f"   ✓ BM25 indexed: {stats['bm25_indexed']}")
    except Exception as e:
        print(f"   ✗ Failed to initialize Hybrid Retriever: {e}")
        retriever = None
    
    try:
        from rag import get_rag_pipeline
        rag = get_rag_pipeline()
        rag.initialize()
        print(f"   ✓ Original RAG Pipeline initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize Original RAG: {e}")
        rag = None
    
    if not retriever and not rag:
        print("\n❌ No RAG components available. Exiting.")
        return
    
    # Run tests
    results = []
    total_time = 0
    
    print("\n" + "=" * 70)
    print("Running Query Tests")
    print("=" * 70)
    
    for test in TEST_QUERIES:
        print(f"\n📝 Test {test['id']}: [{test['category']}]")
        print(f"   Query: {test['query'][:60]}...")
        
        test_result = {
            "id": test["id"],
            "category": test["category"],
            "query": test["query"],
            "expected_topics": test["expected_topics"],
            "results": [],
            "success": False,
            "time_ms": 0,
            "topic_match_score": 0
        }
        
        start_time = time.time()
        
        try:
            # Test with hybrid retriever
            if retriever:
                docs = retriever.hybrid_search(test["query"], top_k=3)
                test_result["results"] = [
                    {
                        "source": doc.source,
                        "score": round(doc.score, 4),
                        "method": doc.retrieval_method,
                        "content_preview": doc.content[:200]
                    }
                    for doc in docs
                ]
                test_result["success"] = len(docs) > 0
                
                # Calculate topic match score
                all_content = " ".join([doc.content.lower() for doc in docs])
                matched_topics = sum(1 for topic in test["expected_topics"] 
                                    if topic.lower() in all_content)
                test_result["topic_match_score"] = matched_topics / len(test["expected_topics"])
        
        except Exception as e:
            test_result["error"] = str(e)
            test_result["success"] = False
        
        elapsed = (time.time() - start_time) * 1000
        test_result["time_ms"] = round(elapsed, 2)
        total_time += elapsed
        
        results.append(test_result)
        
        # Print result summary
        status = "✓" if test_result["success"] else "✗"
        topic_pct = test_result["topic_match_score"] * 100
        print(f"   {status} Results: {len(test_result['results'])} docs | "
              f"Topic Match: {topic_pct:.0f}% | Time: {test_result['time_ms']:.1f}ms")
        
        if test_result["results"]:
            top_doc = test_result["results"][0]
            print(f"   Top result: {top_doc['source']} (score: {top_doc['score']:.3f}, {top_doc['method']})")
    
    # Generate summary report
    print("\n" + "=" * 70)
    print("TEST SUMMARY REPORT")
    print("=" * 70)
    
    successful = sum(1 for r in results if r["success"])
    avg_topic_match = sum(r["topic_match_score"] for r in results) / len(results)
    avg_time = total_time / len(results)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Tests:       {len(results)}")
    print(f"   Successful:        {successful} ({successful/len(results)*100:.1f}%)")
    print(f"   Failed:            {len(results) - successful}")
    print(f"   Avg Topic Match:   {avg_topic_match*100:.1f}%")
    print(f"   Avg Response Time: {avg_time:.1f}ms")
    print(f"   Total Time:        {total_time/1000:.2f}s")
    
    # Category breakdown
    print(f"\n📈 Results by Category:")
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"success": 0, "total": 0, "topic_match": 0}
        categories[cat]["total"] += 1
        if r["success"]:
            categories[cat]["success"] += 1
        categories[cat]["topic_match"] += r["topic_match_score"]
    
    for cat, stats in categories.items():
        success_rate = stats["success"] / stats["total"] * 100
        avg_match = stats["topic_match"] / stats["total"] * 100
        print(f"   {cat:20s}: {stats['success']}/{stats['total']} success, {avg_match:.0f}% topic match")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    for r in results:
        status = "✓" if r["success"] else "✗"
        topic_pct = r["topic_match_score"] * 100
        print(f"   {status} Q{r['id']:02d} [{r['category']:20s}] "
              f"Docs:{len(r['results'])} Topic:{topic_pct:3.0f}% Time:{r['time_ms']:6.1f}ms")
    
    # Save results to file
    import json
    report_path = "rag_test_results.json"
    with open(report_path, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tests": len(results),
                "successful": successful,
                "avg_topic_match": avg_topic_match,
                "avg_time_ms": avg_time,
                "total_time_s": total_time / 1000
            },
            "results": results
        }, f, indent=2)
    print(f"\n💾 Results saved to: {report_path}")
    
    print("\n" + "=" * 70)
    print("RAG Pipeline Test Complete!")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    test_rag_pipeline()
