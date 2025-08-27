"""Base agent class and framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
import uuid
from datetime import datetime

from .events import Event, EventType


@dataclass
class Position:
    """2D position representation."""
    x: float
    y: float
    
    def distance_to(self, other: "Position") -> float:
        """Calculate Euclidean distance to another position."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


@dataclass
class AgentState:
    """Current state of an agent."""
    position: Position
    velocity: Tuple[float, float] = (0.0, 0.0)
    energy: float = 100.0
    health: float = 100.0
    age: int = 0
    active: bool = True
    last_action: Optional[str] = None
    custom_state: Dict[str, Any] = field(default_factory=dict)


class Agent(ABC):
    """Base agent class."""
    
    def __init__(
        self, 
        agent_id: Optional[str] = None,
        position: Optional[Position] = None,
        **kwargs
    ) -> None:
        self.agent_id = agent_id or str(uuid.uuid4())
        self.state = AgentState(
            position=position or Position(0.0, 0.0),
            **kwargs
        )
        self.memory: List[Dict[str, Any]] = []
        self.sensors: Dict[str, Any] = {}
        self.created_at = datetime.now()
    
    @abstractmethod
    def decide_action(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Decide what action to take based on observations."""
        pass
    
    @abstractmethod
    def update(self, dt: float, observations: Dict[str, Any]) -> None:
        """Update agent state."""
        pass
    
    def sense(self, environment: "World") -> Dict[str, Any]:
        """Sense the environment around the agent."""
        from ..environment.world import World
        
        observations = {
            "position": self.state.position,
            "energy": self.state.energy,
            "health": self.state.health,
            "age": self.state.age,
            "timestamp": datetime.now()
        }
        
        # Add nearby agents
        nearby_agents = environment.get_agents_in_radius(
            self.state.position, 
            radius=50.0
        )
        observations["nearby_agents"] = [
            {
                "id": agent.agent_id,
                "position": agent.state.position,
                "distance": self.state.position.distance_to(agent.state.position)
            }
            for agent in nearby_agents
            if agent.agent_id != self.agent_id
        ]
        
        return observations
    
    def move(self, dx: float, dy: float) -> None:
        """Move the agent by the given offset."""
        self.state.position.x += dx
        self.state.position.y += dy
        self.state.velocity = (dx, dy)
        self.state.last_action = "move"
    
    def consume_energy(self, amount: float) -> None:
        """Consume energy."""
        self.state.energy = max(0.0, self.state.energy - amount)
    
    def add_memory(self, memory_item: Dict[str, Any]) -> None:
        """Add an item to agent memory."""
        memory_item["timestamp"] = datetime.now()
        self.memory.append(memory_item)
        
        # Limit memory size
        max_memory = 1000
        if len(self.memory) > max_memory:
            self.memory = self.memory[-max_memory:]
    
    def handle_event(self, event: Event) -> None:
        """Handle incoming events."""
        if event.target_id == self.agent_id or event.target_id is None:
            self.add_memory({
                "type": "event",
                "event_type": event.event_type.value,
                "source": event.source_id,
                "data": event.data
            })
    
    def is_alive(self) -> bool:
        """Check if agent is alive."""
        return self.state.active and self.state.health > 0 and self.state.energy > 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            "agent_id": self.agent_id,
            "state": {
                "position": {"x": self.state.position.x, "y": self.state.position.y},
                "velocity": self.state.velocity,
                "energy": self.state.energy,
                "health": self.state.health,
                "age": self.state.age,
                "active": self.state.active,
                "last_action": self.state.last_action
            },
            "memory_size": len(self.memory),
            "created_at": self.created_at.isoformat()
        }