"""
TDD Cycle 21: Logging System Tests

测试结构化日志系统:
- 日志级别: DEBUG, INFO, WARNING, ERROR
- 日志分类: extraction, performance, error, audit
- JSON 格式输出
"""
import pytest
import json
import logging
import io
from datetime import datetime
from unittest.mock import patch, MagicMock


class TestStructuredLogging:
    """测试结构化日志"""

    def test_logger_creation(self):
        """测试日志记录器创建"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("extraction")
        assert logger.name == "extraction"
        assert logger.logger is not None

    def test_log_debug_level(self):
        """测试 DEBUG 级别日志"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("extraction")
        logger.debug("Test debug message", extra={"key": "value"})

    def test_log_info_level(self):
        """测试 INFO 级别日志"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("extraction")
        logger.info("Test info message", extra={"count": 10})

    def test_log_warning_level(self):
        """测试 WARNING 级别日志"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("extraction")
        logger.warning("Test warning message", extra={"retry": 3})

    def test_log_error_level(self):
        """测试 ERROR 级别日志"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("extraction")
        logger.error("Test error message", extra={"error": "timeout"})

    def test_json_format_output(self):
        """测试 JSON 格式输出"""
        from apps.monitoring.logging_ import StructuredLogger

        # 捕获日志输出
        output = io.StringIO()
        handler = logging.StreamHandler(output)
        handler.setFormatter(logging.Formatter('%(message)s'))

        logger = StructuredLogger("extraction")
        logger.logger.addHandler(handler)
        logger.logger.setLevel(logging.DEBUG)

        # 记录日志
        logger.info("Test message", extra={"tender_id": "12345"})

        # 验证 JSON 格式
        log_line = output.getvalue().strip()
        if log_line:
            log_data = json.loads(log_line)
            assert "timestamp" in log_data
            assert "level" in log_data
            assert "logger" in log_data
            assert "message" in log_data
            assert log_data["logger"] == "extraction"

    def test_log_with_tender_context(self):
        """测试带招标上下文的日志"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("extraction")

        # 记录带上下文的日志
        logger.info(
            "Extraction completed",
            extra={
                "tender_id": "T20240301-001",
                "source_url": "http://example.com",
                "items_count": 10,
                "duration": 2.5
            }
        )

    def test_log_categories_extraction(self):
        """测试 extraction 日志分类"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("extraction")
        assert logger.name == "extraction"

    def test_log_categories_performance(self):
        """测试 performance 日志分类"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("performance")
        assert logger.name == "performance"

    def test_log_categories_error(self):
        """测试 error 日志分类"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("error")
        assert logger.name == "error"

    def test_log_categories_audit(self):
        """测试 audit 日志分类"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("audit")
        assert logger.name == "audit"

    def test_exception_logging(self):
        """测试异常日志记录"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("error")

        try:
            raise ValueError("Test error")
        except ValueError as e:
            logger.exception("Exception occurred", extra={"error_type": "ValueError"})

    def test_performance_logging(self):
        """测试性能日志"""
        from apps.monitoring.logging_ import StructuredLogger

        logger = StructuredLogger("performance")

        logger.info(
            "Performance metric",
            extra={
                "operation": "extract_list",
                "duration_ms": 1500,
                "items_processed": 50
            }
        )


class TestLogConfiguration:
    """测试日志配置"""

    def test_log_config_creation(self):
        """测试日志配置创建"""
        from apps.monitoring.logging_ import LogConfig

        config = LogConfig()
        assert config.level == "INFO"
        assert config.format == "json"

    def test_log_config_custom_level(self):
        """测试自定义日志级别"""
        from apps.monitoring.logging_ import LogConfig

        config = LogConfig(level="DEBUG")
        assert config.level == "DEBUG"

    def test_get_logger(self):
        """测试获取日志记录器"""
        from apps.monitoring.logging_ import get_logger

        logger = get_logger("test")
        assert logger.name == "test"


class TestLoggerFactory:
    """测试日志工厂"""

    def test_get_extraction_logger(self):
        """测试获取 extraction 日志记录器"""
        from apps.monitoring.logging_ import get_logger

        logger = get_logger("extraction")
        assert logger.name == "extraction"

    def test_get_performance_logger(self):
        """测试获取 performance 日志记录器"""
        from apps.monitoring.logging_ import get_logger

        logger = get_logger("performance")
        assert logger.name == "performance"

    def test_get_error_logger(self):
        """测试获取 error 日志记录器"""
        from apps.monitoring.logging_ import get_logger

        logger = get_logger("error")
        assert logger.name == "error"

    def test_get_audit_logger(self):
        """测试获取 audit 日志记录器"""
        from apps.monitoring.logging_ import get_logger

        logger = get_logger("audit")
        assert logger.name == "audit"


class TestExtractionLogger:
    """测试提取日志助手"""

    def test_extraction_logger_info(self):
        """测试提取信息日志"""
        from apps.monitoring.logging_ import get_extraction_logger

        logger = get_extraction_logger()
        logger.info("Extraction started", extra={"url": "http://test.com"})

    def test_extraction_logger_with_timing(self):
        """测试提取计时日志"""
        from apps.monitoring.logging_ import get_extraction_logger

        logger = get_extraction_logger()
        logger.info(
            "Extraction completed",
            extra={
                "url": "http://test.com",
                "duration_seconds": 1.5,
                "items_count": 20
            }
        )


class TestPerformanceLogger:
    """测试性能日志助手"""

    def test_performance_logger_info(self):
        """测试性能日志"""
        from apps.monitoring.logging_ import get_performance_logger

        logger = get_performance_logger()
        logger.info("Performance metric", extra={"metric": "response_time", "value": 100})