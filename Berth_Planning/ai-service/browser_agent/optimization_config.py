"""
Browser Agent Optimization Configuration
GPU acceleration and performance tuning settings
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from enum import Enum


class PerformanceMode(Enum):
    """Performance mode presets"""
    ULTRA_FAST = "ultra_fast"   # Smallest model, minimal delays, aggressive caching
    FAST = "fast"               # Small model, reduced delays, caching enabled
    BALANCED = "balanced"       # Default - good quality + reasonable speed
    QUALITY = "quality"         # Larger model, more thorough analysis


@dataclass
class AgentOptimizationConfig:
    """
    Comprehensive optimization settings for the Browser Agent.
    Tuned for RTX 4070 Laptop GPU (~6-8GB VRAM).
    """
    
    # === Performance Mode Preset ===
    mode: PerformanceMode = PerformanceMode.FAST
    
    # === LLM Settings (GPU Acceleration) ===
    # Model selection by performance tier
    model_ultra_fast: str = "qwen2.5:1.5b"      # ~1GB VRAM, <200ms/decision
    model_fast: str = "qwen2.5:3b"              # ~2GB VRAM, <400ms/decision
    model_balanced: str = "qwen3-8b-instruct:latest"  # ~5GB VRAM, ~1-2s/decision
    model_quality: str = "smartberth-qwen3:latest"    # Domain fine-tuned
    
    # Token limits (smaller = faster)
    max_tokens_decision: int = 384      # Reduced from 1024 - decisions are simple
    max_tokens_summary: int = 256       # Reduced from 600
    
    # Temperature (lower = faster, more deterministic)
    temperature: float = 0.1            # Reduced from 0.2 - more predictable
    
    # === Timing Settings ===
    step_delay_ms: int = 100            # Reduced from 500ms
    page_load_wait_ms: int = 500        # Reduced from 1000ms
    action_timeout_ms: int = 5000       # Timeout for browser actions
    llm_timeout_seconds: float = 30.0   # Reduced from 120s
    
    # === DOM Extraction Optimization ===
    max_dom_elements: int = 50          # Reduced from 80
    max_text_length: int = 2000         # Reduced from 5000
    max_observation_length: int = 1500  # Truncate observation for LLM
    skip_hidden_elements: bool = True   # Don't extract hidden elements
    
    # === Caching Settings ===
    enable_decision_cache: bool = True  # Cache repeated DOM pattern decisions
    cache_ttl_seconds: int = 60         # How long to cache decisions
    cache_max_size: int = 100           # Max cached decisions
    
    # === Parallel Processing ===
    enable_parallel_observation: bool = True   # Observe DOM while LLM thinks
    enable_async_screenshots: bool = True      # Non-blocking screenshots
    
    # === Early Termination ===
    max_consecutive_reads: int = 2      # Force action after N read_page
    min_tabs_for_complete: int = 2      # Min tabs to visit before complete
    max_steps: int = 30                 # Reduced from 50
    
    # === GPU Optimization (Ollama) ===
    gpu_layers: int = -1                # -1 = all layers on GPU
    num_threads: int = 8                # CPU threads for preprocessing
    batch_size: int = 512               # Larger batch = faster (if VRAM allows)
    
    def get_model_for_mode(self) -> str:
        """Get the appropriate model based on performance mode"""
        return {
            PerformanceMode.ULTRA_FAST: self.model_ultra_fast,
            PerformanceMode.FAST: self.model_fast,
            PerformanceMode.BALANCED: self.model_balanced,
            PerformanceMode.QUALITY: self.model_quality,
        }[self.mode]
    
    def get_timing_config(self) -> Dict[str, int]:
        """Get timing settings adjusted for mode"""
        multiplier = {
            PerformanceMode.ULTRA_FAST: 0.5,
            PerformanceMode.FAST: 0.75,
            PerformanceMode.BALANCED: 1.0,
            PerformanceMode.QUALITY: 1.5,
        }[self.mode]
        
        return {
            "step_delay_ms": int(self.step_delay_ms * multiplier),
            "page_load_wait_ms": int(self.page_load_wait_ms * multiplier),
            "action_timeout_ms": int(self.action_timeout_ms * multiplier),
        }


# === Preset Configurations ===

ULTRA_FAST_CONFIG = AgentOptimizationConfig(
    mode=PerformanceMode.ULTRA_FAST,
    step_delay_ms=50,
    page_load_wait_ms=300,
    max_tokens_decision=256,
    max_dom_elements=30,
    max_observation_length=1000,
    max_steps=20,
    temperature=0.05,
)

FAST_CONFIG = AgentOptimizationConfig(
    mode=PerformanceMode.FAST,
    step_delay_ms=100,
    page_load_wait_ms=500,
    max_tokens_decision=384,
    max_dom_elements=50,
    max_observation_length=1500,
    max_steps=30,
    temperature=0.1,
)

BALANCED_CONFIG = AgentOptimizationConfig(
    mode=PerformanceMode.BALANCED,
    step_delay_ms=250,
    page_load_wait_ms=750,
    max_tokens_decision=512,
    max_dom_elements=70,
    max_observation_length=2500,
    max_steps=40,
    temperature=0.2,
)

QUALITY_CONFIG = AgentOptimizationConfig(
    mode=PerformanceMode.QUALITY,
    step_delay_ms=500,
    page_load_wait_ms=1000,
    max_tokens_decision=1024,
    max_dom_elements=100,
    max_observation_length=4000,
    max_steps=50,
    temperature=0.3,
)


# Compact system prompt for faster inference
OPTIMIZED_SYSTEM_PROMPT = """/no_think
You are a FAST browser agent for SmartBerth port management.

## WORKFLOW (follow strictly):
1. CLICK a tab → 2. READ_PAGE → 3. RECORD findings → 4. CLICK next tab → repeat → COMPLETE

## SmartBerth Tabs:
- Upcoming Vessels: incoming vessel list with AI ETAs
- Vessel Tracking: real-time vessel positions on map
- Berth Overview: berth assignments and status
- Digital Twin: 3D port visualization
- Gantt Chart: timeline schedule view

## Response (JSON only, pick ONE):

Browser action:
{"type":"browser","action_type":"click|read_page|scroll_down","target":"CSS selector","reasoning":"why"}

Internal tool (faster than browser!):
{"type":"tool","tool_name":"db_get_vessels|ml_predict_eta","parameters":{},"reasoning":"why"}

Complete (after visiting 2+ tabs):
{"type":"complete","reasoning":"summary","final_summary":"What I found across all tabs..."}

Fail:
{"type":"fail","reasoning":"why"}

RULES:
- After CLICK → always READ_PAGE next
- After READ_PAGE → CLICK next tab or COMPLETE
- PREFER internal tools over browser for data queries
- JSON ONLY - no markdown, no explanations outside JSON"""


def get_config_for_mode(mode: str = "fast") -> AgentOptimizationConfig:
    """Get configuration for specified mode"""
    configs = {
        "ultra_fast": ULTRA_FAST_CONFIG,
        "fast": FAST_CONFIG,
        "balanced": BALANCED_CONFIG,
        "quality": QUALITY_CONFIG,
    }
    return configs.get(mode.lower(), FAST_CONFIG)


class DecisionCache:
    """
    Simple LRU cache for repeated DOM pattern → decision mappings.
    Avoids redundant LLM calls for similar page states.
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 60):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0
    
    def _hash_observation(self, observation: str, task: str) -> str:
        """Create a hash key from observation and task"""
        import hashlib
        # Use first 500 chars of observation + task for key
        content = f"{task[:100]}:{observation[:500]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, observation: str, task: str) -> Optional[Dict[str, Any]]:
        """Get cached decision if available and not expired"""
        import time
        
        key = self._hash_observation(observation, task)
        if key in self._cache:
            # Check TTL
            if time.time() - self._timestamps.get(key, 0) < self._ttl:
                self._hits += 1
                return self._cache[key]
            else:
                # Expired
                del self._cache[key]
                del self._timestamps[key]
        
        self._misses += 1
        return None
    
    def set(self, observation: str, task: str, decision: Dict[str, Any]):
        """Cache a decision"""
        import time
        
        key = self._hash_observation(observation, task)
        
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size:
            oldest = min(self._timestamps, key=self._timestamps.get)
            del self._cache[oldest]
            del self._timestamps[oldest]
        
        self._cache[key] = decision
        self._timestamps[key] = time.time()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._hits + self._misses
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0,
            "size": len(self._cache),
            "max_size": self._max_size,
        }
    
    def clear(self):
        """Clear the cache"""
        self._cache.clear()
        self._timestamps.clear()
        self._hits = 0
        self._misses = 0
