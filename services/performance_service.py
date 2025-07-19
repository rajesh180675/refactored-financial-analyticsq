import time
import threading
import logging
import numpy as np
from typing import Dict, Any, List
from collections import defaultdict, deque
from datetime import datetime
from contextlib import contextmanager


class PerformanceService:
    def __init__(self, config_manager, state_manager, event_system):
        self.config = config_manager
        self.state = state_manager
        self.events = event_system
        self.logger = logging.getLogger(__name__)
        
        self.metrics = defaultdict(list)
        self.api_metrics = defaultdict(lambda: {
            'requests': 0,
            'successes': 0,
            'failures': 0,
            'total_time': 0,
            'response_times': deque(maxlen=100)
        })
        self._lock = threading.Lock()

    @contextmanager
    def measure(self, operation: str):
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            yield
        finally:
            elapsed_time = time.time() - start_time
            memory_delta = self._get_memory_usage() - start_memory
            
            with self._lock:
                self.metrics[operation].append({
                    'duration': elapsed_time,
                    'memory_delta': memory_delta,
                    'timestamp': datetime.now()
                })
            
            if elapsed_time > 1.0:
                self.logger.warning(f"Slow operation '{operation}': {elapsed_time:.2f}s")
            
            self.events.publish("performance_metric_recorded", {
                'operation': operation,
                'duration': elapsed_time,
                'memory_delta': memory_delta
            }, "PerformanceService")

    def track_api_call(self, endpoint: str, success: bool, duration: float, error: str = None):
        with self._lock:
            metrics = self.api_metrics[endpoint]
            metrics['requests'] += 1
            
            if success:
                metrics['successes'] += 1
            else:
                metrics['failures'] += 1
            
            metrics['total_time'] += duration
            metrics['response_times'].append(duration)
            
            if not success and error:
                self.logger.error(f"API call to {endpoint} failed: {error}")

    def _get_memory_usage(self) -> int:
        try:
            import psutil
            return psutil.Process().memory_info().rss
        except:
            return 0

    def get_performance_summary(self) -> Dict[str, Any]:
        with self._lock:
            summary = {}
            
            for operation, measurements in self.metrics.items():
                if measurements:
                    durations = [m['duration'] for m in measurements]
                    summary[operation] = {
                        'avg_duration': sum(durations) / len(durations),
                        'max_duration': max(durations),
                        'min_duration': min(durations),
                        'total_calls': len(measurements),
                        'total_time': sum(durations)
                    }
            
            return summary

    def get_api_summary(self) -> Dict[str, Any]:
        with self._lock:
            summary = {}
            
            for endpoint, metrics in self.api_metrics.items():
                if metrics['requests'] > 0:
                    response_times = list(metrics['response_times'])
                    summary[endpoint] = {
                        'total_requests': metrics['requests'],
                        'success_rate': metrics['successes'] / metrics['requests'],
                        'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
                        'p95_response_time': np.percentile(response_times, 95) if response_times else 0
                    }
            
            return summary

    def clear_metrics(self):
        with self._lock:
            self.metrics.clear()
            self.api_metrics.clear()
