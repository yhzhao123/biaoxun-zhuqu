"""
Performance Monitoring - TDD Cycle 25

性能监控模块:
- 内存监控
- 性能阈值管理
- 性能报告生成
"""
import gc
import logging
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ========== Memory Monitor ==========


class MemoryMonitor:
    """
    内存使用监控器

    功能:
    - 追踪当前内存使用
    - 记录内存基线
    - 检测内存增长
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._baseline: Optional[float] = None
        self._memory_samples: List[Dict[str, Any]] = []

    def get_current_memory(self) -> float:
        """
        获取当前内存使用（MB）

        Returns:
            当前内存使用（MB）
        """
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except ImportError:
            # 如果 psutil 不可用，返回估算值
            import sys
            return sys.getsizeof(globals()) / (1024 * 1024)

    def record_baseline(self) -> None:
        """记录内存基线"""
        self._baseline = self.get_current_memory()
        self.logger.info(f"Memory baseline recorded: {self._baseline:.2f}MB")

    def get_baseline(self) -> float:
        """获取内存基线"""
        if self._baseline is None:
            self.record_baseline()
        return self._baseline or 0.0

    def record_memory_usage(self, operation: str) -> None:
        """
        记录内存使用

        Args:
            operation: 操作名称
        """
        current = self.get_current_memory()
        self._memory_samples.append({
            "operation": operation,
            "memory_mb": current,
            "timestamp": time.time()
        })

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取内存统计

        Returns:
            内存统计字典
        """
        baseline = self.get_baseline()
        current = self.get_current_memory()

        stats = {
            "baseline_mb": baseline,
            "current_mb": current,
            "growth_mb": current - baseline if baseline else 0,
            "sample_count": len(self._memory_samples)
        }

        if self._memory_samples:
            stats["samples"] = self._memory_samples[-10:]  # 最近10条

        return stats


# ========== Threshold Level ==========


class ThresholdLevel(Enum):
    """阈值级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ========== Threshold Result ==========


@dataclass
class ThresholdResult:
    """阈值检查结果"""
    operation: str
    value: float
    threshold: float
    passed: bool
    level: ThresholdLevel = ThresholdLevel.INFO
    message: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# ========== Threshold Alert ==========


@dataclass
class ThresholdAlert:
    """阈值告警"""
    operation: str
    value: float
    threshold: float
    level: ThresholdLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


# ========== Performance Thresholds ==========


class PerformanceThresholds:
    """
    性能阈值管理器

    功能:
    - 设置响应时间阈值
    - 设置吞吐量阈值
    - 设置错误率阈值
    - 触发告警
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._response_time_thresholds: Dict[str, Dict[str, Any]] = {}
        self._throughput_thresholds: Dict[str, Dict[str, Any]] = {}
        self._error_rate_thresholds: Dict[str, float] = {}
        self._alert_handlers: List[Callable[[ThresholdAlert], None]] = []

        # 设置默认阈值
        self._setup_default_thresholds()

    def _setup_default_thresholds(self) -> None:
        """设置默认阈值"""
        self.set_response_time_threshold("list_fetch", 2.0, ThresholdLevel.WARNING)
        self.set_response_time_threshold("detail_fetch", 3.0, ThresholdLevel.WARNING)
        self.set_throughput_threshold("list_fetch", min_throughput=1.0)
        self.set_error_rate_threshold("fetch", 0.1)

    def set_response_time_threshold(
        self,
        operation: str,
        threshold: float,
        level: ThresholdLevel = ThresholdLevel.WARNING
    ) -> None:
        """
        设置响应时间阈值

        Args:
            operation: 操作名称
            threshold: 阈值（秒）
            level: 阈值级别
        """
        self._response_time_thresholds[operation] = {
            "threshold": threshold,
            "level": level
        }
        self.logger.debug(f"Set response time threshold for {operation}: {threshold}s")

    def set_throughput_threshold(
        self,
        operation: str,
        min_throughput: float = 1.0
    ) -> None:
        """
        设置吞吐量阈值

        Args:
            operation: 操作名称
            min_throughput: 最小吞吐量（items/s）
        """
        self._throughput_thresholds[operation] = {
            "min_throughput": min_throughput
        }

    def set_error_rate_threshold(
        self,
        operation: str,
        max_error_rate: float
    ) -> None:
        """
        设置错误率阈值

        Args:
            operation: 操作名称
            max_error_rate: 最大错误率（0.0-1.0）
        """
        self._error_rate_thresholds[operation] = max_error_rate

    def get_default_response_time_threshold(self) -> float:
        """获取默认响应时间阈值"""
        return self._response_time_thresholds.get("list_fetch", {}).get("threshold", 2.0)

    def check_response_time(
        self,
        operation: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ThresholdResult:
        """
        检查响应时间是否超过阈值

        Args:
            operation: 操作名称
            duration: 响应时间（秒）
            metadata: 附加元数据

        Returns:
            ThresholdResult: 检查结果
        """
        threshold_config = self._response_time_thresholds.get(operation)
        if not threshold_config:
            # 如果没有设置阈值，返回通过
            return ThresholdResult(
                operation=operation,
                value=duration,
                threshold=0,
                passed=True,
                message="No threshold configured"
            )

        threshold = threshold_config["threshold"]
        level = threshold_config["level"]
        passed = duration <= threshold

        result = ThresholdResult(
            operation=operation,
            value=duration,
            threshold=threshold,
            passed=passed,
            level=level if not passed else ThresholdLevel.INFO,
            message=f"{operation} took {duration:.2f}s (threshold: {threshold}s)",
            metadata=metadata or {}
        )

        # 触发告警
        if not passed:
            self._trigger_alert(result)

        return result

    def check_throughput(
        self,
        operation: str,
        throughput: float
    ) -> ThresholdResult:
        """
        检查吞吐量是否满足要求

        Args:
            operation: 操作名称
            throughput: 吞吐量（items/s）

        Returns:
            ThresholdResult: 检查结果
        """
        threshold_config = self._throughput_thresholds.get(operation)
        if not threshold_config:
            return ThresholdResult(
                operation=operation,
                value=throughput,
                threshold=0,
                passed=True
            )

        min_throughput = threshold_config["min_throughput"]
        passed = throughput >= min_throughput

        return ThresholdResult(
            operation=operation,
            value=throughput,
            threshold=min_throughput,
            passed=passed,
            level=ThresholdLevel.WARNING if not passed else ThresholdLevel.INFO,
            message=f"{operation} throughput: {throughput:.2f} items/s (min: {min_throughput})"
        )

    def check_error_rate(
        self,
        operation: str,
        error_count: int,
        total_count: int
    ) -> ThresholdResult:
        """
        检查错误率是否超过阈值

        Args:
            operation: 操作名称
            error_count: 错误数量
            total_count: 总数量

        Returns:
            ThresholdResult: 检查结果
        """
        max_error_rate = self._error_rate_thresholds.get(operation, 1.0)

        if total_count == 0:
            return ThresholdResult(
                operation=operation,
                value=0,
                threshold=max_error_rate,
                passed=True
            )

        error_rate = error_count / total_count
        passed = error_rate <= max_error_rate

        return ThresholdResult(
            operation=operation,
            value=error_rate,
            threshold=max_error_rate,
            passed=passed,
            level=ThresholdLevel.CRITICAL if not passed else ThresholdLevel.INFO,
            message=f"{operation} error rate: {error_rate*100:.1f}% (max: {max_error_rate*100}%)"
        )

    def register_alert_handler(
        self,
        handler: Callable[[ThresholdAlert], None]
    ) -> None:
        """
        注册告警处理器

        Args:
            handler: 告警处理函数
        """
        self._alert_handlers.append(handler)

    def _trigger_alert(self, result: ThresholdResult) -> None:
        """触发告警"""
        alert = ThresholdAlert(
            operation=result.operation,
            value=result.value,
            threshold=result.threshold,
            level=result.level,
            message=result.message
        )

        for handler in self._alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Alert handler error: {e}")

    def get_threshold_summary(self) -> Dict[str, Any]:
        """获取阈值配置汇总"""
        return {
            "response_time": self._response_time_thresholds,
            "throughput": self._throughput_thresholds,
            "error_rate": self._error_rate_thresholds
        }


# ========== Performance Reporter ==========


class PerformanceReporter:
    """
    性能报告生成器

    功能:
    - 收集性能指标
    - 生成汇总报告
    - 导出 JSON 格式
    """

    def __init__(self, include_timing: bool = True):
        self.logger = logging.getLogger(__name__)
        self._include_timing = include_timing
        self._operations: List[Dict[str, Any]] = []

    def record_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        记录操作

        Args:
            operation: 操作名称
            duration: 持续时间（秒）
            success: 是否成功
            metadata: 附加元数据
        """
        self._operations.append({
            "operation": operation,
            "duration": duration,
            "success": success,
            "timestamp": time.time(),
            "metadata": metadata or {}
        })

    def collect_metrics(self) -> Dict[str, Any]:
        """
        收集指标数据

        Returns:
            指标字典
        """
        from apps.crawler.deer_flow.metrics import get_metrics

        metrics = get_metrics()
        all_stats = metrics.get_all_stats()

        return {
            "timings": all_stats.get("timings", {}),
            "counters": all_stats.get("counters", {}),
            "gauges": all_stats.get("gauges", {})
        }

    def generate_summary_report(self) -> Dict[str, Any]:
        """
        生成汇总报告

        Returns:
            汇总报告字典
        """
        metrics_data = self.collect_metrics()

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_operations": len(self._operations),
                "operations": self._operations
            },
            "metrics": metrics_data
        }

        # 计算统计信息
        if self._operations:
            durations = [op["duration"] for op in self._operations]
            report["summary"]["avg_duration"] = sum(durations) / len(durations)
            report["summary"]["max_duration"] = max(durations)
            report["summary"]["min_duration"] = min(durations)
            report["summary"]["success_count"] = sum(1 for op in self._operations if op["success"])

        return report

    def generate_detailed_report(self) -> Dict[str, Any]:
        """
        生成详细报告

        Returns:
            详细报告字典
        """
        report = self.generate_summary_report()

        # 按操作分组
        operations_by_type: Dict[str, List[Dict]] = {}
        for op in self._operations:
            op_type = op["operation"]
            if op_type not in operations_by_type:
                operations_by_type[op_type] = []
            operations_by_type[op_type].append(op)

        report["operations_by_type"] = {}
        for op_type, ops in operations_by_type.items():
            durations = [o["duration"] for o in ops]
            report["operations_by_type"][op_type] = {
                "count": len(ops),
                "avg_duration": sum(durations) / len(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
                "max_duration": max(durations) if durations else 0,
                "success_rate": sum(1 for o in ops if o["success"]) / len(ops) if ops else 0
            }

        return report

    def generate_json_report(self) -> str:
        """
        生成 JSON 格式报告

        Returns:
            JSON 字符串
        """
        import json
        return json.dumps(self.generate_detailed_report(), indent=2, ensure_ascii=False)

    def export_to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return self.generate_detailed_report()

    def export_to_json(self) -> str:
        """导出为 JSON 字符串"""
        return self.generate_json_report()


# ========== Global Instances ==========


_memory_monitor: Optional[MemoryMonitor] = None
_performance_thresholds: Optional[PerformanceThresholds] = None
_performance_reporter: Optional[PerformanceReporter] = None


def get_memory_monitor() -> MemoryMonitor:
    """获取内存监控器实例"""
    global _memory_monitor
    if _memory_monitor is None:
        _memory_monitor = MemoryMonitor()
    return _memory_monitor


def get_performance_thresholds() -> PerformanceThresholds:
    """获取性能阈值管理器实例"""
    global _performance_thresholds
    if _performance_thresholds is None:
        _performance_thresholds = PerformanceThresholds()
    return _performance_thresholds


def get_performance_reporter() -> PerformanceReporter:
    """获取性能报告生成器实例"""
    global _performance_reporter
    if _performance_reporter is None:
        _performance_reporter = PerformanceReporter()
    return _performance_reporter