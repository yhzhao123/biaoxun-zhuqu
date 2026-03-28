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

    # 源名称
    source_name: str = ""

    # 分页配置
    pagination: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExtractionStrategy':
        """从字典创建 ExtractionStrategy"""
        return cls(
            site_type=data.get('site_type', 'static'),
            list_strategy=data.get('list_strategy', {}),
            detail_strategy=data.get('detail_strategy', {}),
            anti_detection=data.get('anti_detection', {'delay_seconds': 1.5, 'headers': {}}),
            max_pages=data.get('max_pages', 5),
            api_config=data.get('api_config'),
            source_name=data.get('source_name', ''),
            pagination=data.get('pagination', {}),
        )


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
class TenderItem:
    """
    招标标的/采购物品信息
    """
    name: str = ''  # 物品名称
    specification: str = ''  # 规格型号
    quantity: Optional[float] = None  # 数量
    unit: str = ''  # 单位（台、套、个等）
    budget_unit_price: Optional[Decimal] = None  # 预算单价
    budget_total_price: Optional[Decimal] = None  # 预算总价
    category: str = ''  # 物品类别/品目
    technical_requirements: str = ''  # 技术要求/参数
    delivery_requirements: str = ''  # 交付要求

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'specification': self.specification,
            'quantity': self.quantity,
            'unit': self.unit,
            'budget_unit_price': self.budget_unit_price,
            'budget_total_price': self.budget_total_price,
            'category': self.category,
            'technical_requirements': self.technical_requirements,
            'delivery_requirements': self.delivery_requirements,
        }


@dataclass
class TechnicalParameter:
    """
    技术参数
    """
    name: str = ''  # 参数名称
    value: str = ''  # 参数值/要求
    category: str = ''  # 参数类别（性能指标、功能要求、接口要求等）
    is_mandatory: bool = True  # 是否必须满足

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': self.value,
            'category': self.category,
            'is_mandatory': self.is_mandatory,
        }


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

    # 标的/采购物品列表
    items: List[TenderItem] = field(default_factory=list)

    # 技术参数列表
    technical_parameters: List[TechnicalParameter] = field(default_factory=list)

    # 其他重要信息
    qualification_requirements: str = ''  # 投标人资格要求
    delivery_period: str = ''  # 交付期限
    warranty_period: str = ''  # 质保期
    payment_terms: str = ''  # 付款方式
    evaluation_method: str = ''  # 评标方法

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
            'items': [item.to_dict() for item in self.items],
            'technical_parameters': [param.to_dict() for param in self.technical_parameters],
            'qualification_requirements': self.qualification_requirements,
            'delivery_period': self.delivery_period,
            'warranty_period': self.warranty_period,
            'payment_terms': self.payment_terms,
            'evaluation_method': self.evaluation_method,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TenderNoticeSchema':
        """从字典创建"""
        # 处理标的列表
        items_data = data.get('items', [])
        items = [TenderItem(**item) for item in items_data]

        # 处理技术参数列表
        params_data = data.get('technical_parameters', [])
        technical_parameters = [TechnicalParameter(**param) for param in params_data]

        # 过滤掉不在类定义中的字段
        valid_fields = {k: v for k, v in data.items()
                        if k in cls.__dataclass_fields__ and k not in ('items', 'technical_parameters')}

        return cls(
            **valid_fields,
            items=items,
            technical_parameters=technical_parameters
        )

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
            # PDF相关字段
            'main_pdf_content': self.description or '',  # 使用description存储PDF内容
            'main_pdf_url': self.source_url or '',
            'qualification_requirements': self.qualification_requirements or '',
            'delivery_period': self.delivery_period or '',
            'warranty_period': self.warranty_period or '',
            'payment_terms': self.payment_terms or '',
            'evaluation_method': self.evaluation_method or '',
            'extraction_method': self.extraction_method or 'unknown',
            'extraction_confidence': self.extraction_confidence or 0.0,
        }
