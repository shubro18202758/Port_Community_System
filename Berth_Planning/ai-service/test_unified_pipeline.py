"""
Test Pipeline with Unified Training Data
"""
import asyncio
from pipeline_api import UnifiedSmartBerthPipeline, PipelineQueryRequest

print('='*70)
print('TESTING PIPELINE WITH UNIFIED TRAINING DATA')
print('='*70)

# Initialize pipeline
print('\nInitializing pipeline...')
pipeline = UnifiedSmartBerthPipeline()
pipeline.initialize()

# Get stats
stats = pipeline.get_stats()
print('\nPipeline Components:')
for comp, status in stats['components'].items():
    print(f'  {comp}: {status}')

ki = stats.get('knowledge_index', {})
ge = stats.get('graph_engine', {})
print(f"\nKnowledge Index: {ki.get('collection', 'N/A')} - {ki.get('count', 0)} chunks")
print(f"Graph Engine: {ge.get('status', 'N/A')} - {ge.get('nodes', 0)} nodes, {ge.get('edges', 0)} edges")

# Test queries
print('\n' + '='*70)
print('TESTING AI QUERIES WITH MUNDRA + GLOBAL DATA')
print('='*70)

async def test_query(q):
    request = PipelineQueryRequest(query=q, use_graph=True, max_results=3)
    response = await pipeline.process_query(request)
    return response

queries = [
    'What container terminals are available at Mundra Port?',
    'Show me berth CT1-01 details at Mundra',
    'What are the UKC requirements for deep draft vessels?',
    'List pilots available in the SmartBerth network',
    'What is the tidal pattern at Mundra Port?'
]

for q in queries:
    print(f'\n{"="*60}')
    print(f'Q: {q}')
    print('='*60)
    resp = asyncio.run(test_query(q))
    print(f'Intent: {resp.intent}')
    print(f'Graph Used: {resp.graph_used}')
    print(f'Context Chunks: {len(resp.context_used)}')
    
    # Show sources
    if resp.context_used:
        print('Top sources:')
        for i, ctx in enumerate(resp.context_used[:3]):
            print(f'  [{i+1}] {ctx.source} (score: {ctx.score:.2f})')
    
    print(f'\nAnswer:\n{resp.answer[:400]}...' if len(resp.answer) > 400 else f'\nAnswer:\n{resp.answer}')

print('\n' + '='*70)
print('PIPELINE TEST COMPLETE!')
print('='*70)
