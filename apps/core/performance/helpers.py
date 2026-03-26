"""
Performance Testing Helpers
Task 070: Performance Testing Utilities
"""

import time
import statistics
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class PerformanceMetrics:
    """Container for performance metrics"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """Calculate error rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.failed_requests / self.total_requests) * 100

    @property
    def avg_response_time(self) -> float:
        """Calculate average response time"""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def min_response_time(self) -> float:
        """Get minimum response time"""
        if not self.response_times:
            return 0.0
        return min(self.response_times)

    @property
    def max_response_time(self) -> float:
        """Get maximum response time"""
        if not self.response_times:
            return 0.0
        return max(self.response_times)

    def get_percentile(self, percentile: float) -> float:
        """Calculate percentile of response times"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]

    @property
    def p50(self) -> float:
        """Get 50th percentile (median)"""
        return self.get_percentile(50)

    @property
    def p95(self) -> float:
        """Get 95th percentile"""
        return self.get_percentile(95)

    @property
    def p99(self) -> float:
        """Get 99th percentile"""
        return self.get_percentile(99)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': self.success_rate,
            'error_rate': self.error_rate,
            'avg_response_time_ms': round(self.avg_response_time * 1000, 2),
            'min_response_time_ms': round(self.min_response_time * 1000, 2),
            'max_response_time_ms': round(self.max_response_time * 1000, 2),
            'p50_ms': round(self.p50 * 1000, 2),
            'p95_ms': round(self.p95 * 1000, 2),
            'p99_ms': round(self.p99 * 1000, 2),
        }

    def check_sla(self, p95_threshold_ms: int = 500, p99_threshold_ms: int = 1000,
                  error_rate_threshold: float = 1.0) -> Dict[str, Any]:
        """Check metrics against SLA thresholds"""
        p95_pass = self.p95 * 1000 <= p95_threshold_ms
        p99_pass = self.p99 * 1000 <= p99_threshold_ms
        error_rate_pass = self.error_rate <= error_rate_threshold

        return {
            'p95_pass': p95_pass,
            'p95_threshold_ms': p95_threshold_ms,
            'p95_actual_ms': round(self.p95 * 1000, 2),
            'p99_pass': p99_pass,
            'p99_threshold_ms': p99_threshold_ms,
            'p99_actual_ms': round(self.p99 * 1000, 2),
            'error_rate_pass': error_rate_pass,
            'error_rate_threshold': error_rate_threshold,
            'error_rate_actual': round(self.error_rate, 2),
            'overall_pass': p95_pass and p99_pass and error_rate_pass,
        }


class Timer:
    """Simple timer for measuring response times"""

    def __init__(self):
        self.start_time: Optional[float] = None
        self.elapsed: Optional[float] = None

    def start(self):
        """Start the timer"""
        self.start_time = time.perf_counter()
        self.elapsed = None

    def stop(self) -> float:
        """Stop the timer and return elapsed time"""
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        self.elapsed = time.perf_counter() - self.start_time
        return self.elapsed

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def calculate_percentile(values: List[float], percentile: float) -> float:
    """Calculate percentile of a list of values"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = int(len(sorted_values) * percentile / 100)
    return sorted_values[min(index, len(sorted_values) - 1)]


@contextmanager
def measure_response_time(metrics: PerformanceMetrics):
    """Context manager for measuring response time"""
    timer = Timer()
    timer.start()
    try:
        yield timer
        metrics.successful_requests += 1
    except Exception as e:
        metrics.failed_requests += 1
        metrics.errors.append(str(e))
        raise
    finally:
        elapsed = timer.stop()
        metrics.response_times.append(elapsed)
        metrics.total_requests += 1
