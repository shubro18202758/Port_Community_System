"""
SmartBerth Pipeline Runner
Executes the full berth planning pipeline with test and training data.
"""

import sys
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from smartberth_core import get_smartberth_core


def print_separator():
    print("\n" + "=" * 80 + "\n")


def run_pipeline():
    """Execute the full SmartBerth pipeline"""
    
    print_separator()
    print("🚢 SMARTBERTH AI - BERTH PLANNING INTELLIGENCE SYSTEM")
    print("   Powered by Claude Opus 4")
    print_separator()
    
    # Initialize core
    print("📋 STEP 1: Initializing SmartBerth Core Engine...")
    core = get_smartberth_core()
    
    if not core.initialize():
        print("❌ Failed to initialize SmartBerth Core")
        return False
    
    print_separator()
    print("📊 STEP 2: Analyzing Training Data Patterns...")
    
    # Analyze training data
    analysis = core.analyze_training_data()
    print(f"\n📁 Training Datasets Loaded:")
    for key, size in analysis.get('dataset_sizes', {}).items():
        print(f"   • {key}: {size} records")
    
    # Get AI insights
    print("\n🤖 AI Insights from Training Data:")
    insights = core.get_training_insights()
    print(insights)
    
    print_separator()
    print("🌊 STEP 3: Running Full Pipeline for Test Vessels...")
    
    # Run full pipeline
    results = core.run_full_pipeline()
    
    # Print results
    print(f"\n✅ Pipeline Complete!")
    print(f"   • Vessels Processed: {results['vessels_processed']}")
    print(f"   • Processing Time: {results['processing_time_seconds']:.2f} seconds")
    
    print("\n📍 ETA PREDICTIONS:")
    print("-" * 60)
    for eta in results['eta_predictions'][:5]:  # Show first 5
        print(f"\n  🚢 {eta['vessel_name']}")
        print(f"     Distance: {eta['distance_nm']} NM")
        print(f"     Speed: {eta['current_speed']} kts (adjusted: {eta['factors'].get('adjusted_speed', 'N/A')} kts)")
        print(f"     ETA: {eta['predicted_eta']}")
        print(f"     Confidence: {eta['confidence_score']}%")
        print(f"     AI: {eta['ai_explanation'][:150]}...")
    
    print("\n\n🏗️ BERTH RECOMMENDATIONS:")
    print("-" * 60)
    for rec in results['berth_recommendations'][:5]:  # Show first 5
        status = "✅ Feasible" if rec['is_feasible'] else "⚠️ Has Violations"
        print(f"\n  🚢 {rec['vessel_name']}")
        print(f"     Berth: {rec['recommended_berth']} @ {rec['terminal_name']}")
        print(f"     Score: {rec['score']}/100 - {status}")
        if rec['hard_constraint_violations']:
            print(f"     Violations: {', '.join(rec['hard_constraint_violations'])}")
        print(f"     AI: {rec['ai_reasoning'][:150]}...")
    
    print_separator()
    print("📝 EXECUTIVE SUMMARY:")
    print("-" * 60)
    print(results['summary'])
    
    # Save results to file
    output_file = Path(__file__).parent / "pipeline_results.json"
    
    # Convert datetime objects for JSON
    def json_serializer(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=json_serializer)
    
    print(f"\n💾 Full results saved to: {output_file}")
    print_separator()
    
    return True


def test_individual_predictions():
    """Test individual ETA and berth predictions"""
    print_separator()
    print("🧪 TESTING INDIVIDUAL PREDICTIONS")
    print_separator()
    
    core = get_smartberth_core()
    
    if not core._initialized:
        if not core.initialize():
            print("❌ Failed to initialize")
            return
    
    # Test vessels (using IDs from test data)
    test_vessel_ids = [1, 2, 3, 5, 7]
    
    for vid in test_vessel_ids:
        try:
            print(f"\n--- Vessel ID: {vid} ---")
            
            # ETA Prediction
            eta = core.predict_eta(vid)
            print(f"📍 ETA Prediction for {eta.vessel_name}:")
            print(f"   Position: {eta.current_position}")
            print(f"   Distance: {eta.distance_nm} NM")
            print(f"   ETA: {eta.predicted_eta}")
            print(f"   Confidence: {eta.confidence_score}%")
            
            # Berth Recommendation
            berth = core.recommend_berth(vid)
            print(f"🏗️ Berth Recommendation:")
            print(f"   Berth: {berth.recommended_berth}")
            print(f"   Score: {berth.score}")
            print(f"   Feasible: {berth.is_feasible}")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print_separator()


def test_claude_connection():
    """Test Claude API connection"""
    print_separator()
    print("🔌 TESTING CLAUDE API CONNECTION")
    print_separator()
    
    from model import get_model
    from config import get_settings
    
    settings = get_settings()
    print(f"Model: {settings.claude_model}")
    print(f"Max Tokens: {settings.max_new_tokens}")
    
    model = get_model()
    if model.initialize():
        print("✅ Claude initialized successfully!")
        
        # Test generation
        result = model.generate_text(
            "What is the primary function of a berth planning system in a port?",
            max_tokens=150
        )
        
        if result.get('success'):
            print(f"\n🤖 Claude Response:\n{result['text']}")
        else:
            print(f"❌ Generation failed: {result.get('error')}")
    else:
        print("❌ Claude initialization failed")
    
    print_separator()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SmartBerth Pipeline Runner")
    parser.add_argument('--mode', choices=['full', 'test', 'connection'], 
                       default='full', help='Run mode')
    
    args = parser.parse_args()
    
    if args.mode == 'connection':
        test_claude_connection()
    elif args.mode == 'test':
        test_individual_predictions()
    else:
        run_pipeline()
        print("\n✨ SmartBerth Pipeline execution complete!")
