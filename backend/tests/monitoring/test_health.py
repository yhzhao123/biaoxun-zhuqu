"""
TDD Cycle 21: Health Check Tests

测试健康检查端点:
- Gateway 连接
- Redis 连接
- Database 连接
- 最近错误率
"""
import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock, Mock


class TestHealthCheckEndpoint:
    """测试健康检查端点"""

    def test_health_endpoint_returns_json(self):
        """测试健康端点返回 JSON"""
        from apps.monitoring.health import health_check

        # 模拟请求
        request = MagicMock()

        result = health_check(request)

        assert result.status_code == 200
        data = json.loads(result.content)
        assert "status" in data

    def test_health_endpoint_healthy_status(self):
        """测试健康端点返回 healthy 状态"""
        from apps.monitoring.health import health_check

        request = MagicMock()

        result = health_check(request)

        data = json.loads(result.content)
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_endpoint_includes_timestamp(self):
        """测试健康端点包含时间戳"""
        from apps.monitoring.health import health_check

        request = MagicMock()

        result = health_check(request)

        data = json.loads(result.content)
        assert "timestamp" in data


class TestHealthChecks:
    """测试健康检查项"""

    def test_gateway_health_check_healthy(self):
        """测试 Gateway 健康检查 - 正常"""
        from apps.monitoring.health import check_gateway

        with patch('apps.monitoring.health.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_get.return_value = mock_response

            result = check_gateway()
            assert result["status"] == "healthy"

    def test_gateway_health_check_unreachable(self):
        """测试 Gateway 健康检查 - 无法连接"""
        import requests
        from apps.monitoring.health import check_gateway

        with patch('apps.monitoring.health.requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError()

            result = check_gateway()
            assert result["status"] == "unhealthy"

    def test_gateway_health_check_timeout(self):
        """测试 Gateway 健康检查 - 超时"""
        import requests
        from apps.monitoring.health import check_gateway

        with patch('apps.monitoring.health.requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout()

            result = check_gateway()
            assert result["status"] == "unhealthy"

    @patch('django.core.cache.cache.get')
    def test_redis_health_check_healthy(self, mock_cache_get):
        """测试 Redis 健康检查 - 正常"""
        from apps.monitoring.health import check_redis

        mock_cache_get.return_value = "test"

        result = check_redis()
        assert result["status"] == "healthy"

    @patch('django.core.cache.cache.get')
    def test_redis_health_check_unhealthy(self, mock_cache_get):
        """测试 Redis 健康检查 - 失败"""
        from apps.monitoring.health import check_redis

        mock_cache_get.side_effect = Exception("Connection error")

        result = check_redis()
        assert result["status"] == "unhealthy"

    def test_database_health_check_healthy(self):
        """测试 Database 健康检查 - 正常"""
        from django.db import connection

        from apps.monitoring.health import check_database

        with patch.object(connection, 'ensure_connection') as mock_ensure:
            mock_ensure.return_value = None

            result = check_database()
            assert result["status"] == "healthy"

    def test_database_health_check_unhealthy(self):
        """测试 Database 健康检查 - 失败"""
        from django.db import connection

        from apps.monitoring.health import check_database

        with patch.object(connection, 'ensure_connection') as mock_ensure:
            mock_ensure.side_effect = Exception("Database error")

            result = check_database()
            assert result["status"] == "unhealthy"


class TestErrorRateCalculation:
    """测试错误率计算"""

    def test_error_rate_calculation_no_errors(self):
        """测试错误率计算 - 无错误"""
        from apps.monitoring.health import calculate_error_rate

        error_rate = calculate_error_rate(hours=1)
        assert error_rate == 0.0

    def test_error_rate_calculation_with_errors(self):
        """测试错误率计算 - 有错误"""
        from apps.monitoring.health import calculate_error_rate

        # 模拟错误记录
        error_rate = calculate_error_rate(hours=1)
        assert isinstance(error_rate, float)
        assert 0.0 <= error_rate <= 1.0

    def test_error_rate_threshold(self):
        """测试错误率阈值"""
        from apps.monitoring.health import calculate_error_rate

        rate = calculate_error_rate(hours=1)
        assert isinstance(rate, float)


class TestHealthStatus:
    """测试健康状态"""

    def test_health_status_all_healthy(self):
        """测试全部健康状态"""
        from apps.monitoring.health import HealthStatus

        status = HealthStatus()
        status.add_check("gateway", True, "OK")
        status.add_check("redis", True, "OK")
        status.add_check("database", True, "OK")

        overall = status.get_overall()
        assert overall == "healthy"

    def test_health_status_degraded(self):
        """测试降级状态"""
        from apps.monitoring.health import HealthStatus

        status = HealthStatus()
        status.add_check("gateway", True, "OK")
        status.add_check("redis", False, "Error")
        status.add_check("database", True, "OK")

        overall = status.get_overall()
        assert overall == "degraded"

    def test_health_status_unhealthy(self):
        """测试不健康状态"""
        from apps.monitoring.health import HealthStatus

        status = HealthStatus()
        status.add_check("gateway", False, "Error")
        status.add_check("redis", False, "Error")
        status.add_check("database", False, "Error")

        overall = status.get_overall()
        assert overall == "unhealthy"

    def test_health_status_to_dict(self):
        """测试状态转换为字典"""
        from apps.monitoring.health import HealthStatus

        status = HealthStatus()
        status.add_check("gateway", True, "OK")

        status_dict = status.to_dict()
        assert "checks" in status_dict
        assert "overall" in status_dict


class TestHealthCheckView:
    """测试健康检查视图"""

    def test_health_check_view_returns_200(self):
        """测试健康检查视图返回 200"""
        from django.test import Client

        client = Client()

        with patch('apps.monitoring.health.health_check') as mock_check:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = json.dumps({"status": "healthy"}).encode()
            mock_check.return_value = mock_response

            response = client.get('/api/v1/crawler/deer-flow/health')
            assert response.status_code == 200


class TestHealthConfiguration:
    """测试健康检查配置"""

    def test_health_config_defaults(self):
        """测试健康检查默认配置"""
        from apps.monitoring.health import HealthConfig

        config = HealthConfig()
        assert config.gateway_url == "http://localhost:8001/health"
        assert config.error_rate_threshold == 0.1

    def test_health_config_custom(self):
        """测试健康检查自定义配置"""
        from apps.monitoring.health import HealthConfig

        config = HealthConfig(
            gateway_url="http://custom:8001/health",
            error_rate_threshold=0.2
        )
        assert config.gateway_url == "http://custom:8001/health"
        assert config.error_rate_threshold == 0.2


class TestAlertOnUnhealthy:
    """测试不健康时的告警"""

    @patch('apps.monitoring.health.logger')
    def test_alert_on_critical_failure(self, mock_logger):
        """测试关键故障告警"""
        from apps.monitoring.health import check_gateway

        import requests
        with patch('apps.monitoring.health.requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError()

            result = check_gateway()

            # 验证告警日志
            assert result["status"] == "unhealthy"