#!/usr/bin/env python3
from inmemory_graph import get_knowledge_graph

g = get_knowledge_graph()
if not g.load():
    print('Failed to load graph')
    exit(1)

channels = [(nid, g.graph.nodes[nid]) for nid in g.graph.nodes if g.graph.nodes[nid].get('node_type') == 'CHANNEL']
print(f'Total Channels: {len(channels)}')
print('='*120)

if channels:
    for i, (nid, data) in enumerate(channels[:60], start=1):
        cid = data.get('channel_id') or data.get('id') or nid
        name = data.get('channel_name') or data.get('name') or ''
        depth = data.get('channel_depth') or data.get('depth') or 0
        max_loa = data.get('max_vessel_loa') or data.get('max_loa') or ''
        direction = data.get('direction') or data.get('navigation_direction') or ''
        print(f"{i:2}. ID: {cid} | Name: {name} | Depth: {depth} | Max LOA: {max_loa} | Dir: {direction}")
else:
    print('No channel nodes found.')
