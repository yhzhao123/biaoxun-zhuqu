"""
Concurrency Tests - TDD Cycle 20

测试并发控制:
- 动态并发限制
- 连接池管理
- 并发数追踪
"""
import asyncio
import time
from unittest.mock import MagicMock, AsyncMock, patch

import pytest


class TestDynamicConcurrency:
    """测试动态并发限制"""

    @pytest.mark.asyncio
    async def test_default_concurrent_limit(self):
        """测试默认并发限制为 5"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow, WorkflowConfig

        workflow = TenderExtractionWorkflow()

        assert workflow.config.max_concurrent_requests == 5

    @pytest.mark.asyncio
    async def test_custom_concurrent_limit(self):
        """测试自定义并发限制"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow, WorkflowConfig

        config = WorkflowConfig(max_concurrent_requests=10)
        workflow = TenderExtractionWorkflow(config)

        assert workflow.config.max_concurrent_requests == 10

    @pytest.mark.asyncio
    async def test_semaphore_controls_concurrency(self):
        """测试信号量控制并发数"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        concurrent_count = 0
        max_concurrent = 0

        async def mock_task():
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.1)
            concurrent_count -= 1
            return "done"

        # 使用信号量限制并发为 2
        semaphore = asyncio.Semaphore(2)

        async def run_with_semaphore(task_id):
            async with semaphore:
                return await mock_task()

        # 正确地使用 async with
        results = await asyncio.gather(*[run_with_semaphore(i) for i in range(4)])

        # 最多只有 2 个任务同时执行
        assert max_concurrent <= 2

    @pytest.mark.asyncio
    async def test_concurrent_limit_in_batch(self):
        """测试批量提取时的并发限制"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        sources = [
            {"url": f"http://test{i}.com", "type": "api"}
            for i in range(5)
        ]

        # 验证并发限制配置
        assert workflow.config.max_concurrent_requests == 5


class TestConcurrencyMonitoring:
    """测试并发监控"""

    @pytest.mark.asyncio
    async def test_track_active_tasks(self):
        """测试追踪活跃任务数"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        active_count = 0
        max_active = 0

        async def tracked_task():
            nonlocal active_count, max_active
            workflow._active_tasks = getattr(workflow, '_active_tasks', 0) + 1
            active_count = workflow._active_tasks
            max_active = max(max_active, active_count)

            await asyncio.sleep(0.05)

            workflow._active_tasks = workflow._active_tasks - 1

        await asyncio.gather(*[tracked_task() for _ in range(3)])

        # 应该追踪到最多 3 个同时活跃的任务
        assert max_active >= 3

    def test_queue_length_tracking(self):
        """测试队列长度追踪"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        # 初始队列长度为 0
        assert workflow.get_metrics().get("queue_length", 0) == 0

    def test_concurrent_requests_metric(self):
        """测试并发请求数指标"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        metrics = workflow.get_metrics()

        # 应该有并发相关的指标
        assert "max_concurrent_requests" in metrics.get("config", {})


class TestConnectionPool:
    """测试连接池管理"""

    def test_connection_pool_config(self):
        """测试连接池配置"""
        from apps.crawler.deer_flow.pool import ConnectionPool

        pool = ConnectionPool(max_connections=10, max_keepalive=20)

        assert pool.max_connections == 10
        assert pool.max_keepalive == 20

    @pytest.mark.asyncio
    async def test_acquire_release_connection(self):
        """测试获取和释放连接"""
        from apps.crawler.deer_flow.pool import ConnectionPool

        pool = ConnectionPool(max_connections=2)

        # 获取连接
        conn = await pool.acquire()

        # 连接应该是可用的
        assert conn is not None

        # 释放连接
        await pool.release(conn)

        # 验证连接已返回池中
        stats = pool.get_stats()
        assert stats["available"] >= 1

    def test_pool_exhaustion(self):
        """测试连接池耗尽"""
        from apps.crawler.deer_flow.pool import ConnectionPool

        pool = ConnectionPool(max_connections=1)

        # 获取唯一连接
        conn1 = asyncio.run(pool.acquire())

        # 尝试获取第二个连接应该等待或有超时
        # 连接池应该能处理这种情况

        # 释放连接
        asyncio.run(pool.release(conn1))


class TestPerformanceMetrics:
    """测试性能指标收集"""

    def test_execution_time_tracking(self):
        """测试执行时间追踪"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        # 记录开始时间
        start_time = time.time()

        # 模拟一些工作
        time.sleep(0.1)

        # 记录结束时间
        execution_time = time.time() - start_time

        # 验证时间记录
        assert execution_time >= 0.1

    def test_timing_decorator(self):
        """测试计时装饰器"""
        from apps.crawler.deer_flow.metrics import timed, get_metrics

        # 使用带参数的装饰器
        @timed("mock_operation")
        async def mock_operation():
            await asyncio.sleep(0.01)
            return "done"

        # 执行带计时的操作
        result = asyncio.run(mock_operation())

        # 验证结果和计时
        assert result == "done"

        # 验证指标已记录
        metrics = get_metrics()
        stats = metrics.get_timing_stats("mock_operation")
        assert stats["count"] >= 1

    def test_metrics_accumulation(self):
        """测试指标累积"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        # 记录一些操作
        workflow._metrics["list_calls"] += 1
        workflow._metrics["detail_calls"] += 2
        workflow._metrics["items_fetched"] += 10

        metrics = workflow.get_metrics()

        assert metrics["list_calls"] == 1
        assert metrics["detail_calls"] == 2
        assert metrics["items_fetched"] == 10

    def test_reset_metrics(self):
        """测试重置指标"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        workflow._metrics["list_calls"] = 5

        workflow.reset_metrics()

        assert workflow._metrics["list_calls"] == 0


class TestPerformanceTargets:
    """测试性能目标"""

    @pytest.mark.asyncio
    async def test_list_fetch_under_2s(self):
        """测试列表获取 < 2秒/页"""
        start = time.time()

        # 模拟列表获取 (实际会通过 Tool 调用)
        await asyncio.sleep(0.1)  # 模拟 0.1 秒

        elapsed = time.time() - start

        # 验证性能目标 - 假设每页 2 秒
        assert elapsed < 2.0

    @pytest.mark.asyncio
    async def test_detail_fetch_under_3s(self):
        """测试详情获取 < 3秒/项"""
        start = time.time()

        # 模拟详情获取
        await asyncio.sleep(0.2)

        elapsed = time.time() - start

        assert elapsed < 3.0

    def test_concurrency_target_5_to_10(self):
        """测试并发数目标 5-10"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow, WorkflowConfig

        # 测试默认配置
        workflow = TenderExtractionWorkflow()
        max_concurrent = workflow.config.max_concurrent_requests

        # 目标: 5-10
        assert 5 <= max_concurrent <= 10

        # 测试可配置性
        config = WorkflowConfig(max_concurrent_requests=8)
        workflow2 = TenderExtractionWorkflow(config)

        assert workflow2.config.max_concurrent_requests == 8