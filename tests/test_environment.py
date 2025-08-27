"""Tests for environment and world simulation."""

import pytest
from unittest.mock import Mock

from ai_agent_playground.core.agent import Position
from ai_agent_playground.agents.types import WandererAgent
from ai_agent_playground.environment.world import World, EnvironmentFeature
from ai_agent_playground.environment.spatial import SpatialGrid
from ai_agent_playground.environment.physics import PhysicsEngine, Force


class TestSpatialGrid:
    """Tests for spatial grid partitioning."""
    
    def test_spatial_grid_creation(self):
        grid = SpatialGrid(width=100.0, height=100.0, cell_size=10.0)
        
        assert grid.width == 100.0
        assert grid.height == 100.0
        assert grid.cell_size == 10.0
        assert grid.cols == 10
        assert grid.rows == 10
    
    def test_cell_coordinate_calculation(self):
        grid = SpatialGrid(width=100.0, height=100.0, cell_size=10.0)
        
        # Test various positions
        assert grid._get_cell_coords(Position(5.0, 5.0)) == (0, 0)
        assert grid._get_cell_coords(Position(15.0, 25.0)) == (1, 2)
        assert grid._get_cell_coords(Position(95.0, 95.0)) == (9, 9)
        
        # Test boundary conditions
        assert grid._get_cell_coords(Position(100.0, 100.0)) == (9, 9)  # Should clamp
        assert grid._get_cell_coords(Position(-5.0, -5.0)) == (0, 0)    # Should clamp
    
    def test_agent_addition_and_removal(self):
        grid = SpatialGrid(width=100.0, height=100.0, cell_size=10.0)
        agent = WandererAgent(agent_id="test_agent", position=Position(15.0, 25.0))
        
        grid.add_agent(agent)
        
        assert agent.agent_id in grid.agent_positions
        assert grid.agent_positions[agent.agent_id] == (1, 2)
        assert agent.agent_id in grid.grid[(1, 2)]
        
        grid.remove_agent(agent.agent_id)
        
        assert agent.agent_id not in grid.agent_positions
        assert agent.agent_id not in grid.grid[(1, 2)]
    
    def test_agent_update_position(self):
        grid = SpatialGrid(width=100.0, height=100.0, cell_size=10.0)
        agent = WandererAgent(agent_id="test_agent", position=Position(15.0, 25.0))
        
        grid.add_agent(agent)
        
        # Move agent to different cell
        agent.state.position = Position(35.0, 45.0)
        grid.update_agent(agent)
        
        assert grid.agent_positions[agent.agent_id] == (3, 4)
        assert agent.agent_id in grid.grid[(3, 4)]
        assert agent.agent_id not in grid.grid[(1, 2)]
    
    def test_nearby_agents_query(self):
        grid = SpatialGrid(width=100.0, height=100.0, cell_size=10.0)
        
        # Add agents in different positions
        agent1 = WandererAgent(agent_id="agent1", position=Position(15.0, 15.0))
        agent2 = WandererAgent(agent_id="agent2", position=Position(25.0, 25.0))
        agent3 = WandererAgent(agent_id="agent3", position=Position(75.0, 75.0))
        
        grid.add_agent(agent1)
        grid.add_agent(agent2)
        grid.add_agent(agent3)
        
        # Query for nearby agents
        nearby = grid.get_nearby_agents(Position(20.0, 20.0), radius=15.0)
        
        assert "agent1" in nearby
        assert "agent2" in nearby
        assert "agent3" not in nearby  # Too far
    
    def test_region_query(self):
        grid = SpatialGrid(width=100.0, height=100.0, cell_size=10.0)
        
        agent1 = WandererAgent(agent_id="agent1", position=Position(5.0, 5.0))
        agent2 = WandererAgent(agent_id="agent2", position=Position(15.0, 15.0))
        agent3 = WandererAgent(agent_id="agent3", position=Position(85.0, 85.0))
        
        grid.add_agent(agent1)
        grid.add_agent(agent2)
        grid.add_agent(agent3)
        
        # Query rectangular region
        agents_in_region = grid.get_agents_in_region(0.0, 0.0, 20.0, 20.0)
        
        assert "agent1" in agents_in_region
        assert "agent2" in agents_in_region
        assert "agent3" not in agents_in_region


class TestPhysicsEngine:
    """Tests for physics simulation."""
    
    def test_physics_engine_creation(self):
        physics = PhysicsEngine(world_width=100.0, world_height=100.0)
        
        assert physics.world_width == 100.0
        assert physics.world_height == 100.0
        assert physics.friction > 0
        assert physics.bounce_damping > 0
    
    def test_force_application(self):
        physics = PhysicsEngine(world_width=100.0, world_height=100.0)
        force = Force(fx=10.0, fy=5.0, duration=2.0)
        
        physics.apply_force("agent1", force)
        
        assert "agent1" in physics.agent_forces
        assert len(physics.agent_forces["agent1"]) == 1
        assert physics.agent_forces["agent1"][0].fx == 10.0
    
    def test_gravity_and_wind(self):
        physics = PhysicsEngine(world_width=100.0, world_height=100.0)
        
        physics.set_gravity(0.0, -9.8)
        physics.set_wind(2.0, 0.0)
        
        assert physics.gravity == (0.0, -9.8)
        assert physics.wind == (2.0, 0.0)
    
    def test_boundary_collision(self):
        physics = PhysicsEngine(world_width=100.0, world_height=100.0)
        agent = WandererAgent(position=Position(95.0, 50.0))
        agent.state.velocity = (10.0, 0.0)  # Moving right fast
        
        # This would be called by the physics update
        collision_event = physics._handle_boundaries(agent, 105.0, 50.0)  # Past boundary
        
        assert collision_event is not None
        assert agent.state.position.x == 100.0  # Should be at boundary
        assert agent.state.velocity[0] < 0  # Velocity should reverse
    
    def test_force_cleanup(self):
        physics = PhysicsEngine(world_width=100.0, world_height=100.0)
        
        # Add force with short duration
        force = Force(fx=10.0, fy=5.0, duration=0.5)
        physics.apply_force("agent1", force)
        
        # Force should be there initially
        assert len(physics.agent_forces["agent1"]) == 1
        
        # Clean up forces (simulating time passage)
        physics._cleanup_forces("agent1")
        
        # Force duration should decrease
        assert physics.agent_forces["agent1"][0].duration < 0.5


class TestEnvironmentFeature:
    """Tests for environmental features."""
    
    def test_feature_creation(self):
        position = Position(50.0, 50.0)
        feature = EnvironmentFeature(
            position=position,
            feature_type="obstacle",
            radius=10.0,
            hardness=0.8
        )
        
        assert feature.position == position
        assert feature.feature_type == "obstacle"
        assert feature.radius == 10.0
        assert feature.properties["hardness"] == 0.8
        assert feature.active is True


class TestWorld:
    """Tests for world simulation."""
    
    def test_world_creation(self):
        world = World(width=500.0, height=300.0)
        
        assert world.width == 500.0
        assert world.height == 300.0
        assert len(world.agents) == 0
        assert len(world.features) > 0  # Should have some default features
    
    def test_agent_management(self):
        world = World(width=100.0, height=100.0)
        agent = WandererAgent(position=Position(50.0, 50.0))
        
        world.add_agent(agent)
        
        assert agent.agent_id in world.agents
        assert world.total_agents_created == 1
        
        world.remove_agent(agent)
        
        assert agent.agent_id not in world.agents
        assert world.total_agents_removed == 1
    
    def test_agent_boundary_clamping(self):
        world = World(width=100.0, height=100.0)
        
        # Agent outside boundaries
        agent = WandererAgent(position=Position(150.0, -10.0))
        world.add_agent(agent)
        
        # Position should be clamped to world boundaries
        assert 0 <= agent.state.position.x <= 100.0
        assert 0 <= agent.state.position.y <= 100.0
    
    def test_agents_in_radius_query(self):
        world = World(width=100.0, height=100.0)
        
        agent1 = WandererAgent(agent_id="agent1", position=Position(50.0, 50.0))
        agent2 = WandererAgent(agent_id="agent2", position=Position(55.0, 55.0))
        agent3 = WandererAgent(agent_id="agent3", position=Position(80.0, 80.0))
        
        world.add_agent(agent1)
        world.add_agent(agent2)
        world.add_agent(agent3)
        
        nearby_agents = world.get_agents_in_radius(Position(50.0, 50.0), radius=10.0)
        
        assert agent1 in nearby_agents
        assert agent2 in nearby_agents
        assert agent3 not in nearby_agents
    
    def test_features_in_radius_query(self):
        world = World(width=100.0, height=100.0)
        
        # Add a custom feature
        feature = EnvironmentFeature(
            Position(60.0, 60.0),
            "test_feature",
            radius=5.0
        )
        world.features.append(feature)
        
        nearby_features = world.get_features_in_radius(Position(55.0, 55.0), radius=10.0)
        
        # Should find our test feature
        assert any(f.feature_type == "test_feature" for f in nearby_features)
    
    def test_valid_position_check(self):
        world = World(width=100.0, height=100.0)
        
        # Valid position
        assert world.is_position_valid(Position(50.0, 50.0)) is True
        
        # Invalid positions (outside boundaries)
        assert world.is_position_valid(Position(-5.0, 50.0)) is False
        assert world.is_position_valid(Position(105.0, 50.0)) is False
        assert world.is_position_valid(Position(50.0, -5.0)) is False
        assert world.is_position_valid(Position(50.0, 105.0)) is False
    
    def test_random_valid_position(self):
        world = World(width=100.0, height=100.0)
        
        position = world.get_random_valid_position()
        
        assert world.is_position_valid(position) is True
        assert 0 <= position.x <= 100.0
        assert 0 <= position.y <= 100.0
    
    def test_world_update(self):
        world = World(width=100.0, height=100.0)
        agent = WandererAgent(position=Position(50.0, 50.0))
        world.add_agent(agent)
        
        initial_time = world.time
        events = world.update(dt=0.1)
        
        assert world.time > initial_time
        assert isinstance(events, list)
    
    def test_world_reset(self):
        world = World(width=100.0, height=100.0)
        agent = WandererAgent(position=Position(50.0, 50.0))
        world.add_agent(agent)
        
        world.time = 100.0
        world.reset()
        
        assert len(world.agents) == 0
        assert world.time == 0.0
        assert world.total_agents_created == 0
        assert world.total_agents_removed == 0
    
    def test_world_info_query(self):
        world = World(width=100.0, height=100.0)
        agent = WandererAgent(position=Position(55.0, 55.0))
        world.add_agent(agent)
        
        info = world.get_world_info(Position(50.0, 50.0), radius=20.0)
        
        assert "agents" in info
        assert "features" in info
        assert "environment" in info
        assert len(info["agents"]) >= 1  # Should find our agent
    
    def test_world_statistics(self):
        world = World(width=100.0, height=100.0)
        agent = WandererAgent(position=Position(50.0, 50.0))
        world.add_agent(agent)
        
        stats = world.get_statistics()
        
        assert "world_size" in stats
        assert "simulation_time" in stats
        assert "agents" in stats
        assert "features" in stats
        assert "environment" in stats
        assert stats["agents"]["active"] == 1