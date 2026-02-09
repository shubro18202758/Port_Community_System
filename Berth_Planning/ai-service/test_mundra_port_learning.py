"""
SmartBerth AI - Mundra Port Data Learning Test
==============================================
Tests all tech stack components learning from Mundra Port berth data:
1. Knowledge Index (ChromaDB) - Vector embeddings
2. In-Memory Graph (NetworkX) - Graph relationships
3. Enhanced Manager Agent - Query classification & routing
4. Pipeline API - End-to-end query processing

Mundra Port (INMUN) - India's largest commercial port
- 36 berths across multiple terminals
- Container, Dry Bulk, Liquid Bulk, Multipurpose terminals
"""

import os
import sys
import csv
import json
from datetime import datetime

# Ensure ai-service is in path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

print("=" * 70)
print("SmartBerth AI - Mundra Port Data Learning Test")
print("=" * 70)
print()

# ============================================================================
# 1. LOAD MUNDRA PORT CSV DATA
# ============================================================================
print("1. LOADING MUNDRA PORT CSV DATA")
print("-" * 50)

# Use Test_Data folder which contains the Mundra BERTHS.csv
mundra_csv_path = os.path.join(script_dir, "Test_Data", "BERTHS.csv")
if not os.path.exists(mundra_csv_path):
    # Fallback to old path
    mundra_csv_path = os.path.join(script_dir, "..", "..", "mundra_port_berths_test_data.csv")
mundra_data = []

with open(mundra_csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        mundra_data.append(row)

print(f"   Loaded {len(mundra_data)} Mundra Port berths")

# Analyze berth types
berth_types = {}
terminals = {}
for berth in mundra_data:
    bt = berth.get('berthType', 'Unknown')
    berth_types[bt] = berth_types.get(bt, 0) + 1
    
    tid = berth.get('terminalId', 'Unknown')
    terminals[tid] = terminals.get(tid, 0) + 1

print(f"   Terminals: {len(terminals)}")
print(f"   Berth Types: {berth_types}")
print()

# ============================================================================
# 2. INJECT INTO KNOWLEDGE INDEX (ChromaDB)
# ============================================================================
print("2. INJECTING INTO KNOWLEDGE INDEX (ChromaDB)")
print("-" * 50)

try:
    import chromadb
    
    chroma_path = os.path.join(script_dir, "chroma_db_unified")
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_collection("smartberth_unified")
    
    print(f"   Existing chunks: {collection.count()}")
    
    # Create knowledge chunks for Mundra Port
    mundra_chunks = []
    
    # Port summary chunk
    mundra_summary = f"""Mundra Port (INMUN) - India's Largest Commercial Port

Location: Gujarat, India (Lat: 22.76, Long: 69.70)
Port Code: INMUN
Total Berths: {len(mundra_data)}
Terminals: {len(terminals)}

Terminal Breakdown:
"""
    for tid, count in sorted(terminals.items()):
        mundra_summary += f"- {tid}: {count} berths\n"
    
    mundra_summary += f"\nBerth Type Distribution:\n"
    for bt, count in sorted(berth_types.items()):
        mundra_summary += f"- {bt}: {count} berths\n"
    
    mundra_chunks.append({
        "id": "mundra_port_summary",
        "content": mundra_summary,
        "metadata": {
            "source": "mundra_port_berths_test_data.csv",
            "knowledge_type": "entity_profile",
            "entity_type": "port",
            "port_code": "INMUN"
        }
    })
    
    # Terminal-level chunks
    for tid in terminals:
        terminal_berths = [b for b in mundra_data if b.get('terminalId') == tid]
        
        # Get terminal name from first berth
        sample = terminal_berths[0]
        berth_name = sample.get('berthName', '')
        terminal_name = berth_name.split(' - ')[0] if ' - ' in berth_name else tid
        
        terminal_content = f"""Terminal: {terminal_name} ({tid})
Port: Mundra Port (INMUN)
Total Berths: {len(terminal_berths)}

Berth Details:
"""
        for b in terminal_berths:
            terminal_content += f"""
- {b.get('berthName')} ({b.get('berthCode')})
  Type: {b.get('berthType')}
  Length: {b.get('length')}m, Depth: {b.get('depth')}m, Max Draft: {b.get('maxDraft')}m
  Max LOA: {b.get('maxLOA')}m, Max Beam: {b.get('maxBeam')}m
  Cranes: {b.get('numberOfCranes')}, Bollards: {b.get('bollardCount')}
  Coordinates: ({b.get('latitude')}, {b.get('longitude')})
"""
        
        mundra_chunks.append({
            "id": f"mundra_terminal_{tid}",
            "content": terminal_content,
            "metadata": {
                "source": "mundra_port_berths_test_data.csv",
                "knowledge_type": "entity_profile",
                "entity_type": "terminal",
                "terminal_id": tid,
                "port_code": "INMUN"
            }
        })
    
    # Berth capability chunk (for allocation queries)
    capability_content = """Mundra Port Berth Capabilities for Vessel Allocation

Container Berths (Max Capacity):
"""
    container_berths = [b for b in mundra_data if b.get('berthType') == 'Container']
    for b in sorted(container_berths, key=lambda x: float(x.get('maxLOA', 0)), reverse=True)[:5]:
        capability_content += f"- {b.get('berthCode')}: LOA≤{b.get('maxLOA')}m, Draft≤{b.get('maxDraft')}m, Depth={b.get('depth')}m, Cranes={b.get('numberOfCranes')}\n"
    
    capability_content += "\nDry Bulk Berths (Max Capacity):\n"
    bulk_berths = [b for b in mundra_data if 'Bulk' in b.get('berthType', '')]
    for b in sorted(bulk_berths, key=lambda x: float(x.get('maxLOA', 0)), reverse=True)[:5]:
        capability_content += f"- {b.get('berthCode')}: LOA≤{b.get('maxLOA')}m, Draft≤{b.get('maxDraft')}m, Depth={b.get('depth')}m\n"
    
    capability_content += "\nLiquid Bulk Berths:\n"
    liquid_berths = [b for b in mundra_data if 'Liquid' in b.get('berthType', '')]
    for b in liquid_berths:
        capability_content += f"- {b.get('berthCode')}: LOA≤{b.get('maxLOA')}m, Draft≤{b.get('maxDraft')}m ({b.get('berthName')})\n"
    
    mundra_chunks.append({
        "id": "mundra_berth_capabilities",
        "content": capability_content,
        "metadata": {
            "source": "mundra_port_berths_test_data.csv",
            "knowledge_type": "operational_data",
            "entity_type": "berth_capabilities",
            "port_code": "INMUN"
        }
    })
    
    # Add chunks to ChromaDB
    ids = [c["id"] for c in mundra_chunks]
    documents = [c["content"] for c in mundra_chunks]
    metadatas = [c["metadata"] for c in mundra_chunks]
    
    # Delete existing Mundra chunks if any
    try:
        existing = collection.get(where={"port_code": "INMUN"})
        if existing and existing.get("ids"):
            collection.delete(ids=existing["ids"])
            print(f"   Deleted {len(existing['ids'])} existing Mundra chunks")
    except:
        pass
    
    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"   Added {len(mundra_chunks)} Mundra Port knowledge chunks")
    print(f"   Total chunks now: {collection.count()}")
    
except Exception as e:
    print(f"   ERROR: {e}")

print()

# ============================================================================
# 3. INJECT INTO IN-MEMORY GRAPH (NetworkX)
# ============================================================================
print("3. INJECTING INTO IN-MEMORY GRAPH (NetworkX)")
print("-" * 50)

try:
    from inmemory_graph import get_knowledge_graph
    
    graph = get_knowledge_graph()
    if graph.load():
        stats_before = graph.get_stats()
        print(f"   Before: {stats_before['total_nodes']} nodes, {stats_before['total_edges']} edges")
        
        # Add Mundra Port node
        mundra_port = {
            "portId": "PORT-MUN",
            "portCode": "INMUN",
            "portName": "Mundra Port",
            "country": "India",
            "latitude": 22.76,
            "longitude": 69.70,
            "totalBerths": len(mundra_data),
            "totalTerminals": len(terminals)
        }
        graph.graph.add_node(
            "PORT-MUN",
            node_type="Port",
            **mundra_port
        )
        
        # Add terminal nodes and edges
        for tid in terminals:
            terminal_berths = [b for b in mundra_data if b.get('terminalId') == tid]
            sample = terminal_berths[0]
            
            terminal_data = {
                "terminalId": tid,
                "portId": "PORT-MUN",
                "terminalName": sample.get('berthName', '').split(' - ')[0],
                "totalBerths": len(terminal_berths)
            }
            graph.graph.add_node(tid, node_type="Terminal", **terminal_data)
            graph.graph.add_edge("PORT-MUN", tid, relationship="HAS_TERMINAL")
        
        # Add berth nodes and edges
        for berth in mundra_data:
            berth_id = berth.get('berthId')
            berth_node = {
                "berthId": berth_id,
                "berthCode": berth.get('berthCode'),
                "berthName": berth.get('berthName'),
                "terminalId": berth.get('terminalId'),
                "portId": berth.get('portId'),
                "port_code": "INMUN",  # Add for queries
                "berth_name": berth.get('berthName'),  # Standard key
                "berth_type": berth.get('berthType'),  # Standard key
                "length": float(berth.get('length', 0)),
                "depth": float(berth.get('depth', 0)),
                "berth_depth": float(berth.get('depth', 0)),
                "maxDraft": float(berth.get('maxDraft', 0)),
                "max_draft": float(berth.get('maxDraft', 0)),
                "maxLOA": float(berth.get('maxLOA', 0)),
                "max_loa": float(berth.get('maxLOA', 0)),
                "maxBeam": float(berth.get('maxBeam', 0)),
                "berth_length": float(berth.get('length', 0)),
                "berthType": berth.get('berthType'),
                "numberOfCranes": int(berth.get('numberOfCranes', 0)),
                "bollardCount": int(berth.get('bollardCount', 0)),
                "latitude": float(berth.get('latitude', 0)),
                "longitude": float(berth.get('longitude', 0)),
                "isActive": berth.get('isActive', 'TRUE') == 'TRUE'
            }
            graph.graph.add_node(berth_id, node_type="Berth", **berth_node)
            graph.graph.add_edge(berth.get('terminalId'), berth_id, relationship="HAS_BERTH")
            
            # Update berth index for queries - store node_id (which is berth_id)
            graph._berth_index[berth_id] = berth_id
        
        # Update port index
        graph._port_index["INMUN"] = "PORT-MUN"
        
        # Update stats
        graph._update_stats()
        
        stats_after = graph.get_stats()
        print(f"   After: {stats_after['total_nodes']} nodes, {stats_after['total_edges']} edges")
        print(f"   Added: {stats_after['total_nodes'] - stats_before['total_nodes']} nodes, {stats_after['total_edges'] - stats_before['total_edges']} edges")
        
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# 4. TEST ENHANCED MANAGER AGENT
# ============================================================================
print("4. TESTING ENHANCED MANAGER AGENT")
print("-" * 50)

try:
    from manager_agent.enhanced_manager import get_enhanced_manager_agent
    
    manager = get_enhanced_manager_agent()
    if manager.is_ready():
        print("   Manager Agent: Ready")
        
        # Test Mundra-specific queries
        test_queries = [
            "Find berths at Mundra Port for container vessel with LOA 380m",
            "What terminals are available at INMUN?",
            "Show dry bulk berths at Mundra with depth > 18m",
            "Calculate UKC for vessel with 16m draft at CT4-CB1",
        ]
        
        print("\n   Query Classification Tests:")
        for query in test_queries:
            result = manager.process_query(query)
            task_type = result.get("task_type", "UNKNOWN")
            ctx = result.get("data_flow_context", {})
            phase = ctx.get("operational_phase", {})
            phase_name = phase.get("phase", "N/A") if isinstance(phase, dict) else phase
            
            print(f"   • \"{query[:45]}...\"")
            print(f"     → Phase: {phase_name}, Datasets: {len(ctx.get('datasets', []))} mapped")
        
except Exception as e:
    print(f"   ERROR: {e}")

print()

# ============================================================================
# 5. TEST PIPELINE END-TO-END
# ============================================================================
print("5. TESTING PIPELINE END-TO-END")
print("-" * 50)

try:
    from pipeline_api import get_pipeline, PipelineQueryRequest
    import asyncio
    
    pipeline = get_pipeline()
    if not pipeline._initialized:
        pipeline.initialize()
    
    async def test_mundra_queries():
        queries = [
            "Find suitable berths at Mundra Port for a container vessel with LOA 350m and draft 15m",
            "List all container terminals at INMUN port",
            "What is the deepest berth at Mundra Port?",
        ]
        
        results = []
        for query in queries:
            print(f"\n   Query: {query[:50]}...")
            
            request = PipelineQueryRequest(
                query=query,
                use_rag=True,
                use_graph=True,
                max_context_chunks=5
            )
            
            response = await pipeline.process_query(request)
            
            print(f"   Intent: {response.intent}")
            print(f"   Context chunks: {len(response.context_used)}")
            print(f"   Graph used: {response.graph_used}")
            print(f"   Answer preview: {response.answer[:150]}...")
            
            results.append({
                "query": query,
                "intent": response.intent,
                "context_count": len(response.context_used),
                "graph_used": response.graph_used,
                "latency_ms": response.latency_ms
            })
        
        return results
    
    results = asyncio.run(test_mundra_queries())
    
except Exception as e:
    print(f"   ERROR: {e}")
    import traceback
    traceback.print_exc()

print()

# ============================================================================
# 6. TEST KNOWLEDGE RETRIEVAL FOR MUNDRA
# ============================================================================
print("6. TESTING KNOWLEDGE RETRIEVAL FOR MUNDRA")
print("-" * 50)

try:
    # Query ChromaDB directly for Mundra content
    results = collection.query(
        query_texts=["Mundra Port container berth capabilities"],
        n_results=3,
        where={"port_code": "INMUN"}
    )
    
    if results and results.get("documents"):
        print(f"   Found {len(results['documents'][0])} relevant chunks")
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i]
            print(f"   {i+1}. [{meta.get('knowledge_type')}] {doc[:80]}...")
    else:
        print("   No Mundra-specific chunks found")

except Exception as e:
    print(f"   ERROR: {e}")

print()

# ============================================================================
# 7. TEST GRAPH QUERIES FOR MUNDRA
# ============================================================================
print("7. TESTING GRAPH QUERIES FOR MUNDRA")
print("-" * 50)

try:
    # Query graph for Mundra data
    if graph.is_loaded():
        # Find compatible berths
        compatible = graph.find_compatible_berths(
            vessel_type="Container",
            min_loa=350,
            min_depth=16
        )
        
        # Filter for Mundra
        mundra_compatible = [b for b in compatible if 'MUN' in b.get('berthId', '')]
        print(f"   Container berths (LOA≥350, Depth≥16): {len(mundra_compatible)} at Mundra")
        
        for b in mundra_compatible[:5]:
            print(f"   • {b.get('berthCode')}: LOA={b.get('maxLOA')}m, Depth={b.get('depth')}m")
        
        # Get Mundra port resources
        resources = graph.get_port_resources("INMUN")
        if resources:
            print(f"\n   Mundra Port Resources:")
            print(f"   • Terminals: {resources.get('terminal_count', 0)}")
            print(f"   • Berths: {resources.get('berth_count', 0)}")

except Exception as e:
    print(f"   ERROR: {e}")

print()
print("=" * 70)
print("✓ Mundra Port Data Learning Test Complete!")
print("=" * 70)
