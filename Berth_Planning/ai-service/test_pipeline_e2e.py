"""
End-to-End Pipeline Verification Test
Tests the full SmartBerth pipeline: ChromaDB → Graph → Manager Agent → Claude
"""
import asyncio
import sys
import time
import traceback

# Track results
results = {}

def log(msg, status="INFO"):
    icons = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}
    print(f"  {icons.get(status, 'ℹ️')} {msg}")

async def test_knowledge_retrieval():
    """Test 1: ChromaDB knowledge retrieval"""
    print("\n" + "="*60)
    print("TEST 1: Knowledge Retrieval (ChromaDB)")
    print("="*60)
    try:
        import chromadb
        
        # Test unified collection
        client_unified = chromadb.PersistentClient(path="./chroma_db_unified")
        col_unified = client_unified.get_collection("smartberth_unified")
        count_unified = col_unified.count()
        log(f"Unified collection: {count_unified} chunks", "PASS")
        
        # Test search
        search_results = col_unified.query(
            query_texts=["berth allocation for container vessel at JNPT"],
            n_results=5
        )
        log(f"Search returned {len(search_results['documents'][0])} results", "PASS")
        for i, doc in enumerate(search_results['documents'][0][:3]):
            meta = search_results['metadatas'][0][i]
            preview = doc[:80].replace('\n', ' ')
            log(f"  Result {i+1} [{meta.get('category', 'unknown')}]: {preview}...")
        
        # Test RAG collection
        client_rag = chromadb.PersistentClient(path="./chroma_db_new")
        col_rag = client_rag.get_collection("smartberth_knowledge")
        count_rag = col_rag.count()
        log(f"RAG collection: {count_rag} chunks", "PASS")
        
        results["knowledge_retrieval"] = True
        return True
    except Exception as e:
        log(f"FAILED: {e}", "FAIL")
        traceback.print_exc()
        results["knowledge_retrieval"] = False
        return False


async def test_graph_engine():
    """Test 2: In-Memory Graph queries"""
    print("\n" + "="*60)
    print("TEST 2: Graph Engine (In-Memory)")
    print("="*60)
    try:
        from inmemory_graph import get_knowledge_graph
        
        graph = get_knowledge_graph()
        graph.load()  # Load the graph data
        stats = graph.get_stats()
        log(f"Graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges", "PASS")
        
        # Test node counts by type
        log(f"Ports: {stats['counts'].get('ports', 0)}", "PASS")
        log(f"Berths: {stats['counts'].get('berths', 0)}", "PASS")
        log(f"Vessels: {stats['counts'].get('vessels', 0)}", "PASS")
        log(f"Pilots: {stats['counts'].get('pilots', 0)}", "PASS")
        
        results["graph_engine"] = True
        return True
    except Exception as e:
        log(f"FAILED: {e}", "FAIL")
        traceback.print_exc()
        results["graph_engine"] = False
        return False


async def test_manager_agent():
    """Test 3: Manager Agent (Ollama/Qwen3-8B)"""
    print("\n" + "="*60)
    print("TEST 3: Manager Agent (Ollama → Qwen3-8B)")
    print("="*60)
    try:
        from manager_agent.local_llm import OllamaLLM
        
        llm = OllamaLLM()
        log(f"OllamaLLM initialized: model={llm.model}", "PASS")
        
        # Test task classification (sync method, not async)
        t0 = time.time()
        classification = llm.classify_task(
            "What berths are available for a 300m container vessel arriving tomorrow?"
        )
        t1 = time.time()
        task_type = classification.get('task_type', 'unknown') if isinstance(classification, dict) else classification
        log(f"Task classified in {t1-t0:.1f}s: {task_type}", "PASS")
        
        results["manager_agent"] = True
        return True
    except Exception as e:
        log(f"FAILED: {e}", "FAIL")
        traceback.print_exc()
        results["manager_agent"] = False
        return False


async def test_central_llm():
    """Test 4: Central LLM (Claude Opus 4)"""
    print("\n" + "="*60)
    print("TEST 4: Central LLM (Claude Opus 4)")
    print("="*60)
    try:
        from model import SmartBerthLLM
        
        llm = SmartBerthLLM()
        llm.initialize()
        log(f"SmartBerthLLM initialized: {llm.settings.claude_model}", "PASS")
        
        # Test generation with a maritime query
        t0 = time.time()
        response = llm.generate_text(
            "Briefly explain what factors affect berth allocation at JNPT port. Keep it under 100 words."
        )
        t1 = time.time()
        
        # Handle dict or string response
        if isinstance(response, dict):
            text = response.get('text', '')
            tokens = response.get('total_tokens', 0)
            log(f"Claude responded in {t1-t0:.1f}s ({tokens} tokens)", "PASS")
            preview = text[:150].replace('\n', ' ')
            log(f"  Preview: {preview}...")
        elif response and len(response) > 20:
            preview = response[:150].replace('\n', ' ')
            log(f"Claude responded in {t1-t0:.1f}s ({len(response)} chars)", "PASS")
            log(f"  Preview: {preview}...")
        else:
            log(f"Claude response unexpected: {response}", "WARN")
        
        results["central_llm"] = True
        return True
    except Exception as e:
        log(f"FAILED: {e}", "FAIL")
        traceback.print_exc()
        results["central_llm"] = False
        return False


async def test_unified_pipeline():
    """Test 5: Full Unified Pipeline (end-to-end)"""
    print("\n" + "="*60)
    print("TEST 5: Unified Pipeline (End-to-End)")
    print("="*60)
    try:
        from pipeline_api import UnifiedSmartBerthPipeline, PipelineQueryRequest
        
        pipeline = UnifiedSmartBerthPipeline()
        pipeline.initialize()
        
        # Check initialization status (attributes prefixed with underscore)
        log(f"Knowledge Index: {'✓' if pipeline._knowledge_collection else '✗'}", 
            "PASS" if pipeline._knowledge_collection else "FAIL")
        log(f"Graph Engine: {'✓' if pipeline._graph_engine else '✗'}", 
            "PASS" if pipeline._graph_engine else "FAIL")
        log(f"Manager Agent: {'✓' if pipeline._manager_agent else '✗'}", 
            "PASS" if pipeline._manager_agent else "WARN")
        log(f"Central LLM: {'✓' if pipeline._central_llm else '✗'}", 
            "PASS" if pipeline._central_llm else "FAIL")
        
        # Test intent classification
        test_queries = [
            "What berths are available for a container ship at JNPT?",
            "How does the conflict detection system work?",
            "What is the ETA prediction accuracy for vessel MSC Diana?",
        ]
        
        for query in test_queries:
            intent = pipeline.classify_intent(query)
            log(f"Intent: '{query[:50]}...' → {intent.value}", "PASS")
        
        # Test knowledge retrieval
        kb_results = pipeline.retrieve_knowledge(
            "berth allocation scoring factors for container vessels"
        )
        if kb_results:
            log(f"Knowledge retrieval: {len(kb_results)} results", "PASS")
        else:
            log("Knowledge retrieval returned empty", "WARN")
        
        # Test full query processing
        print("\n  --- Full Pipeline Query ---")
        t0 = time.time()
        request = PipelineQueryRequest(
            query="What are the key factors in berth allocation at JNPT port? Include information about vessel compatibility and constraint checking."
        )
        full_response = await pipeline.process_query(request)
        t1 = time.time()
        
        if full_response:
            log(f"Full pipeline response in {t1-t0:.1f}s", "PASS")
            log(f"  Response length: {len(full_response.answer)} chars", "PASS")
            log(f"  Context used: {len(full_response.context_used)}", "PASS" if full_response.context_used else "WARN")
            preview = full_response.answer[:200].replace('\n', ' ')
            log(f"  Preview: {preview}...")
        else:
            log("Pipeline returned empty response", "WARN")
        
        results["unified_pipeline"] = True
        return True
    except Exception as e:
        log(f"FAILED: {e}", "FAIL")
        traceback.print_exc()
        results["unified_pipeline"] = False
        return False


async def test_embedding_model():
    """Test 6: Embedding Model on GPU"""
    print("\n" + "="*60)
    print("TEST 6: Embedding Model (GPU)")
    print("="*60)
    try:
        from sentence_transformers import SentenceTransformer
        import torch
        
        model = SentenceTransformer('all-MiniLM-L6-v2')
        device = str(model.device)
        log(f"Embedding model device: {device}", "PASS" if "cuda" in device else "WARN")
        
        # Test embedding
        t0 = time.time()
        embeddings = model.encode(["berth allocation", "vessel tracking", "conflict detection"])
        t1 = time.time()
        log(f"Embedding 3 texts: {t1-t0:.3f}s, dim={embeddings.shape[1]}", "PASS")
        
        # Check GPU memory
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**2
            log(f"GPU memory allocated: {allocated:.0f} MB", "PASS")
        
        results["embedding_model"] = True
        return True
    except Exception as e:
        log(f"FAILED: {e}", "FAIL")
        traceback.print_exc()
        results["embedding_model"] = False
        return False


async def test_database():
    """Test 7: Database connectivity"""
    print("\n" + "="*60)
    print("TEST 7: Database (SQL Server)")
    print("="*60)
    try:
        from database import DatabaseService
        
        db = DatabaseService()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM Vessels")
            vessel_count = cursor.fetchone()[0]
            log(f"Database connected: {vessel_count} vessels", "PASS")
            
            cursor.execute("SELECT COUNT(*) FROM Berths")
            berth_count = cursor.fetchone()[0]
            log(f"Berths in DB: {berth_count}", "PASS")
        
        results["database"] = True
        return True
    except Exception as e:
        log(f"FAILED: {e}", "FAIL")
        traceback.print_exc()
        results["database"] = False
        return False


async def main():
    print("╔" + "═"*58 + "╗")
    print("║  SmartBerth AI - End-to-End Pipeline Verification Test   ║")
    print("╚" + "═"*58 + "╝")
    print(f"\nStarted at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    t_start = time.time()
    
    # Run tests in order (some depend on others)
    await test_embedding_model()
    await test_knowledge_retrieval()
    await test_graph_engine()
    await test_database()
    await test_manager_agent()
    await test_central_llm()
    await test_unified_pipeline()
    
    t_end = time.time()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    passed = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    
    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"  {status}  {test_name}")
    
    print(f"\n  Total: {passed}/{passed+failed} passed")
    print(f"  Time: {t_end - t_start:.1f}s")
    print("="*60)
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
