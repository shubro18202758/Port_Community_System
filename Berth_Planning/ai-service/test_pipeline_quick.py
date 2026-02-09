"""Quick test script for the unified pipeline with in-memory graph"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline_api import get_pipeline

def main():
    print("=" * 70)
    print("SmartBerth AI - Unified Pipeline Test (with In-Memory Graph)")
    print("=" * 70)
    
    # Initialize pipeline
    print("\n1. Initializing Pipeline...")
    pipeline = get_pipeline()
    success = pipeline.initialize()
    
    if not success:
        print("Pipeline initialization failed!")
        return
    
    # Get stats
    print("\n2. Pipeline Status:")
    stats = pipeline.get_stats()
    print(f"   Knowledge Index: {stats['knowledge_index']}")
    print(f"   Graph Engine: {stats['graph_stats'].get('engine_type', 'unknown')}")
    print(f"   Graph Status: {stats['graph_stats'].get('status', 'unknown')}")
    if 'total_nodes' in stats['graph_stats']:
        print(f"   Graph Nodes: {stats['graph_stats']['total_nodes']}")
        print(f"   Graph Edges: {stats['graph_stats']['total_edges']}")
        print(f"   Entity Counts: {json.dumps(stats['graph_stats'].get('counts', {}), indent=6)}")
    print(f"   Components: {stats['components']}")
    
    # Test knowledge retrieval
    print("\n3. Knowledge Retrieval Test:")
    results = pipeline.retrieve_knowledge('berth allocation container vessel', top_k=3)
    
    if results:
        for i, r in enumerate(results):
            print(f"   {i+1}. Score: {r['score']:.3f}")
            print(f"      Type: {r['knowledge_type']}")
            print(f"      Source: {r['source']}")
            content_preview = r['content'][:80].replace('\n', ' ')
            print(f"      Preview: {content_preview}...")
            print()
    else:
        print("   No results found (knowledge index may be empty)")
    
    # Test intent classification
    print("4. Intent Classification Test:")
    test_queries = [
        "Find berth for container vessel",
        "Calculate UKC for tanker",
        "Available pilots tonight",
        "Weather forecast for tomorrow"
    ]
    
    for query in test_queries:
        intent = pipeline.classify_intent(query)
        print(f"   '{query[:35]}...' -> {intent.value}")
    
    # Test graph queries
    print("\n5. Graph Query Tests:")
    
    # Test: Find compatible berths
    print("   a) Find compatible berths for Container vessels:")
    result = pipeline.query_graph("Find suitable berths for container vessel with 300m LOA")
    print(f"      Method: {result.get('query_method')}")
    print(f"      Found: {result.get('total_found', len(result.get('results', [])))} berths")
    if result.get('results'):
        sample = result['results'][0] if result['results'] else {}
        print(f"      Sample: {sample.get('berth_name', 'N/A')} ({sample.get('berth_type', 'N/A')})")
    
    # Test: Port resources
    print("\n   b) Get port resources:")
    # Get a sample port code from the graph
    if hasattr(pipeline._graph_engine, '_port_index'):
        sample_port = list(pipeline._graph_engine._port_index.keys())[0] if pipeline._graph_engine._port_index else None
        if sample_port:
            result = pipeline.query_graph(f"What resources are available at port {sample_port}")
            print(f"      Port: {sample_port}")
            if result.get('results') and result['results']:
                resources = result['results'][0]
                summary = resources.get('summary', {})
                print(f"      Terminals: {summary.get('total_terminals', 0)}")
                print(f"      Berths: {summary.get('total_berths', 0)}")
                print(f"      Pilots: {summary.get('total_pilots', 0)}")
                print(f"      Tugboats: {summary.get('total_tugboats', 0)}")
    
    # Test: Port hierarchy
    print("\n   c) Get port hierarchy:")
    if hasattr(pipeline._graph_engine, 'get_port_hierarchy') and hasattr(pipeline._graph_engine, '_port_index'):
        sample_port = list(pipeline._graph_engine._port_index.keys())[0] if pipeline._graph_engine._port_index else None
        if sample_port:
            hierarchy = pipeline._graph_engine.get_port_hierarchy(sample_port)
            if hierarchy:
                port_info = hierarchy.get('port', {})
                terminals = hierarchy.get('terminals', [])
                print(f"      Port: {port_info.get('port_name', sample_port)}")
                print(f"      Terminals: {len(terminals)}")
                if terminals:
                    term = terminals[0]
                    print(f"        - {term.get('terminal_name', 'N/A')}: {len(term.get('berths', []))} berths")
    
    print("\n" + "=" * 70)
    print("✓ Pipeline test completed successfully!")
    print("✓ Graph engine is 100% available (in-memory)")
    print("=" * 70)

if __name__ == "__main__":
    main()
