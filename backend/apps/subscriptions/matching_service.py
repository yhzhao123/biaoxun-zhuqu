"""
Matching Service - Phase 8 Tasks 044-045
High-level matching service for opportunity-to-subscription matching
"""

import logging
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.conf import settings

from apps.tenders.models import TenderNotice
from apps.tenders.repositories import TenderRepository

from .models import Subscription, MatchResult, SubscriptionKeyword
from .rule_engine import RuleEngine
from .matchers import MatcherFactory

logger = logging.getLogger(__name__)


class MatchingService:
    """
    Service for matching opportunities against subscriptions.

    Features:
    - Single opportunity matching
    - Batch matching for efficiency
    - Result persistence
    - Caching for performance
    """

    def __init__(self):
        self.rule_engine = RuleEngine(
            min_score_threshold=getattr(settings, 'MIN_MATCH_SCORE', 0.0),
            max_results=getattr(settings, 'MAX_MATCH_RESULTS', 100),
            base_score_per_keyword=getattr(settings, 'BASE_MATCH_SCORE', 10.0)
        )
        self.tender_repository = TenderRepository()

    def match_opportunity(
        self,
        opportunity_id: str,
        subscription_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Match a single opportunity against subscriptions.

        Args:
            opportunity_id: The opportunity/tender UUID
            subscription_ids: Optional list of subscription IDs to match against

        Returns:
            List of match results as dictionaries
        """
        # Get opportunity
        try:
            opportunity = TenderNotice.objects.get(id=opportunity_id)
        except TenderNotice.DoesNotExist:
            logger.error(f'Opportunity not found: {opportunity_id}')
            return []

        # Build searchable text
        opp_text = self._build_search_text(opportunity)

        # Get subscriptions to match
        subscriptions = self._get_active_subscriptions(subscription_ids)

        if not subscriptions:
            return []

        # Perform matching
        match_results = self.rule_engine.evaluate(opp_text, subscriptions)

        # Persist results
        self._persist_results(opportunity, match_results)

        return [r.to_dict() for r in match_results]

    def match_batch(
        self,
        opportunity_ids: List[str],
        subscription_ids: Optional[List[str]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Match multiple opportunities in batch.

        Args:
            opportunity_ids: List of opportunity UUIDs
            subscription_ids: Optional list of subscription IDs

        Returns:
            Dict mapping opportunity_id to list of match results
        """
        subscriptions = self._get_active_subscriptions(subscription_ids)

        if not subscriptions:
            return {}

        results = {}

        for opp_id in opportunity_ids:
            try:
                opportunity = TenderNotice.objects.get(id=opp_id)
                opp_text = self._build_search_text(opportunity)

                match_results = self.rule_engine.evaluate(opp_text, subscriptions)
                self._persist_results(opportunity, match_results)

                results[str(opp_id)] = [r.to_dict() for r in match_results]
            except TenderNotice.DoesNotExist:
                logger.warning(f'Opportunity not found: {opp_id}')
                results[str(opp_id)] = []

        return results

    def match_against_subscription(
        self,
        subscription_id: str,
        opportunity_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Match opportunities against a specific subscription.

        Args:
            subscription_id: The subscription UUID
            opportunity_ids: Optional list of opportunity IDs (default: recent 7 days)

        Returns:
            List of match results
        """
        try:
            subscription = Subscription.objects.get(
                id=subscription_id,
                is_active=True,
                deleted_at__isnull=True
            )
        except Subscription.DoesNotExist:
            logger.error(f'Subscription not found: {subscription_id}')
            return []

        # Get opportunities to match
        if opportunity_ids:
            opportunities = TenderNotice.objects.filter(id__in=opportunity_ids)
        else:
            from datetime import datetime, timedelta
            date_from = datetime.now() - timedelta(days=7)
            opportunities = TenderNotice.objects.filter(
                publish_date__gte=date_from
            )[:100]

        results = []

        for opportunity in opportunities:
            opp_text = self._build_search_text(opportunity)
            match_results = self.rule_engine.evaluate(opp_text, [subscription])

            if match_results:
                self._persist_results(opportunity, match_results)
                results.extend([r.to_dict() for r in match_results])

        return results

    def get_opportunity_matches(
        self,
        opportunity_id: str,
        min_score: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cached match results for an opportunity.

        Args:
            opportunity_id: The opportunity UUID
            min_score: Optional minimum score filter

        Returns:
            List of match results from database
        """
        queryset = MatchResult.objects.filter(
            opportunity_id=opportunity_id
        ).select_related('subscription', 'subscription__user')

        if min_score is not None:
            queryset = queryset.filter(score__gte=min_score)

        return [
            {
                'subscription_id': str(r.subscription_id),
                'subscription_name': r.subscription.name,
                'user_id': r.subscription.user_id,
                'score': r.score,
                'matched_keywords': r.matched_keywords,
                'match_details': r.match_details,
                'is_notified': r.is_notified,
                'created_at': r.created_at.isoformat(),
            }
            for r in queryset
        ]

    def get_user_matches(
        self,
        user_id: int,
        is_notified: Optional[bool] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get all match results for a user.

        Args:
            user_id: The user ID
            is_notified: Filter by notification status
            limit: Maximum results

        Returns:
            List of match results
        """
        queryset = MatchResult.objects.filter(
            subscription__user_id=user_id
        ).select_related('opportunity', 'subscription')

        if is_notified is not None:
            queryset = queryset.filter(is_notified=is_notified)

        queryset = queryset.order_by('-created_at')[:limit]

        return [
            {
                'match_id': str(r.id),
                'opportunity_id': str(r.opportunity_id),
                'opportunity_title': r.opportunity.title,
                'subscription_id': str(r.subscription_id),
                'subscription_name': r.subscription.name,
                'score': r.score,
                'matched_keywords': r.matched_keywords,
                'is_notified': r.is_notified,
                'created_at': r.created_at.isoformat(),
            }
            for r in queryset
        ]

    def get_match_statistics(self, subscription_id: str) -> Dict[str, Any]:
        """
        Get matching statistics for a subscription.

        Args:
            subscription_id: The subscription UUID

        Returns:
            Dict with statistics
        """
        from django.db.models import Avg, Count, Max, Min

        stats = MatchResult.objects.filter(
            subscription_id=subscription_id
        ).aggregate(
            total_matches=Count('id'),
            avg_score=Avg('score'),
            max_score=Max('score'),
            min_score=Min('score'),
            notified_count=Count('id', filter=models.Q(is_notified=True))
        )

        return {
            'subscription_id': subscription_id,
            'total_matches': stats['total_matches'] or 0,
            'average_score': round(stats['avg_score'] or 0, 2),
            'max_score': round(stats['max_score'] or 0, 2),
            'min_score': round(stats['min_score'] or 0, 2),
            'notified_count': stats['notified_count'] or 0,
            'unnotified_count': (stats['total_matches'] or 0) - (stats['notified_count'] or 0),
        }

    def _build_search_text(self, opportunity: TenderNotice) -> str:
        """Build searchable text from opportunity."""
        parts = [opportunity.title]
        if opportunity.description:
            parts.append(opportunity.description)
        if opportunity.purchaser_name:
            parts.append(opportunity.purchaser_name)
        if opportunity.agency_name:
            parts.append(opportunity.agency_name)
        return ' '.join(parts)

    def _get_active_subscriptions(
        self,
        subscription_ids: Optional[List[str]] = None
    ) -> List[Subscription]:
        """Get active subscriptions."""
        queryset = Subscription.objects.filter(
            is_active=True,
            deleted_at__isnull=True
        ).prefetch_related('subscription_keywords__keyword')

        if subscription_ids:
            queryset = queryset.filter(id__in=subscription_ids)

        return list(queryset)

    def _persist_results(
        self,
        opportunity: TenderNotice,
        match_results: List[Any]
    ):
        """Persist match results to database."""
        with transaction.atomic():
            for result in match_results:
                if not result.is_match:
                    continue

                # Update or create match result
                MatchResult.objects.update_or_create(
                    subscription_id=result.subscription_id,
                    opportunity=opportunity,
                    defaults={
                        'score': result.score,
                        'matched_keywords': result.matched_keywords,
                        'match_details': result.match_details,
                        'is_notified': False,
                    }
                )

    def validate_keyword(self, value: str, match_type: str) -> tuple:
        """
        Validate a keyword pattern.

        Args:
            value: The keyword value
            match_type: The match type

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not value or len(value) > 200:
            return False, '关键词不能为空且不能超过200字符'

        if match_type == 'regex':
            matcher = MatcherFactory.get_matcher('regex')
            if not matcher.validate_pattern(value):
                return False, '无效的正则表达式'

        return True, ''
