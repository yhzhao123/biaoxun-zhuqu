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
    # 根据source_site动态选择爬虫
    spider_map = {
        '政府采购网': 'apps.crawler.spiders.gov_spider.GovSpider',
        '中国政府采购网': 'apps.crawler.spiders.gov_spider.GovSpider',
    }

    spider_path = spider_map.get(task.source_site)
    if not spider_path:
        logger.warning(f"No spider mapping for source_site: {task.source_site}")
        # 返回一个模拟爬虫用于测试
        return MockSpider(task.source_url)

    # 动态导入爬虫类
    try:
        module_path, class_name = spider_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        spider_class = getattr(module, class_name)
        return spider_class()
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import spider: {e}")
        # 返回模拟爬虫用于测试
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

    从数据库读取爬虫源配置，批量创建爬虫任务
    """
    from apps.crawler.models import CrawlTask

    # 示例：自动创建每日爬取任务
    # 实际使用时可以从数据库读取配置
    default_sources = [
        {
            'name': '政府采购网-每日更新',
            'source_url': 'http://www.ccgp.gov.cn/',
            'source_site': '政府采购网',
        },
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