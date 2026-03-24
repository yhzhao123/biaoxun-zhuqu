"""
Trend Service - Phase 7 Tasks 040-041
Market trend analysis and prediction
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from django.db.models import Sum, Avg, Count, Q
from collections import defaultdict
import statistics

from apps.tenders.models import TenderNotice


class TrendService:
    """
    Service for analyzing market trends.

    Features:
    - Budget trend analysis
    - Volume trend analysis
    - Industry/Region breakdowns
    - Trend prediction
    """

    def __init__(self):
        """Initialize trend service."""
        self.model = TenderNotice

    def analyze_market_trends(
        self,
        months: int = 12,
        group_by: Optional[str] = None,
        industries: Optional[List[str]] = None,
        regions: Optional[List[str]] = None
    ) -> Dict:
        """
        Analyze market trends over time.

        Args:
            months: Number of months to analyze
            group_by: Group results by 'industry', 'region', or None
            industries: Filter by industries
            regions: Filter by regions

        Returns:
            Dictionary with trend analysis
        """
        date_from = datetime.now() - timedelta(days=30 * months)

        queryset = self.model.objects.filter(
            publish_date__gte=date_from
        )

        if industries:
            queryset = queryset.filter(industry_code__in=industries)

        if regions:
            queryset = queryset.filter(region_code__in=regions)

        # Budget trend
        budget_trend = self._analyze_budget_trend(queryset, months)

        # Volume trend
        volume_trend = self._analyze_volume_trend(queryset, months)

        result = {
            'analysis_period_months': months,
            'budget_trend': budget_trend,
            'volume_trend': volume_trend,
            'analysis_date': datetime.now().isoformat()
        }

        # Add breakdowns if requested
        if group_by == 'industry':
            result['industry_breakdown'] = self._analyze_by_industry(queryset, months)
        elif group_by == 'region':
            result['region_breakdown'] = self._analyze_by_region(queryset, months)

        return result

    def _analyze_budget_trend(self, queryset, months: int) -> List[Dict]:
        """Analyze budget trend over time."""
        monthly_budgets = defaultdict(lambda: {'total': Decimal('0'), 'count': 0})

        for notice in queryset.filter(budget_amount__isnull=False):
            if notice.publish_date:
                month_key = notice.publish_date.strftime('%Y-%m')
                monthly_budgets[month_key]['total'] += notice.budget_amount
                monthly_budgets[month_key]['count'] += 1

        # Convert to list and calculate growth
        trend = []
        prev_total = None

        for month, data in sorted(monthly_budgets.items()):
            avg_budget = (data['total'] / data['count']
                         if data['count'] > 0 else Decimal('0'))

            growth_rate = None
            if prev_total is not None and prev_total > 0:
                growth_rate = round(
                    float(data['total'] - prev_total) / float(prev_total) * 100, 2
                )

            trend.append({
                'month': month,
                'total_budget': data['total'],
                'avg_budget': avg_budget,
                'project_count': data['count'],
                'growth_rate': growth_rate
            })

            prev_total = data['total']

        return trend

    def _analyze_volume_trend(self, queryset, months: int) -> List[Dict]:
        """Analyze tender volume trend over time."""
        monthly_volumes = defaultdict(lambda: {'bidding': 0, 'win': 0, 'total': 0})

        for notice in queryset:
            if notice.publish_date:
                month_key = notice.publish_date.strftime('%Y-%m')
                monthly_volumes[month_key]['total'] += 1

                if notice.notice_type == TenderNotice.TYPE_BIDDING:
                    monthly_volumes[month_key]['bidding'] += 1
                elif notice.notice_type == TenderNotice.TYPE_WIN:
                    monthly_volumes[month_key]['win'] += 1

        # Convert to list
        trend = []
        for month, data in sorted(monthly_volumes.items()):
            trend.append({
                'month': month,
                'total_tenders': data['total'],
                'bidding_count': data['bidding'],
                'win_count': data['win']
            })

        return trend

    def _analyze_by_industry(self, queryset, months: int) -> List[Dict]:
        """Analyze trends by industry."""
        industry_data = defaultdict(lambda: {
            'total_budget': Decimal('0'),
            'project_count': 0
        })

        for notice in queryset:
            industry = notice.industry_name or notice.industry_code or 'Unknown'
            industry_data[industry]['project_count'] += 1
            if notice.budget_amount:
                industry_data[industry]['total_budget'] += notice.budget_amount

        # Convert to list and sort by budget
        breakdown = [
            {
                'industry': industry,
                'total_budget': data['total_budget'],
                'project_count': data['project_count'],
                'avg_budget': (data['total_budget'] / data['project_count']
                              if data['project_count'] > 0 else Decimal('0'))
            }
            for industry, data in sorted(
                industry_data.items(),
                key=lambda x: x[1]['total_budget'],
                reverse=True
            )
        ]

        return breakdown

    def _analyze_by_region(self, queryset, months: int) -> List[Dict]:
        """Analyze trends by region."""
        region_data = defaultdict(lambda: {
            'total_budget': Decimal('0'),
            'project_count': 0
        })

        for notice in queryset:
            region = notice.region_name or notice.region_code or 'Unknown'
            region_data[region]['project_count'] += 1
            if notice.budget_amount:
                region_data[region]['total_budget'] += notice.budget_amount

        # Convert to list and sort by budget
        breakdown = [
            {
                'region': region,
                'total_budget': data['total_budget'],
                'project_count': data['project_count'],
                'avg_budget': (data['total_budget'] / data['project_count']
                              if data['project_count'] > 0 else Decimal('0'))
            }
            for region, data in sorted(
                region_data.items(),
                key=lambda x: x[1]['total_budget'],
                reverse=True
            )
        ]

        return breakdown

    def predict_trend(self, months_ahead: int = 3) -> Dict:
        """
        Predict future market trends based on historical data.

        Args:
            months_ahead: Number of months to predict

        Returns:
            Dictionary with predictions
        """
        # Get last 12 months of data
        date_from = datetime.now() - timedelta(days=365)

        queryset = self.model.objects.filter(
            publish_date__gte=date_from
        )

        # Get monthly budget totals
        monthly_totals = []
        monthly_counts = []

        for month_offset in range(12):
            month_start = date_from + timedelta(days=30*month_offset)
            month_end = month_start + timedelta(days=30)

            month_data = queryset.filter(
                publish_date__gte=month_start,
                publish_date__lt=month_end
            )

            total = month_data.aggregate(
                total=Sum('budget_amount')
            )['total'] or Decimal('0')

            count = month_data.count()

            monthly_totals.append(float(total))
            monthly_counts.append(count)

        # Simple linear regression for prediction
        predicted_budget = self._linear_predict(monthly_totals, months_ahead)
        predicted_volume = self._linear_predict(monthly_counts, months_ahead)

        # Calculate confidence based on variance
        confidence = self._calculate_prediction_confidence(monthly_totals)

        return {
            'prediction_date': datetime.now().isoformat(),
            'months_ahead': months_ahead,
            'predicted_budget': round(predicted_budget, 2),
            'predicted_volume': round(predicted_volume, 0),
            'confidence': round(confidence, 2),
            'historical_avg_budget': round(statistics.mean(monthly_totals), 2),
            'historical_avg_volume': round(statistics.mean(monthly_counts), 2)
        }

    def _linear_predict(self, values: List[float], steps_ahead: int) -> float:
        """
        Simple linear regression prediction.

        Uses least squares method to predict next value.
        """
        if len(values) < 2:
            return values[-1] if values else 0

        n = len(values)
        x_mean = sum(range(n)) / n
        y_mean = sum(values) / n

        # Calculate slope (m) and intercept (b)
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return y_mean

        slope = numerator / denominator
        intercept = y_mean - slope * x_mean

        # Predict next value
        next_x = n + steps_ahead - 1
        prediction = slope * next_x + intercept

        return max(0, prediction)  # Ensure non-negative

    def _calculate_prediction_confidence(self, values: List[float]) -> float:
        """Calculate confidence level of prediction."""
        if len(values) < 3:
            return 0.5  # Low confidence with limited data

        try:
            # Coefficient of variation
            mean_val = statistics.mean(values)
            stdev_val = statistics.stdev(values)

            if mean_val == 0:
                return 0.5

            cv = stdev_val / mean_val

            # Lower CV = higher confidence, cap at 0.95
            confidence = max(0.1, min(0.95, 1 - cv))

            return confidence
        except:
            return 0.5

    def get_hot_industries(
        self,
        months: int = 3,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Identify hot industries by growth.

        Args:
            months: Analysis period
            top_n: Number of top industries

        Returns:
            List of hot industries
        """
        trends = self.analyze_market_trends(
            months=months,
            group_by='industry'
        )

        industries = trends.get('industry_breakdown', [])

        return industries[:top_n]

    def get_hot_regions(
        self,
        months: int = 3,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Identify hot regions by activity.

        Args:
            months: Analysis period
            top_n: Number of top regions

        Returns:
            List of hot regions
        """
        trends = self.analyze_market_trends(
            months=months,
            group_by='region'
        )

        regions = trends.get('region_breakdown', [])

        return regions[:top_n]

    def compare_periods(
        self,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> Dict:
        """
        Compare two time periods.

        Returns:
            Dictionary with comparison data
        """
        # Period 1
        p1_queryset = self.model.objects.filter(
            publish_date__gte=period1_start,
            publish_date__lt=period1_end
        )

        p1_stats = {
            'total_projects': p1_queryset.count(),
            'total_budget': p1_queryset.aggregate(
                total=Sum('budget_amount')
            )['total'] or Decimal('0'),
            'avg_budget': p1_queryset.aggregate(
                avg=Avg('budget_amount')
            )['avg'] or Decimal('0')
        }

        # Period 2
        p2_queryset = self.model.objects.filter(
            publish_date__gte=period2_start,
            publish_date__lt=period2_end
        )

        p2_stats = {
            'total_projects': p2_queryset.count(),
            'total_budget': p2_queryset.aggregate(
                total=Sum('budget_amount')
            )['total'] or Decimal('0'),
            'avg_budget': p2_queryset.aggregate(
                avg=Avg('budget_amount')
            )['avg'] or Decimal('0')
        }

        # Calculate changes
        changes = {}
        for key in ['total_projects', 'total_budget', 'avg_budget']:
            if p1_stats[key] and float(p1_stats[key]) > 0:
                change = ((float(p2_stats[key]) - float(p1_stats[key]))
                         / float(p1_stats[key]) * 100)
                changes[key] = round(change, 2)
            else:
                changes[key] = None

        return {
            'period1': {
                'start': period1_start.isoformat(),
                'end': period1_end.isoformat(),
                'stats': p1_stats
            },
            'period2': {
                'start': period2_start.isoformat(),
                'end': period2_end.isoformat(),
                'stats': p2_stats
            },
            'changes_percent': changes
        }

