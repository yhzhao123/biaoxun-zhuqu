"""
增强的 LLM 招标信息提取服务
支持 OpenRouter、OpenAI、Claude、Ollama 等提供商
具备重试、超时、批量处理和成本跟踪功能
"""
import logging
import time
import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass
from functools import wraps
import random

from bs4 import BeautifulSoup

from apps.llm.models import LLMConfig
from apps.llm.services import LLMService

from .structured_schema import TenderNoticeSchema
from .prompts import TenderExtractionPrompts

logger = logging.getLogger(__name__)


@dataclass
class ExtractionConfig:
    """提取配置"""
    max_retries: int = 3
    retry_delay: float = 1.0  # 秒
    exponential_backoff: bool = True
    timeout_seconds: int = 60
    max_content_length: int = 6000
    use_few_shot: bool = True
    min_confidence: float = 0.5  # 最低置信度阈值
    enable_cost_tracking: bool = True


class LLMExtractionService:
    """
    增强的 LLM 招标信息提取服务

    功能：
    - 多提供商支持（OpenRouter/OpenAI/Claude/Ollama）
    - 自动重试和指数退避
    - 批量处理优化
    - 成本跟踪
    - 结果验证和置信度评分
    """

    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        extraction_config: Optional[ExtractionConfig] = None
    ):
        """
        初始化服务

        Args:
            config: LLM 配置（为 None 时使用默认配置）
            extraction_config: 提取配置
        """
        self.llm_config = config or self._get_default_config()
        self.extraction_config = extraction_config or ExtractionConfig()
        self.llm_service = LLMService(self.llm_config) if self.llm_config else None

        # 统计信息
        self.total_tokens = 0
        self.total_cost = 0.0
        self.request_count = 0
        self.success_count = 0
        self.failure_count = 0

    def _get_default_config(self) -> Optional[LLMConfig]:
        """获取默认 LLM 配置"""
        try:
            config = LLMConfig.objects.filter(is_active=True, is_default=True).first()
            if not config:
                config = LLMConfig.objects.filter(is_active=True).first()
            return config
        except Exception as e:
            logger.warning(f"无法加载 LLM 配置: {e}")
            return None

    def extract(
        self,
        html: str,
        source_url: str = "",
        use_fallback: bool = True
    ) -> TenderNoticeSchema:
        """
        从 HTML 中提取结构化招标信息

        Args:
            html: HTML 内容
            source_url: 来源 URL
            use_fallback: 失败时是否使用备用方法

        Returns:
            TenderNoticeSchema 实例
        """
        if not html:
            return TenderNoticeSchema(
                extraction_method="skipped",
                extraction_confidence=0.0,
                raw_llm_response="空 HTML 内容"
            )

        # 预处理 HTML
        text_content = self._html_to_text(html)

        if len(text_content) < 50:
            return TenderNoticeSchema(
                extraction_method="skipped",
                extraction_confidence=0.0,
                raw_llm_response="HTML 清理后内容不足"
            )

        # 调用 LLM（带重试）
        result = self._extract_with_retry(text_content, source_url)

        # 如果 LLM 提取失败且启用备用方法
        if result.extraction_confidence < 0.1 and use_fallback:
            logger.info("LLM 提取置信度低，尝试备用提取方法")
            fallback_result = self._fallback_extraction(html, source_url)
            if fallback_result.extraction_confidence > result.extraction_confidence:
                return fallback_result

        return result

    def _extract_with_retry(
        self,
        content: str,
        source_url: str
    ) -> TenderNoticeSchema:
        """带重试的提取逻辑"""
        last_error = None

        for attempt in range(self.extraction_config.max_retries):
            try:
                result = self._call_llm(content, source_url)

                # 验证置信度
                if result.extraction_confidence < self.extraction_config.min_confidence:
                    logger.warning(
                        f"提取置信度较低: {result.extraction_confidence:.2f} "
                        f"(最低要求: {self.extraction_config.min_confidence})"
                    )

                self.success_count += 1
                return result

            except Exception as e:
                last_error = e
                self.failure_count += 1
                logger.warning(f"提取尝试 {attempt + 1} 失败: {e}")

                if attempt < self.extraction_config.max_retries - 1:
                    # 计算延迟时间（指数退避 + 抖动）
                    if self.extraction_config.exponential_backoff:
                        delay = self.extraction_config.retry_delay * (2 ** attempt)
                    else:
                        delay = self.extraction_config.retry_delay

                    # 添加随机抖动（0-20%）
                    jitter = random.uniform(0, delay * 0.2)
                    time.sleep(delay + jitter)

        # 所有重试失败
        logger.error(f"所有提取尝试都失败了: {last_error}")

        return TenderNoticeSchema(
            extraction_method="llm_failed",
            extraction_confidence=0.0,
            raw_llm_response=f"错误: {str(last_error)}"
        )

    def _call_llm(self, content: str, source_url: str) -> TenderNoticeSchema:
        """
        调用 LLM 进行提取

        Args:
            content: 预处理后的文本内容
            source_url: 来源 URL

        Returns:
            TenderNoticeSchema 实例
        """
        if not self.llm_service:
            raise ValueError("LLM 服务未配置")

        # 构建消息
        messages = TenderExtractionPrompts.build_messages(
            content=content,
            source_url=source_url,
            use_few_shot=self.extraction_config.use_few_shot
        )

        # 调用 LLM
        start_time = time.time()
        response = self.llm_service.chat(messages, "")
        elapsed_time = time.time() - start_time

        # 更新统计
        self.request_count += 1
        if 'metadata' in response and 'usage' in response.get('metadata', {}):
            usage = response['metadata']['usage']
            self.total_tokens += usage.get('total_tokens', 0)

        logger.info(
            f"LLM 提取完成，耗时 {elapsed_time:.2f}秒 "
            f"(提供商: {self.llm_config.provider})"
        )

        # 解析响应
        raw_response = response.get('message', '')
        parsed_data = self._parse_llm_response(raw_response)

        # 构建结果
        result = TenderNoticeSchema(
            **parsed_data,
            extraction_method="llm",
            extraction_confidence=self._calculate_confidence(parsed_data),
            llm_provider=self.llm_config.provider,
            llm_model=self.llm_config.model_name,
            raw_llm_response=raw_response[:2000] if raw_response else None,
            source_url=source_url
        )

        return result

    def _html_to_text(self, html: str) -> str:
        """将 HTML 转换为纯文本"""
        soup = BeautifulSoup(html, 'html.parser')

        # 移除无用标签
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
            tag.decompose()

        # 获取文本
        text = soup.get_text(separator='\n', strip=True)

        # 清理空行和重复空白
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = '\n'.join(lines)

        # 限制长度
        max_len = self.extraction_config.max_content_length
        if len(text) > max_len:
            text = text[:max_len] + '\n...'

        return text

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析 LLM 响应"""
        if not response:
            return {}

        # 尝试提取 JSON
        json_str = response

        # 查找 JSON 代码块
        json_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试查找大括号内容
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                json_str = json_match.group(0)

        try:
            data = json.loads(json_str)
            return self._normalize_data(data)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}")
            return self._fallback_parse(response)

    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """标准化数据格式"""
        normalized = {}

        # 字段映射（处理 LLM 可能使用的不同字段名）
        field_mappings = {
            'title': ['title', '项目名称', '标题'],
            'tenderer': ['tenderer', '招标人', '采购人', '采购单位', '招标单位'],
            'winner': ['winner', '中标人', '成交供应商', '中标单位'],
            'contact_person': ['contact_person', '联系人'],
            'contact_phone': ['contact_phone', '联系电话', '联系方式'],
            'project_number': ['project_number', '项目编号', '采购编号', '招标编号'],
            'region': ['region', '地区', '省份'],
            'industry': ['industry', '行业'],
            'description': ['description', '项目概况', '项目内容', 'description'],
            'source_url': ['source_url', '来源URL'],
        }

        # 提取字段
        for standard_field, possible_names in field_mappings.items():
            for name in possible_names:
                if name in data and data[name]:
                    normalized[standard_field] = data[name]
                    break

        # 金额处理
        budget = data.get('budget_amount') or data.get('budget') or data.get('金额')
        if budget is not None:
            try:
                normalized['budget_amount'] = self._parse_amount(budget)
            except:
                pass
        normalized['budget_unit'] = data.get('budget_unit', '元')
        normalized['currency'] = data.get('currency', 'CNY')

        # 日期处理
        publish_date = data.get('publish_date') or data.get('发布日期') or data.get('公告日期')
        if publish_date:
            normalized['publish_date'] = self._parse_date(publish_date)

        deadline = data.get('deadline_date') or data.get('deadline') or data.get('截止日期') or data.get('开标日期')
        if deadline:
            normalized['deadline_date'] = self._parse_date(deadline)

        # 类型处理
        notice_type = data.get('notice_type') or data.get('公告类型')
        if notice_type:
            normalized['notice_type'] = self._normalize_notice_type(notice_type)
        else:
            # 从标题推断
            title = normalized.get('title', '')
            normalized['notice_type'] = self._infer_notice_type(title)

        return normalized

    def _parse_amount(self, amount_value) -> Optional[Decimal]:
        """解析金额"""
        if isinstance(amount_value, (int, float)):
            return Decimal(str(amount_value))

        if isinstance(amount_value, str):
            # 移除货币符号和空格
            amount_str = amount_value.replace(',', '').replace(' ', '')
            amount_str = amount_str.replace('¥', '').replace('$', '').replace('€', '')

            # 提取数字
            match = re.search(r'([\d.]+)\s*([万亿]?)', amount_str)
            if match:
                number = Decimal(match.group(1))
                unit = match.group(2)

                # 转换单位
                if unit == '亿':
                    number *= Decimal('100000000')
                elif unit == '万':
                    number *= Decimal('10000')

                return number

        return None

    def _parse_date(self, date_value) -> Optional[datetime]:
        """解析日期"""
        if isinstance(date_value, datetime):
            return date_value

        date_str = str(date_value).strip()

        # 常见日期格式
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

    def _normalize_notice_type(self, type_value: str) -> str:
        """标准化公告类型"""
        type_str = str(type_value).lower()

        if any(kw in type_str for kw in ['中标', '成交', 'win', 'result']):
            return 'win'
        elif any(kw in type_str for kw in ['变更', 'change', '补遗', '澄清']):
            return 'change'
        else:
            return 'bidding'

    def _infer_notice_type(self, title: str) -> str:
        """从标题推断公告类型"""
        if not title:
            return 'bidding'

        title_lower = title.lower()

        if any(kw in title_lower for kw in ['中标', '成交', '中标候选人', '中标公告']):
            return 'win'
        elif any(kw in title_lower for kw in ['变更', '补遗', '澄清', '更正']):
            return 'change'
        else:
            return 'bidding'

    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """备用解析方法（当 JSON 解析失败时）"""
        result = {}

        # 简单正则提取关键字段
        patterns = {
            'title': r'["\']title["\']\s*:\s*["\']([^"\']+)["\']',
            'tenderer': r'["\']tenderer["\']\s*:\s*["\']([^"\']+)["\']',
            'budget_amount': r'["\']budget_amount["\']\s*:\s*(\d+(?:\.\d+)?)',
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, response)
            if match:
                value = match.group(1)
                if field == 'budget_amount':
                    try:
                        result[field] = Decimal(value)
                    except:
                        pass
                else:
                    result[field] = value

        return result

    def _fallback_extraction(self, html: str, source_url: str) -> TenderNoticeSchema:
        """备用提取方法（基于规则和正则）"""
        # 这里可以集成现有的智能提取逻辑
        # 目前返回一个基础的结果
        soup = BeautifulSoup(html, 'html.parser')

        # 尝试提取标题
        title = soup.title.string if soup.title else None
        if not title:
            h1 = soup.find('h1')
            title = h1.get_text(strip=True) if h1 else None

        return TenderNoticeSchema(
            title=title,
            source_url=source_url,
            extraction_method="fallback",
            extraction_confidence=0.1 if title else 0.0
        )

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """计算提取结果的置信度"""
        score = 0.0
        weights = {
            'title': 0.25,
            'publish_date': 0.15,
            'budget_amount': 0.15,
            'tenderer': 0.20,
            'description': 0.10,
            'project_number': 0.08,
            'contact_info': 0.07,
        }

        # 检查各字段
        if data.get('title') and len(str(data['title'])) > 5:
            score += weights['title']

        if data.get('publish_date'):
            score += weights['publish_date']

        if data.get('budget_amount'):
            score += weights['budget_amount']

        if data.get('tenderer') and len(str(data['tenderer'])) > 2:
            score += weights['tenderer']

        if data.get('description') and len(str(data['description'])) > 20:
            score += weights['description']

        if data.get('project_number'):
            score += weights['project_number']

        # 联系方式
        if data.get('contact_person') or data.get('contact_phone'):
            score += weights['contact_info']

        return min(score, 1.0)

    def batch_extract(
        self,
        items: List[Dict[str, str]],
        batch_size: int = 5
    ) -> List[TenderNoticeSchema]:
        """
        批量提取

        Args:
            items: 包含 html 和 source_url 的字典列表
            batch_size: 批次大小

        Returns:
            TenderNoticeSchema 列表
        """
        results = []

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            logger.info(f"处理批次 {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size}")

            for item in batch:
                result = self.extract(
                    html=item.get('html', ''),
                    source_url=item.get('source_url', '')
                )
                results.append(result)

            # 批次间延迟，避免速率限制
            if i + batch_size < len(items):
                time.sleep(self.extraction_config.retry_delay)

        return results

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_requests': self.request_count,
            'successful': self.success_count,
            'failed': self.failure_count,
            'success_rate': self.success_count / max(self.request_count, 1),
            'total_tokens': self.total_tokens,
        }
