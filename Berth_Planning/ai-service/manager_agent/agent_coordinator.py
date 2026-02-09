"""
Agent Coordinator - Coordinates between Manager Agent (Qwen3) and Central AI (Claude)
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Available agent types"""
    MANAGER = "manager"  # Qwen3 via Ollama (GPU, fast)
    CENTRAL = "central"  # Claude Opus 4 (powerful reasoning)
    RAG = "rag"          # RAG pipeline (retrieval)
    GRAPH = "graph"      # Neo4j (relationships)


@dataclass
class AgentMessage:
    """Message passed between agents"""
    sender: AgentType
    receiver: AgentType
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = ""


@dataclass
class AgentState:
    """State of an agent"""
    agent_type: AgentType
    is_ready: bool = False
    last_used: Optional[datetime] = None
    request_count: int = 0
    error_count: int = 0


class AgentCoordinator:
    """
    Coordinates communication and task delegation between agents.
    
    Architecture:
    - Manager Agent (Qwen3/Ollama): Fast routing, planning, simple responses
    - Central AI (Claude): Complex reasoning, multi-step tasks
    - RAG System: Document retrieval, factual queries
    - Graph System: Relationship queries, path finding
    """
    
    def __init__(self):
        self._agents: Dict[AgentType, Any] = {}
        self._states: Dict[AgentType, AgentState] = {}
        self._message_history: List[AgentMessage] = []
        self._callbacks: Dict[str, Callable] = {}
        
        # Initialize states
        for agent_type in AgentType:
            self._states[agent_type] = AgentState(agent_type=agent_type)
    
    def register_agent(self, agent_type: AgentType, agent: Any):
        """Register an agent with the coordinator"""
        self._agents[agent_type] = agent
        self._states[agent_type].is_ready = True
        logger.info(f"Registered {agent_type.value} agent")
    
    def is_agent_ready(self, agent_type: AgentType) -> bool:
        """Check if an agent is ready"""
        return self._states[agent_type].is_ready
    
    def get_agent(self, agent_type: AgentType) -> Optional[Any]:
        """Get an agent by type"""
        return self._agents.get(agent_type)
    
    def delegate(
        self,
        from_agent: AgentType,
        to_agent: AgentType,
        query: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Delegate a task from one agent to another
        
        Args:
            from_agent: Source agent
            to_agent: Target agent
            query: Query/task to delegate
            context: Additional context
            
        Returns:
            Response from target agent
        """
        if not self.is_agent_ready(to_agent):
            return {
                "error": f"Agent {to_agent.value} is not ready",
                "success": False
            }
        
        # Create message
        message = AgentMessage(
            sender=from_agent,
            receiver=to_agent,
            content=query,
            context=context or {},
            message_id=f"msg_{len(self._message_history)}_{datetime.now().strftime('%H%M%S')}"
        )
        self._message_history.append(message)
        
        # Update stats
        self._states[to_agent].request_count += 1
        self._states[to_agent].last_used = datetime.now()
        
        # Get agent and execute
        agent = self._agents[to_agent]
        
        try:
            # Different agents have different interfaces
            if to_agent == AgentType.MANAGER:
                result = agent.process_query(query)
            elif to_agent == AgentType.CENTRAL:
                # Central AI (Claude) - expects chat interface
                if hasattr(agent, 'chat'):
                    result = agent.chat(query, context or {})
                elif hasattr(agent, 'query'):
                    result = agent.query(query)
                else:
                    result = {"response": "Central AI interface not configured"}
            elif to_agent == AgentType.RAG:
                # RAG system
                if hasattr(agent, 'query'):
                    result = agent.query(query)
                else:
                    result = {"response": "RAG interface not configured"}
            elif to_agent == AgentType.GRAPH:
                # Graph system
                if hasattr(agent, 'query'):
                    result = agent.query(query)
                else:
                    result = {"response": "Graph interface not configured"}
            else:
                result = {"error": f"Unknown agent type: {to_agent}"}
            
            return {
                "success": True,
                "result": result,
                "agent": to_agent.value,
                "message_id": message.message_id
            }
            
        except Exception as e:
            self._states[to_agent].error_count += 1
            logger.error(f"Error delegating to {to_agent.value}: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": to_agent.value
            }
    
    def broadcast(
        self,
        query: str,
        agents: List[AgentType] = None,
        context: Dict[str, Any] = None
    ) -> Dict[AgentType, Dict[str, Any]]:
        """
        Send query to multiple agents and collect responses
        
        Args:
            query: Query to broadcast
            agents: List of agents to query (default: all ready agents)
            context: Additional context
            
        Returns:
            Dict mapping agent types to their responses
        """
        if agents is None:
            agents = [at for at in AgentType if self.is_agent_ready(at)]
        
        results = {}
        for agent_type in agents:
            results[agent_type] = self.delegate(
                from_agent=AgentType.MANAGER,
                to_agent=agent_type,
                query=query,
                context=context
            )
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get coordinator statistics"""
        return {
            "agents": {
                at.value: {
                    "ready": self._states[at].is_ready,
                    "requests": self._states[at].request_count,
                    "errors": self._states[at].error_count,
                    "last_used": self._states[at].last_used.isoformat() if self._states[at].last_used else None
                }
                for at in AgentType
            },
            "total_messages": len(self._message_history)
        }
    
    def get_message_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent message history"""
        messages = self._message_history[-limit:]
        return [
            {
                "id": m.message_id,
                "sender": m.sender.value,
                "receiver": m.receiver.value,
                "content": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]


# Factory function
def get_coordinator() -> AgentCoordinator:
    """Get an AgentCoordinator instance"""
    return AgentCoordinator()
