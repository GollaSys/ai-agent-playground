#!/usr/bin/env python3
"""Example of running a headless simulation with metrics collection."""

import time
import random
from pathlib import Path

from ai_agent_playground.core.engine import SimulatorEngine, SimulationConfig
from ai_agent_playground.core.agent import Position
from ai_agent_playground.agents.types import AgentType
from ai_agent_playground.utils.metrics import MetricsCollector


def main():
    """Run a headless simulation focused on performance and metrics."""
    print("🤖 Headless AI Agent Simulation")
    print("=" * 40)
    
    # Configuration for a larger simulation
    config = SimulationConfig(
        time_step=0.05,  # Smaller time step for more precision
        max_steps=2000,
        world_width=1500,
        world_height=1200,
        enable_physics=True,
        enable_visualization=False,  # Headless
        max_agents=200
    )
    
    # Create simulator
    engine = SimulatorEngine(config)
    
    # Create a large number of agents
    print(f"Creating {config.max_agents} agents...")
    
    agent_distribution = {
        'autonomous': 80,
        'reactive': 70,
        'wanderer': 50
    }
    
    total_agents = 0
    for agent_type, count in agent_distribution.items():
        print(f"  Creating {count} {agent_type} agents...")
        
        for _ in range(count):
            position = engine.world.get_random_valid_position()
            
            if agent_type == 'autonomous':
                agent = AgentType.create_autonomous_agent(position=position)
            elif agent_type == 'reactive':
                agent = AgentType.create_reactive_agent(position=position)
            else:
                agent = AgentType.create_wanderer_agent(position=position)
            
            engine.add_agent(agent)
            total_agents += 1
    
    print(f"✓ Created {total_agents} agents")
    
    # Add performance monitoring
    def monitor_performance(simulator):
        if simulator.current_step % 200 == 0:
            progress = (simulator.current_step / config.max_steps) * 100
            active_agents = len(simulator.agents)
            
            print(f"Step {simulator.current_step:4d}/{config.max_steps} "
                  f"({progress:5.1f}%) - Agents: {active_agents:3d}")
            
            # Log system metrics if available
            simulator.metrics.log_system_metrics()
    
    engine.add_callback("step_end", monitor_performance)
    
    # Add event logging
    def log_major_events(simulator):
        if simulator.current_step % 500 == 0:
            world_stats = simulator.world.get_statistics()
            print(f"  World stats: Temp={world_stats['environment']['temperature']:.1f}°C, "
                  f"Wind={world_stats['environment']['wind_speed']:.1f}m/s")
    
    engine.add_callback("step_end", log_major_events)
    
    # Run simulation
    print(f"\n🚀 Starting simulation ({config.max_steps} steps)...")
    start_time = time.time()
    
    try:
        engine.run()
    except KeyboardInterrupt:
        print("\n⏹️  Simulation interrupted by user")
        engine.stop()
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Results analysis
    print("\n" + "=" * 40)
    print("📊 SIMULATION RESULTS")
    print("=" * 40)
    
    status = engine.get_status()
    world_stats = engine.world.get_statistics()
    metrics_summary = engine.metrics.get_summary()
    
    print(f"Execution time:     {duration:.2f} seconds")
    print(f"Steps completed:    {status['step']}/{config.max_steps}")
    print(f"Simulation time:    {status['simulation_time']:.2f}s")
    print(f"Steps per second:   {status['step'] / duration:.1f}")
    print(f"Agents remaining:   {status['agent_count']}")
    print(f"Agents created:     {world_stats['agents']['total_created']}")
    print(f"Agents removed:     {world_stats['agents']['total_removed']}")
    print(f"Survival rate:      {(status['agent_count'] / world_stats['agents']['total_created']) * 100:.1f}%")
    
    # Performance metrics
    step_duration_stats = engine.metrics.get_histogram_stats("step_duration")
    if step_duration_stats:
        print(f"\nPerformance metrics:")
        print(f"  Avg step duration: {step_duration_stats.get('mean', 0):.4f}s")
        print(f"  Min step duration: {step_duration_stats.get('min', 0):.4f}s")
        print(f"  Max step duration: {step_duration_stats.get('max', 0):.4f}s")
        print(f"  95th percentile:   {step_duration_stats.get('p95', 0):.4f}s")
    
    # Save detailed results
    output_dir = Path("./output")
    output_dir.mkdir(exist_ok=True)
    
    # Export metrics
    metrics_file = output_dir / f"headless_simulation_{total_agents}agents_{config.max_steps}steps.json"
    engine.metrics.export_to_json(str(metrics_file))
    print(f"\n💾 Metrics saved to: {metrics_file}")
    
    # Save world state
    world_file = output_dir / f"final_world_state_{total_agents}agents.json"
    from simulator.utils.visualization import Visualizer
    temp_viz = Visualizer(engine.world)
    temp_viz.export_simulation_data(str(world_file))
    print(f"💾 World state saved to: {world_file}")
    
    print("\n✅ Simulation completed successfully!")


if __name__ == "__main__":
    main()