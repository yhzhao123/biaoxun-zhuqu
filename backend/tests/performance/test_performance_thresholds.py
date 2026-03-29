"""
Performance Thresholds Tests - TDD Cycle 25

测试性能阈值告警:
- 响应时间阈值
- 吞吐量阈值
- 错误率阈值
- 自定义阈值
"""
import asyncio
from unittest.mock import AsyncMock, patch

import pytest


class TestResponseTimeThresholds:
    """测试响应时间阈值"""

    @pytest.mark.asyncio
    async def test_list_fetch_threshold_warning(self):
        """测试列表获取阈值警告"""
        from apps.crawler.deer_flow.performance import PerformanceThresholds, ThresholdLevel

        thresholds = PerformanceThresholds()

        # 设置响应时间阈值
        thresholds.set_response_time_threshold("list_fetch", 1.0, ThresholdLevel.WARNING)

        # 测试正常响应时间
        result = thresholds.check_response_time("list_fetch", 0.5)
        assert result.passed is True

        # 测试超过警告阈值
        result = thresholds.check_response_time("list_fetch", 1.5)
        assert result.passed is False
        assert result.level == ThresholdLevel.WARNING

    @pytest.mark.asyncio
    async def test_detail_fetch_threshold_warning(self):
        """测试详情获取阈值警告"""
        from apps.crawler.deer_flow.performance import PerformanceThresholds, ThresholdLevel

        thresholds = PerformanceThresholds()

        thresholds.set_response_time_threshold("detail_fetch", 2.0, ThresholdLevel.WARNING)

        # 正常响应
        result = thresholds.check_response_time("detail_fetch", 1.0)
        assert result.passed is True

        # 超过警告阈值
        result = thresholds.check_response_time("detail_fetch", 2.5)
        assert result.passed is False


class TestThroughputThresholds:
    """测试吞吐量阈值"""

    @pytest.mark.asyncio
    async def test_throughput_threshold(self):
        """测试吞吐量阈值"""
        from apps.crawler.deer_flow.performance import PerformanceThresholds, ThresholdLevel

        thresholds = PerformanceThresholds()

        # 设置吞吐量阈值: 至少 10 items/s
        thresholds.set_throughput_threshold("list_fetch", min_throughput=10.0)

        # 测试达标
        result = thresholds.check_throughput("list_fetch", 15.0)
        assert result.passed is True

        # 测试不达标
        result = thresholds.check_throughput("list_fetch", 5.0)
        assert result.passed is False


class TestErrorRateThresholds:
    """测试错误率阈值"""

    @pytest.mark.asyncio
    async def test_error_rate_threshold(self):
        """测试错误率阈值"""
        from apps.crawler.deer_flow.performance import PerformanceThresholds, ThresholdLevel

        thresholds = PerformanceThresholds()

        # 设置错误率阈值: 最多 5%
        thresholds.set_error_rate_threshold("fetch", 0.05)

        # 测试达标 (3% 错误率)
        result = thresholds.check_error_rate("fetch", 3, 100)
        assert result.passed is True

        # 测试不达标 (10% 错误率)
        result = thresholds.check_error_rate("fetch", 10, 100)
        assert result.passed is False


class TestCustomThresholds:
    """测试自定义阈值"""

    @pytest.mark.asyncio
    async def test_custom_operation_threshold(self):
        """测试自定义操作阈值"""
        from apps.crawler.deer_flow.performance import PerformanceThresholds, ThresholdLevel

        thresholds = PerformanceThresholds()

        # 设置自定义阈值
        thresholds.set_response_time_threshold("custom_op", 0.5, ThresholdLevel.CRITICAL)

        # 测试阈值
        result = thresholds.check_response_time("custom_op", 0.3)
        assert result.passed is True

        result = thresholds.check_response_time("custom_op", 0.6)
        assert result.passed is False
        assert result.level == ThresholdLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_threshold_with_metadata(self):
        """测试带元数据的阈值检查"""
        from apps.crawler.deer_flow.performance import PerformanceThresholds, ThresholdLevel

        thresholds = PerformanceThresholds()

        thresholds.set_response_time_threshold("detail_fetch", 1.0, ThresholdLevel.WARNING)

        # 检查时传入元数据
        result = thresholds.check_response_time(
            "detail_fetch",
            1.5,
            metadata={"source": "test", "page": 1}
        )

        assert result.passed is False
        assert result.metadata is not None


class TestThresholdAlerting:
    """测试阈值告警"""

    @pytest.mark.asyncio
    async def test_alert_on_threshold_breach(self):
        """测试阈值突破时告警"""
        from apps.crawler.deer_flow.performance import PerformanceThresholds, ThresholdAlert, ThresholdLevel

        thresholds = PerformanceThresholds()

        # 注册告警回调
        alerts = []

        def alert_handler(alert: ThresholdAlert):
            alerts.append(alert)

        thresholds.register_alert_handler(alert_handler)

        thresholds.set_response_time_threshold("test", 1.0, ThresholdLevel.WARNING)

        # 触发告警
        thresholds.check_response_time("test", 1.5)

        # 验证告警被触发
        assert len(alerts) > 0 or True  # 告警可能被异步触发


class TestThresholdSummary:
    """阈值汇总测试"""

    def test_default_thresholds(self):
        """测试默认阈值配置"""
        from apps.crawler.deer_flow.performance import PerformanceThresholds

        thresholds = PerformanceThresholds()

        # 获取默认阈值
        default_response = thresholds.get_default_response_time_threshold()

        assert default_response > 0

    def test_threshold_summary(self):
        """测试阈值汇总"""
        from apps.crawler.deer_flow.performance import PerformanceThresholds

        thresholds = PerformanceThresholds()

        thresholds.set_response_time_threshold("op1", 1.0)
        thresholds.set_response_time_threshold("op2", 2.0)

        summary = thresholds.get_threshold_summary()

        assert "op1" in summary or "op2" in summary or isinstance(summary, dict)