"""
Crawler models
"""

from django.db import models
from django.conf import settings


# Task status choices
STATUS_CHOICES = [
    ('pending', '待执行'),
    ('running', '执行中'),
    ('completed', '已完成'),
    ('failed', '失败'),
]


class CrawlTask(models.Model):
    """
    爬虫任务模型
    """
    name = models.CharField(max_length=200, verbose_name='任务名称')
    source_url = models.URLField(max_length=500, verbose_name='目标URL')
    source_site = models.CharField(max_length=100, verbose_name='来源网站')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='任务状态'
    )
    items_crawled = models.IntegerField(default=0, verbose_name='抓取条目数')
    error_message = models.TextField(blank=True, null=True, verbose_name='错误信息')
    started_at = models.DateTimeField(blank=True, null=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(blank=True, null=True, verbose_name='完成时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'crawler_crawltask'
        verbose_name = '爬虫任务'
        verbose_name_plural = '爬虫任务'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.status})"