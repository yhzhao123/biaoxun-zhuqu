"""
Classify Tender Tool - TDD Cycle 33

将 TenderClassifier 封装为 deer-flow Tool
使用 LangChain 的 @tool 装饰器
"""
import json
import logging
from typing import Optional, Dict, Any

from langchain.tools import tool
from pydantic import BaseModel, Field

from apps.analytics.classification.engine import (
    TenderClassifier,
    TenderClassification,
    ClassificationResult,
)

logger = logging.getLogger(__name__)


class ClassifyTenderInput(BaseModel):
    """分类工具输入模型"""
    tender_id: str = Field(description="招标唯一标识")
    tenderer: str = Field(description="招标人名称")
    region: str = Field(description="地区名称")
    industry: str = Field(description="行业名称")
    amount: Optional[float] = Field(default=None, description="预算金额")


def classification_result_to_dict(result: Optional[ClassificationResult]) -> Optional[Dict[str, Any]]:
    """将 ClassificationResult 转换为字典"""
    if result is None:
        return None
    return {
        "original": result.original_value,
        "normalized": result.normalized_value,
        "category": result.category,
        "confidence": result.confidence,
        "type": result.classification_type.value if result.classification_type else None,
    }


def tender_classification_to_dict(classification: TenderClassification) -> Dict[str, Any]:
    """将 TenderClassification 转换为字典"""
    result = {
        "tender_id": classification.tender_id,
    }

    if classification.tenderer_category:
        result["tenderer_category"] = classification_result_to_dict(classification.tenderer_category)

    if classification.region_category:
        result["region_category"] = classification_result_to_dict(classification.region_category)

    if classification.industry_category:
        result["industry_category"] = classification_result_to_dict(classification.industry_category)

    if classification.amount_category:
        result["amount_category"] = classification_result_to_dict(classification.amount_category)

    if classification.created_at:
        result["created_at"] = classification.created_at

    return result


# 全局分类器实例
_classifier: Optional[TenderClassifier] = None


def _get_classifier() -> TenderClassifier:
    """获取分类器实例"""
    global _classifier
    if _classifier is None:
        _classifier = TenderClassifier()
    return _classifier


@tool(args_schema=ClassifyTenderInput)
def classify_tender(
    tender_id: str,
    tenderer: str,
    region: str,
    industry: str,
    amount: Optional[float] = None
) -> str:
    """
    对招标信息进行智能分类

    对招标人、地区、行业、金额进行分类和标准化处理

    Args:
        tender_id: 招标唯一标识
        tenderer: 招标人名称
        region: 地区名称
        industry: 行业名称
        amount: 预算金额（可选）

    Returns:
        JSON 字符串，包含完整的分类结果
    """
    try:
        classifier = _get_classifier()

        result = classifier.classify_tender(
            tender_id=tender_id,
            tenderer=tenderer,
            region=region,
            industry=industry,
            amount=amount
        )

        return json.dumps(
            tender_classification_to_dict(result),
            ensure_ascii=False
        )

    except Exception as e:
        logger.error(f"分类失败: {e}")
        return json.dumps({
            "tender_id": tender_id,
            "error": str(e),
            "success": False
        }, ensure_ascii=False)