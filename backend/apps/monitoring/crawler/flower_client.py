"""
Task 059: FlowerClient
Flower HTTP API 封装 - 获取 Celery 任务信息
"""
import requests
from typing import Dict, Any, Optional
from apps.monitoring.crawler.models import FlowerTask


class FlowerClient:
    """Flower API 客户端"""

    def __init__(self, base_url: str = 'http://localhost:5555', timeout: int = 5):
        """
        初始化 Flower 客户端

        Args:
            base_url: Flower 服务地址
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json'
        })

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        发送请求

        Args:
            method: HTTP 方法
            endpoint: API 端点
            **kwargs: 其他请求参数
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        kwargs.setdefault('timeout', self.timeout)

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            return {}
        except requests.ConnectionError:
            return {}
        except requests.RequestException as e:
            # 记录错误但返回空字典
            return {}

    def get_active_tasks(self) -> Dict[str, Any]:
        """
        获取活动任务

        Returns:
            活动任务字典
        """
        return self._request('GET', 'api/worker/active')

    def get_task_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息

        Args:
            task_id: 任务 ID

        Returns:
            任务信息字典
        """
        result = self._request('GET', f'task/info/{task_id}')
        return result if result else None

    def get_task_stats(self) -> Dict[str, Any]:
        """
        获取任务统计

        Returns:
            任务统计字典
        """
        return self._request('GET', 'api/workers')

    def get_worker_stats(self, worker_name: str) -> Dict[str, Any]:
        """
        获取 Worker 统计

        Args:
            worker_name: Worker 名称

        Returns:
            Worker 统计字典
        """
        return self._request('GET', f'api/worker/{worker_name}')

    def get_registered_tasks(self, worker_name: str) -> Dict[str, Any]:
        """
        获取 Worker 注册的任务

        Args:
            worker_name: Worker 名称

        Returns:
            注册的任务字典
        """
        return self._request('GET', f'api/worker/{worker_name}/tasks')

    def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        获取任务结果

        Args:
            task_id: 任务 ID

        Returns:
            任务结果
        """
        result = self._request('GET', f'task/result/{task_id}')
        return result

    def revoke_task(self, task_id: str, terminate: bool = False) -> bool:
        """
        撤销任务

        Args:
            task_id: 任务 ID
            terminate: 是否终止任务

        Returns:
            是否成功
        """
        data = {'terminate': terminate} if terminate else {}
        result = self._request('POST', f'task/revoke/{task_id}', json=data)
        return bool(result)

    def ping_workers(self) -> Dict[str, bool]:
        """
        Ping 所有 Worker

        Returns:
            Worker 存活状态字典
        """
        return self._request('GET', 'api/workers/ping')

    def get_reserved_tasks(self, worker_name: str) -> list:
        """
        获取 Worker 保留的任务

        Args:
            worker_name: Worker 名称

        Returns:
            保留的任务列表
        """
        result = self._request('GET', f'api/worker/{worker_name}/reserved')
        return result if isinstance(result, list) else []

    def get_scheduled_tasks(self, worker_name: str) -> list:
        """
        获取 Worker 调度的任务

        Args:
            worker_name: Worker 名称

        Returns:
            调度的任务列表
        """
        result = self._request('GET', f'api/worker/{worker_name}/scheduled')
        return result if isinstance(result, list) else []

    def close(self) -> None:
        """关闭会话"""
        self.session.close()


# 全局客户端实例
_flower_client: Optional[FlowerClient] = None


def get_flower_client(base_url: str = 'http://localhost:5555', timeout: int = 5) -> FlowerClient:
    """获取 Flower 客户端实例"""
    global _flower_client
    if _flower_client is None:
        _flower_client = FlowerClient(base_url, timeout)
    return _flower_client