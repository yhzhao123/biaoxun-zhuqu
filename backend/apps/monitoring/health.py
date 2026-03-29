"""
Health Check - TDD Cycle 21

健康检查系统:
- Gateway 连接检查
- Redis 连接检查
- Database 连接检查
- 错误率计算
"""
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Django imports
try:
    from django.core import cache
    from django.db import connection
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False
    cache = None
    connection = None

# HTTP requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None


@dataclass
class HealthConfig:
    """健康检查配置"""
    gateway_url: str = "http://localhost:8001/health"
    redis_timeout: int = 5
    database_timeout: int = 5
    error_rate_threshold: float = 0.1
    check_interval: int = 60


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    name: str
    status: str  # "healthy", "unhealthy"
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class HealthStatus:
    """健康状态管理"""

    def __init__(self):
        self.checks: Dict[str, HealthCheckResult] = {}

    def add_check(self, name: str, healthy: bool, message: str = "", details: Optional[Dict] = None):
        """添加健康检查结果"""
        self.checks[name] = HealthCheckResult(
            name=name,
            status="healthy" if healthy else "unhealthy",
            message=message,
            details=details or {}
        )

    def get_overall(self) -> str:
        """获取总体健康状态"""
        if not self.checks:
            return "unknown"

        # 如果有任何不健康的检查，返回 unhealthy
        unhealthy_count = sum(1 for c in self.checks.values() if c.status == "unhealthy")

        if unhealthy_count == len(self.checks):
            return "unhealthy"
        elif unhealthy_count > 0:
            return "degraded"
        else:
            return "healthy"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "checks": {
                name: {
                    "status": result.status,
                    "message": result.message,
                    "details": result.details
                }
                for name, result in self.checks.items()
            },
            "overall": self.get_overall()
        }


def check_gateway(config: Optional[HealthConfig] = None) -> Dict[str, Any]:
    """
    检查 Gateway 连接

    Args:
        config: 健康检查配置

    Returns:
        检查结果字典
    """
    config = config or HealthConfig()

    if not REQUESTS_AVAILABLE:
        return {
            "status": "unknown",
            "message": "requests library not available"
        }

    try:
        response = requests.get(
            config.gateway_url,
            timeout=config.redis_timeout
        )

        if response.status_code == 200:
            return {
                "status": "healthy",
                "message": "Gateway is reachable",
                "response_time_ms": response.elapsed.total_seconds() * 1000
            }
        else:
            return {
                "status": "unhealthy",
                "message": f"Gateway returned status {response.status_code}"
            }

    except requests.Timeout:
        return {
            "status": "unhealthy",
            "message": "Gateway connection timeout"
        }

    except requests.ConnectionError:
        return {
            "status": "unhealthy",
            "message": "Gateway is unreachable"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Gateway check failed: {str(e)}"
        }


def check_redis(config: Optional[HealthConfig] = None) -> Dict[str, Any]:
    """
    检查 Redis 连接

    Args:
        config: 健康检查配置

    Returns:
        检查结果字典
    """
    config = config or HealthConfig()

    if not DJANGO_AVAILABLE:
        return {
            "status": "unknown",
            "message": "Django not available"
        }

    try:
        # 尝试获取缓存
        cache.cache.set("health_check", "ok", 10)
        value = cache.cache.get("health_check")

        if value == "ok":
            return {
                "status": "healthy",
                "message": "Redis is reachable"
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Redis returned unexpected value"
            }

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Redis connection failed: {str(e)}"
        }


def check_database(config: Optional[HealthConfig] = None) -> Dict[str, Any]:
    """
    检查 Database 连接

    Args:
        config: 健康检查配置

    Returns:
        检查结果字典
    """
    config = config or HealthConfig()

    if not DJANGO_AVAILABLE:
        return {
            "status": "unknown",
            "message": "Django not available"
        }

    try:
        # 尝试连接数据库
        connection.ensure_connection()

        # 获取数据库信息
        vendor = connection.settings_dict.get("ENGINE", "")

        return {
            "status": "healthy",
            "message": f"Database is reachable ({vendor})"
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }


# 错误记录存储（内存中）
_error_records: List[Dict[str, Any]] = []


def record_error(source_url: str, error_type: str, error_message: str):
    """
    记录错误用于错误率计算

    Args:
        source_url: 源 URL
        error_type: 错误类型
        error_message: 错误信息
    """
    _error_records.append({
        "timestamp": datetime.utcnow(),
        "source_url": source_url,
        "error_type": error_type,
        "error_message": error_message
    })

    # 清理旧记录（只保留1小时内）
    cutoff = datetime.utcnow() - timedelta(hours=1)
    _error_records[:] = [r for r in _error_records if r["timestamp"] > cutoff]


def calculate_error_rate(hours: int = 1) -> float:
    """
    计算最近 N 小时的错误率

    Args:
        hours: 小时数

    Returns:
        错误率 (0.0 - 1.0)
    """
    cutoff = datetime.utcnow() - timedelta(hours=hours)

    # 过滤时间范围内的错误
    recent_errors = [r for r in _error_records if r["timestamp"] > cutoff]

    # 简单计算：假设总请求数 = 错误数 * 10（粗略估计）
    total_requests = len(recent_errors) * 10

    if total_requests == 0:
        return 0.0

    return len(recent_errors) / total_requests


def check_error_rate(config: Optional[HealthConfig] = None) -> Dict[str, Any]:
    """
    检查错误率

    Args:
        config: 健康检查配置

    Returns:
        检查结果字典
    """
    config = config or HealthConfig()

    error_rate = calculate_error_rate(hours=1)

    if error_rate < config.error_rate_threshold:
        return {
            "status": "healthy",
            "message": f"Error rate is {error_rate:.2%}",
            "error_rate": error_rate
        }
    elif error_rate < config.error_rate_threshold * 2:
        return {
            "status": "degraded",
            "message": f"Error rate is {error_rate:.2%}",
            "error_rate": error_rate
        }
    else:
        return {
            "status": "unhealthy",
            "message": f"Error rate is {error_rate:.2%}",
            "error_rate": error_rate
        }


def health_check(request=None) -> Dict[str, Any]:
    """
    执行完整的健康检查

    Args:
        request: Django 请求对象

    Returns:
        健康检查结果字典
    """
    config = HealthConfig()

    status = HealthStatus()

    # 检查 Gateway
    gateway_result = check_gateway(config)
    status.add_check(
        "gateway",
        gateway_result["status"] == "healthy",
        gateway_result.get("message", ""),
        gateway_result
    )

    # 检查 Redis
    redis_result = check_redis(config)
    status.add_check(
        "redis",
        redis_result["status"] == "healthy",
        redis_result.get("message", ""),
        redis_result
    )

    # 检查 Database
    db_result = check_database(config)
    status.add_check(
        "database",
        db_result["status"] == "healthy",
        db_result.get("message", ""),
        db_result
    )

    # 检查错误率
    error_rate_result = check_error_rate(config)
    status.add_check(
        "error_rate",
        error_rate_result["status"] == "healthy",
        error_rate_result.get("message", ""),
        error_rate_result
    )

    # 添加时间戳
    result = status.to_dict()
    result["timestamp"] = datetime.utcnow().isoformat() + "Z"

    return result


def get_health_status() -> str:
    """获取健康状态字符串"""
    result = health_check()
    return result.get("overall", "unknown")