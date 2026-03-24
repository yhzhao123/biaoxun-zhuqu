"""
Matching and Rule Engine Tests - Phase 8 Tasks 044-045
Tests for keyword matching algorithm and rule engine
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.subscriptions.models import (
    Subscription, Keyword, SubscriptionKeyword, MatchResult
)
from apps.subscriptions.rule_engine import RuleEngine, MatchResult as RuleMatchResult
from apps.subscriptions.matching_service import MatchingService
from apps.subscriptions.matchers import MatcherFactory
from apps.tenders.models import TenderNotice


User = get_user_model()


class TestRuleEngine(TestCase):
    """Test RuleEngine."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.rule_engine = RuleEngine(
            min_score_threshold=0.0,
            max_results=100,
            base_score_per_keyword=10.0
        )

    def test_single_keyword_match(self):
        """Should match single keyword."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        keyword = Keyword.objects.create(
            value='construction',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword,
            weight=1.0
        )

        results = self.rule_engine.evaluate(
            'Building Construction Project',
            [subscription]
        )
        assert len(results) == 1
        assert results[0].is_match is True
        assert results[0].score > 0

    def test_no_match(self):
        """Should return no match when keyword not found."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        keyword = Keyword.objects.create(
            value='xyz',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword
        )

        results = self.rule_engine.evaluate(
            'Building Construction Project',
            [subscription]
        )
        assert len(results) == 0

    def test_required_keyword_logic(self):
        """Should require all required keywords."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )

        # Add required keyword
        req_keyword = Keyword.objects.create(
            value='construction',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=req_keyword,
            is_required=True
        )

        # Add optional keyword that won't match
        opt_keyword = Keyword.objects.create(
            value='xyz',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=opt_keyword,
            is_required=False
        )

        # Should not match because optional keyword doesn't match
        # but required does
        results = self.rule_engine.evaluate(
            'Construction Project',
            [subscription]
        )
        assert len(results) == 1
        assert results[0].is_match is True

    def test_multiple_keywords_bonus(self):
        """Should give bonus for multiple keyword matches."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )

        keyword1 = Keyword.objects.create(
            value='construction',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword1,
            weight=1.0
        )

        keyword2 = Keyword.objects.create(
            value='building',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword2,
            weight=1.0
        )

        results = self.rule_engine.evaluate(
            'Construction Building Project',
            [subscription]
        )
        assert len(results) == 1
        # Score should be higher with bonus
        assert results[0].score > 20.0

    def test_weighted_scoring(self):
        """Should apply keyword weights to scoring."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )

        # High weight keyword
        keyword = Keyword.objects.create(
            value='construction',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword,
            weight=5.0  # High weight
        )

        results = self.rule_engine.evaluate(
            'Construction Project',
            [subscription]
        )
        assert len(results) == 1
        # Score should be higher due to weight
        assert results[0].score == 50.0  # 10 * 5

    def test_score_capped_at_100(self):
        """Should cap score at 100."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )

        # Very high weight
        keyword = Keyword.objects.create(
            value='construction',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword,
            weight=20.0
        )

        results = self.rule_engine.evaluate(
            'Construction Project',
            [subscription]
        )
        assert len(results) == 1
        assert results[0].score == 100.0

    def test_min_score_threshold(self):
        """Should filter by minimum score."""
        engine = RuleEngine(min_score_threshold=50.0)
        subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )

        keyword = Keyword.objects.create(
            value='construction',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword,
            weight=1.0  # Score will be 10
        )

        results = engine.evaluate('Construction Project', [subscription])
        # Should be filtered out due to low score
        assert len(results) == 0

    def test_match_result_confidence(self):
        """Should calculate match confidence."""
        result = RuleMatchResult(
            subscription_id='test-id',
            subscription_name='Test',
            user_id=1,
            is_match=True,
            score=85.0,
            matched_keywords=[{'value': 'test'}],
            match_details={'all_required_matched': True}
        )
        confidence = self.rule_engine.calculate_match_confidence(result)
        assert confidence > 0.5
        assert confidence <= 1.0


class TestMatchingService(TestCase):
    """Test MatchingService."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.matching_service = MatchingService()
        self.subscription = Subscription.objects.create(
            user=self.user,
            name='Test Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        self.keyword = Keyword.objects.create(
            value='construction',
            match_type=Keyword.MATCH_CONTAINS
        )
        SubscriptionKeyword.objects.create(
            subscription=self.subscription,
            keyword=self.keyword
        )

    def test_match_opportunity(self):
        """Should match opportunity against subscriptions."""
        opportunity = TenderNotice.objects.create(
            title='Construction Project Announcement',
            notice_id='TEST-001',
            notice_type=TenderNotice.TYPE_BIDDING,
            status=TenderNotice.STATUS_PENDING
        )

        results = self.matching_service.match_opportunity(str(opportunity.id))
        assert len(results) > 0

    def test_match_opportunity_not_found(self):
        """Should handle non-existent opportunity."""
        # Use a non-existent integer ID (TenderNotice uses AutoField, not UUID)
        results = self.matching_service.match_opportunity(
            '999999'
        )
        assert len(results) == 0

    def test_get_user_matches(self):
        """Should get matches for user."""
        opportunity = TenderNotice.objects.create(
            title='Construction Project',
            notice_id='TEST-002',
            notice_type=TenderNotice.TYPE_BIDDING,
            status=TenderNotice.STATUS_PENDING
        )

        # Create match result
        MatchResult.objects.create(
            subscription=self.subscription,
            opportunity=opportunity,
            score=75.0,
            matched_keywords=[{'value': 'construction'}],
            is_notified=False
        )

        results = self.matching_service.get_user_matches(self.user.id)
        assert len(results) > 0

    def test_get_match_statistics(self):
        """Should get match statistics."""
        opportunity = TenderNotice.objects.create(
            title='Construction Project',
            notice_id='TEST-003',
            notice_type=TenderNotice.TYPE_BIDDING,
            status=TenderNotice.STATUS_PENDING
        )

        MatchResult.objects.create(
            subscription=self.subscription,
            opportunity=opportunity,
            score=75.0,
            is_notified=True
        )

        stats = self.matching_service.get_match_statistics(str(self.subscription.id))
        assert stats['total_matches'] == 1
        assert stats['notified_count'] == 1

    def test_validate_keyword(self):
        """Should validate keywords."""
        # Valid keyword
        is_valid, error = self.matching_service.validate_keyword(
            'construction', 'contains'
        )
        assert is_valid is True
        assert error == ''

        # Empty keyword
        is_valid, error = self.matching_service.validate_keyword('', 'contains')
        assert is_valid is False

        # Invalid regex
        is_valid, error = self.matching_service.validate_keyword('[invalid(', 'regex')
        assert is_valid is False

    def test_match_against_subscription(self):
        """Should match opportunities against specific subscription."""
        opportunity = TenderNotice.objects.create(
            title='Construction Building Project',
            notice_id='TEST-004',
            notice_type=TenderNotice.TYPE_BIDDING,
            status=TenderNotice.STATUS_PENDING
        )

        results = self.matching_service.match_against_subscription(
            str(self.subscription.id),
            [str(opportunity.id)]
        )
        assert len(results) > 0


class TestMatcherTypes(TestCase):
    """Test different matcher types with real data."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_exact_match(self):
        """Test exact matching."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Exact Match Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        keyword = Keyword.objects.create(
            value='Construction Project',
            match_type=Keyword.MATCH_EXACT
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword
        )

        engine = RuleEngine()
        results = engine.evaluate('Construction Project', [subscription])
        assert len(results) == 1

        # Should not match partial
        results = engine.evaluate('Construction Projects', [subscription])
        assert len(results) == 0

    def test_regex_match(self):
        """Test regex matching."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Regex Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        keyword = Keyword.objects.create(
            value=r'\d{4}',  # Match 4 digits (year)
            match_type=Keyword.MATCH_REGEX
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword
        )

        engine = RuleEngine()
        results = engine.evaluate('Project 2024 Announcement', [subscription])
        assert len(results) == 1

        # Should match multiple years
        results = engine.evaluate('Project 2023 and 2024', [subscription])
        assert len(results) == 1

    def test_starts_with_match(self):
        """Test starts with matching."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Starts With Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        keyword = Keyword.objects.create(
            value='Construction',
            match_type=Keyword.MATCH_STARTS_WITH
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword
        )

        engine = RuleEngine()
        results = engine.evaluate('Construction Project', [subscription])
        assert len(results) == 1

        # Should not match if not at start
        results = engine.evaluate('Project Construction', [subscription])
        assert len(results) == 0

    def test_ends_with_match(self):
        """Test ends with matching."""
        subscription = Subscription.objects.create(
            user=self.user,
            name='Ends With Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        keyword = Keyword.objects.create(
            value='Project',
            match_type=Keyword.MATCH_ENDS_WITH
        )
        SubscriptionKeyword.objects.create(
            subscription=subscription,
            keyword=keyword
        )

        engine = RuleEngine()
        results = engine.evaluate('Construction Project', [subscription])
        assert len(results) == 1

        # Should not match if not at end
        results = engine.evaluate('Project Construction', [subscription])
        assert len(results) == 0
