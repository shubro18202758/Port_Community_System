"""
SmartBerth AI - External Port Data Loader
==========================================
Utility to load external port/berth data into the SmartBerth AI system.
Supports loading into:
1. Knowledge Index (ChromaDB)
2. In-Memory Graph (NetworkX)

Usage:
    from load_external_port import load_port_data
    load_port_data("path/to/port_data.csv")
"""

import os
import sys
import csv
import logging
from typing import List, Dict, Any, Optional

# Setup path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

logger = logging.getLogger(__name__)


def load_port_data(
    csv_path: str,
    port_code: str = None,
    port_name: str = None,
    load_to_knowledge: bool = True,
    load_to_graph: bool = True
) -> Dict[str, Any]:
    """
    Load external port/berth data into SmartBerth AI system.
    
    Args:
        csv_path: Path to CSV file with berth data
        port_code: Override port code (if not in CSV)
        port_name: Override port name (if not in CSV)
        load_to_knowledge: Whether to load to ChromaDB
        load_to_graph: Whether to load to NetworkX graph
        
    Returns:
        Dictionary with loading results
    """
    results = {
        "success": True,
        "csv_path": csv_path,
        "berths_loaded": 0,
        "terminals_found": 0,
        "knowledge_chunks": 0,
        "graph_nodes": 0,
        "graph_edges": 0,
        "errors": []
    }
    
    # Load CSV data
    if not os.path.exists(csv_path):
        results["success"] = False
        results["errors"].append(f"CSV file not found: {csv_path}")
        return results
    
    berths = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            berths.append(row)
    
    if not berths:
        results["success"] = False
        results["errors"].append("No berths found in CSV")
        return results
    
    results["berths_loaded"] = len(berths)
    
    # Determine port info
    sample = berths[0]
    actual_port_code = port_code or sample.get('portCode', 'UNKNOWN')
    actual_port_name = port_name or f"Port {actual_port_code}"
    
    # Analyze terminals
    terminals = {}
    berth_types = {}
    for berth in berths:
        tid = berth.get('terminalId', 'UNKNOWN')
        terminals[tid] = terminals.get(tid, 0) + 1
        
        bt = berth.get('berthType', 'Unknown')
        berth_types[bt] = berth_types.get(bt, 0) + 1
    
    results["terminals_found"] = len(terminals)
    
    # Load to Knowledge Index
    if load_to_knowledge:
        try:
            import chromadb
            
            chroma_path = os.path.join(script_dir, "chroma_db_unified")
            client = chromadb.PersistentClient(path=chroma_path)
            collection = client.get_collection("smartberth_unified")
            
            chunks = []
            
            # Port summary
            summary = f"""{actual_port_name} ({actual_port_code})

Total Berths: {len(berths)}
Terminals: {len(terminals)}

Terminal Distribution:
"""
            for tid, count in sorted(terminals.items()):
                summary += f"- {tid}: {count} berths\n"
            
            summary += f"\nBerth Types:\n"
            for bt, count in sorted(berth_types.items()):
                summary += f"- {bt}: {count}\n"
            
            chunks.append({
                "id": f"{actual_port_code.lower()}_summary",
                "content": summary,
                "metadata": {
                    "source": os.path.basename(csv_path),
                    "knowledge_type": "entity_profile",
                    "entity_type": "port",
                    "port_code": actual_port_code
                }
            })
            
            # Terminal chunks
            for tid in terminals:
                terminal_berths = [b for b in berths if b.get('terminalId') == tid]
                sample = terminal_berths[0]
                
                content = f"""Terminal: {tid}
Port: {actual_port_name} ({actual_port_code})
Total Berths: {len(terminal_berths)}

Berths:
"""
                for b in terminal_berths:
                    content += f"""- {b.get('berthName', b.get('berthCode', 'Unknown'))}
  Type: {b.get('berthType', 'Unknown')}
  Length: {b.get('length', 'N/A')}m, Depth: {b.get('depth', 'N/A')}m
  Max LOA: {b.get('maxLOA', 'N/A')}m, Max Draft: {b.get('maxDraft', 'N/A')}m
"""
                
                chunks.append({
                    "id": f"{actual_port_code.lower()}_{tid.lower()}",
                    "content": content,
                    "metadata": {
                        "source": os.path.basename(csv_path),
                        "knowledge_type": "entity_profile",
                        "entity_type": "terminal",
                        "terminal_id": tid,
                        "port_code": actual_port_code
                    }
                })
            
            # Delete existing chunks for this port
            try:
                existing = collection.get(where={"port_code": actual_port_code})
                if existing and existing.get("ids"):
                    collection.delete(ids=existing["ids"])
            except:
                pass
            
            # Add new chunks
            collection.add(
                ids=[c["id"] for c in chunks],
                documents=[c["content"] for c in chunks],
                metadatas=[c["metadata"] for c in chunks]
            )
            
            results["knowledge_chunks"] = len(chunks)
            
        except Exception as e:
            results["errors"].append(f"Knowledge index error: {e}")
    
    # Load to Graph
    if load_to_graph:
        try:
            from inmemory_graph import get_knowledge_graph
            
            graph = get_knowledge_graph()
            if graph.load():
                port_node_id = f"PORT-{actual_port_code}"
                
                # Add port node
                graph.graph.add_node(
                    port_node_id,
                    node_type="Port",
                    portId=port_node_id,
                    portCode=actual_port_code,
                    portName=actual_port_name,
                    totalBerths=len(berths),
                    totalTerminals=len(terminals)
                )
                nodes_added = 1
                edges_added = 0
                
                # Add terminals
                for tid in terminals:
                    terminal_berths = [b for b in berths if b.get('terminalId') == tid]
                    
                    graph.graph.add_node(
                        tid,
                        node_type="Terminal",
                        terminalId=tid,
                        portId=port_node_id,
                        totalBerths=len(terminal_berths)
                    )
                    graph.graph.add_edge(port_node_id, tid, relationship="HAS_TERMINAL")
                    nodes_added += 1
                    edges_added += 1
                
                # Add berths
                for berth in berths:
                    berth_id = berth.get('berthId', berth.get('berthCode'))
                    
                    graph.graph.add_node(
                        berth_id,
                        node_type="Berth",
                        berthId=berth_id,
                        berthCode=berth.get('berthCode'),
                        berthName=berth.get('berthName'),
                        port_code=actual_port_code,
                        berth_type=berth.get('berthType'),
                        berth_name=berth.get('berthName'),
                        max_loa=float(berth.get('maxLOA', 0) or 0),
                        max_draft=float(berth.get('maxDraft', 0) or 0),
                        berth_depth=float(berth.get('depth', 0) or 0),
                        berth_length=float(berth.get('length', 0) or 0)
                    )
                    
                    tid = berth.get('terminalId')
                    graph.graph.add_edge(tid, berth_id, relationship="HAS_BERTH")
                    
                    # Update index
                    graph._berth_index[berth_id] = berth_id
                    
                    nodes_added += 1
                    edges_added += 1
                
                # Update port index
                graph._port_index[actual_port_code] = port_node_id
                graph._update_stats()
                
                results["graph_nodes"] = nodes_added
                results["graph_edges"] = edges_added
                
        except Exception as e:
            results["errors"].append(f"Graph loading error: {e}")
    
    return results


if __name__ == "__main__":
    # Test with Mundra port data
    mundra_csv = os.path.join(script_dir, "..", "..", "mundra_port_berths_test_data.csv")
    
    print("Loading Mundra Port data...")
    result = load_port_data(
        mundra_csv,
        port_name="Mundra Port"
    )
    
    print(f"Success: {result['success']}")
    print(f"Berths loaded: {result['berths_loaded']}")
    print(f"Terminals: {result['terminals_found']}")
    print(f"Knowledge chunks: {result['knowledge_chunks']}")
    print(f"Graph nodes: {result['graph_nodes']}")
    print(f"Graph edges: {result['graph_edges']}")
    
    if result['errors']:
        print(f"Errors: {result['errors']}")
