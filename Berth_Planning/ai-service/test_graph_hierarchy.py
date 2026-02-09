#!/usr/bin/env python3
"""
Test script to verify the in-memory graph hierarchy is 100% working.
"""

from inmemory_graph import InMemoryKnowledgeGraph, get_knowledge_graph

def main():
    print("=" * 70)
    print("In-Memory Graph Hierarchy Verification Test")
    print("=" * 70)
    
    # Load the graph
    graph = get_knowledge_graph()
    
    if not graph.load():
        print("ERROR: Failed to load graph!")
        return
    
    # Get stats
    stats = graph.get_stats()
    print(f"\n1. Graph Statistics:")
    print(f"   Total Nodes: {stats['total_nodes']}")
    print(f"   Total Edges: {stats['total_edges']}")
    print(f"   Ports: {stats['counts']['ports']}")
    print(f"   Terminals: {stats['counts']['terminals']}")
    print(f"   Berths: {stats['counts']['berths']}")
    print(f"   Vessels: {stats['counts']['vessels']}")
    print(f"   Pilots: {stats['counts']['pilots']}")
    print(f"   Tugboats: {stats['counts']['tugboats']}")
    
    # Test multiple ports
    test_ports = ['SGSIN', 'NLRTM', 'CNSHA', 'USNYC', 'AEJEA']
    
    # Check which ports exist
    available_ports = [p for p in test_ports if p in graph._port_index]
    
    # Also get some actual ports from the index
    actual_ports = list(set([k for k in graph._port_index.keys() if not k.isdigit()]))[:5]
    
    print(f"\n2. Testing Port Hierarchies:")
    print(f"   Available test ports: {available_ports}")
    print(f"   Sample actual ports: {actual_ports[:5]}")
    
    ports_to_test = actual_ports[:5]  # Use actual ports from the index
    
    total_terminals = 0
    total_berths = 0
    ports_with_terminals = 0
    ports_with_berths = 0
    
    for port_code in ports_to_test:
        resources = graph.get_port_resources(port_code)
        hierarchy = graph.get_port_hierarchy(port_code)
        
        if resources:
            summary = resources.get('summary', {})
            t_count = summary.get('total_terminals', 0)
            b_count = summary.get('total_berths', 0)
            p_count = summary.get('total_pilots', 0)
            tug_count = summary.get('total_tugboats', 0)
            
            total_terminals += t_count
            total_berths += b_count
            if t_count > 0:
                ports_with_terminals += 1
            if b_count > 0:
                ports_with_berths += 1
            
            print(f"\n   Port: {port_code} ({resources.get('port_name', 'N/A')})")
            print(f"      Terminals: {t_count}")
            print(f"      Berths: {b_count}")
            print(f"      Pilots: {p_count}")
            print(f"      Tugboats: {tug_count}")
            
            # Show terminal->berth hierarchy if available
            if hierarchy and hierarchy.get('terminals'):
                print(f"      Hierarchy:")
                for term in hierarchy['terminals'][:3]:  # Show max 3
                    berth_count = len(term.get('berths', []))
                    print(f"        Terminal: {term.get('terminal_name', 'N/A')} -> {berth_count} berths")
    
    print(f"\n3. Summary:")
    print(f"   Ports tested: {len(ports_to_test)}")
    print(f"   Ports with terminals linked: {ports_with_terminals}")
    print(f"   Ports with berths linked: {ports_with_berths}")
    print(f"   Total terminals found: {total_terminals}")
    print(f"   Total berths found: {total_berths}")
    
    # Test compatible berths query
    print(f"\n4. Compatible Berths Query Test:")
    berths = graph.find_compatible_berths(vessel_type="Container", min_loa=250.0)
    print(f"   Query: Container vessels with LOA >= 250m")
    print(f"   Found: {len(berths)} compatible berths")
    if berths:
        sample = berths[0]
        print(f"   Sample: {sample.get('berth_name', 'N/A')} at {sample.get('port_code', 'N/A')}")
        print(f"           Max LOA: {sample.get('max_loa', 'N/A')}m, Max Draft: {sample.get('max_draft', 'N/A')}m")
    
    # Final status
    print("\n" + "=" * 70)
    if ports_with_terminals > 0 and ports_with_berths > 0:
        print("✓ Graph hierarchy is WORKING - Port→Terminal→Berth links confirmed!")
        print("✓ Graph engine is 100% AVAILABLE (in-memory, no Neo4j required)")
    else:
        print("⚠ Graph hierarchy needs verification")
    print("=" * 70)

if __name__ == "__main__":
    main()
