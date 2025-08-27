"""World simulation environment."""

from typing import Dict, List, Optional, Any, Tuple
import random
from datetime import datetime

from ..core.agent import Agent, Position
from ..core.events import Event, EventType
from .spatial import SpatialGrid
from .physics import PhysicsEngine


class EnvironmentFeature:
    """Represents environmental features like obstacles, resources, etc."""
    
    def __init__(self, position: Position, feature_type: str, radius: float = 5.0, **properties):
        self.position = position
        self.feature_type = feature_type
        self.radius = radius
        self.properties = properties
        self.active = True


class World:
    """The simulation world containing agents and environmental features."""
    
    def __init__(self, width: float = 1000.0, height: float = 1000.0, cell_size: float = 50.0):
        self.width = width
        self.height = height
        
        # Spatial partitioning for efficient queries
        self.spatial_grid = SpatialGrid(width, height, cell_size)
        
        # Physics simulation
        self.physics = PhysicsEngine(width, height)
        
        # Agent management
        self.agents: Dict[str, Agent] = {}
        
        # Environmental features
        self.features: List[EnvironmentFeature] = []
        
        # World state
        self.time = 0.0
        self.temperature = 20.0  # Celsius
        self.humidity = 0.5     # 0.0 to 1.0
        self.wind_speed = 0.0
        self.wind_direction = 0.0  # Radians
        
        # Statistics
        self.total_agents_created = 0
        self.total_agents_removed = 0
        
        self._initialize_environment()
    
    def _initialize_environment(self) -> None:
        """Initialize the environment with default features."""
        # Add some random obstacles
        num_obstacles = int((self.width * self.height) / 50000)  # Density-based
        
        for _ in range(num_obstacles):
            x = random.uniform(50, self.width - 50)
            y = random.uniform(50, self.height - 50)
            radius = random.uniform(10, 30)
            
            obstacle = EnvironmentFeature(
                Position(x, y),
                "obstacle",
                radius,
                hardness=random.uniform(0.5, 1.0)
            )
            self.features.append(obstacle)
        
        # Add some resource patches
        num_resources = int(num_obstacles / 2)
        for _ in range(num_resources):
            x = random.uniform(20, self.width - 20)
            y = random.uniform(20, self.height - 20)
            radius = random.uniform(15, 40)
            
            resource = EnvironmentFeature(
                Position(x, y),
                "resource",
                radius,
                energy_value=random.uniform(10, 50),
                regeneration_rate=random.uniform(0.1, 0.5)
            )
            self.features.append(resource)
    
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the world."""
        # Ensure agent is within world bounds
        agent.state.position.x = max(0, min(self.width, agent.state.position.x))
        agent.state.position.y = max(0, min(self.height, agent.state.position.y))
        
        self.agents[agent.agent_id] = agent
        self.spatial_grid.add_agent(agent)
        self.total_agents_created += 1
    
    def remove_agent(self, agent: Agent) -> None:
        """Remove an agent from the world."""
        if agent.agent_id in self.agents:
            self.spatial_grid.remove_agent(agent.agent_id)
            del self.agents[agent.agent_id]
            self.total_agents_removed += 1
    
    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)
    
    def get_agents_in_radius(self, position: Position, radius: float) -> List[Agent]:
        """Get all agents within a radius of a position."""
        nearby_agent_ids = self.spatial_grid.get_nearby_agents(position, radius)
        nearby_agents = []
        
        for agent_id in nearby_agent_ids:
            agent = self.agents.get(agent_id)
            if agent:
                distance = position.distance_to(agent.state.position)
                if distance <= radius:
                    nearby_agents.append(agent)
        
        return nearby_agents
    
    def get_features_in_radius(self, position: Position, radius: float) -> List[EnvironmentFeature]:
        """Get environmental features within a radius."""
        nearby_features = []
        
        for feature in self.features:
            if not feature.active:
                continue
            
            distance = position.distance_to(feature.position)
            if distance <= radius + feature.radius:
                nearby_features.append(feature)
        
        return nearby_features
    
    def is_position_valid(self, position: Position, agent_radius: float = 2.0) -> bool:
        """Check if a position is valid (not inside obstacles)."""
        # Check world boundaries
        if (position.x < agent_radius or position.x > self.width - agent_radius or
            position.y < agent_radius or position.y > self.height - agent_radius):
            return False
        
        # Check obstacles
        for feature in self.features:
            if feature.feature_type == "obstacle" and feature.active:
                distance = position.distance_to(feature.position)
                if distance < feature.radius + agent_radius:
                    return False
        
        return True
    
    def get_random_valid_position(self, agent_radius: float = 2.0, max_attempts: int = 100) -> Position:
        """Get a random valid position in the world."""
        for _ in range(max_attempts):
            x = random.uniform(agent_radius, self.width - agent_radius)
            y = random.uniform(agent_radius, self.height - agent_radius)
            position = Position(x, y)
            
            if self.is_position_valid(position, agent_radius):
                return position
        
        # Fallback to center if no valid position found
        return Position(self.width / 2, self.height / 2)
    
    def update_physics(self, dt: float) -> List[Event]:
        """Update physics simulation."""
        # Update agent positions in spatial grid first
        for agent in self.agents.values():
            self.spatial_grid.update_agent(agent)
        
        # Run physics simulation
        events = self.physics.update(self.agents, dt)
        
        return events
    
    def update_environment(self, dt: float) -> None:
        """Update environmental conditions."""
        self.time += dt
        
        # Simulate weather changes (very simple)
        if random.random() < 0.001:  # 0.1% chance per step
            self.temperature += random.uniform(-1, 1)
            self.temperature = max(-20, min(40, self.temperature))
        
        if random.random() < 0.001:
            self.humidity += random.uniform(-0.05, 0.05)
            self.humidity = max(0, min(1, self.humidity))
        
        # Update wind
        if random.random() < 0.01:  # 1% chance per step
            self.wind_speed = max(0, self.wind_speed + random.uniform(-0.5, 0.5))
            self.wind_direction += random.uniform(-0.1, 0.1)
            
            # Update physics wind
            import math
            wind_x = self.wind_speed * math.cos(self.wind_direction)
            wind_y = self.wind_speed * math.sin(self.wind_direction)
            self.physics.set_wind(wind_x, wind_y)
        
        # Update resources (regeneration)
        for feature in self.features:
            if feature.feature_type == "resource" and feature.active:
                regen_rate = feature.properties.get("regeneration_rate", 0.1)
                max_energy = feature.properties.get("max_energy_value", 100)
                current_energy = feature.properties.get("energy_value", 0)
                
                new_energy = min(max_energy, current_energy + regen_rate * dt)
                feature.properties["energy_value"] = new_energy
    
    def update(self, dt: float) -> List[Event]:
        """Update the entire world simulation."""
        events = []
        
        # Update environment
        self.update_environment(dt)
        
        # Update physics (this also updates agent positions)
        physics_events = self.update_physics(dt)
        events.extend(physics_events)
        
        return events
    
    def reset(self) -> None:
        """Reset the world to initial state."""
        self.agents.clear()
        self.spatial_grid.clear()
        self.features.clear()
        self.time = 0.0
        self.temperature = 20.0
        self.humidity = 0.5
        self.wind_speed = 0.0
        self.wind_direction = 0.0
        self.total_agents_created = 0
        self.total_agents_removed = 0
        
        # Reinitialize environment
        self._initialize_environment()
    
    def get_world_info(self, position: Position, radius: float) -> Dict[str, Any]:
        """Get information about the world around a position."""
        nearby_agents = self.get_agents_in_radius(position, radius)
        nearby_features = self.get_features_in_radius(position, radius)
        
        return {
            "agents": [
                {
                    "id": agent.agent_id,
                    "position": agent.state.position,
                    "distance": position.distance_to(agent.state.position)
                }
                for agent in nearby_agents
            ],
            "features": [
                {
                    "type": feature.feature_type,
                    "position": feature.position,
                    "radius": feature.radius,
                    "distance": position.distance_to(feature.position),
                    "properties": feature.properties
                }
                for feature in nearby_features
            ],
            "environment": {
                "temperature": self.temperature,
                "humidity": self.humidity,
                "wind_speed": self.wind_speed,
                "wind_direction": self.wind_direction,
                "world_time": self.time
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get world statistics."""
        active_agents = len(self.agents)
        active_obstacles = len([f for f in self.features if f.feature_type == "obstacle" and f.active])
        active_resources = len([f for f in self.features if f.feature_type == "resource" and f.active])
        
        spatial_stats = self.spatial_grid.get_stats()
        
        return {
            "world_size": (self.width, self.height),
            "simulation_time": self.time,
            "agents": {
                "active": active_agents,
                "total_created": self.total_agents_created,
                "total_removed": self.total_agents_removed
            },
            "features": {
                "obstacles": active_obstacles,
                "resources": active_resources,
                "total": len(self.features)
            },
            "environment": {
                "temperature": self.temperature,
                "humidity": self.humidity,
                "wind_speed": self.wind_speed
            },
            "spatial_grid": spatial_stats
        }