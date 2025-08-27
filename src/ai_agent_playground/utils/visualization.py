"""Visualization tools for the simulator."""

from typing import Dict, List, Optional, Tuple, Any
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
import numpy as np
from pathlib import Path
import json
from collections import deque

from ..core.agent import Agent, Position
from ..environment.world import World
from .metrics import MetricsCollector


class Visualizer:
    """Handles visualization of the simulation."""
    
    def __init__(self, world: World, figsize: Tuple[int, int] = (12, 8)):
        self.world = world
        self.figsize = figsize
        
        # Matplotlib setup
        self.fig = None
        self.ax = None
        self.agent_scatter = None
        self.feature_patches = []
        
        # Animation
        self.animation = None
        self.frame_count = 0
        
        # Colors for different agent types
        self.agent_colors = {
            "AutonomousAgent": "blue",
            "ReactiveAgent": "red", 
            "WandererAgent": "green",
            "default": "black"
        }
        
        # Visualization settings
        self.show_trails = False
        self.trail_length = 50
        self.agent_trails = {}
        
        self.show_vision = False
        self.vision_radius = 50.0
    
    def setup_plot(self) -> None:
        """Set up the matplotlib plot."""
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        self.ax.set_xlim(0, self.world.width)
        self.ax.set_ylim(0, self.world.height)
        self.ax.set_aspect('equal')
        self.ax.set_title('AI Agent Simulation')
        self.ax.set_xlabel('X Position')
        self.ax.set_ylabel('Y Position')
        
        # Set up background grid
        self.ax.grid(True, alpha=0.3)
        
        # Draw environmental features
        self._draw_features()
    
    def _draw_features(self) -> None:
        """Draw environmental features on the plot."""
        for feature in self.world.features:
            if not feature.active:
                continue
            
            if feature.feature_type == "obstacle":
                color = "gray"
                alpha = 0.7
            elif feature.feature_type == "resource":
                color = "gold"
                alpha = 0.5
            else:
                color = "purple"
                alpha = 0.3
            
            circle = patches.Circle(
                (feature.position.x, feature.position.y),
                feature.radius,
                color=color,
                alpha=alpha
            )
            self.ax.add_patch(circle)
            self.feature_patches.append(circle)
    
    def update_plot(self) -> None:
        """Update the plot with current agent positions."""
        if not self.fig:
            self.setup_plot()
        
        # Clear previous agent scatter
        if self.agent_scatter:
            self.agent_scatter.remove()
        
        # Clear vision circles if shown
        if self.show_vision:
            for patch in self.ax.patches:
                if hasattr(patch, '_vision_circle'):
                    patch.remove()
        
        if not self.world.agents:
            return
        
        # Get agent positions and colors
        positions = []
        colors = []
        sizes = []
        
        for agent in self.world.agents.values():
            positions.append([agent.state.position.x, agent.state.position.y])
            
            # Color based on agent type
            agent_type = agent.__class__.__name__
            color = self.agent_colors.get(agent_type, self.agent_colors["default"])
            
            # Modify color based on agent state
            if agent.state.energy < 30:
                color = "orange"  # Low energy
            if agent.state.health < 50:
                color = "darkred"  # Low health
                
            colors.append(color)
            
            # Size based on energy/health
            base_size = 30
            energy_factor = agent.state.energy / 100.0
            size = base_size * (0.5 + 0.5 * energy_factor)
            sizes.append(size)
            
            # Update trails
            if self.show_trails:
                if agent.agent_id not in self.agent_trails:
                    self.agent_trails[agent.agent_id] = deque(maxlen=self.trail_length)
                
                self.agent_trails[agent.agent_id].append(
                    (agent.state.position.x, agent.state.position.y)
                )
            
            # Draw vision radius
            if self.show_vision:
                vision_circle = patches.Circle(
                    (agent.state.position.x, agent.state.position.y),
                    self.vision_radius,
                    fill=False,
                    edgecolor=color,
                    alpha=0.3,
                    linestyle='--'
                )
                vision_circle._vision_circle = True
                self.ax.add_patch(vision_circle)
        
        if positions:
            positions = np.array(positions)
            self.agent_scatter = self.ax.scatter(
                positions[:, 0], 
                positions[:, 1],
                c=colors,
                s=sizes,
                alpha=0.8,
                edgecolors='black',
                linewidth=0.5
            )
        
        # Draw trails
        if self.show_trails:
            for agent_id, trail in self.agent_trails.items():
                if len(trail) > 1:
                    trail_array = np.array(list(trail))
                    self.ax.plot(
                        trail_array[:, 0], 
                        trail_array[:, 1],
                        alpha=0.3,
                        linewidth=1,
                        color=self.agent_colors.get("default", "gray")
                    )
        
        # Update title with simulation info
        agent_count = len(self.world.agents)
        sim_time = self.world.time
        self.ax.set_title(f'AI Agent Simulation - Agents: {agent_count}, Time: {sim_time:.1f}s')
        
        plt.draw()
    
    def save_frame(self, filename: str) -> None:
        """Save current frame to file."""
        if self.fig:
            filepath = Path(filename)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            self.fig.savefig(filename, dpi=150, bbox_inches='tight')
    
    def animate(self, interval: int = 100) -> None:
        """Start animation of the simulation."""
        if not self.fig:
            self.setup_plot()
        
        def update_frame(frame):
            self.frame_count = frame
            self.update_plot()
            return self.agent_scatter,
        
        self.animation = FuncAnimation(
            self.fig, 
            update_frame, 
            interval=interval,
            blit=False,
            repeat=True
        )
        
        plt.show()
    
    def stop_animation(self) -> None:
        """Stop the animation."""
        if self.animation:
            self.animation.event_source.stop()
    
    def toggle_trails(self) -> None:
        """Toggle agent trails on/off."""
        self.show_trails = not self.show_trails
        if not self.show_trails:
            self.agent_trails.clear()
    
    def toggle_vision(self) -> None:
        """Toggle vision radius display on/off."""
        self.show_vision = not self.show_vision
    
    def create_metrics_dashboard(self, metrics: MetricsCollector, save_path: Optional[str] = None) -> None:
        """Create a dashboard of metrics."""
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Simulation Metrics Dashboard')
        
        # Agent count over time
        agent_count_history = metrics.get_metric_history("active_agents")
        if agent_count_history:
            times = [m.timestamp for m in agent_count_history]
            values = [m.value for m in agent_count_history]
            axes[0, 0].plot(times, values)
            axes[0, 0].set_title('Active Agents Over Time')
            axes[0, 0].set_ylabel('Agent Count')
        
        # Step duration histogram
        duration_stats = metrics.get_histogram_stats("step_duration")
        if duration_stats:
            axes[0, 1].bar(duration_stats.keys(), duration_stats.values())
            axes[0, 1].set_title('Step Duration Statistics')
            axes[0, 1].set_ylabel('Value')
        
        # Simulation performance
        sim_step_history = metrics.get_metric_history("simulation_step")
        if sim_step_history:
            times = [m.timestamp for m in sim_step_history]
            steps = [m.value for m in sim_step_history]
            axes[1, 0].plot(times, steps)
            axes[1, 0].set_title('Simulation Progress')
            axes[1, 0].set_ylabel('Step Number')
        
        # Resource usage (if available)
        memory_history = metrics.get_metric_history("system_memory_percent_gauge")
        cpu_history = metrics.get_metric_history("system_cpu_percent_gauge")
        
        if memory_history or cpu_history:
            if memory_history:
                times = [m.timestamp for m in memory_history]
                values = [m.value for m in memory_history]
                axes[1, 1].plot(times, values, label='Memory %')
            
            if cpu_history:
                times = [m.timestamp for m in cpu_history]
                values = [m.value for m in cpu_history]
                axes[1, 1].plot(times, values, label='CPU %')
            
            axes[1, 1].set_title('System Resource Usage')
            axes[1, 1].set_ylabel('Usage %')
            axes[1, 1].legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.show()
    
    def export_simulation_data(self, filepath: str) -> None:
        """Export current simulation state to JSON."""
        data = {
            "timestamp": self.world.time,
            "world_stats": self.world.get_statistics(),
            "agents": [agent.to_dict() for agent in self.world.agents.values()],
            "features": [
                {
                    "type": feature.feature_type,
                    "position": {"x": feature.position.x, "y": feature.position.y},
                    "radius": feature.radius,
                    "active": feature.active,
                    "properties": feature.properties
                }
                for feature in self.world.features
            ]
        }
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def close(self) -> None:
        """Close the visualization."""
        if self.animation:
            self.animation.event_source.stop()
        
        if self.fig:
            plt.close(self.fig)