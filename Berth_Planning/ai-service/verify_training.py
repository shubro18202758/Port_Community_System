"""
Verify Unified Training Results
"""
import chromadb

print('='*70)
print('VERIFYING UNIFIED TRAINING - CHROMADB')
print('='*70)

client = chromadb.PersistentClient(path='chroma_db_unified')
collection = client.get_collection('smartberth_unified')

print(f'\nTotal chunks indexed: {collection.count()}')

# Check data source distribution
all_docs = collection.get(limit=2200)
sources = {}
data_sources = {}
knowledge_types = {}

for meta in all_docs['metadatas']:
    src = meta.get('source', 'unknown')
    dsrc = meta.get('data_source', 'unknown')
    kt = meta.get('knowledge_type', 'unknown')
    sources[src] = sources.get(src, 0) + 1
    data_sources[dsrc] = data_sources.get(dsrc, 0) + 1
    knowledge_types[kt] = knowledge_types.get(kt, 0) + 1

print('\n📊 Data Source Distribution:')
for ds, count in sorted(data_sources.items(), key=lambda x: -x[1]):
    print(f'  {ds}: {count} chunks')

print('\n📈 Knowledge Types:')
for kt, count in sorted(knowledge_types.items(), key=lambda x: -x[1]):
    print(f'  {kt}: {count}')

print('\n📁 Top Sources:')
for src, count in sorted(sources.items(), key=lambda x: -x[1])[:15]:
    print(f'  {src}: {count}')

# Test Mundra queries
print('\n' + '='*70)
print('TESTING QUERIES')
print('='*70)

print('\n🔍 Query 1: "Mundra port berth allocation container terminal"')
results = collection.query(
    query_texts=['Mundra port berth allocation container terminal'],
    n_results=3
)
for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    src = meta.get('source', 'unknown')
    ds = meta.get('data_source', 'unknown')
    print(f'  [{i+1}] {src} ({ds})')
    print(f'      {doc[:120]}...\n')

# Test global queries
print('\n🔍 Query 2: "UKC calculation vessel draft safety"')
results2 = collection.query(
    query_texts=['UKC calculation vessel draft safety'],
    n_results=3
)
for i, (doc, meta) in enumerate(zip(results2['documents'][0], results2['metadatas'][0])):
    src = meta.get('source', 'unknown')
    ds = meta.get('data_source', 'unknown')
    print(f'  [{i+1}] {src} ({ds})')
    print(f'      {doc[:120]}...\n')

# Test vessel queries
print('\n🔍 Query 3: "vessel schedule terminal cargo type"')
results3 = collection.query(
    query_texts=['vessel schedule terminal cargo type'],
    n_results=3
)
for i, (doc, meta) in enumerate(zip(results3['documents'][0], results3['metadatas'][0])):
    src = meta.get('source', 'unknown')
    ds = meta.get('data_source', 'unknown')
    print(f'  [{i+1}] {src} ({ds})')
    print(f'      {doc[:120]}...\n')

print('='*70)
print('✅ Verification Complete!')
print('='*70)
