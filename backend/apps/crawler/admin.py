"""
Crawler admin configuration
"""

from django.contrib import admin
from apps.crawler.models import CrawlTask, CrawlSource


@admin.register(CrawlTask)
class CrawlTaskAdmin(admin.ModelAdmin):
    """爬虫任务Admin"""

    list_display = ['id', 'name', 'source_site', 'status', 'items_crawled', 'started_at', 'completed_at']
    list_filter = ['status', 'source_site', 'created_at']
    search_fields = ['name', 'source_url', 'error_message']
    readonly_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']
    ordering = ['-created_at']

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'source_url', 'source_site', 'source')
        }),
        ('状态', {
            'fields': ('status', 'items_crawled', 'error_message')
        }),
        ('时间', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )


@admin.register(CrawlSource)
class CrawlSourceAdmin(admin.ModelAdmin):
    """爬虫源配置Admin"""

    list_display = ['id', 'name', 'base_url', 'status', 'total_crawled', 'success_rate', 'last_crawl_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'base_url', 'list_url_pattern']
    readonly_fields = ['created_at', 'updated_at', 'last_crawl_at']
    ordering = ['-created_at']

    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'base_url', 'list_url_pattern')
        }),
        ('CSS选择器', {
            'fields': ('selector_title', 'selector_content', 'selector_publish_date',
                      'selector_tenderer', 'selector_budget')
        }),
        ('请求配置', {
            'fields': ('request_headers', 'request_cookies', 'delay_seconds')
        }),
        ('状态', {
            'fields': ('status', 'last_crawl_at', 'total_crawled', 'success_rate')
        }),
        ('时间', {
            'fields': ('created_at', 'updated_at')
        }),
    )