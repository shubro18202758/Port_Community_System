"""
Test Data Flow Context Integration
==================================
Verifies that the enhanced manager and pipeline correctly use
the SmartBerth Data Flow Architecture mappings.
"""

from manager_agent.enhanced_manager import get_enhanced_manager_agent

def test_data_flow_context():
    """Test enhanced manager data flow context"""
    print("=" * 60)
    print("Testing Data Flow Context Integration")
    print("=" * 60)
    
    manager = get_enhanced_manager_agent()
    if not manager.is_ready():
        print("ERROR: Enhanced Manager not ready")
        return False
    
    print("✓ Enhanced Manager ready\n")
    
    # Test queries for different operational phases
    test_queries = [
        ("Find suitable berths for container vessel with LOA 350m", "berth_allocation"),
        ("Calculate UKC for vessel with 14m draft in channel SGSIN-CH01", "ukc_calculation"),
        ("Check pilot availability for tomorrow morning", "resource_query"),
        ("What's the weather forecast for Singapore port?", "weather_analysis"),
        ("Show vessel history for IMO 9876543", "vessel_info"),
    ]
    
    all_passed = True
    for query, expected_type in test_queries:
        print(f"Query: {query[:50]}...")
        
        result = manager.process_query(query)
        task_type = result.get("task_type", "UNKNOWN")
        confidence = result.get("confidence", 0)
        ctx = result.get("data_flow_context", {})
        
        print(f"  Task Type: {task_type}")
        print(f"  Confidence: {confidence:.2f}")
        
        # Extract phase info (could be dict or string)
        phase_info = ctx.get("operational_phase", "N/A")
        if isinstance(phase_info, dict):
            phase_name = phase_info.get("phase", "unknown")
            phase_datasets = phase_info.get("datasets", [])
            print(f"  Operational Phase: {phase_name}")
            if phase_datasets:
                print(f"  Phase Datasets: {', '.join(phase_datasets[:4])}...")
        else:
            print(f"  Operational Phase: {phase_info}")
        
        # Extract ML model info
        ml_info = ctx.get("ml_model")
        if ml_info and isinstance(ml_info, dict):
            print(f"  ML Model: {ml_info.get('model', 'N/A')}")
            print(f"  Target: {ml_info.get('target', 'N/A')}")
        
        entities = ctx.get("entity_relationships", {})
        if entities:
            print(f"  Entity Context: {list(entities.keys())[:3]}")
        
        if not ctx:
            print("  WARNING: No data flow context returned")
            all_passed = False
        
        print()
    
    print("=" * 60)
    if all_passed:
        print("✓ All tests passed - Data flow context integration working!")
    else:
        print("⚠ Some tests had warnings")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    test_data_flow_context()
