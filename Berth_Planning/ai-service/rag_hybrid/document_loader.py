"""
Document Loader for SmartBerth AI
Handles document loading, chunking, and ChromaDB storage
Adapted from Azure DevOps ai-backend/rag/document_loader.py
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass
from datetime import datetime
import hashlib

import chromadb
from sentence_transformers import SentenceTransformer

# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import get_settings


@dataclass
class DocumentChunk:
    """Represents a document chunk for embedding"""
    id: str
    content: str
    metadata: Dict[str, Any]


class DocumentLoader:
    """
    Handles document loading, chunking, and storage in ChromaDB
    
    Features:
    - Supports .txt, .md, .json files
    - Smart chunking with overlap
    - Category extraction from folder structure
    - Source table detection
    - Deduplication using content hashing
    """

    def __init__(
        self,
        collection_name: str = "smartberth_knowledge",
        embedding_model: str = "all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """
        Initialize the document loader
        
        Args:
            collection_name: ChromaDB collection name
            embedding_model: Sentence transformer model name
            chunk_size: Target chunk size in words
            chunk_overlap: Overlap between chunks in words
        """
        self.settings = get_settings()
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Initialize ChromaDB
        persist_dir = self.settings.chroma_persist_dir
        self.chroma_client = chromadb.PersistentClient(path=persist_dir)
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "SmartBerth knowledge base"}
        )
        
        print(f"Initialized DocumentLoader with collection: {collection_name}")
        print(f"Current documents: {self.collection.count()}")

        # Category mappings
        self.category_mappings = {
            "port_manuals": "Port Operations Manual",
            "historical_logs": "Historical Operations Log",
            "weather_studies": "Weather Impact Study",
            "best_practices": "Industry Best Practices",
            "training": "Training Material",
            "policies": "Policy Document",
            "procedures": "Standard Operating Procedure"
        }
        
        # Source table patterns
        self.source_table_patterns = {
            r"vessel|ship|tanker|bulk|container": "VESSELS",
            r"berth|quay|dock|pier": "BERTHS",
            r"terminal|facility": "TERMINALS",
            r"port|harbor|harbour": "PORTS",
            r"pilot|pilotage": "PILOTS",
            r"tug|tugboat": "TUGBOATS",
            r"weather|wind|wave|visibility": "WEATHER_DATA",
            r"tide|tidal|water.?level": "TIDAL_DATA",
            r"ais|position|tracking": "AIS_DATA",
            r"ukc|underkeel|clearance|draft": "UKC_DATA",
            r"schedule|eta|etd|arrival|departure": "VESSEL_SCHEDULE",
            r"maintenance|repair|outage": "BERTH_MAINTENANCE",
            r"alert|notification|warning": "ALERTS_NOTIFICATIONS",
            r"anchorage|anchor|waiting": "ANCHORAGES",
            r"channel|fairway|approach": "CHANNELS"
        }

    def _generate_chunk_id(self, content: str, source: str, index: int) -> str:
        """Generate unique ID for a chunk"""
        hash_input = f"{source}:{index}:{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _extract_category(self, file_path: str) -> str:
        """Extract category from file path"""
        path_lower = file_path.lower()
        
        for folder, category in self.category_mappings.items():
            if folder in path_lower:
                return category
        
        # Default category based on file extension
        if file_path.endswith(".md"):
            return "Documentation"
        elif file_path.endswith(".json"):
            return "Configuration"
        else:
            return "General"

    def _detect_source_tables(self, content: str) -> List[str]:
        """Detect referenced database tables from content"""
        tables = set()
        content_lower = content.lower()
        
        for pattern, table in self.source_table_patterns.items():
            if re.search(pattern, content_lower):
                tables.add(table)
        
        return list(tables)

    def _chunk_text(self, text: str) -> Generator[str, None, None]:
        """
        Split text into chunks with overlap
        
        Uses word-based chunking for better semantic boundaries
        """
        words = text.split()
        
        if len(words) <= self.chunk_size:
            yield text
            return
        
        start = 0
        while start < len(words):
            end = start + self.chunk_size
            chunk_words = words[start:end]
            yield " ".join(chunk_words)
            start = end - self.chunk_overlap

    def load_file(self, file_path: str) -> List[DocumentChunk]:
        """
        Load and chunk a single file
        
        Args:
            file_path: Path to the file
            
        Returns:
            List of DocumentChunk objects
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return []
        
        # Read content
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return []
        
        if not content.strip():
            print(f"Empty file: {file_path}")
            return []
        
        # Extract metadata
        category = self._extract_category(str(file_path))
        source_tables = self._detect_source_tables(content)
        
        # Chunk and create documents
        chunks = []
        for i, chunk_content in enumerate(self._chunk_text(content)):
            chunk_id = self._generate_chunk_id(chunk_content, str(file_path), i)
            
            chunks.append(DocumentChunk(
                id=chunk_id,
                content=chunk_content,
                metadata={
                    "source": file_path.name,
                    "source_path": str(file_path),
                    "category": category,
                    "source_tables": ",".join(source_tables),
                    "chunk_index": i,
                    "loaded_at": datetime.now().isoformat()
                }
            ))
        
        return chunks

    def load_directory(
        self,
        directory: str,
        extensions: List[str] = [".txt", ".md", ".json"],
        recursive: bool = True
    ) -> int:
        """
        Load all documents from a directory
        
        Args:
            directory: Directory path
            extensions: File extensions to process
            recursive: Whether to process subdirectories
            
        Returns:
            Number of chunks loaded
        """
        directory = Path(directory)
        
        if not directory.exists():
            print(f"Directory not found: {directory}")
            return 0
        
        all_chunks = []
        
        # Find all files
        if recursive:
            files = [f for f in directory.rglob("*") if f.suffix in extensions]
        else:
            files = [f for f in directory.glob("*") if f.suffix in extensions]
        
        print(f"Found {len(files)} files to process")
        
        for file_path in files:
            chunks = self.load_file(str(file_path))
            all_chunks.extend(chunks)
            if chunks:
                print(f"  Loaded {len(chunks)} chunks from {file_path.name}")
        
        # Store in ChromaDB
        if all_chunks:
            self._store_chunks(all_chunks)
        
        return len(all_chunks)

    def _store_chunks(self, chunks: List[DocumentChunk]):
        """
        Store chunks in ChromaDB
        
        Args:
            chunks: List of DocumentChunk objects
        """
        # Generate embeddings
        contents = [chunk.content for chunk in chunks]
        embeddings = self.embedding_model.encode(contents).tolist()
        
        # Prepare for ChromaDB
        ids = [chunk.id for chunk in chunks]
        metadatas = [chunk.metadata for chunk in chunks]
        
        # Check for existing chunks (deduplication)
        try:
            existing = self.collection.get(ids=ids)
            existing_ids = set(existing["ids"])
            
            # Filter out existing chunks
            new_indices = [
                i for i, id in enumerate(ids) 
                if id not in existing_ids
            ]
            
            if not new_indices:
                print("All chunks already exist, skipping")
                return
            
            ids = [ids[i] for i in new_indices]
            contents = [contents[i] for i in new_indices]
            embeddings = [embeddings[i] for i in new_indices]
            metadatas = [metadatas[i] for i in new_indices]
            
            print(f"Adding {len(ids)} new chunks (skipped {len(existing_ids)} duplicates)")
        except Exception:
            print(f"Adding {len(ids)} chunks")
        
        # Add to collection
        self.collection.add(
            ids=ids,
            documents=contents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        
        print(f"Total documents in collection: {self.collection.count()}")

    def add_document(
        self,
        content: str,
        source: str,
        category: str = "General",
        extra_metadata: Optional[Dict] = None
    ) -> int:
        """
        Add a single document to the collection
        
        Args:
            content: Document content
            source: Source identifier
            category: Document category
            extra_metadata: Additional metadata
            
        Returns:
            Number of chunks added
        """
        # Detect source tables
        source_tables = self._detect_source_tables(content)
        
        # Chunk and create documents
        chunks = []
        for i, chunk_content in enumerate(self._chunk_text(content)):
            chunk_id = self._generate_chunk_id(chunk_content, source, i)
            
            metadata = {
                "source": source,
                "category": category,
                "source_tables": ",".join(source_tables),
                "chunk_index": i,
                "loaded_at": datetime.now().isoformat()
            }
            
            if extra_metadata:
                metadata.update(extra_metadata)
            
            chunks.append(DocumentChunk(
                id=chunk_id,
                content=chunk_content,
                metadata=metadata
            ))
        
        if chunks:
            self._store_chunks(chunks)
        
        return len(chunks)

    def clear_collection(self):
        """Clear all documents from the collection"""
        # Delete and recreate collection
        self.chroma_client.delete_collection(self.collection_name)
        self.collection = self.chroma_client.create_collection(
            name=self.collection_name,
            metadata={"description": "SmartBerth knowledge base"}
        )
        print(f"Cleared collection: {self.collection_name}")

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        # Get category counts
        try:
            all_docs = self.collection.get(include=["metadatas"])
            categories = {}
            sources = {}
            
            for metadata in all_docs["metadatas"]:
                cat = metadata.get("category", "Unknown")
                src = metadata.get("source", "Unknown")
                
                categories[cat] = categories.get(cat, 0) + 1
                sources[src] = sources.get(src, 0) + 1
            
            return {
                "collection_name": self.collection_name,
                "total_chunks": self.collection.count(),
                "unique_sources": len(sources),
                "categories": categories,
                "top_sources": dict(sorted(
                    sources.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10])
            }
        except Exception as e:
            return {
                "collection_name": self.collection_name,
                "total_chunks": self.collection.count(),
                "error": str(e)
            }


# Singleton instance
_loader_instance: Optional[DocumentLoader] = None


def get_document_loader() -> DocumentLoader:
    """Get or create singleton loader instance"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = DocumentLoader()
    return _loader_instance
