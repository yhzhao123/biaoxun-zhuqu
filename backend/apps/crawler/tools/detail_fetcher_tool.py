"""
DetailFetcherTool - 详情页爬取工具

将 DetailFetcherAgent 封装为 Deer-Flow Tool
支持多级缓存
"""
import json
import hashlib
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

from langchain.tools import tool

from apps.crawler.agents.agents.fetcher_agents import DetailFetcherAgent
from apps.crawler.tools.error_handling import (
    RetryConfig,
    CircuitBreaker,
    with_retry,
    with_circuit_breaker,
    FallbackStrategy,
    RetryableError,
)
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
class DetailFetchResult:
    """详情页爬取结果"""
    url: str
    html: str
    success: bool
    attachments: list = field(default_factory=list)
    main_pdf_content: Optional[str] = None
    main_pdf_url: Optional[str] = None
    main_pdf_filename: Optional[str] = None
    list_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    content_type: str = "html"  # html, pdf

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "url": self.url,
            "html": self.html[:1000] if self.html else "",  # 截断HTML
            "success": self.success,
            "attachments_count": len(self.attachments),
            "has_pdf_content": self.main_pdf_content is not None,
            "main_pdf_url": self.main_pdf_url,
            "main_pdf_filename": self.main_pdf_filename,
            "content_type": self.content_type,
            "error_message": self.error_message,
        }

    def get_full_text(self) -> str:
        """
        获取完整文本内容

        优先返回 PDF 内容（如果存在），否则返回 HTML
        """
        if self.main_pdf_content:
            return self.main_pdf_content
        return self.html

    def has_attachments(self) -> bool:
        """检查是否有附件"""
        return len(self.attachments) > 0

    def get_pdf_attachments(self) -> list:
        """获取 PDF 类型的附件"""
        return [a for a in self.attachments if a.type == 'pdf']


class DetailFetcherTool:
    """
    详情页爬取工具

    封装 DetailFetcherAgent，提供统一的 Tool 接口
    支持 HTML 页面和 PDF 页面的爬取
    支持多级缓存
    """

    def __init__(self, cache: Optional[MultiLevelCache] = None):
        self.agent = DetailFetcherAgent()
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
        list_item: Dict[str, Any],
        extract_pdf: bool = True,
        use_cache: bool = True,
    ) -> DetailFetchResult:
        """
        爬取详情页

        Args:
            list_item: 列表项数据，必须包含 'url' 字段
            extract_pdf: 是否提取 PDF 内容
            use_cache: 是否使用缓存

        Returns:
            DetailFetchResult: 详情页爬取结果
        """
        url = list_item.get('url')
        if not url:
            self.logger.error("No URL provided in list_item")
            return DetailFetchResult(
                url="",
                html="",
                success=False,
                error_message="No URL provided",
            )

        # 生成缓存键
        tender_id = list_item.get('id', hashlib.md5(url.encode()).hexdigest()[:8])
        cache_key = CacheKeyGenerator.for_tender_detail(tender_id)

        # 尝试从缓存获取
        if use_cache:
            cached_result = await self.cache.get(cache_key)
            if cached_result is not None:
                self.logger.info(f"Cache hit for {cache_key}")
                # 从缓存恢复时，只提取 DetailFetchResult 需要的字段
                return DetailFetchResult(
                    url=cached_result.get("url", ""),
                    html=cached_result.get("html", ""),
                    success=cached_result.get("success", False),
                    attachments=cached_result.get("attachments", []),
                    main_pdf_content=cached_result.get("main_pdf_content"),
                    main_pdf_url=cached_result.get("main_pdf_url"),
                    main_pdf_filename=cached_result.get("main_pdf_filename"),
                    list_data=cached_result.get("list_data", {}),
                    content_type=cached_result.get("content_type", "html"),
                )

        try:
            self.logger.info(f"Fetching detail page: {url}")

            # 调用 Agent 爬取
            detail_result = await self.agent.fetch(list_item)

            if not detail_result:
                return DetailFetchResult(
                    url=url,
                    html="",
                    success=False,
                    error_message="Failed to fetch detail page",
                )

            # 构建结果
            result = DetailFetchResult(
                url=detail_result.url,
                html=detail_result.html,
                success=True,
                attachments=detail_result.attachments,
                main_pdf_content=detail_result.main_pdf_content if extract_pdf else None,
                main_pdf_url=detail_result.main_pdf_url,
                main_pdf_filename=detail_result.main_pdf_filename,
                list_data=detail_result.list_data,
                content_type="pdf" if detail_result.main_pdf_content else "html",
            )

            self.logger.info(
                f"Detail fetch completed: {url}, "
                f"attachments: {len(result.attachments)}, "
                f"has_pdf: {result.main_pdf_content is not None}"
            )

            # 存入缓存
            if use_cache:
                await self.cache.set(cache_key, result.to_dict(), ttl=300)

            return result

        except Exception as e:
            self.logger.error(f"Detail fetch failed: {e}")
            return DetailFetchResult(
                url=url,
                html="",
                success=False,
                error_message=str(e),
            )

    async def fetch_with_retry(
        self,
        list_item: Dict[str, Any],
        max_retries: int = 3,
        extract_pdf: bool = True,
        use_cache: bool = True,
    ) -> DetailFetchResult:
        """
        带重试的详情页爬取

        Args:
            list_item: 列表项数据
            max_retries: 最大重试次数
            extract_pdf: 是否提取 PDF 内容
            use_cache: 是否使用缓存

        Returns:
            DetailFetchResult: 详情页爬取结果
        """
        import asyncio

        last_error = None

        for attempt in range(max_retries):
            try:
                result = await self.fetch(list_item, extract_pdf, use_cache=use_cache)
                if result.success:
                    return result
                last_error = result.error_message
            except Exception as e:
                last_error = str(e)
                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")

            if attempt < max_retries - 1:
                delay = 2 ** attempt  # 指数退避
                self.logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)

        return DetailFetchResult(
            url=list_item.get('url', ''),
            html="",
            success=False,
            error_message=f"Failed after {max_retries} attempts: {last_error}",
        )

    def validate_list_item(self, list_item: Dict[str, Any]) -> bool:
        """
        验证列表项数据是否有效

        Args:
            list_item: 列表项数据

        Returns:
            bool: 是否有效
        """
        if not isinstance(list_item, dict):
            self.logger.error("list_item must be a dictionary")
            return False

        if 'url' not in list_item:
            self.logger.error("list_item must contain 'url' field")
            return False

        url = list_item.get('url')
        if not url or not isinstance(url, str):
            self.logger.error("'url' must be a non-empty string")
            return False

        # 简单验证 URL 格式
        if not url.startswith(('http://', 'https://')):
            self.logger.error(f"Invalid URL format: {url}")
            return False

        return True

    async def fetch_batch(
        self,
        list_items: list[Dict[str, Any]],
        max_concurrent: int = 5,
        extract_pdf: bool = True,
        use_cache: bool = False,
    ) -> list[DetailFetchResult]:
        """
        批量爬取详情页

        Args:
            list_items: 列表项数据列表
            max_concurrent: 最大并发数
            extract_pdf: 是否提取 PDF 内容
            use_cache: 是否使用缓存

        Returns:
            DetailFetchResult 列表
        """
        import asyncio
        from asyncio import Semaphore

        semaphore = Semaphore(max_concurrent)

        async def fetch_with_limit(item: Dict[str, Any]) -> DetailFetchResult:
            async with semaphore:
                return await self.fetch(item, extract_pdf, use_cache)

        tasks = [fetch_with_limit(item) for item in list_items]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"Batch fetch error for item {i}: {result}")
                processed_results.append(
                    DetailFetchResult(
                        url=list_items[i].get('url', ''),
                        html="",
                        success=False,
                        error_message=str(result),
                    )
                )
            else:
                processed_results.append(result)

        return processed_results


# 便捷的函数接口（用于 LangChain Tool 装饰器）
async def detail_fetch_tool(
    url: str,
    title: str = "",
    extract_pdf: bool = True,
) -> Dict[str, Any]:
    """
    详情页爬取工具函数

    Args:
        url: 详情页 URL
        title: 标题（可选）
        extract_pdf: 是否提取 PDF 内容

    Returns:
        爬取结果字典
    """
    list_item = {
        "url": url,
        "title": title,
    }

    tool = DetailFetcherTool()
    result = await tool.fetch(list_item, extract_pdf=extract_pdf)

    return result.to_dict()


@tool("fetch_tender_detail", parse_docstring=True)
async def fetch_tender_detail(
    url: str,
    title: str = "",
    extract_pdf: bool = True,
) -> str:
    """Fetch tender detail page content.

    This tool fetches the content of a tender notice detail page.
    Supports both HTML pages and PDF documents.

    Args:
        url: The URL of the detail page to fetch. Must start with http:// or https://
        title: The title of the tender notice (optional, for context)
        extract_pdf: Whether to extract PDF content if available. Default is True.

    Returns:
        JSON string containing:
        - url: The fetched URL
        - html: HTML content (if HTML page)
        - success: Whether the fetch succeeded
        - attachments_count: Number of attachments found
        - has_pdf_content: Whether PDF content was extracted
        - main_pdf_url: URL of the main PDF if extracted
        - main_pdf_filename: Filename of the main PDF
        - content_type: 'html' or 'pdf'
        - error_message: Error message if failed
    """
    try:
        list_item = {
            "url": url,
            "title": title,
        }

        tool = DetailFetcherTool()
        result = await tool.fetch(list_item, extract_pdf=extract_pdf)

        return json.dumps(result.to_dict(), indent=2, ensure_ascii=False)

    except Exception as e:
        logger.error(f"Failed to fetch tender detail: {e}")
        return json.dumps({
            "url": url,
            "html": "",
            "success": False,
            "attachments_count": 0,
            "has_pdf_content": False,
            "error_message": str(e),
        }, indent=2, ensure_ascii=False)
