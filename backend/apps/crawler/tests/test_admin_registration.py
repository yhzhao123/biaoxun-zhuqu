"""
Admin Registration Tests - 测试Admin注册
"""


class TestCrawlSourceAdminRegistration:
    """测试CrawlSource Admin注册"""

    def test_crawlsource_registered_in_admin(self):
        """CrawlSource should be registered in Django Admin"""
        from django.contrib import admin
        from apps.crawler.models import CrawlSource

        # 检查CrawlSource是否在admin site中注册
        assert CrawlSource in admin.site._registry, \
            "CrawlSource should be registered in Django Admin"

    def test_crawlsource_admin_has_correct_fields(self):
        """CrawlSource Admin should have correct configuration"""
        from django.contrib import admin
        from apps.crawler.models import CrawlSource

        # 获取已注册的Admin类
        crawlsource_admin = admin.site._registry.get(CrawlSource)

        assert crawlsource_admin is not None, "CrawlSource should be registered"

        # 验证list_display包含必要字段
        expected_fields = ['name', 'base_url', 'status', 'total_crawled', 'success_rate']
        for field in expected_fields:
            assert field in crawlsource_admin.list_display, \
                f"list_display should include '{field}'"