"""
Structured Logging System - TDD Cycle 21

结构化日志系统:
- JSON 格式输出
- 日志级别: DEBUG, INFO, WARNING, ERROR
- 日志分类: extraction, performance, error, audit
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "json"
    output: str = "stdout"


class JSONFormatter(logging.Formatter):
    """JSON 格式日志 formatter"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if hasattr(record, "extra"):
            log_data["extra"] = record.extra

        return json.dumps(log_data)


class StructuredLogger:
    """
    结构化日志记录器

    支持不同分类的日志:
    - extraction: 提取任务日志
    - performance: 性能指标日志
    - error: 错误日志
    - audit: 审计日志
    """

    CATEGORIES = ["extraction", "performance", "error", "audit"]

    def __init__(self, name: str, level: str = "INFO"):
        """
        初始化结构化日志记录器

        Args:
            name: 日志分类名称
            level: 日志级别
        """
        self.name = name
        self.logger = logging.getLogger(f"deer_flow.{name}")
        self.logger.setLevel(getattr(logging, level.upper()))

        # 添加 JSON handler 如果尚未添加
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter())
            self.logger.addHandler(handler)

    def _log(self, level: int, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录日志"""
        extra_data = extra or {}
        extra_data["category"] = self.name

        # 使用 logging 的 extra 参数
        self.logger.log(
            level,
            message,
            extra={"extra": extra_data}
        )

    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录 DEBUG 级别日志"""
        self._log(logging.DEBUG, message, extra)

    def info(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录 INFO 级别日志"""
        self._log(logging.INFO, message, extra)

    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录 WARNING 级别日志"""
        self._log(logging.WARNING, message, extra)

    def error(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录 ERROR 级别日志"""
        self._log(logging.ERROR, message, extra)

    def exception(self, message: str, extra: Optional[Dict[str, Any]] = None):
        """记录异常信息"""
        self.logger.exception(message, extra={"extra": extra})


# 日志记录器缓存
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str) -> StructuredLogger:
    """
    获取指定分类的日志记录器

    Args:
        name: 日志分类名称

    Returns:
        StructuredLogger 实例
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name)
    return _loggers[name]


def get_extraction_logger() -> StructuredLogger:
    """获取提取日志记录器"""
    return get_logger("extraction")


def get_performance_logger() -> StructuredLogger:
    """获取性能日志记录器"""
    return get_logger("performance")


def get_error_logger() -> StructuredLogger:
    """获取错误日志记录器"""
    return get_logger("error")


def get_audit_logger() -> StructuredLogger:
    """获取审计日志记录器"""
    return get_logger("audit")


def configure_logging(level: str = "INFO", format: str = "json"):
    """
    配置全局日志系统

    Args:
        level: 日志级别
        format: 日志格式
    """
    root_logger = logging.getLogger("deer_flow")
    root_logger.setLevel(getattr(logging, level.upper()))

    # 清除现有 handlers
    root_logger.handlers.clear()

    # 添加新的 handler
    handler = logging.StreamHandler(sys.stdout)

    if format == "json":
        handler.setFormatter(JSONFormatter())
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

    root_logger.addHandler(handler)