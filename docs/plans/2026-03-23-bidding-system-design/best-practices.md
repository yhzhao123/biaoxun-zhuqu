# Best Practices - 招标信息系统最佳实践

> 安全、性能、代码质量指南

## 目录

1. [安全实践](#安全实践)
2. [性能优化](#性能优化)
3. [代码质量](#代码质量)
4. [运维监控](#运维监控)
5. [开发规范](#开发规范)

---

## 安全实践

### 1. 数据安全

#### 敏感数据加密

```python
# 使用 django-cryptography 加密敏感字段
from django_cryptography.fields import encrypt

class TenderNotice(models.Model):
    # 普通字段
    title = models.CharField(max_length=500)

    # 敏感字段加密存储
    contact_phone = encrypt(models.CharField(max_length=20, blank=True))
    contact_email = encrypt(models.EmailField(blank=True))
```

#### 数据库连接安全

```python
# settings/production.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'sslmode': 'require',  # 强制SSL连接
        },
    }
}
```

### 2. API安全

#### 认证与授权

```python
# 自定义权限类
from rest_framework import permissions

class TenderPermission(permissions.BasePermission):
    """招标数据权限控制"""

    def has_object_permission(self, request, view, obj):
        # 管理员有全部权限
        if request.user.is_staff:
            return True

        # 检查数据权限
        user_regions = request.user.profile.allowed_regions
        if obj.region not in user_regions:
            return False

        return True

# API视图使用
class TenderDetailView(APIView):
    permission_classes = [IsAuthenticated, TenderPermission]
```

#### 请求限流

```python
# settings/base.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}
```

#### SQL注入防护

```python
# ✅ 正确做法 - 使用ORM参数化查询
TenderNotice.objects.filter(title__icontains=user_input)

# ❌ 错误做法 - 字符串拼接
TenderNotice.objects.raw(f"SELECT * FROM tender_notices WHERE title LIKE '%{user_input}%'")
```

### 3. 爬虫安全

#### 请求频率控制

```python
# apps/crawler/middleware/rate_limit.py
import time
import random
from scrapy import signals

class RateLimitMiddleware:
    """请求频率控制中间件"""

    def __init__(self, crawler):
        self.crawler = crawler
        self.delay_range = (1, 3)  # 随机延迟1-3秒

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def process_request(self, request, spider):
        # 添加随机延迟
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)

        # 添加请求头
        request.headers['User-Agent'] = self._get_random_ua()
        request.headers['Accept-Language'] = 'zh-CN,zh;q=0.9'

        return request

    def _get_random_ua(self):
        from fake_useragent import UserAgent
        return UserAgent().random
```

#### 代理池管理

```python
# apps/crawler/services/proxy_service.py
import requests
from typing import List, Optional
import random

class ProxyService:
    """代理池服务"""

    def __init__(self):
        self.proxies: List[dict] = []
        self._load_proxies()

    def _load_proxies(self):
        """从配置或API加载代理"""
        # 从Redis加载可用代理
        # 或使用第三方代理服务API
        pass

    def get_proxy(self) -> Optional[dict]:
        """获取随机代理"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)

    def mark_proxy_failed(self, proxy: dict):
        """标记代理失效"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            # 记录到失效列表，后续移除
```

### 4. 安全配置清单

| 检查项 | 状态 | 说明 |
|--------|------|------|
| DEBUG关闭 | ☐ | 生产环境必须关闭 |
| SECRET_KEY安全 | ☐ | 使用环境变量，长度>50 |
| ALLOWED_HOSTS配置 | ☐ | 限制允许的域名 |
| HTTPS强制 | ☐ | SECURE_SSL_REDIRECT |
| CSRF保护 | ☐ | 默认启用 |
| XSS保护 | ☐ | 模板自动转义 |
| 点击劫持防护 | ☐ | X-Frame-Options |
| 安全Cookie | ☐ | SESSION_COOKIE_SECURE |
| HSTS头 | ☐ | SECURE_HSTS_SECONDS |

---

## 性能优化

### 1. 数据库优化

#### 索引策略

```python
# models.py 中定义复合索引
class TenderNotice(models.Model):
    class Meta:
        indexes = [
            # 常用查询组合索引
            models.Index(
                fields=['region', '-publish_date'],
                name='idx_region_date'
            ),
            models.Index(
                fields=['industry', '-publish_date'],
                name='idx_industry_date'
            ),
            models.Index(
                fields=['tenderer', '-publish_date'],
                name='idx_tenderer_date'
            ),
            # 排序索引
            models.Index(
                fields=['-relevance_score'],
                name='idx_score'
            ),
        ]
```

#### 查询优化

```python
# ✅ 正确做法
# 1. 使用select_related减少查询
TenderNotice.objects.select_related('crawl_task').all()

# 2. 使用values/values_list减少数据传输
TenderNotice.objects.values('id', 'title', 'budget')

# 3. 分页查询
def get_tenders_page(page=1, per_page=20):
    return TenderNotice.objects.all()[
        (page-1)*per_page : page*per_page
    ]

# 4. 批量操作
TenderNotice.objects.bulk_create(tenders, batch_size=500)
TenderNotice.objects.bulk_update(tenders, ['status'], batch_size=500)

# ❌ 避免做法
# 1. N+1查询
for tender in TenderNotice.objects.all():  # 查询1次
    print(tender.crawl_task.name)  # 每次循环查询1次 = N次

# 2. 全表加载
all_tenders = list(TenderNotice.objects.all())  # 内存爆炸
```

#### 数据库分区

```sql
-- 按时间分区（适用于PostgreSQL）
CREATE TABLE tender_notices_partitioned (
    LIKE tender_notices INCLUDING ALL
) PARTITION BY RANGE (publish_date);

-- 创建月度分区
CREATE TABLE tender_notices_2024_01
    PARTITION OF tender_notices_partitioned
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### 2. 缓存策略

#### Redis缓存配置

```python
# settings/base.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        }
    }
}

# 缓存键前缀
CACHE_MIDDLEWARE_KEY_PREFIX = 'tender_system'
```

#### 缓存使用模式

```python
from django.core.cache import cache
from functools import wraps

def cached_result(timeout=300):
    """方法结果缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result

            # 执行并缓存
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator

# 使用示例
class TenderService:
    @cached_result(timeout=3600)  # 缓存1小时
    def get_tenderer_stats(self, tenderer: str):
        # 复杂统计查询
        return self._calculate_stats(tenderer)
```

#### 缓存失效策略

```python
# 数据更新时清除相关缓存
def update_tender(tender_id, data):
    tender = TenderNotice.objects.get(id=tender_id)

    # 更新数据
    for key, value in data.items():
        setattr(tender, key, value)
    tender.save()

    # 清除相关缓存
    cache.delete(f"tender:{tender_id}")
    cache.delete(f"tenderer_stats:{tender.tenderer}")
    cache.delete_pattern("tender_list:*")
```

### 3. 异步处理

#### Celery任务优化

```python
# 任务路由配置
CELERY_TASK_ROUTES = {
    'apps.crawler.tasks.*': {'queue': 'crawler'},
    'apps.analysis.tasks.*': {'queue': 'analysis', 'priority': 5},
    'apps.subscriptions.tasks.*': {'queue': 'notifications', 'priority': 3},
}

# 任务优先级
@shared_task(queue='analysis', priority=10)
def analyze_urgent_tender(tender_id):
    """高优先级分析任务"""
    pass

@shared_task(queue='analysis', priority=1)
def analyze_batch_tenders(tender_ids):
    """批量分析任务，低优先级"""
    pass
```

#### 批量处理

```python
@shared_task
def process_crawled_items_batch(task_id, items, batch_size=100):
    """批量处理爬取数据"""
    from django.db import transaction

    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]

        with transaction.atomic():
            for item in batch:
                process_single_item(item)

        # 每批次后暂停，避免数据库压力过大
        time.sleep(1)
```

### 4. 前端性能

#### 代码分割

```typescript
// React懒加载
import { lazy, Suspense } from 'react';

const TenderDetail = lazy(() => import('./pages/TenderDetail'));
const AnalysisDashboard = lazy(() => import('./pages/AnalysisDashboard'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/tenders/:id" element={<TenderDetail />} />
        <Route path="/analysis" element={<AnalysisDashboard />} />
      </Routes>
    </Suspense>
  );
}
```

#### 数据请求优化

```typescript
// 使用TanStack Query缓存
import { useQuery } from '@tanstack/react-query';

function TenderList() {
  const { data, isLoading } = useQuery({
    queryKey: ['tenders', filters],
    queryFn: () => fetchTenders(filters),
    staleTime: 5 * 60 * 1000, // 5分钟内视为新鲜数据
    cacheTime: 10 * 60 * 1000, // 缓存10分钟
  });
}
```

---

## 代码质量

### 1. 代码风格

#### Python代码规范

```python
# 遵循 PEP8 + Black 格式化
# 使用类型注解
from typing import List, Optional, Dict
from dataclasses import dataclass

@dataclass
class TenderData:
    """招标数据对象"""
    notice_id: str
    title: str
    tenderer: Optional[str] = None
    budget: Optional[float] = None

class TenderService:
    """招标信息服务

    提供招标数据的查询、处理和分析功能。
    """

    def process_new_tender(
        self,
        crawl_data: Dict[str, Any]
    ) -> TenderNotice:
        """处理新爬取的招标信息

        Args:
            crawl_data: 爬虫原始数据

        Returns:
            处理后的招标记录

        Raises:
            ValueError: 数据格式错误
        """
        # 实现逻辑
        pass
```

#### Django最佳实践

```python
# 使用Manager封装查询
class TenderNoticeManager(models.Manager):
    """招标信息查询管理器"""

    def published(self):
        """已发布的招标"""
        return self.filter(status='published')

    def by_tenderer(self, tenderer_name):
        """按招标人筛选"""
        return self.filter(tenderer__icontains=tenderer_name)

    def high_value(self, threshold=1000000):
        """高价值招标"""
        return self.filter(budget__gte=threshold)

class TenderNotice(models.Model):
    objects = TenderNoticeManager()
```

### 2. 错误处理

```python
# 自定义异常
class TenderSystemException(Exception):
    """系统基础异常"""
    pass

class CrawlException(TenderSystemException):
    """爬虫异常"""
    pass

class AnalysisException(TenderSystemException):
    """分析异常"""
    pass

# 服务层错误处理
class TenderService:
    def process_new_tender(self, data):
        try:
            # 业务逻辑
            pass
        except ValidationError as e:
            logger.warning(f"数据验证失败: {e}")
            raise TenderSystemException(f"无效的数据格式: {e}")
        except DatabaseError as e:
            logger.error(f"数据库错误: {e}")
            raise TenderSystemException("数据存储失败，请稍后重试")
```

### 3. 日志规范

```python
# 结构化日志配置
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

# 使用示例
logger = structlog.get_logger(__name__)

logger.info(
    "招标处理完成",
    tender_id=tender.id,
    tenderer=tender.tenderer,
    processing_time=elapsed_time,
)
```

---

## 运维监控

### 1. 应用监控

#### Sentry集成

```python
# settings/production.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=env('SENTRY_DSN'),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
)
```

#### Django Silk性能分析

```python
# settings/development.py
INSTALLED_APPS += ['silk']
MIDDLEWARE += ['silk.middleware.SilkyMiddleware']

SILKY_PYTHON_PROFILER = True
SILKY_ANALYZE_QUERIES = True
```

### 2. Celery监控

#### Flower配置

```python
# docker-compose.yml
services:
  flower:
    image: mher/flower:latest
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    ports:
      - "5555:5555"
```

### 3. 日志收集

```yaml
# docker-compose.yml 增加ELK
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
```

---

## 开发规范

### 1. Git工作流

```bash
# 分支命名
feature/招标搜索优化
bugfix/爬虫超时问题
hotfix/生产环境紧急修复

# Commit规范
type: subject

Types:
- feat: 新功能
- fix: 修复
- refactor: 重构
- docs: 文档
- test: 测试
- chore: 构建/工具

Example:
feat: 添加招标人画像分析功能

- 实现招标人统计查询
- 添加历史趋势图表
- 集成ECharts可视化
```

### 2. 代码审查清单

| 检查项 | 说明 |
|--------|------|
| 功能实现 | 是否满足需求 |
| 代码风格 | 是否符合PEP8 |
| 类型注解 | 是否有类型提示 |
| 测试覆盖 | 是否包含测试 |
| 文档注释 | 关键方法是否有docstring |
| 性能考虑 | 是否有N+1查询等性能问题 |
| 安全考虑 | 是否有SQL注入等安全风险 |
| 错误处理 | 是否有适当的异常处理 |

### 3. 环境管理

```bash
# 环境变量模板
# .env.example
DEBUG=False
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost:5432/tenders
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# 爬虫配置
CRAWL_PROXY_API_KEY=your-proxy-api-key
CAPTCHA_SERVICE_KEY=your-captcha-key

# AI配置
OPENAI_API_KEY=your-openai-key
```

---

## 推荐工具

| 类别 | 工具 | 用途 |
|------|------|------|
| 格式化 | Black, isort | Python代码格式化 |
| 类型检查 | mypy | 静态类型检查 |
| 测试 | pytest, pytest-django | 单元/集成测试 |
| 覆盖率 | coverage.py | 测试覆盖率统计 |
| Lint | flake8, pylint | 代码质量检查 |
| 安全 | bandit | Python安全扫描 |
| 依赖 | safety, pip-audit | 依赖安全扫描 |
| 文档 | Sphinx, MkDocs | 文档生成 |

---

*本文档基于 superpowers:brainstorming 技能生成*
