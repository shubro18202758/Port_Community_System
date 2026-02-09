"""
SmartBerth AI Service - RAG Pipeline
Retrieval Augmented Generation for explainable AI decisions
Uses ChromaDB directly for faster loading
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import os

# Use ChromaDB directly instead of langchain wrappers for faster loading
import chromadb
from sentence_transformers import SentenceTransformer

from config import get_settings
from database import get_db_service
from model import get_model

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG Pipeline for SmartBerth AI
    Provides context-aware explanations for AI decisions
    Uses ChromaDB directly for faster loading
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.db = get_db_service()
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """Initialize the RAG pipeline with embeddings and ChromaDB"""
        try:
            logger.info(f"Initializing RAG with embedding model: {self.settings.embedding_model}")
            
            # Initialize sentence transformer for embeddings
            self.embedding_model = SentenceTransformer(self.settings.embedding_model)
            
            # Initialize ChromaDB client
            chroma_path = os.path.join(os.path.dirname(__file__), "chroma_db_new")
            self.chroma_client = chromadb.PersistentClient(path=chroma_path)
            
            # Get the collection
            try:
                self.collection = self.chroma_client.get_collection("smartberth_knowledge")
                doc_count = self.collection.count()
                logger.info(f"Loaded existing ChromaDB collection with {doc_count} documents")
            except Exception as e:
                logger.warning(f"No existing collection found: {e}")
                self.collection = self.chroma_client.create_collection(
                    name="smartberth_knowledge",
                    metadata={"description": "SmartBerth AI Domain Knowledge"}
                )
                logger.info("Created new ChromaDB collection")
            
            self._initialized = True
            logger.info("RAG pipeline initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def retrieve(self, query: str, n_results: int = 5, category: str = None) -> List[Dict]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: The search query
            n_results: Number of results to return
            category: Optional category filter
            
        Returns:
            List of relevant document chunks with metadata
        """
        if not self._initialized:
            logger.warning("RAG pipeline not initialized, initializing now...")
            if not self.initialize():
                return []
        
        try:
            # Encode the query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Build where clause for category filter
            where = None
            if category:
                where = {"category": category}
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            documents = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    documents.append({
                        'content': doc,
                        'metadata': metadata,
                        'relevance_score': 1 - distance,  # Convert distance to similarity
                        'source': metadata.get('source_file', 'unknown')
                    })
            
            logger.info(f"Retrieved {len(documents)} documents for query: {query[:50]}...")
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def get_context_for_query(self, query: str, max_tokens: int = 4000) -> str:
        """
        Get concatenated context from relevant documents
        
        Args:
            query: The search query
            max_tokens: Maximum context length (approximate)
            
        Returns:
            Formatted context string
        """
        documents = self.retrieve(query, n_results=10)
        
        context_parts = []
        current_length = 0
        
        for doc in documents:
            doc_text = f"[Source: {doc['source']}]\n{doc['content']}\n"
            doc_length = len(doc_text.split())
            
            if current_length + doc_length > max_tokens:
                break
                
            context_parts.append(doc_text)
            current_length += doc_length
        
        return "\n---\n".join(context_parts)
    
    def add_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """Add a new document to the knowledge base"""
        if not self._initialized:
            logger.error("RAG pipeline not initialized")
            return False
        
        try:
            # Generate embedding for the document
            embedding = self.embedding_model.encode(content).tolist()
            
            # Add to collection
            doc_id = f"doc_{self.collection.count()}"
            self.collection.add(
                ids=[doc_id],
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False
    
    def retrieve_context(
        self, 
        query: str, 
        k: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query"""
        if not self._initialized:
            logger.warning("RAG pipeline not initialized, returning empty context")
            return []
        
        try:
            # Build filter if category specified
            where = None
            if category:
                where = {"category": category}
            
            # Encode query
            query_embedding = self.embedding_model.encode(query).tolist()
            
            # Search ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where,
                include=["documents", "metadatas", "distances"]
            )
            
            context = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 0
                    context.append({
                        'content': doc,
                        'metadata': metadata,
                        'relevance_score': round(1 - distance, 3)  # Convert distance to similarity
                    })
            
            return context
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return []
    
    def generate_explanation(
        self,
        query: str,
        context_category: Optional[str] = None,
        additional_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate an AI explanation using RAG
        """
        # Retrieve relevant context
        retrieved_context = self.retrieve_context(query, k=3, category=context_category)
        
        # Build context string
        context_parts = []
        for ctx in retrieved_context:
            context_parts.append(ctx['content'])
        
        if additional_context:
            context_parts.append(f"Current Situation:\n{additional_context}")
        
        context_string = "\n\n---\n\n".join(context_parts)
        
        # Generate explanation using AI model
        model = get_model()
        
        system_prompt = """You are SmartBerth AI, an intelligent maritime operations assistant.
Your role is to explain berth planning decisions clearly and professionally.
Use the provided context to give accurate, factual explanations.
Keep responses concise but informative. Focus on the key factors affecting the decision."""
        
        prompt = f"""Based on the following knowledge:

{context_string}

Please explain: {query}

Provide a clear, professional explanation focusing on the key factors."""
        
        try:
            if model.model is not None:
                result = model.generate_text(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=300,
                    temperature=0.5
                )
                
                if result.get("success"):
                    return {
                        "success": True,
                        "explanation": result.get("text", ""),
                        "context_used": [c['metadata'].get('title', 'Unknown') for c in retrieved_context],
                        "model": model.settings.claude_model
                    }
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
        
        # Fallback: Return context summary
        return {
            "success": True,
            "explanation": f"Based on port operations guidelines: {context_parts[0][:500] if context_parts else 'No specific context available.'}",
            "context_used": [c['metadata'].get('title', 'Unknown') for c in retrieved_context],
            "model": "rule-based-fallback"
        }
    
    def explain_eta_prediction(
        self,
        vessel_name: str,
        predicted_eta: str,
        original_eta: str,
        deviation_minutes: int,
        factors: Dict[str, Any]
    ) -> str:
        """Generate explanation for ETA prediction"""
        query = f"Why is the ETA for vessel {vessel_name} predicted to be {deviation_minutes} minutes {'late' if deviation_minutes > 0 else 'early'}?"
        
        additional_context = f"""
        Vessel: {vessel_name}
        Original ETA: {original_eta}
        Predicted ETA: {predicted_eta}
        Deviation: {deviation_minutes} minutes
        Distance to Port: {factors.get('distance_to_port', 'N/A')} NM
        Current Speed: {factors.get('current_speed', 'N/A')} knots
        Weather Impact: {factors.get('weather_impact', 1.0)}
        Prediction Method: {factors.get('prediction_method', 'Unknown')}
        """
        
        result = self.generate_explanation(
            query=query,
            context_category="prediction",
            additional_context=additional_context
        )
        
        return result.get("explanation", "Unable to generate explanation.")
    
    def explain_berth_allocation(
        self,
        vessel_name: str,
        berth_name: str,
        score: float,
        violations: List[Dict[str, Any]]
    ) -> str:
        """Generate explanation for berth allocation decision"""
        query = f"Why was {berth_name} {'recommended' if score > 70 else 'scored low'} for vessel {vessel_name}?"
        
        violation_text = ""
        if violations:
            violation_text = "\nConstraint Issues:\n" + "\n".join(
                f"- {v.get('description', 'Unknown')}" for v in violations[:3]
            )
        
        additional_context = f"""
        Vessel: {vessel_name}
        Berth: {berth_name}
        Allocation Score: {score}/100
        {violation_text}
        """
        
        result = self.generate_explanation(
            query=query,
            context_category="operations",
            additional_context=additional_context
        )
        
        return result.get("explanation", "Unable to generate explanation.")
    
    def explain_conflict(
        self,
        conflict_type: str,
        vessels_involved: List[str],
        resolution_options: List[str]
    ) -> str:
        """Generate explanation for conflict and resolution"""
        query = f"How should a {conflict_type} conflict between {', '.join(vessels_involved)} be resolved?"
        
        additional_context = f"""
        Conflict Type: {conflict_type}
        Vessels Involved: {', '.join(vessels_involved)}
        Available Options: {', '.join(resolution_options)}
        """
        
        result = self.generate_explanation(
            query=query,
            context_category="conflicts",
            additional_context=additional_context
        )
        
        return result.get("explanation", "Unable to generate explanation.")


# Global RAG pipeline instance
rag_pipeline = RAGPipeline()


def get_rag_pipeline() -> RAGPipeline:
    """Get the global RAG pipeline instance"""
    return rag_pipeline
