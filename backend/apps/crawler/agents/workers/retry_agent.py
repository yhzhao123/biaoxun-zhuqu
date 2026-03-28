"""
重试机制智能体

负责处理HTTP请求的重试逻辑，包括指数退避、抖动、熔断器模式等
"""
import logging
import asyncio
import random
import time
from typing import List, Dict, Any, Optional, Callable, Union, TypeVar, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from collections import defaultdict
from asyncio import Lock

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorType(Enum):
    """错误类型枚举"""
    RATE_LIMIT = auto()  # 429 Too Many Requests
    SERVICE_UNAVAILABLE = auto()  # 503 Service Unavailable
    TIMEOUT = auto()  # 请求超时
    CONNECTION_ERROR = auto()  # 连接错误
    SERVER_ERROR = auto()  # 5xx 服务器错误
    UNKNOWN = auto()  # 未知错误


@dataclass
class RetryConfig:
    """
    重试配置数据类

    Attributes:
        max_retries: 最大重试次数
        base_delay: 基础延迟（秒）
        max_delay: 最大延迟（秒）
        exponential_base: 指数基数
        jitter: 是否启用抖动
        circuit_breaker_threshold: 熔断器阈值（连续失败次数）
        circuit_breaker_timeout: 熔断器超时时间（秒）
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0


@dataclass
class FailedItem:
    """失败项目数据类"""
    item_id: str
    func: Callable
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    error_type: ErrorType
    error_message: str
    retry_count: int
    last_attempt_time: float
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含函数引用）"""
        return {
            'item_id': self.item_id,
            'error_type': self.error_type.name,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'last_attempt_time': self.last_attempt_time,
            'created_at': self.created_at,
        }


class CircuitBreaker:
    """
    熔断器模式实现

    当连续失败次数超过阈值时，暂时停止请求一段时间
    """

    def __init__(self, threshold: int = 5, timeout: float = 60.0):
        self.threshold = threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._lock = Lock()

    @property
    def is_open(self) -> bool:
        """检查熔断器是否打开"""
        if self._state == "OPEN":
            # 检查是否应该进入半开状态
            if self.last_failure_time is not None:
                elapsed = time.time() - self.last_failure_time
                if elapsed >= self.timeout:
                    self._state = "HALF_OPEN"
                    logger.info("Circuit breaker entering HALF_OPEN state")
                    return False
            return True
        return False

    async def record_success(self) -> None:
        """记录成功，重置失败计数"""
        async with self._lock:
            if self._state in ("OPEN", "HALF_OPEN"):
                self._state = "CLOSED"
                logger.info("Circuit breaker CLOSED after success")
            self.failure_count = 0
            self.last_failure_time = None

    async def record_failure(self) -> None:
        """记录失败，增加失败计数"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.failure_count >= self.threshold:
                if self._state != "OPEN":
                    self._state = "OPEN"
                    logger.warning(
                        f"Circuit breaker OPENED after {self.failure_count} consecutive failures"
                    )

    def get_state(self) -> str:
        """获取当前状态"""
        return self._state


class RetryMechanismAgent:
    """
    重试机制智能体

    提供强大的重试机制，包括：
    1. 指数退避 + 抖动
    2. 熔断器模式
    3. 按错误类型分队列管理
    4. 失败请求队列，支持后续重试
    5. 与 ConcurrencyControlAgent 集成，在限流时降低并发
    """

    def __init__(self, config: Optional[RetryConfig] = None):
        self.config = config or RetryConfig()

        # 熔断器
        self.circuit_breaker = CircuitBreaker(
            threshold=self.config.circuit_breaker_threshold,
            timeout=self.config.circuit_breaker_timeout
        )

        # 失败队列，按错误类型分类
        self._failed_queues: Dict[ErrorType, List[FailedItem]] = defaultdict(list)
        self._failed_items_lock = Lock()

        # 统计信息
        self._stats = {
            'total_attempts': 0,
            'successful_retries': 0,
            'failed_permanently': 0,
            'circuit_breaker_tripped': 0,
        }
        self._stats_lock = Lock()

        # 并发控制代理引用（可选）
        self._concurrency_agent: Optional[Any] = None

        # 当前退避延迟（动态调整）
        self._current_delay = self.config.base_delay
        self._delay_lock = Lock()

    def set_concurrency_agent(self, agent: Any) -> None:
        """
        设置并发控制代理

        Args:
            agent: ConcurrencyControlAgent 实例
        """
        self._concurrency_agent = agent
        logger.debug("Concurrency agent registered with retry mechanism")

    def _classify_error(self, exception: Exception) -> ErrorType:
        """
        分类错误类型

        Args:
            exception: 异常对象

        Returns:
            ErrorType 枚举值
        """
        error_str = str(exception).lower()
        exception_type = type(exception).__name__.lower()

        # 检查状态码或错误信息
        if '429' in error_str or 'too many requests' in error_str:
            return ErrorType.RATE_LIMIT
        elif '503' in error_str or 'service unavailable' in error_str:
            return ErrorType.SERVICE_UNAVAILABLE
        elif 'timeout' in error_str or 'timed out' in error_str:
            return ErrorType.TIMEOUT
        elif 'connection' in error_str or 'connect' in error_str:
            return ErrorType.CONNECTION_ERROR
        elif any(code in error_str for code in ['500', '502', '504', '505']):
            return ErrorType.SERVER_ERROR
        else:
            return ErrorType.UNKNOWN

    def _calculate_delay(self, attempt: int) -> float:
        """
        计算退避延迟

        Args:
            attempt: 当前尝试次数（从0开始）

        Returns:
            延迟时间（秒）
        """
        # 指数退避
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)

        # 应用最大延迟限制
        delay = min(delay, self.config.max_delay)

        # 应用当前动态延迟（用于限流响应）
        delay = max(delay, self._current_delay)

        # 添加抖动
        if self.config.jitter:
            # 全抖动：在 [0, delay] 范围内随机
            delay = random.uniform(0, delay)

        return delay

    async def _wait_for_circuit_breaker(self) -> bool:
        """
        等待熔断器关闭

        Returns:
            True 如果熔断器已关闭，False 如果超时
        """
        if not self.circuit_breaker.is_open:
            return True

        logger.warning("Circuit breaker is OPEN, waiting...")
        start_time = time.time()

        while self.circuit_breaker.is_open:
            if time.time() - start_time > self.config.circuit_breaker_timeout:
                logger.error("Timeout waiting for circuit breaker to close")
                return False
            await asyncio.sleep(1)

        return True

    async def execute_with_retry(
        self,
        func: Callable[..., T],
        *args: Any,
        retry_config: Optional[RetryConfig] = None,
        **kwargs: Any
    ) -> T:
        """
        执行函数，带自动重试机制

        Args:
            func: 待执行的函数（可以是同步或异步）
            *args: 函数位置参数
            retry_config: 可选的自定义重试配置
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 当所有重试都失败时抛出最后一次异常
        """
        config = retry_config or self.config

        # 检查熔断器
        if not await self._wait_for_circuit_breaker():
            raise Exception("Circuit breaker is open and timeout exceeded")

        last_exception: Optional[Exception] = None
        item_id = f"{func.__name__}_{time.time()}_{random.randint(1000, 9999)}"

        for attempt in range(config.max_retries + 1):
            async with self._stats_lock:
                self._stats['total_attempts'] += 1

            try:
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)

                # 成功后重置熔断器
                await self.circuit_breaker.record_success()

                # 重置动态延迟
                async with self._delay_lock:
                    self._current_delay = config.base_delay

                logger.debug(f"Function succeeded on attempt {attempt + 1}")
                return result

            except Exception as e:
                last_exception = e
                error_type = self._classify_error(e)

                logger.warning(
                    f"Attempt {attempt + 1}/{config.max_retries + 1} failed "
                    f"with {error_type.name}: {e}"
                )

                # 记录失败到熔断器
                await self.circuit_breaker.record_failure()

                # 如果是最后一次尝试
                if attempt == config.max_retries:
                    logger.error(f"All {config.max_retries + 1} attempts failed for {func.__name__}")

                    # 添加到失败队列
                    await self._add_to_failed_queue(
                        item_id=item_id,
                        func=func,
                        args=args,
                        kwargs=kwargs,
                        error_type=error_type,
                        error_message=str(e),
                        retry_count=attempt + 1
                    )

                    async with self._stats_lock:
                        self._stats['failed_permanently'] += 1

                    raise last_exception

                # 计算并等待延迟
                delay = self._calculate_delay(attempt)
                logger.info(f"Retrying in {delay:.2f}s...")
                await asyncio.sleep(delay)

        # 理论上不会到达这里
        raise last_exception or Exception("Unexpected end of retry loop")

    async def handle_rate_limit(self, retry_after: Optional[float] = None) -> None:
        """
        处理限流响应（HTTP 429）

        当收到429响应时调用，增加退避延迟并降低并发

        Args:
            retry_after: 服务器建议的等待时间（秒）
        """
        async with self._delay_lock:
            if retry_after:
                self._current_delay = max(self._current_delay, retry_after)
            else:
                # 指数增加当前延迟
                self._current_delay = min(
                    self._current_delay * self.config.exponential_base,
                    self.config.max_delay
                )

        logger.warning(f"Rate limit detected. New delay: {self._current_delay:.2f}s")

        # 通知并发控制代理降低并发
        if self._concurrency_agent is not None:
            try:
                # 尝试降低并发限制
                if hasattr(self._concurrency_agent, 'config'):
                    current_max = getattr(
                        self._concurrency_agent.config,
                        'max_concurrent_requests',
                        5
                    )
                    new_max = max(1, current_max // 2)
                    self._concurrency_agent.config.max_concurrent_requests = new_max
                    logger.info(f"Reduced concurrent requests from {current_max} to {new_max}")
            except Exception as e:
                logger.warning(f"Failed to adjust concurrency: {e}")

    async def add_failed_item(
        self,
        item: Dict[str, Any],
        error_message: str,
        error_type: ErrorType = ErrorType.UNKNOWN
    ) -> None:
        """
        添加失败项目到重试队列（公共接口）

        Args:
            item: 失败的项目数据
            error_message: 错误信息
            error_type: 错误类型
        """
        item_id = f"manual_{item.get('url', 'unknown')}_{time.time()}"
        await self._add_to_failed_queue(
            item_id=item_id,
            func=None,  # 手动添加，无执行函数
            args=(),
            kwargs={'item': item},
            error_type=error_type,
            error_message=error_message,
            retry_count=0
        )

    async def _add_to_failed_queue(
        self,
        item_id: str,
        func: Callable,
        args: Tuple[Any, ...],
        kwargs: Dict[str, Any],
        error_type: ErrorType,
        error_message: str,
        retry_count: int
    ) -> None:
        """
        添加失败项目到队列

        Args:
            item_id: 项目唯一标识
            func: 待执行的函数
            args: 函数参数
            kwargs: 函数关键字参数
            error_type: 错误类型
            error_message: 错误信息
            retry_count: 已重试次数
        """
        failed_item = FailedItem(
            item_id=item_id,
            func=func,
            args=args,
            kwargs=kwargs,
            error_type=error_type,
            error_message=error_message,
            retry_count=retry_count,
            last_attempt_time=time.time()
        )

        async with self._failed_items_lock:
            self._failed_queues[error_type].append(failed_item)

        logger.info(
            f"Added failed item {item_id} to {error_type.name} queue. "
            f"Total failed items: {sum(len(q) for q in self._failed_queues.values())}"
        )

    def get_failed_items(self, error_type: Optional[ErrorType] = None) -> List[Dict[str, Any]]:
        """
        获取失败项目列表

        Args:
            error_type: 可选的错误类型过滤

        Returns:
            失败项目字典列表
        """
        if error_type:
            return [item.to_dict() for item in self._failed_queues.get(error_type, [])]

        result = []
        for etype, queue in self._failed_queues.items():
            for item in queue:
                item_dict = item.to_dict()
                item_dict['error_type'] = etype.name
                result.append(item_dict)

        return result

    def get_failed_items_by_type(self, error_type: ErrorType) -> List[FailedItem]:
        """
        获取指定错误类型的失败项目

        Args:
            error_type: 错误类型

        Returns:
            FailedItem 列表
        """
        return list(self._failed_queues.get(error_type, []))

    async def retry_failed_items(
        self,
        process_func: Optional[Callable[[FailedItem], Any]] = None,
        error_types: Optional[List[ErrorType]] = None,
        max_items: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        重试所有失败的项目

        Args:
            process_func: 可选的自定义处理函数
            error_types: 可选的错误类型过滤列表
            max_items: 最大重试项目数

        Returns:
            重试结果统计字典
        """
        results = {
            'total': 0,
            'successful': 0,
            'failed': 0,
            'by_type': defaultdict(int)
        }

        # 收集要处理的项目
        items_to_process: List[Tuple[ErrorType, FailedItem]] = []

        async with self._failed_items_lock:
            types_to_process = error_types or list(self._failed_queues.keys())

            for error_type in types_to_process:
                queue = self._failed_queues[error_type]
                for item in queue[:]:  # 复制列表以便安全删除
                    items_to_process.append((error_type, item))
                    if max_items and len(items_to_process) >= max_items:
                        break
                if max_items and len(items_to_process) >= max_items:
                    break

        if not items_to_process:
            logger.info("No failed items to retry")
            return dict(results)

        logger.info(f"Retrying {len(items_to_process)} failed items")

        for error_type, item in items_to_process:
            results['total'] += 1

            try:
                if process_func:
                    # 使用自定义处理函数
                    await process_func(item) if asyncio.iscoroutinefunction(process_func) else process_func(item)
                else:
                    # 使用原始函数重试
                    await self.execute_with_retry(
                        item.func,
                        *item.args,
                        retry_config=self.config,
                        **item.kwargs
                    )

                results['successful'] += 1
                results['by_type'][error_type.name] += 1

                # 从队列中移除
                async with self._failed_items_lock:
                    if item in self._failed_queues[error_type]:
                        self._failed_queues[error_type].remove(item)

                async with self._stats_lock:
                    self._stats['successful_retries'] += 1

            except Exception as e:
                results['failed'] += 1
                logger.error(f"Retry failed for item {item.item_id}: {e}")

                # 更新重试计数
                item.retry_count += 1
                item.last_attempt_time = time.time()

        logger.info(
            f"Retry batch completed: {results['successful']} succeeded, "
            f"{results['failed']} failed"
        )

        return dict(results)

    async def clear_failed_items(self, error_type: Optional[ErrorType] = None) -> int:
        """
        清空失败队列

        Args:
            error_type: 可选的错误类型，如不指定则清空所有

        Returns:
            清空的項目数量
        """
        async with self._failed_items_lock:
            if error_type:
                count = len(self._failed_queues[error_type])
                self._failed_queues[error_type].clear()
            else:
                count = sum(len(q) for q in self._failed_queues.values())
                self._failed_queues.clear()

        logger.info(f"Cleared {count} failed items")
        return count

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            统计信息字典
        """
        return {
            **self._stats,
            'circuit_breaker_state': self.circuit_breaker.get_state(),
            'circuit_breaker_failures': self.circuit_breaker.failure_count,
            'current_delay': self._current_delay,
            'failed_queue_sizes': {
                etype.name: len(queue)
                for etype, queue in self._failed_queues.items()
            },
            'total_failed_items': sum(len(q) for q in self._failed_queues.values()),
        }

    async def reset(self) -> None:
        """重置所有状态"""
        async with self._failed_items_lock:
            self._failed_queues.clear()

        async with self._stats_lock:
            self._stats = {
                'total_attempts': 0,
                'successful_retries': 0,
                'failed_permanently': 0,
                'circuit_breaker_tripped': 0,
            }

        async with self._delay_lock:
            self._current_delay = self.config.base_delay

        # 重置熔断器
        await self.circuit_breaker.record_success()

        logger.info("Retry mechanism agent reset")


# 全局重试代理实例
_retry_agent: Optional[RetryMechanismAgent] = None


def get_retry_agent(config: Optional[RetryConfig] = None) -> RetryMechanismAgent:
    """获取全局重试代理"""
    global _retry_agent
    if _retry_agent is None:
        _retry_agent = RetryMechanismAgent(config)
    return _retry_agent


def reset_retry_agent() -> None:
    """重置全局重试代理"""
    global _retry_agent
    _retry_agent = None
