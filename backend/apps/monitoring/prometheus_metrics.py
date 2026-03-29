"""
Prometheus Metrics - TDD Cycle 21

Prometheus 指标收集:
- extraction_count (Counter)
- extraction_duration (Histogram)
- extraction_errors (Counter)
- cache_hit_rate (Gauge)
- concurrent_requests (Gauge)
- queue_length (Gauge)
"""
import time
from typing import Any, Dict, Optional
from functools import wraps

# 尝试导入 prometheus_client，如果不可用则使用 mock
try:
    from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # 创建 mock 类
    class Counter:
        def __init__(self, name: str, description: str, labelnames: list = None):
            self._value = 0
            self._labels = {}
        def inc(self, value: float = 1, labels: Dict = None):
            self._value += value
        def labels(self, **kwargs):
            return self

    class Histogram:
        def __init__(self, name: str, description: str, buckets: list = None):
            self._value = 0
        def observe(self, value: float):
            self._value = value

    class Gauge:
        def __init__(self, name: str, description: str, labelnames: list = None):
            self._value = 0
        def set(self, value: float):
            self._value = value
        def inc(self):
            self._value += 1
        def dec(self):
            self._value -= 1

    class CollectorRegistry:
        def __init__(self):
            pass

    def generate_latest(registry=None) -> str:
        return ""

# 创建 Prometheus 注册表
registry = CollectorRegistry()

# 定义指标
if PROMETHEUS_AVAILABLE:
    # 提取计数
    extraction_count = Counter(
        'deer_flow_extraction_total',
        'Total number of extractions',
        ['source_url', 'status'],
        registry=registry
    )

    # 提取错误计数
    extraction_errors = Counter(
        'deer_flow_extraction_errors_total',
        'Total number of extraction errors',
        ['source_url', 'error_type'],
        registry=registry
    )

    # 提取持续时间
    extraction_duration = Histogram(
        'deer_flow_extraction_duration_seconds',
        'Extraction duration in seconds',
        ['source_url'],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
        registry=registry
    )

    # 缓存命中率
    cache_hit_rate = Gauge(
        'deer_flow_cache_hit_rate',
        'Cache hit rate',
        registry=registry
    )

    # 并发请求数
    concurrent_requests = Gauge(
        'deer_flow_concurrent_requests',
        'Number of concurrent requests',
        registry=registry
    )

    # 队列长度
    queue_length = Gauge(
        'deer_flow_queue_length',
        'Length of extraction queue',
        registry=registry
    )
else:
    # 使用简单的内存存储
    extraction_count = Counter(
        'deer_flow_extraction_total',
        'Total number of extractions',
        ['source_url', 'status']
    )
    extraction_errors = Counter(
        'deer_flow_extraction_errors_total',
        'Total number of extraction errors',
        ['source_url', 'error_type']
    )
    extraction_duration = Histogram(
        'deer_flow_extraction_duration_seconds',
        'Extraction duration in seconds',
        ['source_url']
    )
    cache_hit_rate = Gauge(
        'deer_flow_cache_hit_rate',
        'Cache hit rate'
    )
    concurrent_requests = Gauge(
        'deer_flow_concurrent_requests',
        'Number of concurrent requests'
    )
    queue_length = Gauge(
        'deer_flow_queue_length',
        'Length of extraction queue'
    )


class MetricsCollector:
    """
    指标收集器

    提供高级指标收集接口
    """

    def __init__(self):
        self._cache_hits = 0
        self._cache_misses = 0

    def record_extraction(
        self,
        source_url: str,
        duration: float,
        success: bool,
        items_count: int = 0,
        error_message: Optional[str] = None
    ):
        """
        记录提取结果

        Args:
            source_url: 源 URL
            duration: 持续时间（秒）
            success: 是否成功
            items_count: 项目数量
            error_message: 错误信息
        """
        status = "success" if success else "failure"

        # 记录提取计数
        try:
            extraction_count.labels(
                source_url=source_url,
                status=status
            ).inc()
        except Exception:
            extraction_count.inc()

        # 记录错误
        if not success:
            error_type = "unknown"
            if error_message:
                if "timeout" in error_message.lower():
                    error_type = "timeout"
                elif "connection" in error_message.lower():
                    error_type = "connection"
                elif "auth" in error_message.lower():
                    error_type = "auth"
                else:
                    error_type = "other"

            try:
                extraction_errors.labels(
                    source_url=source_url,
                    error_type=error_type
                ).inc()
            except Exception:
                extraction_errors.inc()

        # 记录持续时间
        try:
            extraction_duration.labels(source_url=source_url).observe(duration)
        except Exception:
            extraction_duration.observe(duration)

    def update_cache_stats(self, hits: int, misses: int):
        """
        更新缓存统计

        Args:
            hits: 命中数
            misses: 未命中数
        """
        self._cache_hits = hits
        self._cache_misses = misses

        total = hits + misses
        if total > 0:
            rate = hits / total
            cache_hit_rate.set(rate)

    def update_concurrent_requests(self, count: int):
        """
        更新并发请求数

        Args:
            count: 并发请求数
        """
        concurrent_requests.set(count)

    def update_queue_length(self, length: int):
        """
        更新队列长度

        Args:
            length: 队列长度
        """
        queue_length.set(length)

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        获取所有指标

        Returns:
            指标字典
        """
        return {
            "extraction_count": extraction_count._value if hasattr(extraction_count, '_value') else 0,
            "extraction_errors": extraction_errors._value if hasattr(extraction_errors, '_value') else 0,
            "cache_hit_rate": cache_hit_rate._value if hasattr(cache_hit_rate, '_value') else 0,
            "concurrent_requests": concurrent_requests._value if hasattr(concurrent_requests, '_value') else 0,
            "queue_length": queue_length._value if hasattr(queue_length, '_value') else 0,
        }


class MetricsMiddleware:
    """用于 Django 的指标中间件"""

    def __init__(self, get_response):
        self.get_response = get_response
        self._collector = MetricsCollector()

    def __call__(self, request):
        # 增加并发请求计数
        concurrent_requests.inc()

        response = self.get_response(request)

        # 减少并发请求计数
        concurrent_requests.dec()

        return response


class MetricsExporter:
    """Prometheus 指标导出器"""

    def __init__(self):
        self.registry = registry

    def generate_metrics(self) -> str:
        """生成 Prometheus 格式的指标"""
        return generate_latest(self.registry)


def generate_metrics() -> str:
    """
    生成 Prometheus 指标

    Returns:
        Prometheus 格式的指标字符串
    """
    return generate_latest(registry)


def track_extraction_time(source_url: str):
    """
    跟踪提取时间的上下文管理器

    Args:
        source_url: 源 URL

    Usage:
        with track_extraction_time("http://example.com"):
            # extraction code
            pass
    """
    class ExtractionTimer:
        def __init__(self, url: str):
            self.url = url
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.time() - self.start_time
            try:
                extraction_duration.labels(source_url=self.url).observe(duration)
            except Exception:
                extraction_duration.observe(duration)

    return ExtractionTimer(source_url)


def track_extraction(func):
    """
    跟踪提取的装饰器

    Usage:
        @track_extraction
        def my_extraction():
            pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            source_url = kwargs.get('source_url', 'unknown')
            try:
                extraction_duration.labels(source_url=source_url).observe(duration)
            except Exception:
                extraction_duration.observe(duration)

    return wrapper


# 全局指标收集器实例
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器"""
    global _global_collector
    if _global_collector is None:
        _global_collector = MetricsCollector()
    return _global_collector