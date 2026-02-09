"""
Agentic Browser Controller - Main Agent Loop
Orchestrates the observe-decide-act cycle for autonomous browser operation

This module implements a FULL AGENTIC SYSTEM that can:
1. Control a browser (navigate, click, type, screenshot)
2. Query internal databases (vessels, berths, schedules)
3. Run ML predictions (ETA, berth recommendations)
4. Use the Qwen3 manager agent for task routing
5. Search the RAG knowledge base

The agent LLM (Qwen3-8B via Ollama) decides whether to use browser actions OR internal tools.
GPU-accelerated for fast, local inference.
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import os

# Import optimization config
from .optimization_config import (
    AgentOptimizationConfig, 
    PerformanceMode, 
    get_config_for_mode,
    DecisionCache,
    OPTIMIZED_SYSTEM_PROMPT,
    FAST_CONFIG
)

# Use Qwen3-8B via Ollama (GPU-accelerated) instead of Claude
try:
    from manager_agent.local_llm import OllamaLLM
    QWEN3_AVAILABLE = True
except ImportError:
    QWEN3_AVAILABLE = False
    OllamaLLM = None

# Fallback to Claude if Qwen3 not available
try:
    from anthropic import Anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    Anthropic = None
    CLAUDE_AVAILABLE = False

from .action_schema import BrowserAction, ActionType, ActionResult, AgentState, AgentStep
from .browser_controller import BrowserController
from .dom_extractor import DOMExtractor
from .action_executor import ActionExecutor
from .memory import AgentMemory

# Import tools registry
try:
    from .tools import get_tool_registry, ToolResult, ToolCategory
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class AgentTask:
    """Represents a task for the agent to execute"""
    task_id: str
    description: str
    target_url: str
    max_steps: int = 50
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgenticBrowserController:
    """
    Main agentic browser controller.
    Implements the observe-decide-act loop using Claude as the decision maker.
    
    This is a FULL AGENTIC SYSTEM that can:
    1. Control the browser (navigate, click, type, screenshot)
    2. Call internal database tools (query vessels, berths, schedules)
    3. Run ML predictions (ETA, berth recommendations, conflict detection)
    4. Use the Qwen3 manager agent for smart task routing
    5. Search the RAG knowledge base
    
    The agent decides whether to use browser actions OR internal tools.
    """
    
    # LLM system prompt for browser agent with internal tools  
    AGENT_SYSTEM_PROMPT = """/no_think
You are an AUTONOMOUS MULTI-TAB BROWSER AGENT for SmartBerth port management.

## CRITICAL WORKFLOW - FOLLOW THIS SEQUENCE:
1. CLICK a tab to navigate to it
2. Use READ_PAGE to analyze and understand the content on that tab  
3. DESCRIBE what you see (record findings mentally)
4. ONLY THEN move to the next tab
5. After visiting ALL required tabs, use COMPLETE with a comprehensive summary

## NEVER DO THIS:
- DO NOT click multiple tabs in a row without reading each one
- DO NOT complete the task after visiting only 1 tab
- DO NOT skip the read_page action after clicking a tab

## SmartBerth Navigation Tabs (explore ALL relevant ones):
- **Upcoming Vessels**: Shows incoming vessels with AI-predicted arrival times
- **Vessel Tracking**: Real-time vessel positions on a map
- **Berth Overview**: Current berth assignments and status
- **Digital Twin**: 3D visualization of port operations
- **Gantt Chart**: Timeline view of all scheduled operations

- **Gantt Chart**: Timeline view of all scheduled operations

## 1. BROWSER CAPABILITIES (for UI interaction)
- navigate: Go to a URL
- click: Click on elements (buttons, links, tabs, rows)
- type: Type text into input fields
- scroll_down/scroll_up: Scroll the page
- read_page: Observe and analyze the current page
- extract_data: Extract specific data from the page
- screenshot: Take a screenshot
- wait: Wait for elements to load

## 2. INTERNAL TOOLS (for backend access - FASTER than browser!)
You can call these tools directly without using the browser:

### Database Tools (category: database)
- db_get_vessels: Get all vessels (params: status?, limit?)
- db_get_vessel: Get specific vessel (params: vessel_id or vessel_name)
- db_get_berths: Get all berths (params: terminal_id?, available_only?)
- db_get_schedules: Get schedules (params: status?, start_date?, end_date?)
- db_get_resources: Get pilots/tugs/cranes (params: resource_type)
- db_query: Run custom SELECT query (params: query)

### ML Pipeline Tools (category: ml_pipeline)
- ml_predict_eta: Predict vessel ETA (params: vessel_id, include_weather?, include_traffic?)
- ml_recommend_berth: Get AI berth recommendations (params: vessel_id, preferred_eta?, top_n?)
- ml_detect_conflicts: Detect scheduling conflicts (params: hours_ahead?, include_resolution?)
- ml_pipeline_status: Get ML pipeline health status

### Manager Agent Tools (category: manager)
- manager_classify: Use Qwen3 to classify a query
- manager_plan: Create an execution plan for complex tasks
- manager_respond: Get quick response from local LLM

### RAG Tools (category: rag)
- rag_search: Semantic search in knowledge base (params: query, top_k?)
- rag_explain: Generate explanation with RAG context (params: query)

### System Tools (category: system)
- system_time: Get current time
- system_health: Get health of all components

## Response Format
Always respond with JSON. You have these options:

OPTION A - Browser Action:
```json
{
    "type": "browser",
    "action_type": "click",
    "target": "button:has-text('Submit')",
    "value": null,
    "reasoning": "Clicking submit to save",
    "confidence": 0.9
}
```

OPTION B - Internal Tool:
```json
{
    "type": "tool",
    "tool_name": "db_get_vessels",
    "parameters": {"status": "Approaching"},
    "reasoning": "Getting vessel data from database",
    "confidence": 0.95
}
```

OPTION C - Task Complete (ONLY after visiting multiple relevant pages):
```json
{
    "type": "complete",
    "reasoning": "Task completed successfully. Summary: ...",
    "data": {"result": "..."},
    "final_summary": "A comprehensive user-friendly summary of the entire journey through all tabs/pages visited, all data discovered, and insights gathered..."
}
```

OPTION D - Task Failed:
```json
{
    "type": "fail",
    "reasoning": "Could not complete because..."
}
```

## CRITICAL GUIDELINES
1. NAVIGATE MULTIPLE TABS: Explore at least 2-3 different sections to provide comprehensive information
2. PREFER internal tools over browser when fetching raw data (faster!)
3. Use browser to SHOW the user information visually on screen
4. For data queries, use db_* or ml_* tools directly
5. Always explain your reasoning clearly
6. ONLY use type: "complete" AFTER exploring all relevant pages related to the task
7. Be specific with CSS selectors when targeting browser elements
8. Every click and navigation is visible to the user - make it meaningful

## SmartBerth Context
This is the Mundra Port management system with:
- 50+ vessels with real-time tracking and AI-predicted ETAs
- 10+ berths with capacity constraints and AI suggestions  
- ML models for ETA prediction, berth optimization, and conflict detection
- Digital Twin 3D visualization
- Gantt chart scheduling view
- Knowledge base with port rules and procedures"""

    def __init__(
        self,
        headless: bool = False,  # Default to visible for transparency
        max_retries: int = 3,
        step_delay_ms: int = 100,  # OPTIMIZED: Reduced from 500ms
        performance_mode: str = "fast",  # NEW: ultra_fast, fast, balanced, quality
        on_step: Optional[Callable[[AgentStep], Awaitable[None]]] = None,
        on_state_change: Optional[Callable[[AgentState], Awaitable[None]]] = None,
        on_screenshot: Optional[Callable[[str], Awaitable[None]]] = None,
        on_tool_call: Optional[Callable[[str, Dict, Any], Awaitable[None]]] = None
    ):
        """
        Initialize the agentic browser controller.
        
        Args:
            headless: Run browser in headless mode (False = visible for transparency)
            max_retries: Maximum retries for failed actions
            step_delay_ms: Delay between steps in milliseconds (default: 100ms optimized)
            performance_mode: Performance preset - ultra_fast, fast, balanced, quality
            on_step: Callback for each step (for streaming to UI)
            on_state_change: Callback for state changes
            on_screenshot: Callback when screenshot is taken
            on_tool_call: Callback when internal tool is called
        """
        # Load optimization config based on performance mode
        self.opt_config = get_config_for_mode(performance_mode)
        
        self.headless = headless
        self.max_retries = max_retries
        self.step_delay_ms = self.opt_config.step_delay_ms  # Use optimized delay
        
        # Callbacks for UI streaming
        self._on_step = on_step
        self._on_state_change = on_state_change
        self._on_screenshot = on_screenshot
        self._on_tool_call = on_tool_call
        
        # Initialize LLM - Use model from optimization config (GPU-accelerated via Ollama)
        self.use_qwen3 = False
        self.llm = None
        self.claude = None
        self.model = None
        
        # OPTIMIZATION: Initialize decision cache for repeated patterns
        self._decision_cache = DecisionCache(
            max_size=self.opt_config.cache_max_size,
            ttl_seconds=self.opt_config.cache_ttl_seconds
        ) if self.opt_config.enable_decision_cache else None
        
        # Select model based on performance mode
        selected_model = self.opt_config.get_model_for_mode()
        
        if QWEN3_AVAILABLE:
            try:
                self.llm = OllamaLLM(
                    model=selected_model,
                    timeout=self.opt_config.llm_timeout_seconds,  # Use optimized timeout
                    enable_thinking=False  # Disable extended thinking for faster responses
                )
                if self.llm.is_server_running():
                    self.use_qwen3 = True
                    self.model = selected_model
                    logger.info("="*60)
                    logger.info(f"Browser Agent: USING {selected_model} (GPU-accelerated)")
                    logger.info(f"Performance Mode: {self.opt_config.mode.value}")
                    logger.info(f"Step Delay: {self.step_delay_ms}ms | Max Tokens: {self.opt_config.max_tokens_decision}")
                    logger.info("="*60)
                else:
                    logger.error("Ollama server not running! Start Ollama with: ollama serve")
                    raise ValueError("Ollama server not running. Run 'ollama serve' first.")
            except Exception as e:
                logger.error(f"Failed to initialize LLM: {e}")
                raise ValueError(f"LLM initialization failed: {e}. Make sure Ollama is running.")
        else:
            raise ValueError("OllamaLLM not available. Install required dependencies for local LLM support.")
        
        # Claude fallback disabled - comment out if you need Claude support
        # if not self.use_qwen3 and CLAUDE_AVAILABLE:
        #     api_key = os.getenv("ANTHROPIC_API_KEY")
        #     if api_key:
        #         self.claude = Anthropic(api_key=api_key)
        #         self.model = "claude-sonnet-4-20250514"
        
        # Initialize tools registry
        self.tools_registry = get_tool_registry() if TOOLS_AVAILABLE else None
        if self.tools_registry:
            logger.info(f"Tools registry loaded with {len(self.tools_registry._tools)} tools")
        else:
            logger.warning("Tools registry not available - running in browser-only mode")
        
        # Components (initialized when starting a task)
        self.browser: Optional[BrowserController] = None
        self.dom_extractor: Optional[DOMExtractor] = None
        self.executor: Optional[ActionExecutor] = None
        self.memory: Optional[AgentMemory] = None
        
        # Current state
        self._state = AgentState.IDLE
        self._is_running = False
        self._should_stop = False
        self._current_task: Optional[AgentTask] = None
        
        # Tool call history for this session
        self._tool_calls: List[Dict[str, Any]] = []
        
        # Track consecutive read_page actions to prevent loops
        self._consecutive_reads: int = 0
        self._explored_tabs: List[str] = []  # Tabs that have been clicked AND read
        self._current_tab: str = ""  # Currently active tab
    
    @property
    def state(self) -> AgentState:
        """Get current agent state"""
        return self._state
    
    async def _set_state(self, new_state: AgentState):
        """Set agent state and notify"""
        self._state = new_state
        if self._on_state_change:
            try:
                await self._on_state_change(new_state)
            except Exception as e:
                logger.warning(f"State change callback error: {e}")
    
    async def initialize(self, cdp_endpoint: Optional[str] = None) -> bool:
        """
        Initialize all components.
        
        Args:
            cdp_endpoint: Optional Chrome DevTools Protocol endpoint (e.g., 'http://localhost:9222')
                          If provided, connects to existing Chrome instead of launching new browser.
                          This allows the agent to control the user's visible browser window!
        """
        try:
            # Initialize browser (either launch new or connect to existing)
            self.browser = BrowserController(headless=self.headless, cdp_endpoint=cdp_endpoint)
            if not await self.browser.initialize():
                logger.error("Failed to initialize browser")
                return False
            
            # Initialize other components with OPTIMIZED settings
            self.dom_extractor = DOMExtractor(
                max_elements=self.opt_config.max_dom_elements,  # Optimized: fewer elements
                max_text_length=self.opt_config.max_text_length  # Optimized: shorter text
            )
            self.executor = ActionExecutor(
                browser=self.browser,
                dom_extractor=self.dom_extractor,
                on_action_start=self._on_action_start,
                on_action_complete=self._on_action_complete
            )
            self.memory = AgentMemory()
            
            if cdp_endpoint:
                logger.info("Agentic browser controller initialized - CONNECTED TO YOUR BROWSER!")
            else:
                logger.info("Agentic browser controller initialized")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def close(self):
        """Cleanup resources"""
        if self.browser:
            await self.browser.close()
        self._is_running = False
    
    async def _on_action_start(self, action: BrowserAction):
        """Called when an action starts"""
        logger.debug(f"Action starting: {action.action_type.value}")
    
    async def _on_action_complete(self, result: ActionResult):
        """Called when an action completes"""
        logger.debug(f"Action complete: {result.action.action_type.value} - {'Success' if result.success else 'Failed'}")
    
    # ==================== MAIN AGENT LOOP ====================
    
    async def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        Execute a task using the observe-decide-act loop.
        
        Args:
            task: The task to execute
            
        Returns:
            Task result with summary and data
        """
        self._current_task = task
        self._is_running = True
        self._should_stop = False
        
        # Reset tracking for new task
        self._consecutive_reads = 0
        self._explored_tabs = []
        self._current_tab = ""
        
        # OPTIMIZATION: Clear decision cache for new task
        if self._decision_cache:
            self._decision_cache.clear()
        
        # OPTIMIZATION: Use config max_steps if task doesn't specify
        effective_max_steps = min(task.max_steps, self.opt_config.max_steps)
        
        # Start task tracking
        self.memory.start_task(task.description, task.target_url or "current page")
        
        try:
            # Navigate to target URL (skip if empty - used when connecting to existing browser)
            if task.target_url:
                await self._set_state(AgentState.ACTING)
                success, error = await self.browser.navigate(task.target_url)
                
                if not success:
                    self.memory.fail_task(f"Failed to navigate: {error}")
                    return {"success": False, "error": error}
                
                # OPTIMIZED: Reduced page load wait time
                await asyncio.sleep(self.opt_config.page_load_wait_ms / 1000)
            else:
                # Using current page in connected browser
                logger.info("Using current page (connected mode - no navigation needed)")
            
            # Main agent loop - OPTIMIZED with effective_max_steps
            step_count = 0
            start_time = time.time()  # Track execution time
            
            while step_count < effective_max_steps and not self._should_stop:
                step_count += 1
                
                # Check if browser is still available
                if not self.browser.is_ready:
                    logger.error("Browser is no longer available - task cannot continue")
                    self.memory.fail_task("Browser closed unexpectedly")
                    return {
                        "success": False, 
                        "error": "Browser closed unexpectedly",
                        "steps": step_count,
                        "partial_result": self.memory.get_task_summary()
                    }
                
                # 1. OBSERVE
                await self._set_state(AgentState.OBSERVING)
                observation = await self._observe()
                
                if not observation:
                    observation = "Page not loaded or empty"
                
                # 2. THINK/DECIDE
                await self._set_state(AgentState.THINKING)
                decision = await self._decide(task.description, observation)
                
                if not decision:
                    logger.warning("Failed to decide on action")
                    continue
                
                decision_type = decision.get("type", "browser")
                reasoning = decision.get("reasoning", "")
                
                # Handle completion - generate user-friendly summary with full screen capture
                if decision_type == "complete":
                    final_summary = decision.get("final_summary", reasoning)
                    
                    # Generate a comprehensive summary if not provided
                    if not final_summary or final_summary == reasoning:
                        final_summary = await self._generate_task_summary(task.description)
                    
                    # ENHANCED: Expand all panels and take full-screen screenshot
                    final_screenshot_base64 = None
                    try:
                        # Expand all collapsed panels for comprehensive view
                        await self.browser.expand_all_panels()
                        
                        # Show completion overlay
                        await self.browser.show_action_overlay(
                            "✅ Task Complete",
                            final_summary[:150] + "..." if len(final_summary) > 150 else final_summary,
                            duration=3.0
                        )
                        
                        # Take full-screen screenshot capturing everything user sees
                        _, final_screenshot_base64 = await self.browser.take_full_screen_screenshot(
                            filename=f"final_{task.task_id}.png"
                        )
                        
                        # Notify about final screenshot
                        if final_screenshot_base64 and self._on_screenshot:
                            await self._on_screenshot(final_screenshot_base64)
                            
                    except Exception as e:
                        logger.warning(f"Final screenshot/expansion failed (non-critical): {e}")
                    
                    self.memory.complete_task({"summary": reasoning, "data": decision.get("data")})
                    
                    return {
                        "success": True,
                        "summary": reasoning,
                        "final_summary": final_summary,  # User-friendly summary for initial prompt
                        "steps": step_count,
                        "data": decision.get("data"),
                        "tool_calls": self._tool_calls,
                        "pages_visited": list(self.memory.get_visited_urls()) if hasattr(self.memory, 'get_visited_urls') else [],
                        "model_used": self.model,
                        "final_screenshot": final_screenshot_base64  # Full screen capture
                    }
                
                # Handle failure
                if decision_type == "fail":
                    self.memory.fail_task(reasoning)
                    return {
                        "success": False,
                        "error": reasoning,
                        "steps": step_count,
                        "tool_calls": self._tool_calls
                    }
                
                # 3. ACT - Different paths for browser vs tool
                await self._set_state(AgentState.ACTING)
                
                if decision_type == "tool":
                    # Execute internal tool
                    tool_name = decision.get("tool_name")
                    parameters = decision.get("parameters", {})
                    
                    tool_result = await self._execute_tool(tool_name, parameters)
                    
                    # Create step record for tool call
                    step = AgentStep(
                        step_id=f"step_{step_count}",
                        timestamp=datetime.now().isoformat(),
                        state=AgentState.ACTING,
                        action=BrowserAction(
                            action_type=ActionType.READ_PAGE,  # Placeholder for UI
                            target=f"tool:{tool_name}",
                            reasoning=reasoning
                        ),
                        observation=f"Tool call: {tool_name}",
                        thinking=reasoning,
                        result=ActionResult(
                            action=BrowserAction(action_type=ActionType.READ_PAGE),
                            success=tool_result.get("success", False),
                            data={"tool_result": tool_result}
                        )
                    )
                    
                    # Update memory with tool result
                    self.memory.add_observation(
                        f"Tool {tool_name} result: {json.dumps(tool_result)[:500]}"
                    )
                    
                else:
                    # Execute browser action
                    action = BrowserAction(
                        action_type=ActionType(decision.get("action_type", "read_page")),
                        target=decision.get("target"),
                        value=decision.get("value"),
                        reasoning=reasoning,
                        confidence=decision.get("confidence", 0.5)
                    )
                    
                    # Create step record
                    step = self.memory.create_step(
                        state=AgentState.THINKING,
                        action=action,
                        observation=observation[:1000],
                        thinking=reasoning
                    )
                    
                    # Check for ask_user
                    if action.action_type == ActionType.ASK_USER:
                        await self._set_state(AgentState.WAITING)
                        return {
                            "success": True,
                            "needs_input": True,
                            "question": reasoning,
                            "steps": step_count
                        }
                    
                    # Execute browser action
                    result = await self._act(action)
                    step.result = result
                    
                    # Handle screenshot callback
                    if result.screenshot_base64 and self._on_screenshot:
                        try:
                            await self._on_screenshot(result.screenshot_base64)
                        except Exception as e:
                            logger.warning(f"Screenshot callback error: {e}")
                
                # Notify UI
                if self._on_step:
                    try:
                        await self._on_step(step)
                    except Exception as e:
                        logger.warning(f"Step callback error: {e}")
                
                step.state = AgentState.ACTING
                
                # Add delay between steps
                await asyncio.sleep(self.step_delay_ms / 1000)
            
            # Max steps reached
            self.memory.fail_task("Maximum steps reached without completion")
            return {
                "success": False,
                "error": "Maximum steps reached",
                "steps": step_count,
                "partial_result": self.memory.get_task_summary()
            }
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            self.memory.fail_task(str(e))
            return {"success": False, "error": str(e)}
            
        finally:
            self._is_running = False
            await self._set_state(AgentState.IDLE)
    
    async def _observe(self) -> Optional[str]:
        """
        Observe the current page state.
        
        Returns:
            Page observation as formatted text for LLM
        """
        try:
            url = await self.browser.get_page_url()
            title = await self.browser.get_page_title()
            html = await self.browser.get_page_html()
            
            if not html:
                return None
            
            # Extract DOM data
            dom_data = self.dom_extractor.extract_from_html(html, url)
            
            # Create LLM context
            observation = self.dom_extractor.create_llm_context(
                dom_data, 
                self._current_task.description if self._current_task else ""
            )
            
            # Store snapshot
            self.memory.add_snapshot(
                url=url,
                title=title,
                dom_summary=observation
            )
            
            return observation
            
        except Exception as e:
            logger.error(f"Observation failed: {e}")
            return None
    
    async def _decide(self, task: str, observation: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM (Qwen3 or Claude) to decide the next action.
        OPTIMIZED: Uses decision caching and smaller token limits.
        
        Args:
            task: Current task description
            observation: Current page observation
            
        Returns:
            Decision dict with either browser action or tool call
        """
        try:
            # OPTIMIZATION: Check decision cache first
            if self._decision_cache:
                cached_decision = self._decision_cache.get(observation, task)
                if cached_decision:
                    logger.info(f"[CACHE HIT] Using cached decision: {cached_decision.get('type')}")
                    return cached_decision
            
            # OPTIMIZATION: Truncate observation to configured max length
            truncated_observation = observation[:self.opt_config.max_observation_length] if observation else ""
            
            # Build context
            memory_context = self.memory.build_llm_context(include_steps=5)
            
            # Add recent tool calls to context
            tool_context = ""
            if self._tool_calls:
                recent_tools = self._tool_calls[-5:]  # Last 5 tool calls
                tool_context = "\n## Recent Tool Calls\n"
                for tc in recent_tools:
                    tool_context += f"- {tc['tool']}: {tc['summary']}\n"
            
            # Track last action type to help agent follow click-read pattern
            last_action_hint = ""
            force_action = None
            recent_steps = self.memory.get_recent_steps(5)
            if recent_steps:
                last_step = recent_steps[-1]
                if last_step.action:
                    last_action = last_step.action.action_type.value if hasattr(last_step.action.action_type, 'value') else str(last_step.action.action_type)
                    
                    # Count consecutive read_page actions
                    if last_action == "read_page":
                        self._consecutive_reads += 1
                    else:
                        self._consecutive_reads = 0
                    
                    # Track current tab when clicking
                    if last_action == "click" and last_step.action.target:
                        target = last_step.action.target
                        # Extract tab name from target
                        tab_match = re.search(r"has-text\(['\"]([^'\"]+)['\"]", target)
                        if tab_match:
                            self._current_tab = tab_match.group(1)
                    
                    # Track explored tabs (tab was clicked, then read)
                    if last_action == "read_page" and self._current_tab and self._current_tab not in self._explored_tabs:
                        self._explored_tabs.append(self._current_tab)
                    
                    # Generate appropriate hints
                    if last_action == "click":
                        last_action_hint = f"\n⚠️ YOUR LAST ACTION WAS 'click' on '{self._current_tab}' - You MUST now use 'read_page' to see what's on this page!\n"
                    elif last_action == "read_page":
                        if self._consecutive_reads >= 2:
                            # FORCE progression after 2 consecutive reads
                            last_action_hint = f"\n🛑 STOP! You've called 'read_page' {self._consecutive_reads} times in a row on this tab!\n"
                            last_action_hint += f"✅ TAB '{self._current_tab}' IS NOW READ AND NOTED.\n"
                            last_action_hint += "🔄 YOU MUST NOW CLICK A DIFFERENT TAB to continue exploring.\n"
                            last_action_hint += f"Tabs already explored: {self._explored_tabs}\n"
                            last_action_hint += "Available tabs to explore: 'Berth Overview', 'Vessels Tracking', 'Gantt Chart', 'Digital Twin', 'Upcoming Vessels'\n"
                        else:
                            last_action_hint = f"\n✓ You just read '{self._current_tab}'. Now click the NEXT tab to continue or use 'complete' if done.\n"
                            last_action_hint += f"Tabs already explored: {self._explored_tabs}\n"
                    
            # Build explored tabs context
            explored_context = ""
            if self._explored_tabs:
                explored_context = f"\n## Tabs Already Explored and Read\n"
                explored_context += f"You have fully explored these tabs: {', '.join(self._explored_tabs)}\n"
                explored_context += f"DO NOT click these again unless necessary.\n"
            
            # OPTIMIZED: Shorter, more focused prompt for faster inference
            prompt = f"""## Task
{task}

## Context
{memory_context[:500]}
{tool_context}{explored_context}{last_action_hint}
## Current Page
{truncated_observation if truncated_observation else "No page loaded"}

## Decide Next Action (JSON only):
- After CLICK → use read_page
- After read_page → CLICK next tab or COMPLETE
- Tabs to explore: Upcoming Vessels, Vessel Tracking, Berth Overview, Digital Twin, Gantt Chart

JSON options:
1. {{"type":"browser","action_type":"read_page","reasoning":"..."}}
2. {{"type":"browser","action_type":"click","target":"button:has-text('Tab')","reasoning":"..."}}
3. {{"type":"tool","tool_name":"db_get_vessels","parameters":{{}},"reasoning":"..."}}
4. {{"type":"complete","reasoning":"...","final_summary":"Summary of all tabs visited..."}}
5. {{"type":"fail","reasoning":"..."}}

Output JSON ONLY:"""
            
            if self.use_qwen3:
                # OPTIMIZED: Use config max_tokens (smaller for faster inference)
                response_text = await self.llm.achat(
                    messages=[
                        {"role": "system", "content": OPTIMIZED_SYSTEM_PROMPT},  # Use optimized prompt
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.opt_config.max_tokens_decision,  # Optimized: 384 instead of 1024
                    temperature=self.opt_config.temperature  # Optimized: 0.1 for faster, deterministic
                )
            else:
                # Fallback to Claude
                response = self.claude.messages.create(
                    model=self.model,
                    max_tokens=self.opt_config.max_tokens_decision,
                    temperature=self.opt_config.temperature,
                    system=OPTIMIZED_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            
            # Parse response
            decision = self._parse_decision(response_text)
            
            if decision:
                logger.info(f"Decision [{self.model}]: type={decision.get('type')} - {decision.get('reasoning', '')[:50]}...")
                
                # OPTIMIZATION: Cache successful decisions for repeated patterns
                if self._decision_cache and decision.get('type') in ['browser', 'tool']:
                    self._decision_cache.set(observation, task, decision)
            
            return decision
            
        except Exception as e:
            logger.error(f"Decision failed: {e}")
            # Return a safe default action
            return {
                "type": "browser",
                "action_type": "read_page",
                "reasoning": f"Decision error, re-observing: {str(e)}",
                "confidence": 0.1
            }
    
    def _parse_decision(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse Claude's response into a decision dict"""
        try:
            # Try to extract JSON from response
            # Look for JSON block in markdown
            json_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response_text)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to parse entire response as JSON
            # Find first { and last }
            start = response_text.find('{')
            end = response_text.rfind('}')
            if start != -1 and end != -1:
                return json.loads(response_text[start:end+1])
            
            logger.warning(f"Could not parse decision from: {response_text[:200]}")
            return None
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse error: {e}")
            return None
    
    async def _generate_task_summary(self, original_task: str) -> str:
        """
        Generate a comprehensive user-friendly summary of the task execution.
        GPU-accelerated via Ollama for fast local inference.
        This summarizes the ENTIRE journey through all tabs/pages visited.
        
        Args:
            original_task: The original task description
            
        Returns:
            A comprehensive, structured, user-friendly summary
        """
        try:
            # Gather comprehensive context
            task_summary = self.memory.get_task_summary() if self.memory else {}
            tool_summary = []
            data_findings = {}
            key_metrics = []
            ai_insights = []
            
            # Extract detailed data from tool calls
            for tc in self._tool_calls[-20:]:  # Last 20 tool calls for comprehensive view
                tool_name = tc.get('tool', 'unknown')
                tool_result = tc.get('result', {})
                tool_summary.append(f"• {tool_name}: {tc.get('summary', 'executed')}")
                
                # Extract key data from tool calls
                if tc.get('success'):
                    if 'vessels' in tool_name.lower() or 'vessel' in tool_name.lower():
                        if isinstance(tool_result, list):
                            data_findings['vessels'] = f"Retrieved {len(tool_result)} vessels"
                        elif isinstance(tool_result, dict) and 'data' in tool_result:
                            data_findings['vessels'] = f"Vessel data: {len(tool_result.get('data', []))} records"
                    
                    elif 'berth' in tool_name.lower():
                        if isinstance(tool_result, list):
                            data_findings['berths'] = f"Retrieved {len(tool_result)} berths"
                        elif isinstance(tool_result, dict):
                            if 'allocation' in str(tool_result).lower():
                                ai_insights.append(f"Berth allocation: {tool_result.get('berth_name', 'assigned')}")
                    
                    elif 'schedule' in tool_name.lower():
                        data_findings['schedules'] = "Schedule data accessed"
                    
                    elif 'predict' in tool_name.lower() or 'ml_' in tool_name:
                        if isinstance(tool_result, dict):
                            if 'predicted_eta' in tool_result:
                                ai_insights.append(f"ETA Prediction: {tool_result.get('predicted_eta')}")
                            if 'confidence' in tool_result:
                                key_metrics.append(f"Confidence: {tool_result.get('confidence', 0)*100:.1f}%")
                            if 'score' in str(tool_result).lower():
                                ai_insights.append(f"AI Score calculated")
                    
                    elif 'conflict' in tool_name.lower():
                        ai_insights.append("Conflict detection performed")
                    
                    elif 'weather' in tool_name.lower():
                        data_findings['weather'] = "Weather data retrieved"
            
            pages_visited = task_summary.get('urls_visited', [])
            total_steps = task_summary.get('total_steps', len(self._tool_calls))
            
            # Build structured prompt for GPU-accelerated summary generation
            prompt = f"""/no_think
You are an AI assistant generating a structured summary report for a Browser Agent task.

═══════════════════════════════════════════════════════════════
TASK EXECUTION REPORT - SmartBerth Port Management System
═══════════════════════════════════════════════════════════════

📋 ORIGINAL REQUEST:
{original_task}

📊 EXECUTION METRICS:
• Total steps: {total_steps}
• Pages visited: {len(pages_visited) if pages_visited else 1}
• Tools executed: {len(self._tool_calls)}
• Data sources queried: {len(data_findings)}

🔗 PAGES/SECTIONS EXPLORED:
{chr(10).join(['• ' + p for p in pages_visited]) if pages_visited else '• Current page only'}

🛠️ TOOLS USED:
{chr(10).join(tool_summary[:10]) if tool_summary else '• Direct browser observation only'}

📈 DATA RETRIEVED:
{chr(10).join(['• ' + v for v in data_findings.values()]) if data_findings else '• UI-based data observation'}

🤖 AI/ML INSIGHTS:
{chr(10).join(['• ' + i for i in ai_insights]) if ai_insights else '• No ML predictions in this task'}

Generate a COMPREHENSIVE SUMMARY (6-10 sentences) with the following structure:

**📝 SUMMARY:**
[Brief overview of what was accomplished]

**🔍 KEY FINDINGS:**
[Bullet points of main discoveries]

**💡 RECOMMENDATIONS:**
[Actionable insights based on findings]

**⚠️ NOTES:**
[Any issues, warnings, or important observations]

Write in a professional, clear style. Include specific data points and numbers where available."""

            # GPU-accelerated summary generation via Ollama
            start_time = time.time()
            
            if self.use_qwen3:
                # Use Qwen3 with GPU acceleration for fast inference
                summary = await self.llm.achat(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,  # Longer for comprehensive structured summary
                    temperature=0.2,  # Lower for more consistent output
                    top_p=0.85
                )
            else:
                response = self.claude.messages.create(
                    model=self.model,
                    max_tokens=800,
                    temperature=0.2,
                    messages=[{"role": "user", "content": prompt}]
                )
                summary = response.content[0].text
            
            generation_time = time.time() - start_time
            logger.info(f"Summary generated in {generation_time:.2f}s (GPU-accelerated: {self.use_qwen3})")
            
            # Add generation metadata footer
            summary_with_meta = f"""{summary.strip()}

─────────────────────────────────────────────────────────────
📊 Generated by SmartBerth AI | Model: {self.model}
⏱️  Generation time: {generation_time:.2f}s (GPU-accelerated)
🔧 Tools used: {len(self._tool_calls)} | Steps: {total_steps}
─────────────────────────────────────────────────────────────"""
            
            return summary_with_meta
            
        except Exception as e:
            logger.warning(f"Failed to generate summary: {e}")
            # Fallback to basic structured summary
            return f"""📝 **TASK COMPLETED**

**Request:** {original_task[:100]}...
**Operations:** {len(self._tool_calls)} tool executions performed
**Status:** Task completed with basic summary (detailed generation unavailable)

⚠️ Note: GPU-accelerated summary generation encountered an issue: {str(e)[:100]}"""
    
    async def _execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an internal tool and return results.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool result as dict
        """
        if not self.tools_registry:
            return {"error": "Tools registry not available"}
        
        logger.info(f"Executing tool: {tool_name} with params: {parameters}")
        
        # Execute the tool
        result: ToolResult = await self.tools_registry.execute(tool_name, parameters)
        
        # Record tool call
        tool_record = {
            "tool": tool_name,
            "parameters": parameters,
            "success": result.success,
            "timestamp": datetime.now().isoformat(),
            "execution_time_ms": result.execution_time_ms,
            "summary": self._summarize_tool_result(tool_name, result)
        }
        self._tool_calls.append(tool_record)
        
        # Notify UI
        if self._on_tool_call:
            try:
                await self._on_tool_call(tool_name, parameters, result.data if result.success else result.error)
            except Exception as e:
                logger.warning(f"Tool call callback error: {e}")
        
        if result.success:
            return {"success": True, "data": result.data}
        else:
            return {"success": False, "error": result.error}
    
    def _summarize_tool_result(self, tool_name: str, result: ToolResult) -> str:
        """Create a brief summary of tool result for memory context"""
        if not result.success:
            return f"Failed: {result.error}"
        
        data = result.data
        if isinstance(data, list):
            return f"Returned {len(data)} items"
        elif isinstance(data, dict):
            if "error" in data:
                return f"Error: {data['error']}"
            return f"Returned dict with keys: {list(data.keys())[:5]}"
        else:
            return f"Returned: {str(data)[:100]}"
    
    async def _act(self, action: BrowserAction) -> ActionResult:
        """
        Execute an action.
        
        Args:
            action: Action to execute
            
        Returns:
            ActionResult
        """
        result = await self.executor.execute(action)
        
        # Handle errors
        if not result.success:
            self.memory.add_error(
                result.error_message or "Unknown error",
                action
            )
            
            # Check for repeated errors
            if self.memory.has_repeated_errors(threshold=3):
                logger.warning("Repeated errors detected - task may be stuck")
        
        return result
    
    def stop(self):
        """Stop the current task"""
        self._should_stop = True
        logger.info("Stop requested")
    
    def pause(self):
        """Pause the agent"""
        self._state = AgentState.PAUSED
        logger.info("Agent paused")
    
    def resume(self):
        """Resume the agent"""
        if self._state == AgentState.PAUSED:
            self._state = AgentState.IDLE
            logger.info("Agent resumed")
    
    # ==================== CONVENIENCE METHODS ====================
    
    async def quick_task(
        self,
        description: str,
        url: str = "http://localhost:5173"
    ) -> Dict[str, Any]:
        """
        Execute a quick task with default settings.
        
        Args:
            description: What to do
            url: Target URL (defaults to local frontend)
            
        Returns:
            Task result
        """
        # Initialize if needed
        if not self.browser or not self.browser.is_ready:
            if not await self.initialize():
                return {"success": False, "error": "Failed to initialize"}
        
        task = AgentTask(
            task_id=f"quick_{datetime.now().strftime('%H%M%S')}",
            description=description,
            target_url=url,
            max_steps=30
        )
        
        return await self.execute_task(task)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status"""
        return {
            "state": self._state.value,
            "is_running": self._is_running,
            "current_task": self._current_task.description if self._current_task else None,
            "step_count": self.memory.step_count if self.memory else 0,
            "browser_ready": self.browser.is_ready if self.browser else False,
            "tools_available": TOOLS_AVAILABLE,
            "tool_count": len(self.tools_registry._tools) if self.tools_registry else 0,
            "tool_calls_this_session": len(self._tool_calls),
            "model": self.model,
            "using_qwen3": self.use_qwen3,
            "gpu_accelerated": True,  # Ollama uses GPU for inference
            # Optimization info
            "performance_mode": self.opt_config.mode.value if self.opt_config else "unknown",
            "max_tokens": self.opt_config.max_tokens_decision if self.opt_config else 1024,
            "step_delay_ms": self.opt_config.step_delay_ms if self.opt_config else 500,
            "cache_hits": self._decision_cache.get_stats()["hits"] if self._decision_cache else 0,
            "cache_misses": self._decision_cache.get_stats()["misses"] if self._decision_cache else 0
        }
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of current/last execution"""
        if not self.memory:
            return {}
        
        return {
            "task_summary": self.memory.get_task_summary(),
            "recent_steps": [s.to_dict() for s in self.memory.get_recent_steps(10)],
            "action_stats": self.memory.get_action_history_summary(),
            "tool_calls": self._tool_calls[-10:] if self._tool_calls else []
        }
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available internal tools for API/UI"""
        if not self.tools_registry:
            return []
        
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category.value,
                "parameters": tool.parameters,
                "examples": tool.examples
            }
            for tool in self.tools_registry.list_tools()
        ]
    
    async def execute_tool_direct(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a tool directly without going through the agent loop.
        Useful for API endpoints that need specific tool results.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            Tool result
        """
        if not self.tools_registry:
            return {"success": False, "error": "Tools registry not available"}
        
        return await self._execute_tool(tool_name, parameters or {})
    
    def get_tool_call_history(self) -> List[Dict[str, Any]]:
        """Get history of tool calls in this session"""
        return self._tool_calls.copy()
    
    def clear_tool_history(self):
        """Clear tool call history"""
        self._tool_calls = []


# Factory function for easy creation
def create_browser_agent(
    headless: bool = False,
    on_step: Optional[Callable[[AgentStep], Awaitable[None]]] = None,
    on_tool_call: Optional[Callable[[str, Dict, Any], Awaitable[None]]] = None,
    performance_mode: str = "fast"  # ultra_fast, fast, balanced, quality
) -> AgenticBrowserController:
    """
    Factory function to create a browser agent.
    
    Args:
        headless: Run browser in headless mode
        on_step: Callback for step updates (for UI streaming)
        on_tool_call: Callback for tool call updates
        performance_mode: Performance preset - 'ultra_fast', 'fast', 'balanced', 'quality'
        
    Returns:
        Configured AgenticBrowserController
    """
    return AgenticBrowserController(
        headless=headless,
        on_step=on_step,
        on_tool_call=on_tool_call,
        performance_mode=performance_mode
    )
