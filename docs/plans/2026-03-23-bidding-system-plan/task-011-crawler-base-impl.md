# Task 011: 爬虫基础架构实现

## 任务信息

- **任务ID**: 011
- **任务名称**: 爬虫基础架构实现
- **任务类型**: impl
- **依赖任务**: 010 (爬虫基础架构测试)

## BDD Scenario

```gherkin
Scenario: 爬虫基础架构正常工作
  Given 爬虫系统已初始化
  And Celery任务队列已配置
  When 创建新的爬虫任务
  Then 应支持Scrapy集成
  And 应支持Celery分布式调度
  And 爬虫状态应可监控
```

## 实现目标

实现爬虫基础架构：BaseSpider类、Scrapy集成和Celery任务调度。

## 创建/修改的文件

- `apps/crawler/__init__.py`
- `apps/crawler/base.py` - BaseSpider基类
- `apps/crawler/scrapy_extensions.py` - Scrapy扩展
- `apps/crawler/tasks.py` - Celery任务
- `apps/crawler/models.py` - 爬虫状态模型
- `apps/crawler/config.py` - 爬虫配置
- `config/settings/celery.py` - Celery配置

## 实施步骤

### 1. 创建BaseSpider基类

```python
# apps/crawler/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SpiderConfig:
    """爬虫配置类"""
    def __init__(self, name: str, start_urls: List[str], **kwargs):
        self.name = name
        self.start_urls = start_urls
        self.max_pages = kwargs.get('max_pages', 100)
        self.delay = kwargs.get('delay', 1)
        self.timeout = kwargs.get('timeout', 30)
        self.retry_times = kwargs.get('retry_times', 3)
        self.validate()

    def validate(self):
        if not self.name:
            raise ValueError("Spider name is required")
        if not self.start_urls:
            raise ValueError("At least one start URL is required")


class BaseSpider(ABC):
    """爬虫基类 - 封装通用爬虫逻辑"""

    def __init__(self, config: SpiderConfig):
        self.config = config
        self.name = config.name
        self.pages_crawled = 0
        self.items_extracted = 0
        self.errors = []

    @abstractmethod
    def parse(self, response) -> List[Dict[str, Any]]:
        """解析响应，子类必须实现"""
        pass

    def crawl(self, urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """执行爬取"""
        urls = urls or self.config.start_urls
        results = []

        for url in urls:
            try:
                items = self._fetch_and_parse(url)
                results.extend(items)
            except Exception as e:
                logger.error(f"Failed to crawl {url}: {e}")
                self.errors.append({'url': url, 'error': str(e)})

        return {
            'spider_name': self.name,
            'pages_crawled': self.pages_crawled,
            'items_extracted': len(results),
            'errors': self.errors,
            'data': results
        }

    def _fetch_and_parse(self, url: str) -> List[Dict[str, Any]]:
        """获取并解析单个URL"""
        # 子类实现具体获取逻辑
        pass
```

### 2. 实现Scrapy集成

```python
# apps/crawler/scrapy_extensions.py
from scrapy import Spider, Request
from scrapy.exceptions import DontCloseSpider
from scrapy.signals import spider_idle
from .base import BaseSpider, SpiderConfig


class ScrapySpider(Spider):
    """Scrapy集成基类"""
    name = 'base_scrapy_spider'

    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 4,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = SpiderConfig(
            name=kwargs.get('name', self.name),
            start_urls=kwargs.get('start_urls', []),
            max_pages=kwargs.get('max_pages', 100)
        )
        self.base_spider = None

    def start_requests(self):
        for url in self.config.start_urls:
            yield Request(url, callback=self.parse, errback=self.handle_error)

    def parse(self, response):
        """解析响应 - 调用BaseSpider的parse方法"""
        if self.base_spider:
            return self.base_spider.parse(response)
        return []

    def handle_error(self, failure):
        """处理请求错误"""
        self.logger.error(f"Request failed: {failure}")
        return {'error': str(failure), 'url': failure.request.url}
```

### 3. 实现Celery任务

```python
# apps/crawler/tasks.py
from celery import shared_task
from celery.result import AsyncResult
from django.utils import timezone
from .models import CrawlJob, CrawlStatus
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_spider(self, spider_name: str, spider_config: dict):
    """
    运行爬虫任务

    Args:
        spider_name: 爬虫类名
        spider_config: 爬虫配置字典
    """
    logger.info(f"Starting spider: {spider_name}")

    try:
        # 获取爬虫类
        spider_class = get_spider_class(spider_name)

        # 创建爬虫实例
        spider = spider_class(**spider_config)

        # 执行爬取
        result = spider.crawl()

        # 保存结果
        save_crawl_result(self.request.id, result)

        return {
            'status': 'success',
            'task_id': self.request.id,
            'spider_name': spider_name,
            'result': result
        }

    except Exception as exc:
        logger.exception(f"Spider {spider_name} failed")
        raise self.retry(exc=exc, countdown=60)


@shared_task
def schedule_crawlers():
    """调度所有配置的爬虫"""
    from .config import SPIDER_SCHEDULES

    scheduled = []
    for spider_config in SPIDER_SCHEDULES:
        task = run_spider.delay(
            spider_config['name'],
            spider_config.get('config', {})
        )
        scheduled.append({
            'spider': spider_config['name'],
            'task_id': task.id
        })

    return {'scheduled': scheduled}


@shared_task
def check_crawler_health():
    """检查爬虫健康状态"""
    active_jobs = CrawlJob.objects.filter(
        status=CrawlStatus.RUNNING,
        started_at__lt=timezone.now() - timezone.timedelta(hours=4)
    )

    stalled = []
    for job in active_jobs:
        job.status = CrawlStatus.STALLED
        job.save()
        stalled.append(job.id)

    return {'stalled_jobs': stalled}


def get_spider_class(name: str):
    """动态获取爬虫类"""
    from .spiders import SPIDER_REGISTRY
    if name not in SPIDER_REGISTRY:
        raise ValueError(f"Unknown spider: {name}")
    return SPIDER_REGISTRY[name]


def save_crawl_result(task_id: str, result: dict):
    """保存爬取结果"""
    CrawlJob.objects.filter(task_id=task_id).update(
        status=CrawlStatus.COMPLETED if not result['errors'] else CrawlStatus.FAILED,
        pages_crawled=result['pages_crawled'],
        items_extracted=result['items_extracted'],
        errors=result['errors'],
        completed_at=timezone.now()
    )
```

### 4. 创建爬虫状态模型

```python
# apps/crawler/models.py
from django.db import models
from django.utils import timezone


class CrawlStatus(models.TextChoices):
    PENDING = 'pending', '待执行'
    RUNNING = 'running', '执行中'
    COMPLETED = 'completed', '已完成'
    FAILED = 'failed', '失败'
    STALLED = 'stalled', '已停滞'


class CrawlJob(models.Model):
    """爬虫任务记录"""
    task_id = models.CharField(max_length=255, unique=True)
    spider_name = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=CrawlStatus.choices,
        default=CrawlStatus.PENDING
    )
    start_urls = models.JSONField(default=list)
    config = models.JSONField(default=dict)
    pages_crawled = models.IntegerField(default=0)
    items_extracted = models.IntegerField(default=0)
    errors = models.JSONField(default=list)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['spider_name', '-created_at']),
        ]

    def __str__(self):
        return f"{self.spider_name} - {self.status}"
```

### 5. 配置Celery

```python
# config/settings/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('biaoxun')

# 配置
app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1小时超时
    worker_prefetch_multiplier=1,
)

# 定时任务
app.conf.beat_schedule = {
    'schedule-crawlers': {
        'task': 'apps.crawler.tasks.schedule_crawlers',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
    },
    'check-crawler-health': {
        'task': 'apps.crawler.tasks.check_crawler_health',
        'schedule': 300.0,  # 每5分钟
    },
}

app.autodiscover_tasks()
```

### 6. 创建爬虫配置

```python
# apps/crawler/config.py
"""爬虫配置"""

SPIDER_SCHEDULES = [
    {
        'name': 'gov_spider',
        'schedule': '0 2 * * *',  # 每天凌晨2点
        'config': {
            'start_urls': ['http://www.ccgp.gov.cn/'],
            'max_pages': 100
        }
    },
]

# Scrapy设置
SCRAPY_SETTINGS = {
    'DOWNLOAD_DELAY': 1,
    'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
    'CONCURRENT_REQUESTS': 4,
    'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
    'RETRY_TIMES': 3,
    'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
    'LOG_LEVEL': 'INFO',
}
```

### 7. 创建爬虫注册表

```python
# apps/crawler/spiders/__init__.py
"""爬虫注册表"""

SPIDER_REGISTRY = {}


def register_spider(cls):
    """装饰器：注册爬虫类"""
    SPIDER_REGISTRY[cls.name] = cls
    return cls


def get_spider(name: str):
    """获取爬虫类"""
    return SPIDER_REGISTRY.get(name)


def list_spiders():
    """列出所有注册的爬虫"""
    return list(SPIDER_REGISTRY.keys())
```

## 验证步骤

```bash
# 运行测试
pytest apps/crawler/tests/test_base_spider.py -v
pytest apps/crawler/tests/test_celery_tasks.py -v

# 检查Celery任务
python -c "from apps.crawler.tasks import run_spider; print('Tasks loaded')"

# 创建迁移
python manage.py makemigrations crawler
python manage.py migrate
```

**预期**: 所有测试通过(GREEN状态)

## 提交信息

```
feat: implement crawler base architecture

- Add BaseSpider abstract class with config validation
- Implement Scrapy integration with ScrapySpider base class
- Add Celery tasks for distributed crawling (run_spider, schedule_crawlers)
- Create CrawlJob model for status tracking
- Add Celery Beat scheduling configuration
- Implement spider registry for dynamic loading
- Add health check task for stalled jobs
- All tests passing (GREEN state)
```
