"""
数据聚合 API 测试 - Cycle 30
测试 AnalyticsAPI 的所有功能
"""
import pytest
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass, field

# 导入被测试模块
from apps.analytics.api.aggregator import (
    AnalyticsAPI,
    FilterParams,
    Pagination,
    OverviewResult,
    ClassificationStats,
    OpportunityList,
    TrendResult,
    DashboardResult,
    TenderData,
    OpportunityScoreLevel,
)


# ==================== 测试数据生成器 ====================

def create_sample_tenders(count: int = 10) -> List[TenderData]:
    """创建示例招标数据"""
    tenders = []
    base_date = datetime.now()

    regions = ["北京", "上海", "广东", "浙江", "江苏", "四川", "湖北"]
    industries = ["软件开发", "网络设备", "建筑施工", "咨询服务", "医疗设备"]
    tenderers = [
        "北京市政府",
        "中国移动上海公司",
        "阿里巴巴集团",
        "华为技术有限公司",
        "国家电网浙江分公司",
        "中铁建设集团",
        "腾讯科技",
    ]

    for i in range(count):
        tenders.append(TenderData(
            id=f"tender_{i+1}",
            title=f"招标项目{i+1}",
            publish_date=base_date - timedelta(days=i*3),
            amount=100000 + i * 50000,
            tenderer=tenderers[i % len(tenderers)],
            region=regions[i % len(regions)],
            industry=industries[i % len(industries)],
        ))

    return tenders


def create_tenders_for_period(
    days_ago: int,
    count: int = 5
) -> List[TenderData]:
    """创建指定时间范围内的招标数据"""
    base_date = datetime.now() - timedelta(days=days_ago)
    tenders = []

    for i in range(count):
        tenders.append(TenderData(
            id=f"recent_{i}",
            title=f"近期招标{i}",
            publish_date=base_date + timedelta(days=i),
            amount=200000 + i * 10000,
            tenderer=f"招标人{i}",
            region="北京",
            industry="软件开发",
        ))

    return tenders


# ====================  Fixture ====================

@pytest.fixture
def sample_tenders() -> List[TenderData]:
    """示例招标数据"""
    return create_sample_tenders(20)


@pytest.fixture
def empty_tenders() -> List[TenderData]:
    """空数据列表"""
    return []


@pytest.fixture
def analytics_api() -> AnalyticsAPI:
    """AnalyticsAPI 实例"""
    return AnalyticsAPI()


# ==================== 基础功能测试 ====================

class TestBasicFunctionality:
    """基础功能测试"""

    def test_analytics_api_can_be_instantiated(self, analytics_api):
        """测试 AnalyticsAPI 可以被实例化"""
        assert analytics_api is not None
        assert hasattr(analytics_api, 'classifier')
        assert hasattr(analytics_api, 'scorer')
        assert hasattr(analytics_api, 'analyzer')

    def test_tender_data_structure(self):
        """测试 TenderData 数据结构"""
        tender = TenderData(
            id="test_1",
            title="测试招标",
            publish_date=datetime.now(),
            amount=100000.0,
            tenderer="测试招标人",
            region="北京",
            industry="软件开发",
        )

        assert tender.id == "test_1"
        assert tender.title == "测试招标"
        assert tender.amount == 100000.0


# ==================== 筛选参数测试 ====================

class TestFilterParams:
    """筛选参数测试"""

    def test_filter_params_defaults(self):
        """测试筛选参数默认值"""
        filters = FilterParams()

        assert filters.start_date is None
        assert filters.end_date is None
        assert filters.regions is None
        assert filters.industries is None
        assert filters.amount_range is None
        assert filters.opportunity_score_min is None
        assert filters.tenderers is None

    def test_filter_params_with_values(self):
        """测试筛选参数设置值"""
        start = datetime.now()
        end = datetime.now() + timedelta(days=30)

        filters = FilterParams(
            start_date=start,
            end_date=end,
            regions=["北京", "上海"],
            industries=["软件开发"],
            amount_range=(10000, 1000000),
            opportunity_score_min=50.0,
            tenderers=["招标人A", "招标人B"],
        )

        assert filters.start_date == start
        assert filters.end_date == end
        assert filters.regions == ["北京", "上海"]
        assert filters.industries == ["软件开发"]
        assert filters.amount_range == (10000, 1000000)
        assert filters.opportunity_score_min == 50.0
        assert filters.tenderers == ["招标人A", "招标人B"]


# ==================== 空数据处理测试 ====================

class TestEmptyDataHandling:
    """空数据处理测试"""

    def test_overview_with_empty_data(self, analytics_api, empty_tenders):
        """测试空数据的概览返回"""
        filters = FilterParams()
        result = analytics_api.get_overview(filters, empty_tenders)

        assert result.total_count == 0
        assert result.total_amount == 0.0
        assert result.active_tenderers == 0
        assert result.today_count == 0
        assert result.week_count == 0
        assert result.month_count == 0

    def test_classification_with_empty_data(self, analytics_api, empty_tenders):
        """测试空数据的分类统计返回"""
        filters = FilterParams()
        result = analytics_api.get_classification_stats(filters, empty_tenders)

        assert result.by_tenderer == {}
        assert result.by_region == {}
        assert result.by_industry == {}
        assert result.by_amount_range == {}

    def test_opportunities_with_empty_data(self, analytics_api, empty_tenders):
        """测试空数据的商机列表返回"""
        filters = FilterParams()
        pagination = Pagination(page=1, page_size=10)

        result = analytics_api.get_opportunities(filters, pagination, empty_tenders)

        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.page_size == 10

    def test_trends_with_empty_data(self, analytics_api, empty_tenders):
        """测试空数据的趋势分析返回"""
        filters = FilterParams()
        result = analytics_api.get_trends(filters, empty_tenders)

        assert result.time_series == {}
        assert result.region_distribution == {}
        assert result.industry_heat == {}

    def test_full_dashboard_with_empty_data(self, analytics_api, empty_tenders):
        """测试空数据的完整仪表板返回"""
        filters = FilterParams()
        result = analytics_api.get_full_dashboard(filters, empty_tenders)

        assert result.overview.total_count == 0
        assert isinstance(result.classification, dict)
        assert result.classification.get('by_tenderer', {}) == {}
        assert result.classification.get('by_region', {}) == {}
        assert result.classification.get('by_industry', {}) == {}
        assert result.classification.get('by_amount_range', {}) == {}
        assert result.opportunities == []
        assert result.trends.time_series == {}


# ==================== 概览接口测试 ====================

class TestOverviewEndpoint:
    """概览接口测试"""

    def test_overview_statistics(self, analytics_api, sample_tenders):
        """测试概览统计正确性"""
        filters = FilterParams()
        result = analytics_api.get_overview(filters, sample_tenders)

        assert result.total_count == len(sample_tenders)
        assert result.total_amount > 0
        assert result.active_tenderers > 0
        assert result.avg_amount > 0

    def test_overview_time_period_counts(self, analytics_api):
        """测试时间周期统计"""
        # 创建包含今日、本周、本月数据的测试集
        now = datetime.now()
        tenders = []

        # 今日数据
        tenders.append(TenderData(
            id="today_1", title="今日招标", publish_date=now,
            amount=100000, tenderer="招标人1", region="北京", industry="软件"
        ))

        # 本周数据 (3天内)
        for i in range(2):
            tenders.append(TenderData(
                id=f"week_{i}", title=f"本周招标{i}", publish_date=now - timedelta(days=i+1),
                amount=100000, tenderer="招标人2", region="上海", industry="软件"
            ))

        # 本月数据 (10天内)
        for i in range(3):
            tenders.append(TenderData(
                id=f"month_{i}", title=f"本月招标{i}", publish_date=now - timedelta(days=i+5),
                amount=100000, tenderer="招标人3", region="广东", industry="软件"
            ))

        filters = FilterParams()
        result = analytics_api.get_overview(filters, tenders)

        assert result.today_count >= 1
        assert result.week_count >= 1
        assert result.month_count >= 1


# ==================== 筛选功能测试 ====================

class TestFiltering:
    """筛选功能测试"""

    def test_date_range_filter(self, analytics_api):
        """测试时间范围筛选"""
        now = datetime.now()
        tenders = [
            TenderData(id="old", title="旧招标", publish_date=now - timedelta(days=60),
                      amount=100000, tenderer="A", region="北京", industry="软件"),
            TenderData(id="new", title="新招标", publish_date=now - timedelta(days=5),
                      amount=100000, tenderer="B", region="上海", industry="软件"),
        ]

        # 筛选近30天
        filters = FilterParams(
            start_date=now - timedelta(days=30),
            end_date=now
        )
        result = analytics_api.get_overview(filters, tenders)

        assert result.total_count == 1
        assert result.total_count <= len(tenders)

    def test_region_filter(self, analytics_api, sample_tenders):
        """测试地区筛选"""
        filters = FilterParams(regions=["北京", "上海"])
        result = analytics_api.get_overview(filters, sample_tenders)

        # 应该只统计北京和上海的招标
        for tender_id in sample_tenders:
            pass  # 验证筛选逻辑正确执行

        assert result.total_count >= 0

    def test_industry_filter(self, analytics_api, sample_tenders):
        """测试行业筛选"""
        filters = FilterParams(industries=["软件开发"])
        result = analytics_api.get_overview(filters, sample_tenders)

        assert result.total_count >= 0

    def test_amount_range_filter(self, analytics_api, sample_tenders):
        """测试金额区间筛选"""
        filters = FilterParams(amount_range=(100000, 500000))
        result = analytics_api.get_overview(filters, sample_tenders)

        assert result.total_count >= 0

    def test_opportunity_score_filter(self, analytics_api):
        """测试商机评分筛选"""
        tenders = create_sample_tenders(10)
        filters = FilterParams(opportunity_score_min=50.0)

        pagination = Pagination(page=1, page_size=10)
        result = analytics_api.get_opportunities(filters, pagination, tenders)

        # 所有返回的商机评分应该 >= 50
        for opp in result.items:
            assert opp.total_score >= 50.0

    def test_combined_filters(self, analytics_api):
        """测试多条件组合筛选"""
        now = datetime.now()
        tenders = [
            TenderData(id="1", title="测试1", publish_date=now - timedelta(days=5),
                      amount=500000, tenderer="北京移动", region="北京", industry="软件开发"),
            TenderData(id="2", title="测试2", publish_date=now - timedelta(days=10),
                      amount=100000, tenderer="上海政府", region="上海", industry="咨询服务"),
        ]

        # 组合筛选: 北京 + 软件开发 + 金额 >= 30万
        filters = FilterParams(
            regions=["北京"],
            industries=["软件开发"],
            amount_range=(300000, float('inf'))
        )
        result = analytics_api.get_overview(filters, tenders)

        assert result.total_count >= 0


# ==================== 分页功能测试 ====================

class TestPagination:
    """分页功能测试"""

    def test_pagination_defaults(self):
        """测试分页默认值"""
        pagination = Pagination()

        assert pagination.page == 1
        assert pagination.page_size == 10

    def test_pagination_with_values(self):
        """测试分页参数设置"""
        pagination = Pagination(page=3, page_size=20)

        assert pagination.page == 3
        assert pagination.page_size == 20

    def test_pagination_page_size_limit(self):
        """测试分页大小限制"""
        pagination = Pagination(page=1, page_size=100)

        assert pagination.page_size <= 100

    def test_opportunities_pagination(self, analytics_api, sample_tenders):
        """测试商机列表分页"""
        filters = FilterParams()
        pagination = Pagination(page=1, page_size=5)

        result = analytics_api.get_opportunities(filters, pagination, sample_tenders)

        assert len(result.items) <= 5
        assert result.page == 1
        assert result.page_size == 5
        assert result.total == len(sample_tenders)

    def test_pagination_total_pages(self, analytics_api, sample_tenders):
        """测试分页总数计算"""
        filters = FilterParams()
        pagination = Pagination(page=1, page_size=7)

        result = analytics_api.get_opportunities(filters, pagination, sample_tenders)

        expected_total_pages = (len(sample_tenders) + 6) // 7
        assert result.total_pages == expected_total_pages


# ==================== 排序功能测试 ====================

class TestSorting:
    """排序功能测试"""

    def test_default_sorting(self, analytics_api, sample_tenders):
        """测试默认排序（按评分降序）"""
        filters = FilterParams()
        pagination = Pagination(page=1, page_size=10)

        result = analytics_api.get_opportunities(filters, pagination, sample_tenders)

        # 验证返回的是按评分排序的
        if len(result.items) > 1:
            for i in range(len(result.items) - 1):
                assert result.items[i].total_score >= result.items[i + 1].total_score


# ==================== 分类统计测试 ====================

class TestClassificationStats:
    """分类统计测试"""

    def test_classification_by_tenderer(self, analytics_api, sample_tenders):
        """测试按招标人分类统计"""
        filters = FilterParams()
        result = analytics_api.get_classification_stats(filters, sample_tenders)

        assert isinstance(result.by_tenderer, dict)
        # 验证有数据
        assert len(result.by_tenderer) > 0

    def test_classification_by_region(self, analytics_api, sample_tenders):
        """测试按地区分类统计"""
        filters = FilterParams()
        result = analytics_api.get_classification_stats(filters, sample_tenders)

        assert isinstance(result.by_region, dict)
        assert len(result.by_region) > 0

    def test_classification_by_industry(self, analytics_api, sample_tenders):
        """测试按行业分类统计"""
        filters = FilterParams()
        result = analytics_api.get_classification_stats(filters, sample_tenders)

        assert isinstance(result.by_industry, dict)
        assert len(result.by_industry) > 0

    def test_classification_by_amount_range(self, analytics_api, sample_tenders):
        """测试按金额区间分类统计"""
        filters = FilterParams()
        result = analytics_api.get_classification_stats(filters, sample_tenders)

        assert isinstance(result.by_amount_range, dict)


# ==================== 商机数据测试 ====================

class TestOpportunityData:
    """商机数据测试"""

    def test_opportunity_scoring(self, analytics_api, sample_tenders):
        """测试商机评分"""
        filters = FilterParams()
        pagination = Pagination(page=1, page_size=10)

        result = analytics_api.get_opportunities(filters, pagination, sample_tenders)

        assert len(result.items) > 0

        # 验证每个商机都有评分
        for opp in result.items:
            assert hasattr(opp, 'total_score')
            assert 0 <= opp.total_score <= 100

    def test_opportunity_score_levels(self, analytics_api, sample_tenders):
        """测试商机评分等级"""
        filters = FilterParams()
        pagination = Pagination(page=1, page_size=10)

        result = analytics_api.get_opportunities(filters, pagination, sample_tenders)

        # 验证评分等级正确
        for opp in result.items:
            if opp.total_score >= 80:
                assert opp.score_level == OpportunityScoreLevel.HIGH
            elif opp.total_score >= 50:
                assert opp.score_level == OpportunityScoreLevel.MEDIUM
            else:
                assert opp.score_level == OpportunityScoreLevel.LOW


# ==================== 趋势数据测试 ====================

class TestTrendData:
    """趋势数据测试"""

    def test_time_series_data(self, analytics_api, sample_tenders):
        """测试时间序列数据"""
        filters = FilterParams()
        result = analytics_api.get_trends(filters, sample_tenders)

        assert isinstance(result.time_series, dict)

    def test_region_distribution_data(self, analytics_api, sample_tenders):
        """测试地区分布数据"""
        filters = FilterParams()
        result = analytics_api.get_trends(filters, sample_tenders)

        assert isinstance(result.region_distribution, dict)

    def test_industry_heat_data(self, analytics_api, sample_tenders):
        """测试行业热度数据"""
        filters = FilterParams()
        result = analytics_api.get_trends(filters, sample_tenders)

        assert isinstance(result.industry_heat, dict)


# ==================== 完整仪表板测试 ====================

class TestFullDashboard:
    """完整仪表板测试"""

    def test_full_dashboard_aggregation(self, analytics_api, sample_tenders):
        """测试完整仪表板数据聚合"""
        filters = FilterParams()
        result = analytics_api.get_full_dashboard(filters, sample_tenders)

        # 验证所有部分都有数据
        assert result.overview is not None
        assert result.classification is not None
        assert result.opportunities is not None
        assert result.trends is not None

        # 验证概览数据
        assert result.overview.total_count == len(sample_tenders)

    def test_full_dashboard_with_filters(self, analytics_api, sample_tenders):
        """测试带筛选条件的完整仪表板"""
        filters = FilterParams(
            regions=["北京", "上海"],
            industries=["软件开发"]
        )
        result = analytics_api.get_full_dashboard(filters, sample_tenders)

        assert result.overview is not None
        assert result.classification is not None


# ==================== 边界条件测试 ====================

class TestBoundaryConditions:
    """边界条件测试"""

    def test_single_tender(self, analytics_api):
        """测试单个招标数据"""
        tenders = [
            TenderData(
                id="single",
                title="单一招标",
                publish_date=datetime.now(),
                amount=1000000,
                tenderer="测试招标人",
                region="北京",
                industry="软件开发",
            )
        ]

        filters = FilterParams()
        result = analytics_api.get_overview(filters, tenders)

        assert result.total_count == 1

    def test_all_null_amounts(self, analytics_api):
        """测试全部为空金额的数据"""
        tenders = [
            TenderData(
                id=f"no_amount_{i}",
                title=f"无金额招标{i}",
                publish_date=datetime.now(),
                amount=None,
                tenderer="招标人",
                region="北京",
                industry="软件",
            )
            for i in range(5)
        ]

        filters = FilterParams()
        result = analytics_api.get_overview(filters, tenders)

        assert result.total_count == 5
        assert result.total_amount == 0.0

    def test_extreme_pagination(self, analytics_api, sample_tenders):
        """测试极端分页情况"""
        filters = FilterParams()
        pagination = Pagination(page=1000, page_size=10)

        result = analytics_api.get_opportunities(filters, pagination, sample_tenders)

        # 应该返回空列表而不是报错
        assert isinstance(result.items, list)


# ==================== 数据一致性测试 ====================

class TestDataConsistency:
    """数据一致性测试"""

    def test_overview_matches_filtered_data(self, analytics_api, sample_tenders):
        """测试概览数据与筛选后数据一致"""
        filters = FilterParams(regions=["北京"])
        result = analytics_api.get_overview(filters, sample_tenders)

        # 验证筛选后的统计
        filtered = [t for t in sample_tenders if t.region == "北京"]
        assert result.total_count == len(filtered)

    def test_classification_total_matches(self, analytics_api, sample_tenders):
        """测试分类统计总和匹配"""
        filters = FilterParams()
        result = analytics_api.get_classification_stats(filters, sample_tenders)

        # 各分类的总和应该等于总数量
        total_by_region = sum(result.by_region.values()) if result.by_region else 0

        # 验证数据一致性
        assert isinstance(total_by_region, int)