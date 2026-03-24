"""
Competitor Service - Phase 7 Tasks 038-039
Competitor analysis and benchmarking
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Avg, Count, Q
from collections import defaultdict

from apps.tenders.models import TenderNotice


class CompetitorService:
    """
    Service for analyzing competitors.

    Features:
    - Win count and amount analysis
    - Competitor rankings
    - Trend analysis over time
    - Market benchmarking
    """

    def __init__(self):
        """Initialize competitor service."""
        self.model = TenderNotice

    def analyze_competitors(
        self,
        competitor_name: Optional[str] = None,
        days_back: int = 365,
        industries: Optional[List[str]] = None,
        regions: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze competitor performance.

        Args:
            competitor_name: Name of competitor (optional)
            days_back: Number of days to analyze
            industries: Filter by industries
            regions: Filter by regions

        Returns:
            Dictionary with competitor analysis
        """
        # Base query for win notices
        queryset = self.model.objects.filter(
            notice_type=TenderNotice.TYPE_WIN,
            winner__isnull=False
        )

        # Apply date filter
        date_from = datetime.now() - timedelta(days=days_back)
        queryset = queryset.filter(publish_date__gte=date_from)

        # Apply filters
        if competitor_name:
            queryset = queryset.filter(winner__icontains=competitor_name)

        if industries:
            queryset = queryset.filter(industry_code__in=industries)

        if regions:
            queryset = queryset.filter(region_code__in=regions)

        # Calculate metrics
        total_wins = queryset.count()
        total_amount = queryset.aggregate(
            total=Sum('budget_amount')
        )['total'] or Decimal('0')

        avg_project_size = queryset.aggregate(
            avg=Avg('budget_amount')
        )['avg'] or Decimal('0')

        # Get monthly breakdown
        monthly_data = self._get_monthly_breakdown(queryset)

        # Get industry breakdown
        industry_breakdown = self._get_industry_breakdown(queryset)

        return {
            'competitor_name': competitor_name or 'All Competitors',
            'analysis_period_days': days_back,
            'total_wins': total_wins,
            'total_amount': total_amount,
            'avg_project_size': avg_project_size,
            'monthly_breakdown': monthly_data,
            'industry_breakdown': industry_breakdown,
            'analysis_date': datetime.now().isoformat()
        }

    def rank_competitors(
        self,
        top_n: int = 10,
        days_back: int = 365,
        by_metric: str = 'win_count'
    ) -> List[Dict]:
        """
        Rank competitors by performance.

        Args:
            top_n: Number of top competitors to return
            days_back: Analysis period
            by_metric: Metric to rank by ('win_count', 'total_amount', 'avg_size')

        Returns:
            List of ranked competitors
        """
        date_from = datetime.now() - timedelta(days=days_back)

        # Get all winners in period
        queryset = self.model.objects.filter(
            notice_type=TenderNotice.TYPE_WIN,
            winner__isnull=False,
            publish_date__gte=date_from
        )

        # Aggregate by winner
        competitor_stats = defaultdict(lambda: {
            'win_count': 0,
            'total_amount': Decimal('0'),
            'projects': []
        })

        for notice in queryset.values('winner', 'budget_amount', 'id'):
            winner = notice['winner']
            competitor_stats[winner]['win_count'] += 1
            if notice['budget_amount']:
                competitor_stats[winner]['total_amount'] += notice['budget_amount']
            competitor_stats[winner]['projects'].append(notice['id'])

        # Calculate averages and convert to list
        rankings = []
        for name, stats in competitor_stats.items():
            avg_size = (stats['total_amount'] / stats['win_count']
                       if stats['win_count'] > 0 else Decimal('0'))

            rankings.append({
                'name': name,
                'win_count': stats['win_count'],
                'total_amount': stats['total_amount'],
                'avg_project_size': avg_size
            })

        # Sort by specified metric
        sort_keys = {
            'win_count': lambda x: x['win_count'],
            'total_amount': lambda x: x['total_amount'],
            'avg_size': lambda x: x['avg_project_size']
        }

        sort_key = sort_keys.get(by_metric, sort_keys['win_count'])
        rankings.sort(key=sort_key, reverse=True)

        return rankings[:top_n]

    def analyze_trend(
        self,
        competitor_name: str,
        months: int = 12
    ) -> Dict:
        """
        Analyze competitor trend over time.

        Args:
            competitor_name: Name of competitor
            months: Number of months to analyze

        Returns:
            Dictionary with trend analysis
        """
        date_from = datetime.now() - timedelta(days=30 * months)

        queryset = self.model.objects.filter(
            notice_type=TenderNotice.TYPE_WIN,
            winner__icontains=competitor_name,
            publish_date__gte=date_from
        )

        # Group by month
        monthly_data = defaultdict(lambda: {'wins': 0, 'amount': Decimal('0')})

        for notice in queryset:
            month_key = notice.publish_date.strftime('%Y-%m')
            monthly_data[month_key]['wins'] += 1
            if notice.budget_amount:
                monthly_data[month_key]['amount'] += notice.budget_amount

        # Convert to sorted list
        monthly_wins = [
            {
                'month': month,
                'wins': data['wins'],
                'amount': data['amount']
            }
            for month, data in sorted(monthly_data.items())
        ]

        # Calculate trend direction
        trend_direction = self._calculate_trend_direction(monthly_wins)

        return {
            'competitor_name': competitor_name,
            'months_analyzed': months,
            'monthly_wins': monthly_wins,
            'trend_direction': trend_direction,
            'total_wins_in_period': sum(m['wins'] for m in monthly_wins)
        }

    def benchmark_against_market(
        self,
        competitor_name: str,
        days_back: int = 365
    ) -> Dict:
        """
        Benchmark competitor against overall market.

        Args:
            competitor_name: Name of competitor
            days_back: Analysis period

        Returns:
            Dictionary with benchmarking data
        """
        date_from = datetime.now() - timedelta(days=days_back)

        # Get total market stats
        market_queryset = self.model.objects.filter(
            notice_type=TenderNotice.TYPE_WIN,
            publish_date__gte=date_from
        )

        market_total = market_queryset.count()
        market_amount = market_queryset.aggregate(
            total=Sum('budget_amount')
        )['total'] or Decimal('0')

        market_avg_size = market_queryset.aggregate(
            avg=Avg('budget_amount')
        )['avg'] or Decimal('0')

        # Get competitor stats
        competitor_queryset = market_queryset.filter(
            winner__icontains=competitor_name
        )

        competitor_wins = competitor_queryset.count()
        competitor_amount = competitor_queryset.aggregate(
            total=Sum('budget_amount')
        )['total'] or Decimal('0')

        competitor_avg_size = competitor_queryset.aggregate(
            avg=Avg('budget_amount')
        )['avg'] or Decimal('0')

        # Calculate market share
        market_share_count = (competitor_wins / market_total * 100
                             if market_total > 0 else 0)
        market_share_amount = (competitor_amount / market_amount * 100
                              if market_amount > 0 else 0)

        return {
            'competitor_name': competitor_name,
            'analysis_period_days': days_back,
            'market_share_by_count': round(market_share_count, 2),
            'market_share_by_amount': round(market_share_amount, 2),
            'total_wins': competitor_wins,
            'total_amount': competitor_amount,
            'avg_project_size': competitor_avg_size,
            'market_avg_project_size': market_avg_size,
            'performance_vs_market': {
                'avg_size_ratio': round(
                    float(competitor_avg_size) / float(market_avg_size), 2
                    if market_avg_size > 0 else 1.0
                ),
                'win_rate_vs_market': round(market_share_count, 2)
            }
        }

    def _get_monthly_breakdown(self, queryset) -> List[Dict]:
        """Get monthly breakdown of wins."""
        monthly_data = defaultdict(lambda: {'count': 0, 'amount': Decimal('0')})

        for notice in queryset:
            if notice.publish_date:
                month_key = notice.publish_date.strftime('%Y-%m')
                monthly_data[month_key]['count'] += 1
                if notice.budget_amount:
                    monthly_data[month_key]['amount'] += notice.budget_amount

        return [
            {
                'month': month,
                'wins': data['count'],
                'amount': data['amount']
            }
            for month, data in sorted(monthly_data.items())
        ]

    def _get_industry_breakdown(self, queryset) -> List[Dict]:
        """Get industry breakdown of wins."""
        industry_data = defaultdict(lambda: {'count': 0, 'amount': Decimal('0')})

        for notice in queryset:
            industry = notice.industry_name or notice.industry_code or 'Unknown'
            industry_data[industry]['count'] += 1
            if notice.budget_amount:
                industry_data[industry]['amount'] += notice.budget_amount

        # Sort by amount and convert to list
        breakdown = [
            {
                'industry': industry,
                'wins': data['count'],
                'amount': data['amount']
            }
            for industry, data in sorted(
                industry_data.items(),
                key=lambda x: x[1]['amount'],
                reverse=True
            )
        ]

        return breakdown

    def _calculate_trend_direction(self, monthly_data: List[Dict]) -> str:
        """Calculate trend direction from monthly data."""
        if len(monthly_data) < 3:
            return 'insufficient_data'

        # Compare first half to second half
        mid = len(monthly_data) // 2
        first_half_wins = sum(m['wins'] for m in monthly_data[:mid])
        second_half_wins = sum(m['wins'] for m in monthly_data[mid:])

        if second_half_wins > first_half_wins * 1.2:
            return 'increasing'
        elif second_half_wins < first_half_wins * 0.8:
            return 'decreasing'
        return 'stable'

    def get_competitor_list(
        self,
        days_back: int = 365,
        min_wins: int = 1
    ) -> List[str]:
        """Get list of all competitors."""
        date_from = datetime.now() - timedelta(days=days_back)

        competitors = self.model.objects.filter(
            notice_type=TenderNotice.TYPE_WIN,
            winner__isnull=False,
            publish_date__gte=date_from
        ).values('winner').annotate(
            win_count=Count('id')
        ).filter(win_count__gte=min_wins)

        return [c['winner'] for c in competitors]

