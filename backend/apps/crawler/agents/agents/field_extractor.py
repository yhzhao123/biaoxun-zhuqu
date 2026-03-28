"""
字段提取智能体

使用LLM从HTML/PDF文本中提取结构化字段
"""
import logging
import json
import re
from typing import List, Dict, Any, Optional
from decimal import Decimal
from asgiref.sync import sync_to_async

from bs4 import BeautifulSoup

from apps.crawler.agents.schema import TenderNoticeSchema
from apps.llm.services import LLMService
from apps.llm.models import LLMConfig

logger = logging.getLogger(__name__)


class FieldExtractorAgent:
    """
    字段提取智能体
    使用LLM从HTML内容中提取招标信息字段
    """

    SYSTEM_PROMPT = """你是一个专业的招标信息提取专家。从给定的网页内容中提取招标公告的结构化信息。

提取字段：
- title: 公告标题（去除HTML标签）
- tenderer: 招标人/采购人名称
- winner: 中标人/成交供应商（中标公告时填写）
- budget_amount: 预算金额（转换为元为单位的数字）
- budget_unit: 金额单位（元/万元/亿元）
- publish_date: 发布日期（YYYY-MM-DD格式）
- deadline_date: 截止日期/开标日期（YYYY-MM-DD格式）
- project_number: 项目编号
- region: 地区/省份
- industry: 行业分类
- contact_person: 联系人姓名
- contact_phone: 联系电话
- description: 项目简要描述（去除HTML标签，保留纯文本）
- notice_type: 公告类型（bidding招标|win中标|change变更）

规则：
1. 只返回JSON格式，不要任何其他文字
2. 无法确定的字段设为null
3. 金额统一转换为"元"为单位（如100万元=1000000）
4. 日期使用YYYY-MM-DD格式
5. 公告类型判断：
   - 标题包含"招标公告"、"采购公告"、"竞争性磋商" -> bidding
   - 标题包含"中标公告"、"成交公告"、"中标候选人" -> win
   - 标题包含"变更公告"、"补遗"、"澄清" -> change

请提取所有可能的字段，以JSON对象格式返回。"""

    def __init__(self):
        self.llm_service = None
        # 延迟初始化，避免在异步上下文中调用同步代码
        # self._init_llm()

    def _init_llm(self):
        """初始化LLM服务（同步版本）"""
        try:
            config = LLMConfig.objects.filter(is_active=True, is_default=True).first()
            if not config:
                config = LLMConfig.objects.filter(is_active=True).first()

            if config:
                self.llm_service = LLMService(config)
                logger.info(f"LLM service initialized: {config.provider}/{config.model_name}")
            else:
                logger.warning("No LLM config found")
        except Exception as e:
            logger.error(f"Failed to init LLM: {e}")

    @sync_to_async
    def _init_llm_async(self):
        """异步初始化LLM服务"""
        self._init_llm()

    async def extract_from_text(self, text: str, url: str) -> TenderNoticeSchema:
        """
        从纯文本中提取字段（用于PDF内容）

        Args:
            text: 文本内容
            url: 来源URL

        Returns:
            TenderNoticeSchema 提取结果
        """
        # 延迟初始化LLM服务
        if self.llm_service is None:
            await self._init_llm_async()

        # 如果LLM服务不可用，使用备用提取
        if not self.llm_service:
            logger.warning("LLM service not available, using fallback")
            return self._fallback_extract(text, url)

        try:
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"""从以下招标公告文本中提取结构化信息：

来源URL: {url}

文本内容:
{text[:8000]}

请返回JSON格式的提取结果。"""}
            ]

            response = self.llm_service.chat(messages, "")
            raw_response = response.get('message', '')

            # 解析响应
            extracted_data = self._parse_llm_response(raw_response)

            # 构建Schema
            result = self._build_schema(extracted_data, url)
            result.extraction_method = 'llm_text'
            result.extraction_confidence = self._calculate_confidence(result)

            return result

        except Exception as e:
            logger.error(f"LLM text extraction failed: {e}")
            return self._fallback_extract(text, url)

    async def extract(self, html: str, url: str) -> TenderNoticeSchema:
        """
        从HTML中提取字段

        Args:
            html: HTML内容
            url: 来源URL

        Returns:
            TenderNoticeSchema 提取结果
        """
        # 预处理HTML
        text_content = self._preprocess_html(html)

        # 延迟初始化LLM服务
        if self.llm_service is None:
            await self._init_llm_async()

        # 如果LLM服务不可用，使用备用提取
        if not self.llm_service:
            logger.warning("LLM service not available, using fallback")
            return self._fallback_extract(text_content, url)

        try:
            # 构建消息
            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"""从以下招标公告内容中提取结构化信息：

来源URL: {url}

网页内容:
{text_content[:8000]}

请返回JSON格式的提取结果。"""}
            ]

            # 调用LLM
            response = self.llm_service.chat(messages, "")
            raw_response = response.get('message', '')

            # 解析响应
            extracted_data = self._parse_llm_response(raw_response)

            # 构建Schema
            result = self._build_schema(extracted_data, url)
            result.extraction_method = 'llm'
            result.extraction_confidence = self._calculate_confidence(result)

            return result

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return self._fallback_extract(text_content, url)

    async def extract_missing(
        self,
        data: TenderNoticeSchema,
        missing_fields: List[str],
        html: str
    ) -> TenderNoticeSchema:
        """
        提取缺失字段
        """
        # 延迟初始化LLM服务
        if self.llm_service is None:
            await self._init_llm_async()

        if not self.llm_service or not missing_fields:
            return data

        try:
            text_content = self._preprocess_html(html)

            messages = [
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": f"""请补充以下招标信息的缺失字段：

缺失字段: {', '.join(missing_fields)}

已有信息:
- 标题: {data.title or '未提取'}
- 招标人: {data.tenderer or '未提取'}

网页内容:
{text_content[:6000]}

请只返回缺失字段的JSON对象。"""}
            ]

            response = self.llm_service.chat(messages, "")
            raw_response = response.get('message', '')
            extracted_data = self._parse_llm_response(raw_response)

            # 更新缺失字段
            for field in missing_fields:
                if field in extracted_data and extracted_data[field]:
                    setattr(data, field, extracted_data[field])

            # 重新计算置信度
            data.extraction_confidence = self._calculate_confidence(data)

        except Exception as e:
            logger.error(f"Failed to extract missing fields: {e}")

        return data

    def _preprocess_html(self, html: str) -> str:
        """预处理HTML，提取纯文本"""
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # 移除无用标签
            for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                tag.decompose()

            # 获取文本
            text = soup.get_text(separator='\n', strip=True)

            # 清理空行
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            text = '\n'.join(lines)

            return text
        except Exception as e:
            logger.warning(f"HTML preprocessing failed: {e}")
            return html

    def _parse_llm_response(self, response: str) -> Dict:
        """解析LLM响应"""
        if not response:
            return {}

        # 尝试提取JSON
        json_str = response

        # 查找JSON代码块
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试查找大括号内容
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)

        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parse failed: {e}")
            return {}

    def _build_schema(self, data: Dict, url: str) -> TenderNoticeSchema:
        """从字典构建Schema"""
        # 金额处理
        budget = self._parse_amount(data.get('budget_amount') or data.get('budget'))

        # 日期处理
        publish_date = self._parse_date(data.get('publish_date'))
        deadline_date = self._parse_date(data.get('deadline_date') or data.get('deadline'))

        return TenderNoticeSchema(
            title=data.get('title'),
            tenderer=data.get('tenderer'),
            winner=data.get('winner'),
            budget_amount=budget,
            budget_unit=data.get('budget_unit', '元'),
            currency=data.get('currency', 'CNY'),
            publish_date=publish_date,
            deadline_date=deadline_date,
            project_number=data.get('project_number'),
            region=data.get('region'),
            industry=data.get('industry'),
            contact_person=data.get('contact_person'),
            contact_phone=data.get('contact_phone'),
            description=data.get('description'),
            notice_type=data.get('notice_type', 'bidding'),
            source_url=url,
        )

    def _parse_amount(self, value) -> Optional[Decimal]:
        """解析金额"""
        if value is None:
            return None

        if isinstance(value, (int, float)):
            return Decimal(str(value))

        if isinstance(value, str):
            # 移除货币符号和空格
            amount_str = value.replace(',', '').replace(' ', '')
            amount_str = re.sub(r'[¥￥$€]', '', amount_str)

            # 匹配数字和单位
            match = re.search(r'([\d.]+)\s*([万亿]?)', amount_str)
            if match:
                try:
                    number = Decimal(match.group(1))
                    unit = match.group(2)

                    if unit == '亿':
                        number *= Decimal('100000000')
                    elif unit == '万':
                        number *= Decimal('10000')

                    return number
                except:
                    pass

        return None

    def _parse_date(self, value) -> Optional[Any]:
        """解析日期"""
        if not value:
            return None

        from datetime import datetime

        date_str = str(value).strip()

        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y.%m.%d',
            '%Y年%m月%d日',
            '%Y-%m-%d %H:%M:%S',
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str[:len(fmt)], fmt)
            except ValueError:
                continue

        return None

    def _calculate_confidence(self, data: TenderNoticeSchema) -> float:
        """计算置信度"""
        score = 0.0
        weights = {
            'title': 0.25,
            'tenderer': 0.20,
            'budget_amount': 0.15,
            'publish_date': 0.15,
            'description': 0.15,
            'contact_person': 0.10,
        }

        for field, weight in weights.items():
            value = getattr(data, field)
            if value:
                score += weight

        return min(score, 1.0)

    def _fallback_extract(self, text: str, url: str) -> TenderNoticeSchema:
        """备用提取方法"""
        # 简单规则提取
        result = TenderNoticeSchema(source_url=url)

        # 从文本第一行提取标题
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            if len(line) > 10 and len(line) < 200:
                result.title = line
                break

        result.extraction_method = 'fallback'
        result.extraction_confidence = 0.1

        return result
