"""
招标信息结构化 Schema 定义
用于 LLM 提取后的数据验证和标准化
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
import json


@dataclass
class TenderNoticeSchema:
    """
    招标公告标准 Schema

    定义了从招标网页提取的标准字段，用于 LLM 结构化输出
    """

    # 核心字段
    title: Optional[str] = None  # 招标/中标标题
    description: Optional[str] = None  # 项目描述

    # 相关方信息
    tenderer: Optional[str] = None  # 招标人/采购单位
    winner: Optional[str] = None  # 中标人/成交供应商
    contact_person: Optional[str] = None  # 联系人
    contact_phone: Optional[str] = None  # 联系电话

    # 金额相关
    budget_amount: Optional[Decimal] = None  # 预算/中标金额（单位：元）
    budget_unit: Optional[str] = None  # 原始金额单位：元、万元、亿元
    currency: str = "CNY"  # 货币类型

    # 日期相关
    publish_date: Optional[datetime] = None  # 发布日期
    deadline_date: Optional[datetime] = None  # 截止日期/开标日期

    # 项目标识
    project_number: Optional[str] = None  # 项目编号

    # 分类信息
    region: Optional[str] = None  # 地区/省份
    region_code: Optional[str] = None  # 地区编码
    industry: Optional[str] = None  # 行业分类
    industry_code: Optional[str] = None  # 行业编码

    # 来源相关
    source_url: Optional[str] = None  # 来源 URL
    source_site: Optional[str] = None  # 来源网站名称

    # 元数据（由系统填充）
    notice_type: str = "bidding"  # 公告类型: bidding(招标)|win(中标)|change(变更)
    extraction_method: str = "llm"  # 提取方法
    extraction_confidence: float = 0.0  # 提取置信度 (0-1)
    llm_provider: Optional[str] = None  # LLM 提供商
    llm_model: Optional[str] = None  # LLM 模型
    raw_llm_response: Optional[str] = None  # LLM 原始响应（用于追溯）

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典，用于数据库存储"""
        return {
            'title': self.title,
            'description': self.description,
            'tenderer': self.tenderer,
            'winner': self.winner,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'budget_amount': float(self.budget_amount) if self.budget_amount else None,
            'budget_unit': self.budget_unit,
            'currency': self.currency,
            'publish_date': self.publish_date.isoformat() if self.publish_date else None,
            'deadline_date': self.deadline_date.isoformat() if self.deadline_date else None,
            'project_number': self.project_number,
            'region': self.region,
            'region_code': self.region_code,
            'industry': self.industry,
            'industry_code': self.industry_code,
            'source_url': self.source_url,
            'source_site': self.source_site,
            'notice_type': self.notice_type,
            'extraction_method': self.extraction_method,
            'extraction_confidence': self.extraction_confidence,
            'llm_provider': self.llm_provider,
            'llm_model': self.llm_model,
            'raw_llm_response': self.raw_llm_response,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TenderNoticeSchema':
        """从字典创建实例"""
        # 处理日期字段
        publish_date = None
        if data.get('publish_date'):
            try:
                if isinstance(data['publish_date'], str):
                    publish_date = datetime.fromisoformat(data['publish_date'].replace('Z', '+00:00'))
                elif isinstance(data['publish_date'], datetime):
                    publish_date = data['publish_date']
            except:
                pass

        deadline_date = None
        if data.get('deadline_date'):
            try:
                if isinstance(data['deadline_date'], str):
                    deadline_date = datetime.fromisoformat(data['deadline_date'].replace('Z', '+00:00'))
                elif isinstance(data['deadline_date'], datetime):
                    deadline_date = data['deadline_date']
            except:
                pass

        # 处理金额
        budget_amount = None
        if data.get('budget_amount'):
            try:
                budget_amount = Decimal(str(data['budget_amount']))
            except:
                pass

        return cls(
            title=data.get('title'),
            description=data.get('description'),
            tenderer=data.get('tenderer'),
            winner=data.get('winner'),
            contact_person=data.get('contact_person'),
            contact_phone=data.get('contact_phone'),
            budget_amount=budget_amount,
            budget_unit=data.get('budget_unit'),
            currency=data.get('currency', 'CNY'),
            publish_date=publish_date,
            deadline_date=deadline_date,
            project_number=data.get('project_number'),
            region=data.get('region'),
            region_code=data.get('region_code'),
            industry=data.get('industry'),
            industry_code=data.get('industry_code'),
            source_url=data.get('source_url'),
            source_site=data.get('source_site'),
            notice_type=data.get('notice_type', 'bidding'),
            extraction_method=data.get('extraction_method', 'llm'),
            extraction_confidence=float(data.get('extraction_confidence', 0.0)),
            llm_provider=data.get('llm_provider'),
            llm_model=data.get('llm_model'),
            raw_llm_response=data.get('raw_llm_response'),
        )

    def validate(self) -> List[str]:
        """
        验证数据完整性
        返回：错误消息列表（空列表表示验证通过）
        """
        errors = []

        # 必填字段检查
        if not self.title:
            errors.append("title 是必填字段")

        # 标题长度检查
        if self.title and len(self.title) < 5:
            errors.append("title 长度太短（至少5个字符）")

        # 日期格式验证
        if self.publish_date and not isinstance(self.publish_date, datetime):
            errors.append("publish_date 必须是 datetime 类型")

        if self.deadline_date and not isinstance(self.deadline_date, datetime):
            errors.append("deadline_date 必须是 datetime 类型")

        # 金额验证
        if self.budget_amount is not None:
            if self.budget_amount < 0:
                errors.append("budget_amount 不能为负数")
            if self.budget_amount > 999999999999:  # 9999亿
                errors.append("budget_amount 数值异常过大")

        # 置信度验证
        if not 0 <= self.extraction_confidence <= 1:
            errors.append("extraction_confidence 必须在 0-1 之间")

        # 公告类型验证
        valid_types = ['bidding', 'win', 'change']
        if self.notice_type not in valid_types:
            errors.append(f"notice_type 必须是以下之一: {valid_types}")

        return errors

    def is_valid(self) -> bool:
        """检查数据是否有效"""
        return len(self.validate()) == 0

    def get_quality_score(self) -> float:
        """
        获取数据质量评分
        基于字段完整性和数据质量
        """
        score = 0.0

        # 核心字段（每个 20 分）
        if self.title and len(self.title) > 5:
            score += 20
        if self.tenderer:
            score += 20
        if self.publish_date:
            score += 20
        if self.budget_amount and self.budget_amount > 0:
            score += 20
        if self.description and len(self.description) > 20:
            score += 20

        # 额外字段（每个 5 分，最多 20 分）
        extra_fields = [
            self.project_number,
            self.region,
            self.industry,
            self.contact_person,
            self.contact_phone,
            self.deadline_date,
            self.winner if self.notice_type == 'win' else True  # 中标公告才需要
        ]
        score += sum(5 for f in extra_fields if f) * 5
        score = min(score, 100)

        return score

    def to_model_fields(self) -> Dict[str, Any]:
        """
        转换为 TenderNotice 模型字段
        用于直接创建或更新数据库记录
        """
        return {
            'title': self.title or '',
            'description': self.description or '',
            'tenderer': self.tenderer or '',
            'budget': self.budget_amount,
            'budget_amount': self.budget_amount,
            'currency': self.currency,
            'publish_date': self.publish_date,
            'deadline_date': self.deadline_date,
            'project_number': self.project_number,
            'region': self.region,
            'industry': self.industry,
            'source_url': self.source_url,
            'source_site': self.source_site,
            'notice_type': self.notice_type,
            'status': 'active',
        }
