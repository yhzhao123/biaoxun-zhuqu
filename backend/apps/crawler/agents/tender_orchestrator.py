"""
招标信息提取编排器

协调多个专业智能体完成完整的提取流程
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional

from apps.crawler.models import CrawlSource
from apps.crawler.agents.schema import (
    TenderNoticeSchema,
    ExtractionStrategy,
    ValidationResult
)

logger = logging.getLogger(__name__)


class TenderOrchestrator:
    """
    招标信息提取编排器

    协调多个专业智能体完成完整的提取流程：
    1. URLAnalyzerAgent - 分析爬取源配置
    2. ListFetcherAgent - 获取列表页数据
    3. DetailFetcherAgent - 获取详情页HTML和附件
    4. FieldExtractorAgent - 从HTML提取字段
    5. PDFProcessorAgent - 处理PDF附件
    6. ValidatorAgent - 验证结果
    7. ComposerAgent - 合并多源数据
    """

    def __init__(self):
        # 延迟导入，避免循环依赖
        self._agents: Dict[str, Any] = {}
        self._memory = None

    def _get_agent(self, name: str):
        """延迟加载智能体"""
        if name not in self._agents:
            if name == 'url_analyzer':
                from .agents.url_analyzer import URLAnalyzerAgent
                self._agents[name] = URLAnalyzerAgent()
            elif name == 'list_fetcher':
                from .agents.fetcher_agents import ListFetcherAgent
                self._agents[name] = ListFetcherAgent()
            elif name == 'detail_fetcher':
                from .agents.fetcher_agents import DetailFetcherAgent
                self._agents[name] = DetailFetcherAgent()
            elif name == 'field_extractor':
                from .agents.field_extractor import FieldExtractorAgent
                self._agents[name] = FieldExtractorAgent()
            elif name == 'pdf_processor':
                from .agents.pdf_processor import PDFProcessorAgent
                self._agents[name] = PDFProcessorAgent()
            elif name == 'validator':
                from .agents.validator import ValidatorAgent
                self._agents[name] = ValidatorAgent()
            elif name == 'composer':
                from .agents.composer import ComposerAgent
                self._agents[name] = ComposerAgent()
        return self._agents.get(name)

    async def extract_tender(
        self,
        source_config: CrawlSource,
        max_pages: Optional[int] = None
    ) -> List[TenderNoticeSchema]:
        """
        完整的招标信息提取流程

        Args:
            source_config: 爬取源配置
            max_pages: 最大爬取页数（覆盖配置）

        Returns:
            提取的招标信息列表
        """
        results = []

        try:
            # Step 1: 分析爬取源配置
            logger.info(f"[Step 1/8] Analyzing source: {source_config.name}")
            strategy = await self._analyze_source(source_config)

            if max_pages:
                strategy.max_pages = max_pages

            # Step 2: 获取列表页数据
            logger.info(f"[Step 2/8] Fetching list pages (max {strategy.max_pages})")
            list_items = await self._fetch_list(strategy)
            logger.info(f"Found {len(list_items)} items from list pages")

            # 处理每个列表项
            for idx, item in enumerate(list_items, 1):
                try:
                    logger.info(f"[Item {idx}/{len(list_items)}] Processing: {item.get('title', 'N/A')[:50]}...")

                    # Step 3-7: 处理单个条目
                    result = await self._process_single_item(item, strategy)
                    if result:
                        results.append(result)

                except Exception as e:
                    logger.error(f"Failed to process item {idx}: {e}")
                    continue

            logger.info(f"[Step 8/8] Extraction complete. Total results: {len(results)}")

        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

        return results

    async def _analyze_source(self, source_config: CrawlSource) -> ExtractionStrategy:
        """Step 1: 分析爬取源"""
        agent = self._get_agent('url_analyzer')
        return await agent.analyze(source_config)

    async def _fetch_list(self, strategy: ExtractionStrategy) -> List[Dict]:
        """Step 2: 获取列表页数据"""
        agent = self._get_agent('list_fetcher')
        return await agent.fetch(strategy)

    async def _process_single_item(
        self,
        item: Dict,
        strategy: ExtractionStrategy
    ) -> Optional[TenderNoticeSchema]:
        """
        处理单个招标条目（Steps 3-7）
        """
        # Step 3: 获取详情页
        logger.info(f"  [Step 3/7] Fetching detail page")
        detail_result = await self._fetch_detail(item)
        if not detail_result:
            return None

        # Step 4: 提取字段（HTML）
        logger.info(f"  [Step 4/7] Extracting fields from HTML")
        extracted = await self._extract_fields(detail_result)

        # Step 5: 处理PDF附件（如果有）
        if detail_result.attachments:
            logger.info(f"  [Step 5/7] Processing {len(detail_result.attachments)} attachments")
            for pdf in detail_result.attachments:
                pdf_data = await self._process_pdf(pdf)
                if pdf_data:
                    extracted = await self._merge_data(extracted, pdf_data, 'pdf')
        else:
            logger.info(f"  [Step 5/7] No attachments")

        # Step 6: 验证结果
        logger.info(f"  [Step 6/7] Validating result")
        validation = await self._validate(extracted)

        if not validation.is_complete:
            logger.warning(f"  Missing fields: {validation.missing_fields}")
            # 补充缺失字段
            extracted = await self._complete_missing_fields(
                extracted,
                validation.missing_fields,
                detail_result.html
            )

        # Step 7: 合并列表页数据
        logger.info(f"  [Step 7/7] Composing final result (confidence: {validation.confidence:.2f})")
        final_result = await self._merge_list_data(extracted, item)

        return final_result

    async def _fetch_detail(self, item: Dict) -> Optional[Any]:
        """Step 3: 获取详情页"""
        agent = self._get_agent('detail_fetcher')
        return await agent.fetch(item)

    async def _extract_fields(self, detail_result: Any) -> TenderNoticeSchema:
        """Step 4: 提取字段"""
        agent = self._get_agent('field_extractor')
        return await agent.extract(
            html=detail_result.html,
            url=detail_result.url
        )

    async def _process_pdf(self, attachment: Any) -> Optional[Dict]:
        """Step 5: 处理PDF"""
        agent = self._get_agent('pdf_processor')
        return await agent.process(attachment)

    async def _validate(self, data: TenderNoticeSchema) -> ValidationResult:
        """Step 6: 验证结果"""
        agent = self._get_agent('validator')
        return await agent.validate(data)

    async def _complete_missing_fields(
        self,
        data: TenderNoticeSchema,
        missing_fields: List[str],
        html: str
    ) -> TenderNoticeSchema:
        """补充缺失字段"""
        # 使用FieldExtractorAgent再次尝试提取
        agent = self._get_agent('field_extractor')
        return await agent.extract_missing(data, missing_fields, html)

    async def _merge_data(
        self,
        base: TenderNoticeSchema,
        new_data: Dict,
        source: str
    ) -> TenderNoticeSchema:
        """合并数据"""
        agent = self._get_agent('composer')
        return await agent.merge(base, new_data, source)

    async def _merge_list_data(
        self,
        detail_data: TenderNoticeSchema,
        list_item: Dict
    ) -> TenderNoticeSchema:
        """合并列表页数据"""
        # 列表页数据作为补充
        list_data = {
            'title': list_item.get('title'),
            'budget_amount': list_item.get('budget'),
            'publish_date': list_item.get('publish_date'),
            'source_url': list_item.get('url'),
            'source': 'api_list'
        }

        agent = self._get_agent('composer')
        return await agent.merge(detail_data, list_data, 'api_list')
