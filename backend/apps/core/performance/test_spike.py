"""
Spike Test Tests
Tests for sudden traffic spikes (100 -> 1000 users).
"""

import pytest
import time
import threading

from django.test import Client

from apps.core.performance.config import SPIKE_TEST_CONFIG, API_THRESHOLDS
from apps.core.performance.helpers import PerformanceMetrics


@pytest.mark.django_db
class TestSpikeTest:
    """Spike testing for sudden traffic increases."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test client."""
        self.client = Client()
        self.metrics = PerformanceMetrics()

    def _simulate_user(self, endpoint: str, stop_flag) -> None:
        """Simulate a user making requests until stopped."""
        while not stop_flag.is_set():
            start = time.perf_counter()
            try:
                response = self.client.get(endpoint)
                elapsed = (time.perf_counter() - start) * 1000
                self.metrics.add_response(elapsed, response.status_code)
            except Exception as e:
                self.metrics.add_response(0, 500, str(e))
            time.sleep(0.05)

    def test_spike_increase(self):
        """Test sudden spike from baseline to high load."""
        endpoint = '/api/v1/tenders/'

        baseline_users = SPIKE_TEST_CONFIG['baseline_users']
        spike_users = SPIKE_TEST_CONFIG['spike_users']
        ramp_time = SPIKE_TEST_CONFIG['ramp_up_time']
        hold_time = SPIKE_TEST_CONFIG['hold_time']

        stop_flag = threading.Event()
        threads = []

        # Phase 1: Baseline load
        print(f"\nPhase 1: Baseline load with {baseline_users} users")
        for _ in range(baseline_users):
            t = threading.Thread(target=self._simulate_user, args=(endpoint, stop_flag))
            threads.append(t)
            t.start()

        time.sleep(10)  # Let baseline stabilize

        # Record baseline metrics
        baseline_requests = self.metrics.total_requests
        baseline_p95 = self.metrics.p95

        # Phase 2: Sudden spike
        print(f"Phase 2: Spike to {spike_users} users")
        additional_users = spike_users - baseline_users
        for _ in range(additional_users):
            t = threading.Thread(target=self._simulate_user, args=(endpoint, stop_flag))
            threads.append(t)
            t.start()

        # Hold spike
        time.sleep(hold_time)

        # Record spike metrics
        spike_p95 = self.metrics.p95

        # Phase 3: Recovery
        print("Phase 3: Recovery")
        stop_flag.set()
        for t in threads:
            t.join()

        print(f"\nSpike Test Results:")
        print(f"  Baseline p95: {baseline_p95:.2f}ms")
        print(f"  Spike p95: {spike_p95:.2f}ms")
        print(f"  Total requests: {self.metrics.total_requests}")
        print(f"  Error rate: {self.metrics.error_rate}%")

        # Under spike, system should handle with graceful degradation
        # Error rate should be manageable (< 10%)
        assert self.metrics.error_rate < 10, \
            f"Error rate {self.metrics.error_rate}% too high during spike"

    def test_rapid_ramp_up(self):
        """Test very rapid user increase."""
        endpoint = '/api/v1/statistics/'

        stop_flag = threading.Event()
        threads = []

        # Ramp up quickly from 0 to 500 users
        print("\nRapid ramp-up test: 0 -> 500 users")

        for i in range(500):
            t = threading.Thread(target=self._simulate_user, args=(endpoint, stop_flag))
            threads.append(t)
            t.start()

            if i % 100 == 0:
                time.sleep(0.5)  # Brief pause every 100 users

        # Hold for 30 seconds
        time.sleep(30)
        stop_flag.set()

        for t in threads:
            t.join()

        print(f"\nRamp-up results:")
        print(f"  Total requests: {self.metrics.total_requests}")
        print(f"  p95: {self.metrics.p95:.2f}ms")
        print(f"  Error rate: {self.metrics.error_rate}%")

        # System should handle rapid ramp with acceptable error rate
        assert self.metrics.error_rate < 15, "Error rate too high during rapid ramp"

    def test_spike_recovery(self):
        """Test recovery after spike."""
        client = Client()
        endpoint = '/api/v1/tenders/'

        # Pre-spike baseline
        pre_times = []
        for _ in range(10):
            start = time.perf_counter()
            client.get(endpoint)
            pre_times.append((time.perf_counter() - start) * 1000)

        pre_p95 = sorted(pre_times)[int(len(pre_times) * 0.95)]

        # Spike phase
        print("\nApplying spike...")
        metrics = PerformanceMetrics()
        stop_flag = threading.Event()

        def worker():
            while not stop_flag.is_set():
                start = time.perf_counter()
                try:
                    response = client.get(endpoint)
                    elapsed = (time.perf_counter() - start) * 1000
                    metrics.add_response(elapsed, response.status_code)
                except:
                    pass

        threads = [threading.Thread(target=worker) for _ in range(800)]
        for t in threads:
            t.start()

        time.sleep(20)  # Hold spike
        stop_flag.set()
        for t in threads:
            t.join()

        # Recovery period
        time.sleep(10)

        # Post-spike measurement
        post_times = []
        for _ in range(20):
            start = time.perf_counter()
            client.get(endpoint)
            post_times.append((time.perf_counter() - start) * 1000)

        post_p95 = sorted(post_times)[int(len(post_times) * 0.95)]

        print(f"\nRecovery metrics:")
        print(f"  Pre-spike p95: {pre_p95:.2f}ms")
        print(f"  Post-recovery p95: {post_p95:.2f}ms")

        # After recovery, should be within 2x of baseline
        assert post_p95 < pre_p95 * 2, \
            "System did not recover within acceptable time"


@pytest.mark.django_db
class TestSpikeEdgeCases:
    """Edge case tests for spike scenarios."""

    def test_zero_users_spike(self):
        """Test behavior when spike to 0 users."""
        client = Client()
        endpoint = '/api/v1/tenders/'

        # Should handle gracefully
        start = time.perf_counter()
        response = client.get(endpoint)
        elapsed = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 1000

    def test_very_high_spike(self):
        """Test with extremely high spike (1000+ users)."""
        endpoint = '/api/v1/tenders/'
        client = Client()
        metrics = PerformanceMetrics()

        stop_flag = threading.Event()

        def worker():
            while not stop_flag.is_set():
                start = time.perf_counter()
                try:
                    response = client.get(endpoint)
                    elapsed = (time.perf_counter() - start) * 1000
                    metrics.add_response(elapsed, response.status_code)
                except:
                    metrics.add_response(0, 500, "Exception")

        # Very high load
        threads = [threading.Thread(target=worker) for _ in range(1000)]
        for t in threads:
            t.start()

        time.sleep(15)
        stop_flag.set()
        for t in threads:
            t.join()

        print(f"\nVery high spike results:")
        print(f"  Total requests: {metrics.total_requests}")
        print(f"  Error rate: {metrics.error_rate}%")

        # Even at extreme load, should handle some requests
        assert metrics.total_requests > 0