"""
Mem0 - Persistent Memory Layer for AI
======================================

Implements Mem0-style memory management:
- Long-term Memory: Persist important facts across sessions
- Short-term Memory: Track recent conversation context
- Episodic Memory: Remember specific interactions/events
- Semantic Memory: Store conceptual knowledge
- Memory Consolidation: Merge and deduplicate memories

Enables context-aware conversations with memory persistence.
"""

import logging
import json
import hashlib
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND DATA STRUCTURES
# ============================================================================

class MemoryType(Enum):
    """Types of memories"""
    SHORT_TERM = "short_term"      # Recent context, decays quickly
    LONG_TERM = "long_term"        # Important facts, persistent
    EPISODIC = "episodic"          # Specific events/interactions
    SEMANTIC = "semantic"          # Conceptual knowledge
    WORKING = "working"            # Active task context


class MemoryPriority(Enum):
    """Priority levels for memories"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Memory:
    """A single memory unit"""
    id: str
    content: str
    memory_type: MemoryType
    priority: MemoryPriority = MemoryPriority.MEDIUM
    
    # Associations
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    entity_refs: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Temporal
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_accessed: str = field(default_factory=lambda: datetime.now().isoformat())
    access_count: int = 0
    decay_rate: float = 0.1  # How fast memory fades
    
    # Embeddings
    embedding: Optional[List[float]] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "priority": self.priority.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "tags": self.tags,
            "created_at": self.created_at,
            "access_count": self.access_count,
            "metadata": self.metadata
        }


@dataclass
class MemoryQuery:
    """Query parameters for memory retrieval"""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    memory_types: Optional[List[MemoryType]] = None
    tags: Optional[List[str]] = None
    min_priority: MemoryPriority = MemoryPriority.LOW
    limit: int = 10
    include_expired: bool = False


@dataclass
class MemorySearchResult:
    """Result from memory search"""
    memory: Memory
    relevance_score: float
    recency_score: float
    combined_score: float


# ============================================================================
# MEMORY EXTRACTOR
# ============================================================================

class MemoryExtractor:
    """
    Extract memories from conversations.
    Uses patterns and LLM to identify memorable information.
    """
    
    # Patterns indicating memorable information
    FACT_PATTERNS = [
        r"my name is (\w+)",
        r"i am (?:a|an) (.+)",
        r"i work (?:at|for) (.+)",
        r"i prefer (.+)",
        r"i need (.+)",
        r"i want (.+)",
        r"my (.+) is (.+)",
        r"remember that (.+)",
        r"don't forget (.+)",
    ]
    
    # Maritime domain patterns
    MARITIME_PATTERNS = [
        r"vessel (.+?) (?:is|was|will)",
        r"berth (\w+) (?:is|was|will)",
        r"eta (?:is|for) (.+)",
        r"draft (?:is|of) (.+)",
        r"cargo (?:is|includes) (.+)",
    ]
    
    def __init__(self, llm_caller=None):
        self.llm_caller = llm_caller
    
    def extract_from_text(
        self,
        text: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Memory]:
        """
        Extract memories from text
        
        Args:
            text: Text to extract memories from
            user_id: User ID for association
            session_id: Session ID for association
            
        Returns:
            List of extracted memories
        """
        memories = []
        text_lower = text.lower()
        
        # Pattern-based extraction
        for pattern in self.FACT_PATTERNS + self.MARITIME_PATTERNS:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                content = match if isinstance(match, str) else " ".join(match)
                memory = Memory(
                    id=f"mem_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                    content=content.strip(),
                    memory_type=MemoryType.LONG_TERM,
                    priority=MemoryPriority.MEDIUM,
                    user_id=user_id,
                    session_id=session_id,
                    tags=["extracted"]
                )
                memories.append(memory)
        
        # LLM-based extraction for complex memories
        if self.llm_caller and len(text) > 50:
            llm_memories = self._extract_with_llm(text, user_id, session_id)
            memories.extend(llm_memories)
        
        return memories
    
    def _extract_with_llm(
        self,
        text: str,
        user_id: Optional[str],
        session_id: Optional[str]
    ) -> List[Memory]:
        """Use LLM to extract complex memories"""
        prompt = f"""Extract key facts and preferences from this text that should be remembered.

TEXT:
{text[:1000]}

Output JSON array of memorable facts:
[
  {{"content": "fact to remember", "type": "long_term|episodic|semantic", "priority": 1-4, "tags": ["tag1"]}}
]

Only include genuinely important information. Output JSON only:"""

        try:
            response = self.llm_caller(prompt)
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                data = json.loads(response[start:end])
                
                memories = []
                for item in data:
                    memory_type_str = item.get("type", "long_term")
                    memory_type = MemoryType.LONG_TERM
                    if memory_type_str == "episodic":
                        memory_type = MemoryType.EPISODIC
                    elif memory_type_str == "semantic":
                        memory_type = MemoryType.SEMANTIC
                    
                    priority = MemoryPriority(min(4, max(1, item.get("priority", 2))))
                    
                    memory = Memory(
                        id=f"mem_{hashlib.md5(item['content'].encode()).hexdigest()[:8]}",
                        content=item.get("content", ""),
                        memory_type=memory_type,
                        priority=priority,
                        user_id=user_id,
                        session_id=session_id,
                        tags=item.get("tags", ["llm_extracted"])
                    )
                    memories.append(memory)
                
                return memories
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"LLM memory extraction failed: {e}")
        
        return []


# ============================================================================
# MEMORY STORE
# ============================================================================

class MemoryStore:
    """
    In-memory storage for memories.
    In production, would be backed by persistent storage.
    """
    
    def __init__(self):
        self.memories: Dict[str, Memory] = {}
        self.by_user: Dict[str, List[str]] = defaultdict(list)
        self.by_session: Dict[str, List[str]] = defaultdict(list)
        self.by_type: Dict[MemoryType, List[str]] = defaultdict(list)
        self.by_tag: Dict[str, List[str]] = defaultdict(list)
    
    def add(self, memory: Memory):
        """Add a memory to the store"""
        self.memories[memory.id] = memory
        
        if memory.user_id:
            self.by_user[memory.user_id].append(memory.id)
        if memory.session_id:
            self.by_session[memory.session_id].append(memory.id)
        self.by_type[memory.memory_type].append(memory.id)
        for tag in memory.tags:
            self.by_tag[tag].append(memory.id)
    
    def get(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by ID"""
        memory = self.memories.get(memory_id)
        if memory:
            memory.access_count += 1
            memory.last_accessed = datetime.now().isoformat()
        return memory
    
    def delete(self, memory_id: str):
        """Delete a memory"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            
            if memory.user_id and memory_id in self.by_user[memory.user_id]:
                self.by_user[memory.user_id].remove(memory_id)
            if memory.session_id and memory_id in self.by_session[memory.session_id]:
                self.by_session[memory.session_id].remove(memory_id)
            if memory_id in self.by_type[memory.memory_type]:
                self.by_type[memory.memory_type].remove(memory_id)
            for tag in memory.tags:
                if memory_id in self.by_tag[tag]:
                    self.by_tag[tag].remove(memory_id)
            
            del self.memories[memory_id]
    
    def get_by_user(self, user_id: str) -> List[Memory]:
        """Get all memories for a user"""
        return [self.memories[mid] for mid in self.by_user.get(user_id, []) if mid in self.memories]
    
    def get_by_session(self, session_id: str) -> List[Memory]:
        """Get all memories for a session"""
        return [self.memories[mid] for mid in self.by_session.get(session_id, []) if mid in self.memories]
    
    def get_by_type(self, memory_type: MemoryType) -> List[Memory]:
        """Get all memories of a type"""
        return [self.memories[mid] for mid in self.by_type.get(memory_type, []) if mid in self.memories]
    
    def get_all(self) -> List[Memory]:
        """Get all memories"""
        return list(self.memories.values())


# ============================================================================
# MEMORY RANKER
# ============================================================================

class MemoryRanker:
    """
    Rank memories by relevance and recency.
    """
    
    def __init__(
        self,
        recency_weight: float = 0.3,
        relevance_weight: float = 0.5,
        priority_weight: float = 0.2
    ):
        self.recency_weight = recency_weight
        self.relevance_weight = relevance_weight
        self.priority_weight = priority_weight
    
    def _compute_recency_score(self, memory: Memory) -> float:
        """Compute recency score (0-1, higher is more recent)"""
        created = datetime.fromisoformat(memory.created_at)
        age_hours = (datetime.now() - created).total_seconds() / 3600
        
        # Exponential decay based on memory type
        if memory.memory_type == MemoryType.SHORT_TERM:
            half_life = 1  # 1 hour
        elif memory.memory_type == MemoryType.WORKING:
            half_life = 0.5  # 30 minutes
        else:
            half_life = 24 * 7  # 1 week
        
        return 0.5 ** (age_hours / half_life)
    
    def _compute_relevance_score(
        self,
        memory: Memory,
        query: str,
        query_embedding: Optional[List[float]] = None
    ) -> float:
        """Compute relevance score (0-1)"""
        # Simple keyword matching
        query_words = set(query.lower().split())
        memory_words = set(memory.content.lower().split())
        
        overlap = len(query_words & memory_words)
        total = len(query_words | memory_words)
        
        keyword_score = overlap / total if total > 0 else 0
        
        # Embedding similarity if available
        if query_embedding and memory.embedding:
            import numpy as np
            query_vec = np.array(query_embedding)
            memory_vec = np.array(memory.embedding)
            cosine_sim = np.dot(query_vec, memory_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(memory_vec) + 1e-8
            )
            return 0.5 * keyword_score + 0.5 * max(0, cosine_sim)
        
        return keyword_score
    
    def rank(
        self,
        memories: List[Memory],
        query: str,
        query_embedding: Optional[List[float]] = None
    ) -> List[MemorySearchResult]:
        """
        Rank memories by combined score
        
        Args:
            memories: Memories to rank
            query: Search query
            query_embedding: Optional query embedding
            
        Returns:
            Sorted list of search results
        """
        results = []
        
        for memory in memories:
            recency = self._compute_recency_score(memory)
            relevance = self._compute_relevance_score(memory, query, query_embedding)
            priority_score = memory.priority.value / 4.0
            
            combined = (
                self.recency_weight * recency +
                self.relevance_weight * relevance +
                self.priority_weight * priority_score
            )
            
            results.append(MemorySearchResult(
                memory=memory,
                relevance_score=relevance,
                recency_score=recency,
                combined_score=combined
            ))
        
        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results


# ============================================================================
# MEM0 MEMORY MANAGER
# ============================================================================

class Mem0MemoryManager:
    """
    Main memory management system.
    
    Provides:
    - Memory storage and retrieval
    - Automatic memory extraction
    - Memory consolidation
    - Context-aware recall
    """
    
    def __init__(
        self,
        llm_caller=None,
        embedder=None
    ):
        """
        Initialize memory manager
        
        Args:
            llm_caller: Function to call LLM
            embedder: Function to generate embeddings
        """
        self.store = MemoryStore()
        self.extractor = MemoryExtractor(llm_caller)
        self.ranker = MemoryRanker()
        
        self.llm_caller = llm_caller
        self.embedder = embedder
        
        logger.info("Mem0MemoryManager initialized")
    
    def add(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.LONG_TERM,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Memory:
        """
        Add a memory explicitly
        
        Args:
            content: Memory content
            memory_type: Type of memory
            priority: Priority level
            user_id: User association
            session_id: Session association
            tags: Tags for categorization
            metadata: Additional metadata
            
        Returns:
            Created memory
        """
        memory = Memory(
            id=f"mem_{hashlib.md5((content + str(datetime.now())).encode()).hexdigest()[:8]}",
            content=content,
            memory_type=memory_type,
            priority=priority,
            user_id=user_id,
            session_id=session_id,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Generate embedding if embedder available
        if self.embedder:
            memory.embedding = self.embedder(content)
        
        self.store.add(memory)
        logger.debug(f"Added memory: {memory.id}")
        
        return memory
    
    def add_from_conversation(
        self,
        user_message: str,
        assistant_response: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Memory]:
        """
        Extract and add memories from a conversation turn
        
        Args:
            user_message: User's message
            assistant_response: Assistant's response
            user_id: User ID
            session_id: Session ID
            
        Returns:
            List of extracted memories
        """
        memories = []
        
        # Extract from user message
        user_memories = self.extractor.extract_from_text(
            user_message,
            user_id=user_id,
            session_id=session_id
        )
        
        # Add embeddings
        for memory in user_memories:
            if self.embedder:
                memory.embedding = self.embedder(memory.content)
            self.store.add(memory)
            memories.append(memory)
        
        # Also store the interaction as episodic memory
        episodic = Memory(
            id=f"mem_ep_{hashlib.md5(user_message[:50].encode()).hexdigest()[:8]}",
            content=f"User asked: {user_message[:200]}... Response: {assistant_response[:200]}...",
            memory_type=MemoryType.EPISODIC,
            priority=MemoryPriority.LOW,
            user_id=user_id,
            session_id=session_id,
            tags=["conversation"]
        )
        
        if self.embedder:
            episodic.embedding = self.embedder(episodic.content)
        
        self.store.add(episodic)
        memories.append(episodic)
        
        return memories
    
    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[MemorySearchResult]:
        """
        Search memories
        
        Args:
            query: Search query
            user_id: Filter by user
            session_id: Filter by session
            memory_types: Filter by memory types
            tags: Filter by tags
            limit: Max results
            
        Returns:
            Ranked search results
        """
        # Get candidate memories
        if user_id:
            candidates = self.store.get_by_user(user_id)
        elif session_id:
            candidates = self.store.get_by_session(session_id)
        else:
            candidates = self.store.get_all()
        
        # Filter by type
        if memory_types:
            candidates = [m for m in candidates if m.memory_type in memory_types]
        
        # Filter by tags
        if tags:
            candidates = [m for m in candidates if any(t in m.tags for t in tags)]
        
        # Generate query embedding
        query_embedding = None
        if self.embedder:
            query_embedding = self.embedder(query)
        
        # Rank results
        results = self.ranker.rank(candidates, query, query_embedding)
        
        return results[:limit]
    
    def get_context(
        self,
        query: str,
        user_id: Optional[str] = None,
        max_tokens: int = 1000
    ) -> str:
        """
        Get relevant memory context for a query
        
        Args:
            query: Current query
            user_id: User ID
            max_tokens: Max context tokens
            
        Returns:
            Formatted context string
        """
        results = self.search(
            query=query,
            user_id=user_id,
            memory_types=[MemoryType.LONG_TERM, MemoryType.SEMANTIC],
            limit=10
        )
        
        context_parts = []
        total_length = 0
        
        for result in results:
            memory_text = f"[{result.memory.memory_type.value}] {result.memory.content}"
            if total_length + len(memory_text) > max_tokens * 4:  # Approximate chars
                break
            context_parts.append(memory_text)
            total_length += len(memory_text)
        
        if not context_parts:
            return ""
        
        return "Relevant memories:\n" + "\n".join(context_parts)
    
    def consolidate(self, user_id: Optional[str] = None):
        """
        Consolidate memories - merge similar, remove duplicates
        
        Args:
            user_id: Optionally limit to user's memories
        """
        if user_id:
            memories = self.store.get_by_user(user_id)
        else:
            memories = self.store.get_all()
        
        # Group similar memories
        groups: Dict[str, List[Memory]] = defaultdict(list)
        
        for memory in memories:
            # Simple grouping by first few words
            key = " ".join(memory.content.lower().split()[:3])
            groups[key].append(memory)
        
        # Merge groups with multiple memories
        for key, group in groups.items():
            if len(group) > 1:
                # Keep highest priority, delete others
                group.sort(key=lambda m: m.priority.value, reverse=True)
                for memory in group[1:]:
                    self.store.delete(memory.id)
        
        logger.info(f"Consolidated memories for user {user_id}")
    
    def forget(
        self,
        memory_id: Optional[str] = None,
        user_id: Optional[str] = None,
        older_than: Optional[timedelta] = None
    ):
        """
        Forget (delete) memories
        
        Args:
            memory_id: Specific memory to delete
            user_id: Delete all user memories
            older_than: Delete memories older than this
        """
        if memory_id:
            self.store.delete(memory_id)
            logger.info(f"Forgot memory: {memory_id}")
        
        elif user_id:
            memories = self.store.get_by_user(user_id)
            for memory in memories:
                self.store.delete(memory.id)
            logger.info(f"Forgot all memories for user: {user_id}")
        
        elif older_than:
            cutoff = datetime.now() - older_than
            for memory in self.store.get_all():
                created = datetime.fromisoformat(memory.created_at)
                if created < cutoff:
                    self.store.delete(memory.id)
            logger.info(f"Forgot memories older than {older_than}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        memories = self.store.get_all()
        
        type_counts = defaultdict(int)
        priority_counts = defaultdict(int)
        
        for memory in memories:
            type_counts[memory.memory_type.value] += 1
            priority_counts[memory.priority.name] += 1
        
        return {
            "total_memories": len(memories),
            "by_type": dict(type_counts),
            "by_priority": dict(priority_counts),
            "unique_users": len(set(m.user_id for m in memories if m.user_id)),
            "unique_sessions": len(set(m.session_id for m in memories if m.session_id))
        }


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def get_memory_manager(
    llm_caller=None,
    embedder=None
) -> Mem0MemoryManager:
    """Create a Mem0 memory manager instance"""
    return Mem0MemoryManager(llm_caller=llm_caller, embedder=embedder)
