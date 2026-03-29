"""
FieldExtractorTool - 字段提取工具

将 FieldExtractorAgent 封装为 Deer-Flow Tool
重点解决招标人提取不准确的问题
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from decimal import Decimal
import logging
import re

from apps.crawler.agents.agents.field_extractor import FieldExtractorAgent
from apps.crawler.agents.schema import TenderNoticeSchema
from apps.crawler.deer_flow.config import ConfigManager

logger = logging.getLogger(__name__)


@dataclass
class FieldExtractionResult:
    """字段提取结果"""
    schema: TenderNoticeSchema
    success: bool
    extraction_method: str  # 'llm', 'regex', 'fallback'
    confidence: float
    field_confidences: Dict[str, float] = field(default_factory=dict)
    missing_fields: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "extraction_method": self.extraction_method,
            "confidence": self.confidence,
            "field_confidences": self.field_confidences,
            "missing_fields": self.missing_fields,
            "warnings": self.warnings,
            "error_message": self.error_message,
            "data": {
                "title": self.schema.title,
                "tenderer": self.schema.tenderer,
                "winner": self.schema.winner,
                "budget_amount": self.schema.budget_amount,
                "publish_date": self.schema.publish_date,
                "deadline_date": self.schema.deadline_date,
                "project_number": self.schema.project_number,
                "region": self.schema.region,
                "industry": self.schema.industry,
                "contact_person": self.schema.contact_person,
                "contact_phone": self.schema.contact_phone,
                "notice_type": self.schema.notice_type,
            } if self.schema else {},
        }

    def is_high_quality(self) -> bool:
        """检查是否是高质量结果"""
        return self.success and self.confidence >= 0.8

    def is_medium_quality(self) -> bool:
        """检查是否是中质量结果"""
        return self.success and 0.6 <= self.confidence < 0.8

    def is_low_quality(self) -> bool:
        """检查是否是低质量结果"""
        return not self.success or self.confidence < 0.6


class FieldExtractorTool:
    """
    字段提取工具

    封装 FieldExtractorAgent，提供统一的 Tool 接口
    重点优化招标人(tenderer)提取准确性
    """

    # 招标人提取模式（增强版）
    TENDERER_PATTERNS = [
        # 主要模式 - 标准格式
        r'采\s*购\s*人[：:\s]*([^\n]{2,50}?)(?=\s|$|联系人|电话|地址)',
        r'招\s*标\s*人[：:\s]*([^\n]{2,50}?)(?=\s|$|联系人|电话|地址)',
        r'采\s*购\s*单\s*位[：:\s]*([^\n]{2,50}?)(?=\s|$|联系人|电话|地址)',
        r'招\s*标\s*单\s*位[：:\s]*([^\n]{2,50}?)(?=\s|$|联系人|电话|地址)',
        # 替代模式 - 简化格式
        r'采购人[：:\s]*([^\n]{2,50}?)(?=\n|联系人|电话)',
        r'招标人[：:\s]*([^\n]{2,50}?)(?=\n|联系人|电话)',
        # 宽松模式 - 可能带空格
        r'采\s*购\s*人[:：]\s*([^\n]{2,50}?)\s*(?=联系人|电话|$)',
        r'招\s*标\s*人[:：]\s*([^\n]{2,50}?)\s*(?=联系人|电话|$)',
    ]

    # 联系人提取模式
    CONTACT_PERSON_PATTERNS = [
        r'联\s*系\s*人[：:\s]*([^\n]{2,20}?)(?=\s|$|电话|手机)',
        r'经\s*办\s*人[：:\s]*([^\n]{2,20}?)(?=\s|$|电话|手机)',
        r'联系人[：:\s]*([^\n]{2,20}?)(?=\n|电话|手机)',
    ]

    # 电话提取模式
    CONTACT_PHONE_PATTERNS = [
        r'联\s*系\s*电\s*话[：:\s]*([\d\-\(\)\s]{7,20})',
        r'联系电话[：:\s]*([\d\-\(\)\s]{7,20})',
        r'电话[：:\s]*([\d\-\(\)\s]{7,20})',
        r'手\s*机[：:\s]*([\d\-\(\)\s]{7,20})',
    ]

    # 项目编号模式
    PROJECT_NUMBER_PATTERNS = [
        r'项\s*目\s*编\s*号[：:\s]*([A-Za-z0-9\-\_]{5,30})',
        r'采\s*购\s*编\s*号[：:\s]*([A-Za-z0-9\-\_]{5,30})',
        r'招\s*标\s*编\s*号[：:\s]*([A-Za-z0-9\-\_]{5,30})',
    ]

    # 金额提取模式
    BUDGET_PATTERNS = [
        r'预\s*算\s*金\s*额[：:\s]*([\d,\.\s]+(?:万|亿)?元?)',
        r'最\s*高\s*限\s*价[：:\s]*([\d,\.\s]+(?:万|亿)?元?)',
        r'预\s*算[：:\s]*([\d,\.\s]+(?:万|亿)?元?)',
    ]

    def __init__(self):
        self.agent = FieldExtractorAgent()
        self.config = ConfigManager.get_tender_tool_config()
        self.logger = logging.getLogger(__name__)

    async def extract(
        self,
        html: str,
        url: str,
        use_enhanced_tenderer: bool = True,
    ) -> FieldExtractionResult:
        """
        从 HTML 中提取字段

        Args:
            html: HTML 内容
            url: 来源 URL
            use_enhanced_tenderer: 是否使用增强的招标人提取

        Returns:
            FieldExtractionResult: 提取结果
        """
        try:
            self.logger.info(f"Extracting fields from: {url}")

            # 首先调用 Agent 提取
            schema = await self.agent.extract(html, url)

            if schema is None:
                raise ValueError("Agent returned None")

            extraction_method = 'llm'

            # 安全获取置信度值（处理 Mock 对象）
            try:
                confidence = float(getattr(schema, 'extraction_confidence', 0.5) or 0.5)
            except (TypeError, ValueError):
                confidence = 0.5

            # 安全获取 tenderer 值
            tenderer = getattr(schema, 'tenderer', None)
            # 处理 Mock 对象的情况
            if tenderer is not None and not isinstance(tenderer, str):
                try:
                    tenderer_str = str(tenderer)
                    if len(tenderer_str) < 100:  # 合理的字符串长度
                        tenderer = tenderer_str
                    else:
                        tenderer = None
                except Exception:
                    tenderer = None

            # 如果启用了增强模式，且招标人提取置信度低，进行补充提取
            if use_enhanced_tenderer and (not tenderer or confidence < 0.7):
                enhanced_tenderer = self._extract_tenderer_enhanced(html)
                if enhanced_tenderer:
                    self.logger.info(
                        f"Enhanced tenderer extraction: '{tenderer}' -> '{enhanced_tenderer}'"
                    )
                    schema.tenderer = enhanced_tenderer
                    if extraction_method == 'llm':
                        extraction_method = 'llm+regex'

            # 补充提取其他字段
            field_confidences = self._calculate_field_confidences(schema, html)

            # 识别缺失字段
            missing_fields = self._identify_missing_fields(schema)

            # 重新计算整体置信度
            confidence = self._calculate_overall_confidence(field_confidences)
            schema.extraction_confidence = confidence

            # 生成警告
            warnings = self._generate_warnings(schema, missing_fields)

            return FieldExtractionResult(
                schema=schema,
                success=True,
                extraction_method=extraction_method,
                confidence=confidence,
                field_confidences=field_confidences,
                missing_fields=missing_fields,
                warnings=warnings,
            )

        except Exception as e:
            self.logger.error(f"Field extraction failed: {e}")
            # 使用备用提取
            try:
                schema = await self.agent.extract_from_text(html, url)
                if schema is None:
                    raise ValueError("Fallback returned None")
                return FieldExtractionResult(
                    schema=schema,
                    success=True,
                    extraction_method='fallback',
                    confidence=0.4,
                    warnings=[f"Primary extraction failed, used fallback: {e}"],
                )
            except Exception as fallback_error:
                return FieldExtractionResult(
                    schema=None,
                    success=False,
                    extraction_method='failed',
                    confidence=0.0,
                    error_message=f"Extraction failed: {e}, fallback also failed: {fallback_error}",
                )

    async def extract_from_text(
        self,
        text: str,
        url: str,
    ) -> FieldExtractionResult:
        """
        从纯文本中提取字段（用于 PDF 内容）

        Args:
            text: 文本内容
            url: 来源 URL

        Returns:
            FieldExtractionResult: 提取结果
        """
        try:
            self.logger.info(f"Extracting fields from text: {url}")

            schema = await self.agent.extract_from_text(text, url)

            if schema is None:
                raise ValueError("Agent returned None")

            # 安全获取字段值（处理 Mock 对象）
            def safe_get_str(value, default=None):
                if value is None:
                    return default
                if isinstance(value, str):
                    return value
                try:
                    str_val = str(value)
                    return str_val if len(str_val) < 200 else default
                except Exception:
                    return default

            # 使用增强提取补充字段
            tenderer = safe_get_str(getattr(schema, 'tenderer', None))
            if not tenderer:
                schema.tenderer = self._extract_tenderer_enhanced(text)

            contact_person = safe_get_str(getattr(schema, 'contact_person', None))
            if not contact_person:
                schema.contact_person = self._extract_contact_person_enhanced(text)

            contact_phone = safe_get_str(getattr(schema, 'contact_phone', None))
            if not contact_phone:
                schema.contact_phone = self._extract_contact_phone_enhanced(text)

            project_number = safe_get_str(getattr(schema, 'project_number', None))
            if not project_number:
                schema.project_number = self._extract_project_number_enhanced(text)

            field_confidences = self._calculate_field_confidences(schema, text)
            confidence = self._calculate_overall_confidence(field_confidences)
            schema.extraction_confidence = confidence

            missing_fields = self._identify_missing_fields(schema)

            return FieldExtractionResult(
                schema=schema,
                success=True,
                extraction_method='llm_text+regex',
                confidence=confidence,
                field_confidences=field_confidences,
                missing_fields=missing_fields,
            )

        except Exception as e:
            self.logger.error(f"Text extraction failed: {e}")
            return FieldExtractionResult(
                schema=None,
                success=False,
                extraction_method='failed',
                confidence=0.0,
                error_message=str(e),
            )

    def _extract_tenderer_enhanced(self, content: str) -> Optional[str]:
        """
        增强的招标人提取

        使用多种正则模式匹配，返回最可信的结果
        """
        candidates = []

        for pattern in self.TENDERER_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                tenderer = match.group(1).strip()
                # 清洗结果
                tenderer = self._clean_tenderer(tenderer)
                if self._is_valid_tenderer(tenderer):
                    # 计算该匹配的置信度
                    conf = self._calculate_tenderer_confidence(tenderer, content)
                    candidates.append((tenderer, conf))

        if not candidates:
            return None

        # 按置信度排序，返回最高分的
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]

    def _clean_tenderer(self, tenderer: str) -> str:
        """清洗招标人名称"""
        # 去除多余空白
        tenderer = re.sub(r'\s+', ' ', tenderer)
        # 去除常见后缀
        tenderer = re.sub(r'(联系人|电话|传真|地址|邮编).*$', '', tenderer)
        # 去除 HTML 标签
        tenderer = re.sub(r'<[^>]+>', '', tenderer)
        # 去除特殊字符
        tenderer = tenderer.strip(' :：\n\r\t')
        return tenderer.strip()

    def _is_valid_tenderer(self, tenderer: str) -> bool:
        """验证招标人名称是否有效"""
        if not tenderer or len(tenderer) < 2:
            return False
        if len(tenderer) > 100:
            return False
        # 应该包含中文字符或常见单位词汇
        if not re.search(r'[\u4e00-\u9fa5]', tenderer):
            # 没有中文，检查是否有英文单位名
            if not re.search(r'(Corp|Inc|Ltd|Company|Center)', tenderer, re.I):
                return False
        # 排除常见无效值
        invalid_values = ['无', '详见', '公告', '采购人', '招标人', '/']
        if tenderer in invalid_values:
            return False
        return True

    def _calculate_tenderer_confidence(self, tenderer: str, content: str) -> float:
        """计算招标人名称的置信度"""
        score = 0.5

        # 长度合适加分
        if 4 <= len(tenderer) <= 30:
            score += 0.1

        # 包含单位关键词加分
        keywords = ['公司', '中心', '局', '委', '办', '院', '校', '医院', '研究所', '大学']
        if any(kw in tenderer for kw in keywords):
            score += 0.2

        # 在内容中出现多次加分
        count = content.count(tenderer)
        if count >= 2:
            score += 0.1

        # 标题格式加分（如"XX公司"）
        if tenderer.endswith('公司') or tenderer.endswith('中心'):
            score += 0.1

        return min(score, 1.0)

    def _extract_contact_person_enhanced(self, content: str) -> Optional[str]:
        """增强的联系人提取"""
        for pattern in self.CONTACT_PERSON_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                person = match.group(1).strip()
                person = self._clean_contact_person(person)
                if len(person) >= 2 and len(person) <= 20:
                    return person
        return None

    def _clean_contact_person(self, person: str) -> str:
        """清洗联系人名称"""
        person = re.sub(r'\s+', ' ', person)
        person = re.sub(r'(电话|手机|邮箱).*$', '', person)
        person = person.strip(' :：\n\r\t')
        return person.strip()

    def _extract_contact_phone_enhanced(self, content: str) -> Optional[str]:
        """增强的电话提取"""
        for pattern in self.CONTACT_PHONE_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                phone = match.group(1).strip()
                phone = re.sub(r'\s+', '', phone)
                if len(phone) >= 7:
                    return phone
        return None

    def _extract_project_number_enhanced(self, content: str) -> Optional[str]:
        """增强的项目编号提取"""
        for pattern in self.PROJECT_NUMBER_PATTERNS:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                number = match.group(1).strip()
                if len(number) >= 5:
                    return number
        return None

    def _calculate_field_confidences(
        self,
        schema: TenderNoticeSchema,
        content: str,
    ) -> Dict[str, float]:
        """计算各字段的置信度"""
        confidences = {}

        # 安全获取字符串值（处理 Mock 对象）
        def safe_str(value):
            if value is None:
                return ""
            if isinstance(value, str):
                return value
            try:
                str_val = str(value)
                # 检查是否是合理的字符串表示
                if len(str_val) > 500:  # Mock 对象可能会返回很长的字符串表示
                    return ""
                return str_val
            except Exception:
                return ""

        # title
        title = safe_str(getattr(schema, 'title', None))
        if title and len(title) >= 10:
            confidences['title'] = 0.9
        elif title:
            confidences['title'] = 0.7
        else:
            confidences['title'] = 0.0

        # tenderer
        tenderer = safe_str(getattr(schema, 'tenderer', None))
        if tenderer:
            confidences['tenderer'] = self._calculate_tenderer_confidence(
                tenderer, content
            )
        else:
            confidences['tenderer'] = 0.0

        # budget_amount
        budget_amount = getattr(schema, 'budget_amount', None)
        try:
            if budget_amount is not None and float(budget_amount) > 0:
                confidences['budget_amount'] = 0.8
            else:
                confidences['budget_amount'] = 0.0
        except (TypeError, ValueError):
            confidences['budget_amount'] = 0.0

        # publish_date
        if getattr(schema, 'publish_date', None):
            confidences['publish_date'] = 0.9
        else:
            confidences['publish_date'] = 0.0

        # project_number
        project_number = safe_str(getattr(schema, 'project_number', None))
        if project_number and len(project_number) >= 5:
            confidences['project_number'] = 0.85
        else:
            confidences['project_number'] = 0.0

        # contact_person
        contact_person = safe_str(getattr(schema, 'contact_person', None))
        if contact_person and len(contact_person) >= 2:
            confidences['contact_person'] = 0.75
        else:
            confidences['contact_person'] = 0.0

        # contact_phone
        contact_phone = safe_str(getattr(schema, 'contact_phone', None))
        if contact_phone and len(contact_phone) >= 7:
            confidences['contact_phone'] = 0.75
        else:
            confidences['contact_phone'] = 0.0

        return confidences

    def _calculate_overall_confidence(self, field_confidences: Dict[str, float]) -> float:
        """计算整体置信度"""
        if not field_confidences:
            return 0.0

        # 加权平均
        weights = {
            'title': 0.20,
            'tenderer': 0.20,
            'publish_date': 0.15,
            'budget_amount': 0.15,
            'project_number': 0.10,
            'contact_person': 0.10,
            'contact_phone': 0.10,
        }

        total_weight = 0.0
        weighted_sum = 0.0

        for field, confidence in field_confidences.items():
            weight = weights.get(field, 0.05)
            weighted_sum += confidence * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(weighted_sum / total_weight, 2)

    def _identify_missing_fields(self, schema: TenderNoticeSchema) -> List[str]:
        """识别缺失的必需字段"""
        required_fields = ConfigManager.get_tender_tool_config().required_fields
        missing = []

        for field in required_fields:
            value = getattr(schema, field, None)
            # 安全检查值（处理 Mock 对象）
            if value is None:
                is_empty = True
            elif isinstance(value, str):
                is_empty = len(value.strip()) == 0
            else:
                # 对于非字符串值，尝试转换为字符串检查
                try:
                    str_val = str(value)
                    is_empty = len(str_val.strip()) == 0 or len(str_val) > 200
                except Exception:
                    is_empty = True

            if is_empty:
                missing.append(field)

        return missing

    def _generate_warnings(
        self,
        schema: TenderNoticeSchema,
        missing_fields: List[str],
    ) -> List[str]:
        """生成警告信息"""
        warnings = []

        if 'tenderer' in missing_fields:
            warnings.append("Missing tenderer (招标人)")
        if 'title' in missing_fields:
            warnings.append("Missing title")
        if 'publish_date' in missing_fields:
            warnings.append("Missing publish_date")

        # 安全获取 tenderer 值
        tenderer = getattr(schema, 'tenderer', None)
        if tenderer is not None:
            if isinstance(tenderer, str) and len(tenderer) < 4:
                warnings.append(f"Tenderer name seems too short: '{tenderer}'")

        return warnings


# 便捷的函数接口（用于 LangChain Tool 装饰器）
async def field_extract_tool(
    html: str,
    url: str,
    use_enhanced: bool = True,
) -> Dict[str, Any]:
    """
    字段提取工具函数

    Args:
        html: HTML 内容
        url: 来源 URL
        use_enhanced: 是否使用增强提取

    Returns:
        提取结果字典
    """
    tool = FieldExtractorTool()
    result = await tool.extract(html, url, use_enhanced_tenderer=use_enhanced)

    return result.to_dict()
