"""Quick system check for all SmartBerth AI components"""
import sys
import json

print("=" * 60)
print("SMARTBERTH AI - SYSTEM CHECK")
print("=" * 60)

# 1. GPU Check
print("\n[1] GPU STATUS")
try:
    import torch
    print(f"  CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
        props = torch.cuda.get_device_properties(0)
        print(f"  VRAM: {props.total_memory / 1024**3:.1f} GB")
        print(f"  Allocated: {torch.cuda.memory_allocated()/1024**2:.1f} MB")
        print(f"  Reserved: {torch.cuda.memory_reserved()/1024**2:.1f} MB")
    else:
        print("  No CUDA GPU available")
except ImportError:
    print("  PyTorch not installed")

# 2. Ollama Check
print("\n[2] OLLAMA / MANAGER AGENT (Qwen3-8B)")
try:
    import httpx
    r = httpx.get("http://localhost:11434/api/tags", timeout=5)
    data = r.json()
    models = data.get("models", [])
    print(f"  Ollama running: {len(models)} models available")
    for m in models:
        name = m.get("name", "unknown")
        size = m.get("size", 0) / 1024**3
        print(f"    - {name} ({size:.1f}GB)")
    
    # Check if Qwen3 is loaded into GPU
    try:
        r2 = httpx.get("http://localhost:11434/api/ps", timeout=5)
        ps_data = r2.json()
        running = ps_data.get("models", [])
        if running:
            print(f"  Currently loaded in GPU: {len(running)} models")
            for m in running:
                print(f"    - {m.get('name', 'unknown')} (VRAM: {m.get('size_vram', 0)/1024**3:.1f}GB)")
        else:
            print("  No models currently loaded in GPU memory")
    except Exception as e:
        print(f"  Could not check GPU-loaded models: {e}")
        
except httpx.ConnectError:
    print("  Ollama NOT running (connection refused)")
except Exception as e:
    print(f"  Ollama check failed: {e}")

# 3. Claude API Check
print("\n[3] CENTRAL AI (Claude Opus 4)")
try:
    import anthropic
    from config import get_settings
    settings = get_settings()
    print(f"  Model: {settings.claude_model}")
    print(f"  API Key: {'set' if settings.anthropic_api_key else 'NOT SET'}")
    
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    resp = client.messages.create(
        model=settings.claude_model,
        max_tokens=10,
        messages=[{"role": "user", "content": "Hi"}]
    )
    print(f"  Status: CONNECTED (test response OK)")
except Exception as e:
    print(f"  Claude API: {e}")

# 4. ChromaDB Knowledge Index
print("\n[4] KNOWLEDGE INDEX (ChromaDB)")
try:
    import chromadb
    import os
    
    # Check unified index
    unified_path = os.path.join(os.path.dirname(__file__), "chroma_db_unified")
    if os.path.exists(unified_path):
        client = chromadb.PersistentClient(path=unified_path)
        coll = client.get_collection("smartberth_unified")
        print(f"  Unified index: {coll.count()} chunks")
    else:
        print(f"  Unified index: NOT FOUND")
    
    # Check new index
    new_path = os.path.join(os.path.dirname(__file__), "chroma_db_new")
    if os.path.exists(new_path):
        client2 = chromadb.PersistentClient(path=new_path)
        try:
            coll2 = client2.get_collection("smartberth_knowledge")
            print(f"  Knowledge index: {coll2.count()} chunks")
        except:
            print("  Knowledge index: collection not found")
    else:
        print(f"  Knowledge index (chroma_db_new): NOT FOUND")
        
except Exception as e:
    print(f"  ChromaDB: {e}")

# 5. In-Memory Graph
print("\n[5] KNOWLEDGE GRAPH (In-Memory)")
try:
    from inmemory_graph import get_knowledge_graph
    graph = get_knowledge_graph()
    if graph.load():
        stats = graph.get_stats()
        print(f"  Status: LOADED")
        print(f"  Nodes: {stats['total_nodes']}, Edges: {stats['total_edges']}")
        print(f"  Ports: {stats['counts']['ports']}, Terminals: {stats['counts']['terminals']}, Berths: {stats['counts']['berths']}")
        print(f"  Vessels: {stats['counts']['vessels']}, Pilots: {stats['counts']['pilots']}, Tugs: {stats['counts']['tugboats']}")
    else:
        print("  Status: FAILED TO LOAD")
except Exception as e:
    print(f"  Graph: {e}")

# 6. Database
print("\n[6] DATABASE (SQL Server)")
try:
    from database import get_db_service
    db = get_db_service()
    if db.test_connection():
        print("  Status: CONNECTED")
    else:
        print("  Status: DISCONNECTED")
except Exception as e:
    print(f"  Database: {e}")

# 7. RAG Pipeline
print("\n[7] RAG PIPELINE")
try:
    from rag import get_rag_pipeline
    rag = get_rag_pipeline()
    if rag.initialize():
        count = rag.collection.count() if rag.collection else 0
        print(f"  Status: INITIALIZED ({count} documents)")
    else:
        print("  Status: FAILED")
except Exception as e:
    print(f"  RAG: {e}")

# 8. Sentence Transformers (Embedding Model)
print("\n[8] EMBEDDING MODEL")
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    device = str(model.device)
    print(f"  Model: all-MiniLM-L6-v2")
    print(f"  Device: {device}")
    # Check if it's on GPU
    if "cuda" in device:
        print("  Running on: GPU")
    else:
        print("  Running on: CPU")
except Exception as e:
    print(f"  Embeddings: {e}")

# 9. Frameworks Check
print("\n[9] FRAMEWORKS STATUS")
frameworks = ["ragas_eval", "dspy_optimizer", "graphrag_engine", "colbert_retriever", "pathway_sync", "mem0_memory"]
for fw in frameworks:
    try:
        mod = __import__(f"frameworks.{fw}", fromlist=[fw])
        print(f"  {fw}: Available")
    except Exception as e:
        print(f"  {fw}: {e}")

# 10. Agents Check
print("\n[10] AGENTS STATUS")
agents = ["base_agent", "eta_agent", "berth_agent", "conflict_agent"]
for ag in agents:
    try:
        mod = __import__(f"agents.{ag}", fromlist=[ag])
        print(f"  {ag}: Available")
    except Exception as e:
        print(f"  {ag}: {e}")

print("\n" + "=" * 60)
print("SYSTEM CHECK COMPLETE")
print("=" * 60)
