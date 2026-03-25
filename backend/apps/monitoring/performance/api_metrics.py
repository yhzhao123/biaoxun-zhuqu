"""
Task 061: API Metrics Middleware
API 指标中间件 - 响应时间跟踪、百分位数计算
"""
import time
from typing import List, Optional
from collections import deque

from django.http import HttpRequest, HttpResponse, JsonResponse
from apps.monitoring.performance.models import ApiMetric


class ResponseTimeMiddleware:
    """API 响应时间中间件"""

    # 最大记录数
    MAX_METRICS = 10000

    def __init__(self, get_response):
        """
        初始化中间件

        Args:
            get_response: Django 请求处理函数
        """
        self.get_response = get_response
        self.metrics: deque = deque(maxlen=self.MAX_METRICS)
        # 按端点分组的指标
        self.endpoint_metrics: dict = {}

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """处理请求"""
        # 记录开始时间
        start_time = time.time()

        # 获取响应
        response = self.get_response(request)

        # 计算响应时间
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒

        # 记录指标
        self._record_request(
            endpoint=request.path,
            method=request.method,
            response_time=response_time,
            status_code=response.status_code
        )

        return response

    def _record_request(
        self,
        endpoint: str,
        method: str,
        response_time: float,
        status_code: int
    ) -> None:
        """
        记录请求指标

        Args:
            endpoint: 端点路径
            method: HTTP 方法
            response_time: 响应时间（毫秒）
            status_code: 状态码
        """
        metric = ApiMetric(
            endpoint=endpoint,
            method=method,
            response_time=response_time,
            status_code=status_code
        )
        self.metrics.append(metric)

        # 更新端点指标
        key = f"{method}:{endpoint}"
        if key not in self.endpoint_metrics:
            self.endpoint_metrics[key] = deque(maxlen=self.MAX_METRICS)
        self.endpoint_metrics[key].append(metric)

    def calculate_percentile(self, percentile: int) -> float:
        """
        计算百分位数

        Args:
            percentile: 百分位数 (0-100)

        Returns:
            百分位数值
        """
        if not self.metrics:
            return 0.0

        sorted_times = sorted([m.response_time for m in self.metrics])
        if not sorted_times:
            return 0.0

        index = int(len(sorted_times) * percentile / 100)
        index = min(index, len(sorted_times) - 1)
        return round(sorted_times[index], 2)

    def get_request_count(self) -> int:
        """获取请求总数"""
        return len(self.metrics)

    def get_error_rate(self) -> float:
        """获取错误率（百分比）"""
        if not self.metrics:
            return 0.0

        error_count = sum(1 for m in self.metrics if m.is_error())
        return round((error_count / len(self.metrics)) * 100, 2)

    def get_average_response_time(self) -> float:
        """获取平均响应时间"""
        if not self.metrics:
            return 0.0

        total = sum(m.response_time for m in self.metrics)
        return round(total / len(self.metrics), 2)

    def get_metrics_by_endpoint(self, endpoint: str, method: str = None) -> List[ApiMetric]:
        """
        获取特定端点的指标

        Args:
            endpoint: 端点路径
            method: HTTP 方法（可选）

        Returns:
            指标列表
        """
        key = f"{method or ''}:{endpoint}"
        return list(self.endpoint_metrics.get(key, []))

    def get_endpoint_stats(self, endpoint: str) -> dict:
        """
        获取端点统计信息

        Args:
            endpoint: 端点路径

        Returns:
            统计信息字典
        """
        metrics = self.get_metrics_by_endpoint(endpoint)
        if not metrics:
            return {}

        return {
            'endpoint': endpoint,
            'count': len(metrics),
            'avg_response_time': round(sum(m.response_time for m in metrics) / len(metrics), 2),
            'min_response_time': min(m.response_time for m in metrics),
            'max_response_time': max(m.response_time for m in metrics),
            'error_count': sum(1 for m in metrics if m.is_error()),
            'error_rate': round((sum(1 for m in metrics if m.is_error()) / len(metrics)) * 100, 2)
        }

    def get_all_endpoints(self) -> List[str]:
        """获取所有记录的端点"""
        return list(self.endpoint_metrics.keys())

    def clear_metrics(self) -> None:
        """清除所有指标"""
        self.metrics.clear()
        self.endpoint_metrics.clear()

    def get_recent_metrics(self, count: int = 100) -> List[ApiMetric]:
        """获取最近的指标"""
        return list(self.metrics)[-count:]


# 全局中间件实例
_middleware_instance: Optional[ResponseTimeMiddleware] = None


def get_metrics_middleware() -> Optional[ResponseTimeMiddleware]:
    """获取全局指标中间件实例"""
    return _middleware_instance


def set_metrics_middleware(middleware: ResponseTimeMiddleware) -> None:
    """设置全局指标中间件实例"""
    global _middleware_instance
    _middleware_instance = middleware