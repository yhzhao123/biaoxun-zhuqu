"""
Opportunity Service - Phase 7 Tasks 036-037
Business opportunity identification and scoring
"""

import json
import csv
import io
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Avg, Sum, Count, Q

from apps.tenders.models import TenderNotice


class OpportunityService:
    """
    Service for identifying and scoring business opportunities.

    Features:
    - Identifies high-value opportunities
    - Scores opportunities by attractiveness
    - Filters by industry, region, budget
    - Provides recommendations
    """

    def __init__(self):
        """Initialize opportunity service."""
        self.model = TenderNotice

    def identify_opportunities(
        self,
        min_budget: Optional[float] = None,
        industries: Optional[List[str]] = None,
        regions: Optional[List[str]] = None,
        days_back: int = 30,
        limit: int = 50
    ) -> List[Dict]:
        """
        Identify business opportunities from tender notices.

        Args:
            min_budget: Minimum budget amount
            industries: List of industry codes
            regions: List of region codes
            days_back: Number of days to look back
            limit: Maximum number of results

        Returns:
            List of opportunity dictionaries with scores
        """
        # Build base query for active bidding notices
        queryset = self.model.objects.filter(
            notice_type=TenderNotice.TYPE_BIDDING,
            status__in=[TenderNotice.STATUS_PENDING, TenderNotice.STATUS_ACTIVE]
        )

        # Apply date filter
        date_from = datetime.now() - timedelta(days=days_back)
        queryset = queryset.filter(publish_date__gte=date_from)

        # Apply budget filter
        if min_budget:
            queryset = queryset.filter(budget_amount__gte=min_budget)

        # Apply industry filter
        if industries:
            queryset = queryset.filter(industry_code__in=industries)

        # Apply region filter
        if regions:
            queryset = queryset.filter(region_code__in=regions)

        # Order by budget (highest first)
        queryset = queryset.order_by('-budget_amount')[:limit]

        # Score and convert to opportunities
        opportunities = []
        for notice in queryset:
            opportunity = self._notice_to_opportunity(notice)
            opportunity['attractiveness_score'] = self._calculate_attractiveness(notice)
            opportunity['recommendation'] = self._get_recommendation_level(
                opportunity['attractiveness_score']
            )
            opportunities.append(opportunity)

        # Sort by attractiveness score
        opportunities.sort(key=lambda x: x['attractiveness_score'], reverse=True)

        return opportunities

    def _notice_to_opportunity(self, notice: TenderNotice) -> Dict:
        """Convert tender notice to opportunity dictionary."""
        return {
            'id': notice.id,
            'notice_id': notice.notice_id,
            'title': notice.title,
            'description': notice.description or '',
            'budget_amount': float(notice.budget_amount) if notice.budget_amount else 0,
            'currency': notice.currency,
            'region_code': notice.region_code,
            'region_name': notice.region_name,
            'industry_code': notice.industry_code,
            'industry_name': notice.industry_name,
            'publish_date': notice.publish_date.isoformat() if notice.publish_date else None,
            'deadline_date': notice.deadline_date.isoformat() if notice.deadline_date else None,
            'source_url': notice.source_url,
            'days_until_deadline': self._calculate_days_until_deadline(notice.deadline_date),
        }

    def _calculate_attractiveness(self, notice) -> float:
        """
        Calculate attractiveness score for an opportunity.

        Factors:
        - Budget amount (40%)
        - Time to deadline (20%)
        - Industry attractiveness (20%)
        - Competition level estimate (20%)

        Args:
            notice: TenderNotice object or dict with opportunity data

        Returns:
            Score between 0-100
        """
        # Handle both TenderNotice objects and dicts
        if isinstance(notice, dict):
            budget_amount = notice.get('budget_amount')
            industry_code = notice.get('industry_code')
            deadline_date = notice.get('deadline_date')
            competition_level = notice.get('competition_level')
        else:
            budget_amount = notice.budget_amount
            industry_code = notice.industry_code
            deadline_date = notice.deadline_date
            competition_level = None

        scores = []

        # Budget score (40% weight) - logarithmic scale
        if budget_amount:
            budget_score = min(100, float(budget_amount) / 1000000 * 20)
        else:
            budget_score = 0
        scores.append(budget_score * 0.4)

        # Deadline score (20% weight) - more time is better
        days_until = self._calculate_days_until_deadline(deadline_date)
        if days_until is None:
            deadline_score = 50  # Unknown deadline - neutral
        elif days_until < 0:
            deadline_score = 0  # Already expired
        elif days_until < 7:
            deadline_score = 30  # Very urgent
        elif days_until < 30:
            deadline_score = 70  # Moderate time
        else:
            deadline_score = 100  # Plenty of time
        scores.append(deadline_score * 0.2)

        # Industry score (20% weight) - based on industry attractiveness
        industry_scores = {
            'F06': 90,  # Healthcare - high budget
            'I65': 85,  # IT - growing market
            'E47': 80,  # Construction - stable
            'D35': 75,  # Energy - growing
            'G53': 70,  # Transportation
            'P83': 65,  # Education
            'J66': 60,  # Finance
            'C17': 55,  # Manufacturing
            'A01': 50,  # Agriculture
            'F51': 45,  # Commerce
        }
        industry_score = industry_scores.get(industry_code, 50)
        scores.append(industry_score * 0.2)

        # Competition estimate (20% weight) - inverse of project size
        if competition_level:
            # Use provided competition level
            competition_scores = {'low': 90, 'medium': 60, 'high': 30}
            competition_score = competition_scores.get(competition_level, 50)
        elif budget_amount:
            if budget_amount > 10000000:  # > 10M
                competition_score = 30  # High competition
            elif budget_amount > 5000000:  # > 5M
                competition_score = 50
            elif budget_amount > 1000000:  # > 1M
                competition_score = 70
            else:
                competition_score = 90  # Lower competition
        else:
            competition_score = 50
        scores.append(competition_score * 0.2)

        return round(sum(scores), 2)

    def _get_recommendation_level(self, score: float) -> str:
        """Get recommendation level based on score."""
        if score >= 70:
            return 'high'
        elif score >= 50:
            return 'medium'
        return 'low'

    def _calculate_days_until_deadline(self, deadline_date) -> Optional[int]:
        """Calculate days until deadline."""
        if not deadline_date:
            return None

        if isinstance(deadline_date, datetime):
            deadline = deadline_date.date()
        else:
            deadline = deadline_date

        today = datetime.now().date()
        return (deadline - today).days

    def get_opportunity_details(self, opportunity_id: int) -> Optional[Dict]:
        """Get detailed information about a specific opportunity."""
        try:
            notice = self.model.objects.get(id=opportunity_id)
            opportunity = self._notice_to_opportunity(notice)
            opportunity['attractiveness_score'] = self._calculate_attractiveness(notice)
            opportunity['recommendation'] = self._get_recommendation_level(
                opportunity['attractiveness_score']
            )

            # Add market context
            opportunity['market_context'] = self._get_market_context(notice)

            return opportunity
        except self.model.DoesNotExist:
            return None

    def _get_market_context(self, notice: TenderNotice) -> Dict:
        """Get market context for an opportunity."""
        context = {}

        # Average budget in same industry
        industry_avg = self.model.objects.filter(
            industry_code=notice.industry_code,
            budget_amount__isnull=False
        ).aggregate(avg_budget=Avg('budget_amount'))

        context['industry_avg_budget'] = float(industry_avg['avg_budget'] or 0)

        if notice.budget_amount:
            context['budget_vs_industry_avg'] = round(
                float(notice.budget_amount) / (industry_avg['avg_budget'] or 1), 2
            )

        # Number of similar projects in last 90 days
        recent_count = self.model.objects.filter(
            industry_code=notice.industry_code,
            publish_date__gte=datetime.now() - timedelta(days=90)
        ).count()

        context['similar_projects_90d'] = recent_count

        return context

    def export_to_json(self, opportunities: List[Dict]) -> str:
        """Export opportunities to JSON format."""
        return json.dumps({
            'export_date': datetime.now().isoformat(),
            'opportunities': opportunities
        }, ensure_ascii=False, indent=2)

    def export_to_csv(self, opportunities: List[Dict]) -> str:
        """Export opportunities to CSV format."""
        if not opportunities:
            return ''

        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        headers = [
            'ID', 'Title', 'Budget', 'Currency', 'Region',
            'Industry', 'Publish Date', 'Deadline', 'Score', 'Recommendation'
        ]
        writer.writerow(headers)

        # Write data
        for opp in opportunities:
            writer.writerow([
                opp.get('id', ''),
                opp.get('title', ''),
                opp.get('budget_amount', ''),
                opp.get('currency', ''),
                opp.get('region_name', ''),
                opp.get('industry_name', ''),
                opp.get('publish_date', ''),
                opp.get('deadline_date', ''),
                opp.get('attractiveness_score', ''),
                opp.get('recommendation', '')
            ])

        return output.getvalue()

