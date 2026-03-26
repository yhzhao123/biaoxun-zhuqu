"""
Additional Helper Tests
Tests for helper functions to improve coverage.
"""

import pytest
import time
from apps.core.performance.helpers import (
    PerformanceMetrics,
    measure_time,
    generate_random_string,
    generate_test_tender_data,
    RateLimiter,
    run_concurrent_requests,
    calculate_throughput,
    calculate_average_response_time,
    check_performance_threshold,
)


class TestHelperFunctions:
    """Test helper functions for better coverage."""

    def test_measure_time(self):
        """Test measure_time context manager."""
        with measure_time() as get_elapsed:
            time.sleep(0.01)  # 10ms

        elapsed = get_elapsed()
        assert elapsed >= 10, f"Expected >= 10ms, got {elapsed}ms"

    def test_measure_time_nested(self):
        """Test nested measure_time."""
        with measure_time() as outer:
            time.sleep(0.01)
            with measure_time() as inner:
                time.sleep(0.02)

            inner_elapsed = inner()
            assert inner_elapsed >= 20

        outer_elapsed = outer()
        assert outer_elapsed >= 30

    def test_generate_random_string_default_length(self):
        """Test random string generation with default length."""
        result = generate_random_string()
        assert len(result) == 10

    def test_generate_random_string_custom_length(self):
        """Test random string generation with custom length."""
        result = generate_random_string(20)
        assert len(result) == 20

    def test_generate_random_string_small_length(self):
        """Test random string generation with small length."""
        result = generate_random_string(1)
        assert len(result) == 1

    def test_generate_test_tender_data(self):
        """Test tender data generation."""
        data = generate_test_tender_data(5)
        assert len(data) == 5

        # Check structure
        for tender in data:
            assert 'title' in tender
            assert 'tender_no' in tender
            assert 'status' in tender
            assert 'category' in tender
            assert 'budget' in tender
            assert 'published_at' in tender
            assert 'deadline' in tender

    def test_generate_test_tender_data_zero(self):
        """Test tender data generation with zero count."""
        data = generate_test_tender_data(0)
        assert len(data) == 0

    def test_rate_limiter(self):
        """Test rate limiter."""
        limiter = RateLimiter(max_per_second=10)

        start = time.perf_counter()
        for _ in range(5):
            limiter.wait()
        elapsed = time.perf_counter() - start

        # Should take at least 0.4 seconds for 5 requests at 10/sec
        assert elapsed >= 0.4

    def test_rate_limiter_high_rate(self):
        """Test high rate limiter."""
        limiter = RateLimiter(max_per_second=1000)

        start = time.perf_counter()
        for _ in range(10):
            limiter.wait()
        elapsed = time.perf_counter() - start

        # With 1000/sec, 10 requests should take < 0.05s
        assert elapsed < 0.1

    def test_run_concurrent_requests(self):
        """Test concurrent request runner."""
        results = []

        def mock_request():
            time.sleep(0.01)  # Simulate request
            return 10, 200, None

        metrics = run_concurrent_requests(
            mock_request,
            num_requests=10,
            max_concurrent=5
        )

        assert metrics.total_requests == 10
        assert metrics.error_rate == 0

    def test_run_concurrent_requests_with_errors(self):
        """Test concurrent requests with errors."""

        def mock_error_request():
            time.sleep(0.01)
            return 0, 500, "Server Error"

        metrics = run_concurrent_requests(
            mock_error_request,
            num_requests=5,
            max_concurrent=2
        )

        assert metrics.total_requests == 5
        assert metrics.error_rate == 100

    def test_calculate_throughput(self):
        """Test throughput calculation."""
        assert calculate_throughput(100, 10) == 10
        assert calculate_throughput(0, 10) == 0
        assert calculate_throughput(100, 0) == 0

    def test_calculate_average_response_time(self):
        """Test average response time calculation."""
        assert calculate_average_response_time([100, 200, 300]) == 200
        assert calculate_average_response_time([]) == 0
        assert calculate_average_response_time([100]) == 100

    def test_check_performance_threshold_pass(self):
        """Test threshold checking when passing."""
        metrics = PerformanceMetrics()
        metrics.add_response(100, 200)
        metrics.add_response(200, 200)
        metrics.add_response(300, 200)

        result = check_performance_threshold(
            metrics,
            threshold_p95=500,
            threshold_p99=1000,
            threshold_error_rate=1
        )

        assert result['p95_pass'] == True
        assert result['p99_pass'] == True
        assert result['error_rate_pass'] == True

    def test_check_performance_threshold_fail(self):
        """Test threshold checking when failing."""
        metrics = PerformanceMetrics()
        metrics.add_response(1000, 200)
        metrics.add_response(1500, 200)
        metrics.add_response(2000, 500, "Error")

        result = check_performance_threshold(
            metrics,
            threshold_p95=500,
            threshold_p99=1000,
            threshold_error_rate=1
        )

        assert result['p95_pass'] == False
        assert result['p99_pass'] == False
        assert result['error_rate_pass'] == False


class TestPerformanceMetricsEdgeCases:
    """Test edge cases for PerformanceMetrics."""

    def test_empty_metrics(self):
        """Test empty metrics."""
        metrics = PerformanceMetrics()

        assert metrics.p50 == 0
        assert metrics.p95 == 0
        assert metrics.p99 == 0
        assert metrics.mean == 0
        assert metrics.error_rate == 0
        assert metrics.total_requests == 0

    def test_single_response(self):
        """Test single response."""
        metrics = PerformanceMetrics()
        metrics.add_response(100, 200)

        assert metrics.p50 == 100
        assert metrics.p95 == 100
        assert metrics.p99 == 100
        assert metrics.mean == 100
        assert metrics.error_rate == 0
        assert metrics.total_requests == 1

    def test_calculate_percentile_edge_cases(self):
        """Test percentile calculation edge cases."""
        metrics = PerformanceMetrics()

        # Empty
        assert metrics.calculate_percentile(50) == 0

        # Single value
        metrics.add_response(100, 200)
        assert metrics.calculate_percentile(50) == 100
        assert metrics.calculate_percentile(95) == 100
        assert metrics.calculate_percentile(99) == 100

    def test_to_dict_empty(self):
        """Test to_dict with empty metrics."""
        metrics = PerformanceMetrics()
        result = metrics.to_dict()

        assert result['p50'] == 0
        assert result['p95'] == 0
        assert result['p99'] == 0
        assert result['mean'] == 0
        assert result['error_rate'] == 0
        assert result['total_requests'] == 0

    def test_error_rate_calculation(self):
        """Test error rate calculation."""
        metrics = PerformanceMetrics()

        # No errors
        for _ in range(9):
            metrics.add_response(100, 200)
        metrics.add_response(100, 500, "Error")

        # 1 out of 10 = 10%
        assert metrics.error_rate == 10

    def test_all_errors(self):
        """Test all errors."""
        metrics = PerformanceMetrics()
        for _ in range(5):
            metrics.add_response(0, 500, "Error")

        assert metrics.error_rate == 100