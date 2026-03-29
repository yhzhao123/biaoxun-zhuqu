"""
商机识别系统 - Cycle 28
AI 驱动的商机评分与推荐
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import re


class OpportunityScoreLevel(Enum):
    """商机评分等级"""
    HIGH = "high"           # 高价值商机 (>= 80分)
    MEDIUM = "medium"       # 中等价值 (50-79分)
    LOW = "low"             # 低价值 (< 50分)


@dataclass
class TenderScoreFactors:
    """招标评分因子"""
    amount_score: float = 0.0           # 金额评分 (0-25)
    competition_score: float = 0.0      # 竞争度评分 (0-25)
    timeline_score: float = 0.0         # 时间充裕度评分 (0-20)
    relevance_score: float = 0.0        # 相关性评分 (0-15)
    history_score: float = 0.0          # 历史中标率评分 (0-15)

    @property
    def total_score(self) -> float:
        """计算总分"""
        return (
            self.amount_score +
            self.competition_score +
            self.timeline_score +
            self.relevance_score +
            self.history_score
        )


@dataclass
class TenderOpportunity:
    """招标商机"""
    tender_id: str
    title: str
    tenderer: str
    budget: Optional[float] = None
    deadline_date: Optional[datetime] = None
    publish_date: Optional[datetime] = None

    # 评分相关
    factors: TenderScoreFactors = field(default_factory=TenderScoreFactors)
    total_score: float = 0.0
    score_level: OpportunityScoreLevel = field(default=OpportunityScoreLevel.LOW)

    # 分析结果
    recommendations: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    similar_tenders: List[str] = field(default_factory=list)

    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class OpportunityRecommendation:
    """商机推荐"""
    tender_id: str
    score: float
    reasons: List[str]
    action_items: List[str]
    priority: int


class OpportunityScorer:
    """商机评分器"""

    def __init__(self):
        """初始化评分器"""
        self.amount_scorer = AmountScorer()
        self.competition_scorer = CompetitionScorer()
        self.timeline_scorer = TimelineScorer()
        self.relevance_scorer = RelevanceScorer()
        self.history_scorer = HistoryScorer()

    def score_tender(self, tender: TenderOpportunity) -> TenderOpportunity:
        """
        对招标进行评分

        Args:
            tender: 招标商机

        Returns:
            TenderOpportunity: 带评分的招标商机
        """
        # 计算各项分数
        tender.factors.amount_score = self.amount_scorer.score(tender.budget)
        tender.factors.competition_score = self.competition_scorer.score(
            tender.tender_id, tender.tenderer
        )
        tender.factors.timeline_score = self.timeline_scorer.score(tender.deadline_date)

        # 相关性评分使用默认用户画像
        default_profile = {"industries": [], "regions": []}
        tender.factors.relevance_score = self.relevance_scorer.score(tender, default_profile)
        tender.factors.history_score = self.history_scorer.score(tender.tenderer)

        # 计算总分
        tender.total_score = tender.factors.total_score

        # 计算等级
        tender.score_level = self._calculate_score_level(tender.total_score)

        return tender

    def get_recommendations(
        self,
        tenders: List[TenderOpportunity],
        top_n: int = 10
    ) -> List[OpportunityRecommendation]:
        """
        获取商机推荐

        Args:
            tenders: 招标列表
            top_n: 返回前 N 个推荐

        Returns:
            List[OpportunityRecommendation]: 推荐列表
        """
        # 先为所有招标评分
        scored_tenders = [self.score_tender(t) for t in tenders]

        # 按分数排序
        sorted_tenders = sorted(
            scored_tenders,
            key=lambda x: x.total_score,
            reverse=True
        )

        # 生成推荐
        recommendations = []
        for i, tender in enumerate(sorted_tenders[:top_n]):
            reasons = self._generate_reasons(tender)
            action_items = self._generate_action_items(tender)

            rec = OpportunityRecommendation(
                tender_id=tender.tender_id,
                score=tender.total_score,
                reasons=reasons,
                action_items=action_items,
                priority=i + 1
            )
            recommendations.append(rec)

        return recommendations

    def _calculate_score_level(self, score: float) -> OpportunityScoreLevel:
        """计算评分等级"""
        if score >= 80:
            return OpportunityScoreLevel.HIGH
        elif score >= 50:
            return OpportunityScoreLevel.MEDIUM
        else:
            return OpportunityScoreLevel.LOW

    def _generate_reasons(self, tender: TenderOpportunity) -> List[str]:
        """生成推荐理由"""
        reasons = []
        if tender.factors.amount_score >= 20:
            reasons.append("项目金额较大，值得重点关注")
        if tender.factors.timeline_score >= 15:
            reasons.append("投标时间充裕，准备时间充足")
        if tender.factors.competition_score >= 15:
            reasons.append("竞争相对较小，中标机会较高")
        if not reasons:
            reasons.append("符合基本投标条件")
        return reasons

    def _generate_action_items(self, tender: TenderOpportunity) -> List[str]:
        """生成行动建议"""
        actions = []
        if tender.factors.timeline_score < 10:
            actions.append("紧急：投标截止时间临近，需尽快准备")
        if tender.budget and tender.budget > 10000000:
            actions.append("建议组建专项投标团队")
        if tender.factors.competition_score < 10:
            actions.append("建议深入了解竞争对手情况")
        if not actions:
            actions.append("按正常流程准备投标材料")
        return actions


class AmountScorer:
    """金额评分器"""

    def score(self, amount: Optional[float]) -> float:
        """
        根据金额评分
        评分逻辑：金额越大分数越高，最高25分

        Args:
            amount: 预算金额

        Returns:
            float: 评分 (0-25)
        """
        if amount is None:
            return 0.0

        # 金额分段评分
        if amount >= 10000000:  # >= 1000万
            return 25.0
        elif amount >= 5000000:  # >= 500万
            return 22.5
        elif amount >= 1000000:  # >= 100万
            return 20.0
        elif amount >= 500000:  # >= 50万
            return 17.5
        elif amount >= 100000:  # >= 10万
            return 15.0
        elif amount >= 50000:  # >= 5万
            return 10.0
        elif amount >= 10000:  # >= 1万
            return 7.5
        else:
            return 5.0


class CompetitionScorer:
    """竞争度评分器"""

    # 竞争度关键词
    HIGH_COMPETITION_KEYWORDS = [
        "政府", "国企", "央企", "事业单位", "公开招标", "竞争性磋商"
    ]
    LOW_COMPETITION_KEYWORDS = [
        "邀请招标", "单一来源", "内部采购", "协议供货"
    ]

    def score(self, tender_id: str, tenderer: str) -> float:
        """
        根据竞争情况评分
        评分逻辑：竞争越小分数越高（最高25分）

        Args:
            tender_id: 招标ID
            tenderer: 招标人

        Returns:
            float: 评分 (0-25)
        """
        base_score = 15.0  # 基础分

        # 检查高竞争关键词
        for keyword in self.HIGH_COMPETITION_KEYWORDS:
            if keyword in tenderer:
                base_score -= 5.0
                break

        # 检查低竞争关键词
        for keyword in self.LOW_COMPETITION_KEYWORDS:
            if keyword in tenderer:
                base_score += 5.0
                break

        return max(0.0, min(25.0, base_score))


class TimelineScorer:
    """时间评分器"""

    def score(self, deadline: Optional[datetime]) -> float:
        """
        根据投标截止时间评分
        评分逻辑：时间越充裕分数越高（最高20分）

        Args:
            deadline: 截止时间

        Returns:
            float: 评分 (0-20)
        """
        if deadline is None:
            return 10.0  # 无截止日期给中等分

        now = datetime.now()
        if deadline < now:
            return 0.0  # 已过期

        days_remaining = (deadline - now).days

        # 根据剩余天数评分
        if days_remaining >= 60:
            return 20.0
        elif days_remaining >= 45:
            return 18.0
        elif days_remaining >= 30:
            return 16.0
        elif days_remaining >= 20:
            return 14.0
        elif days_remaining >= 14:
            return 12.0
        elif days_remaining >= 7:
            return 8.0
        elif days_remaining >= 3:
            return 5.0
        else:
            return 2.0


class RelevanceScorer:
    """相关性评分器"""

    # 行业匹配关键词
    INDUSTRY_KEYWORDS = {
        "软件": ["软件", "开发", "系统", "平台", "应用", "程序"],
        "硬件": ["硬件", "设备", "服务器", "计算机", "网络"],
        "建筑": ["建筑", "工程", "施工", "装修", "土建"],
        "服务": ["服务", "咨询", "运维", "维护", "支持"],
    }

    def score(self, tender: TenderOpportunity, user_profile: Dict) -> float:
        """
        根据用户画像计算相关性

        Args:
            tender: 招标信息
            user_profile: 用户画像

        Returns:
            float: 评分 (0-15)
        """
        score = 7.5  # 基础分

        # 行业匹配
        user_industries = user_profile.get("industries", [])
        if user_industries:
            title = tender.title.lower()
            for industry in user_industries:
                if industry in self.INDUSTRY_KEYWORDS:
                    keywords = self.INDUSTRY_KEYWORDS[industry]
                    if any(kw in title for kw in keywords):
                        score += 5.0
                        break

        # 地区匹配
        user_regions = user_profile.get("regions", [])
        if user_regions and tender.tenderer:
            for region in user_regions:
                if region in tender.tenderer:
                    score += 2.5
                    break

        return max(0.0, min(15.0, score))


class HistoryScorer:
    """历史评分器"""

    # 已知优质招标人（示例数据）
    PREMIUM_TENDERERS = [
        "中国移动", "中国联通", "中国电信", "国家电网", "南方电网",
        "中石油", "中石化", "中海油", "中铁", "中建", "中交"
    ]

    def score(self, tenderer: str) -> float:
        """
        根据历史中标率评分

        Args:
            tenderer: 招标人

        Returns:
            float: 评分 (0-15)
        """
        # 检查是否为大企业
        for premium in self.PREMIUM_TENDERERS:
            if premium in tenderer:
                return 12.0  # 大企业给高分

        # 政府机构
        if "政府" in tenderer or "局" in tenderer or "委" in tenderer:
            return 10.0

        # 事业单位
        if "医院" in tenderer or "学校" in tenderer or "研究院" in tenderer:
            return 9.0

        # 默认分数
        return 7.5
