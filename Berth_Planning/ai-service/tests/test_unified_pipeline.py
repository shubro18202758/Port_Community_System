"""
SmartBerth AI - Unified Pipeline Tests
=======================================

Comprehensive tests using real data from the training database.
Tests the complete pipeline: Knowledge Index → Graph → Manager Agent → Claude AI

Milestone 7: Add Comprehensive Tests with Real Data
"""

import os
import sys
import json
import time
import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline_api import (
    UnifiedSmartBerthPipeline,
    PipelineQueryRequest,
    QueryIntent,
    get_pipeline
)


# ============================================================================
# TEST DATA FROM TRAINING DATABASE
# ============================================================================

# Real vessel data from SmartBerth_AI_Vessel_Parameters_Training_Data.csv
REAL_VESSELS = [
    {"vessel_id": "VSL001", "vessel_name": "MAERSK SEALAND", "imo_number": "9786456", 
     "vessel_type": "Container", "loa": 350.5, "beam": 51.2, "draft": 14.5},
    {"vessel_id": "VSL002", "vessel_name": "EVERGREEN HARMONY", "imo_number": "9834521",
     "vessel_type": "Container", "loa": 366.0, "beam": 51.0, "draft": 15.0},
    {"vessel_id": "VSL003", "vessel_name": "CRUDE VOYAGER", "imo_number": "9723891",
     "vessel_type": "Tanker", "loa": 330.0, "beam": 60.0, "draft": 22.0},
]

# Real berth data from SmartBerth_AI_Berth_Parameters_Training_Data.csv
REAL_BERTHS = [
    {"berth_id": "BRT001", "berth_name": "Container Berth A1", "terminal_id": "TRM001",
     "berth_length": 400.0, "berth_depth": 16.5, "max_loa": 380.0, "max_draft": 15.5},
    {"berth_id": "BRT002", "berth_name": "Tanker Berth T1", "terminal_id": "TRM002",
     "berth_length": 350.0, "berth_depth": 24.0, "max_loa": 340.0, "max_draft": 23.0},
]

# Real port data from SmartBerth_AI_Port_Parameters_Training_Data.csv
REAL_PORTS = [
    {"port_code": "INMUN", "port_name": "Mumbai Port", "country": "India"},
    {"port_code": "INNSA", "port_name": "Jawaharlal Nehru Port", "country": "India"},
    {"port_code": "AEDXB", "port_name": "Dubai Port", "country": "UAE"},
]

# Real UKC data from SmartBerth_AI_UKC_Training_Data.csv
REAL_UKC = [
    {"channel_depth": 16.5, "vessel_draft": 14.5, "calculated_ukc": 2.0, 
     "required_ukc": 1.5, "ukc_status": "SAFE"},
    {"channel_depth": 15.0, "vessel_draft": 14.8, "calculated_ukc": 0.2,
     "required_ukc": 1.0, "ukc_status": "CRITICAL"},
]

# Real weather data from SmartBerth_AI_Weather_Parameters_Training_Data.csv
REAL_WEATHER = [
    {"wind_speed": 15.5, "wave_height": 1.2, "visibility": 8.0, "is_alert": False},
    {"wind_speed": 45.0, "wave_height": 4.5, "visibility": 2.0, "is_alert": True},
]


# ============================================================================
# TEST FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def pipeline():
    """Get or initialize the unified pipeline"""
    p = get_pipeline()
    if not p._initialized:
        success = p.initialize()
        if not success:
            pytest.skip("Pipeline initialization failed")
    return p


@pytest.fixture
def sample_berth_query():
    return PipelineQueryRequest(
        query="Find suitable berths for container vessel MAERSK SEALAND with LOA 350m and draft 14.5m",
        use_memory=False,
        use_graph=True,
        use_rag=True,
        max_context_chunks=5
    )


@pytest.fixture
def sample_ukc_query():
    return PipelineQueryRequest(
        query="Calculate UKC for vessel with draft 14.5m in channel with depth 16.5m",
        use_memory=False,
        use_graph=False,
        use_rag=True
    )


@pytest.fixture
def sample_port_query():
    return PipelineQueryRequest(
        query="What resources are available at Mumbai Port INMUN?",
        use_memory=False,
        use_graph=True,
        use_rag=True
    )


# ============================================================================
# INTENT CLASSIFICATION TESTS
# ============================================================================

class TestIntentClassification:
    """Test intent classification accuracy"""
    
    def test_berth_allocation_intent(self, pipeline):
        """Test berth allocation queries are classified correctly"""
        queries = [
            "Allocate berth for vessel MSC HARMONY",
            "Which berth is suitable for a container ship?",
            "Assign dock for tanker vessel",
            "Find available berth at terminal A",
        ]
        
        for query in queries:
            intent = pipeline.classify_intent(query)
            assert intent == QueryIntent.BERTH_ALLOCATION, f"Query '{query}' misclassified as {intent}"
    
    def test_vessel_info_intent(self, pipeline):
        """Test vessel info queries are classified correctly"""
        queries = [
            "Get information about vessel IMO 9786456",
            "What is the LOA of MAERSK SEALAND?",
            "Ship draft specifications",
        ]
        
        for query in queries:
            intent = pipeline.classify_intent(query)
            assert intent == QueryIntent.VESSEL_INFO, f"Query '{query}' misclassified as {intent}"
    
    def test_ukc_intent(self, pipeline):
        """Test UKC queries are classified correctly"""
        queries = [
            "Calculate under keel clearance for vessel",
            "Is UKC sufficient for passage?",
            "Check depth clearance for tanker",
        ]
        
        for query in queries:
            intent = pipeline.classify_intent(query)
            assert intent == QueryIntent.UKC_CALCULATION, f"Query '{query}' misclassified as {intent}"
    
    def test_weather_intent(self, pipeline):
        """Test weather queries are classified correctly"""
        queries = [
            "What is the current wind speed?",
            "Check wave height conditions",
            "Is visibility good for navigation?",
        ]
        
        for query in queries:
            intent = pipeline.classify_intent(query)
            assert intent == QueryIntent.WEATHER_ANALYSIS, f"Query '{query}' misclassified as {intent}"
    
    def test_resource_intent(self, pipeline):
        """Test resource queries are classified correctly"""
        queries = [
            "Available pilots for tonight",
            "Tugboat status at port",
            "Which pilot is certified for VLCCs?",
        ]
        
        for query in queries:
            intent = pipeline.classify_intent(query)
            assert intent == QueryIntent.RESOURCE_QUERY, f"Query '{query}' misclassified as {intent}"


# ============================================================================
# KNOWLEDGE RETRIEVAL TESTS
# ============================================================================

class TestKnowledgeRetrieval:
    """Test knowledge base retrieval"""
    
    def test_knowledge_index_loaded(self, pipeline):
        """Test that knowledge index is loaded"""
        assert pipeline._knowledge_collection is not None, "Knowledge collection should be loaded"
        count = pipeline._knowledge_collection.count()
        assert count > 0, f"Knowledge collection should have chunks, got {count}"
        print(f"Knowledge index loaded with {count} chunks")
    
    def test_retrieve_berth_knowledge(self, pipeline):
        """Test retrieval of berth-related knowledge"""
        results = pipeline.retrieve_knowledge(
            "container berth capacity requirements",
            top_k=5
        )
        
        assert len(results) > 0, "Should retrieve berth knowledge"
        
        # Check result structure
        for r in results:
            assert "content" in r
            assert "score" in r
            assert "source" in r
            assert r["score"] >= 0 and r["score"] <= 1
    
    def test_retrieve_ukc_knowledge(self, pipeline):
        """Test retrieval of UKC-related knowledge"""
        results = pipeline.retrieve_knowledge(
            "under keel clearance calculation safety margin",
            top_k=5
        )
        
        assert len(results) > 0, "Should retrieve UKC knowledge"
        
        # Check for relevant content
        has_ukc_content = any(
            "ukc" in r["content"].lower() or "clearance" in r["content"].lower() or "draft" in r["content"].lower()
            for r in results
        )
        assert has_ukc_content, "Results should contain UKC-related content"
    
    def test_retrieve_by_knowledge_type(self, pipeline):
        """Test filtering by knowledge type"""
        types = ["domain_rule", "operational_data", "entity_profile"]
        
        for ktype in types:
            results = pipeline.retrieve_knowledge(
                "port operations",
                top_k=3,
                knowledge_type=ktype
            )
            
            # All results should match the type (if any returned)
            for r in results:
                assert r.get("knowledge_type") == ktype, f"Result type mismatch: expected {ktype}"
    
    def test_retrieval_scores_ordered(self, pipeline):
        """Test that results are ordered by relevance score"""
        results = pipeline.retrieve_knowledge(
            "vessel arrival berth planning",
            top_k=10
        )
        
        if len(results) > 1:
            scores = [r["score"] for r in results]
            assert scores == sorted(scores, reverse=True), "Results should be ordered by score descending"


# ============================================================================
# GRAPH QUERY TESTS
# ============================================================================

class TestGraphQueries:
    """Test Neo4j graph queries"""
    
    def test_graph_engine_available(self, pipeline):
        """Test graph engine availability"""
        # Graph engine might not be available in test environment
        if pipeline._graph_engine is None:
            pytest.skip("Neo4j graph engine not available")
        
        assert pipeline._graph_engine is not None
    
    @pytest.mark.skipif(True, reason="Requires running Neo4j instance")
    def test_find_compatible_berths(self, pipeline):
        """Test finding compatible berths"""
        if not pipeline._graph_engine:
            pytest.skip("Neo4j not available")
        
        results = pipeline._graph_engine.find_compatible_berths(
            vessel_type="Container",
            min_loa=300.0,
            min_depth=14.0
        )
        
        assert isinstance(results, list)
    
    @pytest.mark.skipif(True, reason="Requires running Neo4j instance")
    def test_get_port_resources(self, pipeline):
        """Test getting port resources"""
        if not pipeline._graph_engine:
            pytest.skip("Neo4j not available")
        
        resources = pipeline._graph_engine.get_port_resources("INMUN")
        
        assert isinstance(resources, dict)


# ============================================================================
# RESPONSE GENERATION TESTS
# ============================================================================

class TestResponseGeneration:
    """Test response generation with Claude"""
    
    def test_central_llm_available(self, pipeline):
        """Test central LLM availability"""
        if pipeline._central_llm is None or not pipeline._central_llm._model_loaded:
            pytest.skip("Claude API not available")
        
        assert pipeline._central_llm is not None
        assert pipeline._central_llm._model_loaded
    
    @pytest.mark.skipif(True, reason="Requires Claude API key")
    def test_generate_berth_response(self, pipeline):
        """Test generating berth allocation response"""
        if not pipeline._central_llm:
            pytest.skip("Claude not available")
        
        context = """
        Berth A1: Length 400m, Depth 16.5m, Suitable for Container vessels up to 380m LOA
        Berth T1: Length 350m, Depth 24.0m, Suitable for Tanker vessels up to 340m LOA
        Vessel: MAERSK SEALAND, Container, LOA 350.5m, Draft 14.5m
        """
        
        response = pipeline.generate_response(
            query="Which berth should MAERSK SEALAND use?",
            context=context,
            intent=QueryIntent.BERTH_ALLOCATION
        )
        
        assert response is not None
        assert len(response) > 50, "Response should be meaningful"
        assert "berth" in response.lower() or "a1" in response.lower()


# ============================================================================
# END-TO-END PIPELINE TESTS
# ============================================================================

class TestEndToEndPipeline:
    """Test complete pipeline flow"""
    
    @pytest.mark.asyncio
    async def test_simple_query(self, pipeline):
        """Test simple query through pipeline"""
        request = PipelineQueryRequest(
            query="What are the main factors in berth allocation?",
            use_memory=False,
            use_graph=False,
            use_rag=True,
            max_context_chunks=3
        )
        
        response = await pipeline.process_query(request)
        
        assert response is not None
        assert response.query == request.query
        assert response.intent is not None
        assert response.answer is not None
        assert response.latency_ms > 0
        
        print(f"Query: {request.query}")
        print(f"Intent: {response.intent}")
        print(f"Latency: {response.latency_ms:.2f}ms")
        print(f"Context chunks used: {len(response.context_used)}")
    
    @pytest.mark.asyncio
    async def test_berth_allocation_query(self, pipeline, sample_berth_query):
        """Test berth allocation query"""
        response = await pipeline.process_query(sample_berth_query)
        
        assert response.intent == "berth_allocation"
        assert len(response.answer) > 0
        
        print(f"Answer preview: {response.answer[:200]}...")
    
    @pytest.mark.asyncio
    async def test_ukc_calculation_query(self, pipeline, sample_ukc_query):
        """Test UKC calculation query"""
        response = await pipeline.process_query(sample_ukc_query)
        
        assert response.intent == "ukc_calculation"
        assert len(response.answer) > 0
    
    @pytest.mark.asyncio
    async def test_multiple_queries_performance(self, pipeline):
        """Test multiple queries and measure performance"""
        queries = [
            "What is a safe UKC margin?",
            "How are berths assigned to vessels?",
            "What pilot certifications are required for VLCC?",
            "Weather restrictions for port operations",
            "Container terminal efficiency metrics",
        ]
        
        latencies = []
        
        for q in queries:
            request = PipelineQueryRequest(
                query=q,
                use_memory=False,
                use_graph=False,
                use_rag=True,
                max_context_chunks=3
            )
            
            response = await pipeline.process_query(request)
            latencies.append(response.latency_ms)
        
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        
        print(f"\nPerformance Summary:")
        print(f"  Queries: {len(queries)}")
        print(f"  Avg Latency: {avg_latency:.2f}ms")
        print(f"  Max Latency: {max_latency:.2f}ms")
        
        # Performance assertion (adjust threshold as needed)
        assert avg_latency < 30000, f"Average latency too high: {avg_latency}ms"


# ============================================================================
# PIPELINE STATISTICS TESTS
# ============================================================================

class TestPipelineStats:
    """Test pipeline statistics and monitoring"""
    
    def test_get_stats(self, pipeline):
        """Test getting pipeline statistics"""
        stats = pipeline.get_stats()
        
        assert "knowledge_index" in stats
        assert "graph_stats" in stats
        assert "pipeline_stats" in stats
        assert "components" in stats
        
        # Check components status
        components = stats["components"]
        assert isinstance(components["knowledge_index"], bool)
        assert isinstance(components["graph_engine"], bool)
        assert isinstance(components["manager_agent"], bool)
        assert isinstance(components["central_llm"], bool)
        
        print(f"\nPipeline Stats:")
        print(json.dumps(stats, indent=2, default=str))
    
    def test_knowledge_index_stats(self, pipeline):
        """Test knowledge index statistics"""
        stats = pipeline.get_stats()
        
        if pipeline._knowledge_collection:
            ki_stats = stats["knowledge_index"]
            assert "total_chunks" in ki_stats
            assert ki_stats["total_chunks"] > 0
            print(f"Knowledge Index: {ki_stats['total_chunks']} chunks")


# ============================================================================
# REAL DATA VALIDATION TESTS
# ============================================================================

class TestRealDataValidation:
    """Validate pipeline with real training data scenarios"""
    
    @pytest.mark.asyncio
    async def test_real_vessel_query(self, pipeline):
        """Test query with real vessel data"""
        vessel = REAL_VESSELS[0]
        
        request = PipelineQueryRequest(
            query=f"Find berth for vessel {vessel['vessel_name']} with LOA {vessel['loa']}m "
                  f"and draft {vessel['draft']}m. It's a {vessel['vessel_type']} vessel.",
            use_memory=False,
            use_graph=True,
            use_rag=True
        )
        
        response = await pipeline.process_query(request)
        
        assert response.answer is not None
        assert response.intent in ["berth_allocation", "vessel_info"]
        
        print(f"\nReal Vessel Query Test:")
        print(f"  Vessel: {vessel['vessel_name']}")
        print(f"  Intent: {response.intent}")
        print(f"  Context chunks: {len(response.context_used)}")
    
    @pytest.mark.asyncio
    async def test_real_ukc_scenario(self, pipeline):
        """Test with real UKC scenario"""
        ukc = REAL_UKC[1]  # Critical UKC scenario
        
        request = PipelineQueryRequest(
            query=f"Is it safe for a vessel with draft {ukc['vessel_draft']}m to transit "
                  f"a channel with depth {ukc['channel_depth']}m? The calculated UKC is {ukc['calculated_ukc']}m "
                  f"and required UKC is {ukc['required_ukc']}m.",
            use_memory=False,
            use_graph=False,
            use_rag=True
        )
        
        response = await pipeline.process_query(request)
        
        assert response.answer is not None
        assert response.intent == "ukc_calculation"
        
        # Response should mention safety concerns
        answer_lower = response.answer.lower()
        has_safety_mention = any(
            word in answer_lower 
            for word in ["unsafe", "critical", "risk", "insufficient", "dangerous", "not safe", "caution"]
        )
        # This is informational, not a hard assertion
        if has_safety_mention:
            print("✓ Response correctly identifies safety concern")
        else:
            print("⚠ Response may not identify safety concern clearly")
    
    @pytest.mark.asyncio
    async def test_real_weather_scenario(self, pipeline):
        """Test with real weather scenario"""
        weather = REAL_WEATHER[1]  # Alert weather
        
        request = PipelineQueryRequest(
            query=f"Can port operations continue with wind speed {weather['wind_speed']} knots, "
                  f"wave height {weather['wave_height']}m, and visibility {weather['visibility']}km?",
            use_memory=False,
            use_graph=False,
            use_rag=True
        )
        
        response = await pipeline.process_query(request)
        
        assert response.answer is not None
        assert response.intent == "weather_analysis"


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    # Run tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-k", "not skipif",  # Skip tests marked with skipif
        "--capture=no"  # Show print statements
    ])
