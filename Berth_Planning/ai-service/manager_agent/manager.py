"""
Manager Agent - Autonomous orchestrator using Qwen3-8B via Ollama
GPU-accelerated for fast task routing and planning
"""

import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .local_llm import OllamaLLM, get_local_llm

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Task types for routing"""
    BERTH_QUERY = "BERTH_QUERY"
    VESSEL_QUERY = "VESSEL_QUERY"
    OPTIMIZATION = "OPTIMIZATION"
    ANALYTICS = "ANALYTICS"
    GRAPH_QUERY = "GRAPH_QUERY"
    GENERAL = "GENERAL"


@dataclass
class Task:
    """Represents a task to be executed"""
    id: str
    query: str
    task_type: TaskType
    confidence: float
    entities: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[Any] = None


@dataclass
class ExecutionPlan:
    """Execution plan for complex tasks"""
    steps: List[Dict[str, str]]
    estimated_time: float = 0.0
    requires_rag: bool = False
    requires_graph: bool = False


class ManagerAgent:
    """
    Autonomous Manager Agent using Qwen3-8B (GPU via Ollama).
    
    Responsibilities:
    - Task classification and routing
    - Execution planning for complex queries
    - Coordination between RAG, Graph, and Central AI
    - Context management and memory
    """
    
    def __init__(
        self,
        model: str = "qwen3-8b-instruct:latest",
        enable_thinking: bool = False
    ):
        """
        Initialize Manager Agent
        
        Args:
            model: Ollama model to use (default: qwen3-8b-instruct for better JSON output)
            enable_thinking: Enable Qwen3's extended thinking mode
        """
        self.llm = get_local_llm(model=model, enable_thinking=enable_thinking)
        self.task_history: List[Task] = []
        self._context: Dict[str, Any] = {}
        
        logger.info(f"ManagerAgent initialized with model: {model}")
    
    def classify_query(self, query: str) -> Task:
        """
        Classify user query and create a Task object
        
        Args:
            query: User's input query
            
        Returns:
            Task object with classification results
        """
        result = self.llm.classify_task(query)
        
        task_type = TaskType.GENERAL
        try:
            task_type = TaskType(result.get("task_type", "GENERAL"))
        except ValueError:
            logger.warning(f"Unknown task type: {result.get('task_type')}")
        
        task = Task(
            id=f"task_{len(self.task_history) + 1}_{datetime.now().strftime('%H%M%S')}",
            query=query,
            task_type=task_type,
            confidence=result.get("confidence", 0.5),
            entities=result.get("entities", [])
        )
        
        self.task_history.append(task)
        logger.info(f"Classified query as {task_type.value} with confidence {task.confidence}")
        
        return task
    
    def create_plan(self, task: Task) -> ExecutionPlan:
        """
        Create execution plan for a task
        
        Args:
            task: Task to plan execution for
            
        Returns:
            ExecutionPlan with steps
        """
        steps = self.llm.plan_execution(task.query, str(task.context))
        
        plan = ExecutionPlan(
            steps=steps,
            requires_rag=any(s.get("action") == "QUERY_RAG" for s in steps),
            requires_graph=any(s.get("action") == "QUERY_GRAPH" for s in steps)
        )
        
        logger.info(f"Created plan with {len(steps)} steps (RAG: {plan.requires_rag}, Graph: {plan.requires_graph})")
        
        return plan
    
    def route_to_system(self, task: Task) -> str:
        """
        Determine which system should handle the task
        
        Returns:
            System name: 'rag', 'graph', 'central', 'direct'
        """
        # Graph queries need relationship traversal
        if task.task_type == TaskType.GRAPH_QUERY:
            return "graph"
        
        # Optimization and analytics may need central AI
        if task.task_type in [TaskType.OPTIMIZATION, TaskType.ANALYTICS]:
            return "central"
        
        # Simple queries can use RAG
        if task.task_type in [TaskType.BERTH_QUERY, TaskType.VESSEL_QUERY]:
            return "rag"
        
        # Default to RAG for grounded responses
        return "rag"
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract domain entities from text"""
        return self.llm.extract_entities(
            text,
            entity_types=["vessel", "port", "berth", "terminal", "date", "time"]
        )
    
    def summarize(self, documents: List[str]) -> str:
        """Summarize retrieved documents"""
        return self.llm.summarize_context(documents)
    
    def process_query(self, query: str) -> Dict[str, Any]:
        """
        Full pipeline: classify -> plan -> route
        
        Args:
            query: User's input query
            
        Returns:
            Dict with task, plan, and routing info
        """
        # Step 1: Classify
        task = self.classify_query(query)
        
        # Step 2: Plan (for complex tasks)
        plan = None
        if task.confidence < 0.8 or task.task_type in [TaskType.OPTIMIZATION, TaskType.ANALYTICS]:
            plan = self.create_plan(task)
        
        # Step 3: Route
        target_system = self.route_to_system(task)
        
        return {
            "task": {
                "id": task.id,
                "type": task.task_type.value,
                "confidence": task.confidence,
                "entities": task.entities
            },
            "plan": {
                "steps": plan.steps if plan else [],
                "requires_rag": plan.requires_rag if plan else False,
                "requires_graph": plan.requires_graph if plan else False
            } if plan else None,
            "route": target_system,
            "query": query
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get manager agent statistics"""
        return {
            "llm": self.llm.get_stats(),
            "tasks_processed": len(self.task_history),
            "task_types": {
                t.value: sum(1 for task in self.task_history if task.task_type == t)
                for t in TaskType
            }
        }
    
    def is_ready(self) -> bool:
        """Check if manager agent is ready"""
        return self.llm.is_loaded()


# Factory function
def get_manager_agent(**kwargs) -> ManagerAgent:
    """Get a ManagerAgent instance"""
    return ManagerAgent(**kwargs)
