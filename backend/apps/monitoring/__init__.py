# Monitoring App - Crawler Monitoring Module
# TDD Cycle 21 - Monitoring Implementation

from .logging_ import (
    StructuredLogger,
    get_logger,
    get_extraction_logger,
    get_performance_logger,
    get_error_logger,
    get_audit_logger,
    configure_logging,
)

from .prometheus_metrics import (
    MetricsCollector,
    MetricsExporter,
    MetricsMiddleware,
    get_metrics_collector,
    generate_metrics,
    track_extraction_time,
    track_extraction,
    extraction_count,
    extraction_errors,
    extraction_duration,
    cache_hit_rate,
    concurrent_requests,
    queue_length,
)

from .health import (
    health_check,
    check_gateway,
    check_redis,
    check_database,
    check_error_rate,
    calculate_error_rate,
    HealthStatus,
    HealthConfig,
    get_health_status,
)

__all__ = [
    # Logging
    "StructuredLogger",
    "get_logger",
    "get_extraction_logger",
    "get_performance_logger",
    "get_error_logger",
    "get_audit_logger",
    "configure_logging",
    # Metrics
    "MetricsCollector",
    "MetricsExporter",
    "MetricsMiddleware",
    "get_metrics_collector",
    "generate_metrics",
    "track_extraction_time",
    "track_extraction",
    "extraction_count",
    "extraction_errors",
    "extraction_duration",
    "cache_hit_rate",
    "concurrent_requests",
    "queue_length",
    # Health
    "health_check",
    "check_gateway",
    "check_redis",
    "check_database",
    "check_error_rate",
    "calculate_error_rate",
    "HealthStatus",
    "HealthConfig",
    "get_health_status",
]