"""
Crawler admin configuration
"""

from django.contrib import admin
from apps.crawler.models import CrawlTask


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
            'fields': ('name', 'source_url', 'source_site')
        }),
        ('状态', {
            'fields': ('status', 'items_crawled', 'error_message')
        }),
        ('时间', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )