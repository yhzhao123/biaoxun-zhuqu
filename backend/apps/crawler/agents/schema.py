"""
招标信息提取 Schema 定义
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal


@dataclass
class Attachment:
    """附件信息"""
    url: str
    filename: str
    type: str  # 'pdf', 'doc', 'docx', etc.
    size: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'url': self.url,
            'filename': self.filename,
            'type': self.type,
            'size': self.size,
        }


@dataclass
class ExtractionStrategy:
    """提取策略配置"""
    site_type: str  # 'api', 'static', 'dynamic'

    # 列表页策略
    list_strategy: Dict[str, Any] = field(default_factory=dict)

    # 详情页策略
    detail_strategy: Dict[str, Any] = field(default_factory=dict)

    # 反检测策略
    anti_detection: Dict[str, Any] = field(default_factory=lambda: {
        'delay_seconds': 1.5,
        'headers': {}
    })

    # 最大页数
    max_pages: int = 5

    # API配置（如果是API类型）
    api_config: Optional[Dict] = None


@dataclass
class DetailResult:
    """详情页爬取结果"""
    url: str
    html: str
    attachments: List[Attachment] = field(default_factory=list)
    list_data: Dict[str, Any] = field(default_factory=dict)

    # 正文PDF内容（当详情页是PDF而非HTML时）
    main_pdf_content: Optional[str] = None  # PDF提取的文本内容
    main_pdf_url: Optional[str] = None  # 正文PDF的URL
    main_pdf_filename: Optional[str] = None  # 正文PDF文件名

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于缓存）"""
        return {
            'url': self.url,
            'html': self.html,
            'attachments': [a.to_dict() for a in self.attachments],
            'list_data': self.list_data,
            'main_pdf_content': self.main_pdf_content,
            'main_pdf_url': self.main_pdf_url,
            'main_pdf_filename': self.main_pdf_filename,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetailResult':
        """从字典创建"""
        attachments = [
            Attachment(**a) for a in data.get('attachments', [])
        ]
        return cls(
            url=data.get('url', ''),
            html=data.get('html', ''),
            attachments=attachments,
            list_data=data.get('list_data', {}),
            main_pdf_content=data.get('main_pdf_content'),
            main_pdf_url=data.get('main_pdf_url'),
            main_pdf_filename=data.get('main_pdf_filename'),
        )


@dataclass
class ValidationResult:
    """验证结果"""
    is_complete: bool
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class TenderNoticeSchema:
    """
    招标信息结构化 Schema
    基于现有 TenderNotice 模型设计
    """
    title: Optional[str] = None
    tenderer: Optional[str] = None
    winner: Optional[str] = None
    budget_amount: Optional[Decimal] = None
    budget_unit: str = '元'
    currency: str = 'CNY'
    publish_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None
    project_number: Optional[str] = None
    region: Optional[str] = None
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    description: Optional[str] = None
    notice_type: str = 'bidding'  # 'bidding', 'win', 'change'
    source_url: str = ''
    source_site: str = ''

    # 元数据
    extraction_method: str = 'unknown'
    extraction_confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'title': self.title,
            'tenderer': self.tenderer,
            'winner': self.winner,
            'budget_amount': self.budget_amount,
            'budget_unit': self.budget_unit,
            'currency': self.currency,
            'publish_date': self.publish_date,
            'deadline_date': self.deadline_date,
            'project_number': self.project_number,
            'region': self.region,
            'industry': self.industry,
            'contact_person': self.contact_person,
            'contact_phone': self.contact_phone,
            'description': self.description,
            'notice_type': self.notice_type,
            'source_url': self.source_url,
            'source_site': self.source_site,
            'extraction_method': self.extraction_method,
            'extraction_confidence': self.extraction_confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TenderNoticeSchema':
        """从字典创建"""
        return cls(**{
            k: v for k, v in data.items()
            if k in cls.__dataclass_fields__
        })

    def to_model_fields(self) -> Dict[str, Any]:
        """
        转换为 TenderNotice 模型字段
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
            'source_url': self.source_url,
            'source_site': self.source_site,
            'notice_type': self.notice_type,
            'project_name': self.title or '',
            'region': self.region or '',
            'industry': self.industry or '',
            'winner': self.winner or '',
        }
