#!/usr/bin/env python3
"""Show vessel data from the in-memory graph"""

from inmemory_graph import get_knowledge_graph
import sys

g = get_knowledge_graph()
g.load()

# Check for filter argument
filter_type = sys.argv[1] if len(sys.argv) > 1 else None

if filter_type and filter_type.lower() == 'feeder':
    # Show only Feeder Container vessels
    print('FEEDER CONTAINER VESSELS')
    print('=' * 120)
    header = f'{"#":>3} {"IMO":<12} {"Vessel Name":<30} {"LOA(m)":>8} {"Beam(m)":>8} {"Draft(m)":>9} {"DWT":>10}'
    print(header)
    print('-' * 120)
    
    count = 0
    for imo, node_id in g._vessel_index.items():
        data = g.graph.nodes[node_id]
        vtype = data.get('vessel_type', '')
        if 'Feeder' in vtype:
            count += 1
            name = data.get('vessel_name', 'N/A')[:28]
            loa = data.get('loa', 0)
            beam = data.get('beam', 0)
            draft = data.get('draft', 0)
            dwt = data.get('dwt', 0)
            print(f'{count:3} {imo:<12} {name:<30} {loa:>8.1f} {beam:>8.1f} {draft:>9.1f} {dwt:>10.0f}')
    
    print('-' * 120)
    print(f'Total Feeder Container Vessels: {count}')

else:
    # Show all vessels summary
    vessel_count = len([k for k in g._vessel_index.keys()])
    print(f'Total Vessels in Index: {vessel_count}')
    
    print(f'\nSample Vessel Data (first 25):')
    print('-' * 110)
    print(f'{"#":3} {"IMO":12} {"Vessel Name":28} {"Type":18} {"LOA (m)":10} {"Draft (m)":10}')
    print('-' * 110)
    
    count = 0
    for imo, node_id in list(g._vessel_index.items())[:25]:
        data = g.graph.nodes[node_id]
        name = data.get("vessel_name", "N/A")[:26]
        vtype = data.get("vessel_type", "N/A")[:16]
        loa = data.get("loa", 0)
        draft = data.get("draft", 0)
        print(f'{count+1:3} {imo:12} {name:28} {vtype:18} {loa:10.1f} {draft:10.1f}')
        count += 1
    
    print('-' * 110)
    
    print(f'\nVessel Types Distribution:')
    print('-' * 40)
    type_counts = {}
    for node_id in g._vessel_index.values():
        vtype = g.graph.nodes[node_id].get('vessel_type', 'Unknown')
        type_counts[vtype] = type_counts.get(vtype, 0) + 1
    
    for vtype, cnt in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f'  {vtype:25}: {cnt:5} vessels')
    
    print('-' * 40)
    print(f'  {"TOTAL":25}: {sum(type_counts.values()):5} vessels')
    print(f'\nUsage: python show_vessels.py [feeder]')
