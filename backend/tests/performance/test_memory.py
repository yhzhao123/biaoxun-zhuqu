"""
Memory Usage Tests - TDD Cycle 25

测试 deer-flow Tools 内存使用:
- 内存使用监控
- 内存泄漏检测
- 大数据处理
"""
import asyncio
import gc
import sys
from unittest.mock import AsyncMock, patch

import pytest


class TestMemoryUsageMonitoring:
    """测试内存使用监控"""

    @pytest.mark.asyncio
    async def test_memory_usage_tracking(self):
        """测试内存使用追踪"""
        from apps.crawler.deer_flow.performance import MemoryMonitor

        monitor = MemoryMonitor()

        # 获取初始内存
        initial_memory = monitor.get_current_memory()

        assert initial_memory > 0

    @pytest.mark.asyncio
    async def test_memory_increase_tracking(self):
        """测试内存增量追踪"""
        from apps.crawler.deer_flow.performance import MemoryMonitor

        monitor = MemoryMonitor()

        # 记录初始内存
        monitor.record_baseline()

        # 执行一些操作
        data = [i for i in range(10000)]

        # 获取当前内存
        current = monitor.get_current_memory()

        # 记录内存使用
        monitor.record_memory_usage("test_operation")

        # 获取统计
        stats = monitor.get_memory_stats()

        # stats 包含 baseline_mb 和 current_mb
        assert "baseline_mb" in stats or "current_mb" in stats


class TestMemoryLeakDetection:
    """测试内存泄漏检测"""

    @pytest.mark.asyncio
    async def test_no_memory_leak_in_repeated_calls(self):
        """测试重复调用无内存泄漏"""
        from apps.crawler.tools.detail_fetcher_tool import DetailFetcherTool
        from apps.crawler.deer_flow.performance import MemoryMonitor

        monitor = MemoryMonitor()
        monitor.record_baseline()

        tool = DetailFetcherTool()

        list_item = {
            "url": "http://example.com/tender/1",
            "title": "Test Tender"
        }

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            async def fast_fetch(item):
                await asyncio.sleep(0.01)
                from types import SimpleNamespace
                return SimpleNamespace(
                    url=item.get("url"),
                    html="<html>Test</html>",
                    attachments=[],
                    main_pdf_content=None,
                    main_pdf_url=None,
                    main_pdf_filename=None,
                    list_data={}
                )

            mock_fetch.side_effect = fast_fetch

            # 重复执行多次
            for _ in range(10):
                await tool.fetch(list_item, use_cache=False)

            # 强制垃圾回收
            gc.collect()

            # 检查内存不应大幅增长（允许一定波动）
            current = monitor.get_current_memory()
            baseline = monitor.get_baseline()

            # 内存增长不应超过 100MB
            if baseline > 0:
                growth = (current - baseline) / (1024 * 1024)
                assert growth < 100, f"Memory grew by {growth:.2f}MB - possible leak"

    @pytest.mark.asyncio
    async def test_cache_memory_management(self):
        """测试缓存内存管理"""
        from apps.crawler.tools.list_fetcher_tool import ListFetcherTool
        from apps.crawler.agents.schema import ExtractionStrategy
        from apps.crawler.deer_flow.performance import MemoryMonitor

        monitor = MemoryMonitor()
        initial_memory = monitor.get_current_memory()

        tool = ListFetcherTool()

        strategy = ExtractionStrategy(
            source_name="test",
            site_type="api",
            max_pages=1,
        )

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = [
                {"title": f"Item {i}", "url": f"http://example.com/{i}"}
                for i in range(50)
            ]

            # 执行多次查询，填充缓存
            for _ in range(3):
                await tool.fetch(strategy, max_pages=1)

            # 缓存应该能正常工作
            gc.collect()

            # 内存应该合理（不应该无限增长）
            final_memory = monitor.get_current_memory()
            memory_growth = (final_memory - initial_memory) / (1024 * 1024)

            assert memory_growth < 50, f"Cache memory grew by {memory_growth:.2f}MB"


class TestLargeDataHandling:
    """测试大数据处理"""

    @pytest.mark.asyncio
    async def test_large_list_fetch_memory(self):
        """测试大量列表项的内存使用"""
        from apps.crawler.tools.list_fetcher_tool import ListFetcherTool
        from apps.crawler.agents.schema import ExtractionStrategy
        from apps.crawler.deer_flow.performance import MemoryMonitor

        monitor = MemoryMonitor()
        monitor.record_baseline()

        tool = ListFetcherTool()

        # 模拟大量数据
        large_item_list = [
            {"title": f"项目{i}", "url": f"http://example.com/{i}"}
            for i in range(1000)
        ]

        strategy = ExtractionStrategy(
            source_name="test_large",
            site_type="api",
            max_pages=10,
        )

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = large_item_list

            result = await tool.fetch(strategy, max_pages=10)

            assert result.success is True
            assert len(result.items) == 1000

        gc.collect()

    @pytest.mark.asyncio
    async def test_large_batch_fetch(self):
        """测试大批量详情页获取"""
        from apps.crawler.tools.detail_fetcher_tool import DetailFetcherTool

        tool = DetailFetcherTool()

        # 准备大量数据
        list_items = [
            {"url": f"http://example.com/tender/{i}", "title": f"Tender {i}"}
            for i in range(100)
        ]

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            async def fast_fetch(item):
                await asyncio.sleep(0.01)
                from types import SimpleNamespace
                return SimpleNamespace(
                    url=item.get("url"),
                    html="<html>" + "x" * 1000 + "</html>",
                    attachments=[],
                    main_pdf_content=None,
                    main_pdf_url=None,
                    main_pdf_filename=None,
                    list_data={}
                )

            mock_fetch.side_effect = fast_fetch

            # 批量获取
            results = await tool.fetch_batch(list_items, max_concurrent=10)

            assert len(results) == 100
            success_count = sum(1 for r in results if r.success)
            assert success_count == 100


class TestMemoryMonitorIntegration:
    """测试内存监控集成"""

    def test_memory_monitor_creation(self):
        """测试内存监控器创建"""
        from apps.crawler.deer_flow.performance import MemoryMonitor

        monitor = MemoryMonitor()

        assert monitor is not None
        assert hasattr(monitor, 'get_current_memory')
        assert hasattr(monitor, 'record_baseline')

    def test_memory_stats(self):
        """测试内存统计"""
        from apps.crawler.deer_flow.performance import MemoryMonitor

        monitor = MemoryMonitor()

        # 记录基线
        monitor.record_baseline()

        # 执行操作
        data = [1, 2, 3]

        # 记录内存使用
        monitor.record_memory_usage("test")

        # 获取统计
        stats = monitor.get_memory_stats()

        assert isinstance(stats, dict)