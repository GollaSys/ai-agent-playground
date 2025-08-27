"""Main simulation engine."""

import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass

from .agent import Agent
from .events import EventManager, Event, EventType
from ..environment.world import World
from ..utils.logging_config import setup_logging
from ..utils.metrics import MetricsCollector

logger = setup_logging(__name__)


@dataclass
class SimulationConfig:
    """Configuration for simulation parameters."""
    time_step: float = 0.1
    max_steps: int = 1000
    real_time: bool = False
    enable_physics: bool = True
    enable_visualization: bool = False
    max_agents: int = 1000
    world_width: float = 1000.0
    world_height: float = 1000.0
    random_seed: Optional[int] = None


class SimulatorEngine:
    """Main simulation engine that orchestrates all components."""
    
    def __init__(self, config: Optional[SimulationConfig] = None) -> None:
        self.config = config or SimulationConfig()
        self.world = World(
            width=self.config.world_width,
            height=self.config.world_height
        )
        self.event_manager = EventManager()
        self.metrics = MetricsCollector()
        
        self.agents: Dict[str, Agent] = {}
        self.running = False
        self.paused = False
        self.current_step = 0
        self.simulation_time = 0.0
        self.start_time: Optional[datetime] = None
        
        self._callbacks: Dict[str, List[Callable]] = {
            "step_start": [],
            "step_end": [],
            "simulation_start": [],
            "simulation_end": []
        }
        
        logger.info(f"Simulator engine initialized with config: {self.config}")
    
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the simulation."""
        if len(self.agents) >= self.config.max_agents:
            logger.warning(f"Max agents ({self.config.max_agents}) reached")
            return
        
        self.agents[agent.agent_id] = agent
        self.world.add_agent(agent)
        self.event_manager.subscribe(EventType.AGENT_SPAWN, agent)
        self.event_manager.subscribe(EventType.ENVIRONMENT_CHANGE, agent)
        
        # Publish spawn event
        spawn_event = Event(
            event_type=EventType.AGENT_SPAWN,
            timestamp=datetime.now(),
            source_id="simulator",
            target_id=agent.agent_id,
            data={"position": agent.state.position}
        )
        self.event_manager.publish(spawn_event)
        
        logger.info(f"Added agent {agent.agent_id}")
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the simulation."""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            self.world.remove_agent(agent)
            
            # Publish death event
            death_event = Event(
                event_type=EventType.AGENT_DEATH,
                timestamp=datetime.now(),
                source_id="simulator",
                target_id=agent_id,
                data={"final_position": agent.state.position}
            )
            self.event_manager.publish(death_event)
            
            del self.agents[agent_id]
            logger.info(f"Removed agent {agent_id}")
    
    def add_callback(self, event_type: str, callback: Callable) -> None:
        """Add a callback for simulation events."""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)
    
    def step(self) -> None:
        """Execute one simulation step."""
        if self.paused:
            return
        
        step_start_time = time.time()
        
        # Execute step start callbacks
        for callback in self._callbacks["step_start"]:
            callback(self)
        
        # Update world physics
        if self.config.enable_physics:
            self.world.update_physics(self.config.time_step)
        
        # Update all agents
        dead_agents = []
        for agent_id, agent in self.agents.items():
            if not agent.is_alive():
                dead_agents.append(agent_id)
                continue
            
            # Get observations for the agent
            observations = agent.sense(self.world)
            
            # Let agent decide and act
            try:
                agent.update(self.config.time_step, observations)
                
                # Age the agent
                agent.state.age += 1
                
                # Consume base energy
                agent.consume_energy(0.1)
                
            except Exception as e:
                logger.error(f"Error updating agent {agent_id}: {e}")
                dead_agents.append(agent_id)
        
        # Remove dead agents
        for agent_id in dead_agents:
            self.remove_agent(agent_id)
        
        # Update world state
        self.world.update(self.config.time_step)
        
        # Update simulation state
        self.current_step += 1
        self.simulation_time += self.config.time_step
        
        # Collect metrics
        self.metrics.record_metric("simulation_step", self.current_step)
        self.metrics.record_metric("active_agents", len(self.agents))
        self.metrics.record_metric("step_duration", time.time() - step_start_time)
        
        # Execute step end callbacks
        for callback in self._callbacks["step_end"]:
            callback(self)
        
        logger.debug(f"Step {self.current_step} completed in {time.time() - step_start_time:.4f}s")
    
    def run(self) -> None:
        """Run the simulation."""
        if self.running:
            logger.warning("Simulation is already running")
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        # Execute simulation start callbacks
        for callback in self._callbacks["simulation_start"]:
            callback(self)
        
        logger.info(f"Starting simulation with {len(self.agents)} agents")
        
        try:
            while (self.running and 
                   self.current_step < self.config.max_steps and 
                   len(self.agents) > 0):
                
                step_start_time = time.time()
                self.step()
                
                # Handle real-time simulation
                if self.config.real_time:
                    elapsed = time.time() - step_start_time
                    sleep_time = self.config.time_step - elapsed
                    if sleep_time > 0:
                        time.sleep(sleep_time)
        
        except KeyboardInterrupt:
            logger.info("Simulation interrupted by user")
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            raise
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the simulation."""
        self.running = False
        
        # Execute simulation end callbacks
        for callback in self._callbacks["simulation_end"]:
            callback(self)
        
        end_time = datetime.now()
        if self.start_time:
            duration = end_time - self.start_time
            logger.info(f"Simulation completed in {duration}")
        
        logger.info(f"Final statistics:")
        logger.info(f"  - Steps: {self.current_step}")
        logger.info(f"  - Simulation time: {self.simulation_time:.2f}s")
        logger.info(f"  - Agents remaining: {len(self.agents)}")
    
    def pause(self) -> None:
        """Pause the simulation."""
        self.paused = True
        logger.info("Simulation paused")
    
    def resume(self) -> None:
        """Resume the simulation."""
        self.paused = False
        logger.info("Simulation resumed")
    
    def reset(self) -> None:
        """Reset the simulation to initial state."""
        self.stop()
        self.agents.clear()
        self.world.reset()
        self.event_manager.clear_history()
        self.metrics.reset()
        self.current_step = 0
        self.simulation_time = 0.0
        self.start_time = None
        logger.info("Simulation reset")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current simulation status."""
        return {
            "running": self.running,
            "paused": self.paused,
            "step": self.current_step,
            "simulation_time": self.simulation_time,
            "agent_count": len(self.agents),
            "world_size": (self.config.world_width, self.config.world_height),
            "start_time": self.start_time.isoformat() if self.start_time else None
        }