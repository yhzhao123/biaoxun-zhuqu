"""
数据聚合 API - Cycle 30
整合分类、商机、趋势分析模块的统一 API
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum

# 导入现有模块
from apps.analytics.classification.engine import TenderClassifier
from apps.analytics.opportunity.scorer import OpportunityScorer, TenderOpportunity, OpportunityScoreLevel as OppScoreLevel
from apps.analytics.trends.analyzer import TrendAnalyzer


# ==================== 数据结构定义 ====================

@dataclass
class TenderData:
    """招标数据结构 (扩展版)"""
    id: str
    title: str
    publish_date: datetime
    amount: Optional[float]
    tenderer: str
    region: str
    industry: str
    status: str = "招标中"  # 招标状态


class OpportunityScoreLevel(Enum):
    """商机评分等级"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class FilterParams:
    """筛选参数"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    regions: Optional[List[str]] = None
    industries: Optional[List[str]] = None
    amount_range: Optional[Tuple[float, float]] = None
    opportunity_score_min: Optional[float] = None
    tenderers: Optional[List[str]] = None


@dataclass
class Pagination:
    """分页参数"""
    page: int = 1
    page_size: int = 10


@dataclass
class OverviewResult:
    """概览结果"""
    total_count: int = 0
    total_amount: float = 0.0
    active_tenderers: int = 0
    avg_amount: float = 0.0
    today_count: int = 0
    week_count: int = 0
    month_count: int = 0


@dataclass
class ClassificationStats:
    """分类统计结果"""
    by_tenderer: Dict[str, int] = field(default_factory=dict)
    by_region: Dict[str, int] = field(default_factory=dict)
    by_industry: Dict[str, int] = field(default_factory=dict)
    by_amount_range: Dict[str, int] = field(default_factory=dict)


@dataclass
class OpportunityItem:
    """商机条目"""
    tender_id: str
    title: str
    tenderer: str
    budget: Optional[float]
    region: str
    industry: str
    total_score: float
    score_level: OpportunityScoreLevel
    publish_date: Optional[datetime] = None


@dataclass
class OpportunityList:
    """商机列表结果"""
    items: List[OpportunityItem] = field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0


@dataclass
class TrendResult:
    """趋势分析结果"""
    time_series: Dict[str, Any] = field(default_factory=dict)
    region_distribution: Dict[str, Any] = field(default_factory=dict)
    industry_heat: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DashboardResult:
    """完整仪表板结果"""
    overview: OverviewResult = field(default_factory=OverviewResult)
    classification: Dict[str, Any] = field(default_factory=dict)
    opportunities: List[OpportunityItem] = field(default_factory=list)
    trends: TrendResult = field(default_factory=TrendResult)


# ==================== 金额区间常量 ====================

AMOUNT_RANGES = [
    ("0-10万", 0, 100000),
    ("10-50万", 100000, 500000),
    ("50-100万", 500000, 1000000),
    ("100-500万", 1000000, 5000000),
    ("500-1000万", 5000000, 10000000),
    ("1000万以上", 10000000, float('inf')),
]


# ==================== AnalyticsAPI 实现 ====================

class AnalyticsAPI:
    """数据分析聚合 API"""

    def __init__(self):
        """初始化 API"""
        self.classifier = TenderClassifier()
        self.scorer = OpportunityScorer()
        self.analyzer = TrendAnalyzer()

    def _apply_filters(
        self,
        tenders: List[TenderData],
        filters: FilterParams
    ) -> List[TenderData]:
        """应用筛选条件"""
        result = tenders

        # 时间范围筛选
        if filters.start_date:
            result = [t for t in result if t.publish_date >= filters.start_date]
        if filters.end_date:
            result = [t for t in result if t.publish_date <= filters.end_date]

        # 地区筛选
        if filters.regions:
            result = [t for t in result if t.region in filters.regions]

        # 行业筛选
        if filters.industries:
            result = [t for t in result if t.industry in filters.industries]

        # 金额区间筛选
        if filters.amount_range:
            min_amt, max_amt = filters.amount_range
            result = [t for t in result if t.amount is not None and min_amt <= t.amount < max_amt]

        # 招标人筛选
        if filters.tenderers:
            result = [t for t in result if t.tenderer in filters.tenderers]

        return result

    def get_overview(
        self,
        filters: FilterParams,
        tenders: List[TenderData]
    ) -> OverviewResult:
        """获取统计概览"""
        filtered = self._apply_filters(tenders, filters)

        if not filtered:
            return OverviewResult()

        # 基本统计
        total_count = len(filtered)
        total_amount = sum(t.amount for t in filtered if t.amount is not None)
        unique_tenderers = len(set(t.tenderer for t in filtered if t.tenderer))
        avg_amount = total_amount / total_count if total_count > 0 else 0.0

        # 时间周期统计
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = today_start.replace(day=1)

        today_count = sum(1 for t in filtered if t.publish_date >= today_start)
        week_count = sum(1 for t in filtered if t.publish_date >= week_start)
        month_count = sum(1 for t in filtered if t.publish_date >= month_start)

        return OverviewResult(
            total_count=total_count,
            total_amount=total_amount,
            active_tenderers=unique_tenderers,
            avg_amount=avg_amount,
            today_count=today_count,
            week_count=week_count,
            month_count=month_count
        )

    def get_classification_stats(
        self,
        filters: FilterParams,
        tenders: List[TenderData]
    ) -> ClassificationStats:
        """获取分类统计"""
        filtered = self._apply_filters(tenders, filters)

        if not filtered:
            return ClassificationStats()

        # 按招标人统计
        by_tenderer: Dict[str, int] = {}
        for t in filtered:
            by_tenderer[t.tenderer] = by_tenderer.get(t.tenderer, 0) + 1

        # 按地区统计
        by_region: Dict[str, int] = {}
        for t in filtered:
            by_region[t.region] = by_region.get(t.region, 0) + 1

        # 按行业统计
        by_industry: Dict[str, int] = {}
        for t in filtered:
            by_industry[t.industry] = by_industry.get(t.industry, 0) + 1

        # 按金额区间统计
        by_amount_range: Dict[str, int] = {}
        for t in filtered:
            if t.amount is not None:
                for range_name, min_val, max_val in AMOUNT_RANGES:
                    if min_val <= t.amount < max_val:
                        by_amount_range[range_name] = by_amount_range.get(range_name, 0) + 1
                        break

        return ClassificationStats(
            by_tenderer=by_tenderer,
            by_region=by_region,
            by_industry=by_industry,
            by_amount_range=by_amount_range
        )

    def get_opportunities(
        self,
        filters: FilterParams,
        pagination: Pagination,
        tenders: List[TenderData]
    ) -> OpportunityList:
        """获取商机列表"""
        filtered = self._apply_filters(tenders, filters)

        # 转换为 TenderOpportunity 并评分
        opportunities: List[OpportunityItem] = []

        for t in filtered:
            # 创建商机对象
            opp = TenderOpportunity(
                tender_id=t.id,
                title=t.title,
                tenderer=t.tenderer,
                budget=t.amount,
                publish_date=t.publish_date,
            )

            # 评分
            scored = self.scorer.score_tender(opp)

            # 创建商机条目
            level = OpportunityScoreLevel.HIGH if scored.total_score >= 80 else \
                    OpportunityScoreLevel.MEDIUM if scored.total_score >= 50 else \
                    OpportunityScoreLevel.LOW

            # 应用商机评分筛选
            if filters.opportunity_score_min and scored.total_score < filters.opportunity_score_min:
                continue

            item = OpportunityItem(
                tender_id=t.id,
                title=t.title,
                tenderer=t.tenderer,
                budget=t.amount,
                region=t.region,
                industry=t.industry,
                total_score=scored.total_score,
                score_level=level,
                publish_date=t.publish_date,
            )
            opportunities.append(item)

        # 按评分排序
        opportunities.sort(key=lambda x: x.total_score, reverse=True)

        # 分页
        total = len(opportunities)
        total_pages = (total + pagination.page_size - 1) // pagination.page_size
        start = (pagination.page - 1) * pagination.page_size
        end = start + pagination.page_size

        return OpportunityList(
            items=opportunities[start:end],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            total_pages=total_pages
        )

    def get_trends(
        self,
        filters: FilterParams,
        tenders: List[TenderData]
    ) -> TrendResult:
        """获取趋势数据"""
        filtered = self._apply_filters(tenders, filters)

        if not filtered:
            return TrendResult()

        # 使用 TrendAnalyzer 分析
        # 需要转换为 trends 模块的 TenderData 格式
        from apps.analytics.trends.analyzer import TenderData as AnalyzerTenderData

        analyzer_tenders = [
            AnalyzerTenderData(
                id=t.id,
                title=t.title,
                publish_date=t.publish_date,
                amount=t.amount,
                tenderer=t.tenderer,
                region=t.region,
                industry=t.industry,
            )
            for t in filtered
        ]

        result = self.analyzer.analyze(analyzer_tenders)

        return TrendResult(
            time_series={
                'monthly_counts': result.time_series.monthly_counts,
                'quarterly_counts': result.time_series.quarterly_counts,
                'yearly_counts': result.time_series.yearly_counts,
            },
            region_distribution={
                'counts': result.region_distribution.counts,
                'ratios': result.region_distribution.ratios,
                'heat_ranking': result.region_distribution.heat_ranking,
            },
            industry_heat={
                'counts': result.industry_heat.counts,
                'heat_ranking': result.industry_heat.heat_ranking,
            }
        )

    def get_full_dashboard(
        self,
        filters: FilterParams,
        tenders: List[TenderData]
    ) -> DashboardResult:
        """获取完整仪表板数据"""
        # 获取各部分数据
        overview = self.get_overview(filters, tenders)
        classification_stats = self.get_classification_stats(filters, tenders)
        opportunities_result = self.get_opportunities(
            filters,
            Pagination(page=1, page_size=10),
            tenders
        )
        trends = self.get_trends(filters, tenders)

        return DashboardResult(
            overview=overview,
            classification={
                'by_tenderer': classification_stats.by_tenderer,
                'by_region': classification_stats.by_region,
                'by_industry': classification_stats.by_industry,
                'by_amount_range': classification_stats.by_amount_range,
            },
            opportunities=opportunities_result.items,
            trends=trends
        )