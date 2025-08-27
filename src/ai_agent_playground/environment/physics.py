"""Physics simulation for the environment."""

from typing import List, Dict, Tuple, Optional
import math
from dataclasses import dataclass

from ..core.agent import Agent, Position
from ..core.events import Event, EventType


@dataclass
class Force:
    """Represents a force vector."""
    fx: float
    fy: float
    duration: float = 1.0  # How long the force lasts


class PhysicsEngine:
    """Simple physics engine for agent movement and interactions."""
    
    def __init__(self, world_width: float, world_height: float):
        self.world_width = world_width
        self.world_height = world_height
        
        # Physics parameters
        self.friction = 0.95
        self.bounce_damping = 0.7
        self.collision_radius = 2.0
        
        # Track forces applied to agents
        self.agent_forces: Dict[str, List[Force]] = {}
        
        # Gravity and global forces
        self.gravity = (0.0, 0.0)  # (gx, gy)
        self.wind = (0.0, 0.0)    # (wx, wy)
    
    def apply_force(self, agent_id: str, force: Force) -> None:
        """Apply a force to an agent."""
        if agent_id not in self.agent_forces:
            self.agent_forces[agent_id] = []
        self.agent_forces[agent_id].append(force)
    
    def set_gravity(self, gx: float, gy: float) -> None:
        """Set global gravity."""
        self.gravity = (gx, gy)
    
    def set_wind(self, wx: float, wy: float) -> None:
        """Set global wind force."""
        self.wind = (wx, wy)
    
    def update(self, agents: Dict[str, Agent], dt: float) -> List[Event]:
        """Update physics for all agents."""
        events = []
        
        # Update each agent
        for agent_id, agent in agents.items():
            # Apply forces
            total_fx, total_fy = self._calculate_total_forces(agent_id, agent)
            
            # Update velocity based on forces
            vx, vy = agent.state.velocity
            vx += total_fx * dt
            vy += total_fy * dt
            
            # Apply friction
            vx *= self.friction
            vy *= self.friction
            
            # Update position
            old_position = Position(agent.state.position.x, agent.state.position.y)
            new_x = agent.state.position.x + vx * dt
            new_y = agent.state.position.y + vy * dt
            
            # Handle boundary collisions
            collision_event = self._handle_boundaries(agent, new_x, new_y)
            if collision_event:
                events.append(collision_event)
                vx, vy = agent.state.velocity  # May have been modified by boundary collision
            
            # Update agent state
            agent.state.velocity = (vx, vy)
            
            # Clean up expired forces
            self._cleanup_forces(agent_id)
        
        # Check for agent-agent collisions
        collision_events = self._check_agent_collisions(agents)
        events.extend(collision_events)
        
        return events
    
    def _calculate_total_forces(self, agent_id: str, agent: Agent) -> Tuple[float, float]:
        """Calculate total forces acting on an agent."""
        total_fx = self.gravity[0] + self.wind[0]
        total_fy = self.gravity[1] + self.wind[1]
        
        # Add applied forces
        if agent_id in self.agent_forces:
            for force in self.agent_forces[agent_id]:
                total_fx += force.fx
                total_fy += force.fy
        
        return total_fx, total_fy
    
    def _handle_boundaries(self, agent: Agent, new_x: float, new_y: float) -> Optional[Event]:
        """Handle collisions with world boundaries."""
        collision = False
        vx, vy = agent.state.velocity
        
        # Left/right boundaries
        if new_x < 0:
            new_x = 0
            vx = -vx * self.bounce_damping
            collision = True
        elif new_x > self.world_width:
            new_x = self.world_width
            vx = -vx * self.bounce_damping
            collision = True
        
        # Top/bottom boundaries
        if new_y < 0:
            new_y = 0
            vy = -vy * self.bounce_damping
            collision = True
        elif new_y > self.world_height:
            new_y = self.world_height
            vy = -vy * self.bounce_damping
            collision = True
        
        # Update agent position and velocity
        agent.state.position.x = new_x
        agent.state.position.y = new_y
        agent.state.velocity = (vx, vy)
        
        if collision:
            return Event(
                event_type=EventType.COLLISION,
                timestamp=agent.state.position.__class__.__module__,  # Placeholder for datetime
                source_id=agent.agent_id,
                data={
                    "collision_type": "boundary",
                    "position": {"x": new_x, "y": new_y}
                }
            )
        
        return None
    
    def _check_agent_collisions(self, agents: Dict[str, Agent]) -> List[Event]:
        """Check for collisions between agents."""
        events = []
        agent_list = list(agents.values())
        
        for i, agent1 in enumerate(agent_list):
            for agent2 in agent_list[i+1:]:
                distance = agent1.state.position.distance_to(agent2.state.position)
                
                if distance < self.collision_radius * 2:
                    # Collision detected
                    self._resolve_collision(agent1, agent2)
                    
                    # Create collision event
                    collision_event = Event(
                        event_type=EventType.COLLISION,
                        timestamp=agent1.state.position.__class__.__module__,  # Placeholder
                        source_id=agent1.agent_id,
                        target_id=agent2.agent_id,
                        data={
                            "collision_type": "agent",
                            "distance": distance,
                            "position1": {"x": agent1.state.position.x, "y": agent1.state.position.y},
                            "position2": {"x": agent2.state.position.x, "y": agent2.state.position.y}
                        }
                    )
                    events.append(collision_event)
        
        return events
    
    def _resolve_collision(self, agent1: Agent, agent2: Agent) -> None:
        """Resolve collision between two agents."""
        # Calculate collision vector
        dx = agent2.state.position.x - agent1.state.position.x
        dy = agent2.state.position.y - agent1.state.position.y
        distance = (dx * dx + dy * dy) ** 0.5
        
        if distance == 0:
            return  # Agents are at exact same position
        
        # Normalize collision vector
        nx = dx / distance
        ny = dy / distance
        
        # Separate agents
        overlap = (self.collision_radius * 2) - distance
        separation = overlap / 2
        
        agent1.state.position.x -= nx * separation
        agent1.state.position.y -= ny * separation
        agent2.state.position.x += nx * separation
        agent2.state.position.y += ny * separation
        
        # Exchange some velocity (simplified elastic collision)
        v1x, v1y = agent1.state.velocity
        v2x, v2y = agent2.state.velocity
        
        # Project velocities onto collision normal
        v1n = v1x * nx + v1y * ny
        v2n = v2x * nx + v2y * ny
        
        # Exchange normal components with damping
        new_v1n = v2n * self.bounce_damping
        new_v2n = v1n * self.bounce_damping
        
        # Calculate new velocities
        agent1.state.velocity = (
            v1x + (new_v1n - v1n) * nx,
            v1y + (new_v1n - v1n) * ny
        )
        agent2.state.velocity = (
            v2x + (new_v2n - v2n) * nx,
            v2y + (new_v2n - v2n) * ny
        )
        
        # Apply collision damage (small health reduction)
        impact_force = abs(v1n - v2n)
        damage = min(1.0, impact_force * 0.1)
        
        agent1.state.health = max(0, agent1.state.health - damage)
        agent2.state.health = max(0, agent2.state.health - damage)
    
    def _cleanup_forces(self, agent_id: str) -> None:
        """Remove expired forces from an agent."""
        if agent_id not in self.agent_forces:
            return
        
        # Reduce duration of all forces and remove expired ones
        active_forces = []
        for force in self.agent_forces[agent_id]:
            force.duration -= 1.0
            if force.duration > 0:
                active_forces.append(force)
        
        self.agent_forces[agent_id] = active_forces
    
    def add_explosion(self, center: Position, radius: float, strength: float, agents: Dict[str, Agent]) -> None:
        """Add an explosion effect that pushes nearby agents away."""
        for agent in agents.values():
            distance = center.distance_to(agent.state.position)
            if distance < radius and distance > 0:
                # Calculate force magnitude (inverse square law with minimum)
                force_magnitude = strength / max(1.0, distance * distance)
                
                # Calculate direction
                dx = agent.state.position.x - center.x
                dy = agent.state.position.y - center.y
                
                # Normalize
                fx = (dx / distance) * force_magnitude
                fy = (dy / distance) * force_magnitude
                
                # Apply impulse force
                explosion_force = Force(fx, fy, duration=5.0)
                self.apply_force(agent.agent_id, explosion_force)