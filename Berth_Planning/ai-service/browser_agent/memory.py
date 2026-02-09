"""
Memory System for Browser Agent
Tracks agent steps, context, and conversation history
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from collections import deque
import hashlib

from .action_schema import AgentStep, BrowserAction, ActionResult, AgentState

logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    """Context for the current task"""
    task_id: str
    task_description: str
    started_at: datetime
    target_url: Optional[str] = None
    completed_at: Optional[datetime] = None
    status: str = "in_progress"  # in_progress, completed, failed, paused
    final_result: Optional[Dict[str, Any]] = None


@dataclass
class PageSnapshot:
    """Snapshot of a page state"""
    url: str
    title: str
    timestamp: datetime
    dom_summary: str
    screenshot_path: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "url": self.url,
            "title": self.title,
            "timestamp": self.timestamp.isoformat(),
            "dom_summary": self.dom_summary[:500],  # Truncate
            "screenshot_path": self.screenshot_path
        }


class AgentMemory:
    """
    Memory system for the browser agent.
    Maintains:
    - Current task context
    - Step history
    - Page snapshots
    - Conversation history
    - Error history
    """
    
    def __init__(
        self,
        max_steps: int = 100,
        max_snapshots: int = 20,
        max_errors: int = 10
    ):
        """
        Initialize agent memory.
        
        Args:
            max_steps: Maximum steps to keep in memory
            max_snapshots: Maximum page snapshots to keep
            max_errors: Maximum error records to keep
        """
        self.max_steps = max_steps
        self.max_snapshots = max_snapshots
        self.max_errors = max_errors
        
        # Current task
        self._current_task: Optional[TaskContext] = None
        
        # Step history (ring buffer)
        self._steps: deque[AgentStep] = deque(maxlen=max_steps)
        
        # Page snapshots
        self._snapshots: deque[PageSnapshot] = deque(maxlen=max_snapshots)
        
        # Error history
        self._errors: deque[Dict[str, Any]] = deque(maxlen=max_errors)
        
        # Conversation history for multi-turn interactions
        self._conversation: List[Dict[str, str]] = []
        
        # Action success tracking
        self._action_stats: Dict[str, Dict[str, int]] = {}
        
        # Visited URLs
        self._visited_urls: set = set()
        
        # Current step number
        self._step_counter = 0
    
    # ==================== TASK MANAGEMENT ====================
    
    def start_task(
        self, 
        task_description: str,
        target_url: Optional[str] = None
    ) -> str:
        """
        Start a new task.
        
        Args:
            task_description: Description of the task
            target_url: Optional starting URL
            
        Returns:
            Task ID
        """
        # Generate task ID
        task_id = hashlib.md5(
            f"{task_description}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        self._current_task = TaskContext(
            task_id=task_id,
            task_description=task_description,
            started_at=datetime.now(),
            target_url=target_url
        )
        
        # Reset step counter
        self._step_counter = 0
        
        # Clear previous task data
        self._steps.clear()
        self._snapshots.clear()
        self._errors.clear()
        self._visited_urls.clear()
        
        logger.info(f"Started task {task_id}: {task_description}")
        return task_id
    
    def complete_task(self, result: Optional[Dict[str, Any]] = None):
        """Mark current task as completed"""
        if self._current_task:
            self._current_task.completed_at = datetime.now()
            self._current_task.status = "completed"
            self._current_task.final_result = result
            logger.info(f"Task {self._current_task.task_id} completed")
    
    def fail_task(self, reason: str):
        """Mark current task as failed"""
        if self._current_task:
            self._current_task.completed_at = datetime.now()
            self._current_task.status = "failed"
            self._current_task.final_result = {"error": reason}
            logger.warning(f"Task {self._current_task.task_id} failed: {reason}")
    
    @property
    def current_task(self) -> Optional[TaskContext]:
        """Get current task context"""
        return self._current_task
    
    # ==================== STEP TRACKING ====================
    
    def add_step(self, step: AgentStep):
        """Add a step to history"""
        self._steps.append(step)
        self._step_counter += 1
        
        # Update action stats
        if step.action:
            action_type = step.action.action_type.value
            if action_type not in self._action_stats:
                self._action_stats[action_type] = {"success": 0, "failure": 0}
            
            if step.result and step.result.success:
                self._action_stats[action_type]["success"] += 1
            else:
                self._action_stats[action_type]["failure"] += 1
    
    def create_step(
        self,
        state: AgentState,
        action: Optional[BrowserAction] = None,
        result: Optional[ActionResult] = None,
        observation: Optional[str] = None,
        thinking: Optional[str] = None
    ) -> AgentStep:
        """Create and add a new step"""
        step = AgentStep(
            step_number=self._step_counter + 1,
            state=state,
            action=action,
            result=result,
            observation=observation,
            thinking=thinking,
            timestamp=datetime.now()
        )
        self.add_step(step)
        return step
    
    def get_recent_steps(self, count: int = 10) -> List[AgentStep]:
        """Get most recent steps"""
        return list(self._steps)[-count:]
    
    def get_all_steps(self) -> List[AgentStep]:
        """Get all steps"""
        return list(self._steps)
    
    @property
    def step_count(self) -> int:
        """Get total step count"""
        return self._step_counter
    
    def get_next_step_number(self) -> int:
        """Get next step number"""
        return self._step_counter + 1
    
    # ==================== PAGE SNAPSHOTS ====================
    
    def add_snapshot(
        self,
        url: str,
        title: str,
        dom_summary: str,
        screenshot_path: Optional[str] = None
    ):
        """Add a page snapshot"""
        snapshot = PageSnapshot(
            url=url,
            title=title,
            timestamp=datetime.now(),
            dom_summary=dom_summary,
            screenshot_path=screenshot_path
        )
        self._snapshots.append(snapshot)
        self._visited_urls.add(url)
    
    def get_latest_snapshot(self) -> Optional[PageSnapshot]:
        """Get most recent page snapshot"""
        return self._snapshots[-1] if self._snapshots else None
    
    def get_all_snapshots(self) -> List[PageSnapshot]:
        """Get all page snapshots"""
        return list(self._snapshots)
    
    def has_visited(self, url: str) -> bool:
        """Check if URL was already visited"""
        return url in self._visited_urls
    
    # ==================== ERROR TRACKING ====================
    
    def add_error(self, error: str, action: Optional[BrowserAction] = None):
        """Add an error record"""
        self._errors.append({
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "action": action.to_dict() if action else None,
            "step_number": self._step_counter
        })
    
    def get_recent_errors(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get most recent errors"""
        return list(self._errors)[-count:]
    
    def has_repeated_errors(self, threshold: int = 3) -> bool:
        """Check if there are repeated consecutive errors"""
        if len(self._errors) < threshold:
            return False
        
        recent_errors = list(self._errors)[-threshold:]
        error_messages = [e["error"] for e in recent_errors]
        return len(set(error_messages)) == 1  # All same error
    
    # ==================== CONVERSATION ====================
    
    def add_user_message(self, message: str):
        """Add user message to conversation"""
        self._conversation.append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def add_assistant_message(self, message: str):
        """Add assistant message to conversation"""
        self._conversation.append({
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
    
    def get_conversation(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        return self._conversation
    
    def clear_conversation(self):
        """Clear conversation history"""
        self._conversation.clear()
    
    # ==================== CONTEXT GENERATION ====================
    
    def build_llm_context(self, include_steps: int = 5) -> str:
        """
        Build context string for LLM.
        
        Args:
            include_steps: Number of recent steps to include
            
        Returns:
            Formatted context string
        """
        lines = []
        
        # Task info
        if self._current_task:
            lines.append(f"## Current Task")
            lines.append(f"Task: {self._current_task.task_description}")
            if self._current_task.target_url:
                lines.append(f"Target URL: {self._current_task.target_url}")
            lines.append(f"Steps taken: {self._step_counter}")
            lines.append("")
        
        # Recent steps
        recent_steps = self.get_recent_steps(include_steps)
        if recent_steps:
            lines.append("## Recent Actions")
            for step in recent_steps:
                step_desc = f"Step {step.step_number}: {step.state.value}"
                if step.action:
                    step_desc += f" - {step.action.action_type.value}"
                    if step.action.target:
                        step_desc += f" on '{step.action.target}'"
                if step.result:
                    step_desc += f" -> {'Success' if step.result.success else 'Failed'}"
                lines.append(step_desc)
            lines.append("")
        
        # Latest page state
        latest_snapshot = self.get_latest_snapshot()
        if latest_snapshot:
            lines.append("## Current Page")
            lines.append(f"URL: {latest_snapshot.url}")
            lines.append(f"Title: {latest_snapshot.title}")
            lines.append("")
            lines.append("Page Content:")
            lines.append(latest_snapshot.dom_summary[:2000])
            lines.append("")
        
        # Recent errors
        recent_errors = self.get_recent_errors(3)
        if recent_errors:
            lines.append("## Recent Errors")
            for err in recent_errors:
                lines.append(f"- {err['error']}")
            lines.append("")
        
        # Visited URLs
        if self._visited_urls:
            lines.append(f"## Visited URLs ({len(self._visited_urls)} pages)")
            for url in list(self._visited_urls)[:5]:
                lines.append(f"- {url}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def get_action_history_summary(self) -> str:
        """Get a summary of action history"""
        lines = ["Action History Summary:"]
        for action_type, stats in self._action_stats.items():
            total = stats["success"] + stats["failure"]
            success_rate = stats["success"] / total * 100 if total > 0 else 0
            lines.append(f"- {action_type}: {total} attempts ({success_rate:.0f}% success)")
        return '\n'.join(lines)
    
    # ==================== STATE EXPORT ====================
    
    def export_state(self) -> Dict[str, Any]:
        """Export full memory state"""
        return {
            "task": {
                "id": self._current_task.task_id if self._current_task else None,
                "description": self._current_task.task_description if self._current_task else None,
                "status": self._current_task.status if self._current_task else None,
                "started_at": self._current_task.started_at.isoformat() if self._current_task else None
            },
            "steps": [step.to_dict() for step in self._steps],
            "snapshots": [snap.to_dict() for snap in self._snapshots],
            "errors": list(self._errors),
            "action_stats": self._action_stats,
            "visited_urls": list(self._visited_urls),
            "step_count": self._step_counter
        }
    
    def get_task_summary(self) -> Dict[str, Any]:
        """Get a summary of the current task execution"""
        successful_actions = sum(
            stats["success"] for stats in self._action_stats.values()
        )
        failed_actions = sum(
            stats["failure"] for stats in self._action_stats.values()
        )
        
        return {
            "task_id": self._current_task.task_id if self._current_task else None,
            "task_description": self._current_task.task_description if self._current_task else None,
            "status": self._current_task.status if self._current_task else None,
            "total_steps": self._step_counter,
            "successful_actions": successful_actions,
            "failed_actions": failed_actions,
            "pages_visited": len(self._visited_urls),
            "urls_visited": list(self._visited_urls),  # Include actual URLs for summary
            "errors_encountered": len(self._errors)
        }
    
    def get_visited_urls(self) -> set:
        """Get the set of visited URLs"""
        return self._visited_urls.copy()
