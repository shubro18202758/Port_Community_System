# Manager Agent Module
# Uses local Qwen3-8B via Ollama (GPU-accelerated, ~6GB VRAM)
# Separate from the Central AI Agent (Claude Opus 4)

from .local_llm import OllamaLLM, LocalQwenLLM, get_local_llm
from .manager import ManagerAgent
from .task_router import TaskRouter
from .agent_coordinator import AgentCoordinator
from .enhanced_manager import EnhancedManagerAgent, get_enhanced_manager_agent

__all__ = [
    "OllamaLLM",
    "LocalQwenLLM",  # Alias for backwards compatibility
    "get_local_llm",
    "ManagerAgent", 
    "EnhancedManagerAgent",  # Training data aware manager
    "get_enhanced_manager_agent",
    "TaskRouter",
    "AgentCoordinator"
]
