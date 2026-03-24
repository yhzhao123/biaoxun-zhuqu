"""
Subscription Models - Phase 8 Tasks 042-043
Models for subscription management and keyword matching
"""

import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Subscription(models.Model):
    """User subscription for bidding opportunity notifications."""

    # Frequency choices
    FREQUENCY_REALTIME = 'realtime'
    FREQUENCY_HOURLY = 'hourly'
    FREQUENCY_DAILY = 'daily'
    FREQUENCY_CHOICES = [
        (FREQUENCY_REALTIME, '实时'),
        (FREQUENCY_HOURLY, '每小时'),
        (FREQUENCY_DAILY, '每天'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='用户'
    )
    name = models.CharField('订阅名称', max_length=100)
    description = models.TextField('描述', blank=True)

    # Notification channels (stored as JSON)
    notify_email = models.BooleanField('邮件通知', default=True)
    notify_in_app = models.BooleanField('应用内通知', default=True)
    notify_sms = models.BooleanField('短信通知', default=False)

    frequency = models.CharField(
        '通知频率',
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default=FREQUENCY_DAILY
    )

    is_active = models.BooleanField('是否激活', default=True)
    max_keywords = models.IntegerField(
        '最大关键词数',
        default=50,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    deleted_at = models.DateTimeField('删除时间', null=True, blank=True)

    class Meta:
        db_table = 'subscriptions'
        verbose_name = '订阅'
        verbose_name_plural = '订阅'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    def is_deleted(self):
        return self.deleted_at is not None

    def get_notification_channels(self):
        """Get enabled notification channels as list."""
        channels = []
        if self.notify_email:
            channels.append('email')
        if self.notify_in_app:
            channels.append('in_app')
        if self.notify_sms:
            channels.append('sms')
        return channels


class Keyword(models.Model):
    """Keyword for subscription matching."""

    # Match type choices
    MATCH_EXACT = 'exact'
    MATCH_CONTAINS = 'contains'
    MATCH_STARTS_WITH = 'starts_with'
    MATCH_ENDS_WITH = 'ends_with'
    MATCH_REGEX = 'regex'
    MATCH_CHOICES = [
        (MATCH_EXACT, '精确匹配'),
        (MATCH_CONTAINS, '包含匹配'),
        (MATCH_STARTS_WITH, '开头匹配'),
        (MATCH_ENDS_WITH, '结尾匹配'),
        (MATCH_REGEX, '正则匹配'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    value = models.CharField('关键词', max_length=200, db_index=True)
    match_type = models.CharField(
        '匹配类型',
        max_length=20,
        choices=MATCH_CHOICES,
        default=MATCH_CONTAINS
    )
    case_sensitive = models.BooleanField('区分大小写', default=False)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'keywords'
        verbose_name = '关键词'
        verbose_name_plural = '关键词'
        indexes = [
            models.Index(fields=['value']),
        ]

    def __str__(self):
        return f"{self.value} ({self.get_match_type_display()})"


class SubscriptionKeyword(models.Model):
    """Association between subscription and keyword with weight and required flag."""

    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='subscription_keywords',
        verbose_name='订阅'
    )
    keyword = models.ForeignKey(
        Keyword,
        on_delete=models.CASCADE,
        related_name='keyword_subscriptions',
        verbose_name='关键词'
    )
    is_required = models.BooleanField('是否必需', default=False)
    weight = models.FloatField(
        '权重',
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)]
    )

    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'subscription_keywords'
        verbose_name = '订阅关键词关联'
        verbose_name_plural = '订阅关键词关联'
        unique_together = ['subscription', 'keyword']
        indexes = [
            models.Index(fields=['subscription']),
            models.Index(fields=['keyword']),
        ]

    def __str__(self):
        return f"{self.subscription.name} - {self.keyword.value}"


class MatchResult(models.Model):
    """Result of matching an opportunity against subscriptions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='match_results',
        verbose_name='订阅'
    )
    opportunity = models.ForeignKey(
        'tenders.TenderNotice',
        on_delete=models.CASCADE,
        related_name='subscription_matches',
        verbose_name='招标机会'
    )
    score = models.FloatField(
        '匹配分数',
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    matched_keywords = models.JSONField('匹配的关键词', default=list)
    match_details = models.JSONField('匹配详情', default=dict)
    is_notified = models.BooleanField('已通知', default=False)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        db_table = 'match_results'
        verbose_name = '匹配结果'
        verbose_name_plural = '匹配结果'
        unique_together = ['subscription', 'opportunity']
        indexes = [
            models.Index(fields=['subscription', 'score']),
            models.Index(fields=['opportunity']),
            models.Index(fields=['is_notified']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.subscription.name} - {self.opportunity.title[:50]} ({self.score:.2f})"
