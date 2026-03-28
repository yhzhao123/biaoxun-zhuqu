"""
RetryMechanismAgent 测试

TDD Cycle 7: 重试机制智能体测试
"""
import pytest
import asyncio
import time
from unittest.mock import Mock, AsyncMock, patch, call
from typing import List

from apps.crawler.agents.workers.retry_agent import (
    RetryMechanismAgent,
    RetryConfig,
    CircuitBreaker,
    FailedItem,
    ErrorType,
    get_retry_agent,
)


class TestErrorType:
    """ErrorType 测试"""

    def test_error_type_values(self):
        """测试错误类型枚举值"""
        assert ErrorType.RATE_LIMIT.name == "RATE_LIMIT"
        assert ErrorType.SERVICE_UNAVAILABLE.name == "SERVICE_UNAVAILABLE"
        assert ErrorType.TIMEOUT.name == "TIMEOUT"
        assert ErrorType.CONNECTION_ERROR.name == "CONNECTION_ERROR"
        assert ErrorType.SERVER_ERROR.name == "SERVER_ERROR"
        assert ErrorType.UNKNOWN.name == "UNKNOWN"


class TestRetryConfig:
    """RetryConfig 测试"""

    def test_default_values(self):
        """测试默认值"""
        config = RetryConfig()

        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
        assert config.circuit_breaker_threshold == 5
        assert config.circuit_breaker_timeout == 60.0

    def test_custom_values(self):
        """测试自定义值"""
        config = RetryConfig(
            max_retries=5,
            base_delay=2.0,
            max_delay=120.0,
            exponential_base=3.0,
            jitter=False,
            circuit_breaker_threshold=3,
            circuit_breaker_timeout=30.0,
        )

        assert config.max_retries == 5
        assert config.base_delay == 2.0
        assert config.max_delay == 120.0
        assert config.exponential_base == 3.0
        assert config.jitter is False
        assert config.circuit_breaker_threshold == 3
        assert config.circuit_breaker_timeout == 30.0


class TestCircuitBreaker:
    """CircuitBreaker 测试"""

    def test_initialization(self):
        """测试初始化"""
        cb = CircuitBreaker(threshold=5, timeout=60.0)

        assert cb.threshold == 5
        assert cb.timeout == 60.0
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.get_state() == "CLOSED"
        assert cb.is_open is False

    @pytest.mark.asyncio
    async def test_record_failure(self):
        """测试记录失败"""
        cb = CircuitBreaker(threshold=3, timeout=60.0)

        await cb.record_failure()
        assert cb.failure_count == 1
        assert cb.get_state() == "CLOSED"

        await cb.record_failure()
        assert cb.failure_count == 2
        assert cb.get_state() == "CLOSED"

        await cb.record_failure()
        assert cb.failure_count == 3
        assert cb.get_state() == "OPEN"

    @pytest.mark.asyncio
    async def test_record_success_resets(self):
        """测试记录成功重置熔断器"""
        cb = CircuitBreaker(threshold=3, timeout=60.0)

        await cb.record_failure()
        await cb.record_failure()
        assert cb.failure_count == 2

        await cb.record_success()
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.get_state() == "CLOSED"

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self):
        """测试达到阈值后熔断器打开"""
        cb = CircuitBreaker(threshold=2, timeout=60.0)

        await cb.record_failure()
        await cb.record_failure()

        assert cb.is_open is True
        assert cb.get_state() == "OPEN"

    @pytest.mark.asyncio
    async def test_circuit_half_open_after_timeout(self):
        """测试超时后进入半开状态"""
        cb = CircuitBreaker(threshold=2, timeout=0.1)  # 100ms超时

        await cb.record_failure()
        await cb.record_failure()
        assert cb.get_state() == "OPEN"

        # 等待超时
        await asyncio.sleep(0.15)
        assert cb.is_open is False  # 应该进入HALF_OPEN
        assert cb.get_state() == "HALF_OPEN"


class TestRetryMechanismAgent:
    """RetryMechanismAgent 测试"""

    def test_initialization(self):
        """测试初始化"""
        config = RetryConfig()
        agent = RetryMechanismAgent(config)

        assert agent.config == config
        assert agent.circuit_breaker is not None
        assert agent._failed_queues is not None
        assert agent._stats['total_attempts'] == 0

    def test_initialization_default_config(self):
        """测试默认配置初始化"""
        agent = RetryMechanismAgent()

        assert agent.config is not None
        assert agent.config.max_retries == 3

    def test_classify_error_rate_limit(self):
        """测试错误分类 - 限流"""
        agent = RetryMechanismAgent()

        error = Exception("429 Too Many Requests")
        assert agent._classify_error(error) == ErrorType.RATE_LIMIT

        error = Exception("Status code: 429")
        assert agent._classify_error(error) == ErrorType.RATE_LIMIT

    def test_classify_error_service_unavailable(self):
        """测试错误分类 - 服务不可用"""
        agent = RetryMechanismAgent()

        error = Exception("503 Service Unavailable")
        assert agent._classify_error(error) == ErrorType.SERVICE_UNAVAILABLE

    def test_classify_error_timeout(self):
        """测试错误分类 - 超时"""
        agent = RetryMechanismAgent()

        error = Exception("Request timeout")
        assert agent._classify_error(error) == ErrorType.TIMEOUT

        error = Exception("Connection timed out")
        assert agent._classify_error(error) == ErrorType.TIMEOUT

    def test_classify_error_connection(self):
        """测试错误分类 - 连接错误"""
        agent = RetryMechanismAgent()

        error = Exception("Connection refused")
        assert agent._classify_error(error) == ErrorType.CONNECTION_ERROR

    def test_classify_error_server_error(self):
        """测试错误分类 - 服务器错误"""
        agent = RetryMechanismAgent()

        error = Exception("500 Internal Server Error")
        assert agent._classify_error(error) == ErrorType.SERVER_ERROR

        error = Exception("502 Bad Gateway")
        assert agent._classify_error(error) == ErrorType.SERVER_ERROR

    def test_classify_error_unknown(self):
        """测试错误分类 - 未知错误"""
        agent = RetryMechanismAgent()

        error = Exception("Some random error")
        assert agent._classify_error(error) == ErrorType.UNKNOWN

    def test_calculate_delay_without_jitter(self):
        """测试延迟计算 - 无抖动"""
        config = RetryConfig(jitter=False, base_delay=1.0, exponential_base=2.0)
        agent = RetryMechanismAgent(config)

        # 第0次尝试: 1.0 * 2^0 = 1.0
        assert agent._calculate_delay(0) == 1.0

        # 第1次尝试: 1.0 * 2^1 = 2.0
        assert agent._calculate_delay(1) == 2.0

        # 第2次尝试: 1.0 * 2^2 = 4.0
        assert agent._calculate_delay(2) == 4.0

    def test_calculate_delay_with_jitter(self):
        """测试延迟计算 - 有抖动"""
        config = RetryConfig(jitter=True, base_delay=1.0, exponential_base=2.0)
        agent = RetryMechanismAgent(config)

        delay = agent._calculate_delay(1)
        # 抖动后延迟应在 [0, 2.0] 范围内
        assert 0 <= delay <= 2.0

    def test_calculate_delay_respects_max_delay(self):
        """测试延迟计算 - 尊重最大延迟"""
        config = RetryConfig(
            jitter=False,
            base_delay=10.0,
            exponential_base=2.0,
            max_delay=50.0
        )
        agent = RetryMechanismAgent(config)

        # 第3次尝试: 10.0 * 2^3 = 80.0，但限制为50.0
        delay = agent._calculate_delay(3)
        assert delay == 50.0

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_first_try(self):
        """测试重试执行 - 首次成功"""
        agent = RetryMechanismAgent()
        mock_func = AsyncMock(return_value="success")

        result = await agent.execute_with_retry(mock_func, "arg1", key="value")

        assert result == "success"
        assert mock_func.call_count == 1
        mock_func.assert_called_once_with("arg1", key="value")

    @pytest.mark.asyncio
    async def test_execute_with_retry_success_after_retries(self):
        """测试重试执行 - 重试后成功"""
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)
        agent = RetryMechanismAgent(config)

        mock_func = AsyncMock(side_effect=[
            ValueError("First fail"),
            ValueError("Second fail"),
            "success"
        ])

        result = await agent.execute_with_retry(mock_func)

        assert result == "success"
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_all_attempts_failed(self):
        """测试重试执行 - 全部尝试失败"""
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        agent = RetryMechanismAgent(config)

        mock_func = AsyncMock(side_effect=ValueError("Always fails"))

        with pytest.raises(ValueError, match="Always fails"):
            await agent.execute_with_retry(mock_func)

        # max_retries + 1 (initial attempt)
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_execute_with_retry_sync_function(self):
        """测试重试执行 - 同步函数"""
        agent = RetryMechanismAgent()

        def sync_func(x):
            return x * 2

        result = await agent.execute_with_retry(sync_func, 5)

        assert result == 10

    @pytest.mark.asyncio
    async def test_failed_item_added_to_queue(self):
        """测试失败项目添加到队列"""
        config = RetryConfig(max_retries=1, base_delay=0.01, jitter=False)
        agent = RetryMechanismAgent(config)

        mock_func = AsyncMock(side_effect=ValueError("Test error"))

        with pytest.raises(ValueError):
            await agent.execute_with_retry(mock_func)

        # 检查失败队列
        failed_items = agent.get_failed_items()
        assert len(failed_items) == 1
        assert failed_items[0]['error_message'] == "Test error"

    @pytest.mark.asyncio
    async def test_get_failed_items_by_type(self):
        """测试按类型获取失败项目"""
        agent = RetryMechanismAgent()

        # 手动添加失败项目
        await agent.add_failed_item(
            {"url": "http://example.com"},
            "Rate limit exceeded",
            ErrorType.RATE_LIMIT
        )
        await agent.add_failed_item(
            {"url": "http://test.com"},
            "Connection refused",
            ErrorType.CONNECTION_ERROR
        )

        rate_limit_items = agent.get_failed_items_by_type(ErrorType.RATE_LIMIT)
        assert len(rate_limit_items) == 1
        assert rate_limit_items[0].error_type == ErrorType.RATE_LIMIT

    @pytest.mark.asyncio
    async def test_clear_failed_items(self):
        """测试清空失败队列"""
        agent = RetryMechanismAgent()

        await agent.add_failed_item(
            {"url": "http://example.com"},
            "Error",
            ErrorType.UNKNOWN
        )

        count = await agent.clear_failed_items()
        assert count == 1
        assert len(agent.get_failed_items()) == 0

    @pytest.mark.asyncio
    async def test_clear_failed_items_by_type(self):
        """测试按类型清空失败队列"""
        agent = RetryMechanismAgent()

        await agent.add_failed_item(
            {"url": "http://example.com"},
            "Rate limit",
            ErrorType.RATE_LIMIT
        )
        await agent.add_failed_item(
            {"url": "http://test.com"},
            "Timeout",
            ErrorType.TIMEOUT
        )

        count = await agent.clear_failed_items(ErrorType.RATE_LIMIT)
        assert count == 1

        all_items = agent.get_failed_items()
        assert len(all_items) == 1

    def test_get_stats(self):
        """测试获取统计信息"""
        agent = RetryMechanismAgent()

        stats = agent.get_stats()

        assert 'total_attempts' in stats
        assert 'circuit_breaker_state' in stats
        assert 'failed_queue_sizes' in stats
        assert stats['circuit_breaker_state'] == "CLOSED"

    @pytest.mark.asyncio
    async def test_reset(self):
        """测试重置"""
        agent = RetryMechanismAgent()

        await agent.add_failed_item({"url": "test"}, "error", ErrorType.UNKNOWN)
        await agent.circuit_breaker.record_failure()
        await agent.circuit_breaker.record_failure()

        await agent.reset()

        assert len(agent.get_failed_items()) == 0
        assert agent.circuit_breaker.failure_count == 0
        assert agent.circuit_breaker.get_state() == "CLOSED"

    @pytest.mark.asyncio
    async def test_handle_rate_limit(self):
        """测试处理限流"""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0)
        agent = RetryMechanismAgent(config)

        await agent.handle_rate_limit(retry_after=5.0)

        assert agent._current_delay == 5.0

    @pytest.mark.asyncio
    async def test_handle_rate_limit_without_retry_after(self):
        """测试处理限流 - 无retry_after"""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=60.0)
        agent = RetryMechanismAgent(config)

        await agent.handle_rate_limit()

        # 应该指数增加
        assert agent._current_delay == 2.0


class TestFailedItem:
    """FailedItem 测试"""

    def test_to_dict(self):
        """测试转换为字典"""
        item = FailedItem(
            item_id="test_123",
            func=None,
            args=(),
            kwargs={},
            error_type=ErrorType.RATE_LIMIT,
            error_message="Rate limit exceeded",
            retry_count=2,
            last_attempt_time=time.time(),
        )

        item_dict = item.to_dict()

        assert item_dict['item_id'] == "test_123"
        assert item_dict['error_type'] == "RATE_LIMIT"
        assert item_dict['error_message'] == "Rate limit exceeded"
        assert item_dict['retry_count'] == 2


class TestGlobalAgent:
    """全局代理测试"""

    def test_get_retry_agent_singleton(self):
        """测试单例模式"""
        # 重置全局实例
        import apps.crawler.agents.workers.retry_agent as ra
        ra._retry_agent = None

        agent1 = get_retry_agent()
        agent2 = get_retry_agent()

        assert agent1 is agent2

    def test_get_retry_agent_with_config(self):
        """测试带配置获取代理"""
        import apps.crawler.agents.workers.retry_agent as ra
        ra._retry_agent = None

        config = RetryConfig(max_retries=5)
        agent = get_retry_agent(config)

        assert agent.config.max_retries == 5


class TestRetryAgentIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_retry_workflow(self):
        """测试完整重试工作流"""
        config = RetryConfig(
            max_retries=2,
            base_delay=0.01,
            jitter=False,
            circuit_breaker_threshold=5
        )
        agent = RetryMechanismAgent(config)

        call_count = 0

        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Temporary error")
            return "success"

        result = await agent.execute_with_retry(flaky_function)

        assert result == "success"
        assert call_count == 2

        stats = agent.get_stats()
        assert stats['total_attempts'] == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_with_retry(self):
        """测试熔断器与重试集成"""
        config = RetryConfig(
            max_retries=1,
            base_delay=0.01,
            jitter=False,
            circuit_breaker_threshold=2
        )
        agent = RetryMechanismAgent(config)

        # 第一次调用失败
        mock_func = AsyncMock(side_effect=ValueError("Error 1"))
        with pytest.raises(ValueError):
            await agent.execute_with_retry(mock_func)

        # 第二次调用失败
        mock_func = AsyncMock(side_effect=ValueError("Error 2"))
        with pytest.raises(ValueError):
            await agent.execute_with_retry(mock_func)

        # 熔断器应该打开
        assert agent.circuit_breaker.is_open is True

    @pytest.mark.asyncio
    async def test_retry_failed_items(self):
        """测试重试失败项目"""
        config = RetryConfig(max_retries=1, base_delay=0.01, jitter=False)
        agent = RetryMechanismAgent(config)

        success_count = 0

        async def process_item(item):
            nonlocal success_count
            success_count += 1

        # 添加失败项目
        await agent.add_failed_item(
            {"url": "http://example.com"},
            "Previous error",
            ErrorType.UNKNOWN
        )

        # 重试失败项目
        results = await agent.retry_failed_items(process_func=process_item)

        assert results['total'] == 1
        assert success_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
