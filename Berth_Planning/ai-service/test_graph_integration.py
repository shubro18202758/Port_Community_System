"""
SmartBerth AI - Graph Integration Test
Tests Neo4j connectivity, data loading, and graph reasoning
Run this after Neo4j is running and accessible
"""

import os
import sys
from datetime import datetime, timedelta

def test_neo4j_integration():
    print("=" * 70)
    print("SmartBerth AI - Graph Integration Test")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {
        "neo4j_connection": False,
        "sql_connection": False,
        "data_loaded": False,
        "queries_tested": 0,
        "reasoner_tested": False
    }
    
    # Step 1: Test Neo4j Connection
    print("\n📡 Step 1: Testing Neo4j Connection...")
    try:
        from graph import get_neo4j_loader
        loader = get_neo4j_loader()
        
        if loader.driver:
            print("   ✓ Neo4j connected successfully")
            results["neo4j_connection"] = True
            
            # Get basic stats
            stats = loader.get_graph_stats()
            if 'error' not in stats:
                print(f"   ✓ Graph accessible")
                if stats.get('total_nodes', 0) > 0:
                    print(f"   ✓ Graph contains {stats['total_nodes']} nodes")
        else:
            print("   ✗ Neo4j not connected")
            print("\n   To connect to your team member's Neo4j instance:")
            print("   1. Get their Neo4j connection details (URI, username, password)")
            print("   2. Update .env file with:")
            print("      NEO4J_URI=bolt://their-ip:7687")
            print("      NEO4J_USERNAME=neo4j")
            print("      NEO4J_PASSWORD=their-password")
            print("\n   Or if running Neo4j locally via Docker:")
            print("      docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \\")
            print("        -e NEO4J_AUTH=neo4j/smartberth123 neo4j:latest")
            return results
            
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return results
    
    # Step 2: Test SQL Server Connection
    print("\n📡 Step 2: Testing SQL Server Connection...")
    try:
        if loader.sql_connection:
            print("   ✓ SQL Server connected")
            results["sql_connection"] = True
        else:
            print("   ✗ SQL Server not connected")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 3: Load Data (if both connected and graph is empty)
    print("\n🔄 Step 3: Loading Data into Neo4j...")
    try:
        stats = loader.get_graph_stats()
        if stats.get('total_nodes', 0) == 0:
            print("   Graph is empty, loading data from SQL Server...")
            load_results = loader.load_all(clear_first=True)
            
            print("\n   Load Results:")
            for entity, count in load_results.items():
                status = "✓" if count > 0 else "○"
                print(f"   {status} {entity}: {count}")
            
            results["data_loaded"] = sum(load_results.values()) > 0
        else:
            print(f"   Graph already has {stats.get('total_nodes', 0)} nodes")
            results["data_loaded"] = True
            
    except Exception as e:
        print(f"   ✗ Error loading data: {e}")
    
    # Step 4: Test Query Templates
    print("\n🔍 Step 4: Testing Cypher Query Templates...")
    try:
        from graph import CypherQueryTemplates
        templates = CypherQueryTemplates.get_all_templates()
        
        for name, template in templates.items():
            print(f"\n   Testing: {template.name}")
            
            # Create test parameters
            test_params = {}
            for param in template.parameters:
                if 'id' in param.lower():
                    test_params[param] = 1
                elif 'time' in param.lower() or 'date' in param.lower():
                    if 'start' in param.lower():
                        test_params[param] = datetime.now().isoformat()
                    else:
                        test_params[param] = (datetime.now() + timedelta(days=1)).isoformat()
                elif param == 'limit':
                    test_params[param] = 5
            
            try:
                results_data = loader.execute_cypher(template.cypher, test_params) if hasattr(loader, 'execute_cypher') else []
                # Execute via driver directly
                with loader.driver.session(database=loader.neo4j_config.database) as session:
                    result = session.run(template.cypher, test_params)
                    results_data = [dict(r) for r in result]
                
                print(f"      ✓ Query executed, {len(results_data)} results")
                results["queries_tested"] += 1
            except Exception as e:
                print(f"      ✗ Query failed: {str(e)[:50]}...")
                
    except Exception as e:
        print(f"   ✗ Template testing error: {e}")
    
    # Step 5: Test Graph Reasoner
    print("\n🧠 Step 5: Testing Graph Reasoner...")
    try:
        from graph import get_graph_reasoner
        reasoner = get_graph_reasoner()
        
        status = reasoner.get_status()
        print(f"   Neo4j Connected: {status['neo4j_connected']}")
        print(f"   Anthropic Available: {status['anthropic_available']}")
        print(f"   Model: {status['model']}")
        
        if status['neo4j_connected']:
            # Test a simple query
            print("\n   Testing find_suitable_berths...")
            result = reasoner.find_suitable_berths(
                vessel_id=1,
                check_time_start=datetime.now().isoformat(),
                check_time_end=(datetime.now() + timedelta(days=1)).isoformat()
            )
            
            print(f"      Query Type: {result.query_type}")
            print(f"      Results: {len(result.raw_results)}")
            print(f"      Time: {result.reasoning_time_ms:.1f}ms")
            print(f"      Confidence: {result.confidence:.0%}")
            
            if result.recommendations:
                print(f"      Recommendations: {len(result.recommendations)}")
            
            results["reasoner_tested"] = True
            
    except Exception as e:
        print(f"   ✗ Reasoner error: {e}")
    
    # Step 6: Test Query Router
    print("\n🔀 Step 6: Testing Query Router...")
    try:
        from rag.router import get_query_orchestrator
        orchestrator = get_query_orchestrator()
        
        test_queries = [
            "What are the LOA constraints for berth allocation?",
            "Find suitable berths for vessel with LOA 340m and draft 14m"
        ]
        
        for query in test_queries:
            print(f"\n   Query: {query[:50]}...")
            result = orchestrator.execute(query)
            print(f"      Primary Engine: {result.routing.primary_engine.value}")
            print(f"      Intent: {result.routing.query_intent}")
            print(f"      Sources: {', '.join(result.sources)}")
            
    except Exception as e:
        print(f"   ✗ Router error: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"   Neo4j Connection:  {'✓' if results['neo4j_connection'] else '✗'}")
    print(f"   SQL Server:        {'✓' if results['sql_connection'] else '✗'}")
    print(f"   Data Loaded:       {'✓' if results['data_loaded'] else '✗'}")
    print(f"   Queries Tested:    {results['queries_tested']}/5")
    print(f"   Reasoner Tested:   {'✓' if results['reasoner_tested'] else '✗'}")
    
    all_passed = all([
        results['neo4j_connection'],
        results['sql_connection'],
        results['data_loaded'],
        results['queries_tested'] >= 3,
        results['reasoner_tested']
    ])
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✅ All tests passed! Graph integration is working.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    print("=" * 70)
    
    return results


if __name__ == "__main__":
    test_neo4j_integration()
