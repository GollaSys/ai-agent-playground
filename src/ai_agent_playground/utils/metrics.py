"""Metrics collection and monitoring for the simulator."""

import time
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import threading
from pathlib import Path


@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collects and manages simulation metrics."""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.start_time = datetime.now()
        self._lock = threading.Lock()
        
        # Performance tracking
        self.performance_timers: Dict[str, float] = {}
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric value."""
        with self._lock:
            metric = Metric(name, value, datetime.now(), tags or {})
            self.metrics[name].append(metric)
    
    def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            self.counters[name] += value
            self.record_metric(f"{name}_counter", self.counters[name], tags)
    
    def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric."""
        with self._lock:
            self.gauges[name] = value
            self.record_metric(f"{name}_gauge", value, tags)
    
    def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a value in a histogram."""
        with self._lock:
            self.histograms[name].append(value)
            # Keep only recent values
            if len(self.histograms[name]) > 1000:
                self.histograms[name] = self.histograms[name][-1000:]
            self.record_metric(f"{name}_histogram", value, tags)
    
    def start_timer(self, name: str) -> None:
        """Start a performance timer."""
        self.performance_timers[name] = time.time()
    
    def end_timer(self, name: str, record_histogram: bool = True) -> float:
        """End a performance timer and return duration."""
        if name not in self.performance_timers:
            return 0.0
        
        duration = time.time() - self.performance_timers[name]
        del self.performance_timers[name]
        
        if record_histogram:
            self.record_histogram(f"{name}_duration", duration)
        
        return duration
    
    def get_metric_history(self, name: str, limit: Optional[int] = None) -> List[Metric]:
        """Get history of a specific metric."""
        with self._lock:
            if name not in self.metrics:
                return []
            
            history = list(self.metrics[name])
            if limit:
                history = history[-limit:]
            return history
    
    def get_counter_value(self, name: str) -> float:
        """Get current counter value."""
        return self.counters.get(name, 0.0)
    
    def get_gauge_value(self, name: str) -> float:
        """Get current gauge value."""
        return self.gauges.get(name, 0.0)
    
    def get_histogram_stats(self, name: str) -> Dict[str, float]:
        """Get statistics for a histogram."""
        if name not in self.histograms or not self.histograms[name]:
            return {}
        
        values = self.histograms[name]
        values.sort()
        
        n = len(values)
        return {
            "count": n,
            "min": values[0],
            "max": values[-1],
            "mean": sum(values) / n,
            "median": values[n // 2],
            "p95": values[int(n * 0.95)] if n > 0 else 0.0,
            "p99": values[int(n * 0.99)] if n > 0 else 0.0
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        with self._lock:
            uptime = datetime.now() - self.start_time
            
            summary = {
                "uptime_seconds": uptime.total_seconds(),
                "metrics_count": sum(len(deque) for deque in self.metrics.values()),
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {
                    name: self.get_histogram_stats(name)
                    for name in self.histograms.keys()
                },
                "last_update": datetime.now().isoformat()
            }
            
            return summary
    
    def export_to_json(self, filepath: str) -> None:
        """Export metrics to JSON file."""
        summary = self.get_summary()
        
        # Add recent metric history
        recent_metrics = {}
        for name, metric_deque in self.metrics.items():
            recent_metrics[name] = [
                {
                    "value": m.value,
                    "timestamp": m.timestamp.isoformat(),
                    "tags": m.tags
                }
                for m in list(metric_deque)[-100:]  # Last 100 points
            ]
        
        summary["recent_metrics"] = recent_metrics
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self.metrics.clear()
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.performance_timers.clear()
            self.start_time = datetime.now()
    
    def get_rate(self, counter_name: str, window_seconds: int = 60) -> float:
        """Get the rate of change for a counter over a time window."""
        if counter_name not in self.metrics:
            return 0.0
        
        now = datetime.now()
        cutoff_time = now - timedelta(seconds=window_seconds)
        
        recent_metrics = [
            m for m in self.metrics[counter_name]
            if m.timestamp >= cutoff_time
        ]
        
        if len(recent_metrics) < 2:
            return 0.0
        
        # Calculate rate based on first and last values in window
        oldest = recent_metrics[0]
        newest = recent_metrics[-1]
        
        time_diff = (newest.timestamp - oldest.timestamp).total_seconds()
        value_diff = newest.value - oldest.value
        
        if time_diff > 0:
            return value_diff / time_diff
        
        return 0.0
    
    def log_system_metrics(self) -> None:
        """Log system metrics like memory usage, CPU, etc."""
        try:
            import psutil
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.set_gauge("system_cpu_percent", cpu_percent)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.set_gauge("system_memory_percent", memory.percent)
            self.set_gauge("system_memory_available_mb", memory.available / (1024 * 1024))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.set_gauge("system_disk_percent", disk.percent)
            
        except ImportError:
            # psutil not available, skip system metrics
            pass