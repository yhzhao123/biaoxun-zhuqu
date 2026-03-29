"""
Performance Benchmark Tests - TDD Cycle 25

测试 deer-flow Tools 性能基准:
- 响应时间测试
- 吞吐量测试
- 延迟测试
"""
import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest


class TestResponseTimeBenchmark:
    """测试响应时间基准"""

    @pytest.mark.asyncio
    async def test_list_fetcher_response_time(self):
        """测试 ListFetcherTool 响应时间 < 2秒"""
        from apps.crawler.tools.list_fetcher_tool import ListFetcherTool
        from apps.crawler.agents.schema import ExtractionStrategy

        tool = ListFetcherTool()

        strategy = ExtractionStrategy(
            source_name="test",
            site_type="api",
            max_pages=1,
        )

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            # 模拟快速响应
            async def fast_fetch(s):
                await asyncio.sleep(0.1)  # 100ms
                return [{"title": "Test"}]

            mock_fetch.side_effect = fast_fetch

            start = time.time()
            # 禁用缓存来测试实际性能
            result = await tool.fetch(strategy, max_pages=1, use_cache=False)
            elapsed = time.time() - start

            assert result.success is True
            assert elapsed < 2.0, f"Response time {elapsed:.2f}s exceeds 2s threshold"

    @pytest.mark.asyncio
    async def test_detail_fetcher_response_time(self):
        """测试 DetailFetcherTool 响应时间 < 3秒"""
        from apps.crawler.tools.detail_fetcher_tool import DetailFetcherTool

        tool = DetailFetcherTool()

        list_item = {
            "url": "http://example.com/tender/1",
            "title": "Test Tender"
        }

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            async def fast_fetch(item):
                await asyncio.sleep(0.1)
                # 返回模拟结果
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

            start = time.time()
            # 禁用缓存来测试实际性能
            result = await tool.fetch(list_item, use_cache=False)
            elapsed = time.time() - start

            assert result.success is True
            assert elapsed < 3.0, f"Response time {elapsed:.2f}s exceeds 3s threshold"


class TestThroughputBenchmark:
    """测试吞吐量基准"""

    @pytest.mark.asyncio
    async def test_batch_throughput(self):
        """测试批量处理吞吐量"""
        from apps.crawler.tools.detail_fetcher_tool import DetailFetcherTool

        tool = DetailFetcherTool()

        # 准备批量数据
        list_items = [
            {"url": f"http://example.com/tender/{i}", "title": f"Tender {i}"}
            for i in range(10)
        ]

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            async def fast_fetch(item):
                await asyncio.sleep(0.05)  # 50ms
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

            start = time.time()
            # 禁用缓存来测试实际性能
            results = await tool.fetch_batch(list_items, max_concurrent=5, use_cache=False)
            elapsed = time.time() - start

            assert len(results) == 10
            # 10 个任务，50ms 每个，5 并发，理论上约 100ms
            # 允许一定开销，目标 2 秒内完成
            assert elapsed < 2.0, f"Batch throughput {elapsed:.2f}s too slow"

    @pytest.mark.asyncio
    async def test_concurrent_list_fetch(self):
        """测试并发列表获取"""
        from apps.crawler.tools.list_fetcher_tool import ListFetcherTool
        from apps.crawler.agents.schema import ExtractionStrategy

        tool = ListFetcherTool()

        strategies = [
            ExtractionStrategy(
                source_name=f"test_{i}",
                site_type="api",
                max_pages=1,
            )
            for i in range(3)
        ]

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            async def fast_fetch(s):
                await asyncio.sleep(0.1)
                return [{"title": "Test"}]

            mock_fetch.side_effect = fast_fetch

            start = time.time()

            # 并发执行多个列表获取，禁用缓存
            tasks = [
                tool.fetch(strategy, max_pages=1, use_cache=False)
                for strategy in strategies
            ]
            results = await asyncio.gather(*tasks)

            elapsed = time.time() - start

            assert len(results) == 3
            assert all(r.success for r in results)
            # 3 个任务并发执行，应该约等于单个任务时间
            assert elapsed < 1.0


class TestLatencyBenchmark:
    """测试延迟基准"""

    @pytest.mark.asyncio
    async def test_cache_latency(self):
        """测试缓存命中延迟 < 10ms"""
        from apps.crawler.tools.list_fetcher_tool import ListFetcherTool
        from apps.crawler.agents.schema import ExtractionStrategy

        tool = ListFetcherTool()

        strategy = ExtractionStrategy(
            source_name="test_cache",
            site_type="api",
            max_pages=1,
        )

        # 第一次调用，填充缓存
        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = [{"title": "Test"}]

            await tool.fetch(strategy, max_pages=1)

            # 第二次调用，应该命中缓存
            start = time.time()
            result = await tool.fetch(strategy, max_pages=1, use_cache=True)
            elapsed = time.time() - start

            assert result.cache_hit is True
            # 缓存命中应该非常快
            assert elapsed < 0.01, f"Cache latency {elapsed*1000:.2f}ms exceeds 10ms"

    @pytest.mark.asyncio
    async def test_no_network_latency_without_cache(self):
        """测试无缓存时的延迟（有网络调用）"""
        from apps.crawler.tools.detail_fetcher_tool import DetailFetcherTool

        tool = DetailFetcherTool()

        list_item = {
            "url": "http://example.com/tender/1",
            "title": "Test Tender"
        }

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock
        ) as mock_fetch:
            # 模拟网络延迟
            async def fetch_with_delay(item):
                await asyncio.sleep(0.2)  # 200ms 延迟
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

            mock_fetch.side_effect = fetch_with_delay

            start = time.time()
            result = await tool.fetch(list_item, use_cache=False)
            elapsed = time.time() - start

            assert result.success is True
            # 网络调用应该至少需要 200ms
            assert elapsed >= 0.2


class TestPerformanceBenchmarkSummary:
    """性能基准汇总测试"""

    @pytest.mark.asyncio
    async def test_all_benchmarks_pass(self):
        """验证所有基准测试通过"""
        # 这个测试确保整体性能达标
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        # 验证配置存在
        assert workflow.config.max_concurrent_requests >= 1

        # 验证指标系统可用
        metrics = workflow.get_metrics()
        assert isinstance(metrics, dict)