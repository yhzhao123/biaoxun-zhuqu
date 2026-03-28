"""
验证智能体

验证提取结果的完整性和准确性
"""
import logging
from typing import List

from apps.crawler.agents.schema import TenderNoticeSchema, ValidationResult

logger = logging.getLogger(__name__)


class ValidatorAgent:
    """
    验证智能体
    验证提取结果的完整性和一致性
    """

    def __init__(self):
        # 必填字段配置
        self.required_fields = ['title', 'publish_date', 'notice_type']
        self.important_fields = ['tenderer', 'description', 'budget_amount']

    async def validate(self, data: TenderNoticeSchema) -> ValidationResult:
        """
        验证提取结果

        Args:
            data: 提取的数据

        Returns:
            ValidationResult 验证结果
        """
        missing_fields = []
        warnings = []

        # 1. 必填字段检查
        for field in self.required_fields:
            value = getattr(data, field)
            if not value:
                missing_fields.append(field)

        # 2. 重要字段检查（记录警告）
        for field in self.important_fields:
            value = getattr(data, field)
            if not value:
                warnings.append(f"缺少重要字段: {field}")

        # 3. 逻辑一致性检查
        self._check_consistency(data, warnings)

        # 4. 计算置信度
        confidence = self._calculate_confidence(data, missing_fields)

        return ValidationResult(
            is_complete=len(missing_fields) == 0 and confidence >= 0.6,
            missing_fields=missing_fields,
            warnings=warnings,
            confidence=confidence
        )

    def _check_consistency(self, data: TenderNoticeSchema, warnings: List[str]):
        """检查数据一致性"""
        # 检查中标公告是否有中标人
        if data.notice_type == 'win' and not data.winner:
            warnings.append("中标公告缺少中标人信息")

        # 检查金额合理性
        if data.budget_amount:
            if data.budget_amount > 1_000_000_000_000:  # 1万亿
                warnings.append("预算金额异常（超过1万亿），请检查单位转换")
            elif data.budget_amount < 100 and data.budget_unit == '元':
                warnings.append("预算金额异常（过低），请检查单位")

        # 检查日期合理性
        from datetime import datetime
        if data.publish_date:
            if data.publish_date > datetime.now():
                warnings.append("发布日期为未来日期")
            if data.publish_date.year < 2020:
                warnings.append("发布日期过早（2020年前）")

        # 检查截止日期是否晚于发布日期
        if data.publish_date and data.deadline_date:
            if data.deadline_date < data.publish_date:
                warnings.append("截止日期早于发布日期")

    def _calculate_confidence(
        self,
        data: TenderNoticeSchema,
        missing_fields: List[str]
    ) -> float:
        """计算整体置信度"""
        score = 0.0
        weights = {
            'title': 0.20,
            'tenderer': 0.20,
            'description': 0.15,
            'budget_amount': 0.15,
            'publish_date': 0.10,
            'contact_person': 0.10,
            'project_number': 0.10,
        }

        for field, weight in weights.items():
            value = getattr(data, field)
            if value:
                score += weight

        # 根据缺失字段调整
        for field in missing_fields:
            if field in weights:
                score -= weights[field] * 0.5

        return max(0.0, min(1.0, score))
