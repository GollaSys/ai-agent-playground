"""
AI Agent Simulator Package

A comprehensive simulation framework for AI agents with environment interaction,
behavior modeling, and performance analysis capabilities.
"""

__version__ = "1.0.0"
__author__ = "AI Simulator Team"

from .core.engine import SimulatorEngine
from .core.agent import Agent
from .environment.world import World
from .cli.main import main

__all__ = ["SimulatorEngine", "Agent", "World", "main"]