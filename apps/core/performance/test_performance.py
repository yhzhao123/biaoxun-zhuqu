"""
Unit tests for performance module helpers
"""

import pytest
from .helpers import PerformanceMetrics, Timer, calculate_percentile


class TestPerformanceMetrics:
    """Test PerformanceMetrics class"""

    def test_initial_state(self):
        """Test initial state of metrics"""
        metrics = PerformanceMetrics()
        assert metrics.total_requests == 0
        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.response_times == []
        assert metrics.errors == []

    def test_success_rate_calculation(self):
        """Test success rate calculation"""
        metrics = PerformanceMetrics()
        metrics.total_requests = 100
        metrics.successful_requests = 95
        metrics.failed_requests = 5

        assert metrics.success_rate == 95.0

    def test_success_rate_zero_requests(self):
        """Test success rate with zero requests"""
        metrics = PerformanceMetrics()
        assert metrics.success_rate == 0.0

    def test_error_rate_calculation(self):
        """Test error rate calculation"""
        metrics = PerformanceMetrics()
        metrics.total_requests = 100
        metrics.successful_requests = 99
        metrics.failed_requests = 1

        assert metrics.error_rate == 1.0

    def test_avg_response_time(self):
        """Test average response time calculation"""
        metrics = PerformanceMetrics()
        metrics.response_times = [0.1, 0.2, 0.3, 0.4, 0.5]

        assert metrics.avg_response_time == 0.3

    def test_percentile_calculation(self):
        """Test percentile calculation"""
        metrics = PerformanceMetrics()
        metrics.response_times = [0.1, 0.2, 0.3, 0.4, 0.5] * 20  # 100 values

        p50 = metrics.get_percentile(50)
        p95 = metrics.get_percentile(95)

        assert p50 == 0.3
        assert p95 == 0.5

    def test_p50_p95_p99_properties(self):
        """Test percentile properties"""
        metrics = PerformanceMetrics()
        metrics.response_times = [i * 0.01 for i in range(1, 101)]  # 0.01 to 1.0

        assert metrics.p50 == pytest.approx(0.51, abs=0.02)
        assert metrics.p95 == pytest.approx(0.96, abs=0.02)
        assert metrics.p99 == pytest.approx(1.0, abs=0.01)

    def test_to_dict(self):
        """Test conversion to dictionary"""
        metrics = PerformanceMetrics()
        metrics.total_requests = 100
        metrics.successful_requests = 95
        metrics.failed_requests = 5
        metrics.response_times = [0.1, 0.2, 0.3]

        result = metrics.to_dict()

        assert result['total_requests'] == 100
        assert result['successful_requests'] == 95
        assert result['failed_requests'] == 5
        assert result['success_rate'] == 95.0
        assert result['error_rate'] == 5.0
        assert 'avg_response_time_ms' in result
        assert 'p95_ms' in result

    def test_check_sla_pass(self):
        """Test SLA check - all pass"""
        metrics = PerformanceMetrics()
        metrics.total_requests = 100
        metrics.successful_requests = 99
        metrics.failed_requests = 1
        metrics.response_times = [0.1] * 95 + [0.4] * 5  # P95 ~ 0.4s = 400ms

        sla = metrics.check_sla(p95_threshold_ms=500, error_rate_threshold=2)

        assert sla['p95_pass'] is True
        assert sla['error_rate_pass'] is True
        assert sla['overall_pass'] is True

    def test_check_sla_fail_p95(self):
        """Test SLA check - P95 fails"""
        metrics = PerformanceMetrics()
        metrics.total_requests = 100
        metrics.successful_requests = 100
        metrics.response_times = [0.1] * 94 + [0.6] * 6  # P95 ~ 0.6s = 600ms

        sla = metrics.check_sla(p95_threshold_ms=500)

        assert sla['p95_pass'] is False
        assert sla['overall_pass'] is False

    def test_check_sla_fail_error_rate(self):
        """Test SLA check - error rate fails"""
        metrics = PerformanceMetrics()
        metrics.total_requests = 100
        metrics.successful_requests = 95
        metrics.failed_requests = 5  # 5% error rate

        sla = metrics.check_sla(error_rate_threshold=2)

        assert sla['error_rate_pass'] is False
        assert sla['overall_pass'] is False


class TestTimer:
    """Test Timer class"""

    def test_timer_basic(self):
        """Test basic timer functionality"""
        import time

        timer = Timer()
        timer.start()
        time.sleep(0.01)  # 10ms
        elapsed = timer.stop()

        assert elapsed >= 0.01
        assert timer.elapsed == elapsed

    def test_timer_context_manager(self):
        """Test timer as context manager"""
        import time

        with Timer() as timer:
            time.sleep(0.01)

        assert timer.elapsed >= 0.01

    def test_timer_stop_before_start(self):
        """Test stopping timer before starting"""
        timer = Timer()

        with pytest.raises(RuntimeError):
            timer.stop()


class TestCalculatePercentile:
    """Test calculate_percentile function"""

    def test_basic_percentile(self):
        """Test basic percentile calculation"""
        values = [1, 2, 3, 4, 5]

        assert calculate_percentile(values, 0) == 1
        assert calculate_percentile(values, 50) == 3
        assert calculate_percentile(values, 100) == 5

    def test_empty_list(self):
        """Test empty list returns 0"""
        assert calculate_percentile([], 50) == 0.0

    def test_single_value(self):
        """Test single value list"""
        assert calculate_percentile([42], 50) == 42

    def test_large_list(self):
        """Test with larger list"""
        values = list(range(1, 101))  # 1 to 100

        # Percentile calculation uses index = int(len * p / 100)
        # For 100 items: index = 50 for p50 -> returns values[50] = 51
        assert calculate_percentile(values, 50) == 51
        assert calculate_percentile(values, 95) == 96
