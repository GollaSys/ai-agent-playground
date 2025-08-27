"""Specific agent types with different behaviors."""

from typing import Dict, Any, Optional
import random

from ..core.agent import Agent, Position
from .behaviors import AutonomousBehavior, ReactiveAgentBehavior, WanderBehavior


class AgentType:
    """Factory for creating different types of agents."""
    
    @staticmethod
    def create_autonomous_agent(
        agent_id: Optional[str] = None,
        position: Optional[Position] = None
    ) -> "AutonomousAgent":
        """Create an autonomous agent."""
        return AutonomousAgent(agent_id=agent_id, position=position)
    
    @staticmethod
    def create_reactive_agent(
        agent_id: Optional[str] = None,
        position: Optional[Position] = None
    ) -> "ReactiveAgent":
        """Create a reactive agent."""
        return ReactiveAgent(agent_id=agent_id, position=position)
    
    @staticmethod
    def create_wanderer_agent(
        agent_id: Optional[str] = None,
        position: Optional[Position] = None
    ) -> "WandererAgent":
        """Create a simple wandering agent."""
        return WandererAgent(agent_id=agent_id, position=position)


class AutonomousAgent(Agent):
    """An autonomous agent with complex decision-making capabilities."""
    
    def __init__(self, agent_id: Optional[str] = None, position: Optional[Position] = None):
        super().__init__(agent_id=agent_id, position=position)
        self.behavior = AutonomousBehavior()
        
        # Enhanced attributes for autonomous agents
        self.state.energy = 120.0
        self.state.health = 100.0
        self.intelligence = random.uniform(0.7, 1.0)
        self.adaptability = random.uniform(0.5, 1.0)
        
        # Goals and objectives
        self.goals = []
        self.current_goal = None
        self.goal_completion_count = 0
    
    def decide_action(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Autonomous decision making with goal-oriented behavior."""
        # Evaluate current situation
        energy_ratio = self.state.energy / 120.0
        nearby_agents = len(observations.get("nearby_agents", []))
        
        # Autonomous goal setting
        if not self.current_goal or random.random() < 0.02:  # 2% chance to set new goal
            self._set_new_goal(observations)
        
        # Execute behavior based on current goal and state
        base_action = self.behavior.execute(self, observations)
        
        # Modify action based on intelligence and adaptability
        if "energy_cost" in base_action:
            # Intelligent agents use less energy
            base_action["energy_cost"] *= (1.0 - self.intelligence * 0.3)
        
        # Add exploration tendency for high adaptability agents
        if self.adaptability > 0.8 and random.random() < 0.1:
            if "dx" in base_action and "dy" in base_action:
                exploration_factor = 1.2
                base_action["dx"] *= exploration_factor
                base_action["dy"] *= exploration_factor
        
        return base_action
    
    def update(self, dt: float, observations: Dict[str, Any]) -> None:
        """Update autonomous agent state."""
        action = self.decide_action(observations)
        
        if action.get("action") == "move":
            self.move(action.get("dx", 0), action.get("dy", 0))
        
        # Consume energy based on action
        energy_cost = action.get("energy_cost", 0.1)
        self.consume_energy(energy_cost)
        
        # Learn from experience (simplified)
        if random.random() < 0.05:  # 5% chance to learn
            self.intelligence = min(1.0, self.intelligence + 0.001)
            self.adaptability = min(1.0, self.adaptability + 0.001)
        
        # Check goal completion
        self._check_goal_completion(observations)
    
    def _set_new_goal(self, observations: Dict[str, Any]) -> None:
        """Set a new goal for the agent."""
        possible_goals = ["explore", "socialize", "conserve_energy", "patrol"]
        
        # Goal selection based on current state
        if self.state.energy < 50:
            self.current_goal = "conserve_energy"
        elif len(observations.get("nearby_agents", [])) > 3:
            self.current_goal = "socialize"
        else:
            self.current_goal = random.choice(possible_goals)
        
        self.add_memory({
            "type": "goal_set",
            "goal": self.current_goal,
            "energy": self.state.energy
        })
    
    def _check_goal_completion(self, observations: Dict[str, Any]) -> None:
        """Check if current goal is completed."""
        if not self.current_goal:
            return
        
        completed = False
        
        if self.current_goal == "conserve_energy" and self.state.energy > 80:
            completed = True
        elif self.current_goal == "socialize" and len(observations.get("nearby_agents", [])) > 5:
            completed = True
        elif self.current_goal in ["explore", "patrol"] and random.random() < 0.01:
            completed = True  # Simplified completion check
        
        if completed:
            self.goal_completion_count += 1
            self.add_memory({
                "type": "goal_completed",
                "goal": self.current_goal,
                "completion_count": self.goal_completion_count
            })
            self.current_goal = None


class ReactiveAgent(Agent):
    """A reactive agent that responds to immediate stimuli."""
    
    def __init__(self, agent_id: Optional[str] = None, position: Optional[Position] = None):
        super().__init__(agent_id=agent_id, position=position)
        self.behavior = ReactiveAgentBehavior()
        
        # Reactive agent attributes
        self.state.energy = 80.0
        self.reaction_speed = random.uniform(0.6, 1.0)
        self.sensitivity = random.uniform(0.4, 0.9)
        
        # Reactive state
        self.last_reaction_time = 0
        self.reaction_cooldown = 10  # Steps
    
    def decide_action(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Reactive decision making based on immediate stimuli."""
        # Quick reaction to immediate threats or opportunities
        nearby_agents = observations.get("nearby_agents", [])
        
        # High sensitivity agents detect threats from further away
        threat_range = 15.0 + (self.sensitivity * 10.0)
        
        for agent_info in nearby_agents:
            if agent_info["distance"] < threat_range:
                # React quickly
                action = self.behavior.execute(self, observations)
                
                # Speed up reaction based on reaction_speed
                if "dx" in action and "dy" in action:
                    speed_multiplier = 1.0 + self.reaction_speed
                    action["dx"] *= speed_multiplier
                    action["dy"] *= speed_multiplier
                
                return action
        
        # No immediate threats, use normal behavior
        return self.behavior.execute(self, observations)
    
    def update(self, dt: float, observations: Dict[str, Any]) -> None:
        """Update reactive agent state."""
        action = self.decide_action(observations)
        
        if action.get("action") in ["move", "flee"]:
            self.move(action.get("dx", 0), action.get("dy", 0))
            
            if action.get("action") == "flee":
                self.last_reaction_time = self.state.age
        
        # Consume energy
        energy_cost = action.get("energy_cost", 0.1)
        self.consume_energy(energy_cost)
        
        # Reactive agents recover energy faster when not reacting
        if self.state.age - self.last_reaction_time > self.reaction_cooldown:
            self.state.energy = min(80.0, self.state.energy + 0.2)


class WandererAgent(Agent):
    """A simple agent that just wanders around."""
    
    def __init__(self, agent_id: Optional[str] = None, position: Optional[Position] = None):
        super().__init__(agent_id=agent_id, position=position)
        self.behavior = WanderBehavior(max_speed=1.5)
        
        # Simple wanderer attributes
        self.state.energy = 100.0
        self.curiosity = random.uniform(0.3, 0.8)
    
    def decide_action(self, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Simple wandering decision making."""
        action = self.behavior.execute(self, observations)
        
        # Curious agents move more
        if self.curiosity > 0.6 and "dx" in action and "dy" in action:
            curiosity_factor = 1.0 + (self.curiosity - 0.6)
            action["dx"] *= curiosity_factor
            action["dy"] *= curiosity_factor
        
        return action
    
    def update(self, dt: float, observations: Dict[str, Any]) -> None:
        """Update wanderer agent state."""
        action = self.decide_action(observations)
        
        if action.get("action") == "move":
            self.move(action.get("dx", 0), action.get("dy", 0))
        
        # Consume energy
        energy_cost = action.get("energy_cost", 0.1)
        self.consume_energy(energy_cost)
        
        # Wanderers slowly regain energy
        if random.random() < 0.1:  # 10% chance per step
            self.state.energy = min(100.0, self.state.energy + 0.5)