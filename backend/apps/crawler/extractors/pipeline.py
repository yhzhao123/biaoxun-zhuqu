"""
Extraction Pipeline - 提取管道

组合多种提取方式，按优先级尝试：
1. 智能提取（IntelligentExtractor）
2. LLM提取（LLMContentExtractor）
3. CSS选择器提取（回退）
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal

from .intelligent_extractor import IntelligentExtractor
from .llm_extractor import LLMContentExtractor, get_llm_extractor

logger = logging.getLogger(__name__)


class ExtractionResult:
    """提取结果封装"""

    def __init__(self, data: Dict = None):
        self.data = data or {}
        self.extraction_method = data.get('extraction_method', 'unknown')
        self.confidence = self._calculate_confidence()

    def _calculate_confidence(self) -> float:
        """计算提取结果的置信度"""
        score = 0.0
        weights = {
            'title': 0.25,
            'publish_date': 0.20,
            'budget': 0.20,
            'tenderer': 0.20,
            'description': 0.15,
        }

        for field, weight in weights.items():
            if self.data.get(field):
                score += weight

        return min(score, 1.0)

    @property
    def title(self) -> Optional[str]:
        return self.data.get('title')

    @property
    def publish_date(self) -> Optional[datetime]:
        return self.data.get('publish_date')

    @property
    def budget(self) -> Optional[Decimal]:
        return self.data.get('budget')

    @property
    def tenderer(self) -> Optional[str]:
        return self.data.get('tenderer')

    @property
    def description(self) -> Optional[str]:
        return self.data.get('description')

    def is_valid(self, min_confidence: float = 0.3) -> bool:
        """检查提取结果是否有效"""
        return self.confidence >= min_confidence and self.title is not None


class ExtractionPipeline:
    """
    提取管道

    按优先级尝试多种提取方式，直到获得满意的结果
    """

    # 提取策略优先级
    EXTRACTION_STRATEGIES = [
        ('intelligent', '智能提取'),
        ('llm', 'LLM提取'),
        ('selector', 'CSS选择器'),
    ]

    def __init__(self, use_llm: bool = True, use_intelligent: bool = True):
        """
        初始化提取管道

        Args:
            use_llm: 是否启用LLM提取
            use_intelligent: 是否启用智能提取
        """
        self.use_llm = use_llm
        self.use_intelligent = use_intelligent

        self.intelligent_extractor = IntelligentExtractor() if use_intelligent else None
        self.llm_extractor = None

        if use_llm:
            try:
                self.llm_extractor = get_llm_extractor()
            except Exception as e:
                logger.warning(f"Failed to initialize LLM extractor: {e}")

    def extract(self, html: str, selectors: Dict = None, source_url: str = '') -> ExtractionResult:
        """
        执行提取管道

        Args:
            html: HTML内容
            selectors: CSS选择器配置（回退用）
            source_url: 来源URL

        Returns:
            ExtractionResult对象
        """
        results = []

        # 策略1: 智能提取
        if self.use_intelligent and self.intelligent_extractor:
            try:
                logger.debug(f"Trying intelligent extraction for {source_url}")
                intelligent_result = self.intelligent_extractor.extract(html)
                result = ExtractionResult(intelligent_result)
                if result.is_valid():
                    logger.info(f"Intelligent extraction succeeded for {source_url}, confidence: {result.confidence:.2f}")
                    return result
                results.append(('intelligent', result))
            except Exception as e:
                logger.warning(f"Intelligent extraction failed: {e}")

        # 策略2: LLM提取
        if self.use_llm and self.llm_extractor:
            try:
                logger.debug(f"Trying LLM extraction for {source_url}")
                llm_result = self.llm_extractor.extract(html, source_url)
                if 'error' not in llm_result:
                    result = ExtractionResult(llm_result)
                    if result.is_valid():
                        logger.info(f"LLM extraction succeeded for {source_url}, confidence: {result.confidence:.2f}")
                        return result
                    results.append(('llm', result))
            except Exception as e:
                logger.warning(f"LLM extraction failed: {e}")

        # 策略3: CSS选择器提取（如果有配置）
        if selectors:
            try:
                logger.debug(f"Trying selector extraction for {source_url}")
                selector_result = self._extract_with_selectors(html, selectors)
                result = ExtractionResult(selector_result)
                if result.is_valid():
                    logger.info(f"Selector extraction succeeded for {source_url}, confidence: {result.confidence:.2f}")
                    return result
                results.append(('selector', result))
            except Exception as e:
                logger.warning(f"Selector extraction failed: {e}")

        # 返回最佳结果
        if results:
            best = max(results, key=lambda x: x[1].confidence)
            logger.info(f"Returning best result from {best[0]} with confidence {best[1].confidence:.2f}")
            return best[1]

        return ExtractionResult({'error': 'All extraction methods failed'})

    def _extract_with_selectors(self, html: str, selectors: Dict) -> Dict:
        """
        使用CSS选择器提取

        Args:
            html: HTML内容
            selectors: 选择器配置

        Returns:
            提取结果字典
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')
        result = {'extraction_method': 'selector'}

        def extract_text(selector: str) -> str:
            if not selector:
                return ''
            elements = soup.select(selector)
            if elements:
                return elements[0].get_text(strip=True)
            return ''

        result['title'] = extract_text(selectors.get('title', ''))
        result['tenderer'] = extract_text(selectors.get('tenderer', ''))
        result['description'] = extract_text(selectors.get('content', ''))

        date_str = extract_text(selectors.get('publish_date', ''))
        if date_str:
            result['publish_date'] = self._parse_date(date_str)

        budget_str = extract_text(selectors.get('budget', ''))
        if budget_str:
            result['budget'] = self._parse_budget(budget_str)

        return result

    def _parse_date(self, date_str: str):
        """解析日期字符串"""
        from datetime import datetime
        import re

        if not date_str:
            return None

        # 中文格式
        match = re.match(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_str)
        if match:
            try:
                return datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                pass

        # 标准格式
        formats = ['%Y-%m-%d', '%Y/%m/%d', '%Y.%m.%d']
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip()[:10], fmt)
            except ValueError:
                continue

        return None

    def _parse_budget(self, budget_str: str):
        """解析预算字符串"""
        from decimal import Decimal, InvalidOperation
        import re

        if not budget_str:
            return None

        # 移除货币符号
        budget_str = re.sub(r'[¥￥$€,\s]', '', budget_str)

        # 匹配数字和单位
        match = re.match(r'([\d.]+)\s*(亿|万|元)?', budget_str)
        if match:
            try:
                amount = Decimal(match.group(1))
                unit = match.group(2)

                if unit == '亿':
                    amount = amount * Decimal('100000000')
                elif unit == '万':
                    amount = amount * Decimal('10000')

                return amount
            except (InvalidOperation, ValueError):
                pass

        return None

    def analyze_page(self, html: str) -> Dict:
        """
        分析页面结构，返回推荐的选择器

        Args:
            html: HTML内容

        Returns:
            分析结果和建议
        """
        if self.intelligent_extractor:
            return self.intelligent_extractor.analyze_page_structure(html)
        return {}