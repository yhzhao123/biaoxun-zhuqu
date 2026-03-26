"""
Soak Test Tests
Tests for long-running load (1 hour duration) to detect memory leaks and degradation.
"""

import pytest
import time
import threading
import psutil
import os
from typing import List

from django.test import Client

from apps.core.performance.config import SOAK_TEST_CONFIG, API_THRESHOLDS
from apps.core.performance.helpers import PerformanceMetrics


# Skip long-running soak tests by default
pytestmark = pytest.mark.skipif(
    os.environ.get('RUN_SOAK_TESTS', '').lower() != 'true',
    reason="Soak tests require RUN_SOAK_TESTS=true environment variable"
)


@pytest.mark.django_db
class TestSoakTest:
    """Soak testing for long-duration performance."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test client."""
        self.client = Client()
        self.metrics = PerformanceMetrics()
        self.process = psutil.Process(os.getpid())

    def _simulate_user(self, endpoint: str, duration: int, results: dict) -> None:
        """Simulate a user making requests for a duration."""
        metrics = PerformanceMetrics()
        end_time = time.time() + duration
        requests_made = 0
        errors = 0

        while time.time() < end_time:
            start = time.perf_counter()
            try:
                response = self.client.get(endpoint)
                elapsed = (time.perf_counter() - start) * 1000
                metrics.add_response(elapsed, response.status_code)
                requests_made += 1
            except Exception as e:
                metrics.add_response(0, 500, str(e))
                errors += 1

            time.sleep(0.1)

        results['metrics'] = metrics
        results['requests'] = requests_made
        results['errors'] = errors

    def test_soak_tenders_endpoint(self):
        """Test long-duration load on tenders endpoint."""
        endpoint = '/api/v1/tenders/'
        num_users = SOAK_TEST_CONFIG['users']
        # Use shorter duration for testing (5 minutes instead of 1 hour)
        # Set RUN_SOAK_TESTS=true for full 1 hour test
        duration = int(os.environ.get('SOAK_DURATION', 300))

        print(f"\nStarting soak test: {num_users} users for {duration}s")

        # Record initial memory
        initial_memory = self.process.memory_info().rss / 1024 / 1024  # MB

        # Store results from threads
        thread_results = []
        start_time = time.perf_counter()

        # Start threads
        threads = []
        for _ in range(num_users):
            result = {}
            thread_results.append(result)
            t = threading.Thread(
                target=self._simulate_user,
                args=(endpoint, duration, result)
            )
            threads.append(t)
            t.start()

        # Monitor during test
        memory_samples = []
        response_time_samples = []

        sample_interval = 10  # Sample every 10 seconds
        last_sample = time.time()

        while time.time() - start_time < duration:
            time.sleep(1)

            if time.time() - last_sample >= sample_interval:
                # Sample memory
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_samples.append(current_memory)

                # Sample response times from threads
                for result in thread_results:
                    if hasattr(result.get('metrics'), 'response_times') and result['metrics'].response_times:
                        response_time_samples.append(result['metrics'].response_times[-1] if result['metrics'].response_times else 0)

                last_sample = time.time()

        # Wait for completion
        for t in threads:
            t.join()

        actual_duration = time.time() - start_time

        # Calculate total metrics
        total_requests = sum(r.get('requests', 0) for r in thread_results)
        total_errors = sum(r.get('errors', 0) for r in thread_results)

        # Aggregate response times
        for result in thread_results:
            if hasattr(result.get('metrics'), 'response_times'):
                self.metrics.response_times.extend(result['metrics'].response_times)
                self.metrics.status_codes.extend(result['metrics'].status_codes)
                self.metrics.errors.extend(result['metrics'].errors)

        # Final memory
        final_memory = self.process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        print(f"\nSoak Test Results:")
        print(f"  Duration: {actual_duration:.2f}s")
        print(f"  Total requests: {total_requests}")
        print(f"  Total errors: {total_errors}")
        print(f"  Initial memory: {initial_memory:.2f}MB")
        print(f"  Final memory: {final_memory:.2f}MB")
        print(f"  Memory increase: {memory_increase:.2f}MB")

        if self.metrics.response_times:
            print(f"  p50: {self.metrics.p50:.2f}ms")
            print(f"  p95: {self.metrics.p95:.2f}ms")
            print(f"  p99: {self.metrics.p99:.2f}ms")

        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        print(f"  Error rate: {error_rate:.2f}%")

        # Memory leak detection: increase should be < 200MB
        assert memory_increase < 200, \
            f"Memory increased by {memory_increase:.2f}MB - possible memory leak"

        # Error rate should remain low
        assert error_rate < 5, f"Error rate {error_rate}% too high"

    def test_performance_degradation(self):
        """Test for performance degradation over time."""
        endpoint = '/api/v1/tenders/'
        num_users = 50
        duration = 300  # 5 minutes

        print(f"\nTesting performance degradation over {duration}s")

        # Collect metrics in time windows
        window_size = 60  # 1 minute windows
        windows = []
        current_window = PerformanceMetrics()
        window_start = time.time()

        stop_flag = threading.Event()

        def worker():
            while not stop_flag.is_set():
                start = time.perf_counter()
                try:
                    response = self.client.get(endpoint)
                    elapsed = (time.perf_counter() - start) * 1000
                    current_window.add_response(elapsed, response.status_code)
                except Exception as e:
                    current_window.add_response(0, 500, str(e))
                time.sleep(0.1)

        threads = [threading.Thread(target=worker) for _ in range(num_users)]
        for t in threads:
            t.start()

        # Collect window data
        while time.time() - window_start < duration:
            time.sleep(1)

            if time.time() - window_start >= window_size * len(windows) + window_size:
                windows.append(current_window)
                current_window = PerformanceMetrics()

        stop_flag.set()
        for t in threads:
            t.join()

        # Add final window
        if current_window.total_requests > 0:
            windows.append(current_window)

        # Analyze degradation
        print(f"\nPerformance by time window:")
        for i, window in enumerate(windows):
            print(f"  Window {i+1}: p95={window.p95:.2f}ms, error_rate={window.error_rate:.2f}%")

        # Check if last window is significantly worse than first
        if len(windows) >= 2:
            first_p95 = windows[0].p95
            last_p95 = windows[-1].p95
            degradation = ((last_p95 - first_p95) / first_p95 * 100) if first_p95 > 0 else 0

            print(f"\nPerformance degradation: {degradation:.2f}%")

            # Allow up to 50% degradation over time
            assert degradation < 50, \
                f"Performance degraded by {degradation:.2f}% - possible issue"


@pytest.mark.django_db
class TestSoakMemoryLeaks:
    """Test for memory leaks in long-running scenarios."""

    def test_memory_stability(self):
        """Test memory remains stable during repeated requests."""
        endpoint = '/api/v1/tenders/'
        client = Client()

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Make many requests
        for _ in range(1000):
            client.get(endpoint)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        print(f"\nMemory stability test:")
        print(f"  Initial: {initial_memory:.2f}MB")
        print(f"  Final: {final_memory:.2f}MB")
        print(f"  Increase: {memory_increase:.2f}MB")

        # Should not have significant memory increase
        assert memory_increase < 100, \
            f"Memory increased by {memory_increase:.2f}MB - possible memory leak"


@pytest.mark.django_db
class TestSoakDatabase:
    """Test database connection stability."""

    def test_database_connection_stability(self):
        """Test database connections remain stable over time."""
        from django.db import connection

        endpoint = '/api/v1/tenders/'
        client = Client()

        # Make many requests
        for i in range(100):
            client.get(endpoint)

        # Check connection is still valid
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result == (1,)
        except Exception as e:
            pytest.fail(f"Database connection failed: {e}")

        print("\nDatabase connection remains stable")

    def test_connection_pool_health(self):
        """Test connection pool remains healthy."""
        from django.db import connections

        endpoint = '/api/v1/tenders/'
        client = Client()

        # Make requests
        for _ in range(50):
            client.get(endpoint)

        # Check connections
        num_connections = len(connections.all())
        print(f"\nActive connections: {num_connections}")

        assert num_connections > 0, "No database connections"