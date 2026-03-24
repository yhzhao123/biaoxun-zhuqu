"""
Subscription Service - Phase 8 Tasks 042-043
Business logic for subscription operations
"""

import re
from typing import List, Optional, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import Subscription, Keyword, SubscriptionKeyword


class SubscriptionService:
    """Service for managing subscriptions and keywords."""

    def __init__(self):
        self.max_subscriptions_per_user = getattr(
            settings, 'SUBSCRIPTION_MAX_PER_USER', 10
        )
        self.max_keywords_per_subscription = getattr(
            settings, 'SUBSCRIPTION_MAX_KEYWORDS', 50
        )
        self.max_keyword_length = getattr(
            settings, 'SUBSCRIPTION_KEYWORD_MAX_LENGTH', 200
        )

    def create_subscription(
        self,
        user_id: int,
        name: str,
        description: str = '',
        notification_channels: Optional[Dict[str, bool]] = None,
        frequency: str = Subscription.FREQUENCY_DAILY,
        keywords_data: Optional[List[Dict]] = None
    ) -> Subscription:
        """
        Create a new subscription for a user.

        Args:
            user_id: The user ID
            name: Subscription name
            description: Optional description
            notification_channels: Dict with notify_email, notify_in_app, notify_sms
            frequency: Notification frequency
            keywords_data: Optional initial keywords

        Returns:
            Created Subscription instance

        Raises:
            ValidationError: If subscription limit exceeded or invalid data
        """
        # Check subscription limit
        current_count = Subscription.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True
        ).count()

        if current_count >= self.max_subscriptions_per_user:
            raise ValidationError(
                f'用户最多只能创建 {self.max_subscriptions_per_user} 个订阅'
            )

        # Validate name
        if not name or len(name) > 100:
            raise ValidationError('订阅名称不能为空且不能超过100字符')

        # Prepare notification channels
        channels = notification_channels or {}

        with transaction.atomic():
            subscription = Subscription.objects.create(
                user_id=user_id,
                name=name,
                description=description,
                notify_email=channels.get('email', True),
                notify_in_app=channels.get('in_app', True),
                notify_sms=channels.get('sms', False),
                frequency=frequency
            )

            # Add initial keywords if provided
            if keywords_data:
                self.add_keywords(subscription.id, user_id, keywords_data)

        return subscription

    def get_subscription(
        self,
        subscription_id: str,
        user_id: int
    ) -> Optional[Subscription]:
        """
        Get a subscription by ID with user authorization check.

        Args:
            subscription_id: The subscription UUID
            user_id: The user ID for authorization

        Returns:
            Subscription instance or None if not found/unauthorized
        """
        try:
            subscription = Subscription.objects.get(
                id=subscription_id,
                deleted_at__isnull=True
            )
            if subscription.user_id != user_id:
                return None
            return subscription
        except Subscription.DoesNotExist:
            return None

    def list_user_subscriptions(
        self,
        user_id: int,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        List subscriptions for a user.

        Args:
            user_id: The user ID
            is_active: Filter by active status
            limit: Maximum number of results
            offset: Offset for pagination

        Returns:
            Dict with subscriptions list and pagination info
        """
        queryset = Subscription.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True
        )

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        total = queryset.count()
        subscriptions = queryset.order_by('-created_at')[offset:offset + limit]

        return {
            'subscriptions': subscriptions,
            'total': total,
            'limit': limit,
            'offset': offset
        }

    def update_subscription(
        self,
        subscription_id: str,
        user_id: int,
        update_data: Dict[str, Any]
    ) -> Optional[Subscription]:
        """
        Update a subscription.

        Args:
            subscription_id: The subscription UUID
            user_id: The user ID for authorization
            update_data: Dict of fields to update

        Returns:
            Updated Subscription instance or None
        """
        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            return None

        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'frequency',
            'notify_email', 'notify_in_app', 'notify_sms'
        ]

        for field in allowed_fields:
            if field in update_data:
                setattr(subscription, field, update_data[field])

        subscription.save()
        return subscription

    def delete_subscription(
        self,
        subscription_id: str,
        user_id: int
    ) -> bool:
        """
        Soft delete a subscription.

        Args:
            subscription_id: The subscription UUID
            user_id: The user ID for authorization

        Returns:
            True if deleted, False otherwise
        """
        from django.utils import timezone

        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            return False

        subscription.deleted_at = timezone.now()
        subscription.is_active = False
        subscription.save(update_fields=['deleted_at', 'is_active'])
        return True

    def activate_subscription(
        self,
        subscription_id: str,
        user_id: int
    ) -> Optional[Subscription]:
        """Activate a subscription."""
        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            return None

        subscription.is_active = True
        subscription.save(update_fields=['is_active'])
        return subscription

    def deactivate_subscription(
        self,
        subscription_id: str,
        user_id: int
    ) -> Optional[Subscription]:
        """Deactivate a subscription."""
        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            return None

        subscription.is_active = False
        subscription.save(update_fields=['is_active'])
        return subscription

    def add_keywords(
        self,
        subscription_id: str,
        user_id: int,
        keywords_data: List[Dict]
    ) -> List[SubscriptionKeyword]:
        """
        Add keywords to a subscription.

        Args:
            subscription_id: The subscription UUID
            user_id: The user ID for authorization
            keywords_data: List of keyword dicts with value, match_type, etc.

        Returns:
            List of created SubscriptionKeyword instances

        Raises:
            ValidationError: If keyword limit exceeded or invalid data
        """
        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            raise ValidationError('订阅不存在或无权访问')

        # Check current keyword count
        current_count = SubscriptionKeyword.objects.filter(
            subscription=subscription
        ).count()

        if current_count + len(keywords_data) > self.max_keywords_per_subscription:
            raise ValidationError(
                f'每个订阅最多只能有 {self.max_keywords_per_subscription} 个关键词'
            )

        created = []
        with transaction.atomic():
            for kw_data in keywords_data:
                # Validate keyword value
                value = kw_data.get('value', '').strip()
                if not value or len(value) > self.max_keyword_length:
                    raise ValidationError(
                        f'关键词不能为空且不能超过 {self.max_keyword_length} 字符'
                    )

                # Validate match type
                match_type = kw_data.get('match_type', Keyword.MATCH_CONTAINS)
                if match_type not in [c[0] for c in Keyword.MATCH_CHOICES]:
                    raise ValidationError(f'无效的匹配类型: {match_type}')

                # Validate regex pattern if regex type
                if match_type == Keyword.MATCH_REGEX:
                    try:
                        re.compile(value)
                    except re.error as e:
                        raise ValidationError(f'无效的正则表达式: {e}')

                # Get or create keyword
                keyword, _ = Keyword.objects.get_or_create(
                    value=value,
                    match_type=match_type,
                    case_sensitive=kw_data.get('case_sensitive', False)
                )

                # Check for duplicates
                if SubscriptionKeyword.objects.filter(
                    subscription=subscription,
                    keyword=keyword
                ).exists():
                    continue

                # Create association
                sub_kw = SubscriptionKeyword.objects.create(
                    subscription=subscription,
                    keyword=keyword,
                    is_required=kw_data.get('is_required', False),
                    weight=kw_data.get('weight', 1.0)
                )
                created.append(sub_kw)

        return created

    def remove_keywords(
        self,
        subscription_id: str,
        user_id: int,
        keyword_ids: List[str]
    ) -> int:
        """
        Remove keywords from a subscription.

        Args:
            subscription_id: The subscription UUID
            user_id: The user ID for authorization
            keyword_ids: List of keyword UUIDs to remove

        Returns:
            Number of keywords removed
        """
        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            return 0

        deleted, _ = SubscriptionKeyword.objects.filter(
            subscription=subscription,
            keyword_id__in=keyword_ids
        ).delete()

        return deleted

    def update_keyword(
        self,
        subscription_id: str,
        user_id: int,
        keyword_id: str,
        update_data: Dict[str, Any]
    ) -> Optional[SubscriptionKeyword]:
        """
        Update a subscription keyword association.

        Args:
            subscription_id: The subscription UUID
            user_id: The user ID for authorization
            keyword_id: The keyword UUID
            update_data: Dict with is_required, weight

        Returns:
            Updated SubscriptionKeyword or None
        """
        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            return None

        try:
            sub_kw = SubscriptionKeyword.objects.get(
                subscription=subscription,
                keyword_id=keyword_id
            )

            if 'is_required' in update_data:
                sub_kw.is_required = update_data['is_required']
            if 'weight' in update_data:
                sub_kw.weight = update_data['weight']

            sub_kw.save()
            return sub_kw
        except SubscriptionKeyword.DoesNotExist:
            return None

    def get_subscription_keywords(
        self,
        subscription_id: str,
        user_id: int
    ) -> List[SubscriptionKeyword]:
        """
        Get all keywords for a subscription.

        Args:
            subscription_id: The subscription UUID
            user_id: The user ID for authorization

        Returns:
            List of SubscriptionKeyword instances
        """
        subscription = self.get_subscription(subscription_id, user_id)
        if not subscription:
            return []

        return list(SubscriptionKeyword.objects.filter(
            subscription=subscription
        ).select_related('keyword'))

    def validate_subscription_limit(self, user_id: int) -> bool:
        """Check if user can create more subscriptions."""
        count = Subscription.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True
        ).count()
        return count < self.max_subscriptions_per_user

    def validate_keyword_limit(self, subscription_id: str) -> bool:
        """Check if subscription can add more keywords."""
        count = SubscriptionKeyword.objects.filter(
            subscription_id=subscription_id
        ).count()
        return count < self.max_keywords_per_subscription
