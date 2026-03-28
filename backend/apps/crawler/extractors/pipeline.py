"""
Extraction Pipeline - 提取管道

组合多种提取方式，按优先级尝试：
1. 结构化LLM提取（LLMExtractionService）- 新的首选方法
2. 智能提取（IntelligentExtractor）
3. 传统LLM提取（LLMContentExtractor）
4. CSS选择器提取（回退）

新增：集成4智能体团队协同工作
"""

import logging
from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal

from .intelligent_extractor import IntelligentExtractor
from .llm_extractor import LLMContentExtractor, get_llm_extractor
from .llm_extraction_service import LLMExtractionService, ExtractionConfig
from .structured_schema import TenderNoticeSchema

# 导入4智能体团队
from apps.crawler.agents import (
    ConcurrencyControlAgent, ConcurrencyConfig,
    RetryMechanismAgent, RetryConfig,
    CacheAgent, CacheConfig,
    FieldOptimizationAgent, FieldOptimizationConfig,
)

logger = logging.getLogger(__name__)


class ExtractionResult:
    """提取结果封装"""

    def __init__(self, data: Dict = None, schema: TenderNoticeSchema = None):
        """
        初始化提取结果

        Args:
            data: 传统字典数据（向后兼容）
            schema: 新的结构化 Schema 数据
        """
        if schema:
            # 从 Schema 转换
            self._schema = schema
            self.data = schema.to_dict()
            self.data['extraction_method'] = schema.extraction_method
            self.data['confidence'] = schema.extraction_confidence
            self.extraction_method = schema.extraction_method
            self.confidence = schema.extraction_confidence
        elif data:
            # 从字典转换
            self._schema = None
            self.data = data
            self.extraction_method = data.get('extraction_method', 'unknown')
            self.confidence = self._calculate_confidence()
        else:
            self._schema = None
            self.data = {}
            self.extraction_method = 'unknown'
            self.confidence = 0.0

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

    def to_model_fields(self) -> Dict:
        """转换为 TenderNotice 模型字段"""
        if self._schema:
            return self._schema.to_model_fields()
        # 向后兼容
        return {
            'title': self.data.get('title', ''),
            'description': self.data.get('description', ''),
            'tenderer': self.data.get('tenderer', ''),
            'budget': self.data.get('budget'),
            'publish_date': self.data.get('publish_date'),
            'source_url': self.data.get('source_url', ''),
            'notice_type': self.data.get('notice_type', 'bidding'),
        }


class ExtractionPipeline:
    """
    提取管道

    按优先级尝试多种提取方式，直到获得满意的结果
    新的优先级：结构化LLM > 智能提取 > 传统LLM > CSS选择器

    集成4智能体团队：
    - ConcurrencyControlAgent: 控制并发和速率限制
    - RetryMechanismAgent: 处理重试和熔断
    - CacheAgent: 缓存提取结果
    - FieldOptimizationAgent: 优化字段提取，减少LLM调用
    """

    # 提取策略优先级
    EXTRACTION_STRATEGIES = [
        ('structured_llm', '结构化LLM提取'),
        ('intelligent', '智能提取'),
        ('llm', 'LLM提取'),
        ('selector', 'CSS选择器'),
    ]

    def __init__(
        self,
        use_structured_llm: bool = True,
        use_llm: bool = True,
        use_intelligent: bool = True,
        extraction_config: Optional[ExtractionConfig] = None,
        # 智能体团队配置
        use_agent_teams: bool = True,
        concurrency_config: Optional[ConcurrencyConfig] = None,
        retry_config: Optional[RetryConfig] = None,
        cache_config: Optional[CacheConfig] = None,
        field_optimization_config: Optional[FieldOptimizationConfig] = None,
    ):
        """
        初始化提取管道

        Args:
            use_structured_llm: 是否启用结构化LLM提取（新）
            use_llm: 是否启用传统LLM提取
            use_intelligent: 是否启用智能提取
            extraction_config: 结构化提取配置
            use_agent_teams: 是否启用4智能体团队
            concurrency_config: 并发控制配置
            retry_config: 重试机制配置
            cache_config: 缓存配置
            field_optimization_config: 字段优化配置
        """
        self.use_structured_llm = use_structured_llm
        self.use_llm = use_llm
        self.use_intelligent = use_intelligent
        self.use_agent_teams = use_agent_teams

        # 初始化各提取器
        self.structured_llm_service = None
        self.intelligent_extractor = None
        self.llm_extractor = None

        # 初始化4智能体团队
        self.concurrency_agent = None
        self.retry_agent = None
        self.cache_agent = None
        self.field_optimizer = None

        # 结构化LLM提取器
        if use_structured_llm:
            try:
                self.structured_llm_service = LLMExtractionService(
                    extraction_config=extraction_config or ExtractionConfig()
                )
                logger.info("结构化LLM提取服务初始化成功")
            except Exception as e:
                logger.warning(f"结构化LLM提取服务初始化失败: {e}")

        # 智能提取器
        if use_intelligent:
            try:
                self.intelligent_extractor = IntelligentExtractor()
            except Exception as e:
                logger.warning(f"智能提取器初始化失败: {e}")

        # 传统LLM提取器
        if use_llm:
            try:
                self.llm_extractor = get_llm_extractor()
            except Exception as e:
                logger.warning(f"传统LLM提取器初始化失败: {e}")

        # 初始化4智能体团队
        if use_agent_teams:
            self._init_agent_teams(
                concurrency_config,
                retry_config,
                cache_config,
                field_optimization_config
            )

    def _init_agent_teams(
        self,
        concurrency_config: Optional[ConcurrencyConfig],
        retry_config: Optional[RetryConfig],
        cache_config: Optional[CacheConfig],
        field_optimization_config: Optional[FieldOptimizationConfig],
    ):
        """初始化4智能体团队"""
        try:
            # 团队1: 并发控制
            self.concurrency_agent = ConcurrencyControlAgent(
                concurrency_config or ConcurrencyConfig()
            )
            logger.info("[Agent Team 1] ConcurrencyControlAgent initialized")

            # 团队2: 重试机制
            self.retry_agent = RetryMechanismAgent(
                retry_config or RetryConfig()
            )
            self.retry_agent.set_concurrency_agent(self.concurrency_agent)
            logger.info("[Agent Team 2] RetryMechanismAgent initialized")

            # 团队3: 缓存系统
            self.cache_agent = CacheAgent(
                cache_config or CacheConfig()
            )
            logger.info("[Agent Team 3] CacheAgent initialized")

            # 团队4: 字段优化
            self.field_optimizer = FieldOptimizationAgent(
                field_optimization_config or FieldOptimizationConfig()
            )
            logger.info("[Agent Team 4] FieldOptimizationAgent initialized")

            logger.info("All 4 agent teams initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent teams: {e}")
            self.use_agent_teams = False

    def extract(
        self,
        html: str,
        selectors: Dict = None,
        source_url: str = '',
        list_item: Dict = None,
    ) -> ExtractionResult:
        """
        执行提取管道

        Args:
            html: HTML内容
            selectors: CSS选择器配置（回退用）
            source_url: 来源URL
            list_item: 列表页数据（用于字段优化）

        Returns:
            ExtractionResult对象
        """
        # 检查缓存（如果启用）
        if self.use_agent_teams and self.cache_agent and source_url:
            hit, cached_data = self.cache_agent.get(source_url)
            if hit and cached_data:
                logger.info(f"Cache hit for {source_url}")
                if isinstance(cached_data, dict):
                    return ExtractionResult(cached_data)
                elif isinstance(cached_data, TenderNoticeSchema):
                    return ExtractionResult(schema=cached_data)

        results = []

        # 策略0: 字段优化（如果启用且有列表数据）
        if self.use_agent_teams and self.field_optimizer and list_item:
            try:
                logger.debug(f"尝试字段优化提取: {source_url}")
                optimized_result = self.field_optimizer.optimize_extraction(
                    list_item, html, source_url, self.llm_extractor
                )
                if optimized_result.data:
                    result = ExtractionResult(optimized_result.data)
                    if result.is_valid(min_confidence=0.5):
                        logger.info(
                            f"字段优化提取成功: {source_url}, "
                            f"LLM调用: {optimized_result.llm_called}"
                        )
                        # 缓存结果
                        if self.cache_agent:
                            self.cache_agent.set(source_url, optimized_result.data)
                        return result
                    results.append(('field_optimized', result))
            except Exception as e:
                logger.warning(f"字段优化提取失败: {e}")

        # 策略1: 结构化LLM提取（新的首选方法）
        if self.use_structured_llm and self.structured_llm_service:
            try:
                logger.debug(f"尝试结构化LLM提取: {source_url}")
                schema_result = self.structured_llm_service.extract(html, source_url)
                result = ExtractionResult(schema=schema_result)
                if result.is_valid(min_confidence=0.4):
                    logger.info(
                        f"结构化LLM提取成功: {source_url}, "
                        f"置信度: {result.confidence:.2f}"
                    )
                    # 缓存结果
                    if self.cache_agent:
                        self.cache_agent.set(source_url, schema_result)
                    return result
                results.append(('structured_llm', result))
            except Exception as e:
                logger.warning(f"结构化LLM提取失败: {e}")

        # 策略2: 智能提取
        if self.use_intelligent and self.intelligent_extractor:
            try:
                logger.debug(f"尝试智能提取: {source_url}")
                intelligent_result = self.intelligent_extractor.extract(html)
                result = ExtractionResult(intelligent_result)
                if result.is_valid():
                    logger.info(f"智能提取成功: {source_url}, 置信度: {result.confidence:.2f}")
                    # 缓存结果
                    if self.cache_agent:
                        self.cache_agent.set(source_url, intelligent_result)
                    return result
                results.append(('intelligent', result))
            except Exception as e:
                logger.warning(f"智能提取失败: {e}")

        # 策略3: 传统LLM提取
        if self.use_llm and self.llm_extractor:
            try:
                logger.debug(f"尝试传统LLM提取: {source_url}")
                llm_result = self.llm_extractor.extract(html, source_url)
                if 'error' not in llm_result:
                    result = ExtractionResult(llm_result)
                    if result.is_valid():
                        logger.info(f"传统LLM提取成功: {source_url}, 置信度: {result.confidence:.2f}")
                        # 缓存结果
                        if self.cache_agent:
                            self.cache_agent.set(source_url, llm_result)
                        return result
                    results.append(('llm', result))
            except Exception as e:
                logger.warning(f"传统LLM提取失败: {e}")

        # 策略4: CSS选择器提取（如果有配置）
        if selectors:
            try:
                logger.debug(f"尝试CSS选择器提取: {source_url}")
                selector_result = self._extract_with_selectors(html, selectors)
                result = ExtractionResult(selector_result)
                if result.is_valid():
                    logger.info(f"CSS选择器提取成功: {source_url}, 置信度: {result.confidence:.2f}")
                    return result
                results.append(('selector', result))
            except Exception as e:
                logger.warning(f"CSS选择器提取失败: {e}")

        # 返回最佳结果
        if results:
            best = max(results, key=lambda x: x[1].confidence)
            logger.info(
                f"返回最佳结果 [{best[0]}], "
                f"置信度: {best[1].confidence:.2f}"
            )
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