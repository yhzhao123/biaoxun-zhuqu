"""
Performance Metrics - TDD Cycle 20

性能指标收集:
- 执行时间追踪
- 计时装饰器
- 性能统计
"""
import asyncio
import functools
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class TimingResult:
    """计时结果"""
    function_name: str
    duration: float
    start_time: float
    end_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMetrics:
    """
    性能指标收集器

    追踪:
    - 执行时间
    - 并发数
    - 队列长度
    - 自定义指标
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 计时结果存储
        self._timings: Dict[str, list] = {}

        # 实时指标
        self._gauge: Dict[str, float] = {}

        # 计数器
        self._counters: Dict[str, int] = {}

    def record_timing(
        self,
        name: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录执行时间

        Args:
            name: 指标名称
            duration: 持续时间（秒）
            metadata: 附加元数据
        """
        if name not in self._timings:
            self._timings[name] = []

        result = TimingResult(
            function_name=name,
            duration=duration,
            start_time=time.time() - duration,
            end_time=time.time(),
            metadata=metadata or {}
        )

        self._timings[name].append(result)
        self.logger.debug(f"Recorded timing: {name}={duration:.3f}s")

    def set_gauge(self, name: str, value: float) -> None:
        """
        设置仪表值

        Args:
            name: 指标名称
            value: 指标值
        """
        self._gauge[name] = value

    def increment_counter(self, name: str, value: int = 1) -> None:
        """
        递增计数器

        Args:
            name: 计数器名称
            value: 递增量
        """
        current = self._counters.get(name, 0)
        self._counters[name] = current + value

    def get_counter(self, name: str) -> int:
        """
        获取计数器值

        Args:
            name: 计数器名称

        Returns:
            计数器值
        """
        return self._counters.get(name, 0)

    def get_timing_stats(self, name: str) -> Dict[str, float]:
        """
        获取计时统计

        Args:
            name: 指标名称

        Returns:
            统计字典，包含 min, max, avg, count
        """
        if name not in self._timings or not self._timings[name]:
            return {"min": 0, "max": 0, "avg": 0, "count": 0}

        durations = [t.duration for t in self._timings[name]]
        return {
            "min": min(durations),
            "max": max(durations),
            "avg": sum(durations) / len(durations),
            "count": len(durations),
            "total": sum(durations)
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """
        获取所有统计信息

        Returns:
            完整统计字典
        """
        timing_stats = {
            name: self.get_timing_stats(name)
            for name in self._timings
        }

        return {
            "timings": timing_stats,
            "gauges": self._gauge.copy(),
            "counters": self._counters.copy()
        }

    def reset(self) -> None:
        """重置所有指标"""
        self._timings.clear()
        self._gauge.clear()
        self._counters.clear()
        self.logger.info("Metrics reset")


def _wrap_function(func: Callable, metric_name: str, metadata_fn: Optional[Callable]) -> Callable:
    """
    包装函数以添加计时功能

    Args:
        func: 要包装的函数
        metric_name: 指标名称
        metadata_fn: 元数据生成函数

    Returns:
        包装后的函数
    """
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start

                # 收集元数据
                meta = {}
                if metadata_fn:
                    try:
                        meta = metadata_fn(*args, **kwargs) or {}
                    except Exception:
                        pass

                # 记录计时（通过全局指标收集器）
                if _global_metrics is not None:
                    _global_metrics.record_timing(metric_name, duration, meta)
    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start

                meta = {}
                if metadata_fn:
                    try:
                        meta = metadata_fn(*args, **kwargs) or {}
                    except Exception:
                        pass

                _global_metrics.record_timing(metric_name, duration, meta)

    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


def timed(name: Optional[str] = None, metadata: Optional[Callable] = None):
    """
    计时装饰器

    用法:
        @timed("my_function")
        async def my_function():
            ...

        或者不带参数:
        @timed
        async def my_function():
            ...

        或者带元数据的:
        @timed("my_function", metadata=lambda *args, **kwargs: {"user_id": kwargs.get("user_id")})
        async def my_function(user_id):
            ...

    Args:
        name: 指标名称，默认使用函数名
        metadata: 元数据生成函数

    Returns:
        装饰后的函数
    """
    def decorator(func: Optional[Callable] = None):
        # 处理不带参数的 @timed 情况
        if func is not None:
            # 直接装饰函数
            return _wrap_function(func, func.__name__, None)
        elif name is not None and callable(name):
            # 情况: @timed (不带参数) 等同于 @timed()
            # 此时 name 是被装饰的函数
            return _wrap_function(name, name.__name__, None)
        elif name is not None:
            # 情况: @timed("name") 或 @timed("name", metadata=...)
            def wrapper(f):
                return _wrap_function(f, name, metadata)
            return wrapper
        else:
            # 默认情况
            def wrapper(f):
                return _wrap_function(f, f.__name__, None)
            return wrapper

    return decorator


# 全局指标实例
_global_metrics: Optional[PerformanceMetrics] = None


def get_metrics() -> PerformanceMetrics:
    """
    获取全局性能指标实例

    Returns:
        PerformanceMetrics 实例
    """
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = PerformanceMetrics()
    return _global_metrics