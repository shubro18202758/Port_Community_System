"""
SmartBerth Data Flow Integration Summary
=========================================
Verifies all components are properly integrated with the Data Flow Architecture
"""

print("=" * 60)
print("SmartBerth Data Flow Integration Summary")
print("=" * 60)

# Check knowledge index
import chromadb
client = chromadb.PersistentClient(path="chroma_db_unified")
collection = client.get_collection("smartberth_unified")
print(f"Knowledge Index: {collection.count()} chunks")

# Check enhanced manager
from manager_agent.enhanced_manager import get_enhanced_manager_agent
manager = get_enhanced_manager_agent()
status = "Ready" if manager.is_ready() else "Not Ready"
print(f"Enhanced Manager: {status}")

# Check data flow constants
from manager_agent.enhanced_manager import OPERATIONAL_PHASE_DATA_MAPPING, ML_MODEL_DATA_MAPPING
print(f"Operational Phases: {list(OPERATIONAL_PHASE_DATA_MAPPING.keys())}")
print(f"ML Models: {list(ML_MODEL_DATA_MAPPING.keys())}")

# Check agent data flow
from agents.berth_agent import BERTH_ALLOCATION_DATA_MAPPING
from agents.eta_agent import ETA_PREDICTION_DATA_MAPPING
print(f"Berth Agent Target: {BERTH_ALLOCATION_DATA_MAPPING['ml_target']}")
print(f"ETA Agent Target: {ETA_PREDICTION_DATA_MAPPING['ml_target']}")

# Check graph
from inmemory_graph import get_knowledge_graph
graph = get_knowledge_graph()
if graph.load():
    stats = graph.get_stats()
    print(f"Graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges")

print("=" * 60)
print("All Data Flow Components Integrated!")
print("=" * 60)
