"""
Business Analysis Tests - Phase 7 Tasks 036-041
Tests for opportunity identification, competitor analysis, and market trends
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from django.test import TestCase
from apps.tenders.models import TenderNotice
from apps.tenders.repositories import TenderRepository
from apps.analysis.business.opportunity_service import OpportunityService
from apps.analysis.business.competitor_service import CompetitorService
from apps.analysis.business.trend_service import TrendService


class TestOpportunityServiceExists:
    """Test 1: OpportunityService class exists"""

    def test_opportunity_service_class_exists(self):
        """OpportunityService class should exist"""
        from apps.analysis.business.opportunity_service import OpportunityService
        assert OpportunityService is not None

    def test_opportunity_service_has_identify_method(self):
        """OpportunityService should have identify_opportunities method"""
        from apps.analysis.business.opportunity_service import OpportunityService
        assert hasattr(OpportunityService, 'identify_opportunities')


class TestOpportunityIdentification(TestCase):
    """Test 2: Business opportunity identification"""

    def setUp(self):
        self.repo = TenderRepository()
        self.service = OpportunityService()

        # Create test data
        self.tender1 = self.repo.create({
            'title': '某市人民医院信息化建设项目',
            'description': '医院信息系统升级，预算充足',
            'budget_amount': Decimal('5000000.00'),
            'region_code': '110000',
            'industry_code': 'F06',
            'notice_type': TenderNotice.TYPE_BIDDING,
            'publish_date': datetime.now()
        })

        self.tender2 = self.repo.create({
            'title': '某县政府办公设备采购',
            'description': '普通办公设备',
            'budget_amount': Decimal('50000.00'),
            'region_code': '130000',
            'industry_code': 'I65',
            'notice_type': TenderNotice.TYPE_BIDDING,
            'publish_date': datetime.now()
        })

    def test_identify_high_value_opportunities(self):
        """Should identify high-value opportunities"""
        opportunities = self.service.identify_opportunities(
            min_budget=1000000
        )

        assert len(opportunities) == 1
        assert opportunities[0]['title'] == '某市人民医院信息化建设项目'

    def test_identify_by_industry(self):
        """Should identify opportunities by industry"""
        opportunities = self.service.identify_opportunities(
            industries=['F06']
        )

        assert len(opportunities) == 1
        assert opportunities[0]['industry_code'] == 'F06'

    def test_opportunity_has_score(self):
        """Opportunities should have attractiveness score"""
        opportunities = self.service.identify_opportunities()

        for opp in opportunities:
            assert 'attractiveness_score' in opp
            assert 0 <= opp['attractiveness_score'] <= 100

    def test_opportunity_has_recommendation(self):
        """Opportunities should have recommendation level"""
        opportunities = self.service.identify_opportunities()

        for opp in opportunities:
            assert 'recommendation' in opp
            assert opp['recommendation'] in ['high', 'medium', 'low']


class TestCompetitorServiceExists:
    """Test 3: CompetitorService class exists"""

    def test_competitor_service_class_exists(self):
        """CompetitorService class should exist"""
        from apps.analysis.business.competitor_service import CompetitorService
        assert CompetitorService is not None

    def test_competitor_service_has_analyze_method(self):
        """CompetitorService should have analyze method"""
        from apps.analysis.business.competitor_service import CompetitorService
        assert hasattr(CompetitorService, 'analyze_competitors')


class TestCompetitorAnalysis(TestCase):
    """Test 4: Competitor analysis"""

    def setUp(self):
        self.repo = TenderRepository()
        self.service = CompetitorService()

        # Create test data - competitor wins
        for i in range(5):
            self.repo.create({
                'title': f'某项目中标公告-{i}',
                'winner': '中国移动通信集团有限公司',
                'budget_amount': Decimal('1000000.00'),
                'notice_type': TenderNotice.TYPE_WIN,
                'publish_date': datetime.now() - timedelta(days=i)
            })

        # Another competitor
        for i in range(3):
            self.repo.create({
                'title': f'另一项目中标-{i}',
                'winner': '华为技术有限公司',
                'budget_amount': Decimal('800000.00'),
                'notice_type': TenderNotice.TYPE_WIN,
                'publish_date': datetime.now() - timedelta(days=i)
            })

        # Some bidding notices without winner
        for i in range(3):
            self.repo.create({
                'title': f'招标项目-{i}',
                'winner': '',  # Empty string for bidding notices
                'budget_amount': Decimal('500000.00'),
                'notice_type': TenderNotice.TYPE_BIDDING,
                'publish_date': datetime.now() - timedelta(days=i)
            })

    def test_analyze_competitor_win_count(self):
        """Should analyze competitor win count"""
        analysis = self.service.analyze_competitors(
            competitor_name='中国移动通信集团有限公司'
        )

        assert analysis['total_wins'] == 5

    def test_analyze_competitor_win_amount(self):
        """Should analyze competitor total win amount"""
        analysis = self.service.analyze_competitors(
            competitor_name='中国移动通信集团有限公司'
        )

        assert analysis['total_amount'] == Decimal('5000000.00')

    def test_rank_competitors(self):
        """Should rank competitors by win count"""
        rankings = self.service.rank_competitors()

        assert len(rankings) >= 2
        #中国移动 should be ranked first (5 wins vs 3)
        assert rankings[0]['win_count'] >= rankings[1]['win_count']

    def test_competitor_trend_analysis(self):
        """Should analyze competitor trend over time"""
        analysis = self.service.analyze_trend(
            competitor_name='中国移动通信集团有限公司',
            months=3
        )

        assert 'monthly_wins' in analysis
        assert len(analysis['monthly_wins']) <= 3


class TestTrendServiceExists:
    """Test 5: TrendService class exists"""

    def test_trend_service_class_exists(self):
        """TrendService class should exist"""
        from apps.analysis.business.trend_service import TrendService
        assert TrendService is not None

    def test_trend_service_has_analyze_method(self):
        """TrendService should have analyze_market_trends method"""
        from apps.analysis.business.trend_service import TrendService
        assert hasattr(TrendService, 'analyze_market_trends')


class TestMarketTrendAnalysis(TestCase):
    """Test 6: Market trend analysis"""

    def setUp(self):
        self.repo = TenderRepository()
        self.service = TrendService()

        # Create test data over time
        base_date = datetime.now() - timedelta(days=90)

        for i in range(12):
            self.repo.create({
                'title': f'趋势测试项目-{i}',
                'budget_amount': Decimal('100000.00') + (i * 10000),
                'industry_code': 'F06' if i % 2 == 0 else 'I65',
                'region_code': '110000',
                'notice_type': TenderNotice.TYPE_BIDDING,
                'publish_date': base_date + timedelta(days=i*7)
            })

    def test_analyze_budget_trend(self):
        """Should analyze budget trend over time"""
        trends = self.service.analyze_market_trends(
            months=3
        )

        assert 'budget_trend' in trends
        assert len(trends['budget_trend']) > 0

    def test_analyze_volume_trend(self):
        """Should analyze tender volume trend"""
        trends = self.service.analyze_market_trends(
            months=3
        )

        assert 'volume_trend' in trends
        assert len(trends['volume_trend']) > 0

    def test_analyze_by_industry(self):
        """Should analyze trends by industry"""
        trends = self.service.analyze_market_trends(
            months=3,
            group_by='industry'
        )

        assert 'industry_breakdown' in trends

    def test_analyze_by_region(self):
        """Should analyze trends by region"""
        trends = self.service.analyze_market_trends(
            months=3,
            group_by='region'
        )

        assert 'region_breakdown' in trends

    def test_trend_has_growth_rate(self):
        """Trends should include growth rate"""
        trends = self.service.analyze_market_trends(months=3)

        if trends['budget_trend']:
            assert 'growth_rate' in trends['budget_trend'][0]


class TestBusinessIntelligence(TestCase):
    """Test 7: Business intelligence integration"""

    def setUp(self):
        self.repo = TenderRepository()
        self.opp_service = OpportunityService()
        self.comp_service = CompetitorService()
        self.trend_service = TrendService()

        # Create comprehensive test data
        for i in range(10):
            self.repo.create({
                'title': f'综合测试项目-{i}',
                'description': '测试描述',
                'budget_amount': Decimal('500000.00'),
                'winner': '某中标公司' if i % 2 == 0 else '',
                'industry_code': 'F06',
                'region_code': '110000',
                'notice_type': TenderNotice.TYPE_WIN if i % 2 == 0 else TenderNotice.TYPE_BIDDING,
                'publish_date': datetime.now() - timedelta(days=i*3)
            })

    def test_integrated_analysis(self):
        """Should provide integrated business analysis"""
        from apps.analysis.business.business_intelligence import BusinessIntelligence

        bi = BusinessIntelligence()
        report = bi.generate_report()

        assert 'opportunities' in report
        assert 'competitors' in report
        assert 'trends' in report

    def test_report_has_recommendations(self):
        """Report should have actionable recommendations"""
        from apps.analysis.business.business_intelligence import BusinessIntelligence

        bi = BusinessIntelligence()
        report = bi.generate_report()

        assert 'recommendations' in report
        assert len(report['recommendations']) > 0


class TestOpportunityScoring(TestCase):
    """Test 8: Opportunity scoring algorithm"""

    def setUp(self):
        self.service = OpportunityService()

    def test_score_considers_budget(self):
        """Score should consider budget amount"""
        high_budget = {'budget_amount': Decimal('10000000'), 'competition_level': 'medium'}
        low_budget = {'budget_amount': Decimal('100000'), 'competition_level': 'medium'}

        high_score = self.service._calculate_attractiveness(high_budget)
        low_score = self.service._calculate_attractiveness(low_budget)

        assert high_score > low_score

    def test_score_considers_competition(self):
        """Score should consider competition level"""
        low_comp = {'budget_amount': Decimal('1000000'), 'competition_level': 'low'}
        high_comp = {'budget_amount': Decimal('1000000'), 'competition_level': 'high'}

        low_score = self.service._calculate_attractiveness(low_comp)
        high_score = self.service._calculate_attractiveness(high_comp)

        assert low_score > high_score


class TestCompetitorBenchmarking(TestCase):
    """Test 9: Competitor benchmarking"""

    def setUp(self):
        self.service = CompetitorService()
        self.repo = TenderRepository()

        # Create benchmark data
        for i in range(10):
            self.repo.create({
                'title': f'基准测试项目-{i}',
                'winner': '目标公司',
                'budget_amount': Decimal('500000.00'),
                'notice_type': TenderNotice.TYPE_WIN,
                'publish_date': datetime.now() - timedelta(days=i*5)
            })

    def test_benchmark_against_market(self):
        """Should benchmark competitor against market average"""
        benchmark = self.service.benchmark_against_market(
            competitor_name='目标公司'
        )

        assert 'market_share_by_count' in benchmark
        assert 'avg_project_size' in benchmark
        assert 'performance_vs_market' in benchmark


class TestTrendPrediction(TestCase):
    """Test 10: Trend prediction"""

    def setUp(self):
        self.service = TrendService()
        self.repo = TenderRepository()

        # Create historical data with upward trend
        for i in range(12):
            self.repo.create({
                'title': f'预测测试-{i}',
                'budget_amount': Decimal('100000') + (i * 50000),
                'notice_type': TenderNotice.TYPE_BIDDING,
                'publish_date': datetime.now() - timedelta(days=30*i)
            })

    def test_predict_future_trend(self):
        """Should predict future market trends"""
        prediction = self.service.predict_trend(months_ahead=3)

        assert 'predicted_budget' in prediction
        assert 'predicted_volume' in prediction
        assert 'confidence' in prediction

    def test_prediction_confidence_range(self):
        """Prediction should have confidence between 0-1"""
        prediction = self.service.predict_trend(months_ahead=3)

        assert 0 <= prediction['confidence'] <= 1


class TestExportAndReporting(TestCase):
    """Test 11: Export and reporting"""

    def setUp(self):
        self.repo = TenderRepository()
        self.service = OpportunityService()

    def test_export_opportunities_to_json(self):
        """Should export opportunities to JSON"""
        opportunities = self.service.identify_opportunities()
        export = self.service.export_to_json(opportunities)

        assert isinstance(export, str)
        assert 'opportunities' in export or len(opportunities) == 0

    def test_export_opportunities_to_csv(self):
        """Should export opportunities to CSV"""
        opportunities = self.service.identify_opportunities()
        export = self.service.export_to_csv(opportunities)

        assert isinstance(export, str)
        if opportunities:
            assert ',' in export or 'title' in export


class TestPerformance(TestCase):
    """Test 12: Performance requirements"""

    def setUp(self):
        self.repo = TenderRepository()
        self.service = OpportunityService()

        # Create 1000 tenders for performance testing
        for i in range(1000):
            self.repo.create({
                'title': f'性能测试项目-{i}',
                'budget_amount': Decimal('100000'),
                'notice_type': TenderNotice.TYPE_BIDDING,
                'publish_date': datetime.now() - timedelta(days=i)
            })

    def test_opportunity_analysis_under_2s(self):
        """Opportunity analysis should complete in under 2 seconds"""
        import time

        start = time.time()
        self.service.identify_opportunities()
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Analysis took {elapsed}s, should be under 2s"

