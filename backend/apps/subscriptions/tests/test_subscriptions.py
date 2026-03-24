"""
Subscription Tests - Phase 8 Tasks 042-043
Tests for subscription management module
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from apps.subscriptions.models import (
    Subscription, Keyword, SubscriptionKeyword, MatchResult
)
from apps.subscriptions.subscription_service import SubscriptionService
from apps.subscriptions.matchers import (
    ExactMatcher, ContainsMatcher, StartsWithMatcher, EndsWithMatcher,
    RegexMatcher, MatcherFactory
)
from apps.tenders.models import TenderNotice


User = get_user_model()


class TestSubscriptionModel(TestCase):
    """Test Subscription model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_subscription(self):
        """Should create subscription with valid data."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test Subscription',
            description='Test description',
            notify_email=True,
            notify_in_app=True,
            frequency=Subscription.FREQUENCY_DAILY
        )
        assert subscription.id is not None
        assert subscription.name == 'Test Subscription'
        assert subscription.is_active is True

    def test_subscription_string_representation(self):
        """Should return proper string representation."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        assert str(subscription) == 'Test Sub (testuser)'

    def test_get_notification_channels(self):
        """Should return enabled notification channels."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test',
            notify_email=True,
            notify_in_app=True,
            notify_sms=False
        )
        channels = subscription.get_notification_channels()
        assert 'email' in channels
        assert 'in_app' in channels
        assert 'sms' not in channels

    def test_is_deleted(self):
        """Should correctly check deletion status."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test',
            frequency=Subscription.FREQUENCY_DAILY
        )
        assert not subscription.is_deleted()

        subscription.deleted_at = datetime.now()
        assert subscription.is_deleted()


class TestKeywordModel(TestCase):
    """Test Keyword model."""

    def test_create_keyword(self):
        """Should create keyword with valid data."""
        keyword = Keyword.objects.create(
            value='construction',
            match_type=Keyword.MATCH_CONTAINS,
            case_sensitive=False
        )
        assert keyword.id is not None
        assert keyword.value == 'construction'
        assert keyword.match_type == Keyword.MATCH_CONTAINS

    def test_keyword_match_type_choices(self):
        """Should validate match type choices."""
        valid_types = [
            Keyword.MATCH_EXACT,
            Keyword.MATCH_CONTAINS,
            Keyword.MATCH_STARTS_WITH,
            Keyword.MATCH_ENDS_WITH,
            Keyword.MATCH_REGEX,
        ]
        for match_type in valid_types:
            keyword = Keyword.objects.create(
                value=f'test_{match_type}',
                match_type=match_type
            )
            assert keyword.match_type == match_type


class TestSubscriptionKeywordAssociation(TestCase):
    """Test SubscriptionKeyword association."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            name='Test Subscription',
            frequency=Subscription.FREQUENCY_DAILY
        )
        self.keyword = Keyword.objects.create(
            value='test',
            match_type=Keyword.MATCH_CONTAINS
        )

    def test_create_association(self):
        """Should create subscription-keyword association."""
        assoc = SubscriptionKeyword.objects.create(
            subscription=self.subscription,
            keyword=self.keyword,
            is_required=True,
            weight=2.0
        )
        assert assoc.subscription == self.subscription
        assert assoc.keyword == self.keyword
        assert assoc.is_required is True
        assert assoc.weight == 2.0

    def test_unique_constraint(self):
        """Should enforce unique constraint on subscription-keyword."""
        SubscriptionKeyword.objects.create(
            subscription=self.subscription,
            keyword=self.keyword
        )
        with pytest.raises(Exception):
            SubscriptionKeyword.objects.create(
                subscription=self.subscription,
                keyword=self.keyword
            )


class TestSubscriptionService(TestCase):
    """Test SubscriptionService."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = SubscriptionService()

    def test_create_subscription(self):
        """Should create subscription with service."""
        subscription = self.service.create_subscription(
            user_id=self.user.id,
            name='New Subscription',
            description='Test desc',
            notification_channels={'email': True, 'in_app': True}
        )
        assert subscription.name == 'New Subscription'
        assert subscription.user_id == self.user.id

    def test_create_subscription_without_name(self):
        """Should raise error when name is missing."""
        with pytest.raises(ValidationError):
            self.service.create_subscription(
                user_id=self.user.id,
                name=''
            )

    def test_get_subscription(self):
        """Should get subscription by ID."""
        sub = self.service.create_subscription(
            user_id=self.user.id,
            name='Test Sub'
        )
        result = self.service.get_subscription(str(sub.id), self.user.id)
        assert result is not None
        assert result.name == 'Test Sub'

    def test_get_subscription_wrong_user(self):
        """Should return None for wrong user."""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        sub = self.service.create_subscription(
            user_id=self.user.id,
            name='Test Sub'
        )
        result = self.service.get_subscription(str(sub.id), other_user.id)
        assert result is None

    def test_list_user_subscriptions(self):
        """Should list user's subscriptions."""
        self.service.create_subscription(
            user_id=self.user.id,
            name='Sub 1'
        )
        self.service.create_subscription(
            user_id=self.user.id,
            name='Sub 2'
        )
        result = self.service.list_user_subscriptions(self.user.id)
        assert result['total'] == 2
        assert len(result['subscriptions']) == 2

    def test_activate_deactivate_subscription(self):
        """Should activate and deactivate subscription."""
        sub = self.service.create_subscription(
            user_id=self.user.id,
            name='Test Sub'
        )
        assert sub.is_active is True

        deactivated = self.service.deactivate_subscription(str(sub.id), self.user.id)
        assert deactivated.is_active is False

        activated = self.service.activate_subscription(str(sub.id), self.user.id)
        assert activated.is_active is True

    def test_delete_subscription(self):
        """Should soft delete subscription."""
        sub = self.service.create_subscription(
            user_id=self.user.id,
            name='Test Sub'
        )
        success = self.service.delete_subscription(str(sub.id), self.user.id)
        assert success is True

        # Should not be found anymore
        result = self.service.get_subscription(str(sub.id), self.user.id)
        assert result is None


class TestKeywordManagement(TestCase):
    """Test keyword management in subscription service."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = SubscriptionService()
        self.subscription = self.service.create_subscription(
            user_id=self.user.id,
            name='Test Sub'
        )

    def test_add_keywords(self):
        """Should add keywords to subscription."""
        keywords_data = [
            {'value': 'construction', 'match_type': Keyword.MATCH_CONTAINS},
            {'value': 'building', 'match_type': Keyword.MATCH_EXACT},
        ]
        result = self.service.add_keywords(
            str(self.subscription.id),
            self.user.id,
            keywords_data
        )
        assert len(result) == 2

    def test_add_duplicate_keywords(self):
        """Should skip duplicate keywords."""
        keywords_data = [
            {'value': 'construction', 'match_type': Keyword.MATCH_CONTAINS},
        ]
        self.service.add_keywords(
            str(self.subscription.id),
            self.user.id,
            keywords_data
        )
        # Add same keyword again
        result = self.service.add_keywords(
            str(self.subscription.id),
            self.user.id,
            keywords_data
        )
        # Should return empty list as it's duplicate
        assert len(result) == 0

    def test_add_invalid_regex_keyword(self):
        """Should raise error for invalid regex."""
        keywords_data = [
            {'value': '[invalid(', 'match_type': Keyword.MATCH_REGEX},
        ]
        with pytest.raises(ValidationError):
            self.service.add_keywords(
                str(self.subscription.id),
                self.user.id,
                keywords_data
            )

    def test_remove_keywords(self):
        """Should remove keywords from subscription."""
        # Add keywords first
        keywords_data = [
            {'value': 'construction', 'match_type': Keyword.MATCH_CONTAINS},
            {'value': 'building', 'match_type': Keyword.MATCH_EXACT},
        ]
        self.service.add_keywords(
            str(self.subscription.id),
            self.user.id,
            keywords_data
        )

        # Get keyword IDs
        keywords = self.service.get_subscription_keywords(
            str(self.subscription.id),
            self.user.id
        )
        keyword_ids = [str(kw.keyword.id) for kw in keywords]

        # Remove keywords
        deleted = self.service.remove_keywords(
            str(self.subscription.id),
            self.user.id,
            keyword_ids[:1]
        )
        assert deleted == 1


class TestMatchers(TestCase):
    """Test matcher classes."""

    def test_exact_matcher(self):
        """Test exact matcher."""
        matcher = ExactMatcher()
        # Case sensitive (default)
        assert matcher.match('Construction Project', 'Construction Project', case_sensitive=True) is True
        assert matcher.match('Construction Project', 'construction project', case_sensitive=True) is False
        assert matcher.match('Construction Project', 'Construction', case_sensitive=True) is False
        # Case insensitive
        assert matcher.match('Construction Project', 'construction project', case_sensitive=False) is True
        assert matcher.match('Construction Project', 'Construction Project', case_sensitive=False) is True

    def test_contains_matcher(self):
        """Test contains matcher."""
        matcher = ContainsMatcher()
        assert matcher.match('Building Construction Project', 'Construction') is True
        assert matcher.match('Building Construction Project', 'construction', case_sensitive=False) is True
        assert matcher.match('Building Construction Project', 'xyz') is False

    def test_starts_with_matcher(self):
        """Test starts with matcher."""
        matcher = StartsWithMatcher()
        assert matcher.match('Construction Project', 'Construction') is True
        assert matcher.match('Construction Project', 'Project') is False
        assert matcher.match('Construction Project', 'construction', case_sensitive=False) is True

    def test_ends_with_matcher(self):
        """Test ends with matcher."""
        matcher = EndsWithMatcher()
        assert matcher.match('Construction Project', 'Project') is True
        assert matcher.match('Construction Project', 'Construction') is False
        assert matcher.match('Construction Project', 'project', case_sensitive=False) is True

    def test_regex_matcher(self):
        """Test regex matcher."""
        matcher = RegexMatcher()
        assert matcher.match('Construction 2024', r'\d{4}') is True
        assert matcher.match('Construction', r'\d{4}') is False
        assert matcher.validate_pattern(r'\d{4}') is True
        assert matcher.validate_pattern('[invalid(') is False

    def test_matcher_factory(self):
        """Test matcher factory."""
        factory = MatcherFactory()
        assert isinstance(factory.get_matcher('exact'), ExactMatcher)
        assert isinstance(factory.get_matcher('contains'), ContainsMatcher)
        assert isinstance(factory.get_matcher('starts_with'), StartsWithMatcher)
        assert isinstance(factory.get_matcher('ends_with'), EndsWithMatcher)
        assert isinstance(factory.get_matcher('regex'), RegexMatcher)


class TestSubscriptionLimits(TestCase):
    """Test subscription and keyword limits."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = SubscriptionService()
        self.service.max_subscriptions_per_user = 3
        self.service.max_keywords_per_subscription = 5

    def test_subscription_limit(self):
        """Should enforce subscription limit per user."""
        # Create max subscriptions
        for i in range(3):
            self.service.create_subscription(
                user_id=self.user.id,
                name=f'Sub {i}'
            )

        # Next should fail
        with pytest.raises(ValidationError):
            self.service.create_subscription(
                user_id=self.user.id,
                name='Sub 4'
            )

    def test_keyword_limit(self):
        """Should enforce keyword limit per subscription."""
        sub = self.service.create_subscription(
            user_id=self.user.id,
            name='Test Sub'
        )

        # Try to add more than limit
        keywords_data = [
            {'value': f'keyword{i}', 'match_type': Keyword.MATCH_CONTAINS}
            for i in range(6)
        ]

        with pytest.raises(ValidationError):
            self.service.add_keywords(
                str(sub.id),
                self.user.id,
                keywords_data
            )


class TestMatchResultModel(TestCase):
    """Test MatchResult model."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subscription = Subscription.objects.create(
            user=self.user,
            name='Test Subscription',
            frequency=Subscription.FREQUENCY_DAILY
        )
        self.opportunity = TenderNotice.objects.create(
            title='Test Opportunity',
            notice_id='TEST-001',
            notice_type=TenderNotice.TYPE_BIDDING,
            status=TenderNotice.STATUS_PENDING
        )

    def test_create_match_result(self):
        """Should create match result."""
        result = MatchResult.objects.create(
            subscription=self.subscription,
            opportunity=self.opportunity,
            score=85.5,
            matched_keywords=[{'value': 'test', 'weight': 1.0}],
            match_details={'test': True},
            is_notified=False
        )
        assert result.score == 85.5
        assert result.is_notified is False

    def test_unique_constraint(self):
        """Should enforce unique constraint on subscription-opportunity."""
        MatchResult.objects.create(
            subscription=self.subscription,
            opportunity=self.opportunity,
            score=50.0
        )
        with pytest.raises(Exception):
            MatchResult.objects.create(
                subscription=self.subscription,
                opportunity=self.opportunity,
                score=60.0
            )
