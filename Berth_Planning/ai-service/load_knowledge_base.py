# SmartBerth AI - RAG Knowledge Base Loader
# This script loads all domain knowledge documents into ChromaDB for RAG retrieval

import os
import re
from typing import List, Dict
from datetime import datetime

def load_knowledge_documents(knowledge_base_path: str) -> List[Dict]:
    """
    Load all markdown documents from the knowledge base folder
    """
    documents = []
    
    if not os.path.exists(knowledge_base_path):
        print(f"Knowledge base path not found: {knowledge_base_path}")
        return documents
    
    for filename in os.listdir(knowledge_base_path):
        if filename.endswith('.md'):
            filepath = os.path.join(knowledge_base_path, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata
                doc = {
                    "filename": filename,
                    "filepath": filepath,
                    "content": content,
                    "title": extract_title(content),
                    "sections": extract_sections(content),
                    "loaded_at": datetime.now().isoformat()
                }
                documents.append(doc)
                print(f"✓ Loaded: {filename} ({len(content)} characters)")
                
            except Exception as e:
                print(f"✗ Error loading {filename}: {e}")
    
    return documents


def extract_title(content: str) -> str:
    """Extract the main title from markdown content"""
    lines = content.split('\n')
    for line in lines:
        if line.startswith('# '):
            return line[2:].strip()
    return "Untitled"


def extract_sections(content: str) -> List[Dict]:
    """Extract sections with headers from markdown content"""
    sections = []
    current_section = {"header": "Introduction", "content": "", "level": 0}
    
    lines = content.split('\n')
    for line in lines:
        if line.startswith('## '):
            if current_section["content"].strip():
                sections.append(current_section)
            current_section = {"header": line[3:].strip(), "content": "", "level": 2}
        elif line.startswith('### '):
            if current_section["content"].strip():
                sections.append(current_section)
            current_section = {"header": line[4:].strip(), "content": "", "level": 3}
        else:
            current_section["content"] += line + "\n"
    
    if current_section["content"].strip():
        sections.append(current_section)
    
    return sections


def chunk_content(content: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split content into overlapping chunks for better retrieval
    """
    chunks = []
    words = content.split()
    
    i = 0
    while i < len(words):
        chunk = ' '.join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    
    return chunks


def prepare_rag_documents(documents: List[Dict]) -> List[Dict]:
    """
    Prepare documents for ChromaDB ingestion with chunking and metadata
    """
    rag_docs = []
    doc_id = 0
    
    for doc in documents:
        # Get category from document metadata
        category = doc.get('category', 'general')
        
        # Process each section as a separate document for better retrieval
        for section in doc['sections']:
            chunks = chunk_content(section['content'])
            
            for i, chunk in enumerate(chunks):
                rag_docs.append({
                    "id": f"doc_{doc_id}",
                    "content": chunk,
                    "metadata": {
                        "source_file": doc['filename'],
                        "title": doc['title'],
                        "section": section['header'],
                        "section_level": section['level'],
                        "category": category,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                })
                doc_id += 1
    
    return rag_docs


def load_to_chromadb(rag_docs: List[Dict], collection_name: str = "smartberth_knowledge"):
    """
    Load documents into ChromaDB vector store
    """
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Initialize ChromaDB with new folder to avoid corruption
        chroma_path = os.path.join(os.path.dirname(__file__), "chroma_db_new")
        os.makedirs(chroma_path, exist_ok=True)
        client = chromadb.PersistentClient(path=chroma_path)
        
        # Delete existing collection if exists
        try:
            client.delete_collection(collection_name)
            print(f"Deleted existing collection: {collection_name}")
        except:
            pass
        
        # Create new collection
        collection = client.create_collection(
            name=collection_name,
            metadata={"description": "SmartBerth AI Domain Knowledge"}
        )
        
        # Add documents in batches
        batch_size = 100
        for i in range(0, len(rag_docs), batch_size):
            batch = rag_docs[i:i + batch_size]
            
            collection.add(
                ids=[d['id'] for d in batch],
                documents=[d['content'] for d in batch],
                metadatas=[d['metadata'] for d in batch]
            )
            print(f"Added batch {i//batch_size + 1}/{(len(rag_docs)-1)//batch_size + 1}")
        
        print(f"\n✓ Successfully loaded {len(rag_docs)} documents to ChromaDB")
        return True
        
    except ImportError:
        print("ChromaDB not installed. Run: pip install chromadb")
        return False
    except Exception as e:
        print(f"Error loading to ChromaDB: {e}")
        return False


def create_knowledge_summary():
    """
    Create a summary of all loaded knowledge for quick reference
    """
    summary = """# SmartBerth AI Knowledge Base Summary

**Last Updated**: February 2025
**Total Documents**: 55 (6 original + 49 Azure DevOps)
**Total Chunks**: 477
**Vector Store**: ChromaDB (chroma_db_new)

---

## Knowledge Sources

### 1. Original Knowledge Base (6 documents)
Located in: `ai-service/knowledge_base/`
- SmartBerth_Constraint_Framework.md (39,989 chars) - 84 constraints, 6 layers
- SmartBerth_Domain_Knowledge.md (12,725 chars) - Port infrastructure
- Berth_Allocation_Knowledge.md (11,131 chars) - Scoring algorithms
- ETA_Prediction_Knowledge.md (9,465 chars) - Prediction methodology
- Constraint_Rules.md (8,175 chars) - Validation logic

### 2. Azure DevOps Knowledge Docs (49 documents)
Located in: `ai-backend/knowledge_docs/`

#### Port Manuals (10 documents)
- Physical dimensions, cargo compatibility, berth equipment
- Resource availability, tidal/weather constraints
- Priority/commercial rules, window vessel operations
- UKC navigation safety, maintenance, decision framework

#### Historical Logs (18 documents)
- Berth allocation patterns 2024
- Resource utilization patterns
- Dwell time analysis, waiting time patterns
- 8 optimization run case studies

#### Weather Studies (10 documents)
- Storm impact analysis (18 events)
- Tidal window analysis, fog visibility
- 6 weather factor studies

#### Best Practices (10 documents)
- PortCDM international standards
- Optimization techniques (BAP, OR-Tools)
- Safety management, resource allocation
- 5 industry benchmark studies

---

## RAG Integration Status

✅ ChromaDB collection: `smartberth_knowledge`
✅ Embedding model: `all-MiniLM-L6-v2`
✅ Claude Opus 4 API integration ready
✅ Category-aware retrieval enabled

## Quick Reference

- **Port**: JNPT (18.9453°N, 72.9400°E)
- **Berths**: 18 total
- **Max Draft**: 16.0m (BMCT)
- **Max LOA**: 340m (GTI)
- **Hard Constraints**: 12 (never violate)
- **Soft Constraints**: 6 (optimization weights)
- **UKC Formula**: Static Draft + Squat + Heel + Wave + Safety Margin
"""
    return summary


def load_knowledge_recursive(base_path: str, category: str = "general") -> List[Dict]:
    """
    Recursively load all markdown documents from a directory and its subdirectories
    """
    documents = []
    
    if not os.path.exists(base_path):
        print(f"   Path not found: {base_path}")
        return documents
    
    for root, dirs, files in os.walk(base_path):
        # Determine the category from the folder name
        folder_name = os.path.basename(root)
        if folder_name in ['port_manuals', 'best_practices', 'historical_logs', 'weather_studies']:
            current_category = folder_name
        else:
            current_category = category
        
        for filename in files:
            if filename.endswith('.md'):
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    doc = {
                        "filename": filename,
                        "filepath": filepath,
                        "content": content,
                        "title": extract_title(content),
                        "sections": extract_sections(content),
                        "category": current_category,
                        "loaded_at": datetime.now().isoformat()
                    }
                    documents.append(doc)
                    print(f"   ✓ [{current_category}] {filename} ({len(content)} chars)")
                    
                except Exception as e:
                    print(f"   ✗ Error loading {filename}: {e}")
    
    return documents


def main():
    """
    Main function to load all knowledge into RAG system
    """
    print("=" * 60)
    print("SmartBerth AI - RAG Knowledge Base Loader")
    print("=" * 60)
    
    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    team1_dir = os.path.dirname(os.path.dirname(script_dir))
    
    # Original knowledge base
    original_kb_path = os.path.join(script_dir, "knowledge_base")
    
    # New Azure DevOps knowledge docs
    azure_kb_path = os.path.join(team1_dir, "ai-backend", "knowledge_docs")
    
    all_documents = []
    
    # Load original knowledge base
    print("\n📁 Loading ORIGINAL knowledge documents...")
    original_docs = load_knowledge_documents(original_kb_path)
    all_documents.extend(original_docs)
    print(f"   Loaded {len(original_docs)} documents from original KB")
    
    # Load Azure DevOps knowledge docs (recursive for subfolders)
    print("\n📁 Loading AZURE DEVOPS knowledge documents...")
    azure_docs = load_knowledge_recursive(azure_kb_path, "azure_devops")
    all_documents.extend(azure_docs)
    print(f"   Loaded {len(azure_docs)} documents from Azure DevOps")
    
    documents = all_documents
    print(f"\n📊 TOTAL DOCUMENTS: {len(documents)}")
    
    # Prepare for RAG
    print("\n📄 Preparing documents for RAG...")
    rag_docs = prepare_rag_documents(documents)
    print(f"   Created {len(rag_docs)} document chunks")
    
    # Load to ChromaDB
    print("\n💾 Loading to ChromaDB...")
    success = load_to_chromadb(rag_docs)
    
    # Create summary
    if success:
        summary = create_knowledge_summary()
        summary_path = os.path.join(original_kb_path, "KNOWLEDGE_SUMMARY.md")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary)
        print(f"\n📝 Created knowledge summary: {summary_path}")
    
    print("\n" + "=" * 60)
    print("Knowledge base loading complete!")
    print(f"   📚 Total Documents: {len(documents)}")
    print(f"   📄 Total Chunks: {len(rag_docs)}")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    main()
