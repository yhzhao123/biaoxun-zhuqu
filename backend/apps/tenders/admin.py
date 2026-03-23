"""
招标公告管理后台 - Phase 2 Task 007
"""
from django.contrib import admin
from .models import TenderNotice


@admin.register(TenderNotice)
class TenderNoticeAdmin(admin.ModelAdmin):
    """招标公告管理后台配置"""

    list_display = [
        'notice_id',
        'title',
        'tenderer',
        'budget',
        'currency',
        'region',
        'industry',
        'status',
        'publish_date',
        'deadline_date',
        'created_at',
    ]
    list_filter = [
        'status',
        'currency',
        'region',
        'industry',
        'source_site',
    ]
    search_fields = [
        'notice_id',
        'title',
        'tenderer',
        'description',
    ]
    date_hierarchy = 'publish_date'
    ordering = ['-publish_date', '-created_at']

    fieldsets = (
        ('基本信息', {
            'fields': (
                'notice_id',
                'title',
                'description',
                'tenderer',
            )
        }),
        ('预算信息', {
            'fields': (
                'budget',
                'currency',
            )
        }),
        ('日期信息', {
            'fields': (
                'publish_date',
                'deadline_date',
            )
        }),
        ('分类信息', {
            'fields': (
                'region',
                'industry',
            )
        }),
        ('来源信息', {
            'fields': (
                'source_url',
                'source_site',
                'status',
                'crawl_batch_id',
            )
        }),
        ('AI分析', {
            'fields': (
                'ai_summary',
                'ai_keywords',
                'ai_category',
                'relevance_score',
            ),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = [
        'notice_id',
        'crawl_batch_id',
        'created_at',
        'updated_at',
    ]