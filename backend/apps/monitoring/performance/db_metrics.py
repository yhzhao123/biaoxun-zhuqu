"""
Task 061: Database Metrics Collector
数据库指标收集器 - 连接池监控、慢查询检测
"""
from typing import List, Optional
from collections import deque
from datetime import datetime

from django.db import connection


class DbMetricsCollector:
    """数据库指标收集器"""

    MAX_METRICS = 1000

    def __init__(self):
        """初始化收集器"""
        self.metrics: deque = deque(maxlen=self.MAX_METRICS)
        self.slow_queries: deque = deque(maxlen=100)

    def record_metric(self, metric) -> None:
        """
        记录指标

        Args:
            metric: DbMetric 实例
        """
        self.metrics.append(metric)

    def collect_pool_stats(self) -> Optional[dict]:
        """
        收集连接池统计信息

        Returns:
            连接池统计字典
        """
        try:
            # 使用 Django 的 connection 获取基本信息
            pool_info = {
                'vendor': connection.vendor,
                'settings': {
                    'name': connection.settings_dict.get('NAME'),
                    'host': connection.settings_dict.get('HOST'),
                }
            }

            # 对于 PostgreSQL，可以获取更详细的连接信息
            if connection.vendor == 'postgresql':
                try:
                    with connection.cursor() as cursor:
                        # 获取活动连接数
                        cursor.execute("""
                            SELECT count(*)
                            FROM pg_stat_activity
                            WHERE datname = current_database()
                        """)
                        active_count = cursor.fetchone()[0]

                        # 获取最大连接数
                        cursor.execute("SHOW max_connections")
                        max_connections = cursor.fetchone()[0]

                        pool_info['pool'] = {
                            'active': active_count,
                            'max': int(max_connections),
                            'usage_percent': round((active_count / int(max_connections)) * 100, 2) if max_connections else 0
                        }
                except Exception:
                    pass

            return pool_info
        except Exception:
            return None

    def get_current_pool_usage(self, pool_size: int, active: int) -> float:
        """
        计算连接池使用率

        Args:
            pool_size: 连接池大小
            active: 活动连接数

        Returns:
            使用率百分比
        """
        if pool_size == 0:
            return 0.0
        return round((active / pool_size) * 100, 2)

    def is_slow_query(self, query_time: float, threshold: float = 1.0) -> bool:
        """
        判断是否为慢查询

        Args:
            query_time: 查询耗时（秒）
            threshold: 阈值（秒）

        Returns:
            是否为慢查询
        """
        return query_time > threshold

    def record_slow_query(self, query: str, query_time: float) -> None:
        """
        记录慢查询

        Args:
            query: SQL 查询
            query_time: 查询耗时
        """
        self.slow_queries.append({
            'query': query[:500],  # 限制长度
            'query_time': query_time,
            'timestamp': datetime.now()
        })

    def get_slow_queries(self, limit: int = 10) -> List[dict]:
        """获取慢查询列表"""
        sorted_queries = sorted(
            self.slow_queries,
            key=lambda x: x['query_time'],
            reverse=True
        )
        return sorted_queries[:limit]

    def get_pool_stats(self) -> dict:
        """获取连接池统计"""
        if not self.metrics:
            return {}

        return {
            'total_metrics': len(self.metrics),
            'avg_pool_usage': self._calculate_avg_pool_usage(),
            'max_pool_usage': self._calculate_max_pool_usage(),
            'slow_queries_count': len(self.slow_queries)
        }

    def _calculate_avg_pool_usage(self) -> float:
        """计算平均连接池使用率"""
        if not self.metrics:
            return 0.0

        pool_usages = [m.get_pool_usage() for m in self.metrics if hasattr(m, 'get_pool_usage')]
        if not pool_usages:
            return 0.0
        return round(sum(pool_usages) / len(pool_usages), 2)

    def _calculate_max_pool_usage(self) -> float:
        """计算最大连接池使用率"""
        if not self.metrics:
            return 0.0

        pool_usages = [m.get_pool_usage() for m in self.metrics if hasattr(m, 'get_pool_usage')]
        if not pool_usages:
            return 0.0
        return max(pool_usages)

    def get_recent_metrics(self, count: int = 100) -> list:
        """获取最近的指标"""
        return list(self.metrics)[-count:]

    def clear_metrics(self) -> None:
        """清除所有指标"""
        self.metrics.clear()
        self.slow_queries.clear()


# 全局收集器实例
_metrics_collector: Optional[DbMetricsCollector] = None


def get_db_metrics_collector() -> DbMetricsCollector:
    """获取全局数据库指标收集器"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = DbMetricsCollector()
    return _metrics_collector