"""
Crawler scheduler configuration
爬虫调度器配置

配置 Celery Beat 定时任务：
- 每日凌晨 02:00 自动执行
"""

from celery import current_app
from celery.schedules import crontab

# 导入 task 用于 scheduler 中直接访问
from apps.crawler.tasks import run_crawl_task


# 默认爬取源配置
DEFAULT_SOURCES = [
    {
        'name': '政府采购网-每日更新',
        'source_url': 'http://www.ccgp.gov.cn/zcdt/',
        'source_site': '政府采购网',
        'enabled': True,
    },
    {
        'name': '中国政府采购网-中央',
        'source_url': 'http://www.ccgp.gov.cn/zcdt/zcdt_zycg/',
        'source_site': '政府采购网',
        'enabled': True,
    },
    {
        'name': '政府采购网-地方',
        'source_url': 'http://www.ccgp.gov.cn/zcdt/zcdt_dfgg/',
        'source_site': '政府采购网',
        'enabled': True,
    },
]


def get_beat_schedule():
    """
    获取 Celery Beat 定时任务配置

    Returns:
        dict: Celery beat schedule configuration
    """
    return {
        'daily-crawl': {
            'task': 'apps.crawler.tasks.scheduled_daily_crawl',
            'schedule': crontab(hour=2, minute=0),
            'options': {
                'expires': 3600,  # 1小时后过期
                'priority': 0,    # 高优先级
            },
            'kwargs': {},
        },
        # 可以添加更多定时任务
        # 'hourly-health-check': {
        #     'task': 'apps.crawler.tasks.health_check',
        #     'schedule': crontab(minute=0),  # 每小时执行
        # },
    }


def get_enabled_sources():
    """
    获取启用的爬取源列表

    Returns:
        list: 启用的爬取源配置
    """
    return [s for s in DEFAULT_SOURCES if s.get('enabled', True)]


def run_scheduled_crawl(sources=None):
    """
    执行定时爬取任务

    Args:
        sources: 指定爬取源，None 使用所有启用的源

    Returns:
        dict: 执行结果
    """
    from apps.crawler.tasks import run_crawl_task
    from apps.crawler.models import CrawlTask

    sources_to_crawl = sources or get_enabled_sources()

    created_tasks = []

    for source in sources_to_crawl:
        try:
            # 创建爬虫任务
            task = CrawlTask.objects.create(
                name=source['name'],
                source_url=source['source_url'],
                source_site=source['source_site'],
                status='pending'
            )

            # 使用 apply_async 异步执行，支持更多选项
            run_crawl_task.apply_async(
                args=[task.id],
                countdown=10,  # 10秒后执行
                max_retries=3,
            )

            created_tasks.append({
                'id': task.id,
                'name': task.name,
                'status': 'scheduled'
            })

        except Exception as e:
            # 记录错误但继续执行其他任务
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to schedule crawl for {source['name']}: {e}")

    return {
        'status': 'scheduled',
        'tasks_created': len(created_tasks),
        'tasks': created_tasks,
    }


def add_source(name: str, source_url: str, source_site: str, enabled: bool = True):
    """
    添加新的爬取源

    Args:
        name: 来源名称
        source_url: 爬取URL
        source_site: 来源网站
        enabled: 是否启用

    Returns:
        bool: 是否添加成功
    """
    # 检查是否已存在
    for source in DEFAULT_SOURCES:
        if source['source_url'] == source_url:
            return False

    DEFAULT_SOURCES.append({
        'name': name,
        'source_url': source_url,
        'source_site': source_site,
        'enabled': enabled,
    })

    return True


def disable_source(source_url: str):
    """
    禁用指定爬取源

    Args:
        source_url: 来源URL

    Returns:
        bool: 是否成功禁用
    """
    for source in DEFAULT_SOURCES:
        if source['source_url'] == source_url:
            source['enabled'] = False
            return True
    return False


def enable_source(source_url: str):
    """
    启用指定爬取源

    Args:
        source_url: 来源URL

    Returns:
        bool: 是否成功启用
    """
    for source in DEFAULT_SOURCES:
        if source['source_url'] == source_url:
            source['enabled'] = True
            return True
    return False


# Celery beat schedule 配置
# 在 config/celery.py 中使用
beat_schedule = get_beat_schedule()
