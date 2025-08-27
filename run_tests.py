#!/usr/bin/env python3
"""
Test runner script for AI Agent Playground
Runs comprehensive tests and demonstrates functionality
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def run_command(command, description, timeout=60):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent
        )
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ SUCCESS ({duration:.2f}s)")
            if result.stdout:
                print("Output:")
                print(result.stdout)
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            print("Error output:")
            print(result.stderr)
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ TIMEOUT after {timeout} seconds")
        return False
    except Exception as e:
        print(f"💥 EXCEPTION: {e}")
        return False
    
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        'pytest', 'numpy', 'matplotlib', 'click', 'rich', 
        'loguru', 'pydantic', 'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies satisfied")
    return True


def main():
    """Main test runner."""
    print("🤖 AI Agent Simulator - Test Runner")
    print("This script will run comprehensive tests and examples\n")
    
    # Check if we're in the right directory
    if not Path("src/ai_agent_playground").exists():
        print("❌ Error: Run this script from the ai-agent-playground root directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        sys.exit(1)
    
    # Test results tracking
    tests_passed = 0
    tests_total = 0
    
    # Define test suite
    test_suite = [
        {
            "command": [sys.executable, "-m", "pytest", "tests/", "-v"],
            "description": "Running Unit Tests",
            "timeout": 120
        },
        {
            "command": [sys.executable, "-m", "pytest", "tests/", "--cov=src/ai_agent_playground", "--cov-report=term-missing"],
            "description": "Running Coverage Analysis",
            "timeout": 120
        },
        {
            "command": [sys.executable, "-c", "import ai_agent_playground; print('✅ Package import successful')"],
            "description": "Testing Package Import",
            "timeout": 10
        },
        {
            "command": [sys.executable, "-m", "ai_agent_playground.cli.main", "info"],
            "description": "Testing CLI Info Command",
            "timeout": 10
        },
        {
            "command": [sys.executable, "-m", "ai_agent_playground.cli.main", "create-config", "--output", "test_config.json"],
            "description": "Testing Configuration Creation",
            "timeout": 10
        },
        {
            "command": [sys.executable, "examples/headless_simulation.py"],
            "description": "Testing Headless Simulation Example",
            "timeout": 60
        }
    ]
    
    # Run all tests
    for test in test_suite:
        tests_total += 1
        if run_command(test["command"], test["description"], test.get("timeout", 60)):
            tests_passed += 1
        else:
            print("⚠️  Continuing with remaining tests...")
    
    # Clean up test files
    cleanup_files = ["test_config.json", "basic_simulation_metrics.json"]
    for file in cleanup_files:
        if Path(file).exists():
            Path(file).unlink()
            print(f"🧹 Cleaned up {file}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    print(f"Success rate: {tests_passed/tests_total*100:.1f}%")
    
    if tests_passed == tests_total:
        print("🎉 ALL TESTS PASSED! The simulator is working correctly.")
        
        # Run interactive demo if all tests pass
        response = input("\nWould you like to run an interactive demo? (y/N): ")
        if response.lower() == 'y':
            print("\n🎮 Starting interactive demo...")
            demo_cmd = [sys.executable, "-m", "ai_agent_playground.cli.main", "demo", 
                       "--agents", "20", "--steps", "100", "--world-size", "400"]
            subprocess.run(demo_cmd)
        
        return 0
    else:
        print(f"❌ {tests_total - tests_passed} tests failed. Please check the error messages above.")
        return 1


def run_manual_test():
    """Run a manual test to verify basic functionality."""
    print("\n🔧 Running manual functionality test...")
    
    try:
        # Test core imports
        from simulator.core.engine import SimulatorEngine, SimulationConfig
        from simulator.core.agent import Position
        from simulator.agents.types import AgentType
        
        print("  ✅ Core imports successful")
        
        # Create a minimal simulation
        config = SimulationConfig(
            time_step=0.1,
            max_steps=10,
            world_width=100,
            world_height=100,
            enable_visualization=False
        )
        
        engine = SimulatorEngine(config)
        print("  ✅ Engine creation successful")
        
        # Add an agent
        agent = AgentType.create_wanderer_agent(position=Position(50, 50))
        engine.add_agent(agent)
        print("  ✅ Agent creation successful")
        
        # Run a few steps
        for _ in range(5):
            engine.step()
        
        print(f"  ✅ Simulation steps successful (completed {engine.current_step} steps)")
        print("  ✅ Manual test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Manual test failed: {e}")
        return False


if __name__ == "__main__":
    try:
        # First run manual test
        if not run_manual_test():
            print("❌ Manual test failed. Exiting.")
            sys.exit(1)
        
        # Then run full test suite
        exit_code = main()
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test runner interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)