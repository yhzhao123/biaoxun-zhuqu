"""
Notification Models - Phase 8 Tasks 046-047
Models for notification service
"""

import uuid
from django.db import models
from django.conf import settings


class Notification(models.Model):
    """Notification for users about matched opportunities."""

    # Type choices
    TYPE_EMAIL = 'email'
    TYPE_IN_APP = 'in_app'
    TYPE_SMS = 'sms'
    TYPE_PUSH = 'push'
    TYPE_CHOICES = [
        (TYPE_EMAIL, '邮件'),
        (TYPE_IN_APP, '应用内'),
        (TYPE_SMS, '短信'),
        (TYPE_PUSH, '推送'),
    ]

    # Status choices
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_DELIVERED = 'delivered'
    STATUS_READ = 'read'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待发送'),
        (STATUS_SENT, '已发送'),
        (STATUS_DELIVERED, '已送达'),
        (STATUS_READ, '已读'),
        (STATUS_FAILED, '失败'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='用户'
    )
    subscription = models.ForeignKey(
        'subscriptions.Subscription',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='订阅'
    )
    opportunity = models.ForeignKey(
        'tenders.TenderNotice',
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name='招标机会'
    )
    match_result = models.ForeignKey(
        'subscriptions.MatchResult',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='匹配结果'
    )

    notification_type = models.CharField(
        '通知类型',
        max_length=20,
        choices=TYPE_CHOICES,
        default=TYPE_IN_APP
    )
    status = models.CharField(
        '状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING
    )

    subject = models.CharField('主题', max_length=500, blank=True)
    content = models.TextField('内容')
    metadata = models.JSONField('元数据', default=dict, blank=True)

    sent_at = models.DateTimeField('发送时间', null=True, blank=True)
    delivered_at = models.DateTimeField('送达时间', null=True, blank=True)
    read_at = models.DateTimeField('阅读时间', null=True, blank=True)

    retry_count = models.IntegerField('重试次数', default=0)
    error_message = models.TextField('错误信息', blank=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = '通知'
        verbose_name_plural = '通知'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.subject[:50]}"

    def mark_as_sent(self):
        """Mark notification as sent."""
        from django.utils import timezone
        self.status = self.STATUS_SENT
        self.sent_at = timezone.now()
        self.save(update_fields=['status', 'sent_at'])

    def mark_as_delivered(self):
        """Mark notification as delivered."""
        from django.utils import timezone
        self.status = self.STATUS_DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status', 'delivered_at'])

    def mark_as_read(self):
        """Mark notification as read."""
        from django.utils import timezone
        self.status = self.STATUS_READ
        self.read_at = timezone.now()
        self.save(update_fields=['status', 'read_at'])

    def mark_as_failed(self, error_message=''):
        """Mark notification as failed."""
        self.status = self.STATUS_FAILED
        self.error_message = error_message
        self.save(update_fields=['status', 'error_message'])

    def increment_retry(self):
        """Increment retry count."""
        self.retry_count += 1
        self.save(update_fields=['retry_count'])


class UserNotificationPreference(models.Model):
    """User preferences for notification settings."""

    # Digest mode choices
    DIGEST_REALTIME = 'realtime'
    DIGEST_HOURLY = 'hourly'
    DIGEST_DAILY = 'daily'
    DIGEST_CHOICES = [
        (DIGEST_REALTIME, '实时'),
        (DIGEST_HOURLY, '每小时'),
        (DIGEST_DAILY, '每日'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='notification_preferences',
        verbose_name='用户'
    )

    email_enabled = models.BooleanField('邮件通知启用', default=True)
    in_app_enabled = models.BooleanField('应用内通知启用', default=True)
    sms_enabled = models.BooleanField('短信通知启用', default=False)
    push_enabled = models.BooleanField('推送通知启用', default=False)

    digest_mode = models.CharField(
        ' digest 模式',
        max_length=20,
        choices=DIGEST_CHOICES,
        default=DIGEST_DAILY
    )
    digest_time = models.TimeField('digest 时间', default='09:00')

    quiet_hours_start = models.TimeField('免打扰开始时间', null=True, blank=True)
    quiet_hours_end = models.TimeField('免打扰结束时间', null=True, blank=True)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        db_table = 'user_notification_preferences'
        verbose_name = '用户通知偏好'
        verbose_name_plural = '用户通知偏好'

    def __str__(self):
        return f"{self.user.username} 的通知偏好"

    def is_quiet_hours(self, current_time=None):
        """Check if current time is in quiet hours."""
        from django.utils import timezone

        if self.quiet_hours_start is None or self.quiet_hours_end is None:
            return False

        if current_time is None:
            current_time = timezone.now().time()

        if self.quiet_hours_start < self.quiet_hours_end:
            return self.quiet_hours_start <= current_time <= self.quiet_hours_end
        else:
            # Handles overnight quiet hours (e.g., 22:00 - 08:00)
            return current_time >= self.quiet_hours_start or current_time <= self.quiet_hours_end
