"""Tests for core simulator components."""

import pytest
from datetime import datetime, timedelta

from ai_agent_playground.core.agent import Agent, Position, AgentState
from ai_agent_playground.core.events import Event, EventType, EventManager
from ai_agent_playground.core.engine import SimulatorEngine, SimulationConfig


class TestAgent(Agent):
    """Test agent implementation."""
    
    def decide_action(self, observations):
        return {"action": "idle"}
    
    def update(self, dt, observations):
        pass


class TestPosition:
    """Tests for Position class."""
    
    def test_position_creation(self):
        pos = Position(10.0, 20.0)
        assert pos.x == 10.0
        assert pos.y == 20.0
    
    def test_distance_calculation(self):
        pos1 = Position(0.0, 0.0)
        pos2 = Position(3.0, 4.0)
        
        distance = pos1.distance_to(pos2)
        assert distance == 5.0  # 3-4-5 triangle
    
    def test_distance_zero(self):
        pos1 = Position(5.0, 5.0)
        pos2 = Position(5.0, 5.0)
        
        distance = pos1.distance_to(pos2)
        assert distance == 0.0


class TestAgent:
    """Tests for Agent class."""
    
    def test_agent_creation(self):
        position = Position(10.0, 15.0)
        agent = TestAgent(position=position)
        
        assert agent.state.position.x == 10.0
        assert agent.state.position.y == 15.0
        assert agent.state.energy == 100.0
        assert agent.state.health == 100.0
        assert agent.state.active is True
    
    def test_agent_movement(self):
        agent = TestAgent(position=Position(0.0, 0.0))
        
        agent.move(5.0, 3.0)
        
        assert agent.state.position.x == 5.0
        assert agent.state.position.y == 3.0
        assert agent.state.velocity == (5.0, 3.0)
        assert agent.state.last_action == "move"
    
    def test_energy_consumption(self):
        agent = TestAgent()
        initial_energy = agent.state.energy
        
        agent.consume_energy(25.0)
        
        assert agent.state.energy == initial_energy - 25.0
    
    def test_energy_cannot_go_negative(self):
        agent = TestAgent()
        
        agent.consume_energy(150.0)  # More than initial energy
        
        assert agent.state.energy == 0.0
    
    def test_agent_alive_check(self):
        agent = TestAgent()
        assert agent.is_alive() is True
        
        agent.state.health = 0
        assert agent.is_alive() is False
        
        agent.state.health = 50
        agent.state.energy = 0
        assert agent.is_alive() is False
        
        agent.state.energy = 50
        agent.state.active = False
        assert agent.is_alive() is False
    
    def test_memory_management(self):
        agent = TestAgent()
        
        agent.add_memory({"type": "test", "data": "some data"})
        
        assert len(agent.memory) == 1
        assert agent.memory[0]["type"] == "test"
        assert "timestamp" in agent.memory[0]
    
    def test_agent_serialization(self):
        agent = TestAgent(position=Position(10.0, 20.0))
        agent_dict = agent.to_dict()
        
        assert agent_dict["agent_id"] == agent.agent_id
        assert agent_dict["state"]["position"]["x"] == 10.0
        assert agent_dict["state"]["position"]["y"] == 20.0


class TestEvent:
    """Tests for Event system."""
    
    def test_event_creation(self):
        event = Event(
            event_type=EventType.AGENT_SPAWN,
            timestamp=datetime.now(),
            source_id="test_agent",
            data={"position": {"x": 10, "y": 20}}
        )
        
        assert event.event_type == EventType.AGENT_SPAWN
        assert event.source_id == "test_agent"
        assert event.data["position"]["x"] == 10
        assert event.event_id is not None


class TestEventManager:
    """Tests for EventManager."""
    
    def test_event_manager_creation(self):
        manager = EventManager()
        assert len(manager._handlers) == 0
        assert len(manager._event_history) == 0
    
    def test_subscription(self):
        manager = EventManager()
        handler = TestAgent()
        
        manager.subscribe(EventType.AGENT_SPAWN, handler)
        
        assert EventType.AGENT_SPAWN in manager._handlers
        assert handler in manager._handlers[EventType.AGENT_SPAWN]
    
    def test_event_publishing(self):
        manager = EventManager()
        handler = TestAgent()
        manager.subscribe(EventType.AGENT_SPAWN, handler)
        
        event = Event(
            event_type=EventType.AGENT_SPAWN,
            timestamp=datetime.now(),
            source_id="test"
        )
        
        manager.publish(event)
        
        assert len(manager._event_history) == 1
        assert event in manager._event_history
    
    def test_event_history_filtering(self):
        manager = EventManager()
        
        spawn_event = Event(EventType.AGENT_SPAWN, datetime.now(), "agent1")
        death_event = Event(EventType.AGENT_DEATH, datetime.now(), "agent2")
        
        manager.publish(spawn_event)
        manager.publish(death_event)
        
        spawn_history = manager.get_event_history(EventType.AGENT_SPAWN)
        death_history = manager.get_event_history(EventType.AGENT_DEATH)
        all_history = manager.get_event_history()
        
        assert len(spawn_history) == 1
        assert len(death_history) == 1
        assert len(all_history) == 2


class TestSimulationConfig:
    """Tests for SimulationConfig."""
    
    def test_default_config(self):
        config = SimulationConfig()
        
        assert config.time_step == 0.1
        assert config.max_steps == 1000
        assert config.world_width == 1000.0
        assert config.world_height == 1000.0
    
    def test_custom_config(self):
        config = SimulationConfig(
            time_step=0.05,
            max_steps=2000,
            world_width=500.0,
            world_height=300.0
        )
        
        assert config.time_step == 0.05
        assert config.max_steps == 2000
        assert config.world_width == 500.0
        assert config.world_height == 300.0


class TestSimulatorEngine:
    """Tests for SimulatorEngine."""
    
    def test_engine_creation(self):
        config = SimulationConfig(max_steps=100)
        engine = SimulatorEngine(config)
        
        assert engine.config.max_steps == 100
        assert len(engine.agents) == 0
        assert engine.running is False
        assert engine.current_step == 0
    
    def test_add_agent(self):
        engine = SimulatorEngine()
        agent = TestAgent(position=Position(50.0, 50.0))
        
        engine.add_agent(agent)
        
        assert agent.agent_id in engine.agents
        assert agent in engine.world.agents.values()
    
    def test_remove_agent(self):
        engine = SimulatorEngine()
        agent = TestAgent(position=Position(50.0, 50.0))
        
        engine.add_agent(agent)
        engine.remove_agent(agent.agent_id)
        
        assert agent.agent_id not in engine.agents
    
    def test_simulation_step(self):
        engine = SimulatorEngine(SimulationConfig(max_steps=10))
        agent = TestAgent(position=Position(50.0, 50.0))
        engine.add_agent(agent)
        
        initial_step = engine.current_step
        engine.step()
        
        assert engine.current_step == initial_step + 1
        assert engine.simulation_time > 0
    
    def test_simulation_run_short(self):
        config = SimulationConfig(max_steps=5)
        engine = SimulatorEngine(config)
        agent = TestAgent(position=Position(50.0, 50.0))
        engine.add_agent(agent)
        
        engine.run()
        
        assert engine.current_step == 5
        assert engine.running is False
    
    def test_callback_system(self):
        engine = SimulatorEngine(SimulationConfig(max_steps=3))
        callback_calls = []
        
        def test_callback(sim):
            callback_calls.append(sim.current_step)
        
        engine.add_callback("step_end", test_callback)
        agent = TestAgent(position=Position(50.0, 50.0))
        engine.add_agent(agent)
        
        engine.run()
        
        assert len(callback_calls) == 3
        assert callback_calls == [1, 2, 3]
    
    def test_simulation_status(self):
        engine = SimulatorEngine()
        agent = TestAgent(position=Position(50.0, 50.0))
        engine.add_agent(agent)
        
        status = engine.get_status()
        
        assert "running" in status
        assert "step" in status
        assert "agent_count" in status
        assert status["agent_count"] == 1
    
    def test_simulation_reset(self):
        engine = SimulatorEngine()
        agent = TestAgent(position=Position(50.0, 50.0))
        engine.add_agent(agent)
        
        engine.step()
        engine.reset()
        
        assert len(engine.agents) == 0
        assert engine.current_step == 0
        assert engine.simulation_time == 0.0