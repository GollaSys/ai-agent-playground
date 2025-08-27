"""Spatial data structures for efficient agent queries."""

from typing import List, Dict, Set, Tuple, Optional
import math
from collections import defaultdict

from ..core.agent import Agent, Position


class SpatialGrid:
    """Grid-based spatial partitioning for efficient neighbor queries."""
    
    def __init__(self, width: float, height: float, cell_size: float = 50.0):
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.cols = max(1, int(math.ceil(width / cell_size)))
        self.rows = max(1, int(math.ceil(height / cell_size)))
        
        # Grid cells contain sets of agent IDs
        self.grid: Dict[Tuple[int, int], Set[str]] = defaultdict(set)
        
        # Track agent positions for easy updates
        self.agent_positions: Dict[str, Tuple[int, int]] = {}
    
    def _get_cell_coords(self, position: Position) -> Tuple[int, int]:
        """Get grid cell coordinates for a position."""
        col = max(0, min(self.cols - 1, int(position.x / self.cell_size)))
        row = max(0, min(self.rows - 1, int(position.y / self.cell_size)))
        return col, row
    
    def add_agent(self, agent: Agent) -> None:
        """Add an agent to the spatial grid."""
        cell_coords = self._get_cell_coords(agent.state.position)
        self.grid[cell_coords].add(agent.agent_id)
        self.agent_positions[agent.agent_id] = cell_coords
    
    def remove_agent(self, agent_id: str) -> None:
        """Remove an agent from the spatial grid."""
        if agent_id in self.agent_positions:
            old_coords = self.agent_positions[agent_id]
            self.grid[old_coords].discard(agent_id)
            del self.agent_positions[agent_id]
    
    def update_agent(self, agent: Agent) -> None:
        """Update an agent's position in the spatial grid."""
        new_coords = self._get_cell_coords(agent.state.position)
        
        if agent.agent_id in self.agent_positions:
            old_coords = self.agent_positions[agent.agent_id]
            
            if old_coords != new_coords:
                # Agent moved to a different cell
                self.grid[old_coords].discard(agent.agent_id)
                self.grid[new_coords].add(agent.agent_id)
                self.agent_positions[agent.agent_id] = new_coords
        else:
            # New agent
            self.add_agent(agent)
    
    def get_nearby_agents(
        self, 
        position: Position, 
        radius: float,
        exclude_id: Optional[str] = None
    ) -> List[str]:
        """Get agent IDs within radius of a position."""
        nearby_agents = []
        
        # Calculate which cells to check
        cell_radius = math.ceil(radius / self.cell_size)
        center_col, center_row = self._get_cell_coords(position)
        
        for row in range(
            max(0, center_row - cell_radius),
            min(self.rows, center_row + cell_radius + 1)
        ):
            for col in range(
                max(0, center_col - cell_radius),
                min(self.cols, center_col + cell_radius + 1)
            ):
                cell_agents = self.grid.get((col, row), set())
                nearby_agents.extend(cell_agents)
        
        # Filter by actual distance and exclude self
        result = []
        for agent_id in nearby_agents:
            if agent_id == exclude_id:
                continue
            result.append(agent_id)
        
        return result
    
    def get_agents_in_region(
        self, 
        min_x: float, 
        min_y: float, 
        max_x: float, 
        max_y: float
    ) -> List[str]:
        """Get all agents in a rectangular region."""
        min_col = max(0, int(min_x / self.cell_size))
        max_col = min(self.cols - 1, int(max_x / self.cell_size))
        min_row = max(0, int(min_y / self.cell_size))
        max_row = min(self.rows - 1, int(max_y / self.cell_size))
        
        agents = []
        for row in range(min_row, max_row + 1):
            for col in range(min_col, max_col + 1):
                cell_agents = self.grid.get((col, row), set())
                agents.extend(cell_agents)
        
        return list(set(agents))  # Remove duplicates
    
    def clear(self) -> None:
        """Clear the spatial grid."""
        self.grid.clear()
        self.agent_positions.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the spatial grid."""
        total_agents = sum(len(agents) for agents in self.grid.values())
        occupied_cells = len([cell for cell in self.grid.values() if cell])
        
        return {
            "total_agents": total_agents,
            "occupied_cells": occupied_cells,
            "total_cells": self.cols * self.rows,
            "occupancy_rate": occupied_cells / (self.cols * self.rows) if self.cols * self.rows > 0 else 0
        }