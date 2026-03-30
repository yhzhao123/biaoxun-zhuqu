"""
Aggregate Data Tool - TDD Cycle 36

将 AnalyticsAPI 封装为 deer-flow Tool
提供统一的数据聚合接口，支持概览、分类统计、商机列表、趋势分析、完整仪表板
"""
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from langchain.tools import tool
from pydantic import BaseModel, Field

from apps.analytics.api.aggregator import (
    AnalyticsAPI,
    FilterParams,
    TenderData,
)

logger = logging.getLogger(__name__)


# ==================== 输入模型 ====================

class AggregateDataInput(BaseModel):
    """数据聚合工具输入模型"""
    tenders_json: str = Field(description="招标数据 JSON 字符串列表")
    query_type: str = Field(
        default="overview",
        description="查询类型: overview, classification, opportunities, trends, dashboard"
    )
    filters_json: Optional[str] = Field(
        default=None,
        description="筛选条件 JSON 字符串"
    )
    page: int = Field(default=1, description="页码")
    page_size: int = Field(default=20, description="每页大小")


# ==================== 辅助函数 ====================

def _parse_tenders_json(tenders_json: str) -> List[Dict[str, Any]]:
    """
    解析 tenders_json 字符串为字典列表

    Args:
        tenders_json: JSON 字符串

    Returns:
        字典列表，解析失败返回空列表
    """
    if not tenders_json:
        return []

    try:
        data = json.loads(tenders_json)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"解析 tenders_json 失败: {e}")
        return []


def _parse_filters_json(filters_json: Optional[str]) -> Dict[str, Any]:
    """
    解析 filters_json 字符串为字典

    Args:
        filters_json: JSON 字符串或 None

    Returns:
        字典，解析失败返回空字典
    """
    if not filters_json:
        return {}

    try:
        data = json.loads(filters_json)
        if isinstance(data, dict):
            return data
        return {}
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"解析 filters_json 失败: {e}")
        return {}


def _parse_datetime(date_str: Union[str, datetime, None]) -> Optional[datetime]:
    """
    解析日期字符串为 datetime

    Args:
        date_str: 日期字符串或 datetime 对象

    Returns:
        datetime 对象，解析失败返回 None
    """
    if date_str is None:
        return None

    if isinstance(date_str, datetime):
        return date_str

    if isinstance(date_str, str):
        # 尝试多种日期格式
        formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

    # 无法解析时返回当前时间
    logger.warning(f"无法解析日期: {date_str}")
    return datetime.now()


def _convert_to_tender_data(raw: Dict[str, Any]) -> TenderData:
    """
    将字典转换为 TenderData 对象

    Args:
        raw: 原始字典

    Returns:
        TenderData 对象
    """
    return TenderData(
        id=raw.get("id", ""),
        title=raw.get("title", ""),
        publish_date=_parse_datetime(raw.get("publish_date")),
        amount=raw.get("amount"),
        tenderer=raw.get("tenderer", ""),
        region=raw.get("region", ""),
        industry=raw.get("industry", ""),
        status=raw.get("status", "招标中"),
    )


def _build_filter_params(filters: Dict[str, Any]) -> FilterParams:
    """
    从字典构建 FilterParams 对象

    Args:
        filters: 筛选条件字典

    Returns:
        FilterParams 对象
    """
    # 解析时间范围
    start_date = _parse_datetime(filters.get("start_date"))
    end_date = _parse_datetime(filters.get("end_date"))

    # 解析地区和行业
    regions = filters.get("regions")
    industries = filters.get("industries")

    # 解析金额区间
    amount_range = filters.get("amount_range")
    if amount_range and isinstance(amount_range, list) and len(amount_range) == 2:
        amount_range = tuple(amount_range)

    # 解析商机评分最低值
    opportunity_score_min = filters.get("opportunity_score_min")
    if opportunity_score_min is not None:
        opportunity_score_min = float(opportunity_score_min)

    # 解析招标人列表
    tenderers = filters.get("tenderers")

    return FilterParams(
        start_date=start_date,
        end_date=end_date,
        regions=regions,
        industries=industries,
        amount_range=amount_range,
        opportunity_score_min=opportunity_score_min,
        tenderers=tenderers,
    )


def _serialize_result(result: Any) -> Dict[str, Any]:
    """
    序列化结果对象为字典

    Args:
        result: 结果对象

    Returns:
        字典
    """
    if hasattr(result, "__dataclass_fields__"):
        result_dict = {}
        for field_name in result.__dataclass_fields__:
            value = getattr(result, field_name)
            if hasattr(value, "__dataclass_fields__"):
                # 嵌套 dataclass
                result_dict[field_name] = _serialize_result(value)
            elif isinstance(value, dict):
                result_dict[field_name] = value
            elif isinstance(value, (list, tuple)):
                result_dict[field_name] = [
                    _serialize_result(item) if hasattr(item, "__dataclass_fields__") else item
                    for item in value
                ]
            else:
                result_dict[field_name] = value
        return result_dict
    elif isinstance(result, dict):
        return result
    else:
        return {}


# ==================== 工具实现 ====================

@tool(args_schema=AggregateDataInput)
def aggregate_data(
    tenders_json: str,
    query_type: str = "overview",
    filters_json: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> str:
    """
    对招标数据进行聚合分析

    提供统一的数据聚合接口，支持以下查询类型:
    - overview: 综合概览（总数量、总金额、今日/本周/本月新增）
    - classification: 分类统计（按招标人/地区/行业/金额分类）
    - opportunities: 商机列表（带评分、分页）
    - trends: 趋势数据（时间序列、地区分布、行业热度）
    - dashboard: 完整仪表板（聚合所有数据）

    Args:
        tenders_json: JSON 字符串，招标数据列表
        query_type: 查询类型 (overview, classification, opportunities, trends, dashboard)
        filters_json: 筛选条件 JSON（时间范围、地区、行业等）
        page: 页码
        page_size: 每页大小

    Returns:
        JSON 字符串，包含聚合分析结果
    """
    try:
        # 1. 解析输入数据
        raw_tenders = _parse_tenders_json(tenders_json)
        filters = _parse_filters_json(filters_json)

        # 2. 转换为 TenderData 列表
        tenders = [_convert_to_tender_data(raw) for raw in raw_tenders]

        # 3. 构建筛选参数
        filter_params = _build_filter_params(filters)

        # 4. 创建 API 实例
        api = AnalyticsAPI()

        # 5. 根据 query_type 执行相应查询
        result: Dict[str, Any] = {}

        if query_type == "overview":
            overview_result = api.get_overview(filter_params, tenders)
            result["overview"] = _serialize_result(overview_result)

        elif query_type == "classification":
            classification_result = api.get_classification_stats(filter_params, tenders)
            result["classification"] = _serialize_result(classification_result)

        elif query_type == "opportunities":
            from apps.analytics.api.aggregator import Pagination
            pagination = Pagination(page=page, page_size=page_size)
            opportunities_result = api.get_opportunities(filter_params, pagination, tenders)
            result["opportunities"] = _serialize_result(opportunities_result)

        elif query_type == "trends":
            trends_result = api.get_trends(filter_params, tenders)
            result["trends"] = _serialize_result(trends_result)

        elif query_type == "dashboard":
            dashboard_result = api.get_full_dashboard(filter_params, tenders)
            result = _serialize_result(dashboard_result)

        else:
            # 未知类型，回退到 overview
            logger.warning(f"未知的 query_type: {query_type}，回退到 overview")
            overview_result = api.get_overview(filter_params, tenders)
            result["overview"] = _serialize_result(overview_result)

        return json.dumps(result, ensure_ascii=False, default=str)

    except Exception as e:
        logger.error(f"聚合分析失败: {e}")
        return json.dumps({
            "error": str(e),
            "success": False
        }, ensure_ascii=False)