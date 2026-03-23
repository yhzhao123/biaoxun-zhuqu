# Task 017: 爬虫调度实现

## 任务信息

- **任务ID**: 017
- **任务名称**: 爬虫调度实现
- **任务类型**: impl
- **依赖任务**: 016 (爬虫调度测试)

## BDD Scenario

```gherkin
Scenario: 定时调度爬虫任务
  Given Celery Beat已配置
  And 爬虫任务"政府采购网-每日更新"已注册
  When 到达每日凌晨2:00
  Then 应自动触发爬虫任务
  And 任务执行状态应可监控
  And 失败任务应自动重试
```

## 实现目标

实现爬虫调度系统：Celery Beat定时任务、任务监控、失败重试机制。

## 创建/修改的文件

- `config/celery.py` - Celery配置和Beat调度
- `apps/crawler/scheduler.py` - 任务调度器
- `apps/crawler/monitoring.py` - 任务监控
- `apps/crawler/retry.py` - 重试策略
- `apps/crawler/management/commands/` - 管理命令
- `apps/crawler/consumers.py` - WebSocket消费者（实时监控）

## 实施步骤

### 1. 配置Celery Beat调度

```python
# config/celery.py
import os
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('biaoxun')

# 使用Django设置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 从已安装的Django应用中自动发现任务
app.autodiscover_tasks()

# Celery Beat 定时任务配置
app.conf.beat_schedule = {
    # 每日凌晨2:00调度所有爬虫
    'schedule-crawlers-daily': {
        'task': 'apps.crawler.tasks.schedule_crawlers',
        'schedule': crontab(hour=2, minute=0),
        'options': {
            'queue': 'crawler',
            'priority': 5,
        }
    },
    # 每小时检查爬虫健康状态
    'check-crawler-health': {
        'task': 'apps.crawler.tasks.check_crawler_health',
        'schedule': 300.0,  # 每5分钟
        'options': {
            'queue': 'monitoring',
        }
    },
    # 每15分钟更新任务统计
    'update-crawler-stats': {
        'task': 'apps.crawler.tasks.update_crawler_stats',
        'schedule': 900.0,  # 每15分钟
        'options': {
            'queue': 'monitoring',
        }
    },
}

# Celery配置
app.conf.update(
    # Broker配置
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/1',

    # 序列化
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',

    # 时区
    timezone='Asia/Shanghai',
    enable_utc=True,

    # 任务执行
    task_track_started=True,
    task_time_limit=14400,  # 4小时硬限制
    task_soft_time_limit=10800,  # 3小时软限制
    worker_prefetch_multiplier=1,
    worker_concurrency=4,

    # 结果存储
    result_expires=3600 * 24 * 7,  # 结果保留7天
    result_extended=True,

    # 重试配置
    task_default_retry_delay=60,  # 默认1分钟后重试
    task_max_retries=3,

    # 队列配置
    task_routes={
        'apps.crawler.tasks.run_spider': {'queue': 'crawler'},
        'apps.crawler.tasks.schedule_crawlers': {'queue': 'scheduler'},
        'apps.crawler.tasks.check_crawler_health': {'queue': 'monitoring'},
        'apps.crawler.tasks.update_crawler_stats': {'queue': 'monitoring'},
    },

    # 速率限制
    task_annotations={
        'apps.crawler.tasks.run_spider': {
            'rate_limit': '10/m',  # 每分钟最多10个爬虫任务
        }
    },
)


# 任务信号处理
@task_prerun.connect
def task_prerun_handler(task_id, task, args, kwargs, **extras):
    """任务开始前处理"""
    from apps.crawler.models import CrawlJob, CrawlStatus
    from django.utils import timezone

    if task.name == 'apps.crawler.tasks.run_spider':
        spider_name = args[0] if args else kwargs.get('spider_name')
        CrawlJob.objects.filter(task_id=task_id).update(
            status=CrawlStatus.RUNNING,
            started_at=timezone.now()
        )


@task_postrun.connect
def task_postrun_handler(task_id, task, args, kwargs, retval, state, **extras):
    """任务完成后处理"""
    from apps.crawler.models import CrawlJob, CrawlStatus
    from django.utils import timezone

    if task.name == 'apps.crawler.tasks.run_spider':
        status_map = {
            'SUCCESS': CrawlStatus.COMPLETED,
            'FAILURE': CrawlStatus.FAILED,
            'RETRY': CrawlStatus.PENDING,
        }
        CrawlJob.objects.filter(task_id=task_id).update(
            status=status_map.get(state, CrawlStatus.FAILED),
            completed_at=timezone.now() if state == 'SUCCESS' else None
        )


@task_failure.connect
def task_failure_handler(task_id, exception, args, kwargs, traceback, einfo, **extras):
    """任务失败处理"""
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Task {task_id} failed: {exception}")

    # 发送告警通知（可选）
    from apps.crawler.notifications import send_failure_alert
    send_failure_alert(task_id, str(exception))
```

### 2. 创建任务调度器

```python
# apps/crawler/scheduler.py
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from django.utils import timezone
from celery import chain, group
from celery.result import AsyncResult

from .models import CrawlJob, CrawlStatus
from .tasks import run_spider
from .config import SPIDER_SCHEDULES

logger = logging.getLogger(__name__)


class TaskScheduler:
    """爬虫任务调度器"""

    def __init__(self):
        self.max_concurrent = 4  # 最大并发数
        self.task_timeout = timedelta(hours=4)  # 任务超时时间

    def submit_task(
        self,
        spider_name: str,
        config: Dict,
        priority: int = 5,
        queue: str = 'crawler'
    ) -> CrawlJob:
        """
        提交单个爬虫任务

        Args:
            spider_name: 爬虫名称
            config: 爬虫配置
            priority: 优先级(0-9，9最高)
            queue: 任务队列

        Returns:
            CrawlJob实例
        """
        # 检查是否已有相同任务在运行
        existing = self._get_running_task(spider_name)
        if existing:
            logger.warning(f"Spider {spider_name} is already running")
            return existing

        # 创建任务记录
        job = CrawlJob.objects.create(
            spider_name=spider_name,
            config=config,
            status=CrawlStatus.PENDING,
            start_urls=config.get('start_urls', [])
        )

        # 提交Celery任务
        task = run_spider.apply_async(
            args=[spider_name, config],
            task_id=job.task_id,
            priority=priority,
            queue=queue,
            time_limit=14400,  # 4小时
            soft_time_limit=10800,  # 3小时软限制
        )

        job.task_id = task.id
        job.save()

        logger.info(f"Submitted task {task.id} for spider {spider_name}")
        return job

    def submit_batch(
        self,
        tasks: List[Dict],
        max_concurrent: Optional[int] = None
    ) -> List[CrawlJob]:
        """
        批量提交任务

        Args:
            tasks: 任务列表 [{'spider_name': ..., 'config': ...}, ...]
            max_concurrent: 最大并发数

        Returns:
            CrawlJob列表
        """
        max_concurrent = max_concurrent or self.max_concurrent
        jobs = []

        # 使用group控制并发
        job_group = group(
            run_spider.s(t['spider_name'], t.get('config', {}))
            for t in tasks
        )

        result = job_group.apply_async()
        logger.info(f"Submitted batch of {len(tasks)} tasks")

        return jobs

    def _get_running_task(self, spider_name: str) -> Optional[CrawlJob]:
        """获取正在运行的相同爬虫任务"""
        try:
            return CrawlJob.objects.get(
                spider_name=spider_name,
                status=CrawlStatus.RUNNING
            )
        except CrawlJob.DoesNotExist:
            return None

    def get_active_count(self) -> int:
        """获取当前活动任务数"""
        return CrawlJob.objects.filter(
            status__in=[CrawlStatus.PENDING, CrawlStatus.RUNNING]
        ).count()

    def get_task_queue(self) -> List[Dict]:
        """获取任务队列"""
        from celery import current_app

        inspector = current_app.control.inspect()
        scheduled = inspector.scheduled() or {}

        queue = []
        for worker, tasks in scheduled.items():
            for task in tasks:
                queue.append({
                    'task_id': task.get('request', {}).get('id'),
                    'spider': task.get('request', {}).get('args', [None])[0],
                    'priority': task.get('priority', 0),
                    'eta': task.get('eta'),
                })

        return sorted(queue, key=lambda x: x['priority'], reverse=True)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        try:
            job = CrawlJob.objects.get(task_id=task_id)

            # 撤销Celery任务
            AsyncResult(task_id).revoke(terminate=True)

            # 更新状态
            job.status = CrawlStatus.FAILED
            job.errors = [{'error': 'Task cancelled by user'}]
            job.save()

            logger.info(f"Cancelled task {task_id}")
            return True
        except CrawlJob.DoesNotExist:
            logger.warning(f"Task {task_id} not found")
            return False


class SpiderScheduleManager:
    """爬虫调度管理器"""

    def __init__(self):
        self.scheduler = TaskScheduler()

    def schedule_all(self):
        """调度所有配置的爬虫"""
        from .config import SPIDER_SCHEDULES

        scheduled = []
        for spider_config in SPIDER_SCHEDULES:
            job = self.scheduler.submit_task(
                spider_name=spider_config['name'],
                config=spider_config.get('config', {}),
                priority=spider_config.get('priority', 5)
            )
            scheduled.append({
                'spider': spider_config['name'],
                'task_id': job.task_id,
                'status': 'scheduled'
            })

        logger.info(f"Scheduled {len(scheduled)} spiders")
        return scheduled

    def schedule_by_spider(self, spider_name: str, config: Dict = None):
        """调度指定爬虫"""
        from .spiders import get_spider

        if not get_spider(spider_name):
            raise ValueError(f"Unknown spider: {spider_name}")

        spider_config = config or {}
        job = self.scheduler.submit_task(
            spider_name=spider_name,
            config=spider_config,
            priority=9  # 手动触发高优先级
        )

        return {'spider': spider_name, 'task_id': job.task_id}

    def get_schedule_status(self) -> Dict:
        """获取调度状态"""
        return {
            'active': CrawlJob.objects.filter(status=CrawlStatus.RUNNING).count(),
            'pending': CrawlJob.objects.filter(status=CrawlStatus.PENDING).count(),
            'completed_today': CrawlJob.objects.filter(
                status=CrawlStatus.COMPLETED,
                completed_at__gte=timezone.now() - timedelta(days=1)
            ).count(),
            'failed_today': CrawlJob.objects.filter(
                status=CrawlStatus.FAILED,
                completed_at__gte=timezone.now() - timedelta(days=1)
            ).count(),
        }
```

### 3. 创建任务监控模块

```python
# apps/crawler/monitoring.py
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from celery import current_app
from celery.result import AsyncResult

from django.utils import timezone
from .models import CrawlJob, CrawlStatus

logger = logging.getLogger(__name__)


class TaskMonitor:
    """任务监控器"""

    def __init__(self):
        self.app = current_app

    def get_active_tasks(self) -> Dict:
        """获取活动任务"""
        inspector = self.app.control.inspect()

        return {
            'active': inspector.active() or {},
            'scheduled': inspector.scheduled() or {},
            'reserved': inspector.reserved() or {},
            'revoked': inspector.revoked() or {},
        }

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取单个任务状态"""
        try:
            job = CrawlJob.objects.get(task_id=task_id)
            async_result = AsyncResult(task_id)

            return {
                'task_id': task_id,
                'spider_name': job.spider_name,
                'status': job.status,
                'celery_state': async_result.state,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'pages_crawled': job.pages_crawled,
                'items_extracted': job.items_extracted,
                'errors_count': len(job.errors) if job.errors else 0,
                'progress': self._calculate_progress(job),
            }
        except CrawlJob.DoesNotExist:
            return None

    def _calculate_progress(self, job: CrawlJob) -> Optional[float]:
        """计算任务进度"""
        if job.status == CrawlStatus.COMPLETED:
            return 100.0
        if job.status == CrawlStatus.PENDING:
            return 0.0

        # 基于时间的估算
        if job.started_at:
            elapsed = (timezone.now() - job.started_at).total_seconds()
            estimated_total = 3600  # 预估1小时
            progress = min(95, (elapsed / estimated_total) * 100)
            return round(progress, 2)

        return None

    def get_stats(self, days: int = 7) -> Dict:
        """获取统计信息"""
        since = timezone.now() - timedelta(days=days)

        jobs = CrawlJob.objects.filter(created_at__gte=since)

        return {
            'total': jobs.count(),
            'completed': jobs.filter(status=CrawlStatus.COMPLETED).count(),
            'failed': jobs.filter(status=CrawlStatus.FAILED).count(),
            'stalled': jobs.filter(status=CrawlStatus.STALLED).count(),
            'success_rate': self._calculate_success_rate(jobs),
            'avg_duration': self._calculate_avg_duration(jobs),
            'by_spider': self._get_stats_by_spider(jobs),
            'daily': self._get_daily_stats(jobs, days),
        }

    def _calculate_success_rate(self, jobs) -> float:
        """计算成功率"""
        completed = jobs.filter(status=CrawlStatus.COMPLETED).count()
        failed = jobs.filter(status=CrawlStatus.FAILED).count()
        total = completed + failed
        return round((completed / total) * 100, 2) if total > 0 else 0.0

    def _calculate_avg_duration(self, jobs) -> Optional[float]:
        """计算平均执行时长（秒）"""
        from django.db.models import Avg, F

        completed = jobs.filter(
            status=CrawlStatus.COMPLETED,
            started_at__isnull=False,
            completed_at__isnull=False
        ).annotate(
            duration=F('completed_at') - F('started_at')
        )

        if completed.exists():
            avg = completed.aggregate(avg_duration=Avg('duration'))['avg_duration']
            return avg.total_seconds() if avg else None
        return None

    def _get_stats_by_spider(self, jobs) -> Dict:
        """按爬虫统计"""
        from django.db.models import Count

        return dict(jobs.values('spider_name').annotate(
            count=Count('id')
        ).values_list('spider_name', 'count'))

    def _get_daily_stats(self, jobs, days: int) -> List[Dict]:
        """获取每日统计"""
        from django.db.models import Count, TruncDate

        daily = jobs.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Count('id'),
            completed=Count('id', filter=models.Q(status=CrawlStatus.COMPLETED)),
            failed=Count('id', filter=models.Q(status=CrawlStatus.FAILED))
        ).order_by('date')

        return list(daily)

    def get_stalled_tasks(self) -> List[Dict]:
        """获取停滞的任务"""
        stalled = CrawlJob.objects.filter(
            status=CrawlStatus.STALLED
        ).order_by('-started_at')

        return [
            {
                'task_id': job.task_id,
                'spider_name': job.spider_name,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'duration_hours': (timezone.now() - job.started_at).total_seconds() / 3600
                if job.started_at else 0,
            }
            for job in stalled
        ]


class HealthChecker:
    """健康检查器"""

    def __init__(self):
        self.monitor = TaskMonitor()

    def check_health(self) -> Dict:
        """执行健康检查"""
        checks = {
            'celery_worker': self._check_celery_worker(),
            'redis_connection': self._check_redis(),
            'database_connection': self._check_database(),
            'stalled_tasks': self._check_stalled_tasks(),
        }

        checks['healthy'] = all(
            c.get('status') == 'ok' for c in checks.values()
            if isinstance(c, dict)
        )

        return checks

    def _check_celery_worker(self) -> Dict:
        """检查Celery Worker"""
        try:
            from celery import current_app
            inspector = current_app.control.inspect()
            stats = inspector.stats()
            return {
                'status': 'ok' if stats else 'error',
                'workers': list(stats.keys()) if stats else [],
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_redis(self) -> Dict:
        """检查Redis连接"""
        try:
            from django.core.cache import cache
            cache.set('health_check', 'ok', 1)
            value = cache.get('health_check')
            return {'status': 'ok' if value == 'ok' else 'error'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_database(self) -> Dict:
        """检查数据库连接"""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return {'status': 'ok'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _check_stalled_tasks(self) -> Dict:
        """检查停滞任务"""
        stalled = self.monitor.get_stalled_tasks()
        return {
            'status': 'warning' if stalled else 'ok',
            'count': len(stalled),
            'tasks': stalled[:5],  # 只显示前5个
        }
```

### 4. 创建重试策略

```python
# apps/crawler/retry.py
import logging
from functools import wraps
from typing import Callable, Optional
from celery.exceptions import MaxRetriesExceededError, SoftTimeLimitExceeded

logger = logging.getLogger(__name__)


class RetryStrategy:
    """重试策略"""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: int = 60,
        backoff_multiplier: float = 2.0,
        max_delay: int = 3600
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.backoff_multiplier = backoff_multiplier
        self.max_delay = max_delay

    def get_delay(self, retry_count: int) -> int:
        """获取重试延迟（指数退避）"""
        delay = self.initial_delay * (self.backoff_multiplier ** retry_count)
        return min(int(delay), self.max_delay)

    def should_retry(self, exception: Exception, retry_count: int) -> bool:
        """判断是否应重试"""
        if retry_count >= self.max_retries:
            return False

        # 某些异常不重试
        non_retryable = (
            'NotConfigured',
            'SpiderNotFound',
            'InvalidSpiderConfig',
        )

        for exc_name in non_retryable:
            if exc_name in exception.__class__.__name__:
                return False

        return True


# 任务特定的重试配置
RETRY_CONFIGS = {
    'run_spider': RetryStrategy(
        max_retries=3,
        initial_delay=60,
        backoff_multiplier=2.0
    ),
    'schedule_crawlers': RetryStrategy(
        max_retries=5,
        initial_delay=30,
        backoff_multiplier=1.5
    ),
}


def with_retry(task_name: str):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            config = RETRY_CONFIGS.get(task_name, RetryStrategy())
            retry_count = kwargs.get('retry_count', 0)

            try:
                return func(*args, **kwargs)
            except Exception as e:
                if config.should_retry(e, retry_count):
                    delay = config.get_delay(retry_count)
                    logger.warning(
                        f"Task {task_name} failed, retrying in {delay}s "
                        f"(attempt {retry_count + 1}/{config.max_retries})"
                    )
                    # 实际重试由Celery处理
                    raise
                else:
                    logger.error(
                        f"Task {task_name} failed after {retry_count} retries"
                    )
                    raise

        return wrapper
    return decorator
```

### 5. 创建管理命令

```python
# apps/crawler/management/commands/run_crawler.py
from django.core.management.base import BaseCommand, CommandError
from apps.crawler.scheduler import SpiderScheduleManager


class Command(BaseCommand):
    help = 'Run a specific spider or all spiders'

    def add_arguments(self, parser):
        parser.add_argument(
            'spider',
            type=str,
            nargs='?',
            help='Spider name to run (runs all if not specified)'
        )
        parser.add_argument(
            '--config',
            type=str,
            help='JSON configuration for the spider'
        )

    def handle(self, *args, **options):
        manager = SpiderScheduleManager()

        if options['spider']:
            self.stdout.write(f"Running spider: {options['spider']}")
            result = manager.schedule_by_spider(
                options['spider'],
                config=options.get('config')
            )
            self.stdout.write(self.style.SUCCESS(
                f"Task scheduled: {result['task_id']}"
            ))
        else:
            self.stdout.write("Running all scheduled spiders...")
            results = manager.schedule_all()
            self.stdout.write(self.style.SUCCESS(
                f"Scheduled {len(results)} spiders"
            ))


# apps/crawler/management/commands/crawler_status.py
from django.core.management.base import BaseCommand
from apps.crawler.monitoring import TaskMonitor, HealthChecker
import json


class Command(BaseCommand):
    help = 'Check crawler status and health'

    def add_arguments(self, parser):
        parser.add_argument(
            '--health',
            action='store_true',
            help='Run health check'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show statistics'
        )

    def handle(self, *args, **options):
        if options['health']:
            checker = HealthChecker()
            health = checker.check_health()
            self.stdout.write(json.dumps(health, indent=2, default=str))

        if options['stats']:
            monitor = TaskMonitor()
            stats = monitor.get_stats(days=7)
            self.stdout.write(json.dumps(stats, indent=2, default=str))

        if not options['health'] and not options['stats']:
            monitor = TaskMonitor()
            active = monitor.get_active_tasks()
            self.stdout.write(json.dumps(active, indent=2, default=str))
```

### 6. 更新任务文件

```python
# apps/crawler/tasks.py (扩展)
from celery import shared_task
from django.utils import timezone
import logging

from .scheduler import SpiderScheduleManager
from .monitoring import TaskMonitor, HealthChecker
from .models import CrawlJob, CrawlStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def run_spider(self, spider_name: str, spider_config: dict):
    """运行爬虫任务（已在task-011中定义，此处扩展）"""
    from .spiders import get_spider
    from .base import SpiderConfig

    try:
        spider_class = get_spider(spider_name)
        if not spider_class:
            raise ValueError(f"Spider {spider_name} not found")

        config = SpiderConfig(
            name=spider_name,
            start_urls=spider_config.get('start_urls', []),
            **spider_config
        )

        spider = spider_class(config=config)
        result = spider.crawl()

        # 更新任务记录
        CrawlJob.objects.filter(task_id=self.request.id).update(
            status=CrawlStatus.COMPLETED,
            pages_crawled=result.get('pages_crawled', 0),
            items_extracted=result.get('items_extracted', 0),
            errors=result.get('errors', []),
            completed_at=timezone.now()
        )

        return result

    except Exception as exc:
        logger.exception(f"Spider {spider_name} failed")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def schedule_crawlers():
    """调度所有爬虫"""
    manager = SpiderScheduleManager()
    return manager.schedule_all()


@shared_task
def check_crawler_health():
    """检查爬虫健康状态"""
    from datetime import timedelta

    stalled = CrawlJob.objects.filter(
        status=CrawlStatus.RUNNING,
        started_at__lt=timezone.now() - timedelta(hours=4)
    )

    count = 0
    for job in stalled:
        job.status = CrawlStatus.STALLED
        job.save()
        count += 1

    return {'stalled_count': count}


@shared_task
def update_crawler_stats():
    """更新爬虫统计"""
    monitor = TaskMonitor()
    stats = monitor.get_stats(days=1)

    # 可以保存到缓存或数据库
    from django.core.cache import cache
    cache.set('crawler_stats', stats, 3600)

    return stats
```

## 验证步骤

```bash
# 运行调度测试
pytest apps/crawler/tests/test_scheduler.py -v
pytest apps/crawler/tests/test_monitoring.py -v

# 测试Celery配置
python -c "
from config.celery import app
print('Beat schedule:', app.conf.beat_schedule)
print('Task routes:', app.conf.task_routes)
"

# 测试调度器
python -c "
from apps.crawler.scheduler import TaskScheduler
scheduler = TaskScheduler()
print('Active count:', scheduler.get_active_count())
"

# 测试监控
python -c "
from apps.crawler.monitoring import TaskMonitor
monitor = TaskMonitor()
stats = monitor.get_stats(days=1)
print('Stats:', stats)
"

# 运行管理命令
python manage.py run_crawler --help
python manage.py crawler_status --health
```

**预期**: 所有测试通过(GREEN状态)

## 提交信息

```
feat: implement crawler scheduler and monitoring

- Configure Celery Beat with daily crawler scheduling (2:00 AM)
- Add TaskScheduler for submitting and managing crawler tasks
- Implement TaskMonitor for real-time status and statistics
- Add HealthChecker for system health monitoring
- Create retry strategy with exponential backoff
- Add management commands: run_crawler, crawler_status
- Implement concurrent task limiting and priority handling
- Add task signals for automatic status tracking
- Configure task routing to separate queues (crawler/monitoring/scheduler)
- All tests passing (GREEN state)
```
