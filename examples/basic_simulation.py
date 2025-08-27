#!/usr/bin/env python3
"""Basic simulation example."""

import random
from ai_agent_playground.core.engine import SimulatorEngine, SimulationConfig
from ai_agent_playground.core.agent import Position
from ai_agent_playground.agents.types import AgentType
from ai_agent_playground.utils.visualization import Visualizer

def main():
    """Run a basic simulation example."""
    # Create simulation configuration
    config = SimulationConfig(
        time_step=0.1,
        max_steps=500,
        world_width=800,
        world_height=600,
        enable_physics=True,
        enable_visualization=True
    )
    
    # Create simulator
    engine = SimulatorEngine(config)
    
    # Add various types of agents
    print("Creating agents...")
    
    # Autonomous agents (complex behavior)
    for _ in range(15):
        position = Position(random.uniform(50, 750), random.uniform(50, 550))
        agent = AgentType.create_autonomous_agent(position=position)
        engine.add_agent(agent)
    
    # Reactive agents (fast response)
    for _ in range(10):
        position = Position(random.uniform(50, 750), random.uniform(50, 550))
        agent = AgentType.create_reactive_agent(position=position)
        engine.add_agent(agent)
    
    # Wanderer agents (simple movement)
    for _ in range(5):
        position = Position(random.uniform(50, 750), random.uniform(50, 550))
        agent = AgentType.create_wanderer_agent(position=position)
        engine.add_agent(agent)
    
    print(f"Created {len(engine.agents)} agents")
    
    # Set up visualization
    visualizer = Visualizer(engine.world)
    visualizer.show_trails = True
    visualizer.show_vision = True
    
    # Add some callbacks for monitoring
    def on_step_end(simulator):
        if simulator.current_step % 50 == 0:
            print(f"Step {simulator.current_step}: {len(simulator.agents)} agents active")
    
    engine.add_callback("step_end", on_step_end)
    
    # Run simulation with visualization
    print("Starting simulation...")
    
    import threading
    
    def run_simulation():
        engine.run()
    
    # Start simulation in separate thread
    sim_thread = threading.Thread(target=run_simulation)
    sim_thread.daemon = True
    sim_thread.start()
    
    # Start visualization
    try:
        visualizer.animate(interval=50)
    except KeyboardInterrupt:
        print("Simulation interrupted")
        engine.stop()
    
    # Wait for simulation to complete
    sim_thread.join()
    
    # Display final results
    print("\nSimulation completed!")
    print(f"Final step: {engine.current_step}")
    print(f"Agents remaining: {len(engine.agents)}")
    print(f"Simulation time: {engine.simulation_time:.2f}s")
    
    # Save metrics
    engine.metrics.export_to_json("basic_simulation_metrics.json")
    print("Metrics saved to basic_simulation_metrics.json")
    
    # Clean up
    visualizer.close()


if __name__ == "__main__":
    main()