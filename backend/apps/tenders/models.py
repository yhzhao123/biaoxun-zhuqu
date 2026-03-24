"""
招标公告模型 - Phase 2 Task 007
"""
from django.db import models
from django.utils import timezone
try:
    from django.contrib.postgres.indexes import GinIndex
    from django.contrib.postgres.search import SearchVectorField
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    GinIndex = None
    SearchVectorField = None
from apps.users.mixins import TimestampMixin


class TenderNotice(TimestampMixin):
    """招标公告模型"""

    # 公告类型
    TYPE_BIDDING = 'bidding'
    TYPE_WIN = 'win'

    TYPE_CHOICES = [
        (TYPE_BIDDING, '招标公告'),
        (TYPE_WIN, '中标公告'),
    ]

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
    winner = models.CharField(max_length=200, blank=True, verbose_name='中标人')
    project_name = models.CharField(max_length=300, blank=True, verbose_name='项目名称')

    # 公告类型
    notice_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_BIDDING,
        db_index=True,
        verbose_name='公告类型'
    )

    # 预算相关
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='预算金额'
    )
    budget_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        db_index=True,
        verbose_name='预算金额(标准化)'
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default=CURRENCY_CNY,
        verbose_name='货币'
    )

    # 日期相关
    publish_date = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name='发布日期')
    deadline_date = models.DateTimeField(null=True, blank=True, verbose_name='截止日期')

    # 分类相关
    region = models.CharField(max_length=100, blank=True, verbose_name='地区')
    region_code = models.CharField(max_length=10, blank=True, db_index=True, verbose_name='地区编码')
    region_name = models.CharField(max_length=100, blank=True, verbose_name='地区名称')
    industry = models.CharField(max_length=100, blank=True, verbose_name='行业')
    industry_code = models.CharField(max_length=10, blank=True, db_index=True, verbose_name='行业编码')
    industry_name = models.CharField(max_length=100, blank=True, verbose_name='行业名称')

    # 全文搜索向量
    if POSTGRES_AVAILABLE:
        search_vector = SearchVectorField(null=True, blank=True, verbose_name='搜索向量')
    else:
        search_vector = models.TextField(null=True, blank=True, verbose_name='搜索向量(SQLite)')

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
            models.Index(fields=['notice_type', 'publish_date']),
            models.Index(fields=['region_code', 'industry_code']),
        ]

    def __str__(self):
        return f"{self.notice_id} - {self.title[:50]}"

    def get_notice_type_display(self):
        """Get display name for notice type."""
        for code, name in self.TYPE_CHOICES:
            if code == self.notice_type:
                return name
        return self.notice_type