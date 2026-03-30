"""
趋势分析引擎 - Cycle 29
实现招标信息的趋势分析功能
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from collections import defaultdict


# ==================== 数据结构定义 ====================

@dataclass
class TenderData:
    """招标数据结构"""
    id: str
    title: str
    publish_date: datetime
    amount: Optional[float]
    tenderer: str
    region: str
    industry: str


@dataclass
class TimeSeriesAnalysis:
    """时间序列分析"""
    monthly_counts: Dict[str, int] = field(default_factory=dict)      # 月度数量
    quarterly_counts: Dict[str, int] = field(default_factory=dict)    # 季度数量
    yearly_counts: Dict[str, int] = field(default_factory=dict)       # 年度数量
    monthly_amounts: Dict[str, float] = field(default_factory=dict)   # 月度金额


@dataclass
class RegionDistribution:
    """地区分布分析"""
    counts: Dict[str, int] = field(default_factory=dict)              # 各地区数量
    ratios: Dict[str, float] = field(default_factory=dict)            # 各地区占比
    amounts: Dict[str, float] = field(default_factory=dict)           # 各地区金额
    heat_ranking: List[str] = field(default_factory=list)             # 地区热度排名


@dataclass
class IndustryHeatAnalysis:
    """行业热度分析"""
    counts: Dict[str, int] = field(default_factory=dict)              # 各行业数量
    amounts: Dict[str, float] = field(default_factory=dict)           # 各行业金额
    heat_ranking: List[str] = field(default_factory=list)             # 行业热度排名


@dataclass
class AmountDistribution:
    """金额区间分布"""
    counts: Dict[str, int] = field(default_factory=dict)              # 各区间数量
    ratios: Dict[str, float] = field(default_factory=dict)            # 各区间占比


@dataclass
class TendererActivity:
    """招标人活跃度分析"""
    publish_counts: Dict[str, int] = field(default_factory=dict)      # 各招标人发布数量
    frequency_ranking: List[str] = field(default_factory=list)        # 发布频率排名
    total_unique_tenderers: int = 0                                   # 总招标人数


@dataclass
class TrendAnalysisResult:
    """趋势分析结果"""
    time_series: TimeSeriesAnalysis = field(default_factory=TimeSeriesAnalysis)
    region_distribution: RegionDistribution = field(default_factory=RegionDistribution)
    industry_heat: IndustryHeatAnalysis = field(default_factory=IndustryHeatAnalysis)
    amount_distribution: AmountDistribution = field(default_factory=AmountDistribution)
    tenderer_activity: TendererActivity = field(default_factory=TendererActivity)
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ==================== 金额区间常量 ====================

AMOUNT_RANGES = [
    ("0-10万", 0, 100000),
    ("10-50万", 100000, 500000),
    ("50-100万", 500000, 1000000),
    ("100-500万", 1000000, 5000000),
    ("500-1000万", 5000000, 10000000),
    ("1000万以上", 10000000, float('inf')),
]


# ==================== 趋势分析器实现 ====================

class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze(self, tenders: List[TenderData]) -> TrendAnalysisResult:
        """
        全面分析招标数据趋势

        Args:
            tenders: 招标数据列表

        Returns:
            TrendAnalysisResult: 分析结果
        """
        if not tenders:
            return TrendAnalysisResult()

        # 1. 时间序列分析
        time_series = self._analyze_time_series(tenders)

        # 2. 地区分布分析
        region_dist = self._analyze_region_distribution(tenders)

        # 3. 行业热度分析
        industry_heat = self._analyze_industry_heat(tenders)

        # 4. 金额分布分析
        amount_dist = self._analyze_amount_distribution(tenders)

        # 5. 招标人活跃度分析
        tenderer_activity = self._analyze_tenderer_activity(tenders)

        return TrendAnalysisResult(
            time_series=time_series,
            region_distribution=region_dist,
            industry_heat=industry_heat,
            amount_distribution=amount_dist,
            tenderer_activity=tenderer_activity,
            analyzed_at=datetime.now().isoformat()
        )

    def get_time_series_analysis(self, tenders: List[TenderData]) -> TimeSeriesAnalysis:
        """获取时间序列分析"""
        return self._analyze_time_series(tenders)

    def get_region_distribution(self, tenders: List[TenderData]) -> RegionDistribution:
        """获取地区分布分析"""
        return self._analyze_region_distribution(tenders)

    def get_industry_heat(self, tenders: List[TenderData]) -> IndustryHeatAnalysis:
        """获取行业热度分析"""
        return self._analyze_industry_heat(tenders)

    def get_amount_distribution(self, tenders: List[TenderData]) -> AmountDistribution:
        """获取金额分布分析"""
        return self._analyze_amount_distribution(tenders)

    def get_tenderer_activity(self, tenders: List[TenderData]) -> TendererActivity:
        """获取招标人活跃度分析"""
        return self._analyze_tenderer_activity(tenders)

    # ==================== 私有分析方法 ====================

    def _analyze_time_series(self, tenders: List[TenderData]) -> TimeSeriesAnalysis:
        """分析时间序列"""
        monthly_counts: Dict[str, int] = defaultdict(int)
        quarterly_counts: Dict[str, int] = defaultdict(int)
        yearly_counts: Dict[str, int] = defaultdict(int)
        monthly_amounts: Dict[str, float] = defaultdict(float)

        for tender in tenders:
            if tender.publish_date is None:
                continue

            # 提取时间维度
            year = tender.publish_date.strftime("%Y")
            month = tender.publish_date.strftime("%Y-%m")
            quarter = f"{year}-Q{(tender.publish_date.month - 1) // 3 + 1}"

            # 统计数量
            monthly_counts[month] += 1
            quarterly_counts[quarter] += 1
            yearly_counts[year] += 1

            # 统计金额（只统计非空金额）
            if tender.amount is not None:
                monthly_amounts[month] += tender.amount

        return TimeSeriesAnalysis(
            monthly_counts=dict(monthly_counts),
            quarterly_counts=dict(quarterly_counts),
            yearly_counts=dict(yearly_counts),
            monthly_amounts=dict(monthly_amounts)
        )

    def _analyze_region_distribution(self, tenders: List[TenderData]) -> RegionDistribution:
        """分析地区分布"""
        counts: Dict[str, int] = defaultdict(int)
        amounts: Dict[str, float] = defaultdict(float)

        for tender in tenders:
            # 处理空地区
            region = tender.region if tender.region else "未知"

            counts[region] += 1

            if tender.amount is not None:
                amounts[region] += tender.amount

        # 计算总数用于占比
        total = sum(counts.values())
        ratios = {k: v / total for k, v in counts.items()} if total > 0 else {}

        # 计算热度排名（按数量降序）
        heat_ranking = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)

        return RegionDistribution(
            counts=dict(counts),
            ratios=ratios,
            amounts=dict(amounts),
            heat_ranking=heat_ranking
        )

    def _analyze_industry_heat(self, tenders: List[TenderData]) -> IndustryHeatAnalysis:
        """分析行业热度"""
        counts: Dict[str, int] = defaultdict(int)
        amounts: Dict[str, float] = defaultdict(float)

        for tender in tenders:
            # 处理空行业
            industry = tender.industry if tender.industry else "未知"

            counts[industry] += 1

            if tender.amount is not None:
                amounts[industry] += tender.amount

        # 计算热度排名（按数量降序）
        heat_ranking = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)

        return IndustryHeatAnalysis(
            counts=dict(counts),
            amounts=dict(amounts),
            heat_ranking=heat_ranking
        )

    def _analyze_amount_distribution(self, tenders: List[TenderData]) -> AmountDistribution:
        """分析金额分布"""
        counts: Dict[str, int] = defaultdict(int)

        for tender in tenders:
            if tender.amount is None:
                continue

            # 找到对应区间
            for range_name, min_val, max_val in AMOUNT_RANGES:
                if min_val <= tender.amount < max_val:
                    counts[range_name] += 1
                    break

        # 计算总数用于占比
        total = sum(counts.values())
        ratios = {k: v / total for k, v in counts.items()} if total > 0 else {}

        return AmountDistribution(
            counts=dict(counts),
            ratios=ratios
        )

    def _analyze_tenderer_activity(self, tenders: List[TenderData]) -> TendererActivity:
        """分析招标人活跃度"""
        publish_counts: Dict[str, int] = defaultdict(int)

        for tender in tenders:
            if tender.tenderer:
                publish_counts[tender.tenderer] += 1

        # 计算频率排名（按发布数量降序）
        frequency_ranking = sorted(
            publish_counts.keys(),
            key=lambda x: publish_counts[x],
            reverse=True
        )

        return TendererActivity(
            publish_counts=dict(publish_counts),
            frequency_ranking=frequency_ranking,
            total_unique_tenderers=len(publish_counts)
        )