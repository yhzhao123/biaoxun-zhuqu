"""
Field Optimization Agent - 字段优化代理

通过充分利用列表页数据来减少LLM调用次数，优化字段提取效率。

核心功能：
1. 从列表项中预提取所有可能的字段
2. 基于字段映射配置进行数据转换
3. 仅对无法从列表提取的字段调用LLM
4. 智能合并列表数据和LLM提取结果
5. 使用正则预处理提取常见模式（日期、金额等）
"""

import re
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class FieldOptimizationConfig:
    """
    字段优化配置

    定义字段提取的优化策略和映射规则。
    """

    # 必需字段列表
    required_fields: List[str] = field(default_factory=lambda: [
        'title', 'tenderer', 'publish_date', 'budget_amount'
    ])

    # 列表页字段到详情页字段的映射
    # key: 详情页字段名, value: 列表页字段名
    list_to_detail_mapping: Dict[str, str] = field(default_factory=lambda: {
        'title': 'title',
        'tenderer': 'purchaser',
        'tenderer': 'buyer',
        'tenderer': 'procurement_unit',
        'publish_date': 'publish_date',
        'publish_date': 'date',
        'publish_date': 'pub_date',
        'budget_amount': 'budget',
        'budget_amount': 'amount',
        'deadline_date': 'deadline',
        'deadline_date': 'end_date',
        'region': 'region',
        'region': 'province',
        'region': 'city',
        'project_number': 'project_no',
        'project_number': 'project_code',
        'industry': 'industry',
        'industry': 'category',
    })

    # 是否启用正则预处理
    use_regex_preprocessing: bool = True

    # LLM回退阈值：置信度低于此值时触发LLM提取
    llm_fallback_threshold: float = 0.5

    # 字段置信度权重配置
    field_confidence_weights: Dict[str, float] = field(default_factory=lambda: {
        'title': 1.0,
        'tenderer': 0.9,
        'publish_date': 0.9,
        'budget_amount': 0.85,
        'deadline_date': 0.8,
        'project_number': 0.85,
        'region': 0.75,
        'industry': 0.7,
        'description': 0.6,
    })

    # 列表页字段的默认置信度
    list_field_default_confidence: float = 0.7

    # HTML字段选择器映射（用于从HTML中提取）
    html_field_selectors: Dict[str, List[str]] = field(default_factory=lambda: {
        'title': ['h1', '.title', '.article-title', '[class*="title"]'],
        'publish_date': ['time', '.date', '.publish-date', '.pub-time'],
        'budget_amount': ['.budget', '.amount', '[class*="budget"]', '[class*="amount"]'],
        'tenderer': ['.purchaser', '.buyer', '.tenderer', '[class*="purchaser"]'],
    })

    def get_list_field_for_detail(self, detail_field: str) -> Optional[str]:
        """
        获取详情字段对应的列表字段名

        支持多对一映射，返回第一个匹配的列表字段名
        """
        # 直接匹配
        if detail_field in self.list_to_detail_mapping:
            return self.list_to_detail_mapping[detail_field]

        # 反向查找：找到映射到该详情字段的所有列表字段
        list_fields = [
            list_field for list_field, detail in self.list_to_detail_mapping.items()
            if detail == detail_field
        ]

        return list_fields[0] if list_fields else None


@dataclass
class ExtractionResult:
    """
    提取结果封装

    包含提取的数据、置信度和来源信息
    """

    data: Dict[str, Any] = field(default_factory=dict)
    confidence: Dict[str, float] = field(default_factory=dict)
    sources: Dict[str, str] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    llm_called: bool = False
    llm_fields_requested: List[str] = field(default_factory=list)

    def get_confidence_score(self, field: str) -> float:
        """获取指定字段的置信度"""
        return self.confidence.get(field, 0.0)

    def get_field_source(self, field: str) -> str:
        """获取指定字段的来源"""
        return self.sources.get(field, 'unknown')

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'data': self.data,
            'confidence': self.confidence,
            'sources': self.sources,
            'missing_fields': self.missing_fields,
            'llm_called': self.llm_called,
            'llm_fields_requested': self.llm_fields_requested,
        }


class FieldOptimizationAgent:
    """
    字段优化代理

    通过最大化利用列表页数据，最小化LLM调用次数，
    实现高效的招标信息字段提取。

    工作流程：
    1. 从列表项提取可用字段
    2. 使用正则预处理HTML提取明显字段
    3. 确定仍需LLM提取的字段
    4. 调用LLM提取缺失字段（如需要）
    5. 智能合并所有来源的数据
    """

    # 日期解析正则模式
    DATE_PATTERNS: List[Tuple[str, str]] = [
        (r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?', '%Y-%m-%d'),
        (r'(\d{4})(\d{2})(\d{2})', '%Y%m%d'),
        (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y-%m-%d'),
        (r'(\d{4})\.(\d{1,2})\.(\d{1,2})', '%Y-%m-%d'),
    ]

    # 金额解析正则模式
    AMOUNT_PATTERNS: List[Tuple[str, Optional[str]]] = [
        (r'[¥￥]?\s*([\d,]+\.?\d*)\s*万[元]?', '10000'),
        (r'[¥￥]?\s*([\d,]+\.?\d*)\s*亿[元]?', '100000000'),
        (r'[¥￥]?\s*([\d,]+\.?\d*)\s*[元]', '1'),
        (r'(?:预算|金额|中标金额|成交金额)[：:]\s*[¥￥]?\s*([\d,]+\.?\d*)', None),
    ]

    # 招标人/采购人关键词
    TENDERER_KEYWORDS: List[str] = [
        '采购人', '招标人', '采购单位', '招标单位', '业主',
        '采购方', '招标方', '需求方', '甲方', '发包人'
    ]

    def __init__(self, config: Optional[FieldOptimizationConfig] = None):
        """
        初始化字段优化代理

        Args:
            config: 字段优化配置，使用默认配置如果未提供
        """
        self.config = config or FieldOptimizationConfig()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def optimize_extraction(
        self,
        list_item: Dict[str, Any],
        html: str,
        url: str,
        llm_extractor: Optional[Any] = None
    ) -> ExtractionResult:
        """
        主优化提取方法

        协调整个提取流程：列表提取 -> 正则预处理 -> LLM补充 -> 智能合并

        Args:
            list_item: 列表页数据项
            html: 详情页HTML内容
            url: 页面URL（用于日志）
            llm_extractor: LLM提取器实例（可选）

        Returns:
            ExtractionResult: 提取结果
        """
        self.logger.info(f"Starting optimized extraction for URL: {url}")

        result = ExtractionResult()

        # 步骤1: 从列表项提取字段
        list_data = self.extract_from_list(list_item)
        if list_data:
            self._add_to_result(result, list_data, 'list_item')
            self.logger.debug(f"Extracted from list item: {list(list_data.keys())}")

        # 步骤2: 正则预处理HTML
        if self.config.use_regex_preprocessing and html:
            regex_data = self.preprocess_with_regex(html)
            if regex_data:
                self._add_to_result(result, regex_data, 'regex')
                self.logger.debug(f"Extracted from regex: {list(regex_data.keys())}")

        # 步骤3: 确定缺失字段
        missing_fields = self.determine_missing_fields(
            result.data,
            self.config.required_fields
        )

        # 步骤4: 如有必要，调用LLM提取
        if missing_fields and llm_extractor:
            result.missing_fields = missing_fields
            result.llm_fields_requested = missing_fields

            try:
                llm_data = await llm_extractor.extract(html, url)
                # Handle both dict and TenderNoticeSchema returns
                if hasattr(llm_data, 'to_dict'):
                    llm_data = llm_data.to_dict()
                if llm_data and not llm_data.get('error'):
                    # 过滤只保留缺失的字段
                    filtered_llm_data = {
                        k: v for k, v in llm_data.items()
                        if k in missing_fields or k not in result.data
                    }
                    self._add_to_result(result, filtered_llm_data, 'llm')
                    result.llm_called = True
                    self.logger.debug(f"Extracted from LLM: {list(filtered_llm_data.keys())}")
            except Exception as e:
                self.logger.error(f"LLM extraction failed: {e}")

        # 步骤5: 最终验证和清理
        result.data = self._normalize_and_validate(result.data)

        self.logger.info(
            f"Extraction completed. Fields: {len(result.data)}, "
            f"LLM called: {result.llm_called}, "
            f"Missing: {result.missing_fields}"
        )

        return result

    def extract_from_list(
        self,
        list_item: Dict[str, Any],
        field_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        从列表项数据中提取字段

        根据字段映射配置，将列表字段转换为详情页字段

        Args:
            list_item: 列表页数据项
            field_mapping: 自定义字段映射（覆盖配置中的映射）

        Returns:
            提取的字段字典
        """
        if not list_item:
            return {}

        mapping = field_mapping or self.config.list_to_detail_mapping
        result: Dict[str, Any] = {}

        # 构建反向映射（列表字段 -> 详情字段）
        reverse_mapping: Dict[str, List[str]] = {}
        for detail_field, list_field in mapping.items():
            if list_field not in reverse_mapping:
                reverse_mapping[list_field] = []
            reverse_mapping[list_field].append(detail_field)

        # 遍历列表项的所有字段
        for list_field_name, value in list_item.items():
            if value is None or value == '':
                continue

            # 直接匹配详情字段名
            if list_field_name in self.config.required_fields:
                result[list_field_name] = value
                continue

            # 通过映射找到对应的详情字段
            if list_field_name in reverse_mapping:
                for detail_field in reverse_mapping[list_field_name]:
                    if detail_field not in result:  # 避免覆盖
                        parsed_value = self._parse_field_value(
                            detail_field, value
                        )
                        result[detail_field] = parsed_value

            # 尝试字段名相似度匹配（简单的子字符串匹配）
            for required_field in self.config.required_fields:
                if required_field not in result:
                    if self._field_names_match(list_field_name, required_field):
                        parsed_value = self._parse_field_value(
                            required_field, value
                        )
                        result[required_field] = parsed_value
                        break

        return result

    def determine_missing_fields(
        self,
        prefilled_data: Dict[str, Any],
        required_fields: List[str]
    ) -> List[str]:
        """
        确定仍需提取的字段

        检查已填充的数据，返回需要LLM提取的字段列表

        Args:
            prefilled_data: 已预填充的数据
            required_fields: 必需字段列表

        Returns:
            缺失字段列表
        """
        missing: List[str] = []

        for field in required_fields:
            value = prefilled_data.get(field)

            # 检查字段是否缺失或无效
            if value is None:
                missing.append(field)
                continue

            # 检查字符串字段是否为空
            if isinstance(value, str) and not value.strip():
                missing.append(field)
                continue

            # 检查数字字段是否为0或负数
            if isinstance(value, (int, float, Decimal)):
                if value <= 0:
                    missing.append(field)
                    continue

            # 检查置信度是否低于阈值
            confidence = prefilled_data.get(f'_{field}_confidence', 1.0)
            if confidence < self.config.llm_fallback_threshold:
                missing.append(field)
                continue

        return missing

    def merge_results(
        self,
        list_data: Dict[str, Any],
        llm_data: Dict[str, Any],
        list_confidence: Optional[Dict[str, float]] = None
    ) -> Tuple[Dict[str, Any], Dict[str, float], Dict[str, str]]:
        """
        智能合并列表数据和LLM数据

        根据置信度评分决定使用哪个来源的数据

        Args:
            list_data: 从列表提取的数据
            llm_data: 从LLM提取的数据
            list_confidence: 列表数据的置信度（可选）

        Returns:
            Tuple[合并数据, 置信度字典, 来源字典]
        """
        merged: Dict[str, Any] = {}
        confidence: Dict[str, float] = {}
        sources: Dict[str, str] = {}

        # 所有可能的字段
        all_fields = set(list_data.keys()) | set(llm_data.keys())

        for field in all_fields:
            list_value = list_data.get(field)
            llm_value = llm_data.get(field)

            list_conf = list_confidence.get(field, self.config.list_field_default_confidence) \
                if list_confidence else self.config.list_field_default_confidence
            llm_conf = self.config.field_confidence_weights.get(field, 0.8)

            # 决策逻辑
            if list_value is not None and llm_value is not None:
                # 两者都有值，选择置信度高的
                if list_conf >= llm_conf:
                    merged[field] = list_value
                    confidence[field] = list_conf
                    sources[field] = 'list'
                else:
                    merged[field] = llm_value
                    confidence[field] = llm_conf
                    sources[field] = 'llm'
            elif list_value is not None:
                # 只有列表数据
                merged[field] = list_value
                confidence[field] = list_conf
                sources[field] = 'list'
            elif llm_value is not None:
                # 只有LLM数据
                merged[field] = llm_value
                confidence[field] = llm_conf
                sources[field] = 'llm'

        return merged, confidence, sources

    def preprocess_with_regex(self, html: str) -> Dict[str, Any]:
        """
        使用正则预处理提取明显字段

        从HTML中提取日期、金额等具有明显模式的字段

        Args:
            html: HTML内容

        Returns:
            提取的字段字典
        """
        if not html:
            return {}

        result: Dict[str, Any] = {}

        # 解析HTML
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
        except Exception as e:
            self.logger.warning(f"Failed to parse HTML: {e}")
            text = html

        # 提取发布日期
        publish_date = self._extract_date_from_text(text)
        if publish_date:
            result['publish_date'] = publish_date
            result['_publish_date_confidence'] = 0.85

        # 提取预算金额
        budget = self._extract_amount_from_text(text)
        if budget:
            result['budget_amount'] = budget
            result['_budget_amount_confidence'] = 0.8

        # 提取招标人/采购人
        tenderer = self._extract_tenderer_from_text(text)
        if tenderer:
            result['tenderer'] = tenderer
            result['_tenderer_confidence'] = 0.75

        # 提取项目编号
        project_number = self._extract_project_number(text)
        if project_number:
            result['project_number'] = project_number
            result['_project_number_confidence'] = 0.8

        return result

    def _add_to_result(
        self,
        result: ExtractionResult,
        data: Dict[str, Any],
        source: str
    ) -> None:
        """
        将数据添加到结果中

        处理置信度字段并更新结果对象
        """
        for key, value in data.items():
            # 跳过内部置信度字段（单独处理）
            if key.startswith('_') and key.endswith('_confidence'):
                field_name = key[1:-11]  # 去掉前缀和后缀
                result.confidence[field_name] = value
                continue

            # 只添加有效值
            if value is not None and value != '':
                # 如果字段已存在，保留现有值（先到先得的策略）
                if key not in result.data:
                    result.data[key] = value
                    result.sources[key] = source

                    # 设置默认置信度
                    if key not in result.confidence:
                        if source == 'list_item':
                            result.confidence[key] = self.config.list_field_default_confidence
                        elif source == 'regex':
                            result.confidence[key] = 0.75
                        elif source == 'llm':
                            result.confidence[key] = self.config.field_confidence_weights.get(key, 0.8)

    def _parse_field_value(self, field_name: str, value: Any) -> Any:
        """
        根据字段类型解析值

        Args:
            field_name: 字段名
            value: 原始值

        Returns:
            解析后的值
        """
        if value is None:
            return None

        # 日期字段
        if 'date' in field_name.lower():
            parsed_date = self._parse_date_value(value)
            if parsed_date:
                return parsed_date

        # 金额字段
        if field_name in ['budget_amount', 'amount', 'budget']:
            parsed_amount = self._parse_amount_value(value)
            if parsed_amount is not None:
                return parsed_amount

        return value

    def _parse_date_value(self, value: Any) -> Optional[datetime]:
        """解析日期值"""
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            value = value.strip()

            for pattern, fmt in self.DATE_PATTERNS:
                match = re.search(pattern, value)
                if match:
                    try:
                        if fmt == '%Y%m%d':
                            return datetime(
                                int(match.group(1)),
                                int(match.group(2)),
                                int(match.group(3))
                            )
                        else:
                            return datetime.strptime(
                                f"{match.group(1)}-{match.group(2)}-{match.group(3)}",
                                fmt
                            )
                    except (ValueError, AttributeError):
                        continue

        return None

    def _parse_amount_value(self, value: Any) -> Optional[Decimal]:
        """解析金额值"""
        if isinstance(value, (int, float)):
            return Decimal(str(value))

        if isinstance(value, Decimal):
            return value

        if isinstance(value, str):
            value = value.strip()

            # 移除货币符号和千分位分隔符
            cleaned = re.sub(r'[¥￥,\s]', '', value)

            # 尝试直接解析
            try:
                return Decimal(cleaned)
            except InvalidOperation:
                pass

            # 使用正则提取
            return self._extract_amount_from_text(value)

        return None

    def _extract_date_from_text(self, text: str) -> Optional[datetime]:
        """从文本中提取日期"""
        if not text:
            return None

        # 优先查找发布日期关键词附近的日期
        date_keywords = [
            '发布时间', '发布日期', '公告日期', '发表时间',
            'Publish Date', 'Published', 'Date:'
        ]

        for keyword in date_keywords:
            pattern = rf'{keyword}[：:]\s*(\d{{4}}[年/-]\d{{1,2}}[月/-]\d{{1,2}}[日]?)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_date_value(match.group(1))

        # 如果没有关键词，搜索整个文本中的日期模式
        for pattern, fmt in self.DATE_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return self._parse_date_value(match.group(0))

        return None

    def _extract_amount_from_text(self, text: str) -> Optional[Decimal]:
        """从文本中提取金额"""
        if not text:
            return None

        # 优先查找预算关键词附近的金额
        amount_keywords = [
            '预算金额', '采购预算', '项目预算', '中标金额',
            '成交金额', '金额', 'Budget', 'Amount'
        ]

        for keyword in amount_keywords:
            pattern = rf'{keyword}[：:]\s*[¥￥]?\s*([\d,]+\.?\d*)\s*(万元|万|亿元|亿|元)?'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                unit = match.group(2) if len(match.groups()) > 1 else None

                try:
                    amount = Decimal(amount_str)

                    # 单位转换
                    if unit in ['亿', '亿元']:
                        amount *= Decimal('100000000')
                    elif unit in ['万', '万元']:
                        amount *= Decimal('10000')

                    return amount
                except (InvalidOperation, ValueError):
                    continue

        # 如果没有关键词，使用通用模式
        for pattern, multiplier in self.AMOUNT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = Decimal(amount_str)

                    # 应用乘数
                    if multiplier:
                        amount *= Decimal(multiplier)

                    return amount
                except (InvalidOperation, ValueError):
                    continue

        return None

    def _extract_tenderer_from_text(self, text: str) -> Optional[str]:
        """从文本中提取招标人/采购人"""
        if not text:
            return None

        for keyword in self.TENDERER_KEYWORDS:
            # 模式：关键词：值
            pattern = rf'{keyword}[：:]\s*([^\n，。；;\s]+(?:[\u4e00-\u9fa5]+))'
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                # 清理常见后缀
                value = re.sub(r'\s*(联系人|联系电话|地址|邮编).*', '', value)
                if len(value) >= 2:
                    return value

            # 模式：关键词是/为/为：值
            pattern = rf'{keyword}(?:是|为)[：:\s]*([^\n，。；;]+)'
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                value = re.sub(r'\s*(联系人|联系电话|地址|邮编).*', '', value)
                if len(value) >= 2:
                    return value

        return None

    def _extract_project_number(self, text: str) -> Optional[str]:
        """从文本中提取项目编号"""
        if not text:
            return None

        # 常见项目编号模式
        patterns = [
            r'项目编号[：:]\s*([A-Z0-9\-]+)',
            r'招标编号[：:]\s*([A-Z0-9\-]+)',
            r'采购编号[：:]\s*([A-Z0-9\-]+)',
            r'项目代码[：:]\s*([A-Z0-9\-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return None

    def _field_names_match(self, field1: str, field2: str) -> bool:
        """
        检查两个字段名是否匹配

        使用简单的相似度算法
        """
        f1 = field1.lower().replace('_', '').replace('-', '')
        f2 = field2.lower().replace('_', '').replace('-', '')

        # 完全匹配
        if f1 == f2:
            return True

        # 包含关系
        if f1 in f2 or f2 in f1:
            return True

        # 常见的别名映射
        aliases = {
            'tenderer': ['purchaser', 'buyer', 'procurementunit', 'owner'],
            'publishdate': ['date', 'pubdate', 'published'],
            'budgetamount': ['budget', 'amount', 'price'],
            'deadlinedate': ['deadline', 'enddate', 'closedate'],
        }

        for canonical, alias_list in aliases.items():
            if f1 == canonical or f1 in alias_list:
                if f2 == canonical or f2 in alias_list:
                    return True

        return False

    def _normalize_and_validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化和验证数据

        确保字段类型正确，移除无效值
        """
        normalized: Dict[str, Any] = {}

        for key, value in data.items():
            # 跳过内部字段
            if key.startswith('_'):
                continue

            if value is None:
                continue

            # 字符串字段：去除空白
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    continue

            normalized[key] = value

        return normalized

    def calculate_savings(
        self,
        result: ExtractionResult
    ) -> Dict[str, Union[int, float, bool]]:
        """
        计算LLM调用节省统计

        Args:
            result: 提取结果

        Returns:
            节省统计信息
        """
        total_required = len(self.config.required_fields)
        from_list = sum(1 for s in result.sources.values() if s == 'list_item')
        from_regex = sum(1 for s in result.sources.values() if s == 'regex')
        from_llm = sum(1 for s in result.sources.values() if s == 'llm')

        # 估算节省（假设每个LLM调用有一定成本）
        llm_cost_per_call = 0.01  # 示例成本
        saved_calls = from_list + from_regex

        return {
            'total_fields_required': total_required,
            'fields_from_list': from_list,
            'fields_from_regex': from_regex,
            'fields_from_llm': from_llm,
            'llm_call_avoided': not result.llm_called,
            'estimated_cost_saved': saved_calls * llm_cost_per_call,
            'optimization_rate': (from_list + from_regex) / total_required if total_required > 0 else 0,
        }
