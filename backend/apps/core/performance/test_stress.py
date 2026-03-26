"""
Stress Test Tests
Tests for high load conditions (400-600 concurrent users).
"""

import pytest
import time
import threading

from django.test import Client

from apps.core.performance.config import STRESS_TEST_CONFIG, API_THRESHOLDS
from apps.core.performance.helpers import (
    PerformanceMetrics,
    check_performance_threshold,
)


@pytest.mark.django_db
class TestStressTest:
    """Stress testing for high load conditions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test client."""
        self.client = Client()
        self.metrics = PerformanceMetrics()

    def _simulate_user(self, endpoint: str, duration: int, stop_flag) -> None:
        """Simulate a single user making requests."""
        end_time = time.time() + duration

        while time.time() < end_time and not stop_flag():
            start = time.perf_counter()
            try:
                response = self.client.get(endpoint)
                elapsed = (time.perf_counter() - start) * 1000
                self.metrics.add_response(elapsed, response.status_code)
            except Exception as e:
                self.metrics.add_response(0, 500, str(e))

            time.sleep(0.05)  # Faster requests in stress test

    def test_stress_tenders_endpoint(self):
        """Test stress on tenders endpoint with high concurrency."""
        endpoint = '/api/v1/tenders/'
        num_users = STRESS_TEST_CONFIG['max_users']
        duration = 60  # Shorter for stress test

        stop_flag = threading.Event()
        print(f"\nStarting stress test: {num_users} users for {duration}s")

        start_time = time.perf_counter()

        # Start in waves to simulate gradual increase
        waves = 6
        users_per_wave = num_users // waves
        threads = []

        for wave in range(waves):
            for _ in range(users_per_wave):
                t = threading.Thread(
                    target=self._simulate_user,
                    args=(endpoint, duration, lambda: stop_flag.is_set())
                )
                threads.append(t)
                t.start()
            time.sleep(10)  # Wait between waves

        # Wait for all threads
        for t in threads:
            t.join()

        actual_duration = time.perf_counter() - start_time

        print(f"\nStress Test Results:")
        print(f"  Total requests: {self.metrics.total_requests}")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  p50: {self.metrics.p50:.2f}ms")
        print(f"  p95: {self.metrics.p95:.2f}ms")
        print(f"  p99: {self.metrics.p99:.2f}ms")
        print(f"  Error rate: {self.metrics.error_rate}%")

        # Stress test allows up to 5% error rate
        assert self.metrics.error_rate < 5, \
            f"Error rate {self.metrics.error_rate}% exceeds 5% threshold"

    def test_stress_degradation(self):
        """Test system behavior under stress - degradation should be graceful."""
        endpoint = '/api/v1/statistics/'
        num_users = 400  # High concurrent users

        stop_flag = threading.Event()

        def worker():
            while not stop_flag():
                start = time.perf_counter()
                try:
                    response = self.client.get(endpoint)
                    elapsed = (time.perf_counter() - start) * 1000
                    self.metrics.add_response(elapsed, response.status_code)
                except Exception as e:
                    self.metrics.add_response(0, 500, str(e))
                time.sleep(0.02)

        threads = []
        for _ in range(num_users):
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # Run for 30 seconds
        time.sleep(30)
        stop_flag.set()

        for t in threads:
            t.join()

        print(f"\nStress degradation test:")
        print(f"  Error rate: {self.metrics.error_rate}%")
        print(f"  p95: {self.metrics.p95:.2f}ms")

        # System should still respond under stress
        assert self.metrics.total_requests > 0, "No requests completed"
        assert self.metrics.error_rate < 10, "Error rate too high under stress"


@pytest.mark.django_db
class TestStressRecovery:
    """Test system recovery after stress."""

    def test_recovery_after_stress(self):
        """Test system returns to normal after high load."""
        client = Client()
        endpoint = '/api/v1/tenders/'

        # First, establish baseline
        baseline_times = []
        for _ in range(10):
            start = time.perf_counter()
            client.get(endpoint)
            baseline_times.append((time.perf_counter() - start) * 1000)

        baseline_p95 = sorted(baseline_times)[int(len(baseline_times) * 0.95)]

        # Apply stress
        print("\nApplying stress load...")
        stress_metrics = PerformanceMetrics()
        stop_flag = threading.Event()

        def stress_worker():
            while not stop_flag.is_set():
                start = time.perf_counter()
                try:
                    response = client.get(endpoint)
                    elapsed = (time.perf_counter() - start) * 1000
                    stress_metrics.add_response(elapsed, response.status_code)
                except:
                    pass
                time.sleep(0.01)

        threads = [threading.Thread(target=stress_worker) for _ in range(200)]
        for t in threads:
            t.start()

        # Run stress for 15 seconds
        time.sleep(15)
        stop_flag.set()
        for t in threads:
            t.join()

        print(f"Stress phase: {stress_metrics.total_requests} requests")

        # Wait for recovery
        time.sleep(5)

        # Test recovery
        recovery_times = []
        for _ in range(10):
            start = time.perf_counter()
            client.get(endpoint)
            recovery_times.append((time.perf_counter() - start) * 1000)

        recovery_p95 = sorted(recovery_times)[int(len(recovery_times) * 0.95)]

        print(f"\nRecovery test:")
        print(f"  Baseline p95: {baseline_p95:.2f}ms")
        print(f"  Recovery p95: {recovery_p95:.2f}ms")

        # Recovery should be within 2x baseline
        assert recovery_p95 < baseline_p95 * 2, \
            "System did not recover properly after stress"