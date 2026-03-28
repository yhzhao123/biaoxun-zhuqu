"""
增强型招标信息提取编排器 V2

集成4个智能体团队协同工作:
1. ConcurrencyControlAgent - 并发控制
2. RetryMechanismAgent - 重试机制
3. CacheAgent - 缓存系统
4. FieldOptimizationAgent - 字段提取优化
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from apps.crawler.agents.schema import ExtractionStrategy, TenderNoticeSchema, DetailResult
from apps.crawler.agents.agents.fetcher_agents import ListFetcherAgent, DetailFetcherAgent
from apps.crawler.agents.agents.field_extractor import FieldExtractorAgent
from apps.crawler.agents.agents.pdf_processor import PDFProcessorAgent
from apps.crawler.agents.workers.concurrency_agent import ConcurrencyControlAgent, ConcurrencyConfig
from apps.crawler.agents.workers.retry_agent import RetryMechanismAgent, RetryConfig
from apps.crawler.agents.workers.cache_agent import CacheAgent, CacheConfig
from apps.crawler.agents.workers.field_optimizer import FieldOptimizationAgent, FieldOptimizationConfig

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorV2Config:
    """编排器V2配置"""
    # 并发配置
    max_concurrent_requests: int = 5
    max_concurrent_llm_calls: int = 2  # 降低LLM并发避免429
    max_concurrent_details: int = 8
    request_delay: float = 1.0
    llm_delay: float = 1.0

    # 重试配置
    max_retries: int = 3
    base_delay: float = 2.0
    circuit_breaker_threshold: int = 5

    # 缓存配置
    cache_enabled: bool = True
    cache_ttl: int = 7200  # 2小时

    # 字段优化配置
    use_list_data: bool = True
    use_regex_preprocessing: bool = True

    # 批次配置
    batch_size: int = 20
    max_items_per_source: int = 100


class TenderOrchestratorV2:
    """
    增强型招标信息提取编排器 V2

    4个智能体团队协同工作，实现高效、稳定、智能的招标信息提取。
    """

    def __init__(self, config: OrchestratorV2Config = None):
        self.config = config or OrchestratorV2Config()

        # 初始化4个智能体团队
        self._init_agents()

        # 基础智能体
        self.list_fetcher = ListFetcherAgent()
        self.detail_fetcher = DetailFetcherAgent()
        self.field_extractor = FieldExtractorAgent()
        self.pdf_processor = PDFProcessorAgent()

        # 统计信息
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'llm_calls_saved': 0,
            'llm_calls_made': 0,
            'retries': 0,
            'circuit_breaker_tripped': 0,
        }

    def _init_agents(self):
        """初始化4个智能体团队"""
        # 团队1: 并发控制
        concurrency_config = ConcurrencyConfig(
            max_concurrent_requests=self.config.max_concurrent_requests,
            max_concurrent_llm_calls=self.config.max_concurrent_llm_calls,
            max_concurrent_details=self.config.max_concurrent_details,
            request_delay=self.config.request_delay,
            llm_delay=self.config.llm_delay,
        )
        self.concurrency_agent = ConcurrencyControlAgent(concurrency_config)

        # 团队2: 重试机制
        retry_config = RetryConfig(
            max_retries=self.config.max_retries,
            base_delay=self.config.base_delay,
            circuit_breaker_threshold=self.config.circuit_breaker_threshold,
        )
        self.retry_agent = RetryMechanismAgent(retry_config)
        self.retry_agent.set_concurrency_agent(self.concurrency_agent)

        # 团队3: 缓存系统
        cache_config = CacheConfig(
            default_ttl=self.config.cache_ttl,
        )
        self.cache_agent = CacheAgent(cache_config)

        # 团队4: 字段优化
        field_config = FieldOptimizationConfig(
            required_fields=[
                'title', 'tenderer', 'winner', 'budget_amount',
                'publish_date', 'deadline_date', 'project_number',
                'contact_person', 'contact_phone', 'description'
            ],
            use_regex_preprocessing=self.config.use_regex_preprocessing,
            llm_fallback_threshold=0.6,
        )
        self.field_optimizer = FieldOptimizationAgent(field_config)

        logger.info("All 4 agent teams initialized successfully")

    async def extract_tenders(
        self,
        source_config: Any,
        max_pages: Optional[int] = None
    ) -> List[TenderNoticeSchema]:
        """
        提取招标信息（增强版）

        Args:
            source_config: 爬取源配置
            max_pages: 最大页数

        Returns:
            提取的招标信息列表
        """
        logger.info(f"Starting enhanced extraction for source: {source_config.name}")
        start_time = asyncio.get_event_loop().time()

        try:
            # Step 1: 获取列表（带缓存）
            list_items = await self._fetch_list_with_cache(source_config, max_pages)
            logger.info(f"Fetched {len(list_items)} items from list")

            # Step 2: 批量处理详情页（带并发控制）
            results = await self._process_items_batch(list_items[:self.config.max_items_per_source])

            # Step 3: 重试失败项
            if self.retry_agent.get_failed_items():
                logger.info("Retrying failed items...")
                retry_results = await self.retry_agent.retry_failed_items(
                    self._process_single_item_retry
                )
                results.extend([r for r in retry_results if r])

            # Step 4: 输出统计
            duration = asyncio.get_event_loop().time() - start_time
            self._log_stats(duration)

            return results

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

    async def _fetch_list_with_cache(
        self,
        source_config: Any,
        max_pages: Optional[int]
    ) -> List[Dict]:
        """获取列表（带缓存）"""
        cache_key = f"list_{source_config.id}_{max_pages or 'all'}"

        # 尝试从缓存获取
        if self.config.cache_enabled:
            hit, cached = self.cache_agent.get(cache_key, source_config.id)
            if hit:
                logger.info("List cache hit")
                self.stats['cache_hits'] += 1
                return cached

        # 获取策略
        from apps.crawler.agents.agents.url_analyzer import URLAnalyzerAgent
        analyzer = URLAnalyzerAgent()
        strategy = await asyncio.to_thread(
            analyzer._analyze_api_source, source_config
        )

        if max_pages:
            strategy.max_pages = max_pages

        # 获取列表（带重试）
        items = await self.retry_agent.execute_with_retry(
            self.list_fetcher.fetch,
            strategy
        )

        # 缓存结果
        if self.config.cache_enabled:
            self.cache_agent.set(cache_key, items, ttl=1800, source_id=source_config.id)
            self.stats['cache_misses'] += 1

        return items

    async def _process_items_batch(self, items: List[Dict]) -> List[TenderNoticeSchema]:
        """批量处理列表项"""

        async def process_with_limit(item: Dict) -> Optional[TenderNoticeSchema]:
            """带限制的处理单个项"""
            async with self.concurrency_agent.detail_semaphore:
                return await self._process_single_item(item)

        # 分批处理
        results = []
        batch_size = self.config.batch_size

        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}: {len(batch)} items")

            tasks = [process_with_limit(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, TenderNoticeSchema):
                    results.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Batch processing error: {result}")

            # 批次间延迟
            await asyncio.sleep(self.config.request_delay)

        return results

    async def _process_single_item(self, item: Dict) -> Optional[TenderNoticeSchema]:
        """处理单个列表项"""
        url = item.get('url')
        if not url:
            return None

        try:
            # 1. 检查缓存
            if self.config.cache_enabled:
                hit, cached = self.cache_agent.get(url)
                if hit:
                    logger.info(f"Detail cache hit: {url}")
                    self.stats['cache_hits'] += 1
                    # 转换回DetailResult
                    from apps.crawler.agents.schema import DetailResult
                    if isinstance(cached, dict):
                        cached = DetailResult.from_dict(cached)
                    # 使用字段优化器从列表预填充
                    return await self._optimize_and_extract(cached, item, url)

            # 2. 获取详情页
            detail = await self.concurrency_agent.execute_with_request_limit(
                self.detail_fetcher.fetch,
                item
            )

            if not detail:
                raise Exception("Failed to fetch detail page")

            # 3. 缓存详情页
            if self.config.cache_enabled:
                self.cache_agent.set(url, detail.to_dict(), source_id=item.get('source_id'))
                self.stats['cache_misses'] += 1

            # 4. 提取字段
            result = await self._optimize_and_extract(detail, item, url)

            # 5. 处理PDF附件
            if detail.attachments:
                result = await self._process_attachments(result, detail.attachments)

            return result

        except Exception as e:
            logger.error(f"Failed to process item {url}: {e}")
            # 添加到重试队列
            await self.retry_agent.add_failed_item(item, str(e))
            return None

    async def _process_single_item_retry(self, item: Dict) -> Optional[TenderNoticeSchema]:
        """重试处理单个项"""
        self.stats['retries'] += 1
        return await self._process_single_item(item)

    async def _optimize_and_extract(
        self,
        detail: DetailResult,
        list_item: Dict,
        url: str
    ) -> TenderNoticeSchema:
        """使用字段优化器提取字段（支持PDF正文）"""

        # 如果存在正文PDF内容，优先使用PDF内容进行提取
        if detail.main_pdf_content:
            logger.info(f"Using main PDF content for extraction: {url}")
            return await self._extract_from_pdf_content(
                detail.main_pdf_content,
                detail.main_pdf_filename or 'document.pdf',
                list_item,
                url,
                detail.main_pdf_url
            )

        if self.config.use_list_data:
            # 使用优化版本：先提取列表页字段
            result = await self.field_optimizer.optimize_extraction(
                list_item, detail.html, url, self.field_extractor
            )

            # 统计节省的LLM调用
            if result.llm_called:
                self.stats['llm_calls_made'] += 1
            else:
                self.stats['llm_calls_saved'] += 1

            # Convert ExtractionResult to TenderNoticeSchema
            return TenderNoticeSchema.from_dict(result.data)
        else:
            # 传统方式：直接调用LLM
            self.stats['llm_calls_made'] += 1
            return await self.field_extractor.extract(detail.html, url)

    async def _extract_from_pdf_content(
        self,
        pdf_content: str,
        pdf_filename: str,
        list_item: Dict,
        url: str,
        main_pdf_url: Optional[str] = None
    ) -> TenderNoticeSchema:
        """从PDF正文内容中提取字段"""
        try:
            # 尝试使用PDF处理器提取
            from apps.crawler.agents.agents.pdf_processor import PDFProcessorAgent

            pdf_processor = PDFProcessorAgent()

            # 使用PDF处理器的提取方法
            extracted = await self._extract_from_pdf_text(pdf_content, list_item)

            # 创建结果
            result = TenderNoticeSchema(
                title=list_item.get('title') or extracted.get('title'),
                tenderer=extracted.get('tenderer'),
                winner=extracted.get('winner'),
                contact_person=extracted.get('contact_person'),
                contact_phone=extracted.get('contact_phone'),
                project_number=extracted.get('project_number'),
                description=pdf_content[:2000] if len(pdf_content) > 2000 else pdf_content,
                source_url=url,
                source_site=list_item.get('source_site', ''),
                extraction_method='pdf_main_content',
                extraction_confidence=0.85 if extracted.get('tenderer') else 0.6
            )

            self.stats['llm_calls_made'] += 1
            return result

        except Exception as e:
            logger.error(f"PDF content extraction failed: {e}")
            # 失败时回退到传统方法
            return await self.field_extractor.extract_from_text(pdf_content, url)

    async def _extract_from_pdf_text(self, text: str, list_item: Dict) -> Dict:
        """从PDF文本中提取字段（使用正则或简单规则）"""
        import re

        result = {}

        # 从list_item获取标题
        result['title'] = list_item.get('title')

        # 正则提取字段
        patterns = {
            'tenderer': r'(招标人|采购人|采购单位)[：:]\s*([^\n]+)',
            'contact_person': r'(联系人|经办人)[：:]\s*([^\n]+)',
            'contact_phone': r'(联系电话|联系方式|电话)[：:]\s*([^\n]+)',
            'project_number': r'(项目编号|采购编号|招标编号)[：:]\s*([^\n]+)',
            'budget_amount': r'(预算金额|最高限价)[：:]\s*([^\n]+)',
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                result[field] = match.group(2).strip()

        # 提取预算金额并转换
        if 'budget_amount' in result:
            amount_str = result['budget_amount']
            # 匹配数字
            num_match = re.search(r'[\d,\.]+', amount_str)
            if num_match:
                try:
                    amount = float(num_match.group().replace(',', ''))
                    # 检测单位
                    if '万' in amount_str:
                        amount *= 10000
                    result['budget_amount'] = amount
                except:
                    pass

        return result

    async def _process_attachments(
        self,
        result: TenderNoticeSchema,
        attachments: List[Any]
    ) -> TenderNoticeSchema:
        """处理PDF附件"""
        for attachment in attachments:
            if attachment.type == 'pdf':
                try:
                    pdf_data = await self.retry_agent.execute_with_retry(
                        self.pdf_processor.process,
                        attachment
                    )

                    if pdf_data:
                        # 合并PDF提取的数据
                        for field in ['tenderer', 'contact_person', 'contact_phone']:
                            if pdf_data.get(field) and not getattr(result, field):
                                setattr(result, field, pdf_data[field])

                except Exception as e:
                    logger.warning(f"PDF processing failed for {attachment.filename}: {e}")

        return result

    def _log_stats(self, duration: float):
        """输出统计信息"""
        logger.info("=" * 50)
        logger.info("Extraction Statistics:")
        logger.info(f"  Duration: {duration:.2f}s")
        logger.info(f"  Cache hits: {self.stats['cache_hits']}")
        logger.info(f"  Cache misses: {self.stats['cache_misses']}")
        logger.info(f"  Cache hit rate: {self._calc_cache_rate():.1%}")
        logger.info(f"  LLM calls made: {self.stats['llm_calls_made']}")
        logger.info(f"  LLM calls saved: {self.stats['llm_calls_saved']}")
        logger.info(f"  Savings rate: {self._calc_savings_rate():.1%}")
        logger.info(f"  Retries: {self.stats['retries']}")
        logger.info("=" * 50)

        # 缓存统计
        cache_stats = self.cache_agent.get_stats()
        logger.info(f"Cache stats: {cache_stats}")

        # 重试统计
        retry_stats = self.retry_agent.get_stats()
        logger.info(f"Retry stats: {retry_stats}")

    def _calc_cache_rate(self) -> float:
        """计算缓存命中率"""
        total = self.stats['cache_hits'] + self.stats['cache_misses']
        return self.stats['cache_hits'] / total if total > 0 else 0

    def _calc_savings_rate(self) -> float:
        """计算LLM节省率"""
        total = self.stats['llm_calls_made'] + self.stats['llm_calls_saved']
        return self.stats['llm_calls_saved'] / total if total > 0 else 0

    async def close(self):
        """清理资源"""
        # 清理缓存
        self.cache_agent.cleanup_expired()

        # 重置重试代理
        await self.retry_agent.reset()

        logger.info("Orchestrator V2 closed")
