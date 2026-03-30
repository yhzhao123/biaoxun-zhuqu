"""
Trend Analysis Agent - TDD Cycle 39

趋势分析专家 Subagent
使用 deer-flow 的 subagent 机制
专门处理时间序列、地区分布、行业热度等多维度趋势分析任务
"""
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from apps.analytics.tools.analyze_trends import analyze_trends
from apps.analytics.trends.analyzer import (
    TrendAnalyzer,
    TenderData,
)

logger = logging.getLogger(__name__)

# 全局分析器实例
_analyzer: Optional[TrendAnalyzer] = None


def _get_analyzer() -> TrendAnalyzer:
    """获取分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = TrendAnalyzer()
    return _analyzer


# 系统提示词
SYSTEM_PROMPT = """你是招标市场趋势分析专家。

你的任务是分析招标数据的趋势和规律，提供市场洞察。

你可以使用以下工具：
- analyze_trends: 对招标数据进行趋势分析

分析维度：
1. 时间序列分析 - 月度/季度/年度趋势
2. 地区分布分析 - 各地区占比和热度
3. 行业热度分析 - 各行业招标数量
4. 金额区间分析 - 不同金额区间分布
5. 招标人活跃度 - 活跃招标人排名

输出要求：
- 返回详细的趋势分析报告
- 提供可视化数据
- 给出市场洞察和建议
"""


def parse_tender_data(tenders_data: List[Dict[str, Any]]) -> List[TenderData]:
    """将字典列表转换为 TenderData 列表"""
    tenders = []
    for item in tenders_data:
        # 解析日期
        publish_date = None
        if item.get("publish_date"):
            try:
                publish_date = datetime.fromisoformat(item["publish_date"])
            except (ValueError, TypeError):
                # 尝试其他日期格式
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日"]:
                    try:
                        publish_date = datetime.strptime(item["publish_date"], fmt)
                        break
                    except (ValueError, TypeError):
                        continue

        tender = TenderData(
            id=item.get("id", ""),
            title=item.get("title", ""),
            publish_date=publish_date,
            amount=item.get("amount"),
            tenderer=item.get("tenderer", ""),
            region=item.get("region", ""),
            industry=item.get("industry", "")
        )
        tenders.append(tender)
    return tenders


def _calculate_trend(monthly_counts: Dict[str, int]) -> str:
    """计算趋势方向

    Args:
        monthly_counts: 月度数量字典

    Returns:
        趋势方向: increasing, stable, decreasing
    """
    if not monthly_counts or len(monthly_counts) < 2:
        return "stable"

    # 按月份排序
    sorted_months = sorted(monthly_counts.keys())
    counts = [monthly_counts[m] for m in sorted_months]

    # 计算平均增长率
    growth_rates = []
    for i in range(1, len(counts)):
        if counts[i - 1] > 0:
            rate = (counts[i] - counts[i - 1]) / counts[i - 1]
            growth_rates.append(rate)

    if not growth_rates:
        return "stable"

    avg_growth = sum(growth_rates) / len(growth_rates)

    if avg_growth > 0.1:
        return "increasing"
    elif avg_growth < -0.1:
        return "decreasing"
    else:
        return "stable"


def _calculate_growth_rate(monthly_counts: Dict[str, int]) -> float:
    """计算增长率

    Args:
        monthly_counts: 月度数量字典

    Returns:
        增长率
    """
    if not monthly_counts or len(monthly_counts) < 2:
        return 0.0

    sorted_months = sorted(monthly_counts.keys())
    first_month = monthly_counts[sorted_months[0]]
    last_month = monthly_counts[sorted_months[-1]]

    if first_month == 0:
        return 0.0

    return (last_month - first_month) / first_month


def generate_insights(
    time_series: Optional[Dict[str, Any]],
    regions: Optional[Dict[str, Any]],
    industry: Optional[Dict[str, Any]],
    amount: Optional[Dict[str, Any]]
) -> List[str]:
    """生成市场洞察

    Args:
        time_series: 时间序列分析结果
        regions: 地区分布分析结果
        industry: 行业热度分析结果
        amount: 金额分布分析结果

    Returns:
        洞察列表
    """
    insights = []

    # 时间序列洞察
    if time_series:
        monthly_counts = time_series.get("monthly_counts", {})
        if monthly_counts:
            trend = time_series.get("trend", "stable")
            if trend == "increasing":
                insights.append("招标市场呈上升趋势，每月招标数量持续增加")
            elif trend == "decreasing":
                insights.append("招标市场呈下降趋势，需关注市场变化")
            else:
                insights.append("招标市场保持稳定态势")

            growth_rate = time_series.get("growth_rate", 0)
            if growth_rate > 0:
                insights.append(f"整体增长率为 {growth_rate*100:.1f}%")

    # 地区洞察
    if regions and "top_regions" in regions:
        top = regions["top_regions"]
        if top:
            insights.append(f"{top[0]['region']}地区招标数量占比最高，达到 {top[0]['percentage']:.1f}%")
            if len(top) > 1:
                insights.append(f"前两大地区（{top[0]['region']}、{top[1]['region']}）占比超过 50%")

    # 行业洞察
    if industry and "top_industries" in industry:
        top = industry["top_industries"]
        if top:
            insights.append(f"{top[0]['industry']}行业热度最高，招标数量最多")
            if len(top) > 1:
                insights.append(f"重点关注 {top[0]['industry']} 和 {top[1]['industry']} 行业")

    # 金额洞察
    if amount and "distribution" in amount:
        dist = amount["distribution"]
        if dist:
            # 找出最多的区间
            max_range = max(dist.items(), key=lambda x: x[1])
            insights.append(f"{max_range[0]}区间招标数量最多")

    return insights


def generate_recommendations(analysis_result: Dict[str, Any]) -> List[str]:
    """基于分析结果生成建议

    Args:
        analysis_result: 分析结果字典

    Returns:
        建议列表
    """
    recommendations = []

    # 地区建议
    regional = analysis_result.get("regional_analysis", {})
    if regional and "top_regions" in regional:
        top_regions = regional["top_regions"]
        if top_regions:
            recommendations.append(f"重点关注 {top_regions[0]['region']} 地区的招标机会")

    # 行业建议
    industry = analysis_result.get("industry_analysis", {})
    if industry and "top_industries" in industry:
        top_industries = industry["top_industries"]
        if top_industries:
            recommendations.append(f"建议加强 {top_industries[0]['industry']} 行业投标能力")

    # 时间建议
    time_series = analysis_result.get("time_series_analysis", {})
    if time_series:
        trend = time_series.get("trend", "stable")
        if trend == "increasing":
            recommendations.append("市场上升期，建议加大投标力度")
        elif trend == "decreasing":
            recommendations.append("市场下行期，建议精选项目，控制成本")

    # 金额建议
    amount = analysis_result.get("amount_analysis", {})
    if amount and "distribution" in amount:
        dist = amount["distribution"]
        if dist:
            # 建议关注中等金额项目
            recommendations.append("建议关注 100-500 万区间的中等金额项目，竞争相对可控")

    if not recommendations:
        recommendations.append("建议持续关注招标市场动态，及时把握商机")

    return recommendations


class TrendAnalysisAgent:
    """趋势分析专用 Subagent

    这个 Subagent 专门处理招标市场趋势分析。
    它可以分析时间序列、地区分布、行业热度、金额区间等维度，
    并生成趋势报告和预测建议。
    """

    name = "trend-analysis-agent"
    system_prompt = SYSTEM_PROMPT

    def __init__(self):
        """初始化趋势分析 Agent"""
        self.analyzer = _get_analyzer()

    def analyze(self, tenders: List[Dict[str, Any]] | Dict[str, Any]) -> Dict[str, Any]:
        """全面分析招标趋势

        Args:
            tenders: 招标数据（单个或列表）

        Returns:
            完整的趋势分析报告
        """
        # 处理单个招标
        if isinstance(tenders, dict):
            tenders = [tenders]

        if not tenders:
            return {
                "status": "success",
                "report_date": datetime.now().strftime("%Y-%m-%d"),
                "total_tenders": 0,
                "data_summary": {
                    "total_tenders": 0,
                    "date_range": "N/A"
                },
                "time_series_analysis": {},
                "regional_analysis": {"top_regions": []},
                "industry_analysis": {"top_industries": []},
                "amount_analysis": {"distribution": {}},
                "insights": [],
                "recommendations": ["暂无数据"]
            }

        # 转换为 TenderData
        tender_data = parse_tender_data(tenders)

        # 执行分析
        result = self.analyzer.analyze(tender_data)

        # 获取日期范围
        dates = [t.publish_date for t in tender_data if t.publish_date]
        if dates:
            min_date = min(dates).strftime("%Y-%m-%d")
            max_date = max(dates).strftime("%Y-%m-%d")
            date_range = f"{min_date} to {max_date}"
        else:
            date_range = "N/A"

        # 计算趋势和增长率
        monthly_counts = result.time_series.monthly_counts
        trend = _calculate_trend(monthly_counts)
        growth_rate = _calculate_growth_rate(monthly_counts)

        # 构建地区分析结果
        top_regions = []
        total = sum(result.region_distribution.counts.values())
        for region_name in result.region_distribution.heat_ranking[:10]:
            count = result.region_distribution.counts.get(region_name, 0)
            amount_sum = result.region_distribution.amounts.get(region_name, 0)
            percentage = (count / total * 100) if total > 0 else 0
            top_regions.append({
                "region": region_name,
                "count": count,
                "percentage": round(percentage, 2),
                "amount_sum": amount_sum
            })

        # 构建行业分析结果
        top_industries = []
        for industry_name in result.industry_heat.heat_ranking[:10]:
            count = result.industry_heat.counts.get(industry_name, 0)
            percentage = (count / len(tender_data) * 100) if tender_data else 0
            top_industries.append({
                "industry": industry_name,
                "count": count,
                "percentage": round(percentage, 2)
            })

        # 构建返回结果
        return {
            "status": "success",
            "report_date": datetime.now().strftime("%Y-%m-%d"),
            "total_tenders": len(tenders),
            "data_summary": {
                "total_tenders": len(tenders),
                "date_range": date_range
            },
            "time_series_analysis": {
                "monthly_counts": result.time_series.monthly_counts,
                "quarterly_counts": result.time_series.quarterly_counts,
                "yearly_counts": result.time_series.yearly_counts,
                "monthly_amounts": result.time_series.monthly_amounts,
                "trend": trend,
                "growth_rate": round(growth_rate, 2)
            },
            "regional_analysis": {
                "top_regions": top_regions,
                "heat_ranking": result.region_distribution.heat_ranking
            },
            "industry_analysis": {
                "top_industries": top_industries,
                "heat_ranking": result.industry_heat.heat_ranking
            },
            "amount_analysis": {
                "distribution": result.amount_distribution.counts,
                "percentages": {k: round(v * 100, 2) for k, v in result.amount_distribution.ratios.items()},
                "total_amount": sum(result.industry_heat.amounts.values())
            },
            "tenderer_activity": {
                "total_unique": result.tenderer_activity.total_unique_tenderers,
                "top_tenderers": result.tenderer_activity.frequency_ranking[:10]
            },
            "insights": generate_insights(
                {"monthly_counts": result.time_series.monthly_counts, "trend": trend, "growth_rate": growth_rate},
                {"top_regions": top_regions},
                {"top_industries": top_industries},
                {"distribution": result.amount_distribution.counts}
            ),
            "recommendations": generate_recommendations({
                "regional_analysis": {"top_regions": top_regions},
                "industry_analysis": {"top_industries": top_industries},
                "time_series_analysis": {"trend": trend},
                "amount_analysis": {"distribution": result.amount_distribution.counts}
            })
        }

    def analyze_time_series(self, tenders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """时间序列分析

        Args:
            tenders: 招标列表

        Returns:
            时间序列分析结果
        """
        if not tenders:
            return {"monthly_counts": {}, "trend": "stable", "growth_rate": 0}

        tender_data = parse_tender_data(tenders)
        result = self.analyzer.get_time_series_analysis(tender_data)

        monthly_counts = result.monthly_counts
        trend = _calculate_trend(monthly_counts)
        growth_rate = _calculate_growth_rate(monthly_counts)

        return {
            "monthly_counts": monthly_counts,
            "quarterly_counts": result.quarterly_counts,
            "yearly_counts": result.yearly_counts,
            "monthly_amounts": result.monthly_amounts,
            "trend": trend,
            "growth_rate": round(growth_rate, 2)
        }

    def analyze_regional_distribution(self, tenders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """地区分布分析

        Args:
            tenders: 招标列表

        Returns:
            地区分布分析结果
        """
        if not tenders:
            return {"top_regions": []}

        tender_data = parse_tender_data(tenders)
        result = self.analyzer.get_region_distribution(tender_data)

        top_regions = []
        total = sum(result.counts.values())
        for region_name in result.heat_ranking[:10]:
            count = result.counts.get(region_name, 0)
            amount_sum = result.amounts.get(region_name, 0)
            percentage = (count / total * 100) if total > 0 else 0
            top_regions.append({
                "region": region_name,
                "count": count,
                "percentage": round(percentage, 2),
                "amount_sum": amount_sum
            })

        return {
            "top_regions": top_regions,
            "heat_ranking": result.heat_ranking,
            "counts": result.counts,
            "ratios": result.ratios
        }

    def analyze_industry_heat(self, tenders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """行业热度分析

        Args:
            tenders: 招标列表

        Returns:
            行业热度分析结果
        """
        if not tenders:
            return {"top_industries": []}

        tender_data = parse_tender_data(tenders)
        result = self.analyzer.get_industry_heat(tender_data)

        top_industries = []
        total = len(tender_data)
        for industry_name in result.heat_ranking[:10]:
            count = result.counts.get(industry_name, 0)
            percentage = (count / total * 100) if total > 0 else 0
            top_industries.append({
                "industry": industry_name,
                "count": count,
                "percentage": round(percentage, 2)
            })

        return {
            "top_industries": top_industries,
            "heat_ranking": result.heat_ranking,
            "counts": result.counts,
            "amounts": result.amounts
        }

    def analyze_amount_distribution(self, tenders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """金额区间分析

        Args:
            tenders: 招标列表

        Returns:
            金额分布分析结果
        """
        if not tenders:
            return {"distribution": {}, "total_amount": 0}

        tender_data = parse_tender_data(tenders)
        result = self.analyzer.get_amount_distribution(tender_data)

        total_amount = sum(
            t.amount for t in tender_data
            if t.amount is not None
        )

        return {
            "distribution": result.counts,
            "percentages": {k: round(v * 100, 2) for k, v in result.ratios.items()},
            "total_amount": total_amount
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
def create_trend_analysis_agent() -> TrendAnalysisAgent:
    """创建趋势分析 Agent 实例"""
    return TrendAnalysisAgent()