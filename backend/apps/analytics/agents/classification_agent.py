"""
Classification Agent - TDD Cycle 37

招标信息分类专家 Subagent
使用 deer-flow 的 subagent 机制
专门处理批量招标信息分类任务
"""
import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

from apps.analytics.classification.engine import TenderClassifier

logger = logging.getLogger(__name__)

# 线程池用于并发分类
_executor = ThreadPoolExecutor(max_workers=10)

# 全局分类器实例
_classifier: Optional[TenderClassifier] = None


def _get_classifier() -> TenderClassifier:
    """获取分类器实例"""
    global _classifier
    if _classifier is None:
        _classifier = TenderClassifier()
    return _classifier


class ClassificationAgent:
    """分类专用 Subagent

    这个 Agent 专门处理批量招标信息的分类任务。
    它使用 TenderClassifier 对多个招标进行分类，
    并生成综合分析报告。
    """

    name = "classification-agent"

    SYSTEM_PROMPT = """你是招标信息分类专家。

你的任务是对招标信息进行多维度分类分析。

你可以使用以下工具：
- classify_tender: 对单个招标进行分类

工作流程：
1. 接收招标数据列表
2. 对每个招标调用 classify_tender 进行分类
3. 汇总分类结果
4. 生成分类统计报告

输出要求：
- 返回 JSON 格式的分类结果
- 包含每个招标的分类详情
- 包含分类统计汇总
"""

    def __init__(self):
        """初始化分类 Agent"""
        self.classifier = _get_classifier()
        self._executor = _executor

    def _classify_single_sync(self, tender: Dict[str, Any]) -> Dict[str, Any]:
        """同步执行单个招标分类"""
        try:
            tender_id = tender.get("id", "")
            tenderer = tender.get("tenderer", "")
            region = tender.get("region", "")
            industry = tender.get("industry", "")
            amount = tender.get("amount")

            result = self.classifier.classify_tender(
                tender_id=tender_id,
                tenderer=tenderer,
                region=region,
                industry=industry,
                amount=amount
            )

            # 转换为字典格式
            classified = {
                "tender_id": result.tender_id,
            }

            if result.tenderer_category:
                classified["tenderer_category"] = {
                    "normalized": result.tenderer_category.normalized_value,
                    "type": result.tenderer_category.category,
                    "confidence": result.tenderer_category.confidence,
                }

            if result.region_category:
                classified["region_category"] = {
                    "normalized": result.region_category.normalized_value,
                    "zone": result.region_category.category,
                    "confidence": result.region_category.confidence,
                }

            if result.industry_category:
                classified["industry_category"] = {
                    "normalized": result.industry_category.normalized_value,
                    "code": result.industry_category.category,
                    "confidence": result.industry_category.confidence,
                }

            if result.amount_category:
                classified["amount_category"] = {
                    "range": result.amount_category.normalized_value,
                    "level": result.amount_category.category,
                    "confidence": result.amount_category.confidence,
                }

            return {
                "status": "success",
                **classified
            }

        except Exception as e:
            logger.error(f"分类失败: {e}")
            return {
                "status": "error",
                "tender_id": tender.get("id", "unknown"),
                "error": str(e)
            }

    def classify_single(
        self,
        tender_id: str,
        tenderer: str,
        region: str,
        industry: str,
        amount: Optional[float] = None
    ) -> Dict[str, Any]:
        """对单个招标进行分类

        Args:
            tender_id: 招标ID
            tenderer: 招标人
            region: 地区
            industry: 行业
            amount: 金额（可选）

        Returns:
            分类结果字典
        """
        tender = {
            "id": tender_id,
            "tenderer": tenderer,
            "region": region,
            "industry": industry,
            "amount": amount
        }
        return self._classify_single_sync(tender)

    def _call_classify_tool(self, tender: Dict[str, Any]) -> Dict[str, Any]:
        """调用 classify_tender Tool（兼容接口）

        Args:
            tender: 招标数据

        Returns:
            分类结果
        """
        return self._classify_single_sync(tender)

    def classify_batch(self, tenders: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量分类多个招标

        Args:
            tenders: 招标列表

        Returns:
            批量分类结果，包含汇总统计
        """
        if not tenders:
            return {
                "status": "success",
                "total": 0,
                "classified": 0,
                "results": [],
                "summary": {}
            }

        # 并发分类
        results = []
        classified_count = 0

        # 使用线程池并发处理
        futures = []
        for tender in tenders:
            future = self._executor.submit(self._classify_single_sync, tender)
            futures.append(future)

        # 收集结果
        for future in futures:
            try:
                result = future.result(timeout=30)
                results.append(result)
                if result.get("status") == "success":
                    classified_count += 1
            except Exception as e:
                logger.error(f"分类任务执行失败: {e}")
                results.append({
                    "status": "error",
                    "error": str(e)
                })

        # 生成汇总统计
        summary = self._generate_summary(results)

        return {
            "status": "success",
            "total": len(tenders),
            "classified": classified_count,
            "results": results,
            "summary": summary
        }

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成分类汇总统计

        Args:
            results: 分类结果列表

        Returns:
            汇总统计字典
        """
        summary = {
            "by_region": {},
            "by_industry": {},
            "by_amount": {},
            "by_tenderer_type": {}
        }

        for result in results:
            if result.get("status") != "success":
                continue

            # 地区统计
            if "region_category" in result and result["region_category"]:
                region = result["region_category"].get("normalized", "未知")
                summary["by_region"][region] = summary["by_region"].get(region, 0) + 1

            # 行业统计
            if "industry_category" in result and result["industry_category"]:
                industry = result["industry_category"].get("normalized", "未知")
                summary["by_industry"][industry] = summary["by_industry"].get(industry, 0) + 1

            # 金额统计
            if "amount_category" in result and result["amount_category"]:
                amount_range = result["amount_category"].get("range", "未知")
                summary["by_amount"][amount_range] = summary["by_amount"].get(amount_range, 0) + 1

            # 招标人类型统计
            if "tenderer_category" in result and result["tenderer_category"]:
                tenderer_type = result["tenderer_category"].get("type", "未知")
                summary["by_tenderer_type"][tenderer_type] = summary["by_tenderer_type"].get(tenderer_type, 0) + 1

        return summary

    async def run(self, task: str, context: dict) -> Dict[str, Any]:
        """执行分类任务（兼容 async 接口）

        Args:
            task: 任务描述
            context: 包含 tenders 列表的上下文

        Returns:
            分类结果
        """
        tenders = context.get("tenders", [])
        return self.classify_batch(tenders)


# 便捷函数
def create_classification_agent() -> ClassificationAgent:
    """创建分类 Agent 实例"""
    return ClassificationAgent()