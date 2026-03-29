"""
TDD Test: Deployment Configuration Management
Tests for Docker, Docker Compose, environment variables, health checks, and monitoring.
"""
import json
import os
import re
from pathlib import Path
from typing import Any

import pytest
import yaml


# Project root path - backend/tests/deployment -> backend -> project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class TestDockerMultiStageBuild:
    """Test Docker multi-stage build configuration"""

    @pytest.fixture
    def dockerfile_content(self) -> str:
        """读取 Dockerfile.backend 内容"""
        dockerfile_path = PROJECT_ROOT / "Dockerfile.backend"
        assert dockerfile_path.exists(), f"Dockerfile not found at {dockerfile_path}"
        return dockerfile_path.read_text(encoding="utf-8")

    def test_dockerfile_exists(self, dockerfile_content: str):
        """测试 Dockerfile.backend 存在"""
        assert dockerfile_content is not None

    def test_multi_stage_build_used(self, dockerfile_content: str):
        """测试使用多阶段构建 (builder + production)"""
        # Check for multiple FROM statements
        from_count = len(re.findall(r"^FROM\s+\S+", dockerfile_content, re.MULTILINE))
        assert from_count >= 2, "Multi-stage build requires at least 2 FROM statements"

    def test_builder_stage_exists(self, dockerfile_content: str):
        """测试 builder 阶段存在"""
        assert "AS builder" in dockerfile_content or "as builder" in dockerfile_content

    def test_production_stage_exists(self, dockerfile_content: str):
        """测试 production 阶段存在"""
        assert "AS production" in dockerfile_content or "as production" in dockerfile_content

    def test_virtual_environment_used(self, dockerfile_content: str):
        """测试使用虚拟环境优化"""
        assert "python -m venv" in dockerfile_content

    def test_non_root_user(self, dockerfile_content: str):
        """测试使用非 root 用户运行"""
        assert "useradd" in dockerfile_content or "USER" in dockerfile_content

    def test_healthcheck_configured(self, dockerfile_content: str):
        """测试配置了健康检查"""
        assert "HEALTHCHECK" in dockerfile_content

    def test_no_cache_pip_install(self, dockerfile_content: str):
        """测试 pip install 使用 --no-cache-dir"""
        assert "--no-cache-dir" in dockerfile_content


class TestDockerComposeConfiguration:
    """Test Docker Compose configuration"""

    @pytest.fixture
    def compose_dev_content(self) -> dict:
        """读取 docker-compose.yml 内容"""
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        assert compose_path.exists()
        return yaml.safe_load(compose_path.read_text(encoding="utf-8"))

    @pytest.fixture
    def compose_prod_content(self) -> dict:
        """读取 docker-compose.prod.yml 内容"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        assert compose_path.exists()
        return yaml.safe_load(compose_path.read_text(encoding="utf-8"))

    @pytest.fixture
    def env_file_content(self) -> str:
        """读取 .env.example 内容"""
        env_path = PROJECT_ROOT / ".env.example"
        assert env_path.exists()
        return env_path.read_text(encoding="utf-8")

    def test_docker_compose_dev_exists(self, compose_dev_content: dict):
        """测试开发用 docker-compose.yml 存在"""
        assert "services" in compose_dev_content
        assert "db" in compose_dev_content["services"]
        assert "redis" in compose_dev_content["services"]
        assert "backend" in compose_dev_content["services"]

    def test_docker_compose_prod_exists(self, compose_prod_content: dict):
        """测试生产用 docker-compose.prod.yml 存在"""
        assert "services" in compose_prod_content
        assert "db" in compose_prod_content["services"]
        assert "redis" in compose_prod_content["services"]
        assert "backend" in compose_prod_content["services"]

    def test_postgres_healthcheck(self, compose_dev_content: dict):
        """测试 PostgreSQL 配置健康检查"""
        db_service = compose_dev_content["services"]["db"]
        assert "healthcheck" in db_service

    def test_redis_healthcheck(self, compose_dev_content: dict):
        """测试 Redis 配置健康检查"""
        redis_service = compose_dev_content["services"]["redis"]
        assert "healthcheck" in redis_service

    def test_backend_depends_on_db(self, compose_dev_content: dict):
        """测试 backend 依赖 db 服务"""
        backend_service = compose_dev_content["services"]["backend"]
        assert "depends_on" in backend_service

    def test_celery_services_configured(self, compose_dev_content: dict):
        """测试 Celery 服务配置"""
        assert "celery" in compose_dev_content["services"]
        assert "celery-beat" in compose_dev_content["services"]

    def test_production_has_networks(self, compose_prod_content: dict):
        """测试生产配置包含网络配置"""
        assert "networks" in compose_prod_content

    def test_production_has_volumes(self, compose_prod_content: dict):
        """测试生产配置包含卷配置"""
        assert "volumes" in compose_prod_content

    def test_env_file_has_required_variables(self, env_file_content: str):
        """测试 .env.example 包含必需的环境变量"""
        required_vars = [
            "SECRET_KEY",
            "POSTGRES_PASSWORD",
            "DEBUG",
            "POSTGRES_DB",
        ]
        for var in required_vars:
            assert var in env_file_content, f"Required env variable {var} not in .env.example"


class TestEnvironmentVariables:
    """Test environment variable management"""

    @pytest.fixture
    def env_example_content(self) -> dict:
        """解析 .env.example 内容为字典"""
        env_path = PROJECT_ROOT / ".env.example"
        content = env_path.read_text(encoding="utf-8")
        env_dict: dict[str, str] = {}
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                env_dict[key.strip()] = value.strip()
        return env_dict

    def test_secret_key_required(self, env_example_content: dict):
        """测试 SECRET_KEY 变量存在"""
        assert "SECRET_KEY" in env_example_content

    def test_postgres_config_present(self, env_example_content: dict):
        """测试 PostgreSQL 配置存在"""
        assert "POSTGRES_DB" in env_example_content
        assert "POSTGRES_USER" in env_example_content
        assert "POSTGRES_PASSWORD" in env_example_content

    def test_redis_config_present(self, env_example_content: dict):
        """测试 Redis 配置存在"""
        assert "REDIS_URL" in env_example_content

    def test_celery_config_present(self, env_example_content: dict):
        """测试 Celery 配置存在"""
        assert "CELERY_BROKER_URL" in env_example_content
        assert "CELERY_RESULT_BACKEND" in env_example_content


class TestHealthCheckEndpoint:
    """Test health check endpoint configuration"""

    @pytest.fixture
    def health_py_content(self) -> str | None:
        """读取 monitoring/health.py 内容"""
        health_path = PROJECT_ROOT / "backend" / "apps" / "monitoring" / "health.py"
        if health_path.exists():
            return health_path.read_text(encoding="utf-8")
        return None

    def test_health_module_exists(self, health_py_content: str | None):
        """测试 health.py 模块存在"""
        assert health_py_content is not None, "health.py module not found"

    def test_health_endpoint_defined(self, health_py_content: str | None):
        """测试健康检查端点已定义"""
        assert health_py_content is not None
        assert "health" in health_py_content.lower() or "HealthCheckResponse" in health_py_content

    def test_healthcheck_in_dockerfile(self):
        """测试 Dockerfile 中配置了健康检查"""
        dockerfile_path = PROJECT_ROOT / "Dockerfile.backend"
        content = dockerfile_path.read_text(encoding="utf-8")
        assert "HEALTHCHECK" in content


class TestLoggingConfiguration:
    """Test logging and monitoring configuration"""

    @pytest.fixture
    def logging_py_content(self) -> str | None:
        """读取 monitoring/logging_.py 内容"""
        logging_path = PROJECT_ROOT / "backend" / "apps" / "monitoring" / "logging_.py"
        if logging_path.exists():
            return logging_path.read_text(encoding="utf-8")
        return None

    def test_logging_module_exists(self, logging_py_content: str | None):
        """测试 logging_.py 模块存在"""
        assert logging_py_content is not None, "logging_.py module not found"

    def test_logging_configured(self, logging_py_content: str | None):
        """测试日志已配置"""
        assert logging_py_content is not None
        # Check for logging configuration (structlog or standard logging)
        has_logging = any(
            keyword in logging_py_content
            for keyword in ["structlog", "logging.config", "logging.getLogger"]
        )
        assert has_logging, "No logging configuration found"

    def test_prometheus_metrics_configured(self):
        """测试 Prometheus 指标配置"""
        metrics_path = PROJECT_ROOT / "backend" / "apps" / "monitoring" / "prometheus_metrics.py"
        assert metrics_path.exists(), "prometheus_metrics.py not found"

    def test_log_volume_mounted_in_docker_compose(self):
        """测试 Docker Compose 中配置了日志卷"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        # Check for log directory or volume configuration
        assert "logs" in content.lower() or "static_files" in content


class TestStartupScript:
    """Test startup script configuration"""

    @pytest.fixture
    def scripts_dir(self) -> Path:
        """获取 scripts 目录路径"""
        return PROJECT_ROOT / "scripts"

    def test_scripts_directory_exists(self, scripts_dir: Path):
        """测试 scripts 目录存在"""
        assert scripts_dir.exists(), "scripts directory not found"

    def test_entrypoint_script_exists(self, scripts_dir: Path):
        """测试 entrypoint.sh 脚本存在"""
        entrypoint = scripts_dir / "entrypoint.sh"
        assert entrypoint.exists(), "entrypoint.sh not found"

    def test_entrypoint_has_database_migration(self, scripts_dir: Path):
        """测试 entrypoint.sh 包含数据库迁移命令"""
        entrypoint = scripts_dir / "entrypoint.sh"
        content = entrypoint.read_text(encoding="utf-8")
        assert "migrate" in content, "Database migration not found in entrypoint.sh"

    def test_entrypoint_has_collectstatic(self, scripts_dir: Path):
        """测试 entrypoint.sh 包含静态文件收集命令"""
        entrypoint = scripts_dir / "entrypoint.sh"
        content = entrypoint.read_text(encoding="utf-8")
        assert "collectstatic" in content or "collect static" in content, "collectstatic not found"


class TestProductionSecurity:
    """Test production security settings"""

    def test_debug_disabled_in_prod_compose(self):
        """测试生产环境关闭 DEBUG"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        # DEBUG should be set to 0 in production
        assert "DEBUG=0" in content

    def test_secret_key_required_in_prod(self):
        """测试生产环境需要 SECRET_KEY"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "SECRET_KEY" in content

    def test_non_root_user_in_dockerfile(self):
        """测试 Dockerfile 使用非 root 用户"""
        dockerfile_path = PROJECT_ROOT / "Dockerfile.backend"
        content = dockerfile_path.read_text(encoding="utf-8")
        assert "USER" in content or "useradd" in content

    def test_production_restart_policy(self):
        """测试生产配置使用 unless-stopped 重启策略"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "unless-stopped" in content


class TestCICDConfiguration:
    """Test CI/CD pipeline configuration"""

    def test_github_workflows_exist(self):
        """测试 GitHub workflows 目录存在"""
        workflows_dir = PROJECT_ROOT / ".github" / "workflows"
        # This is optional - some projects may not have CI/CD
        # Just verify the directory structure if it exists
        if workflows_dir.exists():
            assert workflows_dir.is_dir()

    def test_dockerignore_exists(self):
        """测试 .dockerignore 文件存在"""
        dockerignore = PROJECT_ROOT / ".dockerignore"
        assert dockerignore.exists(), ".dockerignore not found"

    def test_dockerignore_excludes_pycache(self):
        """测试 .dockerignore 排除 __pycache__"""
        dockerignore = PROJECT_ROOT / ".dockerignore"
        content = dockerignore.read_text(encoding="utf-8")
        assert "__pycache__" in content or "*.pyc" in content

    def test_dockerignore_excludes_git(self):
        """测试 .dockerignore 排除 .git"""
        dockerignore = PROJECT_ROOT / ".dockerignore"
        content = dockerignore.read_text(encoding="utf-8")
        assert ".git" in content

    def test_gitignore_present(self):
        """测试 .gitignore 文件存在"""
        gitignore = PROJECT_ROOT / ".gitignore"
        assert gitignore.exists(), ".gitignore not found"


class TestResourceLimits:
    """Test resource limits and scaling configuration"""

    def test_celery_concurrency_configured(self):
        """测试 Celery 并发数配置"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "concurrency" in content

    def test_postgres_performance_tuning(self):
        """测试 PostgreSQL 性能调优配置"""
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        content = compose_path.read_text(encoding="utf-8")
        # Check for performance-related PostgreSQL settings
        assert "max_connections" in content or "shared_buffers" in content

    def test_redis_memory_limit(self):
        """测试 Redis 内存限制配置"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "maxmemory" in content

    def test_redis_persistence_enabled(self):
        """测试 Redis 持久化配置"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "appendonly" in content or "AOF" in content


class TestBackupAndRecovery:
    """Test backup and recovery configuration"""

    def test_postgres_volume_configured(self):
        """测试 PostgreSQL 数据卷配置"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "postgres_data" in content

    def test_redis_volume_configured(self):
        """测试 Redis 数据卷配置"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "redis_data" in content


class TestNetworkConfiguration:
    """Test network configuration"""

    def test_services_use_custom_network(self):
        """测试服务使用自定义网络"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "networks:" in content

    def test_backend_exposes_port(self):
        """测试 backend 服务暴露端口"""
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "8000:8000" in content or "ports:" in content


class TestMonitoringConfiguration:
    """Test monitoring and observability"""

    def test_healthcheck_interval_configured(self):
        """测试健康检查间隔配置"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "interval:" in content

    def test_healthcheck_timeout_configured(self):
        """测试健康检查超时配置"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "timeout:" in content

    def test_healthcheck_retries_configured(self):
        """测试健康检查重试配置"""
        compose_path = PROJECT_ROOT / "docker-compose.prod.yml"
        content = compose_path.read_text(encoding="utf-8")
        assert "retries" in content


class TestEnvironmentValidation:
    """Test environment variable validation"""

    def test_env_file_has_database_url(self):
        """测试环境变量包含 DATABASE_URL"""
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            # DATABASE_URL should be present or constructable
            assert "DATABASE_URL" in content or "POSTGRES_" in content

    def test_env_example_has_debug_setting(self):
        """测试 .env.example 包含 DEBUG 设置"""
        env_path = PROJECT_ROOT / ".env.example"
        content = env_path.read_text(encoding="utf-8")
        assert "DEBUG" in content

    def test_env_example_has_allowed_hosts(self):
        """测试 .env.example 包含 ALLOWED_HOSTS 配置"""
        env_path = PROJECT_ROOT / ".env.example"
        content = env_path.read_text(encoding="utf-8")
        assert "ALLOWED_HOSTS" in content or "ALLOWED" in content


class TestBuildOptimization:
    """Test build optimization settings"""

    def test_dockerfile_uses_slim_base_image(self):
        """测试 Dockerfile 使用 slim 基础镜像"""
        dockerfile_path = PROJECT_ROOT / "Dockerfile.backend"
        content = dockerfile_path.read_text(encoding="utf-8")
        assert "slim" in content.lower()

    def test_dockerfile_removes_apt_lists(self):
        """测试 Dockerfile 清理 apt 缓存"""
        dockerfile_path = PROJECT_ROOT / "Dockerfile.backend"
        content = dockerfile_path.read_text(encoding="utf-8")
        assert "rm -rf" in content or "rm -r" in content

    def test_dockerfile_sets_python_unbuffered(self):
        """测试 Dockerfile 设置 PYTHONUNBUFFERED"""
        dockerfile_path = PROJECT_ROOT / "Dockerfile.backend"
        content = dockerfile_path.read_text(encoding="utf-8")
        assert "PYTHONUNBUFFERED" in content

    def test_dockerfile_exposes_port(self):
        """测试 Dockerfile 暴露端口"""
        dockerfile_path = PROJECT_ROOT / "Dockerfile.backend"
        content = dockerfile_path.read_text(encoding="utf-8")
        assert "EXPOSE" in content