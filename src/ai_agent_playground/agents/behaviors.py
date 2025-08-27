"""Agent behavior implementations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple
import random
import math

from ..core.agent import Agent, Position
from ..core.events import Event, EventType


class BaseBehavior(ABC):
    """Base class for agent behaviors."""
    
    @abstractmethod
    def execute(self, agent: Agent, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the behavior and return actions."""
        pass


class WanderBehavior(BaseBehavior):
    """Random wandering behavior."""
    
    def __init__(self, max_speed: float = 2.0, change_direction_prob: float = 0.1):
        self.max_speed = max_speed
        self.change_direction_prob = change_direction_prob
        self.direction = random.uniform(0, 2 * math.pi)
    
    def execute(self, agent: Agent, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Execute wandering behavior."""
        # Randomly change direction
        if random.random() < self.change_direction_prob:
            self.direction = random.uniform(0, 2 * math.pi)
        
        # Calculate movement
        speed = random.uniform(0.5, self.max_speed)
        dx = math.cos(self.direction) * speed
        dy = math.sin(self.direction) * speed
        
        return {
            "action": "move",
            "dx": dx,
            "dy": dy,
            "energy_cost": speed * 0.1
        }


class SeekBehavior(BaseBehavior):
    """Seek behavior towards a target."""
    
    def __init__(self, target_position: Position, max_speed: float = 3.0):
        self.target_position = target_position
        self.max_speed = max_speed
    
    def execute(self, agent: Agent, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Execute seeking behavior."""
        current_pos = agent.state.position
        
        # Calculate direction to target
        dx = self.target_position.x - current_pos.x
        dy = self.target_position.y - current_pos.y
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance < 1.0:  # Close enough
            return {"action": "idle"}
        
        # Normalize and scale by speed
        if distance > 0:
            dx = (dx / distance) * min(self.max_speed, distance)
            dy = (dy / distance) * min(self.max_speed, distance)
        
        return {
            "action": "move",
            "dx": dx,
            "dy": dy,
            "energy_cost": self.max_speed * 0.15
        }


class FlockBehavior(BaseBehavior):
    """Flocking behavior (separation, alignment, cohesion)."""
    
    def __init__(self, 
                 separation_radius: float = 20.0,
                 alignment_radius: float = 50.0,
                 cohesion_radius: float = 50.0,
                 max_speed: float = 2.5):
        self.separation_radius = separation_radius
        self.alignment_radius = alignment_radius
        self.cohesion_radius = cohesion_radius
        self.max_speed = max_speed
    
    def execute(self, agent: Agent, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Execute flocking behavior."""
        nearby_agents = observations.get("nearby_agents", [])
        
        if not nearby_agents:
            # No nearby agents, wander
            return WanderBehavior().execute(agent, observations)
        
        # Separation: steer away from nearby agents
        sep_x, sep_y = self._separation(agent, nearby_agents)
        
        # Alignment: steer towards average heading of neighbors
        align_x, align_y = self._alignment(agent, nearby_agents)
        
        # Cohesion: steer towards average position of neighbors
        coh_x, coh_y = self._cohesion(agent, nearby_agents)
        
        # Combine forces
        total_x = sep_x * 1.5 + align_x * 1.0 + coh_x * 1.0
        total_y = sep_y * 1.5 + align_y * 1.0 + coh_y * 1.0
        
        # Limit speed
        magnitude = (total_x * total_x + total_y * total_y) ** 0.5
        if magnitude > self.max_speed:
            total_x = (total_x / magnitude) * self.max_speed
            total_y = (total_y / magnitude) * self.max_speed
        
        return {
            "action": "move",
            "dx": total_x,
            "dy": total_y,
            "energy_cost": magnitude * 0.12
        }
    
    def _separation(self, agent: Agent, nearby_agents: List[Dict]) -> Tuple[float, float]:
        """Calculate separation force."""
        force_x, force_y = 0.0, 0.0
        count = 0
        
        for other in nearby_agents:
            distance = other["distance"]
            if distance < self.separation_radius and distance > 0:
                diff_x = agent.state.position.x - other["position"].x
                diff_y = agent.state.position.y - other["position"].y
                
                # Weight by distance (closer = stronger force)
                weight = 1.0 / distance
                force_x += diff_x * weight
                force_y += diff_y * weight
                count += 1
        
        if count > 0:
            force_x /= count
            force_y /= count
        
        return force_x, force_y
    
    def _alignment(self, agent: Agent, nearby_agents: List[Dict]) -> Tuple[float, float]:
        """Calculate alignment force."""
        avg_vel_x, avg_vel_y = 0.0, 0.0
        count = 0
        
        for other in nearby_agents:
            if other["distance"] < self.alignment_radius:
                # Note: We'd need velocity info from other agents for true alignment
                # For now, approximate based on position difference
                avg_vel_x += other["position"].x - agent.state.position.x
                avg_vel_y += other["position"].y - agent.state.position.y
                count += 1
        
        if count > 0:
            avg_vel_x /= count
            avg_vel_y /= count
            
            # Normalize
            magnitude = (avg_vel_x * avg_vel_x + avg_vel_y * avg_vel_y) ** 0.5
            if magnitude > 0:
                avg_vel_x /= magnitude
                avg_vel_y /= magnitude
        
        return avg_vel_x, avg_vel_y
    
    def _cohesion(self, agent: Agent, nearby_agents: List[Dict]) -> Tuple[float, float]:
        """Calculate cohesion force."""
        center_x, center_y = 0.0, 0.0
        count = 0
        
        for other in nearby_agents:
            if other["distance"] < self.cohesion_radius:
                center_x += other["position"].x
                center_y += other["position"].y
                count += 1
        
        if count > 0:
            center_x /= count
            center_y /= count
            
            # Steer towards center
            force_x = center_x - agent.state.position.x
            force_y = center_y - agent.state.position.y
            
            return force_x, force_y
        
        return 0.0, 0.0


class AutonomousBehavior(BaseBehavior):
    """Complex autonomous behavior with multiple sub-behaviors."""
    
    def __init__(self):
        self.behaviors = {
            "wander": WanderBehavior(max_speed=1.5),
            "flock": FlockBehavior(),
        }
        self.current_behavior = "wander"
        self.behavior_switch_timer = 0
        self.behavior_duration = 100  # Steps
    
    def execute(self, agent: Agent, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Execute autonomous behavior with behavior switching."""
        # Switch behaviors based on context
        nearby_count = len(observations.get("nearby_agents", []))
        
        if nearby_count > 2:
            self.current_behavior = "flock"
        else:
            self.current_behavior = "wander"
        
        # Execute current behavior
        behavior = self.behaviors[self.current_behavior]
        action = behavior.execute(agent, observations)
        
        # Add some autonomous decision making
        if agent.state.energy < 30:
            # Low energy, reduce activity
            if "dx" in action and "dy" in action:
                action["dx"] *= 0.5
                action["dy"] *= 0.5
                action["energy_cost"] *= 0.5
        
        return action


class ReactiveAgentBehavior(BaseBehavior):
    """Reactive behavior that responds to events and stimuli."""
    
    def __init__(self):
        self.alert_level = 0.0  # 0.0 to 1.0
        self.last_threat_time = 0
        self.flee_target = None
    
    def execute(self, agent: Agent, observations: Dict[str, Any]) -> Dict[str, Any]:
        """Execute reactive behavior."""
        nearby_agents = observations.get("nearby_agents", [])
        
        # Check for threats (agents that are too close)
        threat_detected = False
        closest_threat = None
        min_distance = float('inf')
        
        for other in nearby_agents:
            if other["distance"] < 15.0:  # Threat range
                threat_detected = True
                if other["distance"] < min_distance:
                    min_distance = other["distance"]
                    closest_threat = other
        
        if threat_detected and closest_threat:
            # Flee from threat
            self.alert_level = min(1.0, self.alert_level + 0.1)
            
            # Calculate flee direction (opposite to threat)
            flee_x = agent.state.position.x - closest_threat["position"].x
            flee_y = agent.state.position.y - closest_threat["position"].y
            
            # Normalize and scale
            distance = (flee_x * flee_x + flee_y * flee_y) ** 0.5
            if distance > 0:
                flee_x = (flee_x / distance) * 4.0  # Fast escape
                flee_y = (flee_y / distance) * 4.0
            
            return {
                "action": "flee",
                "dx": flee_x,
                "dy": flee_y,
                "energy_cost": 0.3  # High energy cost for fleeing
            }
        else:
            # No threats, calm down and wander
            self.alert_level = max(0.0, self.alert_level - 0.02)
            
            # Modify wander behavior based on alert level
            wander = WanderBehavior(max_speed=1.0 + self.alert_level)
            action = wander.execute(agent, observations)
            
            # Add alertness to energy cost
            if "energy_cost" in action:
                action["energy_cost"] += self.alert_level * 0.05
            
            return action