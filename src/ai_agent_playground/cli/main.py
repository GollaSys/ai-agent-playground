"""Main CLI interface for the AI Agent Playground."""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
import random

import click
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel
from dotenv import load_dotenv

from ..core.engine import SimulatorEngine, SimulationConfig
from ..core.agent import Position
from ..agents.types import AgentType
from ..utils.logging_config import setup_logging
from ..utils.metrics import MetricsCollector
from ..utils.visualization import Visualizer

# Load environment variables
load_dotenv()

console = Console()
logger = setup_logging(__name__)


@click.group()
@click.option('--config-file', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.option('--log-level', '-l', default='INFO', help='Logging level')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, config_file, log_level, verbose):
    """AI Agent Simulator - A comprehensive simulation framework."""
    ctx.ensure_object(dict)
    
    # Set up logging
    if verbose:
        log_level = 'DEBUG'
    
    ctx.obj['logger'] = setup_logging(level=log_level.upper())
    ctx.obj['config_file'] = config_file
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--agents', '-a', default=50, help='Number of agents to create')
@click.option('--steps', '-s', default=1000, help='Number of simulation steps')
@click.option('--world-size', '-w', default=1000, help='World size (width=height)')
@click.option('--time-step', '-t', default=0.1, help='Time step for simulation')
@click.option('--visualize', is_flag=True, help='Enable visualization')
@click.option('--save-metrics', is_flag=True, help='Save metrics to file')
@click.option('--output-dir', '-o', default='./output', help='Output directory')
@click.option('--agent-types', default='autonomous:30,reactive:15,wanderer:5', 
              help='Agent types and counts (type:count,type:count,...)')
@click.pass_context
def run(ctx, agents, steps, world_size, time_step, visualize, save_metrics, output_dir, agent_types):
    """Run a simulation with the specified parameters."""
    logger = ctx.obj['logger']
    
    console.print(Panel.fit("🤖 Starting AI Agent Simulation", style="bold blue"))
    
    # Parse agent types
    agent_type_config = _parse_agent_types(agent_types)
    total_requested = sum(agent_type_config.values())
    
    if total_requested != agents:
        console.print(f"[yellow]Warning: Requested {total_requested} agents via types, but {agents} specified. Using {total_requested}.[/yellow]")
        agents = total_requested
    
    # Create simulation config
    config = SimulationConfig(
        time_step=time_step,
        max_steps=steps,
        world_width=world_size,
        world_height=world_size,
        enable_visualization=visualize
    )
    
    # Create simulator
    engine = SimulatorEngine(config)
    
    # Add agents
    console.print(f"[green]Creating {agents} agents...[/green]")
    _create_agents(engine, agent_type_config)
    
    # Set up visualization if requested
    visualizer = None
    if visualize:
        visualizer = Visualizer(engine.world)
        console.print("[blue]Visualization enabled[/blue]")
    
    # Set up metrics saving
    if save_metrics:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        console.print(f"[green]Metrics will be saved to: {output_path}[/green]")
    
    # Add callbacks for progress tracking
    def on_step_end(simulator):
        if simulator.current_step % 100 == 0:
            progress = (simulator.current_step / config.max_steps) * 100
            console.print(f"Progress: {simulator.current_step}/{config.max_steps} ({progress:.1f}%)")
    
    engine.add_callback("step_end", on_step_end)
    
    try:
        # Run simulation
        console.print("[bold green]🚀 Starting simulation...[/bold green]")
        
        if visualize and visualizer:
            # Run with visualization in separate thread
            import threading
            
            def run_simulation():
                engine.run()
            
            sim_thread = threading.Thread(target=run_simulation)
            sim_thread.daemon = True
            sim_thread.start()
            
            # Start visualization
            visualizer.animate(interval=50)
            
            sim_thread.join()
        else:
            # Run simulation with progress bar
            engine.run()
        
        # Display results
        _display_results(engine, console)
        
        # Save metrics if requested
        if save_metrics:
            metrics_file = output_path / f"metrics_{agents}agents_{steps}steps.json"
            engine.metrics.export_to_json(str(metrics_file))
            console.print(f"[green]Metrics saved to: {metrics_file}[/green]")
            
            # Create metrics dashboard
            if visualize:
                dashboard_file = output_path / f"dashboard_{agents}agents_{steps}steps.png"
                visualizer.create_metrics_dashboard(engine.metrics, str(dashboard_file))
        
    except KeyboardInterrupt:
        console.print("[red]Simulation interrupted by user[/red]")
        engine.stop()
    except Exception as e:
        console.print(f"[red]Simulation error: {e}[/red]")
        logger.error(f"Simulation error: {e}")
        sys.exit(1)
    finally:
        if visualizer:
            visualizer.close()


@cli.command()
@click.option('--agents', '-a', default=10, help='Number of agents to create')
@click.option('--world-size', '-w', default=500, help='World size')
@click.option('--steps', '-s', default=100, help='Number of steps to run')
@click.pass_context
def demo(ctx, agents, world_size, steps):
    """Run a quick demo of the simulator."""
    console.print(Panel.fit("🎮 Running Simulator Demo", style="bold magenta"))
    
    # Simple demo configuration
    config = SimulationConfig(
        time_step=0.1,
        max_steps=steps,
        world_width=world_size,
        world_height=world_size,
        enable_visualization=True
    )
    
    engine = SimulatorEngine(config)
    
    # Create mixed agent types for demo
    agent_types = {
        'autonomous': agents // 2,
        'reactive': agents // 3,
        'wanderer': agents - (agents // 2) - (agents // 3)
    }
    
    _create_agents(engine, agent_types)
    
    console.print(f"[green]Demo: {agents} agents in {world_size}x{world_size} world for {steps} steps[/green]")
    
    # Run demo
    visualizer = Visualizer(engine.world)
    
    import threading
    def run_demo():
        engine.run()
    
    demo_thread = threading.Thread(target=run_demo)
    demo_thread.daemon = True
    demo_thread.start()
    
    visualizer.animate(interval=100)
    demo_thread.join()
    
    _display_results(engine, console)
    visualizer.close()


@cli.command()
@click.option('--config-file', '-c', required=True, type=click.Path(exists=True), 
              help='JSON configuration file')
@click.pass_context
def run_config(ctx, config_file):
    """Run simulation from a configuration file."""
    console.print(f"[blue]Loading configuration from: {config_file}[/blue]")
    
    try:
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Create simulation config
        sim_config = SimulationConfig(**config_data.get('simulation', {}))
        engine = SimulatorEngine(sim_config)
        
        # Create agents from config
        agent_config = config_data.get('agents', {'autonomous': 10})
        _create_agents(engine, agent_config)
        
        # Run simulation
        console.print("[green]Starting simulation from config...[/green]")
        engine.run()
        
        _display_results(engine, console)
        
    except Exception as e:
        console.print(f"[red]Error loading config: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--output', '-o', default='./config_template.json', help='Output file path')
def create_config(output):
    """Create a template configuration file."""
    template = {
        "simulation": {
            "time_step": 0.1,
            "max_steps": 1000,
            "world_width": 1000.0,
            "world_height": 1000.0,
            "enable_physics": True,
            "enable_visualization": False,
            "max_agents": 1000
        },
        "agents": {
            "autonomous": 30,
            "reactive": 15,
            "wanderer": 5
        },
        "output": {
            "save_metrics": True,
            "output_directory": "./output",
            "save_visualization": False
        }
    }
    
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(template, f, indent=2)
    
    console.print(f"[green]Configuration template created: {output}[/green]")


@cli.command()
def info():
    """Display information about the simulator."""
    console.print(Panel.fit("🤖 AI Agent Simulator Information", style="bold cyan"))
    
    info_table = Table(title="Simulator Features")
    info_table.add_column("Feature", style="bold")
    info_table.add_column("Description")
    
    info_table.add_row("Agent Types", "Autonomous, Reactive, Wanderer")
    info_table.add_row("Physics", "Collision detection, forces, boundaries")
    info_table.add_row("Environment", "Obstacles, resources, weather")
    info_table.add_row("Visualization", "Real-time matplotlib animation")
    info_table.add_row("Metrics", "Performance tracking and analysis")
    info_table.add_row("Events", "Pub/sub event system")
    
    console.print(info_table)
    
    # Show available agent types
    console.print("\n[bold]Available Agent Types:[/bold]")
    console.print("• [blue]autonomous[/blue]: Complex decision-making with goals")
    console.print("• [red]reactive[/red]: Fast response to immediate stimuli")
    console.print("• [green]wanderer[/green]: Simple random movement")


def _parse_agent_types(agent_types_str: str) -> Dict[str, int]:
    """Parse agent types string into dictionary."""
    agent_types = {}
    
    if not agent_types_str:
        return {"autonomous": 10}
    
    try:
        for pair in agent_types_str.split(','):
            type_name, count_str = pair.split(':')
            agent_types[type_name.strip()] = int(count_str.strip())
    except ValueError as e:
        console.print(f"[red]Error parsing agent types: {e}[/red]")
        return {"autonomous": 10}
    
    return agent_types


def _create_agents(engine: SimulatorEngine, agent_types: Dict[str, int]) -> None:
    """Create agents based on type configuration."""
    for agent_type, count in track(agent_types.items(), description="Creating agents..."):
        for _ in range(count):
            # Get random valid position
            position = engine.world.get_random_valid_position()
            
            # Create agent based on type
            if agent_type == "autonomous":
                agent = AgentType.create_autonomous_agent(position=position)
            elif agent_type == "reactive":
                agent = AgentType.create_reactive_agent(position=position)
            elif agent_type == "wanderer":
                agent = AgentType.create_wanderer_agent(position=position)
            else:
                console.print(f"[yellow]Unknown agent type: {agent_type}, using autonomous[/yellow]")
                agent = AgentType.create_autonomous_agent(position=position)
            
            engine.add_agent(agent)


def _display_results(engine: SimulatorEngine, console: Console) -> None:
    """Display simulation results."""
    status = engine.get_status()
    world_stats = engine.world.get_statistics()
    
    # Create results table
    results_table = Table(title="Simulation Results")
    results_table.add_column("Metric", style="bold")
    results_table.add_column("Value")
    
    results_table.add_row("Total Steps", str(status["step"]))
    results_table.add_row("Simulation Time", f"{status['simulation_time']:.2f}s")
    results_table.add_row("Agents Remaining", str(status["agent_count"]))
    results_table.add_row("Agents Created", str(world_stats["agents"]["total_created"]))
    results_table.add_row("Agents Removed", str(world_stats["agents"]["total_removed"]))
    
    console.print(results_table)
    
    # Show metrics summary
    metrics_summary = engine.metrics.get_summary()
    if metrics_summary["metrics_count"] > 0:
        console.print(f"\n[bold]Metrics collected:[/bold] {metrics_summary['metrics_count']} data points")


def main() -> None:
    """Main entry point."""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()