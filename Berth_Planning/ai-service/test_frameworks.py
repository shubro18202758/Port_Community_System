"""
SmartBerth Framework Integration Test
======================================

Tests all 6 SOTA RAG frameworks working together:
- Manager Agent (Qwen3-8B via Ollama)
- Central AI (Claude - simulated for test)
- All 6 frameworks from 3 tiers
"""

import sys
import asyncio
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_framework_imports():
    """Test all framework imports"""
    print("\n" + "="*60)
    print("TEST 1: Framework Imports")
    print("="*60)
    
    from frameworks import (
        FRAMEWORK_INFO,
        get_framework_info,
        get_tier_frameworks,
        # Tier 1
        RagasEvaluator, get_ragas_evaluator,
        DSPyOptimizer, get_dspy_optimizer,
        # Tier 2
        GraphRAGEngine, get_graphrag_engine,
        ColBERTRetriever, RagatouilleRetriever,
        get_colbert_retriever, get_ragatouille_retriever,
        # Tier 3
        PathwaySyncPipeline, get_pathway_pipeline,
        Mem0MemoryManager, get_memory_manager
    )
    
    print("✓ All imports successful!")
    
    print("\nFramework Status:")
    for name, info in FRAMEWORK_INFO.items():
        print(f"  Tier {info['tier']}: {info['name']} - {info['status']}")
    
    return True


def test_manager_agent():
    """Test Manager Agent (Qwen3-8B via Ollama)"""
    print("\n" + "="*60)
    print("TEST 2: Manager Agent (Qwen3-8B via Ollama)")
    print("="*60)
    
    try:
        from manager_agent.local_llm import OllamaLLM
        
        llm = OllamaLLM()
        
        # Test classification
        test_queries = [
            "What berths are available for vessel MV Pacific?",
            "Find all vessels arriving tomorrow",
            "How does the UKC calculation work?"
        ]
        
        for query in test_queries:
            result = llm.classify_task(query)
            print(f"  Query: {query[:40]}...")
            print(f"    → Task: {result.get('task_type', 'unknown')}, Confidence: {result.get('confidence', 0):.2f}")
        
        print("✓ Manager Agent working!")
        return True
        
    except Exception as e:
        print(f"✗ Manager Agent error: {e}")
        return False


def test_tier1_ragas():
    """Test Tier 1: RAGAS Evaluation"""
    print("\n" + "="*60)
    print("TEST 3: Tier 1 - RAGAS Evaluation Framework")
    print("="*60)
    
    from frameworks import get_ragas_evaluator
    
    # Create mock LLM class with chat method
    class MockLLM:
        def chat(self, messages, max_tokens=500, temperature=0.1):
            prompt = messages[0]["content"] if messages else ""
            if "faithfulness" in prompt.lower():
                return '{"verdict": "yes", "reason": "Answer aligns with context"}'
            elif "relevance" in prompt.lower():
                return '{"verdict": "yes", "reason": "Answer addresses the question"}'
            return "Mock response"
    
    mock_llm = MockLLM()
    evaluator = get_ragas_evaluator(local_llm=mock_llm, use_local_llm=True)
    
    # Create evaluation sample
    from frameworks.ragas_eval import EvaluationSample
    sample = EvaluationSample(
        question="What is the draft requirement for Berth A1?",
        answer="Berth A1 requires a minimum draft of 12 meters.",
        contexts=["Berth A1 is a deep water berth with 12m draft requirement."],
        ground_truth="Berth A1 has a 12 meter draft requirement."
    )
    
    # Test evaluation
    result = evaluator.evaluate_sample(sample)
    
    print(f"  Faithfulness: {result.faithfulness:.2f}")
    print(f"  Answer Relevance: {result.answer_relevance:.2f}")
    print(f"  Context Precision: {result.context_precision:.2f}")
    print(f"  Context Recall: {result.context_recall:.2f}")
    print(f"  Overall Score: {result.overall_score:.2f}")
    
    print("✓ RAGAS Evaluation working!")
    return True


def test_tier1_dspy():
    """Test Tier 1: DSPy Optimization"""
    print("\n" + "="*60)
    print("TEST 4: Tier 1 - DSPy Prompt Optimization")
    print("="*60)
    
    from frameworks import get_dspy_optimizer
    from frameworks.dspy_optimizer import Predict, ChainOfThought, BERTH_RECOMMENDATION_SIG
    
    # Mock LLM for testing
    def mock_llm(prompt):
        return "recommended_berth: Berth A1\nreasoning: Based on vessel specifications, A1 is optimal\nconstraints_satisfied: Yes, all constraints met"
    
    optimizer = get_dspy_optimizer(mock_llm)
    
    # Test prediction using forward method
    predictor = Predict(BERTH_RECOMMENDATION_SIG, mock_llm)
    result = predictor.forward(
        vessel_specs="LOA: 200m, Beam: 32m, Draft: 10m",
        requirements="Container handling, quick turnaround",
        constraints="Available from Monday"
    )
    
    print(f"  Signature: {BERTH_RECOMMENDATION_SIG.name}")
    print(f"  Input Fields: {[f.name for f in BERTH_RECOMMENDATION_SIG.input_fields]}")
    print(f"  Output Fields: {[f.name for f in BERTH_RECOMMENDATION_SIG.output_fields]}")
    print(f"  Result Keys: {list(result.keys())}")
    
    print("✓ DSPy Optimization working!")
    return True


def test_tier2_graphrag():
    """Test Tier 2: GraphRAG"""
    print("\n" + "="*60)
    print("TEST 5: Tier 2 - GraphRAG Engine")
    print("="*60)
    
    from frameworks import get_graphrag_engine
    
    # Mock LLM for entity extraction
    def mock_llm(prompt):
        if "extract" in prompt.lower():
            return '[{"name": "MV Pacific", "type": "VESSEL", "description": "Container ship"}]'
        elif "relationship" in prompt.lower():
            return '[{"source": "MV Pacific", "target": "Berth A1", "type": "DOCKS_AT"}]'
        elif "community" in prompt.lower():
            return '{"name": "Container Operations", "description": "Container vessel cluster"}'
        elif "summarize" in prompt.lower():
            return "This community handles container vessel operations at Terminal A."
        else:
            return "GraphRAG response based on context."
    
    engine = get_graphrag_engine(mock_llm)
    
    # Build small test index
    documents = [
        {"content": "MV Pacific is a container vessel docking at Berth A1."},
        {"content": "Berth A1 is located at Terminal A with 14m depth."},
        {"content": "Terminal A handles container operations."}
    ]
    
    index = engine.build_index(documents, generate_summaries=False)
    
    print(f"  Entities: {len(index.entities)}")
    print(f"  Relationships: {len(index.relationships)}")
    print(f"  Communities: {len(index.communities)}")
    
    # Test search
    local_result = engine.local_search("What berth does MV Pacific use?")
    print(f"  Local Search - Entities found: {len(local_result.get('entities', []))}")
    
    print("✓ GraphRAG Engine working!")
    return True


def test_tier2_colbert():
    """Test Tier 2: ColBERT/Ragatouille"""
    print("\n" + "="*60)
    print("TEST 6: Tier 2 - ColBERT/Ragatouille Retriever")
    print("="*60)
    
    from frameworks import get_ragatouille_retriever
    
    retriever = get_ragatouille_retriever(model_name="test-colbert")
    
    # Index documents
    documents = [
        "Berth A1 has a maximum draft of 14 meters.",
        "Berth B2 is suitable for tanker vessels.",
        "Container vessels should use Terminal C berths.",
        "The port operates 24/7 with pilot services.",
        "Tugboat assistance is required for vessels over 200m LOA."
    ]
    
    result = retriever.index(documents, index_name="test_index")
    print(f"  Indexed: {result['indexed']} documents")
    
    # Search
    results = retriever.search("What is the draft for Berth A1?", k=3)
    print(f"  Search results: {len(results)}")
    if results:
        print(f"  Top result score: {results[0]['score']:.2f}")
    
    # Rerank
    reranked = retriever.rerank("tanker berth", documents[:3], k=2)
    print(f"  Reranked: {len(reranked)} results")
    
    print("✓ ColBERT/Ragatouille working!")
    return True


def test_tier3_pathway():
    """Test Tier 3: Pathway Real-time Sync"""
    print("\n" + "="*60)
    print("TEST 7: Tier 3 - Pathway Real-time Sync")
    print("="*60)
    
    from frameworks import get_pathway_pipeline
    from frameworks.pathway_sync import SourceType
    
    pipeline = get_pathway_pipeline()
    
    # Add a file source
    source = pipeline.add_source(
        name="test_source",
        source_type=SourceType.FILE,
        config={"path": ".", "pattern": "*.json"},
        poll_interval=60.0
    )
    
    status = pipeline.get_status()
    print(f"  Pipeline running: {status['running']}")
    print(f"  Sources configured: {len(status['sources'])}")
    print(f"  Total synced: {status['total_synced']}")
    
    print("✓ Pathway Sync working!")
    return True


def test_tier3_mem0():
    """Test Tier 3: Mem0 Memory"""
    print("\n" + "="*60)
    print("TEST 8: Tier 3 - Mem0 Memory Layer")
    print("="*60)
    
    from frameworks import get_memory_manager
    from frameworks.mem0_memory import MemoryType, MemoryPriority
    
    # Mock LLM for memory extraction
    def mock_llm(prompt):
        return '[{"content": "User prefers quick turnaround", "type": "long_term", "priority": 3}]'
    
    memory = get_memory_manager(mock_llm)
    
    # Add explicit memory
    mem1 = memory.add(
        "User operates container vessels primarily",
        memory_type=MemoryType.LONG_TERM,
        priority=MemoryPriority.HIGH,
        user_id="test_user"
    )
    print(f"  Added memory: {mem1.id}")
    
    # Add from conversation
    memories = memory.add_from_conversation(
        user_message="I need a berth for my tanker vessel arriving Friday",
        assistant_response="I'll find suitable tanker berths for Friday arrival.",
        user_id="test_user",
        session_id="session_1"
    )
    print(f"  Extracted {len(memories)} memories from conversation")
    
    # Search memory
    results = memory.search("container vessels", user_id="test_user", limit=5)
    print(f"  Memory search results: {len(results)}")
    
    # Get context
    context = memory.get_context("What berth should I use?", user_id="test_user")
    print(f"  Context length: {len(context)} chars")
    
    # Stats
    stats = memory.get_stats()
    print(f"  Total memories: {stats['total_memories']}")
    
    print("✓ Mem0 Memory working!")
    return True


def test_advanced_pipeline():
    """Test Advanced Pipeline Integration"""
    print("\n" + "="*60)
    print("TEST 9: Advanced Pipeline Integration")
    print("="*60)
    
    from frameworks.advanced_pipeline import AdvancedRAGPipeline, create_advanced_pipeline
    
    # Mock LLMs
    def mock_manager(prompt):
        return '{"intent": "retrieval"}'
    
    def mock_central(prompt):
        return "Based on the available information, Berth A1 is recommended for your vessel."
    
    def mock_embedder(text):
        import hashlib
        # Simple deterministic embedding
        hash_val = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
        return [float(hash_val % 1000) / 1000.0] * 128
    
    # Create pipeline
    pipeline = create_advanced_pipeline(
        manager_llm_caller=mock_manager,
        central_llm_caller=mock_central,
        embedder=mock_embedder,
        enable_evaluation=False,  # Skip for speed
        enable_memory=True,
        enable_realtime_sync=False
    )
    
    # Get status
    status = pipeline.get_status()
    print(f"  Pipeline status: {status['pipeline_status']}")
    print(f"  Components enabled: {list(status['components'].keys())}")
    
    print("✓ Advanced Pipeline working!")
    return True


async def test_pipeline_query():
    """Test a full query through the pipeline"""
    print("\n" + "="*60)
    print("TEST 10: Full Pipeline Query (Async)")
    print("="*60)
    
    from frameworks.advanced_pipeline import create_advanced_pipeline
    
    # Mock LLMs
    def mock_manager(prompt):
        return '{"intent": "retrieval"}'
    
    def mock_central(prompt):
        return "Based on the context, I recommend Berth A1 for your vessel."
    
    def mock_embedder(text):
        return [0.1] * 128
    
    pipeline = create_advanced_pipeline(
        manager_llm_caller=mock_manager,
        central_llm_caller=mock_central,
        embedder=mock_embedder,
        enable_evaluation=False,
        enable_memory=True,
        enable_realtime_sync=False
    )
    
    # Process query
    response = await pipeline.process(
        query="What berth is best for a 200m container vessel?",
        user_id="test_user",
        use_memory=True,
        use_graph=False,  # No graph index built
        evaluate=False
    )
    
    print(f"  Query: {response.query[:40]}...")
    print(f"  Intent: {response.intent.value}")
    print(f"  Answer: {response.answer[:50]}...")
    print(f"  Latency: {response.latency_ms:.1f}ms")
    print(f"  Memory used: {response.memory_used}")
    
    print("✓ Full Pipeline Query working!")
    return True


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("  SMARTBERTH FRAMEWORK INTEGRATION TEST SUITE")
    print("  Testing 6 SOTA RAG Frameworks + Pipeline")
    print("="*60)
    print(f"  Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # Test 1: Imports
    results.append(("Framework Imports", test_framework_imports()))
    
    # Test 2: Manager Agent
    results.append(("Manager Agent", test_manager_agent()))
    
    # Test 3-4: Tier 1
    results.append(("Tier 1 - RAGAS", test_tier1_ragas()))
    results.append(("Tier 1 - DSPy", test_tier1_dspy()))
    
    # Test 5-6: Tier 2
    results.append(("Tier 2 - GraphRAG", test_tier2_graphrag()))
    results.append(("Tier 2 - ColBERT", test_tier2_colbert()))
    
    # Test 7-8: Tier 3
    results.append(("Tier 3 - Pathway", test_tier3_pathway()))
    results.append(("Tier 3 - Mem0", test_tier3_mem0()))
    
    # Test 9: Advanced Pipeline
    results.append(("Advanced Pipeline", test_advanced_pipeline()))
    
    # Test 10: Full Query (async)
    try:
        async_result = asyncio.run(test_pipeline_query())
        results.append(("Pipeline Query", async_result))
    except Exception as e:
        print(f"  Async test error: {e}")
        results.append(("Pipeline Query", False))
    
    # Summary
    print("\n" + "="*60)
    print("  TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n  Results: {passed}/{total} tests passed")
    print(f"  Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
