"""
LLM Content Extraction - 基于大模型的内容提取

Plan B: 使用配置的LLM从HTML中提取结构化招标信息
"""

import re
import json
import logging
from typing import Dict, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime

logger = logging.getLogger(__name__)


class LLMContentExtractor:
    """
    基于LLM的内容提取器

    使用大模型从HTML中提取招标关键信息
    """

    EXTRACTION_PROMPT = """你是一个招标信息提取专家。请从以下网页内容中提取招标相关信息。

网页内容：
{content}

请提取以下信息并以JSON格式返回：
{{
    "title": "招标标题/公告标题",
    "tenderer": "采购人/招标人名称",
    "budget": 预算金额（纯数字，单位：元，没有则为null）,
    "budget_unit": "金额原始单位，如万元、元等",
    "publish_date": "发布日期，格式YYYY-MM-DD",
    "deadline": "截止日期，格式YYYY-MM-DD",
    "project_number": "项目编号",
    "region": "地区/省份",
    "industry": "行业分类",
    "contact_person": "联系人",
    "contact_phone": "联系电话",
    "description": "项目简要描述（100字以内）"
}}

重要规则：
1. 只返回JSON，不要其他任何文字
2. 如果无法提取某项，设为null
3. 金额必须转换为元为单位
4. 日期统一为YYYY-MM-DD格式
5. 从HTML文本内容提取，忽略HTML标签"""

    def __init__(self, llm_service=None):
        """
        初始化LLM提取器

        Args:
            llm_service: LLM服务实例 (LLMService)
        """
        self.llm_service = llm_service

    def set_llm_service(self, llm_service):
        """设置LLM服务"""
        self.llm_service = llm_service

    def extract(self, html: str, source_url: str = '') -> Dict:
        """
        使用LLM从HTML中提取招标信息

        Args:
            html: HTML内容
            source_url: 来源URL（用于日志）

        Returns:
            提取的信息字典
        """
        if not html:
            return {'error': 'Empty HTML'}

        if not self.llm_service:
            logger.warning("LLM service not configured")
            return {'error': 'LLM service not configured'}

        # 预处理HTML，提取纯文本
        text_content = self._html_to_text(html)

        if len(text_content) < 50:
            return {'error': 'Insufficient content'}

        # 限制内容长度
        max_length = 4000
        if len(text_content) > max_length:
            text_content = text_content[:max_length] + '...'

        try:
            # 调用LLM
            prompt = self.EXTRACTION_PROMPT.format(content=text_content)

            messages = [
                {'role': 'system', 'content': '你是招标信息提取专家，擅长从网页内容中提取结构化信息。'},
                {'role': 'user', 'content': prompt}
            ]

            response = self.llm_service.chat(messages, prompt)

            # 解析响应
            llm_response = response.get('message', '')

            result = self._parse_llm_response(llm_response)
            result['extraction_method'] = 'llm'
            result['llm_provider'] = getattr(self.llm_service, 'provider', 'unknown')

            return result

        except Exception as e:
            logger.error(f"LLM extraction failed for {source_url}: {e}")
            return {'error': str(e), 'extraction_method': 'llm_failed'}

    def _html_to_text(self, html: str) -> str:
        """
        将HTML转换为纯文本，保留结构信息

        Args:
            html: HTML内容

        Returns:
            纯文本内容
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        # 移除脚本和样式
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()

        # 获取文本
        text = soup.get_text(separator='\n', strip=True)

        # 清理多余空行
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)

        return text

    def _parse_llm_response(self, response: str) -> Dict:
        """
        解析LLM响应

        Args:
            response: LLM返回的文本

        Returns:
            解析后的字典
        """
        result = {}

        try:
            # 尝试提取JSON
            json_str = response

            # 查找JSON代码块
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试查找大括号内容
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)

            data = json.loads(json_str)

            # 映射字段
            result['title'] = data.get('title')
            result['tenderer'] = data.get('tenderer')
            result['budget'] = self._parse_budget(data.get('budget'))
            result['publish_date'] = self._parse_date(data.get('publish_date'))
            result['deadline'] = self._parse_date(data.get('deadline'))
            result['project_number'] = data.get('project_number')
            result['region'] = data.get('region')
            result['industry'] = data.get('industry')
            result['contact_person'] = data.get('contact_person')
            result['contact_phone'] = data.get('contact_phone')
            result['description'] = data.get('description')

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            # 尝试正则提取关键字段
            result = self._fallback_extract(response)

        return result

    def _parse_budget(self, value) -> Optional[Decimal]:
        """解析预算金额"""
        if value is None:
            return None

        try:
            if isinstance(value, (int, float)):
                return Decimal(str(value))

            # 字符串处理
            value_str = str(value).strip()
            # 移除货币符号和分隔符
            value_str = re.sub(r'[¥￥,\s]', '', value_str)

            return Decimal(value_str)

        except (InvalidOperation, ValueError):
            return None

    def _parse_date(self, value) -> Optional[datetime]:
        """解析日期"""
        if not value:
            return None

        try:
            # 尝试ISO格式
            return datetime.strptime(str(value)[:10], '%Y-%m-%d')
        except ValueError:
            pass

        # 尝试其他格式
        formats = ['%Y/%m/%d', '%Y.%m.%d', '%Y年%m月%d日']
        for fmt in formats:
            try:
                return datetime.strptime(str(value), fmt)
            except ValueError:
                continue

        return None

    def _fallback_extract(self, text: str) -> Dict:
        """备用提取方法"""
        result = {}

        # 简单正则提取
        title_match = re.search(r'"title"\s*:\s*"([^"]+)"', text)
        if title_match:
            result['title'] = title_match.group(1)

        tenderer_match = re.search(r'"tenderer"\s*:\s*"([^"]+)"', text)
        if tenderer_match:
            result['tenderer'] = tenderer_match.group(1)

        budget_match = re.search(r'"budget"\s*:\s*(\d+)', text)
        if budget_match:
            result['budget'] = Decimal(budget_match.group(1))

        return result


def get_llm_extractor():
    """
    获取配置的LLM提取器实例

    Returns:
        LLMContentExtractor实例或None
    """
    try:
        from apps.llm.models import LLMConfig
        from apps.llm.services import LLMService

        # 获取默认配置
        config = LLMConfig.objects.filter(is_active=True).first()

        if not config:
            logger.warning("No active LLM configuration found")
            return None

        llm_service = LLMService(config)
        return LLMContentExtractor(llm_service)

    except Exception as e:
        logger.error(f"Failed to initialize LLM extractor: {e}")
        return None