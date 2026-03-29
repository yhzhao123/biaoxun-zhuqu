"""
ListFetcherTool - 列表页爬取工具

将 ListFetcherAgent 封装为 Deer-Flow Tool
支持多级缓存
"""
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import aiohttp
from langchain.tools import tool

from apps.crawler.agents.agents.fetcher_agents import ListFetcherAgent
from apps.crawler.agents.schema import ExtractionStrategy
from apps.crawler.tools.cache import (
    MultiLevelCache,
    CacheKeyGenerator,
    get_default_cache,
)

logger = logging.getLogger(__name__)


# 全局缓存实例
_cache: Optional[MultiLevelCache] = None


def _get_cache() -> MultiLevelCache:
    """获取缓存实例"""
    global _cache
    if _cache is None:
        _cache = get_default_cache()
    return _cache


@dataclass
class ListFetchResult:
    """列表爬取结果"""
    items: List[Dict[str, Any]]
    total_count: int
    pages_fetched: int
    source_name: str
    success: bool
    error_message: Optional[str] = None
    cache_hit: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "items": self.items,
            "total_count": self.total_count,
            "pages_fetched": self.pages_fetched,
            "source_name": self.source_name,
            "success": self.success,
            "error_message": self.error_message,
            "cache_hit": self.cache_hit,
        }


class ListFetcherTool:
    """
    列表页爬取工具

    封装 ListFetcherAgent，提供统一的 Tool 接口
    支持多级缓存
    """

    def __init__(self, cache: Optional[MultiLevelCache] = None):
        self.agent = ListFetcherAgent()
        self.logger = logging.getLogger(__name__)
        self._cache = cache

    @property
    def cache(self) -> MultiLevelCache:
        """获取缓存实例"""
        if self._cache is not None:
            return self._cache
        return _get_cache()

    async def fetch(
        self,
        strategy: ExtractionStrategy,
        max_pages: Optional[int] = None,
        use_cache: bool = True,
    ) -> ListFetchResult:
        """
        爬取列表页

        Args:
            strategy: 提取策略
            max_pages: 最大页数（覆盖策略中的设置）
            use_cache: 是否使用缓存

        Returns:
            ListFetchResult: 爬取结果
        """
        try:
            # 应用最大页数限制
            if max_pages is not None:
                strategy.max_pages = max_pages

            # 生成缓存键
            cache_key = CacheKeyGenerator.for_tender_list(
                source=strategy.source_name,
                page=max_pages or 1
            )

            # 尝试从缓存获取
            if use_cache:
                cached_items = await self.cache.get(cache_key)
                if cached_items is not None:
                    self.logger.info(f"Cache hit for {cache_key}")
                    return ListFetchResult(
                        items=cached_items,
                        total_count=len(cached_items),
                        pages_fetched=self._estimate_pages_fetched(cached_items, strategy),
                        source_name=strategy.source_name,
                        success=True,
                        cache_hit=True,
                    )

            self.logger.info(
                f"Starting list fetch for source: {strategy.source_name}, "
                f"max_pages: {strategy.max_pages}"
            )

            # 执行爬取
            items = await self.agent.fetch(strategy)

            self.logger.info(
                f"List fetch completed: {len(items)} items from {strategy.source_name}"
            )

            # 存入缓存
            if use_cache:
                await self.cache.set(cache_key, items, ttl=60)

            return ListFetchResult(
                items=items,
                total_count=len(items),
                pages_fetched=self._estimate_pages_fetched(items, strategy),
                source_name=strategy.source_name,
                success=True,
                cache_hit=False,
            )

        except Exception as e:
            self.logger.error(f"List fetch failed: {e}")
            return ListFetchResult(
                items=[],
                total_count=0,
                pages_fetched=0,
                source_name=strategy.source_name,
                success=False,
                error_message=str(e),
            )

    def _estimate_pages_fetched(
        self, items: List[Dict], strategy: ExtractionStrategy
    ) -> int:
        """估算获取的页数"""
        if not items:
            return 0

        # 根据 items_per_page 估算
        items_per_page = strategy.pagination.get("items_per_page", 10)
        return (len(items) + items_per_page - 1) // items_per_page


@tool("fetch_tender_list", parse_docstring=True)
async def fetch_tender_list(
    source_url: str,
    site_type: str = "api",
    max_pages: int = 5,
    api_config: Optional[str] = None,
) -> str:
    """Fetch tender notice list from a source URL.

    This tool fetches tender/bidding announcement list pages from various sources.
    Supports API-type and HTML-type websites.

    Args:
        source_url: The source URL to fetch from (e.g., http://api.example.com/tender/list)
        site_type: Type of website - 'api' or 'static' or 'dynamic'. Default is 'api'.
        max_pages: Maximum number of pages to fetch. Default is 5.
        api_config: JSON string containing API configuration (for API sites).
            Includes url, method, params, headers, response_path, field_mapping.

    Returns:
        JSON string containing items, total_count, pages_fetched, success, error_message.
    """
    try:
        # Parse api_config JSON
        config = json.loads(api_config) if api_config else {}

        # Build ExtractionStrategy from parameters
        strategy = ExtractionStrategy(
            source_name=source_url,
            site_type=site_type,
            api_config=config,
            max_pages=max_pages,
            list_strategy=config.get("field_mapping", {}),
            pagination={"items_per_page": config.get("items_per_page", 10)},
        )

        # Execute fetch
        tool_instance = ListFetcherTool()
        result = await tool_instance.fetch(strategy, max_pages=max_pages)

        # Return JSON result
        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in api_config: {e}")
        return json.dumps({
            "items": [],
            "total_count": 0,
            "pages_fetched": 0,
            "success": False,
            "error_message": f"Invalid JSON in api_config: {str(e)}",
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Failed to fetch tender list: {e}")
        return json.dumps({
            "items": [],
            "total_count": 0,
            "pages_fetched": 0,
            "success": False,
            "error_message": str(e),
        }, indent=2, ensure_ascii=False)
