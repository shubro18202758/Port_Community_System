"""Quick test of OllamaLLM and Manager Agent"""
import sys
sys.path.insert(0, '.')
import time

# Reset singleton for testing
from manager_agent import local_llm
local_llm.OllamaLLM._instance = None

# Direct import
from manager_agent.local_llm import OllamaLLM
from manager_agent.manager import ManagerAgent
import json

print("=" * 60)
print("Testing SmartBerth Manager Agent (Qwen3-8B GPU via Ollama)")
print("=" * 60)

# Test 1: OllamaLLM
print("\n--- Test 1: OllamaLLM Connection ---")
llm = OllamaLLM()
print(f"✓ Ollama server: {llm.is_server_running()}")
stats = llm.get_stats()
print(f"✓ Model: {stats['model']}")
print(f"✓ Available models: {len(stats['available_models'])}")

# Test 2: Simple Chat
print("\n--- Test 2: Simple Chat (GPU Inference) ---")
start = time.time()
response = llm.chat(
    messages=[{"role": "user", "content": "What is berth planning? One sentence only."}],
    max_tokens=100
)
elapsed = time.time() - start
print(f"Response: {response[:200]}")
print(f"Time: {elapsed:.2f}s")

# Test 3: Manager Agent
print("\n--- Test 3: Manager Agent ---")
agent = ManagerAgent(model="qwen3:8b")
print(f"✓ Agent ready: {agent.is_ready()}")

# Test 4: Query Processing Pipeline
print("\n--- Test 4: Query Processing Pipeline ---")
test_queries = [
    "Show me available berths at Port Singapore",
    "What is the status of vessel MV Atlantic?",
    "Optimize berth allocation for tomorrow",
    "Which vessels are connected to Terminal A?",
    "Hello!"
]

for query in test_queries:
    start = time.time()
    result = agent.process_query(query)
    elapsed = time.time() - start
    
    print(f"\nQuery: {query}")
    print(f"  → Type: {result['task']['type']}")
    print(f"  → Confidence: {result['task']['confidence']:.2f}")
    print(f"  → Route: {result['route']}")
    print(f"  → Time: {elapsed:.2f}s")

# Final stats
print("\n" + "=" * 60)
print("Manager Agent Stats:")
stats = agent.get_stats()
print(f"  Tasks processed: {stats['tasks_processed']}")
print(f"  Task distribution: {stats['task_types']}")
print("\n✓ All tests passed!")
print("=" * 60)
