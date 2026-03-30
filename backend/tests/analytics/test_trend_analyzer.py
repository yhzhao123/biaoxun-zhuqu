"""
趋势分析引擎测试 - Cycle 29
测试趋势分析功能
"""
import pytest
from datetime import datetime
from typing import List, Dict, Any, Optional

from apps.analytics.trends.analyzer import (
    TrendAnalyzer,
    TenderData,
    TrendAnalysisResult,
    TimeSeriesAnalysis,
    RegionDistribution,
    IndustryHeatAnalysis,
    AmountDistribution,
    TendererActivity,
)


# ==================== Fixture ====================

@pytest.fixture
def sample_tenders() -> List[TenderData]:
    """示例招标数据"""
    return [
        TenderData(
            id="t1",
            title="软件开发项目",
            publish_date=datetime(2024, 1, 15),
            amount=500000.0,
            tenderer="中国移动北京公司",
            region="北京",
            industry="信息技术",
        ),
        TenderData(
            id="t2",
            title="网络设备采购",
            publish_date=datetime(2024, 1, 20),
            amount=1000000.0,
            tenderer="中国联通上海公司",
            region="上海",
            industry="通信",
        ),
        TenderData(
            id="t3",
            title="系统集成项目",
            publish_date=datetime(2024, 2, 10),
            amount=800000.0,
            tenderer="中国电信广东公司",
            region="广东",
            industry="信息技术",
        ),
        TenderData(
            id="t4",
            title="服务器采购",
            publish_date=datetime(2024, 2, 15),
            amount=2000000.0,
            tenderer="华为技术有限公司",
            region="深圳",
            industry="硬件",
        ),
        TenderData(
            id="t5",
            title="办公设备招标",
            publish_date=datetime(2024, 3, 1),
            amount=100000.0,
            tenderer="北京市政府",
            region="北京",
            industry="办公",
        ),
        TenderData(
            id="t6",
            title="建筑工程招标",
            publish_date=datetime(2024, 3, 10),
            amount=5000000.0,
            tenderer="中建集团",
            region="北京",
            industry="建筑",
        ),
        TenderData(
            id="t7",
            title="软件开发外包",
            publish_date=datetime(2024, 3, 15),
            amount=300000.0,
            tenderer="腾讯科技",
            region="深圳",
            industry="信息技术",
        ),
        TenderData(
            id="t8",
            title="网络安全服务",
            publish_date=datetime(2024, 4, 1),
            amount=200000.0,
            tenderer="中国工商银行",
            region="北京",
            industry="金融",
        ),
    ]


@pytest.fixture
def analyzer() -> TrendAnalyzer:
    """创建趋势分析器实例"""
    return TrendAnalyzer()


# ==================== 测试用例 ====================

# ==================== 1. 时间序列分析测试 ====================

class TestTimeSeriesAnalysis:
    """时间序列分析测试"""

    def test_monthly_tender_count(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试按月度统计招标数量"""
        result = analyzer.analyze(sample_tenders)

        # 检查1月的招标数量
        assert result.time_series.monthly_counts.get("2024-01") == 2
        assert result.time_series.monthly_counts.get("2024-02") == 2
        assert result.time_series.monthly_counts.get("2024-03") == 3
        assert result.time_series.monthly_counts.get("2024-04") == 1

    def test_quarterly_tender_count(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试按季度统计招标数量"""
        result = analyzer.analyze(sample_tenders)

        assert result.time_series.quarterly_counts.get("2024-Q1") == 7
        assert result.time_series.quarterly_counts.get("2024-Q2") == 1

    def test_yearly_tender_count(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试按年度统计招标数量"""
        result = analyzer.analyze(sample_tenders)

        assert result.time_series.yearly_counts.get("2024") == 8

    def test_monthly_amount_trend(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试按月度统计金额趋势"""
        result = analyzer.analyze(sample_tenders)

        # 1月: 50万 + 100万 = 150万
        assert result.time_series.monthly_amounts.get("2024-01") == 1500000.0
        # 2月: 80万 + 200万 = 280万
        assert result.time_series.monthly_amounts.get("2024-02") == 2800000.0
        # 3月: 10万 + 500万 + 30万 = 540万
        assert result.time_series.monthly_amounts.get("2024-03") == 5400000.0
        # 4月: 20万
        assert result.time_series.monthly_amounts.get("2024-04") == 200000.0


# ==================== 2. 地区分布分析测试 ====================

class TestRegionDistribution:
    """地区分布分析测试"""

    def test_region_tender_counts(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试各地区招标数量"""
        result = analyzer.analyze(sample_tenders)

        assert result.region_distribution.counts.get("北京") == 4
        assert result.region_distribution.counts.get("深圳") == 2
        assert result.region_distribution.counts.get("上海") == 1
        assert result.region_distribution.counts.get("广东") == 1

    def test_region_tender_ratios(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试各地区招标数量占比"""
        result = analyzer.analyze(sample_tenders)

        assert result.region_distribution.ratios.get("北京") == 0.5  # 4/8 = 50%
        assert result.region_distribution.ratios.get("深圳") == 0.25  # 2/8 = 25%

    def test_region_amount_totals(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试各地区金额统计"""
        result = analyzer.analyze(sample_tenders)

        # 北京: 50万 + 10万 + 500万 + 20万 = 580万
        assert result.region_distribution.amounts.get("北京") == 5800000.0

    def test_region_heat_ranking(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试地区热度排名"""
        result = analyzer.analyze(sample_tenders)

        # 北京应该排名第一
        assert result.region_distribution.heat_ranking[0] == "北京"


# ==================== 3. 行业热度分析测试 ====================

class TestIndustryHeatAnalysis:
    """行业热度分析测试"""

    def test_industry_tender_counts(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试各行业招标数量"""
        result = analyzer.analyze(sample_tenders)

        assert result.industry_heat.counts.get("信息技术") == 3
        assert result.industry_heat.counts.get("通信") == 1
        assert result.industry_heat.counts.get("硬件") == 1
        assert result.industry_heat.counts.get("建筑") == 1
        assert result.industry_heat.counts.get("金融") == 1

    def test_industry_amount_distribution(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试行业金额分布"""
        result = analyzer.analyze(sample_tenders)

        # 信息技术: 50万 + 80万 + 30万 = 160万
        assert result.industry_heat.amounts.get("信息技术") == 1600000.0

    def test_industry_heat_ranking(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试行业热度排名"""
        result = analyzer.analyze(sample_tenders)

        # 信息技术应该排名第一
        assert result.industry_heat.heat_ranking[0] == "信息技术"


# ==================== 4. 金额区间统计测试 ====================

class TestAmountDistribution:
    """金额区间统计测试"""

    def test_amount_range_counts(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试不同金额区间的数量分布"""
        result = analyzer.analyze(sample_tenders)

        # 样本数据金额分析：
        # 50万 -> 50-100万, 100万 -> 100-500万
        # 80万 -> 50-100万, 200万 -> 100-500万
        # 10万 -> 10-50万, 500万 -> 500-1000万
        # 30万 -> 10-50万, 20万 -> 10-50万
        assert result.amount_distribution.counts.get("0-10万", 0) == 0
        assert result.amount_distribution.counts.get("10-50万", 0) == 3  # 10万, 30万, 20万
        assert result.amount_distribution.counts.get("50-100万", 0) == 2  # 50万, 80万
        assert result.amount_distribution.counts.get("100-500万", 0) == 2  # 100万, 200万
        assert result.amount_distribution.counts.get("500-1000万", 0) == 1  # 500万
        assert result.amount_distribution.counts.get("1000万以上", 0) == 0

    def test_amount_range_ratios(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试各区间占比分析"""
        result = analyzer.analyze(sample_tenders)

        # 50-100万区间: 2个，占比 25%
        assert result.amount_distribution.ratios.get("50-100万") == 0.25


# ==================== 5. 招标人活跃度分析测试 ====================

class TestTendererActivity:
    """招标人活跃度分析测试"""

    def test_tenderer_publish_frequency(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试招标人发布频率"""
        result = analyzer.analyze(sample_tenders)

        # 每个招标人只发布一次
        assert result.tenderer_activity.publish_counts.get("中国移动北京公司") == 1
        assert result.tenderer_activity.publish_counts.get("中国联通上海公司") == 1

    def test_tenderer_frequency_ranking(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试招标人发布频率排名"""
        result = analyzer.analyze(sample_tenders)

        # 按频率排序，应该返回所有招标人
        assert len(result.tenderer_activity.frequency_ranking) > 0

    def test_active_tenderer_stats(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试活跃招标人统计"""
        result = analyzer.analyze(sample_tenders)

        # 样本中招标人数量
        assert result.tenderer_activity.total_unique_tenderers == 8


# ==================== 6. 边界情况测试 ====================

class TestEdgeCases:
    """边界情况测试"""

    def test_empty_tenders(self, analyzer: TrendAnalyzer):
        """测试空列表输入"""
        result = analyzer.analyze([])

        assert result.time_series.monthly_counts == {}
        assert result.region_distribution.counts == {}
        assert result.industry_heat.counts == {}
        assert result.amount_distribution.counts == {}
        assert result.tenderer_activity.publish_counts == {}

    def test_tenders_with_null_amount(self, analyzer: TrendAnalyzer):
        """测试金额为空的招标"""
        tenders = [
            TenderData(
                id="t1",
                title="测试招标",
                publish_date=datetime(2024, 1, 1),
                amount=None,  # 空金额
                tenderer="测试公司",
                region="北京",
                industry="软件",
            )
        ]

        result = analyzer.analyze(tenders)

        # 空金额应该被正确处理
        assert result.time_series.monthly_counts.get("2024-01") == 1
        # 空金额不计入金额统计（没有对应的键，或为0）
        assert result.time_series.monthly_amounts.get("2024-01", 0) == 0

    def test_tenders_with_null_region(self, analyzer: TrendAnalyzer):
        """测试地区为空的招标"""
        tenders = [
            TenderData(
                id="t1",
                title="测试招标",
                publish_date=datetime(2024, 1, 1),
                amount=100000.0,
                tenderer="测试公司",
                region="",  # 空地区
                industry="软件",
            )
        ]

        result = analyzer.analyze(tenders)

        # 空地区应该有默认处理
        assert result.region_distribution.counts.get("未知") == 1

    def test_tenders_with_null_industry(self, analyzer: TrendAnalyzer):
        """测试行业为空的招标"""
        tenders = [
            TenderData(
                id="t1",
                title="测试招标",
                publish_date=datetime(2024, 1, 1),
                amount=100000.0,
                tenderer="测试公司",
                region="北京",
                industry="",  # 空行业
            )
        ]

        result = analyzer.analyze(tenders)

        # 空行业应该有默认处理
        assert result.industry_heat.counts.get("未知") == 1


# ==================== 7. 综合分析测试 ====================

class TestComprehensiveAnalysis:
    """综合分析测试"""

    def test_full_analysis_result(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试完整分析结果"""
        result = analyzer.analyze(sample_tenders)

        # 验证所有字段都存在
        assert result.time_series is not None
        assert result.region_distribution is not None
        assert result.industry_heat is not None
        assert result.amount_distribution is not None
        assert result.tenderer_activity is not None

    def test_analysis_timestamp(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试分析时间戳"""
        result = analyzer.analyze(sample_tenders)

        # 验证时间戳存在且是有效日期
        assert result.analyzed_at is not None
        parsed = datetime.fromisoformat(result.analyzed_at)
        # 验证是有效的当前时间（年份应该是当前年份）
        assert parsed.year >= 2024


# ==================== 8. 功能测试 ====================

class TestAnalyzerFunctionality:
    """分析器功能测试"""

    def test_get_time_series_analysis(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试时间序列分析功能"""
        time_series = analyzer.get_time_series_analysis(sample_tenders)

        assert time_series is not None
        assert len(time_series.monthly_counts) > 0

    def test_get_region_distribution(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试地区分布分析功能"""
        region_dist = analyzer.get_region_distribution(sample_tenders)

        assert region_dist is not None
        assert len(region_dist.counts) > 0

    def test_get_industry_heat(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试行业热度分析功能"""
        industry_heat = analyzer.get_industry_heat(sample_tenders)

        assert industry_heat is not None
        assert len(industry_heat.counts) > 0

    def test_get_amount_distribution(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试金额分布分析功能"""
        amount_dist = analyzer.get_amount_distribution(sample_tenders)

        assert amount_dist is not None
        assert len(amount_dist.counts) > 0

    def test_get_tenderer_activity(self, analyzer: TrendAnalyzer, sample_tenders: List[TenderData]):
        """测试招标人活跃度分析功能"""
        tenderer_activity = analyzer.get_tenderer_activity(sample_tenders)

        assert tenderer_activity is not None
        assert tenderer_activity.total_unique_tenderers > 0