# AI Agent Playground

A comprehensive AI agent playground framework with environment interaction, behavior modeling, and performance analysis capabilities.

## 🚀 Features

- **Multiple Agent Types**: Autonomous, reactive, and wanderer agents with distinct behaviors
- **Physics Simulation**: Collision detection, forces, and realistic movement
- **Dynamic Environment**: Obstacles, resources, weather simulation, and spatial partitioning
- **Real-time Visualization**: Interactive matplotlib-based visualization with trails and metrics
- **Comprehensive Metrics**: Performance tracking, system monitoring, and data export
- **Event System**: Publisher-subscriber pattern for agent interactions
- **CLI Interface**: Easy-to-use command line interface with multiple simulation modes
- **Extensible Architecture**: Modular design for easy customization and extension

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Quick Installation

1. **Clone or download the project**:
   ```bash
   cd ai-agent-playground
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the package in development mode**:
   ```bash
   pip install -e .
   ```

### Alternative Installation

You can also install using pip directly:
```bash
pip install -e .
```

## 🎮 Quick Start

### 1. Run a Demo

Get started quickly with a demo simulation:

```bash
ai-agent-playground demo --agents 20 --steps 200
```

This will create a visual simulation with 20 agents running for 200 steps.

### 2. Basic Simulation

Run a basic simulation with custom parameters:

```bash
ai-agent-playground run --agents 50 --steps 1000 --world-size 800 --visualize
```

### 3. Headless Simulation (Performance)

For larger simulations without visualization:

```bash
ai-agent-playground run --agents 200 --steps 5000 --save-metrics --output-dir ./results
```

### 4. Configuration File

Create a configuration template:

```bash
ai-agent-playground create-config --output my_config.json
```

Run with configuration:

```bash
ai-agent-playground run-config --config-file my_config.json
```

## 🔧 Usage Examples

### Command Line Interface

The playground provides several CLI commands:

#### Basic Run Command
```bash
# Run with mixed agent types
ai-agent-playground run \
  --agents 100 \
  --steps 2000 \
  --world-size 1200 \
  --agent-types "autonomous:40,reactive:35,wanderer:25" \
  --visualize \
  --save-metrics \
  --output-dir ./simulation_results
```

#### Demo Mode
```bash
# Quick demonstration
ai-agent-playground demo --agents 30 --world-size 600 --steps 150
```

#### Configuration Mode
```bash
# Create configuration template
ai-agent-playground create-config --output large_simulation.json

# Run from configuration
ai-agent-playground run-config --config-file large_simulation.json
```

#### Get Information
```bash
# Display playground capabilities
ai-agent-playground info
```

### Programmatic Usage

#### Basic Simulation

```python
from ai_agent_playground.core.engine import SimulatorEngine, SimulationConfig
from ai_agent_playground.core.agent import Position
from ai_agent_playground.agents.types import AgentType
from ai_agent_playground.utils.visualization import Visualizer

# Create simulation configuration
config = SimulationConfig(
    time_step=0.1,
    max_steps=500,
    world_width=800,
    world_height=600,
    enable_physics=True
)

# Create playground engine
engine = SimulatorEngine(config)

# Add agents
for i in range(30):
    position = engine.world.get_random_valid_position()
    if i < 15:
        agent = AgentType.create_autonomous_agent(position=position)
    elif i < 25:
        agent = AgentType.create_reactive_agent(position=position)
    else:
        agent = AgentType.create_wanderer_agent(position=position)
    
    engine.add_agent(agent)

# Set up visualization
visualizer = Visualizer(engine.world)
visualizer.show_trails = True

# Run simulation
engine.run()

# Display results
print(f"Simulation completed: {len(engine.agents)} agents remaining")
```

#### Headless Simulation with Metrics

```python
from ai_agent_playground.core.engine import SimulatorEngine, SimulationConfig
from ai_agent_playground.agents.types import AgentType
import time

# Large-scale headless simulation
config = SimulationConfig(
    time_step=0.05,
    max_steps=3000,
    world_width=1500,
    world_height=1200,
    enable_visualization=False,  # Headless
    max_agents=300
)

engine = SimulatorEngine(config)

# Create many agents
for i in range(200):
    position = engine.world.get_random_valid_position()
    agent_type = ["autonomous", "reactive", "wanderer"][i % 3]
    
    if agent_type == "autonomous":
        agent = AgentType.create_autonomous_agent(position=position)
    elif agent_type == "reactive":
        agent = AgentType.create_reactive_agent(position=position)
    else:
        agent = AgentType.create_wanderer_agent(position=position)
    
    engine.add_agent(agent)

# Add progress monitoring
def monitor_progress(simulator):
    if simulator.current_step % 300 == 0:
        print(f"Step {simulator.current_step}: {len(simulator.agents)} agents active")

engine.add_callback("step_end", monitor_progress)

# Run simulation
start_time = time.time()
engine.run()
duration = time.time() - start_time

print(f"Simulation completed in {duration:.2f} seconds")
print(f"Performance: {engine.current_step / duration:.1f} steps/second")

# Export metrics
engine.metrics.export_to_json("simulation_metrics.json")
```

## 🎯 Agent Types

### Autonomous Agents
- Complex decision-making with goal-oriented behavior
- Learning and adaptation capabilities
- High intelligence and adaptability attributes
- Energy: 120 units (enhanced)

### Reactive Agents
- Fast response to immediate stimuli and threats
- High sensitivity to nearby agents
- Quick reaction times with energy bursts
- Energy: 80 units (standard)

### Wanderer Agents
- Simple random movement patterns
- Curiosity-driven exploration
- Basic energy management
- Energy: 100 units (standard)

## 🌍 Environment Features

### World Simulation
- **Boundaries**: Agents bounce off world edges
- **Obstacles**: Static barriers that block movement
- **Resources**: Energy sources for agent sustenance
- **Weather**: Temperature, humidity, and wind simulation
- **Spatial Partitioning**: Efficient neighbor queries using grid system

### Physics Engine
- **Collision Detection**: Agent-agent and agent-boundary collisions
- **Forces**: Gravity, wind, and custom force application
- **Movement**: Velocity-based movement with friction
- **Realistic Interactions**: Energy costs for movement and collisions

## 📊 Metrics and Monitoring

The playground provides comprehensive metrics:

### Performance Metrics
- Steps per second execution rate
- Memory usage and system resources
- Agent lifecycle statistics
- Physics simulation performance

### Simulation Metrics
- Agent population over time
- Energy distribution statistics
- Spatial distribution patterns
- Event frequency analysis

### Export Formats
- JSON metrics export
- Visualization dashboards
- CSV data export
- Real-time monitoring

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Simulation Parameters
DEFAULT_WORLD_SIZE=1000
DEFAULT_AGENT_COUNT=100
DEFAULT_SIMULATION_STEPS=1000

# Performance Settings
MAX_THREADS=4
ENABLE_GPU=false

# Visualization
ENABLE_VISUALIZATION=true
VISUALIZATION_FPS=30

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/playground.log
```

### Configuration Files

JSON configuration for complex setups:

```json
{
  "simulation": {
    "time_step": 0.1,
    "max_steps": 2000,
    "world_width": 1200.0,
    "world_height": 900.0,
    "enable_physics": true,
    "max_agents": 500
  },
  "agents": {
    "autonomous": 50,
    "reactive": 30,
    "wanderer": 20
  },
  "output": {
    "save_metrics": true,
    "output_directory": "./results",
    "metrics_interval": 50
  }
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src/ai_agent_playground --cov-report=html

# Run specific test categories
pytest -m "not slow"  # Skip slow tests
pytest tests/test_core.py  # Test specific module
```

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Multi-component interaction testing
- **Performance Tests**: Benchmark and stress testing

## 🔧 Development

### Project Structure

```
ai-agent-playground/
├── src/ai-agent-playground/           # Main package
│   ├── core/               # Core simulation engine
│   ├── agents/             # Agent types and behaviors
│   ├── environment/        # World and physics simulation
│   ├── utils/              # Utilities and helpers
│   └── cli/                # Command line interface
├── tests/                  # Test suite
├── examples/               # Example scripts
├── configs/                # Configuration templates
├── docs/                   # Documentation
├── requirements.txt        # Dependencies
├── pyproject.toml         # Build configuration
└── README.md              # This file
```

### Adding New Agent Types

1. Create a new agent class inheriting from `Agent`:
```python
from ai_agent_playground.core.agent import Agent

class MyCustomAgent(Agent):
    def decide_action(self, observations):
        # Custom decision logic
        return {"action": "move", "dx": 1.0, "dy": 0.0}
    
    def update(self, dt, observations):
        # Custom update logic
        action = self.decide_action(observations)
        if action.get("action") == "move":
            self.move(action["dx"], action["dy"])
```

2. Register in the agent type factory:
```python
# In agents/types.py
@staticmethod
def create_custom_agent(position=None):
    return MyCustomAgent(position=position)
```

### Custom Behaviors

Create new behaviors by inheriting from `BaseBehavior`:

```python
from ai_agent_playground.agents.behaviors import BaseBehavior

class MyCustomBehavior(BaseBehavior):
    def execute(self, agent, observations):
        # Custom behavior logic
        return {
            "action": "custom_action",
            "dx": 2.0,
            "dy": 1.0,
            "energy_cost": 0.2
        }
```

## 📈 Performance Optimization

### For Large Simulations
- Use headless mode (`enable_visualization=False`)
- Increase spatial grid cell size for sparse simulations
- Adjust `time_step` for performance vs. accuracy trade-off
- Monitor system resources with built-in metrics

### Memory Optimization
- Limit agent memory size (default: 1000 items)
- Reduce event history retention
- Use appropriate world size for agent count

### CPU Optimization
- Consider multi-threading for independent operations
- Profile with built-in performance metrics
- Optimize agent decision-making algorithms

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Add docstrings for public methods
- Maintain test coverage above 80%

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Python and scientific computing libraries
- Visualization powered by matplotlib
- CLI interface using Click and Rich
- Logging with Loguru
- Testing with pytest

## 📞 Support

- **Documentation**: Check the `docs/` directory for detailed guides
- **Examples**: See `examples/` for usage patterns
- **Issues**: Report bugs and request features via GitHub issues
- **Configuration**: Use provided templates in `configs/`

## 🚀 What's Next?

- Multi-agent communication protocols
- Machine learning integration for agent behavior
- 3D visualization support
- Distributed simulation capabilities
- Web-based dashboard interface
- Plugin system for custom extensions

---

**Happy Simulating! 🤖✨**