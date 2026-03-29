"""
TDD Cycle 28: 商机识别系统测试
"""
import pytest
from datetime import datetime, timedelta
from apps.analytics.opportunity.scorer import (
    OpportunityScorer,
    AmountScorer,
    CompetitionScorer,
    TimelineScorer,
    RelevanceScorer,
    HistoryScorer,
    TenderOpportunity,
    TenderScoreFactors,
    OpportunityScoreLevel,
    OpportunityRecommendation,
)


class TestTenderScoreFactors:
    """测试评分因子"""

    def test_factors_default_values(self):
        """测试评分因子默认值"""
        factors = TenderScoreFactors()
        assert factors.amount_score == 0.0
        assert factors.competition_score == 0.0
        assert factors.timeline_score == 0.0
        assert factors.relevance_score == 0.0
        assert factors.history_score == 0.0

    def test_factors_total_score_calculation(self):
        """测试总分计算"""
        factors = TenderScoreFactors(
            amount_score=25.0,
            competition_score=20.0,
            timeline_score=20.0,
            relevance_score=15.0,
            history_score=15.0
        )
        assert factors.total_score == 95.0


class TestTenderOpportunity:
    """测试招标商机"""

    def test_opportunity_creation(self):
        """测试商机创建"""
        opp = TenderOpportunity(
            tender_id="T001",
            title="软件开发项目",
            tenderer="中国移动"
        )
        assert opp.tender_id == "T001"
        assert opp.title == "软件开发项目"
        assert opp.tenderer == "中国移动"
        assert opp.factors is not None
        assert opp.total_score == 0.0

    def test_opportunity_with_budget(self):
        """测试带预算的商机"""
        opp = TenderOpportunity(
            tender_id="T002",
            title="硬件采购",
            tenderer="国家电网",
            budget=5000000.0
        )
        assert opp.budget == 5000000.0

    def test_opportunity_score_level_default(self):
        """测试默认评分等级"""
        opp = TenderOpportunity(tender_id="T003", title="测试", tenderer="测试")
        assert opp.score_level == OpportunityScoreLevel.LOW


class TestOpportunityScorerInitialization:
    """测试评分器初始化"""

    def test_scorer_initialization(self):
        """测试评分器可以初始化"""
        scorer = OpportunityScorer()
        assert scorer is not None
        assert scorer.amount_scorer is not None
        assert scorer.competition_scorer is not None
        assert scorer.timeline_scorer is not None
        assert scorer.relevance_scorer is not None
        assert scorer.history_scorer is not None


class TestAmountScorer:
    """测试金额评分"""

    def test_amount_scorer_returns_score(self):
        """测试金额评分返回分数"""
        scorer = AmountScorer()
        score = scorer.score(1000000.0)
        assert isinstance(score, float)
        assert 0 <= score <= 25

    def test_amount_scorer_high_amount(self):
        """测试大额评分"""
        scorer = AmountScorer()
        score = scorer.score(10000000.0)  # 1000万
        assert score >= 20  # 大额应该高分

    def test_amount_scorer_low_amount(self):
        """测试小额评分"""
        scorer = AmountScorer()
        score = scorer.score(10000.0)  # 1万
        assert score <= 10  # 小额应该低分

    def test_amount_scorer_none_amount(self):
        """测试无金额情况"""
        scorer = AmountScorer()
        score = scorer.score(None)
        assert score == 0.0


class TestCompetitionScorer:
    """测试竞争度评分"""

    def test_competition_scorer_returns_score(self):
        """测试竞争评分返回分数"""
        scorer = CompetitionScorer()
        score = scorer.score("T001", "中国移动")
        assert isinstance(score, float)
        assert 0 <= score <= 25

    def test_competition_scorer_government_tenderer(self):
        """测试政府招标人竞争度"""
        scorer = CompetitionScorer()
        score = scorer.score("T001", "某市政府")
        assert score <= 15  # 政府项目竞争激烈，分数应该较低


class TestTimelineScorer:
    """测试时间评分"""

    def test_timeline_scorer_returns_score(self):
        """测试时间评分返回分数"""
        scorer = TimelineScorer()
        deadline = datetime.now() + timedelta(days=30)
        score = scorer.score(deadline)
        assert isinstance(score, float)
        assert 0 <= score <= 20

    def test_timeline_scorer_sufficient_time(self):
        """测试时间充裕情况"""
        scorer = TimelineScorer()
        deadline = datetime.now() + timedelta(days=45)
        score = scorer.score(deadline)
        assert score >= 15  # 45天应该高分

    def test_timeline_scorer_insufficient_time(self):
        """测试时间不足情况"""
        scorer = TimelineScorer()
        deadline = datetime.now() + timedelta(days=3)
        score = scorer.score(deadline)
        assert score <= 10  # 3天应该低分

    def test_timeline_scorer_past_deadline(self):
        """测试已过期"""
        scorer = TimelineScorer()
        deadline = datetime.now() - timedelta(days=1)
        score = scorer.score(deadline)
        assert score == 0.0


class TestRelevanceScorer:
    """测试相关性评分"""

    def test_relevance_scorer_returns_score(self):
        """测试相关性评分返回分数"""
        scorer = RelevanceScorer()
        tender = TenderOpportunity(tender_id="T001", title="软件开发", tenderer="移动")
        user_profile = {"industries": ["IT", "软件"], "regions": ["北京"]}
        score = scorer.score(tender, user_profile)
        assert isinstance(score, float)
        assert 0 <= score <= 15

    def test_relevance_scorer_industry_match(self):
        """测试行业匹配"""
        scorer = RelevanceScorer()
        tender = TenderOpportunity(tender_id="T001", title="软件开发", tenderer="移动")
        user_profile = {"industries": ["软件"], "regions": ["上海"]}
        score1 = scorer.score(tender, user_profile)

        tender2 = TenderOpportunity(tender_id="T002", title="建筑工程", tenderer="建工")
        score2 = scorer.score(tender2, user_profile)

        assert score1 > score2  # 软件项目应该匹配度更高


class TestHistoryScorer:
    """测试历史评分"""

    def test_history_scorer_returns_score(self):
        """测试历史评分返回分数"""
        scorer = HistoryScorer()
        score = scorer.score("中国移动")
        assert isinstance(score, float)
        assert 0 <= score <= 15


class TestOpportunityScorerIntegration:
    """测试完整评分流程"""

    def test_score_tender_returns_scored_opportunity(self):
        """测试完整评分"""
        scorer = OpportunityScorer()
        tender = TenderOpportunity(
            tender_id="T001",
            title="软件开发项目",
            tenderer="中国移动",
            budget=5000000.0,
            deadline_date=datetime.now() + timedelta(days=30)
        )

        result = scorer.score_tender(tender)

        assert isinstance(result, TenderOpportunity)
        assert result.total_score > 0
        assert result.factors.amount_score > 0
        assert result.factors.timeline_score > 0

    def test_score_tender_calculates_level(self):
        """测试评分等级计算"""
        scorer = OpportunityScorer()
        tender = TenderOpportunity(
            tender_id="T002",
            title="大项目",
            tenderer="政府",
            budget=10000000.0,
            deadline_date=datetime.now() + timedelta(days=60)
        )

        result = scorer.score_tender(tender)

        assert result.score_level in [
            OpportunityScoreLevel.HIGH,
            OpportunityScoreLevel.MEDIUM,
            OpportunityScoreLevel.LOW
        ]

    def test_high_score_tender_gets_high_level(self):
        """测试高分为 HIGH 等级"""
        scorer = OpportunityScorer()
        tender = TenderOpportunity(
            tender_id="T003",
            title="超大项目",
            tenderer="国企",
            budget=50000000.0,  # 5000万
            deadline_date=datetime.now() + timedelta(days=90)
        )

        result = scorer.score_tender(tender)

        # 大金额 + 充足时间应该得高分
        assert result.total_score >= 50


class TestRecommendations:
    """测试推荐功能"""

    def test_get_recommendations_returns_list(self):
        """测试推荐返回列表"""
        scorer = OpportunityScorer()
        tenders = [
            TenderOpportunity(tender_id="T001", title="项目1", tenderer="A"),
            TenderOpportunity(tender_id="T002", title="项目2", tenderer="B"),
        ]

        recommendations = scorer.get_recommendations(tenders, top_n=2)

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 2

    def test_get_recommendations_sorted_by_score(self):
        """测试推荐按分数排序"""
        scorer = OpportunityScorer()

        # 创建带评分的招标
        tender1 = TenderOpportunity(tender_id="T001", title="项目1", tenderer="A")
        tender1.total_score = 90.0

        tender2 = TenderOpportunity(tender_id="T002", title="项目2", tenderer="B")
        tender2.total_score = 60.0

        tenders = [tender2, tender1]  # 乱序

        recommendations = scorer.get_recommendations(tenders, top_n=2)

        assert len(recommendations) == 2
        assert recommendations[0].score >= recommendations[1].score
