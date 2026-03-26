"""
Spike Testing
Task 070: Spike Testing (100 -> 1000 users sudden increase)
"""

import pytest
import time
import requests
import threading

from .config import PerformanceConfig, SpikeTestConfig
from .helpers import PerformanceMetrics


def is_server_available():
    """Check if the backend server is running"""
    try:
        response = requests.get("http://localhost:8000/api/tenders/", timeout=2)
        return response.status_code == 200
    except:
        return False


@pytest.mark.performance
@pytest.mark.skipif(not is_server_available(), reason="Backend server not running on localhost:8000")
class TestSpikeTesting:
    """Spike testing - sudden traffic surge"""

    base_url = "http://localhost:8000"
    config = SpikeTestConfig()

    def _make_request(self, endpoint: str, timeout: int = 10) -> tuple:
        """Make a single request and return (success, response_time)"""
        start = time.perf_counter()
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                timeout=timeout
            )
            response.raise_for_status()
            elapsed = time.perf_counter() - start
            return (True, elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return (False, elapsed)

    def test_spike_traffic_surge(self):
        """
        Spike test: Sudden traffic surge
        - Base: 100 concurrent users
        - Spike: sudden increase to 1000 users
        - Duration: 60 seconds spike
        - Cooldown: 120 seconds
        """
        endpoint = PerformanceConfig.API_ENDPOINTS['tender_list']
        base_users = self.config.base_users
        spike_users = self.config.spike_users
        spike_duration = self.config.spike_duration_seconds
        cooldown = self.config.cooldown_seconds

        print(f"\n{'='*60}")
        print(f"Spike Test: Traffic Surge")
        print(f"  Base load: {base_users} users")
        print(f"  Spike: {spike_users} users")
        print(f"  Spike duration: {spike_duration}s")
        print(f"  Cooldown: {cooldown}s")
        print(f"{'='*60}")

        # Phase 1: Base load
        print("\n  Phase 1: Base load...")
        base_metrics = self._run_load(endpoint, base_users, 30)
        print(f"    Success: {base_metrics.success_rate:.1f}% | "
              f"Avg: {base_metrics.avg_response_time*1000:.0f}ms")

        # Phase 2: Spike
        print("\n  Phase 2: SPIKE!...")
        spike_metrics = self._run_load(endpoint, spike_users, spike_duration)
        print(f"    Success: {spike_metrics.success_rate:.1f}% | "
              f"Avg: {spike_metrics.avg_response_time*1000:.0f}ms | "
              f"P95: {spike_metrics.p95*1000:.0f}ms")

        # Phase 3: Cooldown
        print("\n  Phase 3: Cooldown...")
        cooldown_metrics = self._run_load(endpoint, base_users, cooldown)
        print(f"    Success: {cooldown_metrics.success_rate:.1f}% | "
              f"Avg: {cooldown_metrics.avg_response_time*1000:.0f}ms")

        # Summary
        print(f"\n{'='*60}")
        print("Spike Test Summary")
        print(f"{'='*60}")
        print(f"Base load:    {base_metrics.success_rate:>6.1f}% success, "
              f"P95: {base_metrics.p95*1000:>6.0f}ms")
        print(f"Spike:        {spike_metrics.success_rate:>6.1f}% success, "
              f"P95: {spike_metrics.p95*1000:>6.0f}ms")
        print(f"Cooldown:     {cooldown_metrics.success_rate:>6.1f}% success, "
              f"P95: {cooldown_metrics.p95*1000:>6.0f}ms")

        # Assertions
        # Base load should be stable
        assert base_metrics.success_rate >= 95, "Base load success rate too low"

        # During spike, we expect degraded performance but system should recover
        assert spike_metrics.success_rate >= 80, \
            f"Spike success rate {spike_metrics.success_rate:.1f}% too low"

        # After cooldown, system should return to normal
        assert cooldown_metrics.success_rate >= 95, "System didn't recover after spike"

    def _run_load(self, endpoint: str, concurrent: int, duration: int) -> PerformanceMetrics:
        """Run load test and return metrics"""
        metrics = PerformanceMetrics()
        stop_event = threading.Event()

        def worker():
            while not stop_event.is_set():
                success, elapsed = self._make_request(endpoint)
                metrics.response_times.append(elapsed)
                if success:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                metrics.total_requests += 1

        threads = []
        for _ in range(concurrent):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            threads.append(t)

        time.sleep(duration)
        stop_event.set()

        for t in threads:
            t.join(timeout=5)

        return metrics

    def test_spike_multiple_surges(self):
        """
        Multiple spike events
        """
        endpoint = PerformanceConfig.API_ENDPOINTS['tender_list']
        base_users = 50
        spike_users = 500

        print(f"\nMultiple Spike Test")

        results = []
        for i in range(3):
            print(f"\n  Spike {i+1}/3...")

            # Base
            base = self._run_load(endpoint, base_users, 15)

            # Spike
            spike = self._run_load(endpoint, spike_users, 30)

            print(f"    Base: {base.success_rate:.1f}% | Spike: {spike.success_rate:.1f}%")

            results.append({
                'base_success': base.success_rate,
                'spike_success': spike.success_rate,
            })

        # All spikes should maintain >80% success rate
        for i, r in enumerate(results):
            assert r['spike_success'] >= 80, f"Spike {i+1} success rate too low"

    def test_spike_recovery_time(self):
        """
        Measure recovery time after spike
        """
        endpoint = PerformanceConfig.API_ENDPOINTS['tender_list']

        print(f"\nRecovery Time Test")

        # Spike phase
        spike_metrics = self._run_load(endpoint, 800, 30)
        print(f"  After spike: {spike_metrics.success_rate:.1f}% success")

        # Measure recovery
        recovery_times = []
        for check in range(5):
            time.sleep(10)
            check_metrics = self._run_load(endpoint, 50, 10)
            recovery_times.append(check_metrics.success_rate)
            print(f"  Check {check+1}: {check_metrics.success_rate:.1f}% success")

            # System recovered if success rate > 95%
            if check_metrics.success_rate >= 95:
                print(f"  Recovered after {(check+1)*10} seconds")
                break

        # System should recover within 60 seconds
        assert any(r >= 95 for r in recovery_times), "System didn't recover in time"
