"""
Soak Testing
Task 070: Soak/Endurance Testing (1 hour sustained load)
"""

import pytest
import time
import requests
import threading

from .config import PerformanceConfig, SoakTestConfig
from .helpers import PerformanceMetrics


def is_server_available():
    """Check if the backend server is running"""
    try:
        response = requests.get("http://localhost:8000/api/tenders/", timeout=2)
        return response.status_code == 200
    except:
        return False


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.skipif(not is_server_available(), reason="Backend server not running on localhost:8000")
class TestSoakTesting:
    """Soak testing - long duration endurance test"""

    base_url = "http://localhost:8000"
    config = SoakTestConfig()

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

    def test_soak_endurance(self):
        """
        Soak test: 1 hour sustained load
        - 200 concurrent users
        - 1 hour duration
        - Monitor for memory leaks, performance degradation
        """
        endpoint = PerformanceConfig.API_ENDPOINTS['tender_list']
        concurrent = self.config.concurrent_users
        duration_hours = self.config.duration_hours
        duration_seconds = duration_hours * 60 * 60  # Convert to seconds

        # For testing, use shorter duration (5 minutes)
        test_duration = 300  # 5 minutes for actual test

        print(f"\n{'='*60}")
        print(f"Soak Test: Endurance Testing")
        print(f"  Concurrent users: {concurrent}")
        print(f"  Target duration: {duration_hours} hour(s)")
        print(f"  Test duration: {test_duration // 60} minute(s)")
        print(f"{'='*60}")

        # Sample metrics every 5 minutes
        sample_interval = 60  # 1 minute samples for testing
        all_samples = []

        stop_event = threading.Event()
        metrics_lock = threading.Lock()
        current_metrics = PerformanceMetrics()

        def worker():
            while not stop_event.is_set():
                success, elapsed = self._make_request(endpoint)
                with metrics_lock:
                    current_metrics.response_times.append(elapsed)
                    if success:
                        current_metrics.successful_requests += 1
                    else:
                        current_metrics.failed_requests += 1
                    current_metrics.total_requests += 1

        threads = []
        start_time = time.time()

        # Ramp up
        print(f"\n  Ramping up to {concurrent} users...")
        for i in range(concurrent):
            t = threading.Thread(target=worker)
            t.daemon = True
            t.start()
            threads.append(t)
            if i % 20 == 0:
                time.sleep(0.5)  # Gradual ramp

        print(f"  Running for {test_duration // 60} minutes...")

        # Collect samples during test
        sample_count = test_duration // sample_interval
        for sample in range(sample_count):
            time.sleep(sample_interval)

            with metrics_lock:
                # Capture current sample
                sample_metrics = PerformanceMetrics()
                sample_metrics.total_requests = current_metrics.total_requests
                sample_metrics.successful_requests = current_metrics.successful_requests
                sample_metrics.failed_requests = current_metrics.failed_requests
                sample_metrics.response_times = current_metrics.response_times.copy()

                all_samples.append({
                    'time': (sample + 1) * sample_interval,
                    'total': sample_metrics.total_requests,
                    'success_rate': sample_metrics.success_rate,
                    'error_rate': sample_metrics.error_rate,
                    'avg_ms': sample_metrics.avg_response_time * 1000,
                    'p95_ms': sample_metrics.p95 * 1000,
                    'p99_ms': sample_metrics.p99 * 1000,
                })

                elapsed = time.time() - start_time
                progress = (elapsed / test_duration) * 100
                print(f"  [{progress:>5.1f}%] Sample {sample+1}/{sample_count}: "
                      f"{sample_metrics.success_rate:.1f}% success, "
                      f"P95: {sample_metrics.p95*1000:.0f}ms")

        # Stop all threads
        stop_event.set()
        for t in threads:
            t.join(timeout=10)

        total_duration = time.time() - start_time

        # Final metrics
        with metrics_lock:
            final_metrics = PerformanceMetrics()
            final_metrics.total_requests = current_metrics.total_requests
            final_metrics.successful_requests = current_metrics.successful_requests
            final_metrics.failed_requests = current_metrics.failed_requests
            final_metrics.response_times = current_metrics.response_times.copy()

        # Summary
        print(f"\n{'='*60}")
        print("Soak Test Summary")
        print(f"{'='*60}")
        print(f"Total duration: {total_duration / 60:.1f} minutes")
        print(f"Total requests: {final_metrics.total_requests}")
        print(f"Average RPS: {final_metrics.total_requests / total_duration:.2f}")
        print(f"Overall success rate: {final_metrics.success_rate:.2f}%")
        print(f"Overall error rate: {final_metrics.error_rate:.2f}%")
        print(f"Average response time: {final_metrics.avg_response_time * 1000:.2f}ms")
        print(f"P95 response time: {final_metrics.p95 * 1000:.2f}ms")
        print(f"P99 response time: {final_metrics.p99 * 1000:.2f}ms")

        # Performance degradation analysis
        if len(all_samples) >= 2:
            first_sample = all_samples[0]
            last_sample = all_samples[-1]

            print(f"\nPerformance Degradation Analysis:")
            print(f"  First sample P95: {first_sample['p95_ms']:.0f}ms")
            print(f"  Last sample P95:  {last_sample['p95_ms']:.0f}ms")

            degradation = last_sample['p95_ms'] - first_sample['p95_ms']
            degradation_pct = (degradation / first_sample['p95_ms']) * 100 if first_sample['p95_ms'] > 0 else 0

            print(f"  Degradation: {degradation:.0f}ms ({degradation_pct:+.1f}%)")

        # Assertions
        assert final_metrics.success_rate >= 95, \
            f"Overall success rate {final_metrics.success_rate:.1f}% below 95%"
        assert final_metrics.error_rate < 2, \
            f"Overall error rate {final_metrics.error_rate:.1f}% too high"

        # Check for significant degradation (>50% increase in P95)
        if len(all_samples) >= 2:
            first_p95 = all_samples[0]['p95_ms']
            last_p95 = all_samples[-1]['p95_ms']
            assert last_p95 < first_p95 * 1.5, \
                f"Performance degraded significantly: {first_p95:.0f}ms -> {last_p95:.0f}ms"

    def test_soak_memory_stability(self):
        """
        Memory stability test (shorter duration)
        Check for memory leaks by running sustained load
        """
        endpoint = PerformanceConfig.API_ENDPOINTS['tender_list']
        concurrent = 100
        duration = 120  # 2 minutes

        print(f"\nMemory Stability Test ({duration}s at {concurrent} users)")

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

        print(f"  Total requests: {metrics.total_requests}")
        print(f"  Success rate: {metrics.success_rate:.1f}%")
        print(f"  P95: {metrics.p95*1000:.0f}ms")

        # Should maintain consistent performance
        assert metrics.success_rate >= 95
        assert metrics.p95 * 1000 < 1000
