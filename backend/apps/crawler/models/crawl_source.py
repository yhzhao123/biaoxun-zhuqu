"""
CrawlSource model - 爬虫源配置
"""
from django.db import models


class CrawlSource(models.Model):
    """
    爬虫源配置模型
    用于管理可爬取的招标网站
    """

    # 状态选项
    STATUS_ACTIVE = 'active'
    STATUS_INACTIVE = 'inactive'
    STATUS_MAINTENANCE = 'maintenance'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, '启用'),
        (STATUS_INACTIVE, '禁用'),
        (STATUS_MAINTENANCE, '维护中'),
    ]

    name = models.CharField(max_length=100, verbose_name='网站名称')
    base_url = models.URLField(max_length=500, verbose_name='基础URL')
    list_url_pattern = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='列表页URL模式',
        help_text='如: /ggzy/jyxx/001001/001001001/?page={page}'
    )

    # CSS选择器配置
    selector_title = models.CharField(
        max_length=200,
        default='h1, .title, .article-title',
        verbose_name='标题选择器'
    )
    selector_content = models.CharField(
        max_length=200,
        default='.content, .article-content, .detail',
        verbose_name='内容选择器'
    )
    selector_publish_date = models.CharField(
        max_length=200,
        default='.publish-date, .time, .date',
        verbose_name='发布日期选择器'
    )
    selector_tenderer = models.CharField(
        max_length=200,
        default='.tenderer, .buyer, .purchaser',
        verbose_name='招标人选择器'
    )
    selector_budget = models.CharField(
        max_length=200,
        default='.budget, .amount, .price',
        verbose_name='预算金额选择器'
    )

    # 请求配置
    request_headers = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='请求头配置'
    )
    request_cookies = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Cookie配置'
    )
    delay_seconds = models.IntegerField(
        default=1,
        verbose_name='请求间隔(秒)',
        help_text='每次请求之间的间隔时间'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
        verbose_name='状态'
    )

    # 统计信息
    last_crawl_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='最后爬取时间'
    )
    total_crawled = models.IntegerField(
        default=0,
        verbose_name='总爬取数'
    )
    success_rate = models.FloatField(
        default=100.0,
        verbose_name='成功率(%)'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'crawler_sources'
        verbose_name = '爬虫源配置'
        verbose_name_plural = '爬虫源配置'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
