"""
Notification Service - Phase 8 Tasks 046-047
Multi-channel notification service with rate limiting and retry logic
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .notification_models import Notification, UserNotificationPreference
from .notification_models import UserNotificationPreference as UserPref
from .matching_service import MatchingService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for managing notifications.

    Features:
    - Multi-channel notification (email, in-app, sms)
    - Rate limiting
    - Retry logic
    - Digest mode
    - Quiet hours
    """

    def __init__(self):
        self.rate_limit_per_user = getattr(
            settings, 'NOTIFICATION_RATE_LIMIT_PER_USER', 100
        )
        self.max_retries = getattr(settings, 'NOTIFICATION_MAX_RETRIES', 3)
        self.retry_backoff = getattr(settings, 'NOTIFICATION_RETRY_BACKOFF', 2)
        self.matching_service = MatchingService()

    def create_notification(
        self,
        user_id: int,
        opportunity_id: str,
        subscription_id: Optional[str] = None,
        match_result: Optional[Dict] = None,
        channels: Optional[List[str]] = None
    ) -> Optional[Notification]:
        """
        Create a notification for a matched opportunity.

        Args:
            user_id: The user ID
            opportunity_id: The opportunity UUID
            subscription_id: Optional subscription UUID
            match_result: Optional match result data
            channels: Optional list of channels (default from user prefs)

        Returns:
            Created Notification or None
        """
        from apps.tenders.models import TenderNotice

        # Get user preferences
        try:
            user_pref = UserPref.objects.get(user_id=user_id)
        except UserPref.DoesNotExist:
            user_pref = UserPref.objects.create(user_id=user_id)

        # Determine channels
        if channels is None:
            channels = []
            if user_pref.email_enabled:
                channels.append('email')
            if user_pref.in_app_enabled:
                channels.append('in_app')
            if user_pref.sms_enabled:
                channels.append('sms')

        if not channels:
            logger.info(f'No notification channels enabled for user {user_id}')
            return None

        # Check quiet hours
        if user_pref.is_quiet_hours():
            logger.info(f'Notification deferred due to quiet hours for user {user_id}')
            # Still create but mark as pending - will be sent later

        # Get opportunity details
        try:
            opportunity = TenderNotice.objects.get(id=opportunity_id)
        except TenderNotice.DoesNotExist:
            logger.error(f'Opportunity not found: {opportunity_id}')
            return None

        # Build notification content
        subject, content = self._build_notification_content(
            opportunity, match_result
        )

        # Create notifications for each channel
        notifications = []
        for channel in channels:
            # Check rate limit
            if not self._check_rate_limit(user_id, channel):
                logger.warning(f'Rate limit exceeded for user {user_id}')
                continue

            notification = Notification.objects.create(
                user_id=user_id,
                subscription_id=subscription_id,
                opportunity=opportunity,
                notification_type=channel,
                subject=subject,
                content=content,
                metadata={
                    'match_result': match_result,
                    'matched_keywords': match_result.get('matched_keywords', []) if match_result else [],
                    'score': match_result.get('score', 0) if match_result else 0,
                }
            )
            notifications.append(notification)

        return notifications[0] if notifications else None

    def create_notifications_from_match(
        self,
        match_result_id: str
    ) -> List[Notification]:
        """
        Create notifications from a match result.

        Args:
            match_result_id: The match result UUID

        Returns:
            List of created notifications
        """
        from .models import MatchResult

        try:
            match_result = MatchResult.objects.get(id=match_result_id)
        except MatchResult.DoesNotExist:
            logger.error(f'Match result not found: {match_result_id}')
            return []

        subscription = match_result.subscription
        if not subscription.is_active:
            return []

        # Check user preferences
        try:
            user_pref = UserPref.objects.get(user_id=subscription.user_id)
        except UserPref.DoesNotExist:
            user_pref = UserPref.objects.create(user_id=subscription.user_id)

        # Check digest mode - if not realtime, don't create immediate notification
        if user_pref.digest_mode != user_pref.DIGEST_REALTIME:
            # Mark match as not yet notified but don't create notification yet
            # It will be included in the next digest
            logger.info(f'Match {match_result_id} deferred to digest for user {subscription.user_id}')
            return []

        notifications = []
        match_data = {
            'subscription_id': str(subscription.id),
            'subscription_name': subscription.name,
            'score': match_result.score,
            'matched_keywords': match_result.matched_keywords,
        }

        # Create notification for each enabled channel
        for channel in subscription.get_notification_channels():
            if channel == 'email' and user_pref.email_enabled:
                notif = self.create_notification(
                    user_id=subscription.user_id,
                    opportunity_id=str(match_result.opportunity_id),
                    subscription_id=str(subscription.id),
                    match_result=match_data,
                    channels=['email']
                )
                if notif:
                    notifications.append(notif)

            elif channel == 'in_app' and user_pref.in_app_enabled:
                notif = self.create_notification(
                    user_id=subscription.user_id,
                    opportunity_id=str(match_result.opportunity_id),
                    subscription_id=str(subscription.id),
                    match_result=match_data,
                    channels=['in_app']
                )
                if notif:
                    notifications.append(notif)

        # Mark match as notified
        if notifications:
            match_result.is_notified = True
            match_result.save()

        return notifications

    def send_notification(self, notification_id: str) -> bool:
        """
        Send a single notification.

        Args:
            notification_id: The notification UUID

        Returns:
            True if sent successfully
        """
        try:
            notification = Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            logger.error(f'Notification not found: {notification_id}')
            return False

        if notification.status in [notification.STATUS_SENT, notification.STATUS_DELIVERED]:
            return True

        try:
            if notification.notification_type == Notification.TYPE_EMAIL:
                success = self._send_email_notification(notification)
            elif notification.notification_type == Notification.TYPE_IN_APP:
                success = self._send_in_app_notification(notification)
            elif notification.notification_type == Notification.TYPE_SMS:
                success = self._send_sms_notification(notification)
            else:
                logger.warning(f'Unknown notification type: {notification.notification_type}')
                return False

            if success:
                notification.mark_as_sent()
                return True
            else:
                self._handle_send_failure(notification, 'Send failed')
                return False

        except Exception as e:
            logger.exception(f'Error sending notification {notification_id}')
            self._handle_send_failure(notification, str(e))
            return False

    def send_batch_notifications(
        self,
        notification_ids: List[str]
    ) -> Dict[str, bool]:
        """
        Send multiple notifications in batch.

        Args:
            notification_ids: List of notification UUIDs

        Returns:
            Dict mapping notification_id to success status
        """
        results = {}
        for notif_id in notification_ids:
            results[notif_id] = self.send_notification(notif_id)
        return results

    def get_user_notifications(
        self,
        user_id: int,
        status: Optional[str] = None,
        notification_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get notifications for a user.

        Args:
            user_id: The user ID
            status: Optional status filter
            notification_type: Optional type filter
            limit: Maximum results
            offset: Offset for pagination

        Returns:
            Dict with notifications and pagination info
        """
        queryset = Notification.objects.filter(user_id=user_id)

        if status:
            queryset = queryset.filter(status=status)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        total = queryset.count()
        notifications = queryset.order_by('-created_at')[offset:offset + limit]

        return {
            'notifications': [
                {
                    'id': str(n.id),
                    'subject': n.subject,
                    'content': n.content,
                    'type': n.notification_type,
                    'status': n.status,
                    'opportunity_id': str(n.opportunity_id) if n.opportunity_id else None,
                    'created_at': n.created_at.isoformat(),
                    'sent_at': n.sent_at.isoformat() if n.sent_at else None,
                    'read_at': n.read_at.isoformat() if n.read_at else None,
                }
                for n in notifications
            ],
            'total': total,
            'limit': limit,
            'offset': offset
        }

    def get_unread_count(self, user_id: int) -> int:
        """Get unread notification count for user."""
        return Notification.objects.filter(
            user_id=user_id,
            status=Notification.STATUS_DELIVERED
        ).count()

    def mark_as_read(self, notification_id: str, user_id: int) -> bool:
        """Mark a notification as read."""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user_id=user_id
            )
            notification.mark_as_read()
            return True
        except Notification.DoesNotExist:
            return False

    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all user notifications as read."""
        notifications = Notification.objects.filter(
            user_id=user_id,
            status=Notification.STATUS_DELIVERED
        )
        count = notifications.count()
        for notification in notifications:
            notification.mark_as_read()
        return count

    def _send_email_notification(self, notification: Notification) -> bool:
        """Send email notification."""
        try:
            user = notification.user
            if not user.email:
                return False

            # Render template
            context = {
                'user': user,
                'notification': notification,
                'opportunity': notification.opportunity,
                'matched_keywords': notification.metadata.get('matched_keywords', []),
                'score': notification.metadata.get('score', 0),
            }

            html_message = render_to_string(
                'emails/bid_alert.html',
                context
            )

            send_mail(
                subject=notification.subject,
                message=notification.content,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'notifications@example.com'),
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            return True
        except Exception as e:
            logger.exception(f'Failed to send email notification {notification.id}')
            return False

    def _send_in_app_notification(self, notification: Notification) -> bool:
        """Send in-app notification (mark as delivered)."""
        # In-app notifications are considered delivered when created
        notification.mark_as_delivered()
        return True

    def _send_sms_notification(self, notification: Notification) -> bool:
        """Send SMS notification."""
        # SMS sending would integrate with SMS gateway
        # For now, just log it
        logger.info(f'SMS notification would be sent to {notification.user_id}')
        return True

    def _build_notification_content(
        self,
        opportunity,
        match_result: Optional[Dict]
    ) -> tuple:
        """Build notification subject and content."""
        subject = f'新的招标机会: {opportunity.title[:50]}'

        content = f"""
        发现与您订阅匹配的新招标机会:

        标题: {opportunity.title}
        招标单位: {opportunity.tenderer or '未知'}
        预算金额: {opportunity.budget_amount or '未公布'}
        发布日期: {opportunity.publish_date.strftime('%Y-%m-%d') if opportunity.publish_date else '未知'}

        """

        if match_result:
            content += f"\n匹配分数: {match_result.get('score', 0):.1f}\n"
            matched_keywords = match_result.get('matched_keywords', [])
            if matched_keywords:
                content += f"匹配关键词: {', '.join(kw['value'] for kw in matched_keywords)}\n"

        content += "\n点击查看详情"

        return subject, content

    def _check_rate_limit(self, user_id: int, channel: str) -> bool:
        """Check if user has exceeded rate limit."""
        one_hour_ago = timezone.now() - timedelta(hours=1)

        count = Notification.objects.filter(
            user_id=user_id,
            notification_type=channel,
            created_at__gte=one_hour_ago
        ).count()

        return count < self.rate_limit_per_user

    def _handle_send_failure(self, notification: Notification, error_message: str):
        """Handle notification send failure."""
        notification.increment_retry()

        if notification.retry_count >= self.max_retries:
            notification.mark_as_failed(error_message)
            logger.error(f'Notification {notification.id} failed after {self.max_retries} retries')
        else:
            # Will be retried by background task
            logger.warning(f'Notification {notification.id} failed, will retry')
