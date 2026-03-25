"""
Task 061: Queue Metrics Collector
队列指标收集器 - Redis 队列长度监控、Worker 数量统计
"""
from typing import List, Optional, Set
from collections import deque

try:
    import redis
except ImportError:
    redis = None

from apps.monitoring.performance.models import QueueMetric


class QueueMetricsCollector:
    """队列指标收集器"""

    MAX_METRICS = 1000

    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        """
        初始化收集器

        Args:
            redis_url: Redis 连接 URL
        """
        self.redis_url = redis_url
        self.metrics: deque = deque(maxlen=self.MAX_METRICS)
        self._redis_client = None

    def _get_redis_client(self):
        """获取 Redis 客户端"""
        if redis is None:
            return None

        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5
                )
            except Exception:
                return None
        return self._redis_client

    def get_queue_length(self, queue_name: str = 'celery') -> int:
        """
        获取队列长度

        Args:
            queue_name: 队列名称

        Returns:
            队列长度
        """
        client = self._get_redis_client()
        if client is None:
            return 0

        try:
            # Celery 使用 Redis 列表存储任务
            return client.llen(queue_name)
        except Exception:
            return 0

    def get_worker_count(self, worker_prefix: str = 'celery@') -> int:
        """
        获取 Worker 数量

        Args:
            worker_prefix: Worker 前缀

        Returns:
            Worker 数量
        """
        client = self._get_redis_client()
        if client is None:
            return 0

        try:
            # Celery worker 注册信息存储在 Redis 的 set 中
            workers = client.smembers('celery@')
            return len(workers) if workers else 0
        except Exception:
            return 0

    def get_all_workers(self) -> Set[str]:
        """
        获取所有 Worker

        Returns:
            Worker 集合
        """
        client = self._get_redis_client()
        if client is None:
            return set()

        try:
            return client.smembers('celery@') or set()
        except Exception:
            return set()

    def get_queue_info(self, queue_name: str = 'celery') -> dict:
        """
        获取队列信息

        Args:
            queue_name: 队列名称

        Returns:
            队列信息字典
        """
        length = self.get_queue_length(queue_name)
        worker_count = self.get_worker_count()

        # 创建指标
        metric = QueueMetric(
            queue_name=queue_name,
            length=length,
            worker_count=worker_count
        )
        self.record_metric(metric)

        return {
            'queue_name': queue_name,
            'length': length,
            'worker_count': worker_count,
            'is_backlogged': metric.is_backlogged()
        }

    def record_metric(self, metric: QueueMetric) -> None:
        """
        记录指标

        Args:
            metric: QueueMetric 实例
        """
        self.metrics.append(metric)

    def get_all_queue_lengths(self, queues: List[str] = None) -> dict:
        """
        获取所有队列的长度

        Args:
            queues: 队列名称列表

        Returns:
            队列长度字典
        """
        if queues is None:
            queues = ['celery', 'default', 'high_priority', 'low_priority']

        result = {}
        for queue in queues:
            result[queue] = self.get_queue_length(queue)

        return result

    def get_consumer_count(self, queue_name: str = 'celery') -> int:
        """
        获取消费者数量

        Args:
            queue_name: 队列名称

        Returns:
            消费者数量
        """
        # Celery 使用不同的机制来跟踪消费者
        # 这里简单返回 Worker 数量
        return self.get_worker_count()

    def check_queue_health(self, queue_name: str, max_length: int = 1000) -> dict:
        """
        检查队列健康状态

        Args:
            queue_name: 队列名称
            max_length: 最大允许长度

        Returns:
            健康状态字典
        """
        length = self.get_queue_length(queue_name)
        worker_count = self.get_worker_count()

        status = 'healthy'
        issues = []

        if length > max_length:
            status = 'warning'
            issues.append(f'Queue backlog: {length} tasks')

        if worker_count == 0:
            status = 'critical'
            issues.append('No workers available')

        return {
            'queue': queue_name,
            'status': status,
            'issues': issues,
            'length': length,
            'workers': worker_count
        }

    def get_queue_stats(self) -> dict:
        """获取队列统计"""
        if not self.metrics:
            return {}

        lengths = [m.length for m in self.metrics]
        worker_counts = [m.worker_count for m in self.metrics]

        return {
            'total_metrics': len(self.metrics),
            'avg_queue_length': round(sum(lengths) / len(lengths), 2) if lengths else 0,
            'max_queue_length': max(lengths) if lengths else 0,
            'avg_worker_count': round(sum(worker_counts) / len(worker_counts), 2) if worker_counts else 0
        }

    def get_recent_metrics(self, count: int = 100) -> List[QueueMetric]:
        """获取最近的指标"""
        return list(self.metrics)[-count:]

    def clear_metrics(self) -> None:
        """清除所有指标"""
        self.metrics.clear()

    def close(self) -> None:
        """关闭 Redis 连接"""
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None


# 全局收集器实例
_metrics_collector: Optional[QueueMetricsCollector] = None


def get_queue_metrics_collector(redis_url: str = 'redis://localhost:6379/0') -> QueueMetricsCollector:
    """获取全局队列指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = QueueMetricsCollector(redis_url)
    return _metrics_collector