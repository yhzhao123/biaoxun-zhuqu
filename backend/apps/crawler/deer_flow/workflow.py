"""
Tender Extraction Workflow for deer-flow

招标信息提取 Workflow 编排
将 ListFetcherTool 和 DetailFetcherTool 组合为完整提取流程
"""
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from apps.crawler.tools.list_fetcher_tool import ListFetcherTool, ListFetchResult
from apps.crawler.tools.detail_fetcher_tool import DetailFetcherTool, DetailFetchResult

logger = logging.getLogger(__name__)


@dataclass
class WorkflowConfig:
    """Workflow 配置"""
    max_concurrent_requests: int = 5
    max_retries: int = 3
    request_delay: float = 1.0
    max_items_per_source: int = 100


@dataclass
class ExtractionResult:
    """提取结果"""
    items: List[Dict[str, Any]] = field(default_factory=list)
    details: List[Dict[str, Any]] = field(default_factory=list)
    success: bool = False
    error_message: Optional[str] = None
    total_fetched: int = 0
    total_with_details: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "items": self.items,
            "details": self.details,
            "success": self.success,
            "error_message": self.error_message,
            "total_fetched": self.total_fetched,
            "total_with_details": self.total_with_details,
        }


class TenderExtractionWorkflow:
    """
    招标信息提取 Workflow

    编排 ListFetcherTool 和 DetailFetcherTool 完成完整提取流程
    """

    def __init__(self, config: Optional[WorkflowConfig] = None):
        self.config = config or WorkflowConfig()
        self.logger = logging.getLogger(__name__)
        self._metrics = {
            "list_calls": 0,
            "detail_calls": 0,
            "errors": 0,
            "items_fetched": 0,
        }

    async def extract(
        self,
        source_url: str,
        site_type: str = "api",
        max_pages: int = 5,
        api_config: Optional[str] = None,
        max_items: Optional[int] = None,
    ) -> ExtractionResult:
        """
        从单一源提取招标列表

        Args:
            source_url: 源 URL
            site_type: 网站类型
            max_pages: 最大页数
            api_config: API 配置 JSON
            max_items: 最大项目数

        Returns:
            ExtractionResult: 提取结果
        """
        try:
            self.logger.info(f"Starting extraction from {source_url}")

            # 使用 ListFetcherTool 类
            import aiohttp
            from apps.crawler.agents.schema import ExtractionStrategy

            config = json.loads(api_config) if api_config else {}
            strategy = ExtractionStrategy(
                source_name=source_url,
                site_type=site_type,
                api_config=config,
                max_pages=max_pages,
                list_strategy=config.get("field_mapping", {}),
                pagination={"items_per_page": config.get("items_per_page", 10)},
            )

            tool = ListFetcherTool()
            list_result = await tool.fetch(strategy, max_pages=max_pages)

            self._metrics["list_calls"] += 1

            if not list_result.success:
                self.logger.error(f"List fetch failed: {list_result.error_message}")
                return ExtractionResult(
                    success=False,
                    error_message=list_result.error_message
                )

            items = list_result.items

            # 限制项目数
            if max_items and len(items) > max_items:
                items = items[:max_items]

            self._metrics["items_fetched"] += len(items)

            return ExtractionResult(
                items=items,
                success=True,
                total_fetched=len(items)
            )

        except Exception as e:
            self.logger.error(f"Extraction failed: {e}")
            self._metrics["errors"] += 1
            return ExtractionResult(
                success=False,
                error_message=str(e)
            )

    async def extract_with_details(
        self,
        source_url: str,
        site_type: str = "api",
        max_pages: int = 5,
        api_config: Optional[str] = None,
        max_items: Optional[int] = None,
        concurrent_limit: Optional[int] = None,
        fetch_details: bool = True,
    ) -> ExtractionResult:
        """
        提取招标列表并获取详情

        Args:
            source_url: 源 URL
            site_type: 网站类型
            max_pages: 最大页数
            api_config: API 配置 JSON
            max_items: 最大项目数
            concurrent_limit: 并发限制
            fetch_details: 是否获取详情

        Returns:
            ExtractionResult: 包含列表和详情的提取结果
        """
        # 首先获取列表
        list_result = await self.extract(
            source_url=source_url,
            site_type=site_type,
            max_pages=max_pages,
            api_config=api_config,
            max_items=max_items
        )

        if not list_result.success or not list_result.items:
            return list_result

        if not fetch_details:
            return list_result

        # 并发获取详情
        concurrent_limit = concurrent_limit or self.config.max_concurrent_requests
        semaphore = asyncio.Semaphore(concurrent_limit)

        async def fetch_detail_with_limit(item: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                url = item.get("url")
                if not url:
                    return {"error": "No URL in item"}

                try:
                    detail_tool = DetailFetcherTool()
                    detail_result = await detail_tool.fetch(
                        list_item=item,
                        extract_pdf=True
                    )
                    self._metrics["detail_calls"] += 1
                    return detail_result.to_dict()
                except Exception as e:
                    self.logger.error(f"Failed to fetch detail for {url}: {e}")
                    self._metrics["errors"] += 1
                    return {"error": str(e), "url": url}

        # 并发执行详情获取
        tasks = [fetch_detail_with_limit(item) for item in list_result.items]
        details = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_details = []
        for detail in details:
            if isinstance(detail, Exception):
                processed_details.append({"error": str(detail)})
            else:
                processed_details.append(detail)

        successful_details = [d for d in processed_details if d.get("success")]

        return ExtractionResult(
            items=list_result.items,
            details=processed_details,
            success=True,
            total_fetched=len(list_result.items),
            total_with_details=len(successful_details)
        )

    async def extract_batch(
        self,
        sources: List[Dict[str, Any]],
        max_items_per_source: Optional[int] = None,
        fetch_details: bool = False,
    ) -> List[ExtractionResult]:
        """
        批量处理多个源

        Args:
            sources: 源配置列表，每项包含 url 和 type
            max_items_per_source: 每源最大项目数
            fetch_details: 是否获取详情

        Returns:
            List[ExtractionResult]: 各源的提取结果
        """
        max_items = max_items_per_source or self.config.max_items_per_source

        async def process_source(source: Dict[str, Any]) -> ExtractionResult:
            if fetch_details:
                return await self.extract_with_details(
                    source_url=source["url"],
                    site_type=source.get("type", "api"),
                    max_items=max_items
                )
            else:
                return await self.extract(
                    source_url=source["url"],
                    site_type=source.get("type", "api"),
                    max_items=max_items
                )

        # 顺序处理以避免过载
        results = []
        for source in sources:
            result = await process_source(source)
            results.append(result)
            # 源间延迟
            await asyncio.sleep(self.config.request_delay)

        return results

    def get_metrics(self) -> Dict[str, Any]:
        """获取 Workflow 指标"""
        return {
            **self._metrics,
            "config": {
                "max_concurrent_requests": self.config.max_concurrent_requests,
                "max_retries": self.config.max_retries,
                "request_delay": self.config.request_delay,
            }
        }

    def reset_metrics(self):
        """重置指标"""
        self._metrics = {
            "list_calls": 0,
            "detail_calls": 0,
            "errors": 0,
            "items_fetched": 0,
        }
