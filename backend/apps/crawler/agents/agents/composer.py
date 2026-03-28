"""
合并智能体

合并多源数据（列表页、详情页、PDF）
"""
import logging
from typing import Dict, Any, Optional, List

from apps.crawler.agents.schema import TenderNoticeSchema

logger = logging.getLogger(__name__)


class ComposerAgent:
    """
    数据合并智能体
    合并来自不同来源的招标信息
    """

    def __init__(self):
        # 数据源优先级权重
        self.source_weights = {
            'api_list': 0.7,
            'detail_page': 0.85,
            'pdf': 0.95,
            'llm_extraction': 0.8,
            'fallback': 0.3,
        }

        # 字段级别的优先级（某些字段在特定来源中更可靠）
        self.field_source_preference = {
            'title': ['api_list', 'detail_page', 'llm_extraction'],
            'tenderer': ['pdf', 'detail_page', 'llm_extraction'],
            'budget_amount': ['api_list', 'pdf', 'detail_page'],
            'description': ['pdf', 'detail_page', 'llm_extraction'],
            'contact_person': ['pdf', 'detail_page'],
            'contact_phone': ['pdf', 'detail_page'],
        }

    async def merge(
        self,
        base: TenderNoticeSchema,
        new_data: Dict[str, Any],
        source: str
    ) -> TenderNoticeSchema:
        """
        合并数据

        Args:
            base: 基础数据
            new_data: 新数据
            source: 数据来源

        Returns:
            合并后的数据
        """
        if not new_data:
            return base

        # 转换为字典便于操作
        result_dict = base.to_dict()

        # 获取数据源权重
        source_weight = self.source_weights.get(source, 0.5)

        for field, value in new_data.items():
            # 跳过元数据字段
            if field in ['source', 'extraction_method', 'extraction_confidence']:
                continue

            # 跳过空值
            if value is None or value == '':
                continue

            # 获取当前字段的置信度
            current_confidence = result_dict.get(f'{field}_confidence', 0)
            new_confidence = source_weight

            # 根据字段偏好调整
            if field in self.field_source_preference:
                preferred_sources = self.field_source_preference[field]
                if source in preferred_sources:
                    # 优先来源，增加权重
                    new_confidence = min(1.0, new_confidence + 0.1)

            # 如果新数据置信度更高，则替换
            if new_confidence > current_confidence:
                # 类型转换
                converted_value = self._convert_field_value(field, value)
                result_dict[field] = converted_value
                result_dict[f'{field}_confidence'] = new_confidence

                logger.debug(f"Merged field {field} from {source} (confidence: {new_confidence:.2f})")

        # 转换回Schema
        return TenderNoticeSchema.from_dict(result_dict)

    def _convert_field_value(self, field: str, value: Any) -> Any:
        """转换字段值为正确类型"""
        if field == 'budget_amount' and isinstance(value, (int, float, str)):
            from decimal import Decimal
            try:
                return Decimal(str(value))
            except:
                return value

        if field in ['publish_date', 'deadline_date']:
            if isinstance(value, str):
                from datetime import datetime
                try:
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    pass

        return value

    async def merge_multiple(
        self,
        sources: List[Dict[str, Any]],
        base_url: str
    ) -> TenderNoticeSchema:
        """
        合并多个来源的数据

        Args:
            sources: 多个来源数据列表，每个元素是 {'data': dict, 'source': str}
            base_url: 基础URL

        Returns:
            合并后的数据
        """
        result = TenderNoticeSchema(source_url=base_url)

        # 按权重排序来源
        sorted_sources = sorted(
            sources,
            key=lambda x: self.source_weights.get(x.get('source', ''), 0),
            reverse=True
        )

        for source_info in sorted_sources:
            data = source_info.get('data', {})
            source = source_info.get('source', 'unknown')

            result = await self.merge(result, data, source)

        return result
