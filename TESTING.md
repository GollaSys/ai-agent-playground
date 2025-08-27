# Testing Guide for AI Agent Playground

This guide provides detailed instructions for testing the AI Agent Playground project locally.

## 🧪 Test Setup

### 1. Prerequisites

Ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### 2. Environment Setup

```bash
# Navigate to the ai-agent-playground directory
cd ai-agent-playground

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov pytest-mock black flake8 mypy

# Install the package in development mode
pip install -e .
```

## 🚀 Quick Testing

### Run All Tests
```bash
# Basic test run
pytest

# Verbose output
pytest -v

# With coverage report
pytest --cov=src/ai_agent_playground --cov-report=html --cov-report=term-missing
```

### Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only  
pytest -m integration

# Skip slow tests
pytest -m "not slow"

# Test specific modules
pytest tests/test_core.py
pytest tests/test_agents.py
pytest tests/test_environment.py
pytest tests/test_utils.py
```

## 🔍 Detailed Testing Instructions

### 1. Core Functionality Tests

Test the fundamental simulation components:

```bash
# Test core agent and engine functionality
pytest tests/test_core.py -v

# Expected: All agent creation, movement, and engine tests pass
```

**Key Test Areas:**
- Agent creation and initialization
- Position calculations and movement
- Event system functionality
- Simulation engine lifecycle
- Configuration management

### 2. Agent Behavior Tests

Test different agent types and their behaviors:

```bash
# Test agent types and behaviors
pytest tests/test_agents.py -v
```

**Key Test Areas:**
- Autonomous agent decision making
- Reactive agent threat response
- Wanderer agent exploration
- Behavior execution and energy management
- Agent memory and learning

### 3. Environment Tests

Test world simulation and physics:

```bash
# Test environment and physics systems
pytest tests/test_environment.py -v
```

**Key Test Areas:**
- Spatial grid partitioning
- Physics collision detection
- World boundary handling
- Environmental feature placement
- Agent-environment interactions

### 4. Utility Tests

Test metrics, logging, and visualization components:

```bash
# Test utility functions
pytest tests/test_utils.py -v
```

**Key Test Areas:**
- Metrics collection and export
- Logging configuration
- Visualization data export
- Performance measurement

## 🎮 Manual Testing Scenarios

### Scenario 1: Basic Simulation Test

```bash
# Test basic simulation functionality
python examples/basic_simulation.py
```

**Expected Behavior:**
- Simulation window opens with moving agents
- Different colored agents (blue=autonomous, red=reactive, green=wanderer)
- Agents avoid obstacles and interact with each other
- Simulation runs for 500 steps and completes
- Metrics file is generated

### Scenario 2: Headless Performance Test

```bash
# Test large-scale headless simulation
python examples/headless_simulation.py
```

**Expected Behavior:**
- Console output shows progress every 200 steps
- System metrics are logged (if psutil available)
- Simulation completes with performance statistics
- Output files are created in ./output directory
- No visualization window opens

### Scenario 3: CLI Interface Test

```bash
# Test command line interface
ai-agent-playground demo --agents 20 --steps 100

# Test configuration creation
ai-agent-playground create-config --output test_config.json

# Test running from config
ai-agent-playground run-config --config-file configs/default.json
```

**Expected Behavior:**
- Demo runs with visual simulation
- Configuration file is created successfully
- Simulation runs according to config parameters

### Scenario 4: Agent Type Testing

```bash
# Test different agent distributions
ai-agent-playground run --agents 30 --agent-types "autonomous:10,reactive:10,wanderer:10" --steps 200 --visualize
```

**Expected Behavior:**
- Equal numbers of each agent type
- Distinct behavioral patterns visible
- Autonomous agents show complex movement
- Reactive agents flee from threats
- Wanderer agents move randomly

### Scenario 5: Metrics and Output Testing

```bash
# Test metrics collection
ai-agent-playground run --agents 50 --steps 500 --save-metrics --output-dir ./test_output
```

**Expected Behavior:**
- Simulation runs to completion
- Metrics JSON file created in test_output directory
- File contains performance data and statistics

## 🛠 Code Quality Tests

### Style and Format Testing

```bash
# Check code formatting
black --check src/ tests/ examples/

# Run linting
flake8 src/ tests/ examples/

# Type checking
mypy src/ai_agent_playground/ --ignore-missing-imports
```

### Performance Testing

```bash
# Run performance benchmarks
pytest tests/test_performance.py -v --benchmark-only
```

## 🐛 Debugging Failed Tests

### Common Issues and Solutions

#### 1. Import Errors
```bash
# If you see "ModuleNotFoundError"
pip install -e .
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

#### 2. Visualization Tests Failing
```bash
# Install GUI dependencies
pip install matplotlib[gui]

# Or skip visualization tests
pytest -k "not visualization"
```

#### 3. Permission Errors
```bash
# On Windows, run as administrator
# On Unix systems:
sudo pytest  # Not recommended, fix permissions instead
chmod +x examples/*.py
```

#### 4. Memory Issues
```bash
# Reduce test parameters
pytest tests/test_core.py::TestSimulatorEngine::test_simulation_run_short
```

### Debug Mode Testing

```bash
# Run with debug output
pytest --log-cli-level=DEBUG tests/test_core.py

# Run single test with full output
pytest tests/test_core.py::TestAgent::test_agent_creation -v -s
```

## 📊 Coverage Analysis

### Generate Coverage Reports

```bash
# HTML coverage report
pytest --cov=src/ai_agent_playground --cov-report=html
# Open htmlcov/index.html in browser

# Terminal coverage report
pytest --cov=src/ai_agent_playground --cov-report=term-missing

# Coverage with branch analysis
pytest --cov=src/ai_agent_playground --cov-branch --cov-report=html
```

### Coverage Targets
- **Minimum acceptable coverage**: 80%
- **Target coverage**: 90%+
- **Critical paths**: 100% (core engine, agent lifecycle)

## 🚀 Performance Testing

### Benchmark Tests

```bash
# Basic performance benchmark
python -m pytest tests/test_performance.py --benchmark-only --benchmark-sort=mean

# Memory usage testing
python -m memory_profiler examples/headless_simulation.py

# Time-based performance test
time python examples/headless_simulation.py
```

### Performance Targets
- **Small simulation** (50 agents, 1000 steps): < 30 seconds
- **Medium simulation** (200 agents, 2000 steps): < 120 seconds  
- **Large simulation** (500 agents, 5000 steps): < 300 seconds
- **Memory usage**: < 500MB for 1000 agents

## 🔄 Continuous Integration Testing

### Pre-commit Checks

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run all pre-commit checks
pre-commit run --all-files
```

### Full Test Suite

```bash
# Complete testing pipeline
./scripts/run_full_tests.sh

# Or manual equivalent:
black src/ tests/ examples/
flake8 src/ tests/ examples/
mypy src/ai_agent_playground/
pytest --cov=src/ai_agent_playground --cov-report=html --cov-fail-under=80
python examples/basic_simulation.py
python examples/headless_simulation.py
```

## 📝 Test Results Interpretation

### Successful Test Run
```
========================= test session starts ==========================
collected 45 items

tests/test_core.py ................ [100%]
tests/test_agents.py .............. [100%]
tests/test_environment.py ........ [100%]
tests/test_utils.py ............... [100%]

---------- coverage: platform darwin, python 3.9.7 -----------
Name                           Stmts   Miss  Cover   Missing
----------------------------------------------------------
src/ai_agent_playground/core/agent.py      125     8    94%   12-15, 89
src/ai_agent_playground/core/engine.py     180    12    93%   45-48, 156-159
src/ai_agent_playground/core/events.py      95     5    95%   78-82
...
----------------------------------------------------------
TOTAL                            1245    67    95%

========================= 45 passed in 12.34s ==========================
```

### Failed Test Analysis
- Check specific test failure messages
- Verify environment setup
- Check for missing dependencies
- Review recent code changes

## 🆘 Troubleshooting

### Environment Issues
```bash
# Reset virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
pip install -e .
```

### Test Data Issues
```bash
# Clean test artifacts
rm -rf .pytest_cache
rm -rf htmlcov
rm -rf output
find . -name "*.pyc" -delete
find . -name "__pycache__" -delete
```

### Common Error Solutions

| Error | Solution |
|-------|----------|
| `ImportError: No module named 'ai_agent_playground'` | Run `pip install -e .` |
| `matplotlib backend error` | Set `export MPLBACKEND=Agg` |
| `Permission denied` | Check file permissions and ownership |
| `Memory error` | Reduce test parameters or increase system memory |
| `Timeout in visualization tests` | Skip visualization tests with `-k "not visualization"` |

## ✅ Test Checklist

Before submitting code:

- [ ] All unit tests pass
- [ ] Code coverage > 80%
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Manual testing scenarios work
- [ ] Performance within acceptable limits
- [ ] Documentation updated
- [ ] Examples still work

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Simulator API Documentation](./docs/api.md)

Happy Testing! 🧪✨