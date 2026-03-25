"""
Task 059: Crawler Monitoring Models
爬虫监控数据模型 - TaskRecord, TaskCounter, FlowerTask
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class TaskRecord:
    """爬虫任务记录"""
    task_id: str
    name: str
    status: str = 'pending'  # pending, running, success, failure, retry
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    error_message: Optional[str] = None
    result: Optional[dict] = None

    def is_running(self) -> bool:
        return self.status == 'running'

    def is_completed(self) -> bool:
        return self.status == 'success'

    def is_failed(self) -> bool:
        return self.status == 'failure'

    def duration(self) -> Optional[float]:
        """返回任务执行时长（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


@dataclass
class TaskCounter:
    """任务计数器 - 聚合统计"""
    task_name: str
    window: str = 'hour'  # hour, day
    success_count: int = 0
    failure_count: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def increment_success(self) -> None:
        """增加成功计数"""
        self.success_count += 1

    def increment_failure(self) -> None:
        """增加失败计数"""
        self.failure_count += 1

    def get_total_count(self) -> int:
        """获取总计数"""
        return self.success_count + self.failure_count

    def get_success_rate(self) -> float:
        """计算成功率（百分比）"""
        total = self.get_total_count()
        if total == 0:
            return 0.0
        return round((self.success_count / total) * 100, 2)


@dataclass
class FlowerTask:
    """Flower API 响应解析"""
    id: str
    name: str
    status: str
    startTime: Optional[int] = None
    endTime: Optional[int] = None
    runtime: Optional[float] = None
    worker: Optional[str] = None
    result: Optional[str] = None
    retries: int = 0

    @property
    def start_time(self) -> Optional[datetime]:
        """将时间戳转换为 datetime"""
        if self.startTime:
            return datetime.fromtimestamp(self.startTime)
        return None

    @property
    def end_time(self) -> Optional[datetime]:
        """将时间戳转换为 datetime"""
        if self.endTime:
            return datetime.fromtimestamp(self.endTime)
        return None

    @property
    def is_success(self) -> bool:
        return self.status == 'SUCCESS'

    @property
    def is_failure(self) -> bool:
        return self.status == 'FAILURE'

    @property
    def is_running(self) -> bool:
        return self.status in ('STARTED', 'PENDING', 'RECEIVED')