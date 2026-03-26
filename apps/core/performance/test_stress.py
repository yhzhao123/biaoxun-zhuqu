"""
Stress Testing
Task 070: Stress Testing (400-600 concurrent users)
"""

import pytest
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .config import PerformanceConfig, StressTestConfig
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
class TestStressTesting:
    """Stress testing to find system breaking point"""

    base_url = "http://localhost:8000"
    config = StressTestConfig()

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

    def test_stress_gradual_ramp(self):
        """
        Stress test: Gradual ramp-up
        Increase load in steps to find breaking point
        """
        endpoint = PerformanceConfig.API_ENDPOINTS['tender_list']
        step_users = self.config.step_users
        step_duration = self.config.step_duration_seconds
        max_users = self.config.max_concurrent_users

        print(f"\n{'='*60}")
        print(f"Stress Test: Gradual Ramp-up")
        print(f"  Max users: {max_users}")
        print(f"  Step size: {step_users} users")
        print(f"  Step duration: {step_duration}s")
        print(f"{'='*60}")

        all_results = []

        for current_users in range(step_users, max_users + 1, step_users):
            metrics = PerformanceMetrics()
            stop_event = threading.Event()

            print(f"\n  Step: {current_users} concurrent users...")

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
            start_time = time.time()

            for _ in range(current_users):
                t = threading.Thread(target=worker)
                t.daemon = True
                t.start()
                threads.append(t)

            time.sleep(step_duration)
            stop_event.set()

            for t in threads:
                t.join(timeout=5)

            duration = time.time() - start_time
            rps = metrics.total_requests / duration

            result = {
                'concurrent': current_users,
                'total': metrics.total_requests,
                'success_rate': metrics.success_rate,
                'error_rate': metrics.error_rate,
                'avg_ms': metrics.avg_response_time * 1000,
                'p95_ms': metrics.p95 * 1000,
                'p99_ms': metrics.p99 * 1000,
                'rps': rps,
            }
            all_results.append(result)

            print(f"    RPS: {rps:.2f} | Success: {metrics.success_rate:.1f}% | "
                  f"P95: {metrics.p95*1000:.0f}ms")

        # Print summary table
        print(f"\n{'='*60}")
        print("Stress Test Summary")
        print(f"{'='*60}")
        print(f"{'Users':>8} | {'RPS':>8} | {'Success%':>8} | {'Avg(ms)':>8} | {'P95(ms)':>8}")
        print(f"{'-'*60}")
        for r in all_results:
            print(f"{r['concurrent']:>8} | {r['rps']:>8.1f} | {r['success_rate']:>8.1f} | "
                  f"{r['avg_ms']:>8.1f} | {r['p95_ms']:>8.1f}")

        # System should handle up to 400 users gracefully
        mid_point = len(all_results) // 2
        if mid_point > 0:
            mid_result = all_results[mid_point]
            assert mid_result['success_rate'] >= 95, \
                f"Success rate {mid_result['success_rate']:.1f}% below 95% at {mid_result['concurrent']} users"
            assert mid_result['error_rate'] < 5, \
                f"Error rate {mid_result['error_rate']:.1f}% too high"

    def test_stress_search_endpoint(self):
        """
        Stress test: Search endpoint (heavier load)
        """
        endpoint = f"{PerformanceConfig.API_ENDPOINTS['search']}?q=test"
        metrics = PerformanceMetrics()
        concurrent = 200
        duration = 30

        print(f"\nStress Test: Search ({concurrent} users, {duration}s)")

        stop_event = threading.Event()

        def worker():
            while not stop_event.is_set():
                success, elapsed = self._make_request(endpoint, timeout=15)
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

        print(f"  Total: {metrics.total_requests}")
        print(f"  Success: {metrics.success_rate:.1f}%")
        print(f"  P95: {metrics.p95*1000:.0f}ms")

        # Search can be slower, allow higher thresholds
        assert metrics.success_rate >= 90, \
            f"Success rate {metrics.success_rate:.1f}% below 90%"

    def test_stress_breaking_point(self):
        """
        Find approximate breaking point
        Increase load until error rate exceeds 10%
        """
        endpoint = PerformanceConfig.API_ENDPOINTS['tender_list']

        print(f"\nBreaking Point Analysis")

        for concurrent in [100, 200, 400, 600, 800]:
            metrics = PerformanceMetrics()
            requests_per_user = 10

            with ThreadPoolExecutor(max_workers=concurrent) as executor:
                futures = [
                    executor.submit(self._make_request, endpoint)
                    for _ in range(concurrent * requests_per_user)
                ]

                for future in as_completed(futures):
                    success, elapsed = future.result()
                    metrics.response_times.append(elapsed)
                    if success:
                        metrics.successful_requests += 1
                    else:
                        metrics.failed_requests += 1
                    metrics.total_requests += 1

            print(f"  {concurrent:>4} users: {metrics.success_rate:>5.1f}% success, "
                  f"P95: {metrics.p95*1000:>6.0f}ms")

            # Breaking point: error rate > 10%
            if metrics.error_rate > 10:
                print(f"  Breaking point found at ~{concurrent} users")
                break
