"""
SmartBerth Agentic Tools Layer
==============================

This module exposes all internal system capabilities as tools that the agentic
browser controller can use. This is the "hands" of the agent - what allows it
to interact with:

1. Database - Query vessels, berths, schedules, resources
2. ML Pipeline - Run predictions, train models, get status
3. Manager Agent (Qwen3) - Task routing, planning, simple responses
4. RAG System - Knowledge retrieval, semantic search
5. Graph System - Relationship queries, path finding
6. Browser - Web automation (already in browser_controller)

The agent LLM decides which tools to call based on the user's task.
Each tool returns structured data that the agent can use to proceed.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Categories of tools"""
    DATABASE = "database"
    ML_PIPELINE = "ml_pipeline"
    MANAGER = "manager"
    RAG = "rag"
    GRAPH = "graph"
    BROWSER = "browser"
    SYSTEM = "system"
    SCREEN_CONTROL = "screen_control"  # Windows screen control via pyautogui


@dataclass
class ToolResult:
    """Result from a tool execution"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: float = 0.0


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by the agent"""
    name: str
    description: str
    category: ToolCategory
    parameters: Dict[str, Any]  # JSON Schema for parameters
    examples: List[str] = field(default_factory=list)
    handler: Optional[Callable] = None


class AgentToolRegistry:
    """
    Registry of all tools available to the agentic system.
    This is the central place where we expose internal capabilities.
    """
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._handlers: Dict[str, Callable] = {}
        
        # Initialize database service
        self._db_service = None
        self._pipeline = None
        self._manager_agent = None
        self._rag_pipeline = None
        
        # Register all tools
        self._register_database_tools()
        self._register_ml_pipeline_tools()
        self._register_manager_tools()
        self._register_rag_tools()
        self._register_system_tools()
        self._register_screen_control_tools()  # Add screen control tools
        
        logger.info(f"AgentToolRegistry initialized with {len(self._tools)} tools")
    
    def _get_db(self):
        """Lazy load database service"""
        if self._db_service is None:
            try:
                from database import get_db_service
                self._db_service = get_db_service()
            except Exception as e:
                logger.error(f"Failed to initialize database service: {e}")
        return self._db_service
    
    def _get_pipeline(self):
        """Lazy load unified pipeline"""
        if self._pipeline is None:
            try:
                from pipeline_api import get_pipeline
                self._pipeline = get_pipeline()
            except Exception as e:
                logger.warning(f"Failed to initialize pipeline: {e}")
        return self._pipeline
    
    def _get_manager(self):
        """Lazy load manager agent"""
        if self._manager_agent is None:
            try:
                from manager_agent import get_manager_agent
                self._manager_agent = get_manager_agent()
            except Exception as e:
                logger.warning(f"Failed to initialize manager agent: {e}")
        return self._manager_agent
    
    def _get_rag(self):
        """Lazy load RAG pipeline"""
        if self._rag_pipeline is None:
            try:
                from rag import get_rag_pipeline
                self._rag_pipeline = get_rag_pipeline()
            except Exception as e:
                logger.warning(f"Failed to initialize RAG pipeline: {e}")
        return self._rag_pipeline
    
    # ==================== DATABASE TOOLS ====================
    
    def _register_database_tools(self):
        """Register all database-related tools"""
        
        # Get all vessels
        self._tools["db_get_vessels"] = ToolDefinition(
            name="db_get_vessels",
            description="Get all vessels from the database with their details (LOA, beam, draft, cargo type, etc.)",
            category=ToolCategory.DATABASE,
            parameters={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status: 'Scheduled', 'Approaching', 'Berthed', 'Departed'",
                        "enum": ["Scheduled", "Approaching", "Berthed", "Departed", None]
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of vessels to return",
                        "default": 50
                    }
                }
            },
            examples=[
                "Get all vessels in the system",
                "Show me vessels that are currently approaching",
                "List berthed vessels"
            ]
        )
        self._handlers["db_get_vessels"] = self._handle_get_vessels
        
        # Get vessel by ID
        self._tools["db_get_vessel"] = ToolDefinition(
            name="db_get_vessel",
            description="Get detailed information about a specific vessel by its ID or name",
            category=ToolCategory.DATABASE,
            parameters={
                "type": "object",
                "properties": {
                    "vessel_id": {"type": "integer", "description": "Vessel ID"},
                    "vessel_name": {"type": "string", "description": "Vessel name (partial match)"}
                },
                "oneOf": [
                    {"required": ["vessel_id"]},
                    {"required": ["vessel_name"]}
                ]
            },
            examples=[
                "Get details for vessel ID 5",
                "Find vessel named 'Ever Given'"
            ]
        )
        self._handlers["db_get_vessel"] = self._handle_get_vessel
        
        # Get all berths
        self._tools["db_get_berths"] = ToolDefinition(
            name="db_get_berths",
            description="Get all berths with their specifications (max LOA, depth, equipment)",
            category=ToolCategory.DATABASE,
            parameters={
                "type": "object",
                "properties": {
                    "terminal_id": {"type": "integer", "description": "Filter by terminal ID"},
                    "available_only": {"type": "boolean", "description": "Only return available berths"}
                }
            },
            examples=[
                "List all berths",
                "Show available berths in terminal 1"
            ]
        )
        self._handlers["db_get_berths"] = self._handle_get_berths
        
        # Get schedules
        self._tools["db_get_schedules"] = ToolDefinition(
            name="db_get_schedules",
            description="Get vessel schedules - includes ETA, ETD, berth assignments, status",
            category=ToolCategory.DATABASE,
            parameters={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status"},
                    "start_date": {"type": "string", "description": "Start date (ISO format)"},
                    "end_date": {"type": "string", "description": "End date (ISO format)"},
                    "berth_id": {"type": "integer", "description": "Filter by berth ID"}
                }
            },
            examples=[
                "Show active schedules",
                "Get schedules for next 48 hours",
                "What's scheduled at Berth 3?"
            ]
        )
        self._handlers["db_get_schedules"] = self._handle_get_schedules
        
        # Get resources (pilots, tugs)
        self._tools["db_get_resources"] = ToolDefinition(
            name="db_get_resources",
            description="Get port resources - pilots, tugboats, cranes",
            category=ToolCategory.DATABASE,
            parameters={
                "type": "object",
                "properties": {
                    "resource_type": {
                        "type": "string",
                        "enum": ["pilots", "tugs", "cranes", "all"]
                    }
                }
            },
            examples=[
                "How many pilots are available?",
                "Show tugboat capacity"
            ]
        )
        self._handlers["db_get_resources"] = self._handle_get_resources
        
        # Execute custom query (read-only)
        self._tools["db_query"] = ToolDefinition(
            name="db_query",
            description="Execute a custom read-only SQL query on the database",
            category=ToolCategory.DATABASE,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL SELECT query to execute"}
                },
                "required": ["query"]
            },
            examples=[
                "Count vessels by type",
                "Find busiest berth this week"
            ]
        )
        self._handlers["db_query"] = self._handle_db_query
    
    # ==================== ML PIPELINE TOOLS ====================
    
    def _register_ml_pipeline_tools(self):
        """Register ML pipeline tools"""
        
        # ETA Prediction
        self._tools["ml_predict_eta"] = ToolDefinition(
            name="ml_predict_eta",
            description="Run ML model to predict ETA for a vessel",
            category=ToolCategory.ML_PIPELINE,
            parameters={
                "type": "object",
                "properties": {
                    "vessel_id": {"type": "integer", "description": "Vessel ID"},
                    "include_weather": {"type": "boolean", "default": True},
                    "include_traffic": {"type": "boolean", "default": True}
                },
                "required": ["vessel_id"]
            },
            examples=[
                "Predict ETA for vessel 12",
                "When will vessel 7 arrive?"
            ]
        )
        self._handlers["ml_predict_eta"] = self._handle_predict_eta
        
        # Berth Recommendation
        self._tools["ml_recommend_berth"] = ToolDefinition(
            name="ml_recommend_berth",
            description="Get AI-powered berth recommendations for a vessel",
            category=ToolCategory.ML_PIPELINE,
            parameters={
                "type": "object",
                "properties": {
                    "vessel_id": {"type": "integer", "description": "Vessel ID"},
                    "preferred_eta": {"type": "string", "description": "Preferred arrival time (ISO format)"},
                    "top_n": {"type": "integer", "default": 3, "description": "Number of recommendations"}
                },
                "required": ["vessel_id"]
            },
            examples=[
                "Recommend berth for vessel 5",
                "Best berth options for container ship arriving tomorrow"
            ]
        )
        self._handlers["ml_recommend_berth"] = self._handle_recommend_berth
        
        # Conflict Detection
        self._tools["ml_detect_conflicts"] = ToolDefinition(
            name="ml_detect_conflicts",
            description="Detect scheduling conflicts in the port",
            category=ToolCategory.ML_PIPELINE,
            parameters={
                "type": "object",
                "properties": {
                    "hours_ahead": {"type": "integer", "default": 48},
                    "include_resolution": {"type": "boolean", "default": True}
                }
            },
            examples=[
                "Are there any scheduling conflicts?",
                "Check for conflicts in next 24 hours"
            ]
        )
        self._handlers["ml_detect_conflicts"] = self._handle_detect_conflicts
        
        # Pipeline Status
        self._tools["ml_pipeline_status"] = ToolDefinition(
            name="ml_pipeline_status",
            description="Get status of the ML pipeline components",
            category=ToolCategory.ML_PIPELINE,
            parameters={
                "type": "object",
                "properties": {}
            },
            examples=[
                "Is the ML pipeline running?",
                "Check model status"
            ]
        )
        self._handlers["ml_pipeline_status"] = self._handle_pipeline_status
        
        # Train Model
        self._tools["ml_trigger_training"] = ToolDefinition(
            name="ml_trigger_training",
            description="Trigger model training/fine-tuning (admin only)",
            category=ToolCategory.ML_PIPELINE,
            parameters={
                "type": "object",
                "properties": {
                    "model_type": {
                        "type": "string",
                        "enum": ["eta_predictor", "berth_optimizer", "demand_forecaster"]
                    },
                    "epochs": {"type": "integer", "default": 10}
                }
            },
            examples=[
                "Train ETA prediction model",
                "Retrain berth optimizer"
            ]
        )
        self._handlers["ml_trigger_training"] = self._handle_trigger_training
    
    # ==================== MANAGER AGENT TOOLS ====================
    
    def _register_manager_tools(self):
        """Register manager agent (Qwen3) tools"""
        
        # Classify query
        self._tools["manager_classify"] = ToolDefinition(
            name="manager_classify",
            description="Use Qwen3 manager to classify a user query into task types",
            category=ToolCategory.MANAGER,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "User query to classify"}
                },
                "required": ["query"]
            },
            examples=[
                "Classify: where should vessel X berth?",
                "What type of query is this?"
            ]
        )
        self._handlers["manager_classify"] = self._handle_manager_classify
        
        # Create execution plan
        self._tools["manager_plan"] = ToolDefinition(
            name="manager_plan",
            description="Use Qwen3 to create an execution plan for a complex task",
            category=ToolCategory.MANAGER,
            parameters={
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task description"},
                    "context": {"type": "object", "description": "Additional context"}
                },
                "required": ["task"]
            },
            examples=[
                "Plan how to optimize tomorrow's schedule",
                "Create plan for handling vessel delay"
            ]
        )
        self._handlers["manager_plan"] = self._handle_manager_plan
        
        # Quick response
        self._tools["manager_respond"] = ToolDefinition(
            name="manager_respond",
            description="Get a quick response from Qwen3 for simple queries",
            category=ToolCategory.MANAGER,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "context": {"type": "string", "default": ""}
                },
                "required": ["query"]
            },
            examples=[
                "Quick answer to simple question",
                "Summarize this data"
            ]
        )
        self._handlers["manager_respond"] = self._handle_manager_respond
    
    # ==================== RAG TOOLS ====================
    
    def _register_rag_tools(self):
        """Register RAG (retrieval-augmented generation) tools"""
        
        # Semantic search
        self._tools["rag_search"] = ToolDefinition(
            name="rag_search",
            description="Search the knowledge base using semantic similarity",
            category=ToolCategory.RAG,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                    "category": {"type": "string", "description": "Filter by category"}
                },
                "required": ["query"]
            },
            examples=[
                "Search for berth allocation rules",
                "Find UKC calculation formula"
            ]
        )
        self._handlers["rag_search"] = self._handle_rag_search
        
        # Generate explanation
        self._tools["rag_explain"] = ToolDefinition(
            name="rag_explain",
            description="Generate an explanation using RAG with knowledge base context",
            category=ToolCategory.RAG,
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "include_sources": {"type": "boolean", "default": True}
                },
                "required": ["query"]
            },
            examples=[
                "Explain why vessel X can't berth at Y",
                "What are the safety rules for tankers?"
            ]
        )
        self._handlers["rag_explain"] = self._handle_rag_explain
    
    # ==================== SYSTEM TOOLS ====================
    
    def _register_system_tools(self):
        """Register system utility tools"""
        
        # Get current time
        self._tools["system_time"] = ToolDefinition(
            name="system_time",
            description="Get current system time in various formats",
            category=ToolCategory.SYSTEM,
            parameters={
                "type": "object",
                "properties": {
                    "format": {"type": "string", "default": "iso"}
                }
            },
            examples=["What time is it?"]
        )
        self._handlers["system_time"] = self._handle_system_time
        
        # Get system health
        self._tools["system_health"] = ToolDefinition(
            name="system_health",
            description="Get health status of all system components",
            category=ToolCategory.SYSTEM,
            parameters={"type": "object", "properties": {}},
            examples=["Is everything running?"]
        )
        self._handlers["system_health"] = self._handle_system_health
    
    # ==================== SCREEN CONTROL TOOLS ====================
    
    def _register_screen_control_tools(self):
        """
        Register screen control tools using pyautogui.
        These allow the agent to control the Windows desktop while navigating.
        """
        
        # Move mouse
        self._tools["screen_move_mouse"] = ToolDefinition(
            name="screen_move_mouse",
            description="Move the mouse cursor to a specific position on screen",
            category=ToolCategory.SCREEN_CONTROL,
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate"},
                    "y": {"type": "integer", "description": "Y coordinate"},
                    "duration": {"type": "number", "default": 0.3, "description": "Movement duration in seconds"}
                },
                "required": ["x", "y"]
            },
            examples=["Move mouse to 100, 200", "Navigate cursor to button"]
        )
        self._handlers["screen_move_mouse"] = self._handle_screen_move_mouse
        
        # Click
        self._tools["screen_click"] = ToolDefinition(
            name="screen_click",
            description="Click at current mouse position or specified coordinates",
            category=ToolCategory.SCREEN_CONTROL,
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate (optional)"},
                    "y": {"type": "integer", "description": "Y coordinate (optional)"},
                    "button": {"type": "string", "enum": ["left", "right", "middle"], "default": "left"},
                    "clicks": {"type": "integer", "default": 1, "description": "Number of clicks"}
                }
            },
            examples=["Click button", "Double click icon", "Right click menu"]
        )
        self._handlers["screen_click"] = self._handle_screen_click
        
        # Type text
        self._tools["screen_type"] = ToolDefinition(
            name="screen_type",
            description="Type text at current cursor position",
            category=ToolCategory.SCREEN_CONTROL,
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to type"},
                    "interval": {"type": "number", "default": 0.02, "description": "Interval between keystrokes"}
                },
                "required": ["text"]
            },
            examples=["Type search query", "Enter vessel name"]
        )
        self._handlers["screen_type"] = self._handle_screen_type
        
        # Press key
        self._tools["screen_hotkey"] = ToolDefinition(
            name="screen_hotkey",
            description="Press a keyboard hotkey or key combination",
            category=ToolCategory.SCREEN_CONTROL,
            parameters={
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array", 
                        "items": {"type": "string"},
                        "description": "Keys to press together (e.g., ['ctrl', 'c'])"
                    }
                },
                "required": ["keys"]
            },
            examples=["Press Enter", "Ctrl+C to copy", "Alt+Tab to switch windows"]
        )
        self._handlers["screen_hotkey"] = self._handle_screen_hotkey
        
        # Screenshot
        self._tools["screen_screenshot"] = ToolDefinition(
            name="screen_screenshot",
            description="Take a screenshot of the screen or a region",
            category=ToolCategory.SCREEN_CONTROL,
            parameters={
                "type": "object",
                "properties": {
                    "region": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"},
                            "width": {"type": "integer"},
                            "height": {"type": "integer"}
                        },
                        "description": "Region to capture (optional, full screen if not specified)"
                    },
                    "save_path": {"type": "string", "description": "Path to save screenshot (optional)"}
                }
            },
            examples=["Capture screen", "Take screenshot of berth table"]
        )
        self._handlers["screen_screenshot"] = self._handle_screen_screenshot
        
        # Get screen size
        self._tools["screen_size"] = ToolDefinition(
            name="screen_size",
            description="Get the screen resolution/size",
            category=ToolCategory.SCREEN_CONTROL,
            parameters={"type": "object", "properties": {}},
            examples=["Get screen dimensions"]
        )
        self._handlers["screen_size"] = self._handle_screen_size
        
        # Scroll
        self._tools["screen_scroll"] = ToolDefinition(
            name="screen_scroll",
            description="Scroll the mouse wheel up or down",
            category=ToolCategory.SCREEN_CONTROL,
            parameters={
                "type": "object",
                "properties": {
                    "clicks": {"type": "integer", "description": "Number of scroll clicks (positive=up, negative=down)"},
                    "x": {"type": "integer", "description": "X position to scroll at (optional)"},
                    "y": {"type": "integer", "description": "Y position to scroll at (optional)"}
                },
                "required": ["clicks"]
            },
            examples=["Scroll down the page", "Scroll up to see more vessels"]
        )
        self._handlers["screen_scroll"] = self._handle_screen_scroll
        
        # Locate on screen
        self._tools["screen_locate_text"] = ToolDefinition(
            name="screen_locate_text",
            description="Get current mouse position",
            category=ToolCategory.SCREEN_CONTROL,
            parameters={"type": "object", "properties": {}},
            examples=["Where is the mouse?", "Get cursor position"]
        )
        self._handlers["screen_locate_text"] = self._handle_screen_get_position
    
    # ==================== TOOL EXECUTION ====================
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name"""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
        """List all available tools, optionally filtered by category"""
        if category:
            return [t for t in self._tools.values() if t.category == category]
        return list(self._tools.values())
    
    def get_tools_schema(self) -> str:
        """Get a formatted schema of all tools for LLM prompt"""
        schema_parts = []
        for name, tool in self._tools.items():
            schema_parts.append(f"""
Tool: {name}
Description: {tool.description}
Category: {tool.category.value}
Parameters: {json.dumps(tool.parameters, indent=2)}
Examples: {', '.join(tool.examples[:2]) if tool.examples else 'N/A'}
""")
        return "\n---\n".join(schema_parts)
    
    async def execute(self, tool_name: str, parameters: Dict[str, Any] = None) -> ToolResult:
        """Execute a tool by name with given parameters"""
        start_time = datetime.now()
        
        if tool_name not in self._handlers:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {tool_name}",
                metadata={"available_tools": list(self._tools.keys())}
            )
        
        try:
            handler = self._handlers[tool_name]
            result = await handler(parameters or {})
            
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return ToolResult(
                success=True,
                data=result,
                execution_time_ms=execution_time,
                metadata={"tool": tool_name}
            )
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"tool": tool_name}
            )
    
    # ==================== HANDLER IMPLEMENTATIONS ====================
    
    async def _handle_get_vessels(self, params: Dict[str, Any]) -> List[Dict]:
        """Handler for db_get_vessels"""
        db = self._get_db()
        if not db:
            return []
        
        status = params.get("status")
        limit = params.get("limit", 50)
        
        if status:
            vessels = db.get_vessels_by_status(status)
        else:
            vessels = db.get_all_vessels()
        
        return vessels[:limit]
    
    async def _handle_get_vessel(self, params: Dict[str, Any]) -> Optional[Dict]:
        """Handler for db_get_vessel"""
        db = self._get_db()
        if not db:
            return None
        
        if "vessel_id" in params:
            return db.get_vessel_by_id(params["vessel_id"])
        elif "vessel_name" in params:
            # Search by name
            all_vessels = db.get_all_vessels()
            name_lower = params["vessel_name"].lower()
            for v in all_vessels:
                if name_lower in v.get("VesselName", "").lower():
                    return v
        return None
    
    async def _handle_get_berths(self, params: Dict[str, Any]) -> List[Dict]:
        """Handler for db_get_berths"""
        db = self._get_db()
        if not db:
            return []
        
        berths = db.get_all_berths()
        
        terminal_id = params.get("terminal_id")
        if terminal_id:
            berths = [b for b in berths if b.get("TerminalId") == terminal_id]
        
        return berths
    
    async def _handle_get_schedules(self, params: Dict[str, Any]) -> List[Dict]:
        """Handler for db_get_schedules"""
        db = self._get_db()
        if not db:
            return []
        
        status = params.get("status")
        start_date = params.get("start_date")
        end_date = params.get("end_date")
        
        if start_date and end_date:
            return db.get_schedules_in_range(start_date, end_date)
        elif status:
            return db.get_vessels_by_status(status)
        else:
            return db.get_active_schedules()
    
    async def _handle_get_resources(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for db_get_resources"""
        db = self._get_db()
        if not db:
            return {}
        
        resource_type = params.get("resource_type", "all")
        result = {}
        
        try:
            if resource_type in ["pilots", "all"]:
                result["pilots"] = db.execute_query(
                    "SELECT * FROM PILOTS WHERE IsActive = 1"
                )
            if resource_type in ["tugs", "all"]:
                result["tugs"] = db.execute_query(
                    "SELECT * FROM TUGBOATS WHERE IsActive = 1"
                )
            if resource_type in ["cranes", "all"]:
                result["cranes"] = db.execute_query(
                    "SELECT * FROM CRANES WHERE Status = 'Operational'"
                )
        except Exception as e:
            logger.warning(f"Resource query failed: {e}")
        
        return result
    
    async def _handle_db_query(self, params: Dict[str, Any]) -> List[Dict]:
        """Handler for db_query - read-only custom queries"""
        db = self._get_db()
        if not db:
            return []
        
        query = params.get("query", "")
        
        # Safety: Only allow SELECT queries
        if not query.strip().upper().startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")
        
        # Block dangerous keywords
        dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "TRUNCATE", "ALTER", "CREATE", "EXEC"]
        query_upper = query.upper()
        for word in dangerous:
            if word in query_upper:
                raise ValueError(f"Query contains forbidden keyword: {word}")
        
        return db.execute_query(query)
    
    async def _handle_predict_eta(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for ml_predict_eta"""
        try:
            from services import get_eta_predictor
            predictor = get_eta_predictor()
            
            vessel_id = params["vessel_id"]
            result = predictor.predict_eta(vessel_id)
            
            return {
                "vessel_id": vessel_id,
                "predicted_eta": result.predicted_eta.isoformat() if result.predicted_eta else None,
                "confidence": result.confidence_score,
                "deviation_minutes": result.deviation_minutes,
                "status": result.status,
                "explanation": result.ai_explanation
            }
        except Exception as e:
            logger.error(f"ETA prediction failed: {e}")
            return {"error": str(e)}
    
    async def _handle_recommend_berth(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for ml_recommend_berth"""
        try:
            from services import get_berth_allocator
            allocator = get_berth_allocator()
            
            vessel_id = params["vessel_id"]
            top_n = params.get("top_n", 3)
            
            recommendations = allocator.get_berth_recommendations(vessel_id, top_n=top_n)
            
            return {
                "vessel_id": vessel_id,
                "recommendations": [
                    {
                        "berth_id": r.berth_id,
                        "berth_name": r.berth_name,
                        "score": r.total_score,
                        "is_feasible": r.is_feasible,
                        "explanation": r.explanation
                    }
                    for r in recommendations
                ]
            }
        except Exception as e:
            logger.error(f"Berth recommendation failed: {e}")
            return {"error": str(e)}
    
    async def _handle_detect_conflicts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for ml_detect_conflicts"""
        try:
            pipeline = self._get_pipeline()
            if pipeline and hasattr(pipeline, 'detect_conflicts'):
                hours = params.get("hours_ahead", 48)
                conflicts = pipeline.detect_conflicts(hours)
                return {"conflicts": conflicts, "hours_checked": hours}
            return {"conflicts": [], "message": "Conflict detection not available"}
        except Exception as e:
            return {"error": str(e)}
    
    async def _handle_pipeline_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for ml_pipeline_status"""
        pipeline = self._get_pipeline()
        
        status = {
            "pipeline_available": pipeline is not None,
            "components": {}
        }
        
        if pipeline:
            status["components"] = {
                "knowledge_index": pipeline._index_initialized if hasattr(pipeline, '_index_initialized') else False,
                "graph_engine": pipeline._graph_engine is not None if hasattr(pipeline, '_graph_engine') else False,
                "manager_agent": pipeline._manager_agent is not None if hasattr(pipeline, '_manager_agent') else False,
                "central_llm": pipeline._central_llm is not None if hasattr(pipeline, '_central_llm') else False,
            }
        
        return status
    
    async def _handle_trigger_training(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for ml_trigger_training"""
        # This would trigger actual training - placeholder for now
        return {
            "status": "queued",
            "model_type": params.get("model_type"),
            "message": "Training job queued (admin approval required)"
        }
    
    async def _handle_manager_classify(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for manager_classify"""
        manager = self._get_manager()
        if not manager:
            return {"error": "Manager agent not available"}
        
        query = params["query"]
        result = manager.classify_query(query)
        
        return {
            "query": query,
            "task_type": result.task_type.value if hasattr(result.task_type, 'value') else str(result.task_type),
            "confidence": result.confidence,
            "entities": result.entities
        }
    
    async def _handle_manager_plan(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for manager_plan"""
        manager = self._get_manager()
        if not manager:
            return {"error": "Manager agent not available"}
        
        task = params["task"]
        
        # First classify, then plan
        classification = manager.classify_query(task)
        plan = manager.create_plan(classification)
        
        return {
            "task": task,
            "classification": classification.task_type.value if hasattr(classification.task_type, 'value') else str(classification.task_type),
            "steps": plan.steps,
            "requires_rag": plan.requires_rag,
            "requires_graph": plan.requires_graph
        }
    
    async def _handle_manager_respond(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for manager_respond"""
        manager = self._get_manager()
        if not manager:
            return {"error": "Manager agent not available"}
        
        query = params["query"]
        context = params.get("context", "")
        
        # Use local LLM for quick response
        if hasattr(manager, 'llm'):
            response = manager.llm.generate(
                prompt=f"Context: {context}\n\nQuestion: {query}\n\nAnswer concisely:",
                max_tokens=200
            )
            return {"response": response}
        
        return {"error": "Quick response not available"}
    
    async def _handle_rag_search(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for rag_search"""
        rag = self._get_rag()
        if not rag:
            return {"error": "RAG pipeline not available", "results": []}
        
        query = params["query"]
        top_k = params.get("top_k", 5)
        
        results = rag.search(query, top_k=top_k)
        
        return {
            "query": query,
            "results": results
        }
    
    async def _handle_rag_explain(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for rag_explain"""
        rag = self._get_rag()
        if not rag:
            return {"error": "RAG pipeline not available"}
        
        query = params["query"]
        response = rag.generate(query)
        
        return {
            "query": query,
            "explanation": response.get("answer", ""),
            "sources": response.get("sources", [])
        }
    
    async def _handle_system_time(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for system_time"""
        now = datetime.now()
        return {
            "iso": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": now.timestamp()
        }
    
    async def _handle_system_health(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for system_health"""
        health = {
            "status": "healthy",
            "components": {
                "database": False,
                "pipeline": False,
                "manager_agent": False,
                "rag_pipeline": False
            }
        }
        
        # Check database
        db = self._get_db()
        if db:
            try:
                health["components"]["database"] = db.test_connection()
            except:
                pass
        
        # Check pipeline
        health["components"]["pipeline"] = self._get_pipeline() is not None
        health["components"]["manager_agent"] = self._get_manager() is not None
        health["components"]["rag_pipeline"] = self._get_rag() is not None
        
        # Overall status
        all_healthy = all(health["components"].values())
        health["status"] = "healthy" if all_healthy else "degraded"
        
        return health
    
    # ==================== SCREEN CONTROL HANDLERS ====================
    
    def _get_pyautogui(self):
        """Lazy load pyautogui with fail-safe enabled"""
        try:
            import pyautogui
            pyautogui.FAILSAFE = True  # Move mouse to corner to abort
            pyautogui.PAUSE = 0.1  # Small pause between actions for safety
            return pyautogui
        except ImportError:
            logger.error("pyautogui not installed. Install with: pip install pyautogui")
            return None
    
    async def _handle_screen_move_mouse(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for screen_move_mouse"""
        pyautogui = self._get_pyautogui()
        if not pyautogui:
            return {"error": "pyautogui not available", "success": False}
        
        x = params["x"]
        y = params["y"]
        duration = params.get("duration", 0.3)
        
        try:
            pyautogui.moveTo(x, y, duration=duration)
            return {
                "success": True,
                "position": {"x": x, "y": y},
                "action": "move_mouse"
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _handle_screen_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for screen_click"""
        pyautogui = self._get_pyautogui()
        if not pyautogui:
            return {"error": "pyautogui not available", "success": False}
        
        x = params.get("x")
        y = params.get("y")
        button = params.get("button", "left")
        clicks = params.get("clicks", 1)
        
        try:
            if x is not None and y is not None:
                pyautogui.click(x, y, clicks=clicks, button=button)
                pos = {"x": x, "y": y}
            else:
                pyautogui.click(clicks=clicks, button=button)
                pos = pyautogui.position()
                pos = {"x": pos[0], "y": pos[1]}
            
            return {
                "success": True,
                "position": pos,
                "button": button,
                "clicks": clicks,
                "action": "click"
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _handle_screen_type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for screen_type"""
        pyautogui = self._get_pyautogui()
        if not pyautogui:
            return {"error": "pyautogui not available", "success": False}
        
        text = params["text"]
        interval = params.get("interval", 0.02)
        
        try:
            pyautogui.write(text, interval=interval)
            return {
                "success": True,
                "text_length": len(text),
                "action": "type"
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _handle_screen_hotkey(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for screen_hotkey"""
        pyautogui = self._get_pyautogui()
        if not pyautogui:
            return {"error": "pyautogui not available", "success": False}
        
        keys = params["keys"]
        
        try:
            pyautogui.hotkey(*keys)
            return {
                "success": True,
                "keys": keys,
                "action": "hotkey"
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _handle_screen_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for screen_screenshot"""
        pyautogui = self._get_pyautogui()
        if not pyautogui:
            return {"error": "pyautogui not available", "success": False}
        
        region = params.get("region")
        save_path = params.get("save_path")
        
        try:
            if region:
                screenshot = pyautogui.screenshot(region=(
                    region["x"], region["y"], 
                    region["width"], region["height"]
                ))
            else:
                screenshot = pyautogui.screenshot()
            
            if save_path:
                screenshot.save(save_path)
                return {
                    "success": True,
                    "saved_to": save_path,
                    "size": {"width": screenshot.width, "height": screenshot.height},
                    "action": "screenshot"
                }
            else:
                # Return screenshot info without saving
                return {
                    "success": True,
                    "size": {"width": screenshot.width, "height": screenshot.height},
                    "action": "screenshot",
                    "note": "Screenshot captured (not saved - provide save_path to save)"
                }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _handle_screen_size(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for screen_size"""
        pyautogui = self._get_pyautogui()
        if not pyautogui:
            return {"error": "pyautogui not available", "success": False}
        
        try:
            size = pyautogui.size()
            return {
                "success": True,
                "width": size[0],
                "height": size[1],
                "action": "get_size"
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _handle_screen_scroll(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for screen_scroll"""
        pyautogui = self._get_pyautogui()
        if not pyautogui:
            return {"error": "pyautogui not available", "success": False}
        
        clicks = params["clicks"]
        x = params.get("x")
        y = params.get("y")
        
        try:
            if x is not None and y is not None:
                pyautogui.scroll(clicks, x=x, y=y)
            else:
                pyautogui.scroll(clicks)
            
            return {
                "success": True,
                "scroll_amount": clicks,
                "direction": "up" if clicks > 0 else "down",
                "action": "scroll"
            }
        except Exception as e:
            return {"error": str(e), "success": False}
    
    async def _handle_screen_get_position(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handler for getting current mouse position"""
        pyautogui = self._get_pyautogui()
        if not pyautogui:
            return {"error": "pyautogui not available", "success": False}
        
        try:
            pos = pyautogui.position()
            return {
                "success": True,
                "x": pos[0],
                "y": pos[1],
                "action": "get_position"
            }
        except Exception as e:
            return {"error": str(e), "success": False}


# Singleton instance
_tool_registry: Optional[AgentToolRegistry] = None


def get_tool_registry() -> AgentToolRegistry:
    """Get the singleton tool registry"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = AgentToolRegistry()
    return _tool_registry
