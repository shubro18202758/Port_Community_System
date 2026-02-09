"""
Document Loader for Berth Planning Knowledge Base
Loads markdown documents, chunks them, generates embeddings, and stores in ChromaDB
"""

import os
import glob
from typing import List, Dict, Any
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import re


class DocumentLoader:
    """
    Loads knowledge documents and stores them in ChromaDB with embeddings
    """

    def __init__(
        self,
        docs_dir: str = "../knowledge_docs",
        chroma_persist_dir: str = "./chroma_db",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        self.docs_dir = docs_dir
        self.chroma_persist_dir = chroma_persist_dir
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize sentence transformer model
        print(f"Loading embedding model: {embedding_model}...")
        self.embedding_model = SentenceTransformer(embedding_model)
        print(f"Embedding model loaded. Dimension: {self.embedding_model.get_sentence_embedding_dimension()}")

        # Initialize ChromaDB client
        print(f"Initializing ChromaDB at {chroma_persist_dir}...")
        self.chroma_client = chromadb.PersistentClient(path=chroma_persist_dir)

        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="berth_knowledge",
            metadata={"description": "Berth Planning Knowledge Base for RAG"}
        )
        print(f"ChromaDB collection 'berth_knowledge' ready. Current size: {self.collection.count()}")

    def load_all_documents(self) -> List[Dict[str, Any]]:
        """
        Load all markdown documents from knowledge_docs directory
        """
        documents = []

        # Find all markdown files
        pattern = os.path.join(self.docs_dir, "**/*.md")
        md_files = glob.glob(pattern, recursive=True)

        print(f"\nFound {len(md_files)} markdown files")

        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Extract document metadata
                filename = os.path.basename(file_path)
                relative_path = os.path.relpath(file_path, self.docs_dir)
                category = self._extract_category(relative_path)
                source_tables = self._extract_source_tables(content)

                documents.append({
                    "filename": filename,
                    "filepath": file_path,
                    "relative_path": relative_path,
                    "category": category,
                    "content": content,
                    "source_tables": source_tables,
                    "size_bytes": len(content.encode('utf-8'))
                })

                print(f"  Loaded: {relative_path} ({len(content)} chars)")

            except Exception as e:
                print(f"  ERROR loading {file_path}: {e}")

        print(f"\nSuccessfully loaded {len(documents)} documents")
        return documents

    def _extract_category(self, relative_path: str) -> str:
        """
        Extract document category from file path
        """
        if "port_manuals" in relative_path:
            return "Port Manual"
        elif "historical_logs" in relative_path:
            return "Historical Log"
        elif "weather_studies" in relative_path:
            return "Weather Study"
        elif "best_practices" in relative_path:
            return "Best Practice"
        else:
            return "General"

    def _extract_source_tables(self, content: str) -> List[str]:
        """
        Extract database table names referenced in document
        """
        tables = set()

        # Common table patterns
        table_patterns = [
            r'VESSELS?',
            r'BERTHS?',
            r'VESSEL_SCHEDULE',
            r'RESOURCES?',
            r'RESOURCE_ALLOCATION',
            r'WEATHER_DATA',
            r'TIDAL_DATA',
            r'AIS_DATA',
            r'CONFLICTS?',
            r'OPTIMIZATION_RUNS?',
            r'KNOWLEDGE_BASE',
            r'VESSEL_HISTORY',
            r'BERTH_MAINTENANCE',
            r'ALERTS_NOTIFICATIONS'
        ]

        for pattern in table_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Normalize to uppercase
                tables.add(pattern.replace('?', '').replace(r'\b', '').upper())

        return sorted(list(tables))

    def chunk_document(self, content: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split document into chunks with overlap
        """
        chunks = []

        # Simple character-based chunking (approximation of token count)
        # Assuming ~4 chars per token, 500 tokens ≈ 2000 characters
        char_chunk_size = self.chunk_size * 4
        char_overlap = self.chunk_overlap * 4

        # Split by paragraphs first (preserve context)
        paragraphs = content.split('\n\n')

        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            # If adding this paragraph exceeds chunk size
            if len(current_chunk) + len(para) > char_chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": {
                        **metadata,
                        "chunk_index": chunk_index,
                        "char_count": len(current_chunk)
                    }
                })

                # Start new chunk with overlap (last N chars of previous chunk)
                current_chunk = current_chunk[-char_overlap:] + "\n\n" + para
                chunk_index += 1
            else:
                # Add paragraph to current chunk
                current_chunk += "\n\n" + para if current_chunk else para

        # Add final chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "metadata": {
                    **metadata,
                    "chunk_index": chunk_index,
                    "char_count": len(current_chunk)
                }
            })

        return chunks

    def embed_and_store(self, documents: List[Dict[str, Any]]) -> int:
        """
        Chunk documents, generate embeddings, and store in ChromaDB
        """
        all_chunks = []
        all_embeddings = []
        all_metadatas = []
        all_ids = []

        chunk_id = 0

        print("\nChunking documents...")
        for doc in documents:
            metadata_base = {
                "document_name": doc["filename"],
                "document_type": doc["category"],
                "relative_path": doc["relative_path"],
                "source_tables": ",".join(doc["source_tables"]),
                "created_at": datetime.now().isoformat()
            }

            chunks = self.chunk_document(doc["content"], metadata_base)

            print(f"  {doc['filename']}: {len(chunks)} chunks")

            for chunk in chunks:
                all_chunks.append(chunk["content"])
                all_metadatas.append(chunk["metadata"])
                all_ids.append(f"chunk_{chunk_id}")
                chunk_id += 1

        print(f"\nTotal chunks created: {len(all_chunks)}")

        print("\nGenerating embeddings...")
        # Generate embeddings in batches for efficiency
        batch_size = 32
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i:i + batch_size]
            batch_embeddings = self.embedding_model.encode(
                batch_chunks,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            all_embeddings.extend(batch_embeddings.tolist())

            print(f"  Embedded {min(i + batch_size, len(all_chunks))}/{len(all_chunks)} chunks")

        print(f"\nStoring in ChromaDB...")
        # Store in ChromaDB
        self.collection.add(
            documents=all_chunks,
            embeddings=all_embeddings,
            metadatas=all_metadatas,
            ids=all_ids
        )

        print(f"✓ Successfully stored {len(all_chunks)} chunks in ChromaDB")
        print(f"Collection size: {self.collection.count()}")

        return len(all_chunks)

    def clear_collection(self):
        """
        Clear all data from collection (for re-indexing)
        """
        print("Clearing collection...")
        self.chroma_client.delete_collection(name="berth_knowledge")
        self.collection = self.chroma_client.create_collection(
            name="berth_knowledge",
            metadata={"description": "Berth Planning Knowledge Base for RAG"}
        )
        print("Collection cleared")

    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the collection
        """
        count = self.collection.count()

        # Get sample to analyze metadata
        if count > 0:
            sample = self.collection.peek(limit=min(10, count))

            categories = set()
            source_tables = set()

            for metadata in sample['metadatas']:
                if 'document_type' in metadata:
                    categories.add(metadata['document_type'])
                if 'source_tables' in metadata:
                    source_tables.update(metadata['source_tables'].split(','))

            return {
                "total_chunks": count,
                "categories": sorted(list(categories)),
                "source_tables": sorted([t for t in source_tables if t]),
                "embedding_dimension": self.embedding_model.get_sentence_embedding_dimension(),
                "model": self.embedding_model_name
            }
        else:
            return {
                "total_chunks": 0,
                "message": "Collection is empty"
            }


def main():
    """
    Main function to load documents and populate ChromaDB
    """
    print("=" * 70)
    print("BERTH PLANNING KNOWLEDGE BASE - DOCUMENT LOADER")
    print("=" * 70)

    # Initialize loader
    loader = DocumentLoader(
        docs_dir="../knowledge_docs",
        chroma_persist_dir="./chroma_db",
        embedding_model="all-MiniLM-L6-v2",
        chunk_size=500,
        chunk_overlap=50
    )

    # Option to clear existing collection
    response = input("\nClear existing collection? (y/n): ")
    if response.lower() == 'y':
        loader.clear_collection()

    # Load documents
    documents = loader.load_all_documents()

    if not documents:
        print("ERROR: No documents found!")
        return

    # Calculate total size
    total_size = sum(doc["size_bytes"] for doc in documents)
    print(f"\nTotal knowledge base size: {total_size / 1024:.2f} KB")

    # Embed and store
    chunk_count = loader.embed_and_store(documents)

    # Print stats
    print("\n" + "=" * 70)
    print("COLLECTION STATISTICS")
    print("=" * 70)
    stats = loader.get_collection_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n✓ Document loading complete!")
    print("\nYou can now use the retriever to query this knowledge base.")


if __name__ == "__main__":
    main()
