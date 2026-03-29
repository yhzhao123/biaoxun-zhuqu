"""
TDD Cycle 21: Metrics Tests

测试 Prometheus 指标收集:
- extraction_count (Counter)
- extraction_duration (Histogram)
- extraction_errors (Counter)
- cache_hit_rate (Gauge)
- concurrent_requests (Gauge)
- queue_length (Gauge)
"""
import pytest
import time
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestPrometheusMetrics:
    """测试 Prometheus 指标"""

    def test_metrics_exporter_creation(self):
        """测试指标导出器创建"""
        from apps.monitoring.prometheus_metrics import MetricsExporter

        exporter = MetricsExporter()
        assert exporter.registry is not None

    def test_extraction_counter(self):
        """测试提取计数器"""
        from apps.monitoring.prometheus_metrics import extraction_count

        # 增加计数器
        extraction_count.inc()
        extraction_count.inc()

    def test_extraction_errors_counter(self):
        """测试提取错误计数器"""
        from apps.monitoring.prometheus_metrics import extraction_errors

        # 增加错误计数器
        extraction_errors.inc()

    def test_extraction_duration_histogram(self):
        """测试提取持续时间直方图"""
        from apps.monitoring.prometheus_metrics import extraction_duration

        # 记录提取时间
        extraction_duration.observe(1.5)
        extraction_duration.observe(2.3)

    def test_cache_hit_rate_gauge(self):
        """测试缓存命中率仪表"""
        from apps.monitoring.prometheus_metrics import cache_hit_rate

        # 设置缓存命中率
        cache_hit_rate.set(0.85)

    def test_concurrent_requests_gauge(self):
        """测试并发请求仪表"""
        from apps.monitoring.prometheus_metrics import concurrent_requests

        # 设置并发请求数
        concurrent_requests.set(5)

    def test_queue_length_gauge(self):
        """测试队列长度仪表"""
        from apps.monitoring.prometheus_metrics import queue_length

        # 设置队列长度
        queue_length.set(10)


class TestMetricsCollector:
    """测试指标收集器"""

    def test_metrics_collector_creation(self):
        """测试指标收集器创建"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()
        assert collector is not None

    def test_record_extraction(self):
        """测试记录提取"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()
        collector.record_extraction(
            source_url="http://test.com",
            duration=1.5,
            success=True,
            items_count=10
        )

    def test_record_extraction_error(self):
        """测试记录提取错误"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()
        collector.record_extraction(
            source_url="http://test.com",
            duration=0.5,
            success=False,
            error_message="Connection timeout"
        )

    def test_update_cache_stats(self):
        """测试更新缓存统计"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()
        collector.update_cache_stats(hits=80, misses=20)

    def test_update_concurrent_requests(self):
        """测试更新并发请求数"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()
        collector.update_concurrent_requests(5)

    def test_update_queue_length(self):
        """测试更新队列长度"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()
        collector.update_queue_length(15)

    def test_get_all_metrics(self):
        """测试获取所有指标"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()
        metrics = collector.get_all_metrics()

        assert "extraction_count" in metrics
        assert "extraction_errors" in metrics
        assert "cache_hit_rate" in metrics


class TestMetricsEndpoint:
    """测试指标端点"""

    def test_metrics_endpoint_returns_prometheus_format(self):
        """测试指标端点返回 Prometheus 格式"""
        from apps.monitoring.prometheus_metrics import generate_metrics

        # 生成指标
        metrics_output = generate_metrics()

        assert isinstance(metrics_output, str)
        assert "# HELP" in metrics_output or "# TYPE" in metrics_output


class TestMetricsMiddleware:
    """测试指标中间件"""

    def test_metrics_middleware_creation(self):
        """测试指标中间件创建"""
        from apps.monitoring.prometheus_metrics import MetricsMiddleware

        middleware = MetricsMiddleware(get_response=MagicMock())
        assert middleware.get_response is not None


class TestMetricsContextManager:
    """测试指标上下文管理器"""

    def test_track_extraction_time(self):
        """测试跟踪提取时间"""
        from apps.monitoring.prometheus_metrics import track_extraction_time

        with track_extraction_time("test_source"):
            time.sleep(0.01)


class TestMetricsDecorator:
    """测试指标装饰器"""

    @patch('apps.monitoring.prometheus_metrics.extraction_count')
    def test_track_extraction_decorator(self, mock_counter):
        """测试跟踪提取装饰器"""
        from apps.monitoring.prometheus_metrics import track_extraction

        @track_extraction
        def mock_extraction():
            return {"items": []}

        mock_extraction()


class TestMetricsIntegration:
    """测试指标集成"""

    def test_full_extraction_flow_metrics(self):
        """测试完整提取流程指标"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()

        # 记录提取开始
        collector.update_concurrent_requests(1)

        # 模拟提取
        collector.record_extraction(
            source_url="http://example.com/api",
            duration=2.5,
            success=True,
            items_count=20
        )

        # 更新缓存
        collector.update_cache_stats(hits=15, misses=5)

        # 记录完成
        collector.update_concurrent_requests(0)

        # 验证指标
        metrics = collector.get_all_metrics()
        assert metrics["extraction_count"] >= 1

    def test_error_flow_metrics(self):
        """测试错误流程指标"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()

        # 模拟提取错误
        collector.record_extraction(
            source_url="http://example.com/api",
            duration=0.5,
            success=False,
            error_message="Network error"
        )

        # 验证错误计数
        metrics = collector.get_all_metrics()
        assert metrics["extraction_errors"] >= 1


class TestPrometheusLabels:
    """测试 Prometheus 标签"""

    def test_extraction_with_source_label(self):
        """测试带源标签的提取指标"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()
        collector.record_extraction(
            source_url="http://source-a.com",
            duration=1.0,
            success=True,
            items_count=10
        )

    def test_extraction_with_status_label(self):
        """测试带状态标签的提取指标"""
        from apps.monitoring.prometheus_metrics import MetricsCollector

        collector = MetricsCollector()
        collector.record_extraction(
            source_url="http://test.com",
            duration=1.0,
            success=True,
            items_count=10
        )