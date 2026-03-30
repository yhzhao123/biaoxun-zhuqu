"""
Analyze Trends Tool - TDD Cycle 35

将 TrendAnalyzer 封装为 deer-flow Tool
使用 LangChain 的 @tool 装饰器
"""
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from langchain.tools import tool
from pydantic import BaseModel, Field

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

logger = logging.getLogger(__name__)


class AnalyzeTrendsInput(BaseModel):
    """趋势分析工具输入模型"""
    tenders_json: str = Field(
        description="招标数据 JSON 字符串列表，每项包含id, title, publish_date, amount, tenderer, region, industry"
    )
    analysis_type: str = Field(
        default="all",
        description="分析类型: time_series, region, industry, amount, tenderer, all"
    )


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


def time_series_to_dict(ts: TimeSeriesAnalysis) -> Dict[str, Any]:
    """将 TimeSeriesAnalysis 转换为字典"""
    return {
        "monthly_counts": ts.monthly_counts,
        "quarterly_counts": ts.quarterly_counts,
        "yearly_counts": ts.yearly_counts,
        "monthly_amounts": ts.monthly_amounts
    }


def region_distribution_to_dict(region: RegionDistribution) -> Dict[str, Any]:
    """将 RegionDistribution 转换为字典"""
    # 构建 heat_ranking 为完整对象列表
    heat_ranking_list = []
    for region_name in region.heat_ranking:
        count = region.counts.get(region_name, 0)
        total = sum(region.counts.values())
        percentage = (count / total * 100) if total > 0 else 0
        heat_ranking_list.append({
            "region": region_name,
            "count": count,
            "percentage": round(percentage, 2)
        })

    return {
        "counts": region.counts,
        "ratios": region.ratios,
        "amounts": region.amounts,
        "heat_ranking": heat_ranking_list
    }


def industry_heat_to_dict(industry: IndustryHeatAnalysis) -> Dict[str, Any]:
    """将 IndustryHeatAnalysis 转换为字典"""
    # 构建 heat_ranking 为完整对象列表
    heat_ranking_list = []
    for industry_name in industry.heat_ranking:
        count = industry.counts.get(industry_name, 0)
        heat_ranking_list.append({
            "industry": industry_name,
            "count": count
        })

    return {
        "counts": industry.counts,
        "amounts": industry.amounts,
        "heat_ranking": heat_ranking_list
    }


def amount_distribution_to_dict(amount: AmountDistribution) -> Dict[str, Any]:
    """将 AmountDistribution 转换为字典"""
    return {
        "counts": amount.counts,
        "percentages": {k: round(v * 100, 2) for k, v in amount.ratios.items()}
    }


def tenderer_activity_to_dict(tenderer: TendererActivity) -> Dict[str, Any]:
    """将 TendererActivity 转换为字典"""
    # 构建 frequency_ranking 为完整对象列表
    frequency_ranking_list = []
    for tenderer_name in tenderer.frequency_ranking:
        count = tenderer.publish_counts.get(tenderer_name, 0)
        frequency_ranking_list.append({
            "tenderer": tenderer_name,
            "count": count
        })

    return {
        "publish_counts": tenderer.publish_counts,
        "frequency_ranking": frequency_ranking_list,
        "total_unique_tenderers": tenderer.total_unique_tenderers
    }


def result_to_dict(result: TrendAnalysisResult) -> Dict[str, Any]:
    """将 TrendAnalysisResult 转换为字典"""
    return {
        "time_series": time_series_to_dict(result.time_series),
        "region_distribution": region_distribution_to_dict(result.region_distribution),
        "industry_heat": industry_heat_to_dict(result.industry_heat),
        "amount_distribution": amount_distribution_to_dict(result.amount_distribution),
        "tenderer_activity": tenderer_activity_to_dict(result.tenderer_activity),
        "analyzed_at": result.analyzed_at
    }


# 全局分析器实例
_analyzer: Optional[TrendAnalyzer] = None


def _get_analyzer() -> TrendAnalyzer:
    """获取分析器实例"""
    global _analyzer
    if _analyzer is None:
        _analyzer = TrendAnalyzer()
    return _analyzer


@tool(args_schema=AnalyzeTrendsInput)
def analyze_trends(tenders_json: str, analysis_type: str = "all") -> str:
    """
    对招标数据进行趋势分析

    支持时间序列、地区分布、行业热度、金额区间、招标人活跃度等多维度分析

    Args:
        tenders_json: JSON 字符串，招标数据列表
        analysis_type: 分析类型 (time_series, region, industry, amount, tenderer, all)

    Returns:
        JSON 字符串，包含分析结果
    """
    try:
        # 解析 JSON 输入
        try:
            tenders_data = json.loads(tenders_json)
        except json.JSONDecodeError as e:
            return json.dumps({
                "error": f"JSON 解析失败: {str(e)}",
                "success": False
            }, ensure_ascii=False)

        if not isinstance(tenders_data, list):
            return json.dumps({
                "error": "输入必须是招标数据列表",
                "success": False
            }, ensure_ascii=False)

        # 转换为 TenderData 对象
        tenders = parse_tender_data(tenders_data)

        # 获取分析器
        analyzer = _get_analyzer()

        # 根据 analysis_type 执行分析
        if analysis_type == "all":
            result = analyzer.analyze(tenders)
            return json.dumps(result_to_dict(result), ensure_ascii=False)

        elif analysis_type == "time_series":
            ts = analyzer.get_time_series_analysis(tenders)
            return json.dumps({
                "time_series": time_series_to_dict(ts),
                "analyzed_at": datetime.now().isoformat()
            }, ensure_ascii=False)

        elif analysis_type == "region":
            region = analyzer.get_region_distribution(tenders)
            return json.dumps({
                "region_distribution": region_distribution_to_dict(region),
                "analyzed_at": datetime.now().isoformat()
            }, ensure_ascii=False)

        elif analysis_type == "industry":
            industry = analyzer.get_industry_heat(tenders)
            return json.dumps({
                "industry_heat": industry_heat_to_dict(industry),
                "analyzed_at": datetime.now().isoformat()
            }, ensure_ascii=False)

        elif analysis_type == "amount":
            amount = analyzer.get_amount_distribution(tenders)
            return json.dumps({
                "amount_distribution": amount_distribution_to_dict(amount),
                "analyzed_at": datetime.now().isoformat()
            }, ensure_ascii=False)

        elif analysis_type == "tenderer":
            tenderer = analyzer.get_tenderer_activity(tenders)
            return json.dumps({
                "tenderer_activity": tenderer_activity_to_dict(tenderer),
                "analyzed_at": datetime.now().isoformat()
            }, ensure_ascii=False)

        else:
            return json.dumps({
                "error": f"未知的 analysis_type: {analysis_type}",
                "success": False
            }, ensure_ascii=False)

    except Exception as e:
        logger.error(f"趋势分析失败: {e}")
        return json.dumps({
            "error": str(e),
            "success": False
        }, ensure_ascii=False)