"""
Rule Engine - Phase 8 Tasks 044-045
Rule evaluation engine for keyword matching
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import Subscription, Keyword, SubscriptionKeyword
from .matchers import MatcherFactory


@dataclass
class MatchResult:
    """Result of matching an opportunity against a subscription."""
    subscription_id: str
    subscription_name: str
    user_id: int
    matched_keywords: List[Dict[str, Any]] = field(default_factory=list)
    score: float = 0.0
    match_details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    is_match: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'subscription_id': str(self.subscription_id),
            'subscription_name': self.subscription_name,
            'user_id': self.user_id,
            'matched_keywords': self.matched_keywords,
            'score': self.score,
            'match_details': self.match_details,
            'timestamp': self.timestamp.isoformat(),
            'is_match': self.is_match,
        }


class RuleEngine:
    """
    Rule engine for evaluating keyword matches.

    Supports:
    - AND logic: all required keywords must match
    - OR logic: at least one keyword must match
    - Weighted scoring based on keyword weights
    - Minimum score threshold
    """

    def __init__(
        self,
        min_score_threshold: float = 0.0,
        max_results: int = 100,
        base_score_per_keyword: float = 10.0
    ):
        self.min_score_threshold = min_score_threshold
        self.max_results = max_results
        self.base_score_per_keyword = base_score_per_keyword
        self.matcher_factory = MatcherFactory()

    def evaluate(
        self,
        opportunity_text: str,
        subscriptions: List[Subscription]
    ) -> List[MatchResult]:
        """
        Evaluate opportunity against multiple subscriptions.

        Args:
            opportunity_text: Text to match against (title + description)
            subscriptions: List of subscriptions to evaluate

        Returns:
            List of MatchResult sorted by score descending
        """
        results = []

        for subscription in subscriptions:
            if not subscription.is_active or subscription.is_deleted():
                continue

            result = self._evaluate_single(opportunity_text, subscription)
            if result.is_match and result.score >= self.min_score_threshold:
                results.append(result)

        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)

        return results[:self.max_results]

    def _evaluate_single(
        self,
        opportunity_text: str,
        subscription: Subscription
    ) -> MatchResult:
        """Evaluate opportunity against a single subscription."""
        result = MatchResult(
            subscription_id=subscription.id,
            subscription_name=subscription.name,
            user_id=subscription.user_id
        )

        # Get all keywords for this subscription
        sub_keywords = SubscriptionKeyword.objects.filter(
            subscription=subscription
        ).select_related('keyword')

        if not sub_keywords.exists():
            return result

        matched_keywords = []
        required_keywords = []
        optional_keywords = []
        total_score = 0.0

        for sub_kw in sub_keywords:
            keyword = sub_kw.keyword
            matcher = self.matcher_factory.get_matcher(keyword.match_type)

            is_match = matcher.match(
                opportunity_text,
                keyword.value,
                keyword.case_sensitive
            )

            if is_match:
                match_info = {
                    'keyword_id': str(keyword.id),
                    'value': keyword.value,
                    'match_type': keyword.match_type,
                    'weight': sub_kw.weight,
                    'is_required': sub_kw.is_required,
                }

                # Add match positions for detailed reporting
                if keyword.match_type == 'regex':
                    matcher_instance = matcher
                    if hasattr(matcher_instance, 'find_matches'):
                        matches = matcher_instance.find_matches(
                            opportunity_text,
                            keyword.value,
                            keyword.case_sensitive
                        )
                        match_info['positions'] = matches

                matched_keywords.append(match_info)

                # Calculate score
                keyword_score = self.base_score_per_keyword * sub_kw.weight
                total_score += keyword_score

                if sub_kw.is_required:
                    required_keywords.append(match_info)
                else:
                    optional_keywords.append(match_info)

        # Apply bonus for multiple matches
        if len(matched_keywords) > 1:
            bonus = min(len(matched_keywords) * 2, 20)  # Max 20 bonus
            total_score += bonus

        # Check AND logic: all required keywords must match
        all_required_matched = all(
            any(kw['value'] == sk.keyword.value for kw in matched_keywords)
            for sk in sub_keywords if sk.is_required
        )

        # Determine if it's a match
        # OR logic: at least one keyword matches
        has_optional_match = len(optional_keywords) > 0

        result.matched_keywords = matched_keywords
        result.score = min(total_score, 100.0)  # Cap at 100
        result.match_details = {
            'required_keywords_count': sub_keywords.filter(is_required=True).count(),
            'required_matched_count': len(required_keywords),
            'optional_matched_count': len(optional_keywords),
            'total_keywords_count': sub_keywords.count(),
            'all_required_matched': all_required_matched,
            'has_optional_match': has_optional_match,
        }

        # It's a match if:
        # - All required keywords matched (if any)
        # - OR at least one optional keyword matched (if no required)
        if sub_keywords.filter(is_required=True).exists():
            result.is_match = all_required_matched
        else:
            result.is_match = has_optional_match

        return result

    def evaluate_batch(
        self,
        opportunities: List[Dict[str, Any]],
        subscriptions: List[Subscription]
    ) -> Dict[str, List[MatchResult]]:
        """
        Evaluate multiple opportunities against subscriptions.

        Args:
            opportunities: List of opportunity dicts with 'id' and 'text'
            subscriptions: List of subscriptions

        Returns:
            Dict mapping opportunity_id to list of MatchResults
        """
        results = {}

        for opp in opportunities:
            opp_id = opp['id']
            opp_text = opp['text']
            results[opp_id] = self.evaluate(opp_text, subscriptions)

        return results

    def calculate_match_confidence(
        self,
        match_result: MatchResult
    ) -> float:
        """
        Calculate confidence level of a match.

        Returns a value between 0 and 1 where:
        - 1.0: High confidence (all required matched, high score)
        - 0.0: Low confidence
        """
        if not match_result.is_match:
            return 0.0

        details = match_result.match_details

        # Base confidence from score (0-100 -> 0-0.5)
        score_confidence = match_result.score / 200.0

        # Bonus for all required matched (0.3)
        required_bonus = 0.3 if details.get('all_required_matched', False) else 0.0

        # Bonus for multiple matches (0.2 max)
        match_count = len(match_result.matched_keywords)
        multi_match_bonus = min(match_count * 0.05, 0.2)

        confidence = score_confidence + required_bonus + multi_match_bonus
        return min(confidence, 1.0)
