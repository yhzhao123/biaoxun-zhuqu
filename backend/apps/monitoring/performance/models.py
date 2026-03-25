"""
Task 061: Performance Monitoring Models
性能监控数据模型 - ApiMetric, DbMetric, QueueMetric, AlertRule
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ApiMetric:
    """API 指标"""
    endpoint: str
    method: str
    response_time: float  # 毫秒
    status_code: int
    timestamp: datetime = field(default_factory=datetime.now)
    request_size: Optional[int] = None
    response_size: Optional[int] = None

    def is_error(self) -> bool:
        """判断是否为错误响应"""
        return self.status_code >= 400

    def is_success(self) -> bool:
        """判断是否为成功响应"""
        return 200 <= self.status_code < 300

    def is_redirect(self) -> bool:
        """判断是否为重定向"""
        return 300 <= self.status_code < 400

    def get_severity(self) -> str:
        """根据状态码获取严重程度"""
        if 200 <= self.status_code < 300:
            return 'success'
        elif 300 <= self.status_code < 400:
            return 'info'
        elif 400 <= self.status_code < 500:
            return 'warning'
        elif 500 <= self.status_code:
            return 'error'
        return 'unknown'


@dataclass
class DbMetric:
    """数据库指标"""
    pool_size: int
    active_connections: int
    wait_time: float  # 秒
    timestamp: datetime = field(default_factory=datetime.now)
    query_time: Optional[float] = None  # 查询耗时
    connection_timeout: int = 30  # 连接超时秒数

    def get_pool_usage(self) -> float:
        """获取连接池使用率（百分比）"""
        if self.pool_size == 0:
            return 0.0
        return round((self.active_connections / self.pool_size) * 100, 2)

    def is_pool_exhausted(self) -> bool:
        """判断连接池是否耗尽"""
        return self.active_connections >= self.pool_size

    def is_high_wait_time(self, threshold: float = 1.0) -> bool:
        """判断等待时间是否过高"""
        return self.wait_time > threshold


@dataclass
class QueueMetric:
    """队列指标"""
    queue_name: str
    length: int  # 队列长度
    worker_count: int  # Worker 数量
    timestamp: datetime = field(default_factory=datetime.now)
    consumer_count: int = 0  # 消费者数量
    scheduled_count: int = 0  # 调度任务数
    reserved_count: int = 0  # 保留任务数

    def is_empty(self) -> bool:
        """判断队列是否为空"""
        return self.length == 0

    def is_backlogged(self, threshold: int = 1000) -> bool:
        """判断是否积压"""
        return self.length > threshold

    def get_worker_utilization(self) -> float:
        """计算 Worker 利用率"""
        if self.worker_count == 0:
            return 0.0
        # 简单计算：消费者数/Worker数
        return round((self.consumer_count / self.worker_count) * 100, 2)


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric_type: str  # api, db, queue
    threshold: float
    severity: str = 'warning'  # info, warning, critical
    cooldown_seconds: int = 60  # 冷却期秒数
    enabled: bool = True
    description: str = ''

    def should_trigger(self, metric_data: dict) -> bool:
        """
        判断是否应触发告警

        Args:
            metric_data: 指标数据

        Returns:
            是否触发
        """
        if not self.enabled:
            return False

        # 根据指标类型检查阈值
        if self.metric_type == 'api':
            response_time = metric_data.get('response_time', 0)
            return response_time > self.threshold

        elif self.metric_type == 'db':
            pool_usage = metric_data.get('pool_usage', 0)
            wait_time = metric_data.get('wait_time', 0)
            return pool_usage > self.threshold or wait_time > self.threshold

        elif self.metric_type == 'queue':
            queue_length = metric_data.get('length', 0)
            return queue_length > self.threshold

        elif self.metric_type == 'error_rate':
            error_rate = metric_data.get('error_rate', 0)
            return error_rate > self.threshold

        return False

    def get_severity_score(self) -> int:
        """获取严重程度分数"""
        severity_scores = {
            'info': 1,
            'warning': 2,
            'critical': 3
        }
        return severity_scores.get(self.severity, 1)


@dataclass
class Alert:
    """告警实例"""
    rule: AlertRule
    metric_data: dict
    triggered_at: datetime = field(default_factory=datetime.now)
    acknowledged: bool = False
    resolved: bool = False

    def get_message(self) -> str:
        """获取告警消息"""
        return f"[{self.rule.severity.upper()}] {self.rule.name}: {self.rule.description}"

    def acknowledge(self) -> None:
        """确认告警"""
        self.acknowledged = True

    def resolve(self) -> None:
        """解决告警"""
        self.resolved = True