"""
Crawler Celery tasks
"""

import logging
import requests
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.utils import timezone
from datetime import datetime

logger = logging.getLogger(__name__)


# 定义可重试的异常类型
RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    requests.ConnectionError,
    requests.Timeout,
    requests.RequestException,
)


@shared_task(
    bind=True,
    autoretry_for=RETRYABLE_EXCEPTIONS,
    retry_backoff=True,
    retry_backoff_max=60,
    max_retries=3,
)
def run_crawl_task(self, task_id: int):
    """
    执行爬虫任务

    Args:
        task_id: CrawlTask ID

    Returns:
        dict: Task execution result
    """
    from apps.crawler.models import CrawlTask

    try:
        # 获取任务
        task = CrawlTask.objects.get(id=task_id)
        logger.info(f"Starting crawl task: {task.name} (ID: {task.id})")

        # 更新状态为running
        task.status = 'running'
        task.started_at = timezone.now()
        task.save()

        # 导入爬虫并执行
        # 这里使用动态导入，实际使用时根据source_site选择对应的爬虫
        spider = _get_spider_for_task(task)

        if spider:
            items = spider.crawl()
            items_count = len(items) if items else 0

            # 更新任务状态为completed
            task.status = 'completed'
            task.completed_at = timezone.now()
            task.items_crawled = items_count
            task.save()

            logger.info(f"Crawl task completed: {task.name}, items: {items_count}")
            return {
                'status': 'completed',
                'task_id': task.id,
                'items_crawled': items_count
            }
        else:
            raise ValueError(f"No spider found for source site: {task.source_site}")

    except Exception as exc:
        logger.error(f"Crawl task failed: {task_id}, error: {str(exc)}")

        # 获取任务记录
        try:
            task = CrawlTask.objects.get(id=task_id)
            task.status = 'failed'
            task.error_message = str(exc)
            task.completed_at = timezone.now()
            task.save()
        except CrawlTask.DoesNotExist:
            logger.error(f"Task not found: {task_id}")

        # 重试逻辑
        try:
            # 使用指数退避策略，基础时间为60秒
            countdown = 60 * (2 ** self.request.retries)
            raise self.retry(exc=exc, countdown=countdown)
        except MaxRetriesExceededError:
            logger.error(f"Task {task_id} failed after max retries")
            return {
                'status': 'failed',
                'task_id': task_id,
                'error': str(exc)
            }


def _get_spider_for_task(task):
    """
    根据任务获取对应的爬虫实例

    Args:
        task: CrawlTask instance

    Returns:
        Spider instance or None
    """
    from apps.crawler.models import CrawlSource
    from apps.crawler.spiders.dynamic import DynamicSpider

    # 1. 优先使用任务的 source 外键（推荐方式）
    if task.source:
        logger.info(f"Using DynamicSpider for source: {task.source.name} (ID: {task.source.id})")
        return DynamicSpider(crawl_source=task.source)

    # 2. 尝试通过 source_site 名称查找 CrawlSource（兼容旧数据）
    try:
        crawl_source = CrawlSource.objects.filter(
            name=task.source_site,
            status=CrawlSource.STATUS_ACTIVE
        ).first()

        if crawl_source:
            logger.info(f"Using DynamicSpider for source (by name): {task.source_site}")
            return DynamicSpider(crawl_source=crawl_source)
    except Exception as e:
        logger.warning(f"Failed to get CrawlSource by name: {e}")

    # 3. 回退到预定义的爬虫映射（兼容旧逻辑）
    spider_map = {
        '政府采购网': 'apps.crawler.spiders.gov_spider.GovSpider',
        '中国政府采购网': 'apps.crawler.spiders.gov_spider.GovSpider',
    }

    spider_path = spider_map.get(task.source_site)
    if spider_path:
        try:
            module_path, class_name = spider_path.rsplit('.', 1)
            module = __import__(module_path, fromlist=[class_name])
            spider_class = getattr(module, class_name)
            return spider_class()
        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to import spider: {e}")

    # 4. 最后返回模拟爬虫
    logger.warning(f"No spider found for source_site: {task.source_site}, using MockSpider")
    return MockSpider(task.source_url)


class MockSpider:
    """Mock spider for testing"""

    def __init__(self, source_url):
        self.source_url = source_url

    def crawl(self):
        """Return empty list for mock"""
        return []


@shared_task
def scheduled_daily_crawl():
    """
    每日定时爬取任务

    从数据库读取启用的爬虫源配置，批量创建爬虫任务
    """
    from apps.crawler.models import CrawlTask, CrawlSource

    # 从数据库读取启用的爬虫源配置
    active_sources = CrawlSource.objects.filter(status=CrawlSource.STATUS_ACTIVE)

    if not active_sources.exists():
        logger.warning("No active crawl sources found")
        # 如果没有配置，使用默认源
        default_sources = [
            {
                'name': '政府采购网-每日更新',
                'source_url': 'http://www.ccgp.gov.cn/',
                'source_site': '政府采购网',
            },
        ]
    else:
        # 使用配置的爬虫源
        default_sources = [
            {
                'name': source.name,
                'source_url': source.base_url,
                'source_site': source.name,
            }
            for source in active_sources
        ]

    created_tasks = []
    for source in default_sources:
        task = CrawlTask.objects.create(
            name=source['name'],
            source_url=source['source_url'],
            source_site=source['source_site'],
            status='pending'
        )
        # 触发异步执行
        run_crawl_task.delay(task.id)
        created_tasks.append(task.id)
        logger.info(f"Created and scheduled crawl task: {task.name}")

    return {
        'status': 'scheduled',
        'tasks_created': len(created_tasks),
        'task_ids': created_tasks
    }


# =============================================================================
# Deer-Flow 数据提取任务
# =============================================================================

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def run_deer_flow_extraction(self, task_id: str):
    """
    执行 deer-flow 数据提取任务

    Args:
        task_id: ExtractionTask ID

    Returns:
        dict: 任务执行结果
    """
    from apps.crawler.services.deer_flow_extraction import get_extraction_service

    try:
        logger.info(f"Starting deer-flow extraction task: {task_id}")

        service = get_extraction_service()
        task = service.get_task(task_id)

        if not task:
            logger.error(f"Task {task_id} not found")
            return {
                "status": "failed",
                "task_id": task_id,
                "error": "Task not found"
            }

        # 执行提取任务
        result = service.run_task(task_id)

        logger.info(f"Extraction task {task_id} completed: success={result.get('success')}")

        return {
            "status": task.status,
            "task_id": task_id,
            "success": result.get("success", False),
            "total_fetched": result.get("total_fetched", 0),
            "error": result.get("error_message"),
        }

    except Exception as exc:
        logger.error(f"Extraction task {task_id} failed: {exc}")
        return {
            "status": "failed",
            "task_id": task_id,
            "error": str(exc)
        }


@shared_task
def run_batch_extraction(sources: list):
    """
    批量执行提取任务

    Args:
        sources: 源配置列表，每项包含 url 和 type

    Returns:
        dict: 批量执行结果
    """
    from apps.crawler.services.deer_flow_extraction import get_extraction_service
    from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
    import asyncio

    results = []
    workflow = TenderExtractionWorkflow()

    async def process_source(source: dict):
        url = source.get("url")
        site_type = source.get("type", "api")
        max_items = source.get("max_items", 10)

        try:
            result = await workflow.extract(
                source_url=url,
                site_type=site_type,
                max_items=max_items
            )
            return {"url": url, "success": True, "result": result.to_dict()}
        except Exception as e:
            logger.error(f"Failed to extract from {url}: {e}")
            return {"url": url, "success": False, "error": str(e)}

    async def run_batch():
        tasks = [process_source(s) for s in sources]
        return await asyncio.gather(*tasks, return_exceptions=True)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(run_batch())
        loop.close()
    except Exception as e:
        logger.error(f"Batch extraction failed: {e}")
        return {"status": "failed", "error": str(e)}

    return {
        "status": "completed",
        "total": len(sources),
        "successful": sum(1 for r in results if isinstance(r, dict) and r.get("success")),
        "results": results
    }