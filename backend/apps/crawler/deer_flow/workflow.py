"""
Tender Extraction Workflow for deer-flow

招标信息提取 Workflow 编排
将 ListFetcherTool 和 DetailFetcherTool 组合为完整提取流程

性能优化特性:
- 动态并发限制 (根据系统负载调整)
- 连接池管理
- 多级缓存支持
- 性能指标收集
"""
import json
import asyncio
import logging
import time
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

from apps.crawler.tools.list_fetcher_tool import ListFetcherTool, ListFetchResult
from apps.crawler.tools.detail_fetcher_tool import DetailFetcherTool, DetailFetchResult
from apps.crawler.deer_flow.cache import TenderCache, CacheLevel, get_cache
from apps.crawler.deer_flow.pool import ConnectionPool, get_connection_pool
from apps.crawler.deer_flow.metrics import PerformanceMetrics, get_metrics

logger = logging.getLogger(__name__)


@dataclass
class WorkflowConfig:
    """Workflow 配置"""
    max_concurrent_requests: int = 5
    max_retries: int = 3
    request_delay: float = 1.0
    max_items_per_source: int = 100
    # 性能优化配置
    enable_cache: bool = True
    enable_connection_pool: bool = True
    cache_ttl_l1: int = 300  # 5 minutes
    cache_ttl_l2: int = 3600  # 1 hour


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

    性能优化:
    - 动态并发限制
    - 多级缓存 (L1/L2/L3)
    - 连接池管理
    - 性能指标收集
    """

    def __init__(self, config: Optional[WorkflowConfig] = None):
        self.config = config or WorkflowConfig()
        self.logger = logging.getLogger(__name__)

        # 基础指标
        self._metrics = {
            "list_calls": 0,
            "detail_calls": 0,
            "errors": 0,
            "items_fetched": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # 动态并发控制
        self._active_tasks = 0
        self._semaphore: Optional[asyncio.Semaphore] = None

        # 缓存 (L1/L2/L3)
        self._cache: Optional[TenderCache] = None
        if self.config.enable_cache:
            try:
                self._cache = get_cache()
            except Exception as e:
                self.logger.warning(f"Cache initialization failed: {e}")

        # 连接池
        self._pool: Optional[ConnectionPool] = None
        if self.config.enable_connection_pool:
            try:
                self._pool = get_connection_pool()
            except Exception as e:
                self.logger.warning(f"Connection pool initialization failed: {e}")

        # 性能指标收集器
        self._perf_metrics = get_metrics()

        # 动态并发调整
        self._base_concurrent_limit = self.config.max_concurrent_requests
        self._dynamic_concurrent_limit = self._base_concurrent_limit

    def _get_semaphore(self) -> asyncio.Semaphore:
        """获取或创建信号量（动态并发控制）"""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._dynamic_concurrent_limit)
        return self._semaphore

    async def _adjust_concurrency(self, system_load: float = 0.0) -> int:
        """
        根据系统负载动态调整并发限制

        Args:
            system_load: 系统负载 (0.0 - 1.0)

        Returns:
            新的并发限制
        """
        # 系统负载高时降低并发，负载低时提高并发
        if system_load > 0.8:
            self._dynamic_concurrent_limit = max(2, self._base_concurrent_limit // 2)
        elif system_load > 0.5:
            self._dynamic_concurrent_limit = int(self._base_concurrent_requests * 0.8)
        else:
            self._dynamic_concurrent_limit = self._base_concurrent_requests

        # 重建信号量
        if self._semaphore is not None:
            # 取消旧的信号量引用，强制创建新的
            self._semaphore = None

        self._perf_metrics.set_gauge("concurrent_limit", self._dynamic_concurrent_limit)
        self.logger.debug(f"Adjusted concurrency limit: {self._dynamic_concurrent_limit}")

        return self._dynamic_concurrent_limit

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
        start_time = time.time()

        try:
            self.logger.info(f"Starting extraction from {source_url}")

            # 尝试从缓存获取 (使用源 URL 作为缓存键)
            cache_key = f"{source_url}:{max_pages}:{max_items}"
            if self._cache:
                cached = self._cache.get(source_url, cache_key)
                if cached:
                    self._metrics["cache_hits"] += 1
                    self.logger.info(f"Cache hit for {source_url}")
                    return ExtractionResult(**cached)

            self._metrics["cache_misses"] += 1

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

            # 写入缓存
            if self._cache:
                result_data = {
                    "items": items,
                    "success": True,
                    "total_fetched": len(items)
                }
                try:
                    self._cache.set(source_url, cache_key, result_data, level=CacheLevel.L1)
                except Exception as e:
                    self.logger.warning(f"Cache write failed: {e}")

            # 记录性能指标
            duration = time.time() - start_time
            self._perf_metrics.record_timing("extract", duration, {"source": source_url})

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
        # 计算缓存命中率
        cache_total = self._metrics.get("cache_hits", 0) + self._metrics.get("cache_misses", 0)
        cache_hit_rate = self._metrics.get("cache_hits", 0) / cache_total if cache_total > 0 else 0.0

        # 获取性能指标
        perf_stats = {}
        try:
            perf_stats = self._perf_metrics.get_all_stats()
        except Exception:
            pass

        return {
            **self._metrics,
            "cache_hit_rate": round(cache_hit_rate, 2),
            "config": {
                "max_concurrent_requests": self.config.max_concurrent_requests,
                "max_retries": self.config.max_retries,
                "request_delay": self.config.request_delay,
                "enable_cache": self.config.enable_cache,
                "enable_connection_pool": self.config.enable_connection_pool,
            },
            "dynamic": {
                "concurrent_limit": self._dynamic_concurrent_limit,
                "active_tasks": self._active_tasks,
            },
            "performance": perf_stats,
        }

    def reset_metrics(self):
        """重置指标"""
        self._metrics = {
            "list_calls": 0,
            "detail_calls": 0,
            "errors": 0,
            "items_fetched": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        self._active_tasks = 0
