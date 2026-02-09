"""
GraphRAG - Graph-Enhanced Retrieval Augmented Generation
=========================================================

Implements Microsoft GraphRAG-style graph-enhanced retrieval:
- Entity Extraction: Extract entities from documents
- Relationship Mapping: Build knowledge graph from text
- Community Detection: Find clusters of related entities
- Global Search: Answer questions requiring broad context
- Local Search: Answer questions about specific entities

Integrates with Neo4j for graph storage and traversal.
"""

import logging
import json
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Entity:
    """An extracted entity from text"""
    id: str
    name: str
    type: str  # VESSEL, BERTH, PORT, TERMINAL, CARGO, etc.
    description: str = ""
    source_chunks: List[str] = field(default_factory=list)
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relationship:
    """A relationship between entities"""
    id: str
    source_id: str
    target_id: str
    type: str  # DOCKS_AT, CARRIES, OPERATES, REQUIRES, etc.
    description: str = ""
    weight: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Community:
    """A community of related entities"""
    id: str
    name: str
    description: str
    entity_ids: List[str]
    summary: str = ""
    level: int = 0  # Hierarchy level


@dataclass
class GraphRAGIndex:
    """Complete GraphRAG index"""
    entities: Dict[str, Entity]
    relationships: Dict[str, Relationship]
    communities: Dict[str, Community]
    entity_embeddings: Dict[str, List[float]] = field(default_factory=dict)
    community_summaries: Dict[str, str] = field(default_factory=dict)
    build_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


# ============================================================================
# ENTITY EXTRACTION
# ============================================================================

class EntityExtractor:
    """
    Extract entities from text using LLM.
    Identifies domain-specific entities for SmartBerth.
    """
    
    # SmartBerth entity types
    ENTITY_TYPES = [
        "VESSEL", "BERTH", "PORT", "TERMINAL", "CARGO",
        "PILOT", "TUGBOAT", "CHANNEL", "ANCHORAGE",
        "ORGANIZATION", "REGULATION", "CONSTRAINT"
    ]
    
    def __init__(self, llm_caller):
        self.llm_caller = llm_caller
        self.entity_cache: Dict[str, List[Entity]] = {}
    
    def _get_chunk_id(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def extract(self, text: str, use_cache: bool = True) -> List[Entity]:
        """
        Extract entities from text chunk
        
        Args:
            text: Text to extract entities from
            use_cache: Use cached results if available
            
        Returns:
            List of extracted entities
        """
        chunk_id = self._get_chunk_id(text)
        
        if use_cache and chunk_id in self.entity_cache:
            return self.entity_cache[chunk_id]
        
        prompt = f"""Extract all named entities from this maritime/port operations text.

TEXT:
{text[:2000]}

ENTITY TYPES: {', '.join(self.ENTITY_TYPES)}

Extract entities in JSON format:
[
  {{"name": "entity name", "type": "ENTITY_TYPE", "description": "brief description"}}
]

Only extract clearly identifiable entities. Output JSON array only:"""

        response = self.llm_caller(prompt)
        
        entities = []
        try:
            # Parse JSON response
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                data = json.loads(response[start:end])
                
                for item in data:
                    entity = Entity(
                        id=f"ent_{hashlib.md5(item['name'].encode()).hexdigest()[:8]}",
                        name=item.get("name", ""),
                        type=item.get("type", "UNKNOWN"),
                        description=item.get("description", ""),
                        source_chunks=[chunk_id]
                    )
                    entities.append(entity)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse entity extraction: {e}")
        
        self.entity_cache[chunk_id] = entities
        return entities


class RelationshipExtractor:
    """
    Extract relationships between entities.
    """
    
    # SmartBerth relationship types
    RELATIONSHIP_TYPES = [
        "DOCKS_AT", "CARRIES", "OPERATES_FROM", "REQUIRES",
        "SERVES", "CONNECTS_TO", "MANAGED_BY", "PART_OF",
        "CONFLICTS_WITH", "COMPATIBLE_WITH", "ALLOCATED_TO"
    ]
    
    def __init__(self, llm_caller):
        self.llm_caller = llm_caller
    
    def extract(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[Relationship]:
        """
        Extract relationships between entities in text
        
        Args:
            text: Source text
            entities: Entities found in text
            
        Returns:
            List of relationships
        """
        if len(entities) < 2:
            return []
        
        entity_list = "\n".join([f"- {e.name} ({e.type})" for e in entities[:20]])
        
        prompt = f"""Given these entities found in maritime/port text, identify relationships between them.

ENTITIES:
{entity_list}

TEXT:
{text[:1500]}

RELATIONSHIP TYPES: {', '.join(self.RELATIONSHIP_TYPES)}

Extract relationships in JSON format:
[
  {{"source": "entity1 name", "target": "entity2 name", "type": "REL_TYPE", "description": "brief description"}}
]

Output JSON array only:"""

        response = self.llm_caller(prompt)
        
        relationships = []
        entity_name_map = {e.name.lower(): e for e in entities}
        
        try:
            if "[" in response:
                start = response.index("[")
                end = response.rindex("]") + 1
                data = json.loads(response[start:end])
                
                for item in data:
                    source_name = item.get("source", "").lower()
                    target_name = item.get("target", "").lower()
                    
                    source_entity = entity_name_map.get(source_name)
                    target_entity = entity_name_map.get(target_name)
                    
                    if source_entity and target_entity:
                        rel = Relationship(
                            id=f"rel_{hashlib.md5(f'{source_entity.id}:{target_entity.id}'.encode()).hexdigest()[:8]}",
                            source_id=source_entity.id,
                            target_id=target_entity.id,
                            type=item.get("type", "RELATED_TO"),
                            description=item.get("description", "")
                        )
                        relationships.append(rel)
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse relationship extraction: {e}")
        
        return relationships


# ============================================================================
# COMMUNITY DETECTION
# ============================================================================

class CommunityDetector:
    """
    Detect communities of related entities using simple clustering.
    For full GraphRAG, would use Leiden algorithm.
    """
    
    def __init__(self, llm_caller=None):
        self.llm_caller = llm_caller
    
    def detect(
        self,
        entities: Dict[str, Entity],
        relationships: Dict[str, Relationship],
        min_community_size: int = 2
    ) -> List[Community]:
        """
        Detect communities from entity-relationship graph
        
        Args:
            entities: Entity dictionary
            relationships: Relationship dictionary
            min_community_size: Minimum entities per community
            
        Returns:
            List of detected communities
        """
        # Build adjacency list
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        for rel in relationships.values():
            adjacency[rel.source_id].add(rel.target_id)
            adjacency[rel.target_id].add(rel.source_id)
        
        # Simple connected components for communities
        visited = set()
        communities = []
        
        def dfs(entity_id: str, component: List[str]):
            if entity_id in visited:
                return
            visited.add(entity_id)
            component.append(entity_id)
            for neighbor in adjacency.get(entity_id, []):
                dfs(neighbor, component)
        
        for entity_id in entities:
            if entity_id not in visited:
                component = []
                dfs(entity_id, component)
                if len(component) >= min_community_size:
                    community = Community(
                        id=f"comm_{len(communities)}",
                        name=f"Community {len(communities)}",
                        description="",
                        entity_ids=component
                    )
                    communities.append(community)
        
        # Generate community names/descriptions using LLM if available
        if self.llm_caller:
            for community in communities[:10]:  # Limit for performance
                entity_names = [entities[eid].name for eid in community.entity_ids[:10] if eid in entities]
                if entity_names:
                    prompt = f"""Name this community of related maritime entities:
Entities: {', '.join(entity_names)}

Provide: {{"name": "short name", "description": "1-2 sentence description"}}"""
                    
                    response = self.llm_caller(prompt)
                    try:
                        if "{" in response:
                            data = json.loads(response[response.index("{"):response.rindex("}")+1])
                            community.name = data.get("name", community.name)
                            community.description = data.get("description", "")
                    except (json.JSONDecodeError, ValueError):
                        pass
        
        return communities


# ============================================================================
# SEARCH METHODS
# ============================================================================

class GraphRAGSearch:
    """
    Search methods for GraphRAG.
    """
    
    def __init__(
        self,
        index: GraphRAGIndex,
        llm_caller,
        embedding_model=None
    ):
        self.index = index
        self.llm_caller = llm_caller
        self.embedding_model = embedding_model
    
    def local_search(
        self,
        query: str,
        start_entities: List[str] = None,
        max_hops: int = 2,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Local search: Start from entities and traverse graph.
        Best for specific questions about particular entities.
        
        Args:
            query: Search query
            start_entities: Entity IDs to start from (auto-detected if None)
            max_hops: Max graph traversal depth
            max_results: Max results to return
            
        Returns:
            Search results with entities, relationships, and answer
        """
        # Auto-detect starting entities from query
        if not start_entities:
            start_entities = self._find_query_entities(query)
        
        # Traverse graph from starting entities
        collected_entities = set(start_entities)
        collected_rels = []
        
        frontier = set(start_entities)
        for hop in range(max_hops):
            new_frontier = set()
            for eid in frontier:
                # Find relationships involving this entity
                for rel in self.index.relationships.values():
                    if rel.source_id == eid:
                        collected_rels.append(rel)
                        new_frontier.add(rel.target_id)
                    elif rel.target_id == eid:
                        collected_rels.append(rel)
                        new_frontier.add(rel.source_id)
            
            collected_entities.update(new_frontier)
            frontier = new_frontier - collected_entities
            
            if len(collected_entities) >= max_results:
                break
        
        # Build context from collected graph elements
        context_parts = []
        for eid in list(collected_entities)[:max_results]:
            if eid in self.index.entities:
                e = self.index.entities[eid]
                context_parts.append(f"{e.name} ({e.type}): {e.description}")
        
        for rel in collected_rels[:max_results]:
            src = self.index.entities.get(rel.source_id)
            tgt = self.index.entities.get(rel.target_id)
            if src and tgt:
                context_parts.append(f"{src.name} --[{rel.type}]--> {tgt.name}")
        
        context = "\n".join(context_parts)
        
        # Generate answer using LLM
        answer_prompt = f"""Using this graph context about maritime entities, answer the question.

GRAPH CONTEXT:
{context}

QUESTION: {query}

Provide a specific answer based on the graph relationships:"""

        answer = self.llm_caller(answer_prompt)
        
        return {
            "query": query,
            "search_type": "local",
            "entities": [self.index.entities[eid] for eid in collected_entities if eid in self.index.entities],
            "relationships": collected_rels,
            "context": context,
            "answer": answer
        }
    
    def global_search(
        self,
        query: str,
        use_communities: bool = True,
        max_communities: int = 5
    ) -> Dict[str, Any]:
        """
        Global search: Use community summaries for broad questions.
        Best for questions requiring understanding of entire domain.
        
        Args:
            query: Search query
            use_communities: Whether to use community summaries
            max_communities: Max communities to include
            
        Returns:
            Search results with community context and answer
        """
        context_parts = []
        
        if use_communities and self.index.communities:
            # Use community summaries
            for comm_id, summary in list(self.index.community_summaries.items())[:max_communities]:
                if summary:
                    context_parts.append(f"[{comm_id}]: {summary}")
            
            # Also include community descriptions
            for comm in list(self.index.communities.values())[:max_communities]:
                if comm.description:
                    context_parts.append(f"{comm.name}: {comm.description}")
        else:
            # Fallback: sample entities across types
            type_samples: Dict[str, List[Entity]] = defaultdict(list)
            for entity in self.index.entities.values():
                type_samples[entity.type].append(entity)
            
            for etype, entities in type_samples.items():
                for e in entities[:3]:
                    context_parts.append(f"{e.name} ({e.type}): {e.description}")
        
        context = "\n".join(context_parts)
        
        # Generate answer using LLM with global context
        answer_prompt = f"""Using this high-level overview of the maritime domain, answer the question.

DOMAIN OVERVIEW:
{context}

QUESTION: {query}

Provide a comprehensive answer considering the broad context:"""

        answer = self.llm_caller(answer_prompt)
        
        return {
            "query": query,
            "search_type": "global",
            "communities_used": len(context_parts),
            "context": context,
            "answer": answer
        }
    
    def _find_query_entities(self, query: str) -> List[str]:
        """Find entities mentioned in query"""
        query_lower = query.lower()
        matching = []
        
        for entity in self.index.entities.values():
            if entity.name.lower() in query_lower:
                matching.append(entity.id)
        
        return matching[:5]  # Limit starting points


# ============================================================================
# MAIN GRAPHRAG ENGINE
# ============================================================================

class GraphRAGEngine:
    """
    Main GraphRAG engine integrating all components.
    
    Provides:
    - Index building from documents
    - Local and global search
    - Neo4j integration for persistence
    """
    
    def __init__(
        self,
        llm_caller,
        embedding_model=None,
        neo4j_driver=None
    ):
        """
        Initialize GraphRAG engine
        
        Args:
            llm_caller: Function to call LLM
            embedding_model: Embedding model for entity embeddings
            neo4j_driver: Neo4j driver for graph persistence
        """
        self.llm_caller = llm_caller
        self.embedding_model = embedding_model
        self.neo4j_driver = neo4j_driver
        
        self.entity_extractor = EntityExtractor(llm_caller)
        self.relationship_extractor = RelationshipExtractor(llm_caller)
        self.community_detector = CommunityDetector(llm_caller)
        
        self.index: Optional[GraphRAGIndex] = None
        self.search: Optional[GraphRAGSearch] = None
        
        logger.info("GraphRAGEngine initialized")
    
    def build_index(
        self,
        documents: List[Dict[str, Any]],
        generate_summaries: bool = True
    ) -> GraphRAGIndex:
        """
        Build GraphRAG index from documents
        
        Args:
            documents: List of documents with 'content' and optional 'metadata'
            generate_summaries: Generate community summaries
            
        Returns:
            Built GraphRAGIndex
        """
        logger.info(f"Building GraphRAG index from {len(documents)} documents")
        
        all_entities: Dict[str, Entity] = {}
        all_relationships: Dict[str, Relationship] = {}
        
        # Phase 1: Extract entities from all documents
        logger.info("Phase 1: Extracting entities...")
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            entities = self.entity_extractor.extract(content)
            
            for entity in entities:
                if entity.id in all_entities:
                    # Merge source chunks
                    all_entities[entity.id].source_chunks.extend(entity.source_chunks)
                else:
                    all_entities[entity.id] = entity
            
            if (i + 1) % 10 == 0:
                logger.info(f"  Processed {i+1}/{len(documents)} documents, {len(all_entities)} entities")
        
        # Phase 2: Extract relationships
        logger.info("Phase 2: Extracting relationships...")
        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            # Get entities for this document
            doc_entities = self.entity_extractor.extract(content, use_cache=True)
            relationships = self.relationship_extractor.extract(content, doc_entities)
            
            for rel in relationships:
                all_relationships[rel.id] = rel
        
        logger.info(f"  Extracted {len(all_relationships)} relationships")
        
        # Phase 3: Detect communities
        logger.info("Phase 3: Detecting communities...")
        communities = self.community_detector.detect(all_entities, all_relationships)
        community_dict = {c.id: c for c in communities}
        logger.info(f"  Found {len(communities)} communities")
        
        # Phase 4: Generate community summaries
        community_summaries = {}
        if generate_summaries:
            logger.info("Phase 4: Generating community summaries...")
            for community in communities[:20]:  # Limit for performance
                entity_names = [all_entities[eid].name for eid in community.entity_ids[:10] if eid in all_entities]
                if entity_names:
                    summary_prompt = f"""Summarize this community of maritime entities in 2-3 sentences:
Community: {community.name}
Entities: {', '.join(entity_names)}

Summary:"""
                    summary = self.llm_caller(summary_prompt)
                    community_summaries[community.id] = summary.strip()
        
        # Build index
        self.index = GraphRAGIndex(
            entities=all_entities,
            relationships=all_relationships,
            communities=community_dict,
            community_summaries=community_summaries
        )
        
        # Initialize search
        self.search = GraphRAGSearch(self.index, self.llm_caller, self.embedding_model)
        
        logger.info(f"GraphRAG index built: {len(all_entities)} entities, {len(all_relationships)} relationships, {len(communities)} communities")
        
        return self.index
    
    def local_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Perform local search"""
        if not self.search:
            raise RuntimeError("Index not built. Call build_index first.")
        return self.search.local_search(query, **kwargs)
    
    def global_search(self, query: str, **kwargs) -> Dict[str, Any]:
        """Perform global search"""
        if not self.search:
            raise RuntimeError("Index not built. Call build_index first.")
        return self.search.global_search(query, **kwargs)
    
    def query(self, query: str, search_type: str = "auto") -> Dict[str, Any]:
        """
        Query the graph with automatic search type selection
        
        Args:
            query: User query
            search_type: 'local', 'global', or 'auto'
            
        Returns:
            Search results
        """
        if search_type == "auto":
            # Heuristic: use local for specific entities, global for broad questions
            query_lower = query.lower()
            
            # Check if query mentions specific entities
            entity_mentions = sum(1 for e in self.index.entities.values() 
                                 if e.name.lower() in query_lower)
            
            # Check for broad question indicators
            broad_indicators = ["all", "overview", "general", "types of", "what are"]
            is_broad = any(ind in query_lower for ind in broad_indicators)
            
            if entity_mentions > 0 and not is_broad:
                search_type = "local"
            else:
                search_type = "global"
        
        if search_type == "local":
            return self.local_search(query)
        else:
            return self.global_search(query)
    
    def save_to_neo4j(self):
        """Persist graph to Neo4j"""
        if not self.neo4j_driver or not self.index:
            logger.warning("Neo4j driver not available or index not built")
            return
        
        with self.neo4j_driver.session() as session:
            # Create entities as nodes
            for entity in self.index.entities.values():
                session.run(
                    f"""MERGE (e:{entity.type} {{id: $id}})
                        SET e.name = $name, e.description = $description""",
                    id=entity.id,
                    name=entity.name,
                    description=entity.description
                )
            
            # Create relationships
            for rel in self.index.relationships.values():
                session.run(
                    f"""MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
                        MERGE (a)-[r:{rel.type}]->(b)
                        SET r.description = $description""",
                    source_id=rel.source_id,
                    target_id=rel.target_id,
                    description=rel.description
                )
        
        logger.info("Graph saved to Neo4j")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.index:
            return {"status": "not_built"}
        
        return {
            "status": "ready",
            "entities": len(self.index.entities),
            "relationships": len(self.index.relationships),
            "communities": len(self.index.communities),
            "entity_types": dict(defaultdict(int, [(e.type, 1) for e in self.index.entities.values()])),
            "build_timestamp": self.index.build_timestamp
        }


# Factory function
def get_graphrag_engine(llm_caller, embedding_model=None, neo4j_driver=None) -> GraphRAGEngine:
    """Create a GraphRAG engine instance"""
    return GraphRAGEngine(llm_caller=llm_caller, embedding_model=embedding_model, neo4j_driver=neo4j_driver)
