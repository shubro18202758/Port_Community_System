"""
Action Schema for Browser Agent
Defines structured actions the LLM can output
"""

from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json


class ActionType(str, Enum):
    """Types of browser actions the agent can perform"""
    # Navigation
    NAVIGATE = "navigate"
    BACK = "back"
    FORWARD = "forward"
    REFRESH = "refresh"
    
    # Interaction
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    HOVER = "hover"
    
    # Input
    TYPE = "type"
    CLEAR = "clear"
    SELECT = "select"
    
    # Scrolling
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"
    SCROLL_TO = "scroll_to"
    
    # Reading/Observing
    READ_PAGE = "read_page"
    EXTRACT_DATA = "extract_data"
    SCREENSHOT = "screenshot"
    WAIT = "wait"
    
    # Control
    COMPLETE = "complete"  # Task finished
    FAIL = "fail"          # Cannot complete
    ASK_USER = "ask_user"  # Need clarification


@dataclass
class BrowserAction:
    """
    Structured browser action from LLM.
    This is what the LLM outputs when deciding what to do.
    """
    action_type: ActionType
    target: Optional[str] = None  # CSS selector, element description, or URL
    value: Optional[str] = None   # Text to type, option to select
    reasoning: str = ""           # Why the agent chose this action
    confidence: float = 0.0       # How confident the agent is (0-1)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "target": self.target,
            "value": self.value,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrowserAction':
        return cls(
            action_type=ActionType(data["action_type"]),
            target=data.get("target"),
            value=data.get("value"),
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence", 0.0),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_llm_response(cls, response: str) -> 'BrowserAction':
        """Parse LLM response to extract action"""
        try:
            # Try to extract JSON from response
            json_match = response
            if "```json" in response:
                json_match = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_match = response.split("```")[1].split("```")[0]
            
            data = json.loads(json_match.strip())
            return cls.from_dict(data)
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            # Fallback: try to parse natural language
            return cls._parse_natural_language(response)
    
    @classmethod
    def _parse_natural_language(cls, response: str) -> 'BrowserAction':
        """Fallback parser for natural language responses"""
        response_lower = response.lower()
        
        # Check for completion signals
        if any(word in response_lower for word in ["complete", "done", "finished", "task complete"]):
            return cls(
                action_type=ActionType.COMPLETE,
                reasoning=response,
                confidence=0.8
            )
        
        # Check for click actions
        if "click" in response_lower:
            return cls(
                action_type=ActionType.CLICK,
                reasoning=response,
                confidence=0.6
            )
        
        # Default to read page if unsure
        return cls(
            action_type=ActionType.READ_PAGE,
            reasoning=f"Could not parse action, defaulting to read: {response}",
            confidence=0.3
        )


class AgentState(str, Enum):
    """Current state of the agent"""
    IDLE = "idle"
    THINKING = "thinking"
    ACTING = "acting"
    OBSERVING = "observing"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


@dataclass
class ActionResult:
    """Result of executing a browser action"""
    success: bool
    action: BrowserAction
    screenshot_path: Optional[str] = None
    screenshot_base64: Optional[str] = None
    dom_snapshot: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: int = 0
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action.to_dict(),
            "screenshot_base64": self.screenshot_base64,
            "dom_snapshot": self.dom_snapshot[:500] if self.dom_snapshot else None,  # Truncate for serialization
            "extracted_data": self.extracted_data,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class AgentStep:
    """A single step in the agent's execution"""
    step_number: int
    state: AgentState
    action: Optional[BrowserAction] = None
    result: Optional[ActionResult] = None
    observation: Optional[str] = None
    thinking: Optional[str] = None  # Agent's reasoning visible to user
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "state": self.state.value,
            "action": self.action.to_dict() if self.action else None,
            "result": self.result.to_dict() if self.result else None,
            "observation": self.observation[:1000] if self.observation else None,  # Truncate
            "thinking": self.thinking,
            "timestamp": self.timestamp.isoformat()
        }


# Action templates for common SmartBerth operations
SMARTBERTH_ACTION_TEMPLATES = {
    "check_vessel_status": [
        BrowserAction(ActionType.CLICK, target='[data-testid="vessel-list"]', reasoning="Open vessel list"),
        BrowserAction(ActionType.READ_PAGE, reasoning="Read vessel information"),
    ],
    "view_berth_schedule": [
        BrowserAction(ActionType.CLICK, target='[data-testid="schedule-tab"]', reasoning="Open schedule view"),
        BrowserAction(ActionType.READ_PAGE, reasoning="Read berth schedule"),
    ],
    "check_notifications": [
        BrowserAction(ActionType.CLICK, target='[data-testid="notifications-btn"]', reasoning="Open notifications"),
        BrowserAction(ActionType.READ_PAGE, reasoning="Read notifications and alerts"),
    ],
    "analyze_dashboard": [
        BrowserAction(ActionType.READ_PAGE, reasoning="Analyze dashboard KPIs"),
        BrowserAction(ActionType.EXTRACT_DATA, target=".kpi-card", reasoning="Extract KPI values"),
    ],
}
