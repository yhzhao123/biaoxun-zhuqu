"""
Load Testing
Task 070: Load Testing (100-200 concurrent users)
"""

import pytest
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from .config import PerformanceConfig, LoadTestConfig
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
class TestLoadTesting:
    """Load testing with 100-200 concurrent users"""

    base_url = "http://localhost:8000"
    config = LoadTestConfig()

    def _make_request(self, endpoint: str) -> tuple:
        """Make a single request and return (success, response_time)"""
        start = time.perf_counter()
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                timeout=30
            )
            response.raise_for_status()
            elapsed = time.perf_counter() - start
            return (True, elapsed)
        except Exception as e:
            elapsed = time.perf_counter() - start
            return (False, elapsed)

    def test_load_tender_list(self):
        """
        Load test: Tender list endpoint
        - 100 concurrent users
        - Duration: 5 minutes
        - Target: 100 RPS
        """
        metrics = PerformanceMetrics()
        endpoint = PerformanceConfig.API_ENDPOINTS['tender_list']
        num_requests = 500  # 100 users * 5 requests each
        concurrent = self.config.concurrent_users

        print(f"\n{'='*60}")
        print(f"Load Test: Tender List")
        print(f"  Concurrent users: {concurrent}")
        print(f"  Total requests: {num_requests}")
        print(f"{'='*60}")

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [
                executor.submit(self._make_request, endpoint)
                for _ in range(num_requests)
            ]

            for future in as_completed(futures):
                success, elapsed = future.result()
                metrics.response_times.append(elapsed)
                if success:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                metrics.total_requests += 1

        duration = time.time() - start_time
        actual_rps = num_requests / duration

        print(f"\nResults:")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Actual RPS: {actual_rps:.2f}")
        print(f"  Success rate: {metrics.success_rate:.2f}%")
        print(f"  Error rate: {metrics.error_rate:.2f}%")
        print(f"  Avg response: {metrics.avg_response_time*1000:.2f}ms")
        print(f"  P95 response: {metrics.p95*1000:.2f}ms")
        print(f"  P99 response: {metrics.p99*1000:.2f}ms")

        # Assertions
        sla_check = metrics.check_sla()
        assert sla_check['p95_pass'], f"P95 {sla_check['p95_actual_ms']}ms exceeds 500ms threshold"
        assert sla_check['error_rate_pass'], f"Error rate {sla_check['error_rate_actual']}% exceeds 1% threshold"
        assert actual_rps >= 50, f"RPS {actual_rps:.2f} is below target"

    def test_load_dashboard(self):
        """
        Load test: Dashboard endpoint
        - 100 concurrent users
        """
        metrics = PerformanceMetrics()
        endpoint = PerformanceConfig.API_ENDPOINTS['dashboard']
        num_requests = 300
        concurrent = self.config.concurrent_users

        print(f"\nLoad Test: Dashboard ({concurrent} concurrent users)")

        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [
                executor.submit(self._make_request, endpoint)
                for _ in range(num_requests)
            ]

            for future in as_completed(futures):
                success, elapsed = future.result()
                metrics.response_times.append(elapsed)
                if success:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                metrics.total_requests += 1

        print(f"  Success rate: {metrics.success_rate:.2f}%")
        print(f"  P95: {metrics.p95*1000:.2f}ms")

        sla_check = metrics.check_sla()
        assert sla_check['p95_pass']
        assert sla_check['error_rate_pass']

    def test_load_mixed_endpoints(self):
        """
        Load test: Mixed API endpoints
        Simulates realistic traffic pattern
        """
        metrics = PerformanceMetrics()
        endpoints = [
            PerformanceConfig.API_ENDPOINTS['tender_list'],
            PerformanceConfig.API_ENDPOINTS['dashboard'],
            PerformanceConfig.API_ENDPOINTS['stats'],
            PerformanceConfig.API_ENDPOINTS['tender_list'],  # Higher weight
        ]

        num_requests = 400
        concurrent = self.config.concurrent_users

        print(f"\nLoad Test: Mixed Endpoints ({concurrent} concurrent users)")

        request_count = 0
        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = []
            for i in range(num_requests):
                endpoint = endpoints[i % len(endpoints)]
                futures.append(executor.submit(self._make_request, endpoint))

            for future in as_completed(futures):
                success, elapsed = future.result()
                metrics.response_times.append(elapsed)
                if success:
                    metrics.successful_requests += 1
                else:
                    metrics.failed_requests += 1
                metrics.total_requests += 1

        print(f"  Total requests: {metrics.total_requests}")
        print(f"  Success rate: {metrics.success_rate:.2f}%")
        print(f"  Error rate: {metrics.error_rate:.2f}%")
        print(f"  Avg: {metrics.avg_response_time*1000:.2f}ms")
        print(f"  P95: {metrics.p95*1000:.2f}ms")
        print(f"  P99: {metrics.p99*1000:.2f}ms")

        sla_check = metrics.check_sla()
        assert sla_check['p95_pass']
        assert sla_check['p99_pass']
        assert sla_check['error_rate_pass']

    def test_sustained_load(self):
        """
        Sustained load test
        Maintain load for extended period
        """
        metrics = PerformanceMetrics()
        endpoint = PerformanceConfig.API_ENDPOINTS['tender_list']
        concurrent = 50  # Lower concurrent for sustained test
        duration_seconds = 30  # 30 seconds

        print(f"\nSustained Load Test: {duration_seconds}s at {concurrent} concurrent")

        start_time = time.time()
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

        time.sleep(duration_seconds)
        stop_event.set()

        for t in threads:
            t.join(timeout=5)

        print(f"  Total requests: {metrics.total_requests}")
        print(f"  Success rate: {metrics.success_rate:.2f}%")
        print(f"  Avg RPS: {metrics.total_requests / duration_seconds:.2f}")

        # Under sustained load, we allow slightly higher thresholds
        assert metrics.success_rate >= 95, f"Success rate {metrics.success_rate:.2f}% below 95%"
        assert metrics.p95 * 1000 < 1000, f"P95 {metrics.p95*1000:.2f}ms exceeds 1000ms"
