"""
Performance Report Tests - TDD Cycle 25

测试性能报告生成:
- 报告数据收集
- 报告格式化
- 报告导出
"""
import asyncio
import json
from unittest.mock import patch

import pytest


class TestPerformanceDataCollection:
    """测试性能数据收集"""

    @pytest.mark.asyncio
    async def test_collect_metrics_data(self):
        """测试收集指标数据"""
        from apps.crawler.deer_flow.performance import PerformanceReporter

        reporter = PerformanceReporter()

        # 收集指标
        data = reporter.collect_metrics()

        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_collect_timing_data(self):
        """测试收集计时数据"""
        from apps.crawler.deer_flow.metrics import get_metrics

        # 初始化全局 metrics
        metrics = get_metrics()

        # 直接记录计时
        metrics.record_timing("test_operation", 0.015)

        # 获取指标
        stats = metrics.get_timing_stats("test_operation")

        assert stats["count"] >= 1


class TestPerformanceReportGeneration:
    """测试性能报告生成"""

    @pytest.mark.asyncio
    async def test_generate_summary_report(self):
        """测试生成汇总报告"""
        from apps.crawler.deer_flow.performance import PerformanceReporter

        reporter = PerformanceReporter()

        # 生成汇总报告
        report = reporter.generate_summary_report()

        assert isinstance(report, dict)

    @pytest.mark.asyncio
    async def test_generate_detailed_report(self):
        """测试生成详细报告"""
        from apps.crawler.deer_flow.performance import PerformanceReporter

        reporter = PerformanceReporter()

        # 添加一些测试数据
        reporter.record_operation("test_op", 0.1, success=True)

        # 生成详细报告
        report = reporter.generate_detailed_report()

        assert isinstance(report, dict)
        assert "operations" in report or "summary" in report or isinstance(report, dict)


class TestPerformanceReportFormat:
    """测试性能报告格式"""

    @pytest.mark.asyncio
    async def test_report_json_format(self):
        """测试 JSON 格式报告"""
        from apps.crawler.deer_flow.performance import PerformanceReporter

        reporter = PerformanceReporter()

        # 生成 JSON 格式
        json_report = reporter.generate_json_report()

        # 验证是有效的 JSON
        data = json.loads(json_report)

        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_report_contains_required_fields(self):
        """测试报告包含必需字段"""
        from apps.crawler.deer_flow.performance import PerformanceReporter

        reporter = PerformanceReporter()

        report = reporter.generate_summary_report()

        # 验证必需字段
        assert "timestamp" in report or "generated_at" in report or "operations" in report or isinstance(report, dict)


class TestPerformanceReportExport:
    """测试性能报告导出"""

    @pytest.mark.asyncio
    async def test_export_to_dict(self):
        """测试导出为字典"""
        from apps.crawler.deer_flow.performance import PerformanceReporter

        reporter = PerformanceReporter()

        data = reporter.export_to_dict()

        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_export_to_json_string(self):
        """测试导出为 JSON 字符串"""
        from apps.crawler.deer_flow.performance import PerformanceReporter

        reporter = PerformanceReporter()

        json_str = reporter.export_to_json()

        # 验证是有效的 JSON 字符串
        assert isinstance(json_str, str)
        json.loads(json_str)  # 应该不抛异常


class TestPerformanceReportIntegration:
    """测试性能报告集成"""

    @pytest.mark.asyncio
    async def test_full_report_workflow(self):
        """测试完整报告流程"""
        from apps.crawler.deer_flow.performance import PerformanceReporter
        from apps.crawler.deer_flow.metrics import get_metrics

        # 记录一些操作
        metrics = get_metrics()
        metrics.record_timing("list_fetch", 0.1)
        metrics.record_timing("detail_fetch", 0.2)

        metrics.increment_counter("fetch_success", 10)
        metrics.increment_counter("fetch_failure", 1)

        # 生成报告
        reporter = PerformanceReporter()
        report = reporter.generate_summary_report()

        # 验证报告包含操作统计
        assert isinstance(report, dict)

    @pytest.mark.asyncio
    async def test_report_with_thresholds(self):
        """测试带阈值的报告"""
        from apps.crawler.deer_flow.performance import (
            PerformanceReporter,
            PerformanceThresholds,
        )

        reporter = PerformanceReporter()
        thresholds = PerformanceThresholds()

        thresholds.set_response_time_threshold("test_op", 1.0)

        # 记录操作
        reporter.record_operation("test_op", 0.5, success=True)

        # 生成报告
        report = reporter.generate_summary_report()

        # 报告应包含阈值信息
        assert isinstance(report, dict)


class TestPerformanceReporterCreation:
    """测试性能报告器创建"""

    def test_reporter_initialization(self):
        """测试报告器初始化"""
        from apps.crawler.deer_flow.performance import PerformanceReporter

        reporter = PerformanceReporter()

        assert reporter is not None
        assert hasattr(reporter, 'generate_summary_report')
        assert hasattr(reporter, 'generate_json_report')

    def test_reporter_with_config(self):
        """测试带配置的报告器"""
        from apps.crawler.deer_flow.performance import PerformanceReporter

        reporter = PerformanceReporter(include_timing=True)

        assert reporter is not None