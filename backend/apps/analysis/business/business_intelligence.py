"""
Business Intelligence - Phase 7 Integration
Integrates opportunity, competitor, and trend analysis
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta

from .opportunity_service import OpportunityService
from .competitor_service import CompetitorService
from .trend_service import TrendService


class BusinessIntelligence:
    """
    Integrated business intelligence service.

    Combines opportunity identification, competitor analysis,
    and market trend analysis into comprehensive reports.
    """

    def __init__(self):
        """Initialize business intelligence service."""
        self.opportunity_service = OpportunityService()
        self.competitor_service = CompetitorService()
        self.trend_service = TrendService()

    def generate_report(
        self,
        industries: List[str] = None,
        regions: List[str] = None,
        days_back: int = 90
    ) -> Dict:
        """
        Generate comprehensive business intelligence report.

        Args:
            industries: Filter by industries
            regions: Filter by regions
            days_back: Analysis period

        Returns:
            Comprehensive report dictionary
        """
        report = {
            'report_date': datetime.now().isoformat(),
            'analysis_period_days': days_back,
            'filters': {
                'industries': industries,
                'regions': regions
            }
        }

        # Opportunity analysis
        report['opportunities'] = self._analyze_opportunities(
            industries, regions, days_back
        )

        # Competitor analysis
        report['competitors'] = self._analyze_competitors(days_back)

        # Market trends
        report['trends'] = self._analyze_trends(
            industries, regions, days_back
        )

        # Generate actionable recommendations
        report['recommendations'] = self._generate_recommendations(report)

        # Executive summary
        report['executive_summary'] = self._generate_executive_summary(report)

        return report

    def _analyze_opportunities(
        self,
        industries: List[str],
        regions: List[str],
        days_back: int
    ) -> Dict:
        """Analyze opportunities."""
        # Get high-value opportunities
        opportunities = self.opportunity_service.identify_opportunities(
            min_budget=1000000,
            industries=industries,
            regions=regions,
            days_back=days_back,
            limit=20
        )

        # Categorize by recommendation
        high_priority = [o for o in opportunities if o['recommendation'] == 'high']
        medium_priority = [o for o in opportunities if o['recommendation'] == 'medium']

        # Calculate totals
        total_opportunity_value = sum(
            o['budget_amount'] for o in opportunities if o['budget_amount']
        )

        return {
            'total_opportunities': len(opportunities),
            'high_priority_count': len(high_priority),
            'medium_priority_count': len(medium_priority),
            'total_opportunity_value': total_opportunity_value,
            'top_opportunities': opportunities[:10],
            'by_industry': self._group_by_industry(opportunities),
            'by_region': self._group_by_region(opportunities)
        }

    def _analyze_competitors(self, days_back: int) -> Dict:
        """Analyze competitors."""
        # Get top competitors
        top_competitors = self.competitor_service.rank_competitors(
            top_n=10,
            days_back=days_back,
            by_metric='total_amount'
        )

        # Calculate market concentration
        total_wins = sum(c['win_count'] for c in top_competitors)
        top_3_wins = sum(c['win_count'] for c in top_competitors[:3])

        market_concentration = (
            top_3_wins / total_wins if total_wins > 0 else 0
        )

        return {
            'top_competitors': top_competitors,
            'market_concentration': round(market_concentration, 2),
            'total_competitors_analyzed': len(top_competitors)
        }

    def _analyze_trends(
        self,
        industries: List[str],
        regions: List[str],
        days_back: int
    ) -> Dict:
        """Analyze market trends."""
        months = min(days_back // 30, 12)

        trends = self.trend_service.analyze_market_trends(
            months=months,
            industries=industries,
            regions=regions
        )

        # Get hot industries and regions
        hot_industries = self.trend_service.get_hot_industries(months=3, top_n=5)
        hot_regions = self.trend_service.get_hot_regions(months=3, top_n=5)

        # Calculate overall growth
        budget_trend = trends.get('budget_trend', [])
        if len(budget_trend) >= 2:
            first_month = budget_trend[0]['total_budget']
            last_month = budget_trend[-1]['total_budget']

            if first_month > 0:
                growth_rate = (last_month - first_month) / first_month * 100
            else:
                growth_rate = 0
        else:
            growth_rate = 0

        return {
            'budget_trend': trends.get('budget_trend', []),
            'volume_trend': trends.get('volume_trend', []),
            'hot_industries': hot_industries,
            'hot_regions': hot_regions,
            'overall_growth_rate': round(growth_rate, 2)
        }

    def _generate_recommendations(self, report: Dict) -> List[Dict]:
        """Generate actionable recommendations."""
        recommendations = []

        # Opportunity recommendations
        opportunities = report.get('opportunities', {})
        if opportunities.get('high_priority_count', 0) > 0:
            recommendations.append({
                'category': 'opportunity',
                'priority': 'high',
                'title': '高优先级机会',
                'description': f"发现 {opportunities['high_priority_count']} 个高优先级商业机会，建议立即跟进。",
                'action': 'review_high_priority_opportunities'
            })

        # Competitor recommendations
        competitors = report.get('competitors', {})
        concentration = competitors.get('market_concentration', 0)
        if concentration > 0.5:
            recommendations.append({
                'category': 'competitor',
                'priority': 'medium',
                'title': '市场集中度高',
                'description': f"前3名竞争对手占据 {concentration*100:.0f}% 市场份额，建议关注差异化策略。",
                'action': 'differentiate_from_competitors'
            })

        # Trend recommendations
        trends = report.get('trends', {})
        growth_rate = trends.get('overall_growth_rate', 0)
        if growth_rate > 20:
            recommendations.append({
                'category': 'trend',
                'priority': 'high',
                'title': '市场快速增长',
                'description': f"市场预算增长 {growth_rate:.1f}%，建议加大投入。",
                'action': 'increase_market_investment'
            })
        elif growth_rate < -10:
            recommendations.append({
                'category': 'trend',
                'priority': 'high',
                'title': '市场萎缩',
                'description': f"市场预算下降 {abs(growth_rate):.1f}%，建议谨慎投资。",
                'action': 'reduce_costs_focus_on_efficiency'
            })

        # Industry-specific recommendations
        hot_industries = trends.get('hot_industries', [])
        if hot_industries:
            top_industry = hot_industries[0]
            recommendations.append({
                'category': 'industry',
                'priority': 'medium',
                'title': f"关注 {top_industry['industry']} 行业",
                'description': f"{top_industry['industry']} 行业活跃度高，预算总额 {top_industry['total_budget']:,.0f}。",
                'action': 'focus_on_hot_industry'
            })

        return recommendations

    def _generate_executive_summary(self, report: Dict) -> Dict:
        """Generate executive summary."""
        opportunities = report.get('opportunities', {})
        competitors = report.get('competitors', {})
        trends = report.get('trends', {})

        return {
            'key_findings': [
                f"识别 {opportunities.get('total_opportunities', 0)} 个商业机会，总价值 {opportunities.get('total_opportunity_value', 0):,.0f}",
                f"分析 {competitors.get('total_competitors_analyzed', 0)} 个竞争对手",
                f"市场增长率: {trends.get('overall_growth_rate', 0):.1f}%"
            ],
            'top_recommendations': [
                r['title'] for r in report.get('recommendations', [])[:3]
            ],
            'alert_level': self._determine_alert_level(report)
        }

    def _determine_alert_level(self, report: Dict) -> str:
        """Determine alert level based on analysis."""
        recommendations = report.get('recommendations', [])

        high_priority_count = sum(
            1 for r in recommendations if r.get('priority') == 'high'
        )

        if high_priority_count >= 2:
            return 'high'
        elif high_priority_count == 1:
            return 'medium'
        return 'low'

    def _group_by_industry(self, opportunities: List[Dict]) -> Dict:
        """Group opportunities by industry."""
        by_industry = {}

        for opp in opportunities:
            industry = opp.get('industry_name') or opp.get('industry_code') or 'Unknown'
            if industry not in by_industry:
                by_industry[industry] = {
                    'count': 0,
                    'total_value': 0
                }
            by_industry[industry]['count'] += 1
            by_industry[industry]['total_value'] += opp.get('budget_amount', 0)

        return by_industry

    def _group_by_region(self, opportunities: List[Dict]) -> Dict:
        """Group opportunities by region."""
        by_region = {}

        for opp in opportunities:
            region = opp.get('region_name') or opp.get('region_code') or 'Unknown'
            if region not in by_region:
                by_region[region] = {
                    'count': 0,
                    'total_value': 0
                }
            by_region[region]['count'] += 1
            by_region[region]['total_value'] += opp.get('budget_amount', 0)

        return by_region

    def get_quick_insights(self) -> Dict:
        """Get quick insights for dashboard."""
        # Opportunities this week
        weekly_opps = self.opportunity_service.identify_opportunities(
            days_back=7,
            limit=5
        )

        # Top competitor
        top_competitors = self.competitor_service.rank_competitors(top_n=1)
        top_competitor = top_competitors[0] if top_competitors else None

        # Trend direction
        trends = self.trend_service.analyze_market_trends(months=3)
        budget_trend = trends.get('budget_trend', [])

        if len(budget_trend) >= 2:
            trend_direction = 'up' if budget_trend[-1]['total_budget'] > budget_trend[0]['total_budget'] else 'down'
        else:
            trend_direction = 'stable'

        return {
            'new_opportunities_this_week': len(weekly_opps),
            'top_opportunity_value': weekly_opps[0]['budget_amount'] if weekly_opps else 0,
            'top_competitor': top_competitor['name'] if top_competitor else None,
            'market_trend': trend_direction,
            'hot_industry': trends.get('industry_breakdown', [{}])[0].get('industry', 'N/A')
        }

