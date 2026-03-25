"""
Task 059: TaskCounter
任务计数器 - 聚合成功/失败统计，时间窗口统计
"""
from datetime import datetime, timedelta
from typing import Dict, Optional
from collections import defaultdict


class TaskCounter:
    """任务计数器类 - 聚合统计"""

    def __init__(self, task_name: str, window: str = 'hour'):
        """
        初始化计数器

        Args:
            task_name: 任务名称
            window: 时间窗口 ('hour', 'day')
        """
        self.task_name = task_name
        self.window = window
        self.success = 0
        self.failure = 0
        self.retries = 0
        self._hourly_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {'success': 0, 'failure': 0})
        self._daily_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {'success': 0, 'failure': 0})

    def record_success(self) -> None:
        """记录成功"""
        self.success += 1
        self._record_to_time_window('success')

    def record_failure(self) -> None:
        """记录失败"""
        self.failure += 1
        self._record_to_time_window('failure')

    def record_retry(self) -> None:
        """记录重试"""
        self.retries += 1

    def _record_to_time_window(self, status: str) -> None:
        """记录到时间窗口"""
        now = datetime.now()

        # 小时统计
        hour_key = now.strftime('%Y-%m-%d %H:00')
        self._hourly_stats[hour_key][status] += 1

        # 天统计
        day_key = now.strftime('%Y-%m-%d')
        self._daily_stats[day_key][status] += 1

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            'task_name': self.task_name,
            'success': self.success,
            'failure': self.failure,
            'retries': self.retries,
            'total': self.get_total(),
            'success_rate': self.get_success_rate()
        }

    def get_total(self) -> int:
        """获取总计数"""
        return self.success + self.failure

    def get_success_rate(self) -> float:
        """计算成功率"""
        total = self.get_total()
        if total == 0:
            return 0.0
        return round((self.success / total) * 100, 2)

    def get_hourly_stats(self, hours: int = 1) -> dict:
        """获取小时统计"""
        now = datetime.now()
        result = {}

        for i in range(hours):
            hour_time = now - timedelta(hours=i)
            hour_key = hour_time.strftime('%Y-%m-%d %H:00')

            if hour_key in self._hourly_stats:
                result[hour_key] = self._hourly_stats[hour_key].copy()

        return {
            'hour': result,
            'success': sum(s['success'] for s in result.values()),
            'failure': sum(s['failure'] for s in result.values())
        }

    def get_daily_stats(self, days: int = 1) -> dict:
        """获取天统计"""
        now = datetime.now()
        result = {}

        for i in range(days):
            day_time = now - timedelta(days=i)
            day_key = day_time.strftime('%Y-%m-%d')

            if day_key in self._daily_stats:
                result[day_key] = self._daily_stats[day_key].copy()

        return {
            'day': result,
            'success': sum(s['success'] for s in result.values()),
            'failure': sum(s['failure'] for s in result.values()),
            'total': sum(s['success'] + s['failure'] for s in result.values())
        }

    def reset(self) -> None:
        """重置计数器"""
        self.success = 0
        self.failure = 0
        self.retries = 0
        self._hourly_stats.clear()
        self._daily_stats.clear()


# 全局计数器存储
_counters: Dict[str, 'TaskCounter'] = {}


def get_counter(task_name: str, window: str = 'hour') -> TaskCounter:
    """获取任务计数器"""
    key = f"{task_name}:{window}"
    if key not in _counters:
        _counters[key] = TaskCounter(task_name, window)
    return _counters[key]


def reset_all_counters() -> None:
    """重置所有计数器"""
    _counters.clear()