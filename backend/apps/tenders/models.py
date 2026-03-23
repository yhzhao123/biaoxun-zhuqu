"""
招标公告模型 - Phase 2 Task 007
"""
from django.db import models
from django.utils import timezone
from apps.users.mixins import TimestampMixin


class TenderNotice(TimestampMixin):
    """招标公告模型"""

    # 状态选项
    STATUS_PENDING = 'pending'
    STATUS_ACTIVE = 'active'
    STATUS_CLOSED = 'closed'
    STATUS_EXPIRED = 'expired'

    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_ACTIVE, '进行中'),
        (STATUS_CLOSED, '已关闭'),
        (STATUS_EXPIRED, '已过期'),
    ]

    # 货币选项
    CURRENCY_CNY = 'CNY'
    CURRENCY_USD = 'USD'
    CURRENCY_EUR = 'EUR'

    CURRENCY_CHOICES = [
        (CURRENCY_CNY, '人民币'),
        (CURRENCY_USD, '美元'),
        (CURRENCY_EUR, '欧元'),
    ]

    # 核心字段
    notice_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name='公告编号'
    )
    title = models.CharField(max_length=500, verbose_name='公告标题')
    description = models.TextField(blank=True, verbose_name='公告描述')
    tenderer = models.CharField(max_length=200, verbose_name='招标人')

    # 预算相关
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='预算金额'
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=CURRENCY_CNY,
        verbose_name='货币'
    )

    # 日期相关
    publish_date = models.DateTimeField(null=True, blank=True, verbose_name='发布日期')
    deadline_date = models.DateTimeField(null=True, blank=True, verbose_name='截止日期')

    # 分类相关
    region = models.CharField(max_length=100, blank=True, verbose_name='地区')
    industry = models.CharField(max_length=100, blank=True, verbose_name='行业')

    # 来源相关
    source_url = models.URLField(max_length=500, blank=True, verbose_name='来源URL')
    source_site = models.CharField(max_length=100, blank=True, verbose_name='来源网站')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
        verbose_name='状态'
    )

    # AI分析相关
    ai_summary = models.TextField(blank=True, verbose_name='AI摘要')
    ai_keywords = models.CharField(max_length=500, blank=True, verbose_name='AI关键词')
    ai_category = models.CharField(max_length=100, blank=True, verbose_name='AI分类')

    # 评分相关
    relevance_score = models.FloatField(
        null=True,
        blank=True,
        verbose_name='相关度评分'
    )

    # 爬虫批次
    crawl_batch_id = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        verbose_name='爬虫批次ID'
    )

    class Meta:
        db_table = 'tender_notices'
        verbose_name = '招标公告'
        verbose_name_plural = '招标公告'
        ordering = ['-publish_date', '-created_at']
        indexes = [
            models.Index(fields=['title', 'publish_date']),
            models.Index(fields=['tenderer', 'status']),
            models.Index(fields=['region', 'industry']),
            models.Index(fields=['crawl_batch_id', 'created_at']),
        ]

    def __str__(self):
        return f"{self.notice_id} - {self.title[:50]}"