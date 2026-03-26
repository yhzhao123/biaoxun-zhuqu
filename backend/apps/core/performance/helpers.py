"""
Performance Test Helper Functions
Utilities for performance testing including timing, measurement, and data generation.
"""

import time
import random
import string
import statistics
from contextlib import contextmanager
from typing import List, Dict, Any, Callable
from dataclasses import dataclass, field


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    response_times: List[float] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    status_codes: List[int] = field(default_factory=list)

    def add_response(self, response_time: float, status_code: int, error: str = None):
        """Add a response measurement."""
        self.response_times.append(response_time)
        self.status_codes.append(status_code)
        if error:
            self.errors.append(error)

    def calculate_percentile(self, percentile: float) -> float:
        """Calculate percentile of response times."""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * percentile / 100)
        return sorted_times[min(index, len(sorted_times) - 1)]

    @property
    def p50(self) -> float:
        """Median response time."""
        return self.calculate_percentile(50)

    @property
    def p95(self) -> float:
        """95th percentile response time."""
        return self.calculate_percentile(95)

    @property
    def p99(self) -> float:
        """99th percentile response time."""
        return self.calculate_percentile(99)

    @property
    def mean(self) -> float:
        """Mean response time."""
        if not self.response_times:
            return 0.0
        return statistics.mean(self.response_times)

    @property
    def error_rate(self) -> float:
        """Error rate percentage."""
        if not self.status_codes:
            return 0.0
        errors = sum(1 for code in self.status_codes if code >= 400)
        return (errors / len(self.status_codes)) * 100

    @property
    def total_requests(self) -> int:
        """Total number of requests."""
        return len(self.response_times)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'p50': round(self.p50, 2),
            'p95': round(self.p95, 2),
            'p99': round(self.p99, 2),
            'mean': round(self.mean, 2),
            'error_rate': round(self.error_rate, 2),
            'total_requests': self.total_requests,
        }


@contextmanager
def measure_time():
    """Context manager to measure execution time in milliseconds."""
    start = time.perf_counter()
    yield lambda: (time.perf_counter() - start) * 1000


def generate_random_string(length: int = 10) -> str:
    """Generate a random string for test data."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_test_tender_data(count: int = 10) -> List[Dict[str, Any]]:
    """Generate test tender data."""
    tenders = []
    statuses = ['pending', 'published', 'awarded', 'closed']
    categories = ['工程', '货物', '服务', '采购']

    for i in range(count):
        tenders.append({
            'title': f'测试招标项目_{generate_random_string(8)}',
            'tender_no': f'T{time.time():.0f}{i:04d}',
            'status': random.choice(statuses),
            'category': random.choice(categories),
            'budget': random.randint(100000, 10000000),
            'published_at': '2024-01-15T10:00:00Z',
            'deadline': '2024-02-15T10:00:00Z',
        })
    return tenders


class RateLimiter:
    """Simple rate limiter for controlling request rate."""

    def __init__(self, max_per_second: int):
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second
        self.last_request = 0

    def wait(self):
        """Wait if necessary to respect rate limit."""
        current_time = time.perf_counter()
        elapsed = current_time - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.perf_counter()


def run_concurrent_requests(
    request_func: Callable,
    num_requests: int,
    max_concurrent: int = 10
) -> PerformanceMetrics:
    """Run multiple concurrent requests and collect metrics.

    Args:
        request_func: Function that makes a single request and returns (response_time, status_code, error)
        num_requests: Total number of requests to make
        max_concurrent: Maximum concurrent requests

    Returns:
        PerformanceMetrics object with collected data
    """
    import threading
    from queue import Queue

    metrics = PerformanceMetrics()
    queue = Queue()
    threads = []
    semaphore = threading.Semaphore(max_concurrent)

    def worker():
        with semaphore:
            try:
                response_time, status_code, error = request_func()
                metrics.add_response(response_time, status_code, error)
            except Exception as e:
                metrics.add_response(0, 500, str(e))

    # Create threads
    for _ in range(num_requests):
        t = threading.Thread(target=worker)
        threads.append(t)

    # Start all threads
    for t in threads:
        t.start()

    # Wait for completion
    for t in threads:
        t.join()

    return metrics


def calculate_throughput(total_requests: int, duration: float) -> float:
    """Calculate throughput in requests per second."""
    if duration <= 0:
        return 0.0
    return total_requests / duration


def calculate_average_response_time(response_times: List[float]) -> float:
    """Calculate average response time."""
    if not response_times:
        return 0.0
    return statistics.mean(response_times)


def check_performance_threshold(
    metrics: PerformanceMetrics,
    threshold_p95: float,
    threshold_p99: float,
    threshold_error_rate: float
) -> Dict[str, bool]:
    """Check if metrics meet performance thresholds.

    Returns:
        Dictionary with pass/fail for each threshold
    """
    return {
        'p95_pass': metrics.p95 <= threshold_p95,
        'p99_pass': metrics.p99 <= threshold_p99,
        'error_rate_pass': metrics.error_rate <= threshold_error_rate,
    }