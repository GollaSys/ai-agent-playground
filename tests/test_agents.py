"""Tests for agent types and behaviors."""

import pytest
from unittest.mock import Mock

from ai_agent_playground.core.agent import Position
from ai_agent_playground.agents.types import AutonomousAgent, ReactiveAgent, WandererAgent, AgentType
from ai_agent_playground.agents.behaviors import WanderBehavior, SeekBehavior, FlockBehavior, AutonomousBehavior


class TestAgentTypes:
    """Tests for different agent types."""
    
    def test_autonomous_agent_creation(self):
        position = Position(10.0, 20.0)
        agent = AutonomousAgent(position=position)
        
        assert agent.state.position.x == 10.0
        assert agent.state.position.y == 20.0
        assert hasattr(agent, 'intelligence')
        assert hasattr(agent, 'adaptability')
        assert hasattr(agent, 'behavior')
        assert 0.7 <= agent.intelligence <= 1.0
        assert 0.5 <= agent.adaptability <= 1.0
    
    def test_reactive_agent_creation(self):
        position = Position(15.0, 25.0)
        agent = ReactiveAgent(position=position)
        
        assert agent.state.position.x == 15.0
        assert agent.state.position.y == 25.0
        assert hasattr(agent, 'reaction_speed')
        assert hasattr(agent, 'sensitivity')
        assert 0.6 <= agent.reaction_speed <= 1.0
        assert 0.4 <= agent.sensitivity <= 0.9
    
    def test_wanderer_agent_creation(self):
        position = Position(5.0, 35.0)
        agent = WandererAgent(position=position)
        
        assert agent.state.position.x == 5.0
        assert agent.state.position.y == 35.0
        assert hasattr(agent, 'curiosity')
        assert 0.3 <= agent.curiosity <= 0.8
    
    def test_agent_type_factory(self):
        position = Position(0.0, 0.0)
        
        autonomous = AgentType.create_autonomous_agent(position=position)
        reactive = AgentType.create_reactive_agent(position=position)
        wanderer = AgentType.create_wanderer_agent(position=position)
        
        assert isinstance(autonomous, AutonomousAgent)
        assert isinstance(reactive, ReactiveAgent)
        assert isinstance(wanderer, WandererAgent)


class TestAgentBehaviors:
    """Tests for agent behaviors."""
    
    def test_wander_behavior(self):
        behavior = WanderBehavior(max_speed=2.0)
        agent = WandererAgent(position=Position(50.0, 50.0))
        observations = {"nearby_agents": []}
        
        action = behavior.execute(agent, observations)
        
        assert "action" in action
        assert action["action"] == "move"
        assert "dx" in action
        assert "dy" in action
        assert "energy_cost" in action
        
        # Check that movement is within speed limits
        speed = (action["dx"]**2 + action["dy"]**2)**0.5
        assert speed <= 2.0
    
    def test_seek_behavior(self):
        target = Position(100.0, 100.0)
        behavior = SeekBehavior(target, max_speed=3.0)
        agent = WandererAgent(position=Position(50.0, 50.0))
        observations = {}
        
        action = behavior.execute(agent, observations)
        
        assert action["action"] == "move"
        assert action["dx"] > 0  # Should move towards target
        assert action["dy"] > 0  # Should move towards target
    
    def test_seek_behavior_at_target(self):
        target = Position(50.0, 50.0)
        behavior = SeekBehavior(target, max_speed=3.0)
        agent = WandererAgent(position=Position(50.0, 50.0))
        observations = {}
        
        action = behavior.execute(agent, observations)
        
        assert action["action"] == "idle"
    
    def test_flock_behavior_no_neighbors(self):
        behavior = FlockBehavior()
        agent = AutonomousAgent(position=Position(50.0, 50.0))
        observations = {"nearby_agents": []}
        
        action = behavior.execute(agent, observations)
        
        # Should default to wandering when no neighbors
        assert "action" in action
        assert "dx" in action
        assert "dy" in action
    
    def test_flock_behavior_with_neighbors(self):
        behavior = FlockBehavior()
        agent = AutonomousAgent(position=Position(50.0, 50.0))
        
        # Mock nearby agents
        nearby_agents = [
            {
                "id": "agent1",
                "position": Position(55.0, 55.0),
                "distance": 7.07  # sqrt(5^2 + 5^2)
            },
            {
                "id": "agent2", 
                "position": Position(45.0, 45.0),
                "distance": 7.07
            }
        ]
        observations = {"nearby_agents": nearby_agents}
        
        action = behavior.execute(agent, observations)
        
        assert action["action"] == "move"
        assert "dx" in action
        assert "dy" in action
        assert "energy_cost" in action
    
    def test_autonomous_behavior(self):
        behavior = AutonomousBehavior()
        agent = AutonomousAgent(position=Position(50.0, 50.0))
        observations = {"nearby_agents": []}
        
        action = behavior.execute(agent, observations)
        
        assert "action" in action
        assert "energy_cost" in action


class TestAgentUpdate:
    """Tests for agent update methods."""
    
    def test_autonomous_agent_update(self):
        agent = AutonomousAgent(position=Position(50.0, 50.0))
        initial_energy = agent.state.energy
        initial_age = agent.state.age
        
        observations = {"nearby_agents": []}
        agent.update(0.1, observations)
        
        # Energy should be consumed
        assert agent.state.energy < initial_energy
        # Age should not increase here (engine handles that)
    
    def test_reactive_agent_update(self):
        agent = ReactiveAgent(position=Position(50.0, 50.0))
        initial_energy = agent.state.energy
        
        observations = {"nearby_agents": []}
        agent.update(0.1, observations)
        
        assert agent.state.energy < initial_energy
    
    def test_wanderer_agent_update(self):
        agent = WandererAgent(position=Position(50.0, 50.0))
        initial_energy = agent.state.energy
        
        observations = {"nearby_agents": []}
        agent.update(0.1, observations)
        
        assert agent.state.energy < initial_energy


class TestAgentDecisionMaking:
    """Tests for agent decision making."""
    
    def test_autonomous_agent_decisions(self):
        agent = AutonomousAgent(position=Position(50.0, 50.0))
        observations = {"nearby_agents": []}
        
        action = agent.decide_action(observations)
        
        assert isinstance(action, dict)
        assert "action" in action or "dx" in action
    
    def test_reactive_agent_decisions(self):
        agent = ReactiveAgent(position=Position(50.0, 50.0))
        
        # Test with no threats
        observations = {"nearby_agents": []}
        action = agent.decide_action(observations)
        assert isinstance(action, dict)
        
        # Test with nearby threat
        threat_observations = {
            "nearby_agents": [{
                "id": "threat",
                "position": Position(52.0, 52.0),
                "distance": 5.0  # Within threat range
            }]
        }
        action = agent.decide_action(threat_observations)
        assert isinstance(action, dict)
    
    def test_wanderer_agent_decisions(self):
        agent = WandererAgent(position=Position(50.0, 50.0))
        observations = {"nearby_agents": []}
        
        action = agent.decide_action(observations)
        
        assert isinstance(action, dict)
        assert "action" in action


class TestAgentMemory:
    """Tests for agent memory functionality."""
    
    def test_memory_addition(self):
        agent = AutonomousAgent(position=Position(50.0, 50.0))
        initial_memory_size = len(agent.memory)
        
        agent.add_memory({"type": "observation", "data": "test_data"})
        
        assert len(agent.memory) == initial_memory_size + 1
        assert agent.memory[-1]["type"] == "observation"
        assert "timestamp" in agent.memory[-1]
    
    def test_memory_limit(self):
        agent = AutonomousAgent(position=Position(50.0, 50.0))
        
        # Add many memories (more than the limit of 1000)
        for i in range(1200):
            agent.add_memory({"type": "test", "data": f"item_{i}"})
        
        # Should be limited to 1000
        assert len(agent.memory) == 1000
        # Should keep the most recent memories
        assert agent.memory[-1]["data"] == "item_1199"


class TestAgentInteractions:
    """Tests for agent interactions."""
    
    def test_agent_sensing(self):
        # This would require a world mock, but we can test the interface
        agent = AutonomousAgent(position=Position(50.0, 50.0))
        
        # Mock world
        mock_world = Mock()
        mock_world.get_agents_in_radius.return_value = []
        
        observations = agent.sense(mock_world)
        
        assert "position" in observations
        assert "energy" in observations
        assert "health" in observations
        assert "nearby_agents" in observations