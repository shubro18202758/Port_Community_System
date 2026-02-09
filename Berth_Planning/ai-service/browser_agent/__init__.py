"""
SmartBerth Browser Agent - Agentic Browser Automation System
Enables autonomous browser interaction AND internal tool access for the chatbot.

This is a FULL AGENTIC SYSTEM that can:
1. Control a browser (navigate, click, type, screenshot)
2. Query internal databases (vessels, berths, schedules)
3. Run ML predictions (ETA, berth recommendations)
4. Use the Qwen3 manager agent for task routing
5. Search the RAG knowledge base
"""

from .action_schema import (
    BrowserAction, 
    ActionType, 
    ActionResult, 
    AgentState,
    AgentStep
)
from .dom_extractor import DOMExtractor
from .browser_controller import BrowserController
from .action_executor import ActionExecutor
from .memory import AgentMemory
from .agent_loop import AgenticBrowserController, AgentTask, create_browser_agent

# Import tools if available
try:
    from .tools import (
        get_tool_registry,
        AgentToolRegistry,
        ToolResult,
        ToolCategory,
        ToolDefinition
    )
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False
    get_tool_registry = None
    AgentToolRegistry = None
    ToolResult = None
    ToolCategory = None
    ToolDefinition = None

__all__ = [
    # Action schema
    'BrowserAction',
    'ActionType', 
    'ActionResult',
    'AgentState',
    'AgentStep',
    # Components
    'DOMExtractor',
    'BrowserController',
    'ActionExecutor',
    'AgentMemory',
    # Main controller
    'AgenticBrowserController',
    'AgentTask',
    'create_browser_agent',
    # Tools
    'get_tool_registry',
    'AgentToolRegistry',
    'ToolResult',
    'ToolCategory',
    'ToolDefinition',
    'TOOLS_AVAILABLE'
]
