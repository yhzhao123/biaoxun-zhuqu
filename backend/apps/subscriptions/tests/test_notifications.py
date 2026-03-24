"""
Notification Tests - Phase 8 Tasks 046-047
Tests for notification service
"""

import pytest
from datetime import datetime, time
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.subscriptions.models import (
    Subscription, Keyword, SubscriptionKeyword, MatchResult
)
from apps.subscriptions.notification_models import (
    Notification, UserNotificationPreference
)
from apps.subscriptions.notification_service import NotificationService
from apps.tenders.models import TenderNotice


User = get_user_model()


class TestNotificationModel(TestCase):
    """Test Notification model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        self.opportunity = TenderNotice.objects.create(
            title='Test Opportunity',
            notice_id='TEST-001',
            notice_type=TenderNotice.TYPE_BIDDING,
            status=TenderNotice.STATUS_PENDING
        )

    def test_create_notification(self):
        """Should create notification."""
        notification = Notification.objects.create(
            user=self.user,
            subscription=self.subscription,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_IN_APP,
            subject='Test Notification',
            content='This is a test notification'
        )
        assert notification.id is not None
        assert notification.status == Notification.STATUS_PENDING

    def test_mark_as_sent(self):
        """Should mark notification as sent."""
        notification = Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_EMAIL,
            subject='Test',
            content='Test content'
        )
        notification.mark_as_sent()
        assert notification.status == Notification.STATUS_SENT
        assert notification.sent_at is not None

    def test_mark_as_read(self):
        """Should mark notification as read."""
        notification = Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_IN_APP,
            subject='Test',
            content='Test content'
        )
        notification.mark_as_delivered()
        notification.mark_as_read()
        assert notification.status == Notification.STATUS_READ
        assert notification.read_at is not None

    def test_mark_as_failed(self):
        """Should mark notification as failed."""
        notification = Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_EMAIL,
            subject='Test',
            content='Test content'
        )
        notification.mark_as_failed('SMTP error')
        assert notification.status == Notification.STATUS_FAILED
        assert notification.error_message == 'SMTP error'

    def test_increment_retry(self):
        """Should increment retry count."""
        notification = Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_EMAIL,
            subject='Test',
            content='Test content'
        )
        notification.increment_retry()
        assert notification.retry_count == 1


class TestUserNotificationPreference(TestCase):
    """Test UserNotificationPreference model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_preference(self):
        """Should create default preferences."""
        pref = UserNotificationPreference.objects.create(user=self.user)
        assert pref.email_enabled is True
        assert pref.in_app_enabled is True
        assert pref.sms_enabled is False
        assert pref.digest_mode == UserNotificationPreference.DIGEST_DAILY

    def test_is_quiet_hours(self):
        """Should check quiet hours."""
        pref = UserNotificationPreference.objects.create(
            user=self.user,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0)
        )

        # Test during quiet hours (23:00)
        current_time = time(23, 0)
        assert pref.is_quiet_hours(current_time) is True

        # Test outside quiet hours (12:00)
        current_time = time(12, 0)
        assert pref.is_quiet_hours(current_time) is False

    def test_is_not_quiet_hours_without_setting(self):
        """Should return False when quiet hours not set."""
        pref = UserNotificationPreference.objects.create(user=self.user)
        assert pref.is_quiet_hours() is False


class TestNotificationService(TestCase):
    """Test NotificationService."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = NotificationService()
        self.subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY,
            notify_email=True,
            notify_in_app=True
        )
        self.opportunity = TenderNotice.objects.create(
            title='Test Construction Project',
            notice_id='TEST-001',
            notice_type=TenderNotice.TYPE_BIDDING,
            status=TenderNotice.STATUS_PENDING
        )
        # Create user preferences with realtime digest mode for immediate notifications
        UserNotificationPreference.objects.create(
            user=self.user,
            digest_mode=UserNotificationPreference.DIGEST_REALTIME,
            email_enabled=True,
            in_app_enabled=True
        )

    def test_create_notification(self):
        """Should create notification."""
        notification = self.service.create_notification(
            user_id=self.user.id,
            opportunity_id=str(self.opportunity.id),
            subscription_id=str(self.subscription.id),
            match_result={'score': 85.0, 'matched_keywords': []},
            channels=['in_app']
        )
        assert notification is not None
        assert notification.user_id == self.user.id

    def test_create_notification_no_channels(self):
        """Should return None when no channels enabled."""
        # Disable all channels in subscription
        self.subscription.notify_email = False
        self.subscription.notify_in_app = False
        self.subscription.save()

        notification = self.service.create_notification(
            user_id=self.user.id,
            opportunity_id=str(self.opportunity.id),
            channels=[]
        )
        assert notification is None

    def test_get_user_notifications(self):
        """Should get user notifications."""
        # Create notifications
        for i in range(3):
            Notification.objects.create(
                user=self.user,
                opportunity=self.opportunity,
                notification_type=Notification.TYPE_IN_APP,
                subject=f'Notification {i}',
                content=f'Content {i}'
            )

        result = self.service.get_user_notifications(self.user.id)
        assert result['total'] == 3
        assert len(result['notifications']) == 3

    def test_get_user_notifications_with_filter(self):
        """Should filter notifications by status."""
        Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_IN_APP,
            subject='Pending',
            content='Content',
            status=Notification.STATUS_PENDING
        )
        Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_IN_APP,
            subject='Sent',
            content='Content',
            status=Notification.STATUS_SENT
        )

        result = self.service.get_user_notifications(
            self.user.id,
            status=Notification.STATUS_SENT
        )
        assert result['total'] == 1
        assert result['notifications'][0]['subject'] == 'Sent'

    def test_mark_as_read(self):
        """Should mark notification as read."""
        notification = Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_IN_APP,
            subject='Test',
            content='Content',
            status=Notification.STATUS_DELIVERED
        )

        success = self.service.mark_as_read(str(notification.id), self.user.id)
        assert success is True

        notification.refresh_from_db()
        assert notification.status == Notification.STATUS_READ

    def test_mark_all_as_read(self):
        """Should mark all notifications as read."""
        for i in range(3):
            Notification.objects.create(
                user=self.user,
                opportunity=self.opportunity,
                notification_type=Notification.TYPE_IN_APP,
                subject=f'Test {i}',
                content='Content',
                status=Notification.STATUS_DELIVERED
            )

        count = self.service.mark_all_as_read(self.user.id)
        assert count == 3

        unread = Notification.objects.filter(
            user=self.user,
            status=Notification.STATUS_DELIVERED
        ).count()
        assert unread == 0

    def test_get_unread_count(self):
        """Should get unread notification count."""
        # Create delivered (unread) notifications
        for i in range(5):
            Notification.objects.create(
                user=self.user,
                opportunity=self.opportunity,
                notification_type=Notification.TYPE_IN_APP,
                subject=f'Test {i}',
                content='Content',
                status=Notification.STATUS_DELIVERED
            )

        count = self.service.get_unread_count(self.user.id)
        assert count == 5

    def test_rate_limiting(self):
        """Should enforce rate limiting."""
        self.service.rate_limit_per_user = 2

        # Create notifications up to limit
        for i in range(3):
            notif = self.service.create_notification(
                user_id=self.user.id,
                opportunity_id=str(self.opportunity.id),
                channels=['in_app']
            )
            # Only first 2 should be created
            if i < 2:
                assert notif is not None
            else:
                assert notif is None

    def test_build_notification_content(self):
        """Should build notification content."""
        subject, content = self.service._build_notification_content(
            self.opportunity,
            {'score': 90.0, 'matched_keywords': [{'value': 'construction'}]}
        )
        assert 'Test Construction Project' in subject
        assert 'construction' in content.lower()

    def test_create_notifications_from_match(self):
        """Should create notifications from match result."""
        match = MatchResult.objects.create(
            subscription=self.subscription,
            opportunity=self.opportunity,
            score=85.0,
            matched_keywords=[{'value': 'construction'}],
            is_notified=False
        )

        notifications = self.service.create_notifications_from_match(str(match.id))
        assert len(notifications) > 0

        match.refresh_from_db()
        assert match.is_notified is True

    def test_digest_mode_deferral(self):
        """Should defer notifications in digest mode."""
        # Set user preference to digest mode
        pref, _ = UserNotificationPreference.objects.get_or_create(
            user=self.user,
            defaults={'digest_mode': UserNotificationPreference.DIGEST_DAILY}
        )
        pref.digest_mode = UserNotificationPreference.DIGEST_DAILY
        pref.save()

        match = MatchResult.objects.create(
            subscription=self.subscription,
            opportunity=self.opportunity,
            score=85.0,
            is_notified=False
        )

        # Should not create immediate notifications
        notifications = self.service.create_notifications_from_match(str(match.id))
        assert len(notifications) == 0


class TestNotificationStatusTransitions(TestCase):
    """Test notification status transitions."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.opportunity = TenderNotice.objects.create(
            title='Test Opportunity',
            notice_id='TEST-001',
            notice_type=TenderNotice.TYPE_BIDDING,
            status=TenderNotice.STATUS_PENDING
        )

    def test_pending_to_sent(self):
        """Test transition from pending to sent."""
        notification = Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_EMAIL,
            subject='Test',
            content='Content',
            status=Notification.STATUS_PENDING
        )
        notification.mark_as_sent()
        assert notification.status == Notification.STATUS_SENT

    def test_sent_to_delivered(self):
        """Test transition from sent to delivered."""
        notification = Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_EMAIL,
            subject='Test',
            content='Content',
            status=Notification.STATUS_SENT
        )
        notification.mark_as_delivered()
        assert notification.status == Notification.STATUS_DELIVERED

    def test_delivered_to_read(self):
        """Test transition from delivered to read."""
        notification = Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_IN_APP,
            subject='Test',
            content='Content',
            status=Notification.STATUS_DELIVERED
        )
        notification.mark_as_read()
        assert notification.status == Notification.STATUS_READ

    def test_pending_to_failed(self):
        """Test transition from pending to failed."""
        notification = Notification.objects.create(
            user=self.user,
            opportunity=self.opportunity,
            notification_type=Notification.TYPE_EMAIL,
            subject='Test',
            content='Content',
            status=Notification.STATUS_PENDING
        )
        notification.mark_as_failed('SMTP error')
        assert notification.status == Notification.STATUS_FAILED
        assert notification.error_message == 'SMTP error'


class TestQuietHours(TestCase):
    """Test quiet hours functionality."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_overnight_quiet_hours(self):
        """Test overnight quiet hours (22:00 - 08:00)."""
        pref = UserNotificationPreference.objects.create(
            user=self.user,
            quiet_hours_start=time(22, 0),
            quiet_hours_end=time(8, 0)
        )

        # During quiet hours
        assert pref.is_quiet_hours(time(23, 0)) is True
        assert pref.is_quiet_hours(time(3, 0)) is True

        # Outside quiet hours
        assert pref.is_quiet_hours(time(12, 0)) is False
        assert pref.is_quiet_hours(time(18, 0)) is False

    def test_daytime_quiet_hours(self):
        """Test daytime quiet hours (12:00 - 14:00)."""
        pref = UserNotificationPreference.objects.create(
            user=self.user,
            quiet_hours_start=time(12, 0),
            quiet_hours_end=time(14, 0)
        )

        # During quiet hours
        assert pref.is_quiet_hours(time(13, 0)) is True

        # Outside quiet hours
        assert pref.is_quiet_hours(time(10, 0)) is False
        assert pref.is_quiet_hours(time(16, 0)) is False
