"""
API Benchmark Tests
Tests for API endpoint performance baselines.
"""

import pytest
import time
import statistics
from typing import List, Dict, Any

from django.test import Client
from django.urls import reverse

from apps.core.performance.config import API_THRESHOLDS, TARGET_ENDPOINTS
from apps.core.performance.helpers import (
    PerformanceMetrics,
    measure_time,
    check_performance_threshold,
    generate_test_tender_data,
)


@pytest.mark.django_db
class TestAPIBenchmark:
    """API benchmark tests for measuring endpoint performance."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test client and data."""
        self.client = Client()
        self.metrics = PerformanceMetrics()

    def _make_request(self, endpoint: str, method: str = 'GET', data: Dict = None) -> float:
        """Make a single HTTP request and return response time in ms."""
        start_time = time.perf_counter()

        if method == 'GET':
            response = self.client.get(endpoint)
        elif method == 'POST':
            response = self.client.post(endpoint, data, content_type='application/json')
        else:
            raise ValueError(f"Unsupported method: {method}")

        elapsed = (time.perf_counter() - start_time) * 1000

        # Track status code
        self.metrics.add_response(elapsed, response.status_code)

        return elapsed

    def test_tenders_list_endpoint(self):
        """Test /api/v1/tenders/ endpoint performance."""
        endpoint = '/api/v1/tenders/'

        # Warm up requests
        for _ in range(3):
            self._make_request(endpoint)

        # Test requests
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nTenders list p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_statistics_overview_endpoint(self):
        """Test /api/v1/statistics/ endpoint performance."""
        endpoint = '/api/v1/statistics/'

        # Warm up
        for _ in range(3):
            self._make_request(endpoint)

        # Test
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nStatistics overview p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_statistics_trend_endpoint(self):
        """Test /api/v1/statistics/trend/ endpoint performance."""
        endpoint = '/api/v1/statistics/trend/'

        # Warm up
        for _ in range(3):
            self._make_request(endpoint)

        # Test
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nStatistics trend p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_statistics_budget_endpoint(self):
        """Test /api/v1/statistics/budget/ endpoint performance."""
        endpoint = '/api/v1/statistics/budget/'

        # Warm up
        for _ in range(3):
            self._make_request(endpoint)

        # Test
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nStatistics budget p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_statistics_top_tenderers_endpoint(self):
        """Test /api/v1/statistics/top-tenderers/ endpoint performance."""
        endpoint = '/api/v1/statistics/top-tenderers/'

        # Warm up
        for _ in range(3):
            self._make_request(endpoint)

        # Test
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nStatistics top-tenderers p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_opportunities_endpoint(self):
        """Test /api/v1/opportunities/ endpoint performance."""
        endpoint = '/api/v1/opportunities/'

        # Warm up
        for _ in range(3):
            self._make_request(endpoint)

        # Test
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nOpportunities p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_opportunities_high_value_endpoint(self):
        """Test /api/v1/opportunities/high-value/ endpoint performance."""
        endpoint = '/api/v1/opportunities/high-value/'

        # Warm up
        for _ in range(3):
            self._make_request(endpoint)

        # Test
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nOpportunities high-value p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_opportunities_urgent_endpoint(self):
        """Test /api/v1/opportunities/urgent/ endpoint performance."""
        endpoint = '/api/v1/opportunities/urgent/'

        # Warm up
        for _ in range(3):
            self._make_request(endpoint)

        # Test
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nOpportunities urgent p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_reports_daily_endpoint(self):
        """Test /api/v1/reports/daily/ endpoint performance."""
        endpoint = '/api/v1/reports/daily/'

        # Warm up
        for _ in range(3):
            self._make_request(endpoint)

        # Test
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nReports daily p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_reports_weekly_endpoint(self):
        """Test /api/v1/reports/weekly/ endpoint performance."""
        endpoint = '/api/v1/reports/weekly/'

        # Warm up
        for _ in range(3):
            self._make_request(endpoint)

        # Test
        for _ in range(20):
            self._make_request(endpoint)

        p95 = self.metrics.p95
        print(f"\nReports weekly p95: {p95}ms")

        assert p95 < API_THRESHOLDS['p95_response_time'], \
            f"p95 response time {p95}ms exceeds threshold {API_THRESHOLDS['p95_response_time']}ms"

    def test_concurrent_requests_performance(self):
        """Test concurrent request handling."""
        import threading

        endpoint = '/api/v1/statistics/'
        num_threads = 20
        requests_per_thread = 5

        def make_requests():
            for _ in range(requests_per_thread):
                self._make_request(endpoint)

        # Start concurrent threads
        threads = []
        start_time = time.perf_counter()

        for _ in range(num_threads):
            t = threading.Thread(target=make_requests)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        duration = time.perf_counter() - start_time
        total_requests = num_threads * requests_per_thread
        throughput = total_requests / duration

        print(f"\nConcurrent test: {total_requests} requests in {duration:.2f}s")
        print(f"Throughput: {throughput:.2f} req/s")
        print(f"Error rate: {self.metrics.error_rate}%")

        assert self.metrics.error_rate < API_THRESHOLDS['error_rate'], \
            f"Error rate {self.metrics.error_rate}% exceeds threshold"

    def test_response_time_consistency(self):
        """Test response time consistency across multiple requests."""
        endpoint = '/api/v1/tenders/'

        # Make many requests to check consistency
        for _ in range(50):
            self._make_request(endpoint)

        # Check standard deviation
        if len(self.metrics.response_times) > 1:
            std_dev = statistics.stdev(self.metrics.response_times)
            mean = self.metrics.mean
            cv = (std_dev / mean * 100) if mean > 0 else 0

            print(f"\nResponse time CV: {cv:.2f}%")

            # Coefficient of variation should be < 80% for consistent performance
            # (relaxed for test environment)
            assert cv < 80, f"Response time variation {cv:.2f}% too high"