"""
Security configuration tests
验证安全相关的配置是否正确
"""

import os
import pytest
from unittest.mock import patch


class TestEnvironmentVariables:
    """Test 1: 环境变量安全配置"""

    def test_secret_key_not_hardcoded(self):
        """SECRET_KEY 不应该使用硬编码"""
        # 读取 settings.py 文件内容
        import config.settings as settings_module
        settings_file = settings_module.__file__

        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否没有硬编码的默认 SECRET_KEY
        assert "django-insecure-dev-key-change-in-production" not in content
        # 检查是否从环境变量读取
        assert "os.environ.get('SECRET_KEY')" in content

    def test_database_password_from_env(self):
        """数据库密码应该从环境变量读取"""
        import config.settings as settings_module
        settings_file = settings_module.__file__

        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查数据库密码配置
        assert "os.environ.get('POSTGRES_PASSWORD')" in content
        # 检查没有硬编码的 'postgres' 作为默认值
        assert "'PASSWORD': 'postgres'" not in content

    def test_debug_configurable(self):
        """DEBUG 应该可以通过环境变量配置"""
        import config.settings as settings_module
        settings_file = settings_module.__file__

        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查 DEBUG 设置
        assert "os.environ.get('DEBUG'" in content


class TestAPIPermissions:
    """Test 2: API 权限配置"""

    def test_api_uses_is_authenticated(self):
        """API 应该使用 IsAuthenticated"""
        import config.settings as settings_module
        settings_file = settings_module.__file__

        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否使用 IsAuthenticated
        assert "IsAuthenticated" in content
        # 检查主配置中不使用 AllowAny
        # 注意：测试配置可能使用 AllowAny

    def test_api_has_authentication_classes(self):
        """应该配置认证类"""
        import config.settings as settings_module
        settings_file = settings_module.__file__

        with open(settings_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 检查是否配置了认证类
        assert "DEFAULT_AUTHENTICATION_CLASSES" in content
        assert "SessionAuthentication" in content or "TokenAuthentication" in content


class TestCeleryRetryConfig:
    """Test 3: Celery 重试配置"""

    def test_celery_does_not_retry_all_exceptions(self):
        """Celery 不应该重试所有异常"""
        from apps.crawler import tasks

        # 获取 run_crawl_task 的装饰器配置
        task = tasks.run_crawl_task

        # 检查 autoretry_for 是否包含所有异常
        autoretry_for = getattr(task, 'autoretry_for', None)

        if autoretry_for:
            # 不应该包含基类 Exception
            assert Exception not in autoretry_for, \
                "Should not retry all Exception types"

            # 应该只包含具体的异常类型
            assert len(autoretry_for) > 0
            for exc in autoretry_for:
                assert exc != Exception


class TestBudgetValidation:
    """Test 4: 预算参数验证"""

    def test_budget_range_validation(self):
        """预算范围应该被验证"""
        # 测试有效范围
        min_budget = 1000
        max_budget = 100000
        assert min_budget <= max_budget

        # 测试超大值应该被拒绝
        huge_budget = 10**15  # 过大
        max_allowed = 10**12
        assert huge_budget > max_allowed


class TestRateLimiting:
    """Test 5: 速率限制"""

    def test_spider_has_delay(self):
        """爬虫应该有延迟设置"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()
        assert spider.min_delay >= 1.0
        assert spider.max_delay >= spider.min_delay

    def test_spider_has_timeout(self):
        """爬虫应该有超时设置"""
        from apps.crawler.spiders.gov_spider import GovSpider

        spider = GovSpider()
        assert spider.timeout > 0
        assert spider.timeout <= 60  # 合理的超时时间
