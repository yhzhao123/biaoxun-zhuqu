"""
Task 059: TaskTracker
任务追踪器 - 记录任务生命周期
"""
from datetime import datetime
from typing import Dict, List, Optional
from apps.monitoring.crawler.models import TaskRecord


class TaskTracker:
    """任务追踪器类 - 记录 Celery 任务生命周期"""

    def __init__(self):
        self.tasks: Dict[str, TaskRecord] = {}

    def start(self, task_id: str, name: str, **kwargs) -> TaskRecord:
        """
        任务开始

        Args:
            task_id: 任务 ID
            name: 任务名称
            **kwargs: 其他参数
        """
        record = TaskRecord(
            task_id=task_id,
            name=name,
            status='running',
            start_time=datetime.now(),
            **kwargs
        )
        self.tasks[task_id] = record
        return record

    def complete(self, task_id: str, result: Optional[dict] = None) -> Optional[TaskRecord]:
        """
        任务完成

        Args:
            task_id: 任务 ID
            result: 任务结果
        """
        task = self.tasks.get(task_id)
        if task:
            task.status = 'success'
            task.end_time = datetime.now()
            if result:
                task.result = result
        return task

    def fail(self, task_id: str, error_message: Optional[str] = None) -> Optional[TaskRecord]:
        """
        任务失败

        Args:
            task_id: 任务 ID
            error_message: 错误信息
        """
        task = self.tasks.get(task_id)
        if task:
            task.status = 'failure'
            task.end_time = datetime.now()
            task.error_message = error_message
        return task

    def retry(self, task_id: str) -> Optional[TaskRecord]:
        """
        任务重试

        Args:
            task_id: 任务 ID
        """
        task = self.tasks.get(task_id)
        if task:
            task.status = 'retry'
            task.retry_count += 1
        return task

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        """
        获取任务记录

        Args:
            task_id: 任务 ID
        """
        return self.tasks.get(task_id)

    def get_running_tasks(self) -> List[TaskRecord]:
        """获取运行中的任务"""
        return [task for task in self.tasks.values() if task.is_running()]

    def get_tasks_by_status(self, status: str) -> List[TaskRecord]:
        """按状态获取任务"""
        return [task for task in self.tasks.values() if task.status == status]

    def get_tasks_by_name(self, name: str) -> List[TaskRecord]:
        """按名称获取任务"""
        return [task for task in self.tasks.values() if task.name == name]

    def remove_task(self, task_id: str) -> bool:
        """移除任务记录"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            return True
        return False

    def clear_completed(self) -> int:
        """清除已完成的任务"""
        completed_ids = [
            task_id for task_id, task in self.tasks.items()
            if task.status in ('success', 'failure')
        ]
        for task_id in completed_ids:
            del self.tasks[task_id]
        return len(completed_ids)

    def get_all_tasks(self) -> Dict[str, TaskRecord]:
        """获取所有任务"""
        return self.tasks.copy()

    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = {
            'total': len(self.tasks),
            'running': 0,
            'success': 0,
            'failure': 0,
            'retry': 0,
            'pending': 0
        }
        for task in self.tasks.values():
            stats[task.status] = stats.get(task.status, 0) + 1
        return stats


# 全局任务追踪器实例
_task_tracker = None


def get_task_tracker() -> TaskTracker:
    """获取全局任务追踪器实例"""
    global _task_tracker
    if _task_tracker is None:
        _task_tracker = TaskTracker()
    return _task_tracker