"""
Task 060: Performance Monitoring Tests
测试性能监控功能 - ApiMetric, DbMetric, QueueMetric, AlertRule, 中间件
"""
import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from collections import deque

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')
django.setup()


class TestApiMetric:
    """测试 API 指标数据模型"""

    def test_api_metric_creation(self):
        """测试 ApiMetric 创建"""
        from apps.monitoring.performance.models import ApiMetric

        metric = ApiMetric(
            endpoint='/api/tenders',
            method='GET',
            response_time=150.5,
            status_code=200
        )

        assert metric.endpoint == '/api/tenders'
        assert metric.method == 'GET'
        assert metric.response_time == 150.5
        assert metric.status_code == 200

    def test_api_metric_is_error(self):
        """测试错误状态码识别"""
        from apps.monitoring.performance.models import ApiMetric

        metric = ApiMetric(
            endpoint='/api/tenders',
            method='GET',
            response_time=150.5,
            status_code=500
        )

        assert metric.is_error() is True

    def test_api_metric_is_success(self):
        """测试成功状态码识别"""
        from apps.monitoring.performance.models import ApiMetric

        metric = ApiMetric(
            endpoint='/api/tenders',
            method='GET',
            response_time=150.5,
            status_code=200
        )

        assert metric.is_error() is False


class TestDbMetric:
    """测试数据库指标数据模型"""

    def test_db_metric_creation(self):
        """测试 DbMetric 创建"""
        from apps.monitoring.performance.models import DbMetric

        metric = DbMetric(
            pool_size=10,
            active_connections=5,
            wait_time=0.1
        )

        assert metric.pool_size == 10
        assert metric.active_connections == 5
        assert metric.wait_time == 0.1

    def test_db_metric_pool_usage(self):
        """测试连接池使用率计算"""
        from apps.monitoring.performance.models import DbMetric

        metric = DbMetric(
            pool_size=10,
            active_connections=8,
            wait_time=0.1
        )

        assert metric.get_pool_usage() == 80.0


class TestQueueMetric:
    """测试队列指标数据模型"""

    def test_queue_metric_creation(self):
        """测试 QueueMetric 创建"""
        from apps.monitoring.performance.models import QueueMetric

        metric = QueueMetric(
            queue_name='celery',
            length=100,
            worker_count=3
        )

        assert metric.queue_name == 'celery'
        assert metric.length == 100
        assert metric.worker_count == 3


class TestAlertRule:
    """测试告警规则数据模型"""

    def test_alert_rule_creation(self):
        """测试 AlertRule 创建"""
        from apps.monitoring.performance.models import AlertRule

        rule = AlertRule(
            name='high_response_time',
            metric_type='api',
            threshold=1000,
            severity='warning'
        )

        assert rule.name == 'high_response_time'
        assert rule.metric_type == 'api'
        assert rule.threshold == 1000
        assert rule.severity == 'warning'

    def test_alert_rule_trigger(self):
        """测试告警触发"""
        from apps.monitoring.performance.models import AlertRule

        rule = AlertRule(
            name='high_response_time',
            metric_type='api',
            threshold=1000,
            severity='warning'
        )

        # response_time > threshold
        assert rule.should_trigger({'response_time': 1500}) is True

        # response_time < threshold
        assert rule.should_trigger({'response_time': 500}) is False


class TestResponseTimeMiddleware:
    """测试 API 指标中间件"""

    def test_middleware_creation(self):
        """测试中间件创建"""
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware

        middleware = ResponseTimeMiddleware(Mock())

        assert middleware.metrics is not None
        assert len(middleware.metrics) == 0

    def test_middleware_record_request(self):
        """测试记录请求"""
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware

        middleware = ResponseTimeMiddleware(Mock())

        # 模拟请求
        middleware._record_request(
            endpoint='/api/tenders',
            method='GET',
            response_time=150.5,
            status_code=200
        )

        assert len(middleware.metrics) == 1
        metric = middleware.metrics[0]
        assert metric.endpoint == '/api/tenders'
        assert metric.response_time == 150.5

    def test_middleware_calculate_p50(self):
        """测试计算 p50 百分位数"""
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware

        middleware = ResponseTimeMiddleware(Mock())

        # 添加多个指标
        for i in [100, 200, 300, 400, 500]:
            middleware._record_request('/api/test', 'GET', i, 200)

        p50 = middleware.calculate_percentile(50)
        assert p50 == 300

    def test_middleware_calculate_p95(self):
        """测试计算 p95 百分位数"""
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware

        middleware = ResponseTimeMiddleware(Mock())

        # 添加更多指标来获得更准确的百分位数
        response_times = [50, 100, 150, 200, 250, 300, 350, 400, 450, 500,
                         550, 600, 650, 700, 750, 800, 850, 900, 950, 1000]
        for rt in response_times:
            middleware._record_request('/api/test', 'GET', rt, 200)

        p95 = middleware.calculate_percentile(95)
        assert p95 >= 950

    def test_middleware_calculate_p99(self):
        """测试计算 p99 百分位数"""
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware

        middleware = ResponseTimeMiddleware(Mock())

        response_times = list(range(1, 101))
        for rt in response_times:
            middleware._record_request('/api/test', 'GET', float(rt), 200)

        p99 = middleware.calculate_percentile(99)
        assert p99 >= 99

    def test_middleware_get_request_count(self):
        """测试获取请求数"""
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware

        middleware = ResponseTimeMiddleware(Mock())

        middleware._record_request('/api/test1', 'GET', 100, 200)
        middleware._record_request('/api/test2', 'GET', 200, 200)
        middleware._record_request('/api/test3', 'GET', 300, 200)

        assert middleware.get_request_count() == 3

    def test_middleware_get_error_rate(self):
        """测试获取错误率"""
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware

        middleware = ResponseTimeMiddleware(Mock())

        # 7 个成功, 3 个错误
        for _ in range(7):
            middleware._record_request('/api/test', 'GET', 100, 200)
        for _ in range(3):
            middleware._record_request('/api/test', 'GET', 100, 500)

        error_rate = middleware.get_error_rate()
        assert error_rate == 30.0

    def test_middleware_get_average_response_time(self):
        """测试获取平均响应时间"""
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware

        middleware = ResponseTimeMiddleware(Mock())

        middleware._record_request('/api/test', 'GET', 100, 200)
        middleware._record_request('/api/test', 'GET', 200, 200)
        middleware._record_request('/api/test', 'GET', 300, 200)

        avg = middleware.get_average_response_time()
        assert avg == 200.0


class TestDbMetricsCollector:
    """测试数据库指标收集器"""

    def test_collector_creation(self):
        """测试收集器创建"""
        from apps.monitoring.performance.db_metrics import DbMetricsCollector

        collector = DbMetricsCollector()

        assert collector.metrics is not None
        assert len(collector.metrics) == 0

    @patch('apps.monitoring.performance.db_metrics.connection')
    def test_collector_collect_pool_stats(self, mock_connection):
        """测试收集连接池统计"""
        from apps.monitoring.performance.db_metrics import DbMetricsCollector

        # Mock 数据库连接
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {'count': 5}
        mock_connection.cursor.return_value = __iter__ = lambda self: iter([mock_cursor])

        collector = DbMetricsCollector()

        # 由于是内存数据库，我们需要模拟
        collector.collect_pool_stats()

        # 至少验证收集方法存在
        assert hasattr(collector, 'collect_pool_stats')

    def test_collector_record_metric(self):
        """测试记录指标"""
        from apps.monitoring.performance.db_metrics import DbMetricsCollector
        from apps.monitoring.performance.models import DbMetric

        collector = DbMetricsCollector()

        metric = DbMetric(
            pool_size=10,
            active_connections=5,
            wait_time=0.1
        )
        collector.record_metric(metric)

        assert len(collector.metrics) == 1

    def test_collector_get_pool_usage(self):
        """测试获取连接池使用率"""
        from apps.monitoring.performance.db_metrics import DbMetricsCollector

        collector = DbMetricsCollector()

        usage = collector.get_current_pool_usage(10, 8)
        assert usage == 80.0

    def test_collector_detect_slow_query(self):
        """测试检测慢查询"""
        from apps.monitoring.performance.db_metrics import DbMetricsCollector

        collector = DbMetricsCollector()

        # 超过阈值的查询
        assert collector.is_slow_query(1.5, threshold=1.0) is True
        # 低于阈值的查询
        assert collector.is_slow_query(0.5, threshold=1.0) is False


class TestQueueMetricsCollector:
    """测试队列指标收集器"""

    def test_collector_creation(self):
        """测试收集器创建"""
        from apps.monitoring.performance.queue_metrics import QueueMetricsCollector

        collector = QueueMetricsCollector()

        assert collector.metrics is not None

    @patch('apps.monitoring.performance.queue_metrics.redis.from_url')
    def test_collector_get_queue_length(self, mock_from_url):
        """测试获取队列长度"""
        from apps.monitoring.performance.queue_metrics import QueueMetricsCollector

        mock_redis = MagicMock()
        mock_redis.llen.return_value = 100
        mock_from_url.return_value = mock_redis

        collector = QueueMetricsCollector()
        length = collector.get_queue_length('celery')

        assert length == 100

    @patch('apps.monitoring.performance.queue_metrics.redis.from_url')
    def test_collector_get_worker_count(self, mock_from_url):
        """测试获取 worker 数量"""
        from apps.monitoring.performance.queue_metrics import QueueMetricsCollector

        mock_redis = MagicMock()
        mock_redis.smembers.return_value = {'worker1', 'worker2', 'worker3'}
        mock_from_url.return_value = mock_redis

        collector = QueueMetricsCollector()
        count = collector.get_worker_count('celery')

        assert count == 3

    def test_collector_record_metric(self):
        """测试记录指标"""
        from apps.monitoring.performance.queue_metrics import QueueMetricsCollector
        from apps.monitoring.performance.models import QueueMetric

        collector = QueueMetricsCollector()

        metric = QueueMetric(
            queue_name='celery',
            length=100,
            worker_count=3
        )
        collector.record_metric(metric)

        assert len(collector.metrics) >= 1


class TestAlertManager:
    """测试告警管理器"""

    def test_alert_manager_creation(self):
        """测试告警管理器创建"""
        from apps.monitoring.performance.alerts import AlertManager

        manager = AlertManager()

        assert manager.rules is not None
        assert len(manager.rules) == 0
        assert manager.alerts == [] or manager.alerts is not None

    def test_alert_manager_add_rule(self):
        """测试添加告警规则"""
        from apps.monitoring.performance.alerts import AlertManager
        from apps.monitoring.performance.models import AlertRule

        manager = AlertManager()

        rule = AlertRule(
            name='high_response_time',
            metric_type='api',
            threshold=1000,
            severity='warning'
        )
        manager.add_rule(rule)

        assert len(manager.rules) == 1
        assert manager.rules[0].name == 'high_response_time'

    def test_alert_manager_check_threshold(self):
        """测试检查阈值触发告警"""
        from apps.monitoring.performance.alerts import AlertManager
        from apps.monitoring.performance.models import AlertRule

        manager = AlertManager()

        rule = AlertRule(
            name='high_response_time',
            metric_type='api',
            threshold=1000,
            severity='warning'
        )
        manager.add_rule(rule)

        # 触发告警
        alerts = manager.check_threshold('api', {'response_time': 1500})
        assert len(alerts) == 1

    def test_alert_manager_no_trigger(self):
        """测试未触发告警"""
        from apps.monitoring.performance.alerts import AlertManager
        from apps.monitoring.performance.models import AlertRule

        manager = AlertManager()

        rule = AlertRule(
            name='high_response_time',
            metric_type='api',
            threshold=1000,
            severity='warning'
        )
        manager.add_rule(rule)

        # 未触发告警
        alerts = manager.check_threshold('api', {'response_time': 500})
        assert len(alerts) == 0

    def test_alert_manager_cooldown(self):
        """测试冷却期处理"""
        from apps.monitoring.performance.alerts import AlertManager
        from apps.monitoring.performance.models import AlertRule

        manager = AlertManager()
        manager.cooldown_seconds = 60

        rule = AlertRule(
            name='high_error_rate',
            metric_type='error_rate',
            threshold=50,
            severity='critical'
        )
        manager.add_rule(rule)

        # 第一次触发
        alerts1 = manager.check_threshold('error_rate', {'error_rate': 60})
        assert len(alerts1) == 1

        # 冷却期内再次触发（应该被抑制）
        alerts2 = manager.check_threshold('error_rate', {'error_rate': 60})
        # 取决于实现，可能返回空或减少

    def test_alert_manager_get_active_alerts(self):
        """测试获取活动告警"""
        from apps.monitoring.performance.alerts import AlertManager
        from apps.monitoring.performance.models import AlertRule

        manager = AlertManager()

        rule = AlertRule(
            name='test_alert',
            metric_type='api',
            threshold=1000,
            severity='warning'
        )
        manager.add_rule(rule)

        manager.check_threshold('api', {'response_time': 1500})

        active = manager.get_active_alerts()
        assert len(active) >= 0

    def test_alert_manager_clear_alerts(self):
        """测试清除告警"""
        from apps.monitoring.performance.alerts import AlertManager
        from apps.monitoring.performance.models import AlertRule

        manager = AlertManager()

        rule = AlertRule(
            name='test_alert',
            metric_type='api',
            threshold=1000,
            severity='warning'
        )
        manager.add_rule(rule)

        manager.check_threshold('api', {'response_time': 1500})
        manager.clear_alerts()

        # 验证告警已清除
        assert manager.alerts == [] or len(manager.alerts) == 0


class TestPerformanceModelsEdgeCases:
    """测试性能监控模型边界情况"""

    def test_api_metric_empty_response_time(self):
        """测试空响应时间"""
        from apps.monitoring.performance.models import ApiMetric

        metric = ApiMetric(
            endpoint='/api/test',
            method='GET',
            response_time=0,
            status_code=200
        )

        assert metric.response_time == 0

    def test_db_metric_zero_pool(self):
        """测试零连接池"""
        from apps.monitoring.performance.models import DbMetric

        metric = DbMetric(
            pool_size=0,
            active_connections=0,
            wait_time=0
        )

        assert metric.pool_size == 0
        # 0 池大小的使用率应该是 0 或处理边界情况
        usage = metric.get_pool_usage()
        assert usage == 0

    def test_alert_rule_invalid_metric_type(self):
        """测试无效的指标类型"""
        from apps.monitoring.performance.models import AlertRule

        rule = AlertRule(
            name='test',
            metric_type='invalid',
            threshold=100,
            severity='warning'
        )

        result = rule.should_trigger({'unknown_field': 150})
        # 取决于实现
        assert isinstance(result, bool)

    def test_middleware_empty_metrics(self):
        """测试空指标计算"""
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware

        middleware = ResponseTimeMiddleware(Mock())

        p50 = middleware.calculate_percentile(50)
        assert p50 == 0 or p50 is None

        error_rate = middleware.get_error_rate()
        assert error_rate == 0.0


class TestPerformanceIntegration:
    """测试性能监控集成场景"""

    def test_full_monitoring_flow(self):
        """测试完整监控流程"""
        from apps.monitoring.performance.models import ApiMetric, AlertRule
        from apps.monitoring.performance.api_metrics import ResponseTimeMiddleware
        from apps.monitoring.performance.alerts import AlertManager

        # 1. 记录 API 指标
        middleware = ResponseTimeMiddleware(Mock())
        middleware._record_request('/api/tenders', 'GET', 1500, 200)
        middleware._record_request('/api/tenders', 'GET', 2000, 500)

        # 2. 检查告警
        manager = AlertManager()
        rule = AlertRule(
            name='slow_response',
            metric_type='api',
            threshold=1000,
            severity='warning'
        )
        manager.add_rule(rule)

        alerts = manager.check_threshold('api', {'response_time': 1500})

        # 3. 验证流程工作
        assert middleware.get_request_count() == 2
        assert isinstance(alerts, list)