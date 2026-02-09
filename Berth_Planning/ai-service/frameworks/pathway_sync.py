"""
Pathway Real-Time Data Sync Pipeline
=====================================

Implements Pathway-style real-time data synchronization:
- Live Data Streaming: Ingest data from multiple sources
- Incremental Updates: Process changes without full reindexing
- Vector Index Sync: Keep embeddings up-to-date
- Change Detection: Track modifications and deletions

Enables real-time RAG with live document updates.
"""

import logging
import json
import asyncio
import hashlib
from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import threading
import queue
import time

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA STRUCTURES
# ============================================================================

class ChangeType(Enum):
    """Types of data changes"""
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    UPSERT = "upsert"


class SourceType(Enum):
    """Types of data sources"""
    FILE = "file"
    DATABASE = "database"
    API = "api"
    STREAM = "stream"
    WEBHOOK = "webhook"


@dataclass
class DataChange:
    """Represents a data change event"""
    id: str
    change_type: ChangeType
    source: str
    timestamp: str
    data: Dict[str, Any]
    previous_hash: Optional[str] = None
    current_hash: Optional[str] = None


@dataclass
class DataSource:
    """A data source configuration"""
    name: str
    source_type: SourceType
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    poll_interval: float = 60.0  # seconds
    last_sync: Optional[str] = None


@dataclass
class SyncState:
    """Synchronization state for a source"""
    source_name: str
    last_sync_time: str
    documents_synced: int
    changes_pending: int
    errors: List[str] = field(default_factory=list)
    document_hashes: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# CHANGE DETECTOR
# ============================================================================

class ChangeDetector:
    """
    Detects changes in documents by comparing hashes.
    """
    
    def __init__(self):
        self.document_hashes: Dict[str, str] = {}
    
    def _compute_hash(self, content: Any) -> str:
        """Compute hash of content"""
        if isinstance(content, dict):
            content = json.dumps(content, sort_keys=True)
        elif not isinstance(content, str):
            content = str(content)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def detect_changes(
        self,
        documents: List[Dict[str, Any]],
        id_field: str = "id"
    ) -> List[DataChange]:
        """
        Detect changes in a batch of documents
        
        Args:
            documents: List of documents with id and content
            id_field: Field to use as document ID
            
        Returns:
            List of detected changes
        """
        changes = []
        current_ids = set()
        
        for doc in documents:
            doc_id = doc.get(id_field)
            if not doc_id:
                continue
            
            current_ids.add(doc_id)
            current_hash = self._compute_hash(doc)
            previous_hash = self.document_hashes.get(doc_id)
            
            if previous_hash is None:
                # New document
                change = DataChange(
                    id=doc_id,
                    change_type=ChangeType.INSERT,
                    source="detector",
                    timestamp=datetime.now().isoformat(),
                    data=doc,
                    current_hash=current_hash
                )
                changes.append(change)
            elif previous_hash != current_hash:
                # Updated document
                change = DataChange(
                    id=doc_id,
                    change_type=ChangeType.UPDATE,
                    source="detector",
                    timestamp=datetime.now().isoformat(),
                    data=doc,
                    previous_hash=previous_hash,
                    current_hash=current_hash
                )
                changes.append(change)
            
            # Update stored hash
            self.document_hashes[doc_id] = current_hash
        
        # Detect deletions
        deleted_ids = set(self.document_hashes.keys()) - current_ids
        for doc_id in deleted_ids:
            change = DataChange(
                id=doc_id,
                change_type=ChangeType.DELETE,
                source="detector",
                timestamp=datetime.now().isoformat(),
                data={"id": doc_id},
                previous_hash=self.document_hashes[doc_id]
            )
            changes.append(change)
            del self.document_hashes[doc_id]
        
        return changes


# ============================================================================
# DATA CONNECTORS
# ============================================================================

class BaseConnector:
    """Base class for data source connectors"""
    
    def __init__(self, source: DataSource):
        self.source = source
        self.change_detector = ChangeDetector()
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch documents from source"""
        raise NotImplementedError
    
    async def fetch_changes(self) -> List[DataChange]:
        """Fetch only changes since last sync"""
        documents = await self.fetch()
        return self.change_detector.detect_changes(documents)


class FileConnector(BaseConnector):
    """Connector for file-based data sources"""
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch documents from files"""
        import os
        
        path = self.source.config.get("path", ".")
        pattern = self.source.config.get("pattern", "*.json")
        
        documents = []
        
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        documents.extend(data)
                    else:
                        documents.append(data)
            except Exception as e:
                logger.error(f"Failed to read file {path}: {e}")
        elif os.path.isdir(path):
            import glob
            for filepath in glob.glob(os.path.join(path, pattern)):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for item in data:
                                item["_source_file"] = filepath
                            documents.extend(data)
                        else:
                            data["_source_file"] = filepath
                            documents.append(data)
                except Exception as e:
                    logger.error(f"Failed to read file {filepath}: {e}")
        
        return documents


class DatabaseConnector(BaseConnector):
    """Connector for database sources"""
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch documents from database"""
        query = self.source.config.get("query", "")
        connection_string = self.source.config.get("connection_string", "")
        
        # Simulated - in production would execute actual query
        logger.info(f"Database fetch: {query}")
        return []


class APIConnector(BaseConnector):
    """Connector for API sources"""
    
    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch documents from API"""
        import aiohttp
        
        url = self.source.config.get("url", "")
        headers = self.source.config.get("headers", {})
        
        documents = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list):
                            documents.extend(data)
                        else:
                            documents.append(data)
        except Exception as e:
            logger.error(f"API fetch failed: {e}")
        
        return documents


# Connector factory
def get_connector(source: DataSource) -> BaseConnector:
    """Get appropriate connector for source type"""
    connectors = {
        SourceType.FILE: FileConnector,
        SourceType.DATABASE: DatabaseConnector,
        SourceType.API: APIConnector,
    }
    connector_class = connectors.get(source.source_type, BaseConnector)
    return connector_class(source)


# ============================================================================
# VECTOR INDEX UPDATER
# ============================================================================

class VectorIndexUpdater:
    """
    Handles incremental updates to vector index.
    """
    
    def __init__(
        self,
        embedder=None,
        vector_store=None
    ):
        """
        Initialize updater
        
        Args:
            embedder: Function to generate embeddings
            vector_store: Vector store instance (ChromaDB, etc.)
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.pending_updates: List[DataChange] = []
    
    async def process_change(self, change: DataChange):
        """
        Process a single change
        
        Args:
            change: The data change to process
        """
        if change.change_type == ChangeType.DELETE:
            await self._handle_delete(change)
        elif change.change_type == ChangeType.INSERT:
            await self._handle_insert(change)
        elif change.change_type == ChangeType.UPDATE:
            await self._handle_update(change)
        elif change.change_type == ChangeType.UPSERT:
            await self._handle_upsert(change)
    
    async def _handle_insert(self, change: DataChange):
        """Handle document insertion"""
        if not self.vector_store or not self.embedder:
            self.pending_updates.append(change)
            return
        
        content = change.data.get("content", "")
        if content and self.embedder:
            embedding = self.embedder(content)
            
            # Add to vector store
            if hasattr(self.vector_store, 'add'):
                self.vector_store.add(
                    ids=[change.id],
                    documents=[content],
                    embeddings=[embedding] if embedding else None,
                    metadatas=[change.data.get("metadata", {})]
                )
        
        logger.debug(f"Inserted document: {change.id}")
    
    async def _handle_update(self, change: DataChange):
        """Handle document update"""
        await self._handle_delete(change)
        await self._handle_insert(change)
        logger.debug(f"Updated document: {change.id}")
    
    async def _handle_delete(self, change: DataChange):
        """Handle document deletion"""
        if not self.vector_store:
            self.pending_updates.append(change)
            return
        
        if hasattr(self.vector_store, 'delete'):
            self.vector_store.delete(ids=[change.id])
        
        logger.debug(f"Deleted document: {change.id}")
    
    async def _handle_upsert(self, change: DataChange):
        """Handle upsert (insert or update)"""
        await self._handle_update(change)
    
    async def process_batch(self, changes: List[DataChange]):
        """Process a batch of changes"""
        for change in changes:
            await self.process_change(change)
        
        logger.info(f"Processed batch of {len(changes)} changes")


# ============================================================================
# PATHWAY SYNC PIPELINE
# ============================================================================

class PathwaySyncPipeline:
    """
    Real-time data synchronization pipeline.
    
    Features:
    - Multiple data source support
    - Incremental updates
    - Change detection
    - Vector index synchronization
    """
    
    def __init__(
        self,
        embedder=None,
        vector_store=None
    ):
        """
        Initialize sync pipeline
        
        Args:
            embedder: Embedding function
            vector_store: Vector store instance
        """
        self.sources: Dict[str, DataSource] = {}
        self.connectors: Dict[str, BaseConnector] = {}
        self.sync_states: Dict[str, SyncState] = {}
        
        self.index_updater = VectorIndexUpdater(embedder, vector_store)
        
        self.change_queue: queue.Queue = queue.Queue()
        self.callbacks: List[Callable[[DataChange], None]] = []
        
        self._running = False
        self._sync_thread: Optional[threading.Thread] = None
        
        logger.info("PathwaySyncPipeline initialized")
    
    def add_source(
        self,
        name: str,
        source_type: SourceType,
        config: Dict[str, Any] = None,
        poll_interval: float = 60.0
    ) -> DataSource:
        """
        Add a data source
        
        Args:
            name: Source name
            source_type: Type of source
            config: Source configuration
            poll_interval: Polling interval in seconds
            
        Returns:
            Created DataSource
        """
        source = DataSource(
            name=name,
            source_type=source_type,
            config=config or {},
            poll_interval=poll_interval
        )
        
        self.sources[name] = source
        self.connectors[name] = get_connector(source)
        self.sync_states[name] = SyncState(
            source_name=name,
            last_sync_time=datetime.now().isoformat(),
            documents_synced=0,
            changes_pending=0
        )
        
        logger.info(f"Added data source: {name} ({source_type.value})")
        return source
    
    def remove_source(self, name: str):
        """Remove a data source"""
        if name in self.sources:
            del self.sources[name]
            del self.connectors[name]
            del self.sync_states[name]
            logger.info(f"Removed data source: {name}")
    
    def on_change(self, callback: Callable[[DataChange], None]):
        """Register callback for changes"""
        self.callbacks.append(callback)
    
    async def sync_source(self, name: str) -> List[DataChange]:
        """
        Sync a single source
        
        Args:
            name: Source name
            
        Returns:
            List of changes detected
        """
        if name not in self.connectors:
            logger.warning(f"Unknown source: {name}")
            return []
        
        connector = self.connectors[name]
        
        try:
            changes = await connector.fetch_changes()
            
            # Update sync state
            state = self.sync_states[name]
            state.last_sync_time = datetime.now().isoformat()
            state.documents_synced += len([c for c in changes if c.change_type != ChangeType.DELETE])
            
            # Process changes
            await self.index_updater.process_batch(changes)
            
            # Call callbacks
            for change in changes:
                for callback in self.callbacks:
                    try:
                        callback(change)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
            
            logger.info(f"Synced source {name}: {len(changes)} changes")
            return changes
            
        except Exception as e:
            logger.error(f"Sync failed for {name}: {e}")
            self.sync_states[name].errors.append(str(e))
            return []
    
    async def sync_all(self) -> Dict[str, List[DataChange]]:
        """
        Sync all enabled sources
        
        Returns:
            Dict of source name to changes
        """
        results = {}
        
        for name, source in self.sources.items():
            if source.enabled:
                changes = await self.sync_source(name)
                results[name] = changes
        
        return results
    
    def start_background_sync(self):
        """Start background synchronization thread"""
        if self._running:
            logger.warning("Sync already running")
            return
        
        self._running = True
        self._sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self._sync_thread.start()
        logger.info("Started background sync")
    
    def stop_background_sync(self):
        """Stop background synchronization"""
        self._running = False
        if self._sync_thread:
            self._sync_thread.join(timeout=5.0)
        logger.info("Stopped background sync")
    
    def _sync_loop(self):
        """Background sync loop"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        while self._running:
            for name, source in self.sources.items():
                if not self._running:
                    break
                
                if source.enabled:
                    try:
                        loop.run_until_complete(self.sync_source(name))
                    except Exception as e:
                        logger.error(f"Sync error for {name}: {e}")
                
                # Sleep for poll interval
                time.sleep(source.poll_interval)
        
        loop.close()
    
    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status"""
        return {
            "running": self._running,
            "sources": {
                name: {
                    "type": source.source_type.value,
                    "enabled": source.enabled,
                    "poll_interval": source.poll_interval,
                    "last_sync": self.sync_states.get(name, SyncState(name, "", 0, 0)).last_sync_time
                }
                for name, source in self.sources.items()
            },
            "total_synced": sum(s.documents_synced for s in self.sync_states.values())
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_pathway_pipeline(
    embedder=None,
    vector_store=None
) -> PathwaySyncPipeline:
    """Create a Pathway sync pipeline instance"""
    return PathwaySyncPipeline(embedder=embedder, vector_store=vector_store)
