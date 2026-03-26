"""
Load Test Tests
Tests for normal load conditions (100-200 concurrent users).
"""

import pytest
import time
import threading
from typing import List, Callable

from django.test import Client

from apps.core.performance.config import LOAD_TEST_CONFIG, API_THRESHOLDS
from apps.core.performance.helpers import (
    PerformanceMetrics,
    calculate_throughput,
    check_performance_threshold,
)


@pytest.mark.django_db
class TestLoadTest:
    """Load testing for normal user conditions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test client."""
        self.client = Client()
        self.metrics = PerformanceMetrics()

    def _simulate_user(self, endpoint: str, duration: int) -> None:
        """Simulate a single user making requests for a duration."""
        end_time = time.time() + duration

        while time.time() < end_time:
            start = time.perf_counter()
            try:
                response = self.client.get(endpoint)
                elapsed = (time.perf_counter() - start) * 1000
                self.metrics.add_response(elapsed, response.status_code)
            except Exception as e:
                self.metrics.add_response(0, 500, str(e))

            # Random think time between requests
            time.sleep(0.1)

    def test_load_tenders_endpoint(self):
        """Test load on tenders list endpoint with normal users."""
        endpoint = '/api/v1/tenders/'
        num_users = LOAD_TEST_CONFIG['normal_users']
        duration = LOAD_TEST_CONFIG['test_duration']

        print(f"\nStarting load test: {num_users} users for {duration}s")

        # Start user threads
        threads = []
        start_time = time.perf_counter()

        for _ in range(num_users):
            t = threading.Thread(target=self._simulate_user, args=(endpoint, duration))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        actual_duration = time.perf_counter() - start_time
        throughput = calculate_throughput(self.metrics.total_requests, actual_duration)

        print(f"\nLoad Test Results:")
        print(f"  Total requests: {self.metrics.total_requests}")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} req/s")
        print(f"  p50: {self.metrics.p50:.2f}ms")
        print(f"  p95: {self.metrics.p95:.2f}ms")
        print(f"  p99: {self.metrics.p99:.2f}ms")
        print(f"  Error rate: {self.metrics.error_rate}%")

        # Check thresholds
        results = check_performance_threshold(
            self.metrics,
            API_THRESHOLDS['p95_response_time'],
            API_THRESHOLDS['p99_response_time'],
            API_THRESHOLDS['error_rate']
        )

        assert results['p95_pass'], f"p95 {self.metrics.p95}ms exceeds threshold"
        assert results['error_rate_pass'], f"Error rate {self.metrics.error_rate}% exceeds threshold"

    def test_load_statistics_endpoint(self):
        """Test load on statistics endpoint with normal users."""
        endpoint = '/api/v1/statistics/'
        num_users = LOAD_TEST_CONFIG['normal_users']
        duration = 60  # Shorter test for statistics

        print(f"\nStarting load test: {num_users} users for {duration}s")

        # Start user threads
        threads = []
        start_time = time.perf_counter()

        for _ in range(num_users):
            t = threading.Thread(target=self._simulate_user, args=(endpoint, duration))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join()

        actual_duration = time.perf_counter() - start_time
        throughput = calculate_throughput(self.metrics.total_requests, actual_duration)

        print(f"\nLoad Test Results (Statistics):")
        print(f"  Total requests: {self.metrics.total_requests}")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Throughput: {throughput:.2f} req/s")
        print(f"  p50: {self.metrics.p50:.2f}ms")
        print(f"  p95: {self.metrics.p95:.2f}ms")
        print(f"  p99: {self.metrics.p99:.2f}ms")
        print(f"  Error rate: {self.metrics.error_rate}%")

        # Check thresholds - slightly relaxed for load test
        threshold_p95 = API_THRESHOLDS['p95_response_time'] * 1.5
        assert self.metrics.p95 < threshold_p95, f"p95 {self.metrics.p95}ms exceeds threshold"
        assert self.metrics.error_rate < 5, f"Error rate {self.metrics.error_rate}% too high"

    def test_multiple_endpoints_load(self):
        """Test load across multiple endpoints."""
        endpoints = [
            '/api/v1/tenders/',
            '/api/v1/statistics/',
            '/api/v1/opportunities/',
        ]
        num_users = 50
        duration = 30

        def user_simulation():
            end_time = time.time() + duration
            while time.time() < end_time:
                for endpoint in endpoints:
                    start = time.perf_counter()
                    try:
                        response = self.client.get(endpoint)
                        elapsed = (time.perf_counter() - start) * 1000
                        self.metrics.add_response(elapsed, response.status_code)
                    except Exception as e:
                        self.metrics.add_response(0, 500, str(e))
                time.sleep(0.1)

        print(f"\nMulti-endpoint load test: {num_users} users for {duration}s")

        threads = []
        for _ in range(num_users):
            t = threading.Thread(target=user_simulation)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        print(f"\nMulti-endpoint Results:")
        print(f"  Total requests: {self.metrics.total_requests}")
        print(f"  p95: {self.metrics.p95:.2f}ms")
        print(f"  Error rate: {self.metrics.error_rate}%")

        assert self.metrics.error_rate < 5, "Error rate too high"


@pytest.mark.django_db
class TestLoadTestMetrics:
    """Test metrics collection and calculation."""

    def test_metrics_collection(self):
        """Test that metrics are collected correctly."""
        from apps.core.performance.helpers import PerformanceMetrics

        metrics = PerformanceMetrics()

        # Add some test data
        metrics.add_response(100, 200)
        metrics.add_response(200, 200)
        metrics.add_response(300, 200)
        metrics.add_response(400, 500, "Error")
        metrics.add_response(500, 500, "Error")

        assert metrics.total_requests == 5
        assert metrics.p50 == 300
        assert metrics.error_rate == 40  # 2 out of 5

    def test_throughput_calculation(self):
        """Test throughput calculation."""
        from apps.core.performance.helpers import calculate_throughput

        # 100 requests in 10 seconds = 10 req/s
        throughput = calculate_throughput(100, 10)
        assert throughput == 10

        # Edge cases
        assert calculate_throughput(0, 10) == 0
        assert calculate_throughput(100, 0) == 0