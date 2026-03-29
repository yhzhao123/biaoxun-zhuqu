"""
Alert System - TDD Cycle 22

告警系统:
- 告警规则配置 (AlertRule)
- 告警条件 (AlertCondition)
- 告警严重级别 (AlertSeverity)
- 通知渠道 (AlertChannel):
  - 日志渠道 (LogAlertChannel)
  - Webhook 渠道 (WebhookAlertChannel)
  - 邮件渠道 (EmailAlertChannel)
- 告警管理器 (AlertManager)
- Dashboard 数据接口
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Protocol
from dataclasses import dataclass, field
from enum import IntEnum
import json

# 邮件发送
try:
    from django.core.mail import send_mail
    DJANGO_EMAIL_AVAILABLE = True
except ImportError:
    DJANGO_EMAIL_AVAILABLE = False
    send_mail = None

# HTTP 请求
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


logger = logging.getLogger(__name__)


class AlertSeverity(IntEnum):
    """告警严重级别"""
    INFO = 0
    WARNING = 1
    CRITICAL = 2


class AlertCondition:
    """告警条件类型"""
    ERROR_RATE = "error_rate"
    LATENCY = "latency"
    SUCCESS_RATE = "success_rate"
    QUEUE_LENGTH = "queue_length"
    CONCURRENT_REQUESTS = "concurrent_requests"


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    condition: str  # AlertCondition 值
    threshold: float
    severity: AlertSeverity
    message: str
    enabled: bool = True
    cooldown_seconds: int = 300  # 冷却时间（秒）

    def evaluate(self, value: float) -> bool:
        """
        评估是否触发告警

        Args:
            value: 当前值

        Returns:
            是否触发告警
        """
        if not self.enabled:
            return False

        # 根据条件类型评估
        if self.condition == AlertCondition.ERROR_RATE:
            # 错误率高于阈值触发
            return value > self.threshold
        elif self.condition == AlertCondition.LATENCY:
            # 延迟高于阈值触发
            return value > self.threshold
        elif self.condition == AlertCondition.SUCCESS_RATE:
            # 成功率低于阈值触发
            return value < self.threshold
        elif self.condition == AlertCondition.QUEUE_LENGTH:
            # 队列长度高于阈值触发
            return value > self.threshold
        elif self.condition == AlertCondition.CONCURRENT_REQUESTS:
            # 并发请求数高于阈值触发
            return value > self.threshold

        return False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "condition": self.condition,
            "threshold": self.threshold,
            "severity": self.severity.name,
            "message": self.message,
            "enabled": self.enabled,
            "cooldown_seconds": self.cooldown_seconds,
        }


@dataclass
class Alert:
    """告警实例"""
    rule: AlertRule
    value: float
    timestamp: datetime
    status: str = "firing"  # "firing", "resolved"
    acknowledged: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule": self.rule.to_dict(),
            "value": self.value,
            "timestamp": self.timestamp.isoformat() + "Z",
            "status": self.status,
            "acknowledged": self.acknowledged,
        }


class AlertChannel(Protocol):
    """告警渠道协议"""

    def send(self, rule: AlertRule, value: float) -> bool:
        """发送告警通知"""
        ...


@dataclass
class LogAlertChannel:
    """日志告警渠道"""
    enabled: bool = True

    def send(self, rule: AlertRule, value: float) -> bool:
        """
        通过日志发送告警

        Args:
            rule: 告警规则
            value: 当前值

        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False

        try:
            from apps.monitoring.logging_ import get_error_logger
            error_logger = get_error_logger()

            message = f"[{rule.severity.name}] {rule.name}: {rule.message} (value: {value}, threshold: {rule.threshold})"

            if rule.severity == AlertSeverity.CRITICAL:
                error_logger.error(message)
            elif rule.severity == AlertSeverity.WARNING:
                error_logger.warning(message)
            else:
                error_logger.info(message)

            return True
        except Exception as e:
            logger.error(f"Failed to send log alert: {e}")
            return False


@dataclass
class WebhookAlertChannel:
    """Webhook 告警渠道"""
    webhook_url: str
    enabled: bool = True
    timeout: int = 10

    def send(self, rule: AlertRule, value: float) -> bool:
        """
        通过 Webhook 发送告警

        Args:
            rule: 告警规则
            value: 当前值

        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False

        if not REQUESTS_AVAILABLE:
            logger.warning("requests library not available for webhook")
            return False

        payload = {
            "alert": rule.name,
            "message": rule.message,
            "severity": rule.severity.name,
            "condition": rule.condition,
            "threshold": rule.threshold,
            "value": value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=self.timeout
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False


@dataclass
class EmailAlertChannel:
    """邮件告警渠道"""
    smtp_host: str
    smtp_port: int
    from_addr: str
    to_addrs: List[str]
    enabled: bool = True
    use_tls: bool = True

    def send(self, rule: AlertRule, value: float) -> bool:
        """
        通过邮件发送告警

        Args:
            rule: 告警规则
            value: 当前值

        Returns:
            是否发送成功
        """
        if not self.enabled:
            return False

        if not DJANGO_EMAIL_AVAILABLE:
            logger.warning("Django email not available")
            return False

        subject = f"[{rule.severity.name}] {rule.name}"
        message = f"""
{rule.message}

Details:
- Condition: {rule.condition}
- Threshold: {rule.threshold}
- Current Value: {value}
- Time: {datetime.utcnow().isoformat()}Z
"""

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=self.from_addr,
                recipient_list=self.to_addrs,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


class AlertHistory:
    """告警历史记录"""

    def __init__(self, max_size: int = 1000):
        self.alerts: List[Alert] = []
        self.max_size = max_size

    def add(self, alert: Alert):
        """添加告警到历史"""
        self.alerts.append(alert)

        # 限制历史大小
        if len(self.alerts) > self.max_size:
            self.alerts = self.alerts[-self.max_size:]

    def get_recent(self, hours: int = 1) -> List[Alert]:
        """获取最近 N 小时的告警"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return [a for a in self.alerts if a.timestamp > cutoff]

    def filter_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """按严重级别过滤"""
        return [a for a in self.alerts if a.rule.severity == severity]

    def filter_by_status(self, status: str) -> List[Alert]:
        """按状态过滤"""
        return [a for a in self.alerts if a.status == status]


class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.channels: List[AlertChannel] = []
        self.history = AlertHistory()
        self.active_alerts: Dict[str, Alert] = {}  # rule.name -> Alert
        self.recovered_alerts: set = set()
        self.cooldown_seconds: int = 300
        self._last_alert_time: Dict[str, datetime] = {}

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> bool:
        """移除告警规则"""
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False

    def add_channel(self, channel: AlertChannel):
        """添加通知渠道"""
        self.channels.append(channel)

    def evaluate(self, value: float, condition: Optional[str] = None) -> List[Alert]:
        """
        评估所有规则并触发告警

        Args:
            value: 当前值
            condition: 可选的特定条件

        Returns:
            触发的告警列表
        """
        triggered_alerts = []

        for rule in self.rules:
            # 如果指定了条件，只评估该条件
            if condition and rule.condition != condition:
                continue

            should_alert = rule.evaluate(value)

            if should_alert:
                # 检查冷却时间
                last_alert = self._last_alert_time.get(rule.name)
                now = datetime.utcnow()

                if last_alert and (now - last_alert).total_seconds() < rule.cooldown_seconds:
                    # 在冷却时间内，跳过
                    continue

                # 创建告警
                alert = Alert(
                    rule=rule,
                    value=value,
                    timestamp=now,
                    status="firing"
                )

                # 添加到历史
                self.history.add(alert)

                # 标记为活跃
                self.active_alerts[rule.name] = alert
                self._last_alert_time[rule.name] = now

                # 发送到所有渠道
                for channel in self.channels:
                    channel.send(rule, value)

                triggered_alerts.append(alert)

            else:
                # 检查是否需要恢复
                if rule.name in self.active_alerts:
                    # 告警恢复
                    alert = self.active_alerts.pop(rule.name)
                    alert.status = "resolved"
                    self.recovered_alerts.add(rule.name)
                    self.history.add(alert)

        return triggered_alerts

    def get_active_alerts(self) -> List[Alert]:
        """获取当前活跃告警"""
        return list(self.active_alerts.values())

    def acknowledge_alert(self, rule_name: str) -> bool:
        """确认告警"""
        if rule_name in self.active_alerts:
            self.active_alerts[rule_name].acknowledged = True
            return True
        return False


# 全局告警管理器
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """获取全局告警管理器"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager


def initialize_default_alerts():
    """初始化默认告警规则"""
    manager = get_alert_manager()

    # 添加默认告警规则
    rules = [
        AlertRule(
            name="High Error Rate",
            condition=AlertCondition.ERROR_RATE,
            threshold=0.1,
            severity=AlertSeverity.CRITICAL,
            message="Error rate exceeds 10%",
            cooldown_seconds=300
        ),
        AlertRule(
            name="High Latency",
            condition=AlertCondition.LATENCY,
            threshold=5.0,
            severity=AlertSeverity.WARNING,
            message="Latency exceeds 5 seconds",
            cooldown_seconds=600
        ),
        AlertRule(
            name="Long Queue",
            condition=AlertCondition.QUEUE_LENGTH,
            threshold=100,
            severity=AlertSeverity.WARNING,
            message="Queue length exceeds 100",
            cooldown_seconds=300
        ),
        AlertRule(
            name="Low Success Rate",
            condition=AlertCondition.SUCCESS_RATE,
            threshold=0.8,
            severity=AlertSeverity.CRITICAL,
            message="Success rate below 80%",
            cooldown_seconds=300
        ),
    ]

    for rule in rules:
        manager.add_rule(rule)

    # 添加默认渠道
    manager.add_channel(LogAlertChannel())


# Dashboard 数据接口

def get_dashboard_data() -> Dict[str, Any]:
    """
    获取 Dashboard 完整数据

    Returns:
        Dashboard 数据字典
    """
    return {
        "metrics": get_dashboard_metrics(),
        "alerts": get_active_alerts(),
        "health": get_health_summary(),
    }


def get_dashboard_metrics() -> Dict[str, float]:
    """
    获取 Dashboard 指标数据

    Returns:
        指标字典
    """
    # 从 metrics 模块获取指标
    try:
        from apps.monitoring.prometheus_metrics import get_metrics_collector

        collector = get_metrics_collector()
        metrics = collector.get_all_metrics()

        # 计算成功率（如果有提取计数和错误）
        extraction_count = metrics.get("extraction_count", 0)
        extraction_errors = metrics.get("extraction_errors", 0)

        if extraction_count > 0:
            success_rate = (extraction_count - extraction_errors) / extraction_count
        else:
            success_rate = 1.0

        # 错误率
        error_rate = extraction_errors / max(extraction_count, 1)

        return {
            "success_rate": success_rate,
            "error_rate": error_rate,
            "avg_latency": metrics.get("extraction_duration", 0),
            "queue_length": metrics.get("queue_length", 0),
            "concurrent_requests": metrics.get("concurrent_requests", 0),
            "cache_hit_rate": metrics.get("cache_hit_rate", 0),
        }
    except Exception as e:
        logger.warning(f"Failed to get metrics: {e}")
        return {
            "success_rate": 1.0,
            "error_rate": 0.0,
            "avg_latency": 0.0,
            "queue_length": 0,
            "concurrent_requests": 0,
            "cache_hit_rate": 0.0,
        }


def get_active_alerts() -> List[Dict[str, Any]]:
    """
    获取当前活跃告警

    Returns:
        活跃告警列表
    """
    manager = get_alert_manager()
    active = manager.get_active_alerts()

    return [alert.to_dict() for alert in active]


def get_health_summary() -> Dict[str, Any]:
    """
    获取健康状态摘要

    Returns:
        健康状态字典
    """
    try:
        from apps.monitoring.health import health_check

        result = health_check()
        return result
    except Exception as e:
        logger.warning(f"Failed to get health: {e}")
        return {
            "overall": "unknown",
            "error": str(e)
        }


def check_and_trigger_alerts():
    """检查并触发告警"""
    manager = get_alert_manager()
    metrics = get_dashboard_metrics()

    # 检查各个条件
    alerts = []

    # 错误率告警
    error_alerts = manager.evaluate(metrics["error_rate"], AlertCondition.ERROR_RATE)
    alerts.extend(error_alerts)

    # 延迟告警
    latency_alerts = manager.evaluate(metrics["avg_latency"], AlertCondition.LATENCY)
    alerts.extend(latency_alerts)

    # 队列长度告警
    queue_alerts = manager.evaluate(metrics["queue_length"], AlertCondition.QUEUE_LENGTH)
    alerts.extend(queue_alerts)

    # 成功率告警
    success_alerts = manager.evaluate(metrics["success_rate"], AlertCondition.SUCCESS_RATE)
    alerts.extend(success_alerts)

    return alerts