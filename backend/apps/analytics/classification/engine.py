"""
智能分类引擎 - Cycle 27
实现招标信息的自动分类功能
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import re
from datetime import datetime


class ClassificationType(Enum):
    """分类类型"""
    TENDERER = "tenderer"        # 招标人
    REGION = "region"            # 地区
    INDUSTRY = "industry"        # 行业
    AMOUNT = "amount"            # 金额区间
    DATE = "date"                # 时间


@dataclass
class ClassificationResult:
    """分类结果"""
    original_value: str
    normalized_value: str
    category: str
    confidence: float
    classification_type: ClassificationType
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenderClassification:
    """招标信息分类"""
    tender_id: str
    tenderer_category: Optional[ClassificationResult] = None
    region_category: Optional[ClassificationResult] = None
    industry_category: Optional[ClassificationResult] = None
    amount_category: Optional[ClassificationResult] = None
    created_at: Optional[str] = None


class TenderClassifier:
    """招标信息分类器"""

    def __init__(self):
        """初始化分类器"""
        self.tenderer_rules = TendererClassificationRules()
        self.region_rules = RegionClassificationRules()
        self.industry_rules = IndustryClassificationRules()
        self.amount_rules = AmountClassificationRules()

    def classify_tender(
        self,
        tender_id: str,
        tenderer: str,
        region: str,
        industry: str,
        amount: Optional[float] = None
    ) -> TenderClassification:
        """
        对招标信息进行分类

        Args:
            tender_id: 招标ID
            tenderer: 招标人名称
            region: 地区名称
            industry: 行业名称
            amount: 预算金额

        Returns:
            TenderClassification: 分类结果
        """
        classification = TenderClassification(
            tender_id=tender_id,
            created_at=datetime.now().isoformat()
        )

        # 分类招标人
        classification.tenderer_category = self.classify_tenderer(tenderer)

        # 分类地区
        classification.region_category = self.classify_region(region)

        # 分类行业
        classification.industry_category = self.classify_industry(industry)

        # 分类金额（如果有）
        if amount is not None:
            classification.amount_category = self.amount_rules.classify(amount)

        return classification

    def classify_tenderer(self, tenderer: str) -> ClassificationResult:
        """分类招标人"""
        return self.tenderer_rules.classify(tenderer)

    def classify_region(self, region: str) -> ClassificationResult:
        """分类地区"""
        return self.region_rules.classify(region)

    def classify_industry(self, industry: str) -> ClassificationResult:
        """分类行业"""
        return self.industry_rules.classify(industry)


class TendererClassificationRules:
    """招标人分类规则"""

    # 常见公司后缀及其规范化形式
    COMPANY_SUFFIXES = [
        (r'通信集团公司', ''),
        (r'通信集团', ''),
        (r'股份有限公司', '股份'),
        (r'股份公司', '股份'),
        (r'有限责任公司', ''),
        (r'有限公司', ''),
        (r'集团公司', ''),
        (r'集团', ''),
        (r'总公司', ''),
        (r'公司', ''),
    ]

    # 企业类型关键词
    ENTERPRISE_TYPES = {
        '国有企业': ['中国移动', '中国联通', '中国电信', '中石油', '中石化', '国家电网', '南方电网', '中铁', '中建', '中交'],
        '政府': ['政府', '人民政府', '街道办', '开发区管委会', '财政局', '教育局', '卫生局'],
        '事业单位': ['医院', '学校', '大学', '研究院', '研究所', '中心'],
        '民营企业': ['腾讯', '阿里巴巴', '华为', '小米', '京东'],
    }

    def classify(self, tenderer: str) -> ClassificationResult:
        """分类招标人"""
        if not tenderer:
            return ClassificationResult(
                original_value="",
                normalized_value="",
                category="未知",
                confidence=0.0,
                classification_type=ClassificationType.TENDERER
            )

        # 规范化名称
        normalized = self._normalize_name(tenderer)

        # 确定企业类型
        category, confidence = self._determine_type(normalized)

        return ClassificationResult(
            original_value=tenderer,
            normalized_value=normalized,
            category=category,
            confidence=confidence,
            classification_type=ClassificationType.TENDERER
        )

    def _normalize_name(self, name: str) -> str:
        """规范化公司名称"""
        normalized = name
        for pattern, replacement in self.COMPANY_SUFFIXES:
            normalized = re.sub(pattern, replacement, normalized)
        return normalized.strip()

    def _determine_type(self, normalized_name: str) -> tuple:
        """确定企业类型"""
        for category, keywords in self.ENTERPRISE_TYPES.items():
            for keyword in keywords:
                if keyword in normalized_name:
                    return category, 0.9
        return "其他企业", 0.6


class RegionClassificationRules:
    """地区分类规则"""

    # 地区映射
    REGION_MAP = {
        # 华北地区
        '北京': ('华北地区', 0.98),
        '天津': ('华北地区', 0.98),
        '河北': ('华北地区', 0.98),
        '山西': ('华北地区', 0.98),
        '内蒙古': ('华北地区', 0.98),
        # 华东地区
        '上海': ('华东地区', 0.98),
        '江苏': ('华东地区', 0.98),
        '浙江': ('华东地区', 0.98),
        '安徽': ('华东地区', 0.98),
        '福建': ('华东地区', 0.98),
        '江西': ('华东地区', 0.98),
        '山东': ('华东地区', 0.98),
        # 华南地区
        '广东': ('华南地区', 0.98),
        '广西': ('华南地区', 0.98),
        '海南': ('华南地区', 0.98),
        # 华中地区
        '河南': ('华中地区', 0.98),
        '湖北': ('华中地区', 0.98),
        '湖南': ('华中地区', 0.98),
        # 西南地区
        '重庆': ('西南地区', 0.98),
        '四川': ('西南地区', 0.98),
        '贵州': ('西南地区', 0.98),
        '云南': ('西南地区', 0.98),
        '西藏': ('西南地区', 0.98),
        # 西北地区
        '陕西': ('西北地区', 0.98),
        '甘肃': ('西北地区', 0.98),
        '青海': ('西北地区', 0.98),
        '宁夏': ('西北地区', 0.98),
        '新疆': ('西北地区', 0.98),
        # 东北地区
        '辽宁': ('东北地区', 0.98),
        '吉林': ('东北地区', 0.98),
        '黑龙江': ('东北地区', 0.98),
    }

    def classify(self, region: str) -> ClassificationResult:
        """分类地区"""
        if not region:
            return ClassificationResult(
                original_value="",
                normalized_value="",
                category="未知",
                confidence=0.0,
                classification_type=ClassificationType.REGION
            )

        # 规范化地区名称
        normalized = self._normalize_region(region)

        # 查找地区分类
        if normalized in self.REGION_MAP:
            category, confidence = self.REGION_MAP[normalized]
        else:
            category, confidence = "未知", 0.3

        return ClassificationResult(
            original_value=region,
            normalized_value=normalized,
            category=category,
            confidence=confidence,
            classification_type=ClassificationType.REGION
        )

    def _normalize_region(self, region: str) -> str:
        """规范化地区名称"""
        # 移除"市"、"省"等后缀
        normalized = region.replace('市', '').replace('省', '').replace('自治区', '').replace('地区', '')
        return normalized.strip()


class IndustryClassificationRules:
    """行业分类规则"""

    # 行业映射表
    INDUSTRY_MAP = {
        '信息技术': '信息传输、软件和信息技术服务业',
        '软件开发': '信息传输、软件和信息技术服务业',
        '互联网': '信息传输、软件和信息技术服务业',
        '电信': '信息传输、软件和信息技术服务业',
        '通信': '信息传输、软件和信息技术服务业',
        '建筑': '建筑业',
        '工程': '建筑业',
        '房地产': '房地产业',
        '制造': '制造业',
        '医疗': '卫生和社会工作',
        '教育': '教育',
        '金融': '金融业',
        '交通': '交通运输、仓储和邮政业',
        '能源': '电力、热力、燃气及水生产和供应业',
        '电力': '电力、热力、燃气及水生产和供应业',
    }

    def classify(self, industry: str) -> ClassificationResult:
        """分类行业"""
        if not industry:
            return ClassificationResult(
                original_value="",
                normalized_value="",
                category="未知",
                confidence=0.0,
                classification_type=ClassificationType.INDUSTRY
            )

        # 查找行业分类
        category = self._map_industry(industry)
        confidence = 0.85 if category != "未知" else 0.3

        return ClassificationResult(
            original_value=industry,
            normalized_value=industry,
            category=category,
            confidence=confidence,
            classification_type=ClassificationType.INDUSTRY
        )

    def _map_industry(self, industry: str) -> str:
        """映射行业到标准分类"""
        for key, value in self.INDUSTRY_MAP.items():
            if key in industry:
                return value
        return "未知"


class AmountClassificationRules:
    """金额分类规则"""

    def classify(self, amount: float) -> ClassificationResult:
        """分类金额"""
        if amount < 100000:  # < 10万
            category = "小额 (<10万)"
        elif amount < 1000000:  # < 100万
            category = "中额 (10-100万)"
        elif amount < 10000000:  # < 1000万
            category = "大额 (100-1000万)"
        else:  # >= 1000万
            category = "超大额 (>=1000万)"

        return ClassificationResult(
            original_value=str(amount),
            normalized_value=str(amount),
            category=category,
            confidence=0.95,
            classification_type=ClassificationType.AMOUNT
        )
