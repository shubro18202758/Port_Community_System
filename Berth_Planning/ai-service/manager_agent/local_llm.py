"""
Local Qwen3-8B LLM Wrapper using Ollama
GPU-accelerated via Ollama server (RTX 4070 Laptop ~6GB VRAM)
Designed for Manager Agent orchestration tasks
"""

import os
import json
import logging
import httpx
from typing import Optional, List, Dict, Any, Generator, AsyncGenerator
from functools import lru_cache
import asyncio

logger = logging.getLogger(__name__)


class OllamaLLM:
    """
    Ollama-based Qwen3-8B LLM for Manager Agent tasks.
    GPU-accelerated via Ollama server (RTX 4070 ~6.7GB VRAM).
    Optimized for orchestration, routing, and planning.
    """
    
    # Configuration defaults - using qwen3-8b-instruct for better JSON output
    DEFAULT_MODEL = "qwen3-8b-instruct:latest"
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MAX_TOKENS = 512
    DEFAULT_TEMPERATURE = 0.7
    DEFAULT_TOP_P = 0.9
    DEFAULT_TIMEOUT = 120.0
    
    # Available SmartBerth models
    AVAILABLE_MODELS = [
        "qwen3-8b-instruct:latest",  # Best for structured output
        "smartberth-qwen3:latest",   # Domain fine-tuned
        "qwen3:8b",                  # Base model
        "qwen3:8b-q4_K_M"
    ]
    
    # Singleton instance
    _instance: Optional["OllamaLLM"] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern - only one instance"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        enable_thinking: bool = False  # Qwen3's extended thinking mode
    ):
        """
        Initialize Ollama LLM wrapper
        
        Args:
            model: Model name (default: qwen3:8b)
            base_url: Ollama server URL (default: http://localhost:11434)
            timeout: Request timeout in seconds
            enable_thinking: Enable Qwen3's extended thinking mode
        """
        if self._initialized:
            return
            
        self.model = os.environ.get("OLLAMA_MODEL", model)
        self.base_url = os.environ.get("OLLAMA_BASE_URL", base_url)
        self.timeout = timeout
        self.enable_thinking = enable_thinking
        
        # HTTP clients
        self._sync_client = httpx.Client(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout)
        )
        self._async_client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout)
        )
        
        self._initialized = True
        logger.info(f"OllamaLLM initialized with model: {self.model} at {self.base_url}")
    
    def is_server_running(self) -> bool:
        """Check if Ollama server is running"""
        try:
            response = self._sync_client.get("/")
            return response.status_code == 200
        except Exception:
            return False
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available models on Ollama server"""
        try:
            response = self._sync_client.get("/api/tags")
            if response.status_code == 200:
                return response.json().get("models", [])
            return []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed info about a model"""
        try:
            response = self._sync_client.post(
                "/api/show",
                json={"name": model or self.model}
            )
            if response.status_code == 200:
                return response.json()
            return {}
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {}
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        stop: Optional[List[str]] = None,
        system: Optional[str] = None,
        stream: bool = False
    ) -> str | Generator[str, None, None]:
        """
        Generate completion from prompt
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop: Stop sequences
            system: System prompt
            stream: Whether to stream output
            
        Returns:
            Generated text or generator for streaming
        """
        # Build options with Qwen3 thinking mode support
        options = {
            "num_predict": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if stop:
            options["stop"] = stop
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "options": options,
            "stream": stream
        }
        
        if system:
            payload["system"] = system
        
        # Handle Qwen3 thinking mode via /no_think or /think tags
        if self.enable_thinking and "/no_think" not in prompt and "/think" not in prompt:
            payload["prompt"] = f"/think\n{prompt}"
        
        if stream:
            return self._generate_stream(payload)
        
        try:
            response = self._sync_client.post("/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            raise
    
    def _generate_stream(self, payload: Dict) -> Generator[str, None, None]:
        """Stream generation token by token"""
        try:
            with self._sync_client.stream("POST", "/api/generate", json=payload) as response:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        stop: Optional[List[str]] = None,
        stream: bool = False
    ) -> str | Generator[str, None, None]:
        """
        Chat completion with message history
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop: Stop sequences
            stream: Whether to stream output
            
        Returns:
            Assistant response or generator for streaming
        """
        options = {
            "num_predict": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if stop:
            options["stop"] = stop
        
        payload = {
            "model": self.model,
            "messages": messages,
            "options": options,
            "stream": stream
        }
        
        if stream:
            return self._chat_stream(payload)
        
        try:
            response = self._sync_client.post("/api/chat", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise
    
    def _chat_stream(self, payload: Dict) -> Generator[str, None, None]:
        """Stream chat response"""
        try:
            with self._sync_client.stream("POST", "/api/chat", json=payload) as response:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data:
                            content = data["message"].get("content", "")
                            if content:
                                yield content
                        if data.get("done", False):
                            break
        except Exception as e:
            logger.error(f"Stream chat failed: {e}")
            raise
    
    # ============= Async Methods =============
    
    async def agenerate(
        self,
        prompt: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        stop: Optional[List[str]] = None,
        system: Optional[str] = None,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """Async version of generate"""
        options = {
            "num_predict": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if stop:
            options["stop"] = stop
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "options": options,
            "stream": stream
        }
        
        if system:
            payload["system"] = system
        
        if self.enable_thinking and "/no_think" not in prompt:
            payload["prompt"] = f"/think\n{prompt}"
        
        if stream:
            return self._agenerate_stream(payload)
        
        try:
            response = await self._async_client.post("/api/generate", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except Exception as e:
            logger.error(f"Async generation failed: {e}")
            raise
    
    async def _agenerate_stream(self, payload: Dict) -> AsyncGenerator[str, None]:
        """Async stream generation"""
        try:
            async with self._async_client.stream("POST", "/api/generate", json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done", False):
                            break
        except Exception as e:
            logger.error(f"Async stream generation failed: {e}")
            raise
    
    async def achat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        stop: Optional[List[str]] = None,
        stream: bool = False
    ) -> str | AsyncGenerator[str, None]:
        """Async version of chat"""
        options = {
            "num_predict": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
        
        if stop:
            options["stop"] = stop
        
        payload = {
            "model": self.model,
            "messages": messages,
            "options": options,
            "stream": stream
        }
        
        if stream:
            return self._achat_stream(payload)
        
        try:
            response = await self._async_client.post("/api/chat", json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "").strip()
        except Exception as e:
            logger.error(f"Async chat failed: {e}")
            raise
    
    async def _achat_stream(self, payload: Dict) -> AsyncGenerator[str, None]:
        """Async stream chat"""
        try:
            async with self._async_client.stream("POST", "/api/chat", json=payload) as response:
                async for line in response.aiter_lines():
                    if line:
                        data = json.loads(line)
                        if "message" in data:
                            content = data["message"].get("content", "")
                            if content:
                                yield content
                        if data.get("done", False):
                            break
        except Exception as e:
            logger.error(f"Async stream chat failed: {e}")
            raise
    
    # ============= Manager Agent Specialized Methods =============
    
    def classify_task(self, user_query: str) -> Dict[str, Any]:
        """
        Classify user query into task type for routing
        
        Returns:
            Dict with task_type, confidence, entities
        """
        # Use /no_think to disable Qwen3's extended thinking for faster JSON response
        system_prompt = """/no_think
You are a task classifier for SmartBerth port management. Output ONLY valid JSON.
Categories: BERTH_QUERY, VESSEL_QUERY, OPTIMIZATION, ANALYTICS, GRAPH_QUERY, GENERAL
Format: {"task_type": "CATEGORY", "confidence": 0.9, "entities": []}"""
        
        response = self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            max_tokens=150,
            temperature=0.1  # Lower temp for deterministic output
        )
        
        try:
            # Clean response - remove thinking tags if present
            clean_response = response
            if "<think>" in clean_response:
                # Remove thinking blocks
                import re
                clean_response = re.sub(r'<think>.*?</think>', '', clean_response, flags=re.DOTALL)
            
            # Extract JSON from response
            if "```json" in clean_response:
                json_str = clean_response.split("```json")[1].split("```")[0]
            elif "```" in clean_response:
                json_str = clean_response.split("```")[1].split("```")[0]
            elif "{" in clean_response:
                start = clean_response.index("{")
                end = clean_response.rindex("}") + 1
                json_str = clean_response[start:end]
            else:
                json_str = clean_response
            
            result = json.loads(json_str.strip())
            
            # Validate task_type
            valid_types = ["BERTH_QUERY", "VESSEL_QUERY", "OPTIMIZATION", "ANALYTICS", "GRAPH_QUERY", "GENERAL"]
            if result.get("task_type") not in valid_types:
                result["task_type"] = "GENERAL"
            
            return result
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse classification response: {response[:200]}")
            # Fallback: keyword-based classification
            query_lower = user_query.lower()
            if any(w in query_lower for w in ["berth", "dock", "allocat", "availab"]):
                return {"task_type": "BERTH_QUERY", "confidence": 0.7, "entities": []}
            elif any(w in query_lower for w in ["vessel", "ship", "arrival", "depart"]):
                return {"task_type": "VESSEL_QUERY", "confidence": 0.7, "entities": []}
            elif any(w in query_lower for w in ["optimi", "schedule", "plan"]):
                return {"task_type": "OPTIMIZATION", "confidence": 0.7, "entities": []}
            elif any(w in query_lower for w in ["connect", "relation", "link", "path"]):
                return {"task_type": "GRAPH_QUERY", "confidence": 0.7, "entities": []}
            elif any(w in query_lower for w in ["report", "analys", "statist"]):
                return {"task_type": "ANALYTICS", "confidence": 0.7, "entities": []}
            return {"task_type": "GENERAL", "confidence": 0.5, "entities": []}
    
    def plan_execution(self, task: str, context: str = "") -> List[Dict[str, str]]:
        """
        Create execution plan for complex tasks
        
        Returns:
            List of steps with action and target
        """
        system_prompt = """You are a task planner for SmartBerth port management.
Given a task, create a step-by-step execution plan.

Respond in JSON format only:
{"steps": [{"action": "action_type", "target": "target_entity", "description": "what to do"}]}

Available actions: QUERY_RAG, QUERY_GRAPH, CALL_API, OPTIMIZE, ANALYZE, RESPOND"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {task}\n\nContext: {context}" if context else f"Task: {task}"}
        ]
        
        response = self.chat(messages, max_tokens=300, temperature=0.3)
        
        try:
            if "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                result = json.loads(response[start:end])
                return result.get("steps", [])
        except (json.JSONDecodeError, ValueError):
            logger.warning(f"Failed to parse plan: {response}")
        
        return [{"action": "RESPOND", "target": "user", "description": "Respond directly"}]
    
    def extract_entities(
        self,
        text: str,
        entity_types: List[str]
    ) -> Dict[str, List[str]]:
        """
        Extract named entities from text
        
        Args:
            text: Input text
            entity_types: Types to extract (e.g., ["vessel", "port", "berth"])
            
        Returns:
            Dict mapping entity types to lists of extracted entities
        """
        system_prompt = f"""Extract entities from the text.
Entity types: {', '.join(entity_types)}
Respond in JSON only: {{{', '.join([f'"{et}": ["entity1"]' for et in entity_types])}}}"""
        
        response = self.chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            max_tokens=200,
            temperature=0.1
        )
        
        try:
            if "{" in response:
                start = response.index("{")
                end = response.rindex("}") + 1
                return json.loads(response[start:end])
        except (json.JSONDecodeError, ValueError):
            pass
        return {et: [] for et in entity_types}
    
    def summarize_context(self, documents: List[str], max_length: int = 200) -> str:
        """Summarize retrieved documents for context"""
        combined = "\n---\n".join(documents[:5])
        
        response = self.generate(
            prompt=f"/no_think\nSummarize concisely:\n\n{combined}",
            max_tokens=max_length,
            temperature=0.3
        )
        
        return response
    
    def is_loaded(self) -> bool:
        """Check if Ollama is running and model available"""
        return self.is_server_running()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get model statistics"""
        return {
            "model": self.model,
            "base_url": self.base_url,
            "server_running": self.is_server_running(),
            "enable_thinking": self.enable_thinking,
            "available_models": [m["name"] for m in self.list_models()[:5]]
        }
    
    def close(self):
        """Close HTTP clients"""
        self._sync_client.close()
    
    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.close()
        except Exception:
            pass


# Backwards compatibility alias
LocalQwenLLM = OllamaLLM


# Factory function
def get_local_llm(
    model: str = OllamaLLM.DEFAULT_MODEL,
    base_url: str = OllamaLLM.DEFAULT_BASE_URL,
    **kwargs
) -> OllamaLLM:
    """Get or create the singleton OllamaLLM instance"""
    return OllamaLLM(model=model, base_url=base_url, **kwargs)


# ============= Quick Test =============

if __name__ == "__main__":
    import time
    
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("OllamaLLM Test - Qwen3-8B GPU Accelerated")
    print("=" * 60)
    
    llm = OllamaLLM()
    
    # Check server
    print(f"\n✓ Ollama server running: {llm.is_server_running()}")
    
    # List models
    models = llm.list_models()
    print(f"✓ Available models: {len(models)}")
    for m in models[:5]:
        size_gb = m.get('size', 0) / (1024**3)
        print(f"  - {m['name']} ({size_gb:.1f} GB)")
    
    # Test generation
    print("\n--- Testing generate() ---")
    start = time.time()
    response = llm.generate(
        "What is berth planning? One sentence.",
        max_tokens=100,
        temperature=0.7
    )
    elapsed = time.time() - start
    print(f"Response: {response[:200]}...")
    print(f"Time: {elapsed:.2f}s")
    
    # Test chat
    print("\n--- Testing chat() ---")
    start = time.time()
    response = llm.chat(
        messages=[
            {"role": "system", "content": "You are a port management expert."},
            {"role": "user", "content": "List 3 factors for berth allocation."}
        ],
        max_tokens=150
    )
    elapsed = time.time() - start
    print(f"Response: {response[:200]}...")
    print(f"Time: {elapsed:.2f}s")
    
    # Test task classification
    print("\n--- Testing classify_task() ---")
    classification = llm.classify_task("Show me available berths for vessel MV Atlantic at Port Singapore")
    print(f"Classification: {json.dumps(classification, indent=2)}")
    
    print("\n" + "=" * 60)
    print("All tests passed!")
