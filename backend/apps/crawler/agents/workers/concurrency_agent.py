"""
并发控制智能体

负责实现智能体框架的并发控制机制
"""
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from asyncio import Semaphore, Task

logger = logging.getLogger(__name__)


@dataclass
class ConcurrencyConfig:
    """并发配置"""
    max_concurrent_requests: int = 5  # 最大并发HTTP请求
    max_concurrent_llm_calls: int = 3  # 最大并发LLM调用
    max_concurrent_details: int = 10  # 最大并发详情页爬取
    request_delay: float = 1.0  # 请求间隔（秒）
    llm_delay: float = 0.5  # LLM调用间隔（秒）


class ConcurrencyControlAgent:
    """
    并发控制智能体

    管理所有智能体的并发执行，防止：
    1. 对目标网站的过度请求
    2. LLM API的限流
    3. 资源耗尽
    """

    def __init__(self, config: ConcurrencyConfig = None):
        self.config = config or ConcurrencyConfig()

        # 信号量控制
        self.request_semaphore = Semaphore(self.config.max_concurrent_requests)
        self.llm_semaphore = Semaphore(self.config.max_concurrent_llm_calls)
        self.detail_semaphore = Semaphore(self.config.max_concurrent_details)

        # 速率限制器
        self.last_request_time = 0
        self.last_llm_time = 0
        self._lock = asyncio.Lock()

    async def execute_with_request_limit(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        在请求限制下执行函数
        """
        async with self.request_semaphore:
            # 速率限制
            async with self._lock:
                now = asyncio.get_event_loop().time()
                elapsed = now - self.last_request_time
                if elapsed < self.config.request_delay:
                    await asyncio.sleep(self.config.request_delay - elapsed)
                self.last_request_time = asyncio.get_event_loop().time()

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise

    async def execute_with_llm_limit(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        在LLM调用限制下执行函数
        """
        async with self.llm_semaphore:
            # 速率限制
            async with self._lock:
                now = asyncio.get_event_loop().time()
                elapsed = now - self.last_llm_time
                if elapsed < self.config.llm_delay:
                    await asyncio.sleep(self.config.llm_delay - elapsed)
                self.last_llm_time = asyncio.get_event_loop().time()

            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                raise

    async def execute_batch_with_limit(
        self,
        items: List[Any],
        process_func: Callable,
        max_concurrent: int = None,
        batch_size: int = None
    ) -> List[Any]:
        """
        批量处理，带并发限制

        Args:
            items: 待处理项目列表
            process_func: 处理函数
            max_concurrent: 最大并发数
            batch_size: 批次大小

        Returns:
            处理结果列表
        """
        if not items:
            return []

        max_concurrent = max_concurrent or self.config.max_concurrent_details
        batch_size = batch_size or max_concurrent * 2

        results = []

        # 分批处理
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}: {len(batch)} items")

            # 创建任务
            semaphore = Semaphore(max_concurrent)

            async def process_with_limit(item):
                async with semaphore:
                    try:
                        return await process_func(item)
                    except Exception as e:
                        logger.error(f"Failed to process item: {e}")
                        return None

            # 并发执行批次
            tasks = [process_with_limit(item) for item in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            # 过滤异常和None
            for result in batch_results:
                if result is not None and not isinstance(result, Exception):
                    results.append(result)

            logger.info(f"Batch completed: {len([r for r in batch_results if r is not None and not isinstance(r, Exception)])} succeeded")

        return results

    async def execute_with_backoff(
        self,
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        *args,
        **kwargs
    ) -> Any:
        """
        带指数退避的执行

        Args:
            func: 待执行函数
            max_retries: 最大重试次数
            base_delay: 基础延迟（秒）
        """
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"All retries failed: {e}")
                    raise

                # 指数退避
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}, retrying in {delay}s...")
                await asyncio.sleep(delay)


# 全局并发控制器实例
_concurrency_controller: Optional[ConcurrencyControlAgent] = None


def get_concurrency_controller() -> ConcurrencyControlAgent:
    """获取全局并发控制器"""
    global _concurrency_controller
    if _concurrency_controller is None:
        _concurrency_controller = ConcurrencyControlAgent()
    return _concurrency_controller
