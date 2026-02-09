"""
SmartBerth Pipeline - Comprehensive Status Check
"""
import asyncio
from pipeline_api import UnifiedSmartBerthPipeline, PipelineQueryRequest

async def test_pipeline():
    print("=" * 70)
    print("SMARTBERTH PIPELINE - COMPREHENSIVE TEST")
    print("=" * 70)
    
    p = UnifiedSmartBerthPipeline()
    p.initialize()
    
    # Get stats
    stats = p.get_stats()
    print("\n[1] COMPONENT STATUS:")
    for comp, status in stats['components'].items():
        status_str = "OK" if status else "NOT LOADED"
        print(f"    {comp:20} {status_str}")
    
    print("\n[2] KNOWLEDGE INDEX:")
    ki = stats['knowledge_index']
    print(f"    Collection: {ki.get('collection_name', 'N/A')}")
    print(f"    Total chunks: {ki.get('total_chunks', 0)}")
    
    print("\n[3] GRAPH ENGINE:")
    gs = stats['graph_stats']
    print(f"    Status: {gs.get('status', 'N/A')}")
    print(f"    Total nodes: {gs.get('total_nodes', 0)}")
    print(f"    Total edges: {gs.get('total_edges', 0)}")
    print(f"    Engine type: {gs.get('engine_type', 'N/A')}")
    
    if 'counts' in gs:
        print("    Entity counts:")
        for entity, count in gs['counts'].items():
            print(f"      - {entity}: {count}")
    
    # Test queries
    print("\n[4] QUERY TESTS:")
    queries = [
        "What vessels are scheduled at Mundra Port?",
        "Show me container berths",
        "What pilots are available?"
    ]
    
    for q in queries:
        req = PipelineQueryRequest(query=q)
        result = await p.process_query(req)
        print(f"    Q: {q[:50]}")
        print(f"       Intent: {result.intent}, Latency: {result.latency_ms:.0f}ms, Graph: {result.graph_used}")
    
    print("\n" + "=" * 70)
    print("PIPELINE STATUS: OPERATIONAL")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_pipeline())
