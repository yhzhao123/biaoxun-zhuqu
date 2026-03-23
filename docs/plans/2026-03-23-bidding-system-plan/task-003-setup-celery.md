# Task 003: 配置Celery异步任务

**Task ID:** 003
**Task Name:** 配置Celery异步任务
**Type:** setup
**Depends-on:** [002]
**Status:** pending

---

## Description

Configure Celery for asynchronous task processing with Redis as the message broker. Set up task routing, result backend, and Flower monitoring interface.

---

## Files to Create

| File | Purpose |
|------|---------|
| `config/celery.py` | Celery application configuration |
| `apps/core/tasks.py` | Core shared tasks |
| `apps/core/signals.py` | Celery task signals |
| `scripts/celery_worker.sh` | Worker startup script |
| `scripts/celery_beat.sh` | Beat scheduler startup script |
| `scripts/flower.sh` | Flower monitoring startup script |
| `requirements/celery.txt` | Celery-specific dependencies |

## Files to Modify

| File | Changes |
|------|---------|
| `config/__init__.py` | Import celery app |
| `config/settings/base.py` | Add Celery configuration |
| `apps/__init__.py` | Ensure proper app loading |

---

## Implementation Steps

### 1. Install Dependencies

Create `requirements/celery.txt`:
```
celery>=5.3.0
redis>=5.0.0
flower>=2.0.0
django-celery-beat>=2.5.0
django-celery-results>=2.5.0
```

Update `requirements/base.txt`:
```
-r celery.txt
```

### 2. Celery Application Configuration

Create `config/celery.py`:
```python
import os
from celery import Celery
from celery.signals import task_failure, task_success

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('bidding_system')

# Load config from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

# Task routing configuration
app.conf.task_routes = {
    # Spider tasks - high priority queue
    'apps.spider.tasks.*': {'queue': 'spider'},
    # NLP tasks - compute intensive
    'apps.nlp.tasks.*': {'queue': 'nlp'},
    # Notification tasks - default queue
    'apps.notification.tasks.*': {'queue': 'default'},
    # Report generation - low priority
    'apps.report.tasks.*': {'queue': 'reports'},
    # Data sync tasks
    'apps.sync.tasks.*': {'queue': 'sync'},
}

# Task annotations for rate limiting
app.conf.task_annotations = {
    'apps.spider.tasks.fetch_*': {'rate_limit': '10/m'},
    'apps.nlp.tasks.analyze_*': {'rate_limit': '5/m'},
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f'Request: {self.request!r}')


@task_failure.connect
def handle_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **extras):
    """Handle task failures - log to monitoring system."""
    print(f'Task {sender.name} [{task_id}] failed: {exception}')


@task_success.connect
def handle_task_success(sender, result, **kwargs):
    """Handle task success - optional metrics collection."""
    pass
```

### 3. Update Celery Configuration in Settings

Add to `config/settings/base.py`:
```python
# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Serialization
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

# Task execution
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Disable prefetch for long tasks

# Result backend
CELERY_RESULT_EXPIRES = 3600  # 1 hour
CELERY_RESULT_EXTENDED = True

# Worker configuration
CELERY_WORKER_CONCURRENCY = 4
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# Beat scheduler
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SYNC_EVERY = 1

# Task queues
from kombu import Queue

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_QUEUES = (
    Queue('default', routing_key='task.#'),
    Queue('spider', routing_key='spider.#'),
    Queue('nlp', routing_key='nlp.#'),
    Queue('reports', routing_key='reports.#'),
    Queue('sync', routing_key='sync.#'),
)

# Celery beat schedule (defined in database via django-celery-beat)
# Initial schedules can be defined here for development
CELERY_BEAT_SCHEDULE = {}
```

### 4. Initialize Celery in Django

Update `config/__init__.py`:
```python
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### 5. Create Core Tasks Module

Create `apps/core/tasks.py`:
```python
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def health_check_task(self):
    """Simple health check task."""
    try:
        return {'status': 'ok', 'task_id': self.request.id}
    except SoftTimeLimitExceeded:
        logger.warning('Health check task timed out')
        raise
    except Exception as exc:
        logger.error(f'Health check failed: {exc}')
        raise self.retry(exc=exc, countdown=60)


@shared_task
def cleanup_old_tasks():
    """Cleanup old task results from backend."""
    from django_celery_results.models import TaskResult
    from datetime import timedelta
    from django.utils import timezone

    cutoff = timezone.now() - timedelta(days=7)
    deleted, _ = TaskResult.objects.filter(date_done__lt=cutoff).delete()
    return f'Deleted {deleted} old task results'
```

### 6. Create Startup Scripts

Create `scripts/celery_worker.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")/.."

# Default queue workers
exec celery -A config worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=default,spider,nlp,reports,sync \
    --hostname=worker@%h \
    --pidfile=/tmp/celery_worker.pid
```

Create `scripts/celery_beat.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")/.."

exec celery -A config beat \
    --loglevel=info \
    --scheduler django_celery_beat.schedulers:DatabaseScheduler \
    --pidfile=/tmp/celery_beat.pid
```

Create `scripts/flower.sh`:
```bash
#!/bin/bash
cd "$(dirname "$0")/.."

exec celery -A config flower \
    --port=5555 \
    --broker=redis://localhost:6379/0 \
    --basic_auth=admin:admin \
    --url_prefix=flower
```

Make scripts executable:
```bash
chmod +x scripts/*.sh
```

### 7. Update Installed Apps

Add to `config/settings/base.py` INSTALLED_APPS:
```python
INSTALLED_APPS = [
    # ... existing apps
    'django_celery_beat',
    'django_celery_results',
]
```

### 8. Run Migrations

```bash
python manage.py migrate django_celery_results
python manage.py migrate django_celery_beat
```

---

## Verification Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements/celery.txt
   ```

2. **Test Celery connection:**
   ```bash
   python -c "
   from config.celery import app
   print(f'Broker: {app.conf.broker_url}')
   print(f'Result Backend: {app.conf.result_backend}')
   print('Celery app loaded successfully')
   "
   ```

3. **Start worker and test task:**
   ```bash
   # Terminal 1: Start worker
   celery -A config worker --loglevel=info

   # Terminal 2: Run debug task
   python -c "
   from config.celery import debug_task
   result = debug_task.delay()
   print(f'Task ID: {result.id}')
   print(f'Result: {result.get(timeout=10)}')
   "
   ```

4. **Test Flower (optional):**
   ```bash
   celery -A config flower --port=5555
   # Open http://localhost:5555
   ```

5. **Verify database tables:**
   ```bash
   python manage.py dbshell
   # \dt (should show django_celery_* tables)
   ```

---

## Git Commit Message

```
chore: configure Celery for async task processing

- Set up Celery with Redis broker and result backend
- Configure task routing for spider, nlp, reports, sync queues
- Add Flower monitoring interface
- Integrate django-celery-beat for database-backed scheduling
- Add task signals for error handling
- Create startup scripts for worker, beat, and flower
```
