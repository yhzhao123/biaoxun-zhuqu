"""
Task 061: Alert Manager
告警系统 - 可配置阈值、冷却期处理
"""
from typing import List, Dict, Optional
from collections import deque
from datetime import datetime, timedelta

from apps.monitoring.performance.models import AlertRule, Alert


class AlertManager:
    """告警管理器"""

    MAX_ALERTS = 1000

    def __init__(self, cooldown_seconds: int = 60):
        """
        初始化告警管理器

        Args:
            cooldown_seconds: 全局冷却期（秒）
        """
        self.rules: List[AlertRule] = []
        self.alerts: deque = deque(maxlen=self.MAX_ALERTS)
        self.cooldown_seconds = cooldown_seconds
        self._last_alert_time: Dict[str, datetime] = {}
        self._active_alerts: Dict[str, Alert] = {}

    def add_rule(self, rule: AlertRule) -> None:
        """
        添加告警规则

        Args:
            rule: AlertRule 实例
        """
        self.rules.append(rule)

    def remove_rule(self, rule_name: str) -> bool:
        """
        移除告警规则

        Args:
            rule_name: 规则名称

        Returns:
            是否成功移除
        """
        for i, rule in enumerate(self.rules):
            if rule.name == rule_name:
                self.rules.pop(i)
                return True
        return False

    def enable_rule(self, rule_name: str) -> bool:
        """启用规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = True
                return True
        return False

    def disable_rule(self, rule_name: str) -> bool:
        """禁用规则"""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = False
                return True
        return False

    def check_threshold(self, metric_type: str, metric_data: dict) -> List[Alert]:
        """
        检查阈值是否触发告警

        Args:
            metric_type: 指标类型
            metric_data: 指标数据

        Returns:
            告警列表
        """
        triggered_alerts = []

        for rule in self.rules:
            if not rule.enabled:
                continue

            if rule.metric_type != metric_type:
                continue

            if rule.should_trigger(metric_data):
                # 检查冷却期
                if self._is_in_cooldown(rule.name):
                    continue

                # 创建告警
                alert = Alert(
                    rule=rule,
                    metric_data=metric_data
                )
                triggered_alerts.append(alert)

                # 记录告警
                self.alerts.append(alert)
                self._last_alert_time[rule.name] = datetime.now()
                self._active_alerts[f"{rule.name}:{metric_type}"] = alert

        return triggered_alerts

    def _is_in_cooldown(self, rule_name: str) -> bool:
        """
        检查是否在冷却期内

        Args:
            rule_name: 规则名称

        Returns:
            是否在冷却期
        """
        if rule_name not in self._last_alert_time:
            return False

        last_alert = self._last_alert_time[rule_name]
        cooldown = timedelta(seconds=self.cooldown_seconds)

        return datetime.now() - last_alert < cooldown

    def get_active_alerts(self) -> List[Alert]:
        """获取活动告警"""
        return list(self._active_alerts.values())

    def get_recent_alerts(self, count: int = 50) -> List[Alert]:
        """获取最近的告警"""
        return list(self.alerts)[-count:]

    def get_alerts_by_severity(self, severity: str) -> List[Alert]:
        """按严重程度获取告警"""
        return [alert for alert in self.alerts if alert.rule.severity == severity]

    def acknowledge_alert(self, rule_name: str) -> bool:
        """确认告警"""
        for alert in self._active_alerts.values():
            if alert.rule.name == rule_name:
                alert.acknowledge()
                return True
        return False

    def resolve_alert(self, rule_name: str) -> bool:
        """解决告警"""
        key_to_remove = None
        for key, alert in self._active_alerts.items():
            if alert.rule.name == rule_name:
                alert.resolve()
                key_to_remove = key
                break

        if key_to_remove:
            del self._active_alerts[key_to_remove]
            return True
        return False

    def clear_alerts(self) -> None:
        """清除所有告警"""
        self.alerts.clear()
        self._active_alerts.clear()
        self._last_alert_time.clear()

    def get_alert_stats(self) -> dict:
        """获取告警统计"""
        if not self.alerts:
            return {
                'total': 0,
                'active': len(self._active_alerts),
                'by_severity': {},
                'by_type': {}
            }

        by_severity = {}
        by_type = {}

        for alert in self.alerts:
            severity = alert.rule.severity
            metric_type = alert.rule.metric_type

            by_severity[severity] = by_severity.get(severity, 0) + 1
            by_type[metric_type] = by_type.get(metric_type, 0) + 1

        return {
            'total': len(self.alerts),
            'active': len(self._active_alerts),
            'by_severity': by_severity,
            'by_type': by_type,
            'rules_count': len(self.rules),
            'enabled_rules': sum(1 for r in self.rules if r.enabled)
        }

    def create_default_rules(self) -> None:
        """创建默认告警规则"""
        default_rules = [
            AlertRule(
                name='high_response_time',
                metric_type='api',
                threshold=3000,
                severity='warning',
                description='API response time exceeds 3 seconds'
            ),
            AlertRule(
                name='critical_response_time',
                metric_type='api',
                threshold=10000,
                severity='critical',
                description='API response time exceeds 10 seconds'
            ),
            AlertRule(
                name='high_error_rate',
                metric_type='error_rate',
                threshold=10,
                severity='warning',
                description='Error rate exceeds 10%'
            ),
            AlertRule(
                name='db_pool_exhausted',
                metric_type='db',
                threshold=90,
                severity='critical',
                description='Database connection pool usage exceeds 90%'
            ),
            AlertRule(
                name='queue_backlog',
                metric_type='queue',
                threshold=1000,
                severity='warning',
                description='Queue backlog exceeds 1000 tasks'
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)


# 全局告警管理器
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """获取全局告警管理器"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager