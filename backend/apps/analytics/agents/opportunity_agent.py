"""
Opportunity Analysis Agent - TDD Cycle 38

商机分析专家 Subagent
使用 deer-flow 的 subagent 机制
专门处理商机评分、推荐和风险分析任务
"""
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Dict, List, Optional

from apps.analytics.opportunity.scorer import (
    OpportunityScorer,
    TenderOpportunity,
    OpportunityScoreLevel,
)

logger = logging.getLogger(__name__)

# 线程池用于并发评分
_executor = ThreadPoolExecutor(max_workers=10)

# 全局评分器实例
_scorer: Optional[OpportunityScorer] = None


def _get_scorer() -> OpportunityScorer:
    """获取评分器实例"""
    global _scorer
    if _scorer is None:
        _scorer = OpportunityScorer()
    return _scorer


# 系统提示词
SYSTEM_PROMPT = """你是商机分析专家。

你的任务是深度分析招标商机价值，提供专业的评估和建议。

你可以使用以下工具：
- score_opportunity: 对单个招标进行商机评分

分析维度：
1. 金额评分 - 评估预算规模
2. 竞争度评分 - 评估竞争激烈程度
3. 时间评分 - 评估投标准备时间
4. 相关性评分 - 评估匹配程度
5. 历史评分 - 评估招标人信誉

总分100分：
- >=80分：高价值商机（优先跟进）
- 50-79分：中等价值（考虑跟进）
- <50分：低价值（选择性跟进）

输出要求：
- 返回详细的评分报告
- 提供行动建议
- 识别风险因素
"""


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """解析日期字符串为 datetime"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"无法解析日期: {date_str}")
            return None


def tender_to_dict(tender: TenderOpportunity) -> Dict[str, Any]:
    """将 TenderOpportunity 转换为字典"""
    return {
        "tender_id": tender.tender_id,
        "title": tender.title,
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


def _generate_recommendations(tender: TenderOpportunity) -> List[str]:
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


def _identify_risk_factors(tender: TenderOpportunity) -> List[str]:
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

    # 招标人风险
    if tender.factors.history_score < 8:
        risk_factors.append("招标人风险：招标人历史记录较少")

    # 空值风险
    if tender.budget is None:
        risk_factors.append("信息风险：预算金额未公开")
    if tender.deadline_date is None:
        risk_factors.append("信息风险：截止日期未确定")

    return risk_factors


class OpportunityAgent:
    """商机分析专用 Subagent

    这个 Subagent 专门处理商机价值分析和推荐。
    它可以对招标进行深度评分，识别高价值商机，
    并生成行动建议和风险控制方案。
    """

    name = "opportunity-agent"
    system_prompt = SYSTEM_PROMPT

    def __init__(self):
        """初始化商机分析 Agent"""
        self.scorer = _get_scorer()
        self._executor = _executor
        self._analysis_cache: Dict[str, Dict[str, Any]] = {}

    def _score_single_sync(self, tender_data: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行单个招标评分"""
        try:
            # 提取数据
            tender_id = tender_data.get("id") or tender_data.get("tender_id", "")
            title = tender_data.get("title", "")
            tenderer = tender_data.get("tenderer", "")
            budget = tender_data.get("budget")
            deadline_str = tender_data.get("deadline_date")
            publish_str = tender_data.get("publish_date")

            # 解析日期
            deadline = parse_date(deadline_str)
            publish = parse_date(publish_str)

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
            scored_tender = self.scorer.score_tender(tender)

            # 生成推荐和风险因素
            scored_tender.recommendations = _generate_recommendations(scored_tender)
            scored_tender.risk_factors = _identify_risk_factors(scored_tender)

            # 转换为字典
            result = tender_to_dict(scored_tender)
            result["status"] = "success"

            return result

        except Exception as e:
            logger.error(f"评分失败: {e}")
            tender_id = tender_data.get("id", tender_data.get("tender_id", "unknown"))
            return {
                "status": "error",
                "tender_id": tender_id,
                "error": str(e)
            }

    def analyze(self, tenders: List[Dict[str, Any]] | Dict[str, Any]) -> Dict[str, Any]:
        """分析商机

        Args:
            tenders: 招标数据（单个或列表）

        Returns:
            分析结果
        """
        # 处理单个招标
        if isinstance(tenders, dict):
            tenders = [tenders]

        if not tenders:
            return {
                "status": "success",
                "total_analyzed": 0,
                "high_value_count": 0,
                "medium_value_count": 0,
                "low_value_count": 0,
                "results": [],
                "top_opportunities": []
            }

        # 清空缓存
        self._analysis_cache.clear()

        # 并发评分
        results = []
        high_count = 0
        medium_count = 0
        low_count = 0

        futures = []
        for tender in tenders:
            future = self._executor.submit(self._score_single_sync, tender)
            futures.append((tender.get("id", ""), future))

        # 收集结果
        for tender_id, future in futures:
            try:
                result = future.result(timeout=30)
                results.append(result)

                # 统计各级别数量
                if result.get("status") == "success":
                    score_level = result.get("score_level", "low")
                    if score_level == "high":
                        high_count += 1
                    elif score_level == "medium":
                        medium_count += 1
                    else:
                        low_count += 1

                    # 缓存结果
                    self._analysis_cache[tender_id] = result

            except Exception as e:
                logger.error(f"评分任务执行失败: {e}")
                results.append({
                    "status": "error",
                    "tender_id": tender_id,
                    "error": str(e)
                })

        # 排序获取 TOP 机会
        scored_results = [
            (r.get("tender_id"), r.get("total_score", 0), r)
            for r in results
            if r.get("status") == "success"
        ]
        scored_results.sort(key=lambda x: x[1], reverse=True)
        top_opportunities = [r[0] for r in scored_results[:10]]

        return {
            "status": "success",
            "total_analyzed": len(tenders),
            "high_value_count": high_count,
            "medium_value_count": medium_count,
            "low_value_count": low_count,
            "results": results,
            "top_opportunities": top_opportunities
        }

    def find_high_value(self, tenders: List[Dict[str, Any]], threshold: float = 80.0) -> List[Dict[str, Any]]:
        """找出高价值商机

        Args:
            tenders: 招标列表
            threshold: 分数阈值

        Returns:
            高价值商机列表
        """
        if not tenders:
            return []

        # 先分析所有招标
        result = self.analyze(tenders)

        # 筛选高于阈值的
        high_value = []
        for r in result.get("results", []):
            if r.get("status") == "success" and r.get("total_score", 0) >= threshold:
                high_value.append(r)

        return high_value

    def generate_report(self, tender_id: str) -> Dict[str, Any]:
        """生成详细报告

        Args:
            tender_id: 招标ID

        Returns:
            详细报告
        """
        # 从缓存中获取分析结果
        if tender_id in self._analysis_cache:
            cached = self._analysis_cache[tender_id]
            return {
                "status": "success",
                "tender_id": tender_id,
                "report": {
                    "total_score": cached.get("total_score"),
                    "score_level": cached.get("score_level"),
                    "factors": cached.get("factors"),
                    "recommendations": cached.get("recommendations"),
                    "risk_factors": cached.get("risk_factors"),
                }
            }

        # 如果缓存中没有，返回错误
        return {
            "status": "error",
            "tender_id": tender_id,
            "error": "分析结果未找到，请先调用 analyze 方法"
        }

    async def run(self, task: str, context: dict) -> Dict[str, Any]:
        """执行分析任务（兼容 async 接口）

        Args:
            task: 任务描述
            context: 包含 tenders 列表的上下文

        Returns:
            分析结果
        """
        tenders = context.get("tenders", [])
        return self.analyze(tenders)


# 便捷函数
def create_opportunity_agent() -> OpportunityAgent:
    """创建商机分析 Agent 实例"""
    return OpportunityAgent()