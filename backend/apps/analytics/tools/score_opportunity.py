"""
Score Opportunity Tool - TDD Cycle 34

将 OpportunityScorer 封装为 deer-flow Tool
使用 LangChain 的 @tool 装饰器
"""
import json
import logging
from typing import Optional, Dict, Any

from langchain.tools import tool
from pydantic import BaseModel, Field
from datetime import datetime

from apps.analytics.opportunity.scorer import (
    OpportunityScorer,
    TenderOpportunity,
    OpportunityScoreLevel,
)

logger = logging.getLogger(__name__)


class ScoreOpportunityInput(BaseModel):
    """评分工具输入模型"""
    tender_id: str = Field(description="招标唯一标识")
    title: str = Field(description="招标标题")
    tenderer: str = Field(description="招标人名称")
    budget: Optional[float] = Field(default=None, description="预算金额")
    deadline_date: Optional[str] = Field(default=None, description="截止日期 (ISO格式)")
    publish_date: Optional[str] = Field(default=None, description="发布日期 (ISO格式)")
    region: Optional[str] = Field(default=None, description="地区")
    industry: Optional[str] = Field(default=None, description="行业")


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """解析日期字符串为 datetime"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        try:
            # 尝试简单格式 YYYY-MM-DD
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"无法解析日期: {date_str}")
            return None


def tender_opportunity_to_dict(tender: TenderOpportunity) -> Dict[str, Any]:
    """将 TenderOpportunity 转换为字典"""
    return {
        "tender_id": tender.tender_id,
        "total_score": tender.total_score,
        "score_level": tender.score_level.value,
        "factors": {
            "amount_score": tender.factors.amount_score,
            "competition_score": tender.factors.competition_score,
            "timeline_score": tender.factors.timeline_score,
            "relevance_score": tender.factors.relevance_score,
            "history_score": tender.factors.history_score,
        },
        "recommendations": tender.recommendations,
        "risk_factors": tender.risk_factors,
    }


# 全局评分器实例
_scorer: Optional[OpportunityScorer] = None


def _get_scorer() -> OpportunityScorer:
    """获取评分器实例"""
    global _scorer
    if _scorer is None:
        _scorer = OpportunityScorer()
    return _scorer


@tool(args_schema=ScoreOpportunityInput)
def score_opportunity(
    tender_id: str,
    title: str,
    tenderer: str,
    budget: Optional[float] = None,
    deadline_date: Optional[str] = None,
    publish_date: Optional[str] = None,
    region: Optional[str] = None,
    industry: Optional[str] = None
) -> str:
    """
    对招标商机进行智能评分

    从5个维度评估商机价值：金额、竞争度、时间、相关性、历史
    总分100分，>=80分为高价值商机

    Args:
        tender_id: 招标唯一标识
        title: 招标标题
        tenderer: 招标人名称
        budget: 预算金额（可选）
        deadline_date: 截止日期，ISO格式如 "2024-06-30"（可选）
        publish_date: 发布日期，ISO格式如 "2024-01-15"（可选）
        region: 地区（可选）
        industry: 行业（可选）

    Returns:
        JSON 字符串，包含评分结果和推荐建议
    """
    try:
        scorer = _get_scorer()

        # 解析日期
        deadline = parse_date(deadline_date)
        publish = parse_date(publish_date)

        # 创建 TenderOpportunity
        tender = TenderOpportunity(
            tender_id=tender_id,
            title=title,
            tenderer=tenderer,
            budget=budget,
            deadline_date=deadline,
            publish_date=publish,
        )

        # 评分
        scored_tender = scorer.score_tender(tender)

        # 生成推荐和风险因素
        scored_tender.recommendations = _generate_recommendations(scored_tender)
        scored_tender.risk_factors = _identify_risk_factors(scored_tender)

        return json.dumps(
            tender_opportunity_to_dict(scored_tender),
            ensure_ascii=False
        )

    except Exception as e:
        logger.error(f"评分失败: {e}")
        return json.dumps({
            "tender_id": tender_id,
            "error": str(e),
            "success": False
        }, ensure_ascii=False)


def _generate_recommendations(tender: TenderOpportunity) -> list:
    """生成推荐建议"""
    recommendations = []

    # 根据评分等级推荐
    if tender.score_level == OpportunityScoreLevel.HIGH:
        recommendations.append("高价值商机，建议优先跟进")
    elif tender.score_level == OpportunityScoreLevel.MEDIUM:
        recommendations.append("中等价值商机，可选择性跟进")
    else:
        recommendations.append("低价值商机，建议评估后决策")

    # 根据招标人类型推荐
    premium_tenderers = ["中国移动", "中国联通", "中国电信", "国家电网", "南方电网",
                        "中石油", "中石化", "中海油", "中铁", "中建", "中交"]
    for premium in premium_tenderers:
        if premium in tender.tenderer:
            recommendations.append("招标人信誉良好，国有企业")
            break

    # 根据金额推荐
    if tender.budget and tender.budget >= 10000000:
        recommendations.append("项目金额较大，值得重点投入资源")
    elif tender.budget and tender.budget >= 1000000:
        recommendations.append("项目金额适中，值得关注")

    # 根据时间推荐
    if tender.factors.timeline_score >= 15:
        recommendations.append("投标时间充裕，准备时间充足")
    elif tender.factors.timeline_score < 5:
        recommendations.append("警告：投标截止时间临近，需尽快准备")

    # 根据竞争度推荐
    if tender.factors.competition_score >= 15:
        recommendations.append("竞争相对较小，中标机会较高")
    elif tender.factors.competition_score < 10:
        recommendations.append("竞争激烈，需充分准备竞争优势")

    return recommendations


def _identify_risk_factors(tender: TenderOpportunity) -> list:
    """识别风险因素"""
    risk_factors = []

    # 时间风险
    if tender.factors.timeline_score < 10:
        risk_factors.append("时间紧迫风险：投标准备时间不足")

    # 金额风险
    if tender.budget and tender.budget < 50000:
        risk_factors.append("金额风险：项目金额较小，收益有限")

    # 竞争风险
    if tender.factors.competition_score < 10:
        risk_factors.append("竞争风险：参与竞争者众多")

    # 招标人风险（非常见招标人）
    if tender.factors.history_score < 8:
        risk_factors.append("招标人风险：招标人历史记录较少")

    # 空值风险
    if tender.budget is None:
        risk_factors.append("信息风险：预算金额未公开")
    if tender.deadline_date is None:
        risk_factors.append("信息风险：截止日期未确定")

    return risk_factors