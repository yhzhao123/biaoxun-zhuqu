"""
API Benchmark Tests
Task 070: API Performance Benchmarking
"""

import pytest
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

from .config import PerformanceConfig
from .helpers import PerformanceMetrics, measure_response_time


def is_server_available():
    """Check if the backend server is running"""
    try:
        response = requests.get("http://localhost:8000/api/tenders/", timeout=2)
        return response.status_code == 200
    except:
        return False


@pytest.mark.performance
@pytest.mark.skipif(not is_server_available(), reason="Backend server not running on localhost:8000")
class TestAPIBenchmark:
    """API endpoint benchmark tests"""

    base_url = "http://localhost:8000"

    def _make_request(self, endpoint: str) -> float:
        """Make a single request and return response time"""
        start = time.perf_counter()
        try:
            response = requests.get(f"{self.base_url}{endpoint}", timeout=30)
            response.raise_for_status()
        except Exception as e:
            raise e
        finally:
            elapsed = time.perf_counter() - start
        return elapsed

    def _run_concurrent_requests(self, endpoint: str, num_requests: int,
                                  concurrent: int = 10) -> PerformanceMetrics:
        """Run concurrent requests and collect metrics"""
        metrics = PerformanceMetrics()

        with ThreadPoolExecutor(max_workers=concurrent) as executor:
            futures = [
                executor.submit(self._make_request, endpoint)
                for _ in range(num_requests)
            ]

            for future in as_completed(futures):
                try:
                    elapsed = future.result()
                    metrics.response_times.append(elapsed)
                    metrics.successful_requests += 1
                except Exception as e:
                    metrics.failed_requests += 1
                    metrics.errors.append(str(e))
                finally:
                    metrics.total_requests += 1

        return metrics

    def test_tender_list_benchmark(self):
        """Benchmark tender list endpoint"""
        metrics = self._run_concurrent_requests(
            PerformanceConfig.API_ENDPOINTS['tender_list'],
            num_requests=100,
            concurrent=10
        )

        print(f"\nTender List Benchmark:")
        print(f"  Total: {metrics.total_requests}")
        print(f"  Success: {metrics.successful_requests}")
        print(f"  Failed: {metrics.failed_requests}")
        print(f"  Avg: {metrics.avg_response_time * 1000:.2f}ms")
        print(f"  P95: {metrics.p95 * 1000:.2f}ms")
        print(f"  P99: {metrics.p99 * 1000:.2f}ms")

        # Verify SLA compliance
        sla_check = metrics.check_sla()
        assert sla_check['p95_pass'], f"P95 {sla_check['p95_actual_ms']}ms exceeds threshold"
        assert sla_check['error_rate_pass'], f"Error rate {sla_check['error_rate_actual']}% exceeds threshold"

    def test_dashboard_benchmark(self):
        """Benchmark dashboard endpoint"""
        metrics = self._run_concurrent_requests(
            PerformanceConfig.API_ENDPOINTS['dashboard'],
            num_requests=50,
            concurrent=5
        )

        print(f"\nDashboard Benchmark:")
        print(f"  Total: {metrics.total_requests}")
        print(f"  Avg: {metrics.avg_response_time * 1000:.2f}ms")
        print(f"  P95: {metrics.p95 * 1000:.2f}ms")

        sla_check = metrics.check_sla()
        assert sla_check['p95_pass'], f"P95 {sla_check['p95_actual_ms']}ms exceeds threshold"

    def test_search_benchmark(self):
        """Benchmark search endpoint"""
        search_url = f"{PerformanceConfig.API_ENDPOINTS['search']}?q=test"
        metrics = self._run_concurrent_requests(
            search_url,
            num_requests=50,
            concurrent=5
        )

        print(f"\nSearch Benchmark:")
        print(f"  Total: {metrics.total_requests}")
        print(f"  Avg: {metrics.avg_response_time * 1000:.2f}ms")
        print(f"  P95: {metrics.p95 * 1000:.2f}ms")

        sla_check = metrics.check_sla(p95_threshold_ms=1000)  # Search can be slower
        assert sla_check['p95_pass'], f"P95 {sla_check['p95_actual_ms']}ms exceeds threshold"

    def test_stats_benchmark(self):
        """Benchmark stats endpoint"""
        metrics = self._run_concurrent_requests(
            PerformanceConfig.API_ENDPOINTS['stats'],
            num_requests=50,
            concurrent=5
        )

        print(f"\nStats Benchmark:")
        print(f"  Total: {metrics.total_requests}")
        print(f"  Avg: {metrics.avg_response_time * 1000:.2f}ms")
        print(f"  P95: {metrics.p95 * 1000:.2f}ms")

        sla_check = metrics.check_sla()
        assert sla_check['p95_pass'], f"P95 {sla_check['p95_actual_ms']}ms exceeds threshold"

    def test_endpoint_response_times(self):
        """Test response times for all key endpoints"""
        endpoints = [
            ('tender_list', PerformanceConfig.API_ENDPOINTS['tender_list']),
            ('stats', PerformanceConfig.API_ENDPOINTS['stats']),
            ('regions', PerformanceConfig.API_ENDPOINTS['regions']),
            ('industries', PerformanceConfig.API_ENDPOINTS['industries']),
        ]

        results: Dict[str, PerformanceMetrics] = {}

        for name, endpoint in endpoints:
            metrics = self._run_concurrent_requests(
                endpoint,
                num_requests=20,
                concurrent=5
            )
            results[name] = metrics

        # Print summary
        print("\n" + "="*60)
        print("API Benchmark Summary")
        print("="*60)
        for name, metrics in results.items():
            print(f"{name:20s} | Avg: {metrics.avg_response_time*1000:>8.2f}ms | "
                  f"P95: {metrics.p95*1000:>8.2f}ms | "
                  f"Errors: {metrics.failed_requests}")

        # Verify all pass SLA
        for name, metrics in results.items():
            sla_check = metrics.check_sla()
            assert sla_check['p95_pass'], f"{name} P95 {sla_check['p95_actual_ms']}ms exceeds threshold"
            assert sla_check['error_rate_pass'], f"{name} error rate exceeds threshold"
