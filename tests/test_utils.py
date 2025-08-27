"""Tests for utility modules."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from ai_agent_playground.utils.metrics import MetricsCollector, Metric
from ai_agent_playground.utils.logging_config import setup_logging
from ai_agent_playground.utils.visualization import Visualizer
from ai_agent_playground.environment.world import World


class TestMetricsCollector:
    """Tests for metrics collection."""
    
    def test_metrics_collector_creation(self):
        collector = MetricsCollector(max_history=1000)
        
        assert collector.max_history == 1000
        assert len(collector.metrics) == 0
        assert len(collector.counters) == 0
        assert len(collector.gauges) == 0
    
    def test_metric_recording(self):
        collector = MetricsCollector()
        
        collector.record_metric("test_metric", 42.5)
        
        assert "test_metric" in collector.metrics
        assert len(collector.metrics["test_metric"]) == 1
        
        metric = collector.metrics["test_metric"][0]
        assert metric.name == "test_metric"
        assert metric.value == 42.5
        assert metric.timestamp is not None
    
    def test_counter_operations(self):
        collector = MetricsCollector()
        
        collector.increment_counter("test_counter", 5.0)
        collector.increment_counter("test_counter", 3.0)
        
        assert collector.get_counter_value("test_counter") == 8.0
        assert "test_counter_counter" in collector.metrics
    
    def test_gauge_operations(self):
        collector = MetricsCollector()
        
        collector.set_gauge("test_gauge", 25.5)
        collector.set_gauge("test_gauge", 30.0)  # Update value
        
        assert collector.get_gauge_value("test_gauge") == 30.0
        assert "test_gauge_gauge" in collector.metrics
    
    def test_histogram_operations(self):
        collector = MetricsCollector()
        
        # Record multiple values
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 5.0, 5.0]
        for value in values:
            collector.record_histogram("test_histogram", value)
        
        stats = collector.get_histogram_stats("test_histogram")
        
        assert stats["count"] == 7
        assert stats["min"] == 1.0
        assert stats["max"] == 5.0
        assert stats["mean"] == 25.0 / 7  # Sum of values / count
        assert stats["median"] == 4.0  # Middle value when sorted
    
    def test_timer_operations(self):
        collector = MetricsCollector()
        
        collector.start_timer("test_timer")
        
        # Simulate some time passage
        import time
        time.sleep(0.01)
        
        duration = collector.end_timer("test_timer")
        
        assert duration > 0
        assert "test_timer_duration" in collector.metrics
    
    def test_metric_history_retrieval(self):
        collector = MetricsCollector()
        
        # Record several metrics
        for i in range(10):
            collector.record_metric("test_metric", float(i))
        
        # Get all history
        history = collector.get_metric_history("test_metric")
        assert len(history) == 10
        
        # Get limited history
        limited_history = collector.get_metric_history("test_metric", limit=5)
        assert len(limited_history) == 5
        assert limited_history[-1].value == 9.0  # Should be the last 5 values
    
    def test_metrics_summary(self):
        collector = MetricsCollector()
        
        collector.record_metric("test_metric", 42.0)
        collector.increment_counter("test_counter", 10.0)
        collector.set_gauge("test_gauge", 25.0)
        collector.record_histogram("test_histogram", 5.0)
        
        summary = collector.get_summary()
        
        assert "uptime_seconds" in summary
        assert "metrics_count" in summary
        assert "counters" in summary
        assert "gauges" in summary
        assert "histograms" in summary
        assert summary["counters"]["test_counter"] == 10.0
        assert summary["gauges"]["test_gauge"] == 25.0
    
    def test_metrics_export(self):
        collector = MetricsCollector()
        
        collector.record_metric("test_metric", 42.0)
        collector.increment_counter("test_counter", 10.0)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            collector.export_to_json(temp_file)
            
            # Verify file was created and contains expected data
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            assert "counters" in data
            assert "recent_metrics" in data
            assert data["counters"]["test_counter"] == 10.0
            
        finally:
            Path(temp_file).unlink()
    
    def test_metrics_reset(self):
        collector = MetricsCollector()
        
        collector.record_metric("test_metric", 42.0)
        collector.increment_counter("test_counter", 10.0)
        collector.set_gauge("test_gauge", 25.0)
        
        collector.reset()
        
        assert len(collector.metrics) == 0
        assert len(collector.counters) == 0
        assert len(collector.gauges) == 0
        assert len(collector.histograms) == 0
    
    def test_rate_calculation(self):
        collector = MetricsCollector()
        
        # Record counter values over time (simulated)
        import time
        start_time = time.time()
        
        collector.increment_counter("requests", 10)
        time.sleep(0.05)  # Small delay
        collector.increment_counter("requests", 20)
        
        rate = collector.get_rate("requests_counter", window_seconds=1)
        
        # Rate should be positive (requests per second)
        assert rate >= 0


class TestLoggingConfig:
    """Tests for logging configuration."""
    
    def test_setup_logging_basic(self):
        logger = setup_logging(name="test_logger", level="DEBUG", enable_console=False)
        
        assert logger is not None
        # Note: More extensive logging tests would require log capture
    
    def test_setup_logging_with_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            temp_log_file = f.name
        
        try:
            logger = setup_logging(
                name="test_logger",
                level="INFO",
                log_file=temp_log_file,
                enable_console=False
            )
            
            logger.info("Test message")
            
            # Verify log file was created
            assert Path(temp_log_file).exists()
            
        finally:
            if Path(temp_log_file).exists():
                Path(temp_log_file).unlink()
    
    @patch.dict('os.environ', {'LOG_LEVEL': 'WARNING', 'LOG_FORMAT': 'simple'})
    def test_configure_from_env(self):
        from simulator.utils.logging_config import configure_from_env
        
        logger = configure_from_env()
        assert logger is not None


class TestVisualizer:
    """Tests for visualization components."""
    
    def test_visualizer_creation(self):
        world = World(width=100.0, height=100.0)
        visualizer = Visualizer(world, figsize=(10, 8))
        
        assert visualizer.world == world
        assert visualizer.figsize == (10, 8)
        assert visualizer.fig is None  # Not set up yet
        assert visualizer.show_trails is False
        assert visualizer.show_vision is False
    
    def test_visualizer_agent_colors(self):
        world = World(width=100.0, height=100.0)
        visualizer = Visualizer(world)
        
        assert "AutonomousAgent" in visualizer.agent_colors
        assert "ReactiveAgent" in visualizer.agent_colors
        assert "WandererAgent" in visualizer.agent_colors
        assert "default" in visualizer.agent_colors
    
    def test_visualizer_toggle_features(self):
        world = World(width=100.0, height=100.0)
        visualizer = Visualizer(world)
        
        # Test trail toggle
        initial_trails = visualizer.show_trails
        visualizer.toggle_trails()
        assert visualizer.show_trails == (not initial_trails)
        
        # Test vision toggle
        initial_vision = visualizer.show_vision
        visualizer.toggle_vision()
        assert visualizer.show_vision == (not initial_vision)
    
    def test_export_simulation_data(self):
        world = World(width=100.0, height=100.0)
        visualizer = Visualizer(world)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            visualizer.export_simulation_data(temp_file)
            
            # Verify file was created and contains expected data
            with open(temp_file, 'r') as f:
                data = json.load(f)
            
            assert "timestamp" in data
            assert "world_stats" in data
            assert "agents" in data
            assert "features" in data
            
        finally:
            Path(temp_file).unlink()
    
    @patch('matplotlib.pyplot.subplots')
    def test_metrics_dashboard_creation(self, mock_subplots):
        # Mock matplotlib to avoid GUI dependencies in tests
        mock_fig = Mock()
        mock_axes = [[Mock(), Mock()], [Mock(), Mock()]]
        mock_subplots.return_value = (mock_fig, mock_axes)
        
        world = World(width=100.0, height=100.0)
        visualizer = Visualizer(world)
        metrics = MetricsCollector()
        
        # Add some test metrics
        metrics.record_metric("active_agents", 10)
        metrics.record_histogram("step_duration", 0.1)
        
        # This should not raise an exception
        visualizer.create_metrics_dashboard(metrics)
        
        # Verify matplotlib was called
        mock_subplots.assert_called_once()
    
    def test_visualizer_close(self):
        world = World(width=100.0, height=100.0)
        visualizer = Visualizer(world)
        
        # This should not raise an exception
        visualizer.close()


class TestUtilityIntegration:
    """Integration tests for utility components."""
    
    def test_metrics_and_logging_integration(self):
        # Set up logging
        logger = setup_logging(name="test", level="INFO", enable_console=False)
        
        # Set up metrics
        collector = MetricsCollector()
        collector.record_metric("integration_test", 1.0)
        
        # Both should work together without issues
        summary = collector.get_summary()
        assert summary["metrics_count"] == 1
    
    def test_visualization_and_metrics_integration(self):
        world = World(width=100.0, height=100.0)
        visualizer = Visualizer(world)
        metrics = MetricsCollector()
        
        # Add some metrics
        for i in range(10):
            metrics.record_metric("test_metric", float(i))
        
        # Export both visualization and metrics data
        with tempfile.TemporaryDirectory() as temp_dir:
            viz_file = Path(temp_dir) / "viz_data.json"
            metrics_file = Path(temp_dir) / "metrics_data.json"
            
            visualizer.export_simulation_data(str(viz_file))
            metrics.export_to_json(str(metrics_file))
            
            # Both files should exist and be valid JSON
            assert viz_file.exists()
            assert metrics_file.exists()
            
            with open(viz_file) as f:
                viz_data = json.load(f)
            
            with open(metrics_file) as f:
                metrics_data = json.load(f)
            
            assert "world_stats" in viz_data
            assert "metrics_count" in metrics_data