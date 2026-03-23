# Architecture - 招标信息系统架构文档

> 详细技术架构与组件设计

## 目录

1. [系统架构概览](#系统架构概览)
2. [技术栈详解](#技术栈详解)
3. [数据流设计](#数据流设计)
4. [模块详细设计](#模块详细设计)
5. [接口设计](#接口设计)
6. [安全设计](#安全设计)

---

## 系统架构概览

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                          用户层 (Users)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ 销售/业务    │  │ 系统管理员   │  │   管理层     │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
└─────────┼─────────────────┼─────────────────┼──────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    React 18 + TypeScript                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │ Dashboard│ │  Tenders │ │ Analysis │ │   Admin  │       │   │
│  │  │  仪表盘  │ │  招标列表│ │  深度分析│ │  管理后台│       │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ HTTPS/REST API
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API层 (Backend)                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  Django 4.2 + DRF 3.14                      │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐               │   │
│  │  │  TenderAPI │ │  CrawlAPI  │ │AnalysisAPI │               │   │
│  │  │  招标API   │ │ 爬虫API   │ │ 分析API   │               │   │
│  │  └────────────┘ └────────────┘ └────────────┘               │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐               │   │
│  │  │  AuthAPI   │ │  UserAPI   │ │ NotifyAPI  │               │   │
│  │  │ 认证API   │ │ 用户API   │ │ 通知API   │               │   │
│  │  └────────────┘ └────────────┘ └────────────┘               │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
          ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Service层     │    │   Celery Worker │    │   Celery Beat   │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │TenderService│ │    │ │Crawl Tasks  │ │    │ │ Scheduled   │ │
│ │招标服务     │ │    │ │爬虫任务     │ │    │ │ Tasks       │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ │定时任务     │ │
│ ┌─────────────┐ │    │ ┌─────────────┘ │    │ └─────────────┘ │
│ │AIService    │ │    │ │AI Analysis  │ │    └─────────────────┘
│ │AI服务       │ │    │ │分析任务     │ │
│ └─────────────┘ │    │ └─────────────┘ │
│ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │CrawlService │ │    │ │Notification │ │
│ │爬虫服务     │ │    │ │通知任务     │ │
│ └─────────────┘ │    │ └─────────────┘ │
└────────┬────────┘    └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Repository层 (Data Access)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ TenderRepo   │  │  CrawlRepo   │  │   UserRepo   │              │
│  │ 招标数据访问 │  │ 爬虫数据访问 │  │ 用户数据访问 │              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
└─────────┼─────────────────┼─────────────────┼──────────────────────┘
          │                 │                 │
          └─────────────────┴─────────────────┘
                            │
          ┌─────────────────┴─────────────────┐
          │                                   │
          ▼                                   ▼
┌─────────────────────┐          ┌─────────────────────┐
│    PostgreSQL 15    │          │      Redis 7        │
│  ┌───────────────┐  │          │  ┌───────────────┐  │
│  │ tender_notices│  │          │  │   任务队列    │  │
│  │ crawl_tasks   │  │          │  │   缓存数据    │  │
│  │ users         │  │          │  │   Session     │  │
│  └───────────────┘  │          │  └───────────────┘  │
└─────────────────────┘          └─────────────────────┘
```

---

## 技术栈详解

### 后端技术栈

#### Django 4.2 LTS

**选择理由**:
- 内置Admin后台，便于招标数据管理
- 成熟ORM，支持复杂查询和聚合
- 完善的安全机制（CSRF、XSS防护）
- 丰富的生态（django-celery、django-filter等）

**关键配置**:
```python
# settings/base.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'rest_framework',
    'django_filters',
    'django_celery_beat',
    'django_celery_results',
    # 项目应用
    'apps.tenders',
    'apps.crawler',
    'apps.analysis',
    'apps.subscriptions',
]

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

#### Celery 5.3 + Redis

**架构设计**:
```python
# config/celery.py
from celery import Celery

app = Celery('tender_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 队列配置
CELERY_TASK_ROUTES = {
    'apps.crawler.tasks.*': {'queue': 'crawler'},
    'apps.analysis.tasks.*': {'queue': 'analysis'},
    'apps.subscriptions.tasks.*': {'queue': 'notifications'},
}
```

**任务类型**:
- `crawler`: 爬虫任务队列
- `analysis`: AI分析任务队列
- `notifications`: 通知任务队列

#### PostgreSQL 15

**数据库配置**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tenders',
        'USER': 'tender_user',
        'PASSWORD': '***',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 600,  # 连接池
    }
}
```

### 前端技术栈

#### React 18 + TypeScript

**项目结构**:
```
frontend/
├── src/
│   ├── components/       # 通用组件
│   ├── pages/           # 页面组件
│   │   ├── Dashboard/
│   │   ├── Tenders/
│   │   ├── Analysis/
│   │   └── Admin/
│   ├── hooks/           # 自定义Hooks
│   ├── services/        # API服务
│   ├── store/           # 状态管理 (Zustand)
│   ├── types/           # TypeScript类型
│   └── utils/           # 工具函数
├── public/
└── package.json
```

**API客户端**:
```typescript
// services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL,
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

---

## 数据流设计

### 爬虫数据流

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ 定时任务触发 │───▶│  爬虫执行   │───▶│  数据清洗   │───▶│  NLP处理   │
│(Celery Beat)│    │(Scrapy/    │    │(Pipeline)  │    │(实体提取)  │
│             │    │ Playwright)│    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘
                                                                 │
                                                                 ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  商机分析   │◀───│  分类聚类   │◀───│  数据存储   │◀───│  标准化    │
│(评分/推荐)  │    │(行业/地区)  │    │(PostgreSQL) │    │(字段映射)  │
└──────┬──────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │
       ▼
┌─────────────┐    ┌─────────────┐
│  通知触发   │───▶│  用户通知   │
│(匹配订阅)   │    │(邮件/站内)  │
└─────────────┘    └─────────────┘
```

### API请求数据流

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Client  │───▶│  Nginx   │───▶│  Django  │───▶│ Service  │───▶│ Repository│
│  Request │    │  (Proxy) │    │   View   │    │  Layer   │    │  Layer   │
└──────────┘    └──────────┘    └────┬─────┘    └──────────┘    └────┬─────┘
                                     │                               │
                                     │                               │
                                     ▼                               ▼
                               ┌──────────┐                   ┌──────────┐
                               │ Serializer│                  │  Model   │
                               │          │                   │ (ORM)    │
                               └──────────┘                   └──────────┘
```

---

## 模块详细设计

### 1. Tender模块（招标信息）

#### 核心模型

```python
# apps/tenders/models.py
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.indexes import GinIndex

class TenderNotice(models.Model):
    """招标信息模型"""

    class Status(models.TextChoices):
        PENDING = 'pending', '待处理'
        PROCESSED = 'processed', '已处理'
        ANALYZED = 'analyzed', '已分析'

    # 基础信息
    notice_id = models.CharField(max_length=64, unique=True, db_index=True)
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    tenderer = models.CharField(max_length=200, blank=True, db_index=True)
    winner = models.CharField(max_length=200, blank=True)

    # 金额信息
    budget = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    final_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    currency = models.CharField(max_length=3, default='CNY')

    # 时间地点
    publish_date = models.DateField(db_index=True)
    deadline_date = models.DateField(null=True, blank=True)
    region = models.CharField(max_length=100, db_index=True)
    industry = models.CharField(max_length=100, db_index=True)

    # 来源
    source_url = models.URLField()
    source_site = models.CharField(max_length=100)

    # AI分析结果
    ai_summary = models.TextField(blank=True)
    ai_keywords = models.JSONField(default=list, blank=True)
    ai_category = models.CharField(max_length=50, blank=True)
    relevance_score = models.DecimalField(max_digits=5, decimal_places=4, null=True)

    # 状态管理
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    crawl_batch_id = models.BigIntegerField(null=True, db_index=True)

    # 元数据
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tender_notices'
        indexes = [
            models.Index(fields=['-publish_date']),
            models.Index(fields=['tenderer', '-publish_date']),
            models.Index(fields=['region', '-publish_date']),
            models.Index(fields=['industry', '-publish_date']),
            models.Index(fields=['-relevance_score']),
            GinIndex(fields=['ai_keywords'], name='tender_ai_keywords_gin'),
        ]

    def __str__(self):
        return f"{self.notice_id} - {self.title[:50]}"
```

#### Repository层

```python
# apps/tenders/repositories.py
from typing import List, Optional, Dict, Any
from django.db import transaction
from django.db.models import Q, QuerySet
from .models import TenderNotice

class TenderRepository:
    """招标信息数据访问层"""

    def __init__(self):
        self.model = TenderNotice

    def get_by_id(self, tender_id: int) -> Optional[TenderNotice]:
        """根据ID获取"""
        try:
            return self.model.objects.get(id=tender_id)
        except self.model.DoesNotExist:
            return None

    def get_by_notice_id(self, notice_id: str) -> Optional[TenderNotice]:
        """根据招标编号获取"""
        try:
            return self.model.objects.get(notice_id=notice_id)
        except self.model.DoesNotExist:
            return None

    def find_duplicates(self, title: str, publish_date, tenderer: str = None) -> QuerySet:
        """查找可能重复的招标"""
        queryset = self.model.objects.filter(
            title__icontains=title[:50],
            publish_date=publish_date
        )
        if tenderer:
            queryset = queryset.filter(tenderer__icontains=tenderer)
        return queryset[:5]

    @transaction.atomic
    def create_or_update(self, data: Dict[str, Any]) -> TenderNotice:
        """创建或更新招标信息"""
        notice_id = data.get('notice_id')

        defaults = {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'tenderer': data.get('tenderer', ''),
            'winner': data.get('winner', ''),
            'budget': data.get('budget'),
            'final_amount': data.get('final_amount'),
            'currency': data.get('currency', 'CNY'),
            'publish_date': data.get('publish_date'),
            'deadline_date': data.get('deadline_date'),
            'region': data.get('region', ''),
            'industry': data.get('industry', ''),
            'source_url': data.get('source_url', ''),
            'source_site': data.get('source_site', ''),
            'crawl_batch_id': data.get('crawl_batch_id'),
            'status': TenderNotice.Status.PENDING,
        }

        notice, created = self.model.objects.update_or_create(
            notice_id=notice_id,
            defaults=defaults
        )
        return notice

    def search(
        self,
        keywords: Optional[str] = None,
        regions: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_budget: Optional[float] = None,
        max_budget: Optional[float] = None,
        status: Optional[str] = None,
        order_by: str = '-publish_date',
        limit: int = 20,
        offset: int = 0
    ) -> QuerySet:
        """多条件搜索"""
        queryset = self.model.objects.all()

        # 关键词搜索
        if keywords:
            queryset = queryset.filter(
                Q(title__icontains=keywords) |
                Q(description__icontains=keywords) |
                Q(tenderer__icontains=keywords)
            )

        # 地区筛选
        if regions:
            queryset = queryset.filter(region__in=regions)

        # 行业筛选
        if industries:
            queryset = queryset.filter(industry__in=industries)

        # 时间范围
        if start_date:
            queryset = queryset.filter(publish_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(publish_date__lte=end_date)

        # 金额范围
        if min_budget:
            queryset = queryset.filter(budget__gte=min_budget)
        if max_budget:
            queryset = queryset.filter(budget__lte=max_budget)

        # 状态筛选
        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by(order_by)[offset:offset+limit]

    def get_tenderer_stats(self, tenderer: str) -> Dict:
        """获取招标人统计信息"""
        from django.db.models import Count, Sum, Avg

        stats = self.model.objects.filter(tenderer=tenderer).aggregate(
            total_count=Count('id'),
            total_budget=Sum('budget'),
            avg_budget=Avg('budget')
        )
        return stats

    def get_by_tenderer(self, tenderer: str, limit: int = 100) -> QuerySet:
        """按招标人获取招标列表"""
        return self.model.objects.filter(
            tenderer__icontains=tenderer
        ).order_by('-publish_date')[:limit]
```

#### Service层

```python
# apps/tenders/services.py
from typing import List, Dict, Any
from django.db import transaction
from .models import TenderNotice
from .repositories import TenderRepository
from ..analysis.services import AIService

class TenderService:
    """招标信息业务逻辑层"""

    def __init__(self):
        self.repo = TenderRepository()
        self.ai_service = AIService()

    @transaction.atomic
    def process_new_tender(self, crawl_data: Dict[str, Any]) -> TenderNotice:
        """处理新爬取的招标信息"""
        # 1. 去重检查
        existing = self.repo.get_by_notice_id(crawl_data.get('notice_id'))
        if existing:
            return existing

        # 2. 检查相似度去重
        duplicates = self.repo.find_duplicates(
            title=crawl_data.get('title', ''),
            publish_date=crawl_data.get('publish_date'),
            tenderer=crawl_data.get('tenderer', '')
        )

        if duplicates.exists():
            # 更新现有记录或标记为重复
            pass

        # 3. 创建记录
        tender = self.repo.create_or_update(crawl_data)

        # 4. 异步触发AI分析
        from ..analysis.tasks import analyze_tender_task
        analyze_tender_task.delay(tender.id)

        return tender

    def get_tender_detail(self, tender_id: int) -> Dict[str, Any]:
        """获取招标详情"""
        tender = self.repo.get_by_id(tender_id)
        if not tender:
            raise ValueError(f"Tender not found: {tender_id}")

        # 获取同招标人历史
        related = self.repo.get_by_tenderer(tender.tenderer, limit=5)

        return {
            'tender': tender,
            'related_tenders': list(related),
            'tenderer_stats': self.repo.get_tenderer_stats(tender.tenderer)
        }

    def search_tenders(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """搜索招标信息"""
        results = self.repo.search(**filters)
        total = results.count()

        return {
            'results': list(results),
            'total': total,
            'page': filters.get('offset', 0) // filters.get('limit', 20) + 1,
            'per_page': filters.get('limit', 20)
        }
```

### 2. Crawler模块（爬虫）

#### 任务定义

```python
# apps/crawler/tasks.py
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.utils import timezone
from .models import CrawlTask
from .spiders.gov_spider import GovSpider
from .spiders.platform_spider import PlatformSpider

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_crawl_task(self, task_id: int):
    """执行爬取任务"""
    task = CrawlTask.objects.get(id=task_id)

    # 更新任务状态
    task.crawl_status = 'running'
    task.started_at = timezone.now()
    task.save()

    try:
        # 根据任务类型选择爬虫
        if 'gov' in task.source_site.lower():
            spider = GovSpider()
        else:
            spider = PlatformSpider()

        # 执行爬取
        items = spider.crawl(task.source_url)

        # 更新任务状态
        task.items_crawled = len(items)
        task.crawl_status = 'completed'
        task.completed_at = timezone.now()
        task.save()

        # 异步处理爬取的数据
        from ..tenders.tasks import process_crawled_items
        process_crawled_items.delay(task.id, items)

        return {
            'status': 'success',
            'task_id': task_id,
            'items_count': len(items)
        }

    except Exception as exc:
        task.crawl_status = 'failed'
        task.error_message = str(exc)
        task.save()

        # 重试逻辑
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            return {
                'status': 'failed',
                'task_id': task_id,
                'error': str(exc)
            }

@shared_task
def scheduled_daily_crawl():
    """每日定时爬取任务"""
    from django.conf import settings

    sources = settings.CRAWL_SOURCES
    created_tasks = []

    for source in sources:
        task = CrawlTask.objects.create(
            task_name=f"{source['name']}-{timezone.now().strftime('%Y%m%d')}",
            source_url=source['url'],
            source_site=source['name']
        )
        run_crawl_task.delay(task.id)
        created_tasks.append(task.id)

    return {
        'status': 'success',
        'tasks_created': len(created_tasks),
        'task_ids': created_tasks
    }
```

#### 爬虫基类

```python
# apps/crawler/spiders/base_spider.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
import scrapy
from scrapy.http import Response

class BaseSpider(ABC):
    """爬虫基类"""

    name: str = 'base'

    def __init__(self):
        self.proxy_pool = []
        self.current_proxy = None

    @abstractmethod
    def crawl(self, url: str) -> List[Dict[str, Any]]:
        """执行爬取，返回结构化数据列表"""
        pass

    @abstractmethod
    def parse_list(self, response: Response) -> List[Dict]:
        """解析列表页"""
        pass

    @abstractmethod
    def parse_detail(self, response: Response) -> Dict:
        """解析详情页"""
        pass

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """提取实体信息"""
        # 调用NLP服务
        from ..services.nlp_service import NLPService
        return NLPService.extract(text)
```

### 3. Analysis模块（AI分析）

#### AI服务

```python
# apps/analysis/services.py
from typing import Dict, List, Any
import numpy as np
from django.conf import settings

class AIService:
    """AI分析服务"""

    def __init__(self):
        self.nlp_service = NLPService()
        self.scoring_service = OpportunityScoringService()

    def analyze_tender(self, tender_data: Dict) -> Dict[str, Any]:
        """分析单个招标"""
        # 1. NLP实体提取
        entities = self.nlp_service.extract(tender_data.get('description', ''))

        # 2. 分类
        category = self.classify_tender(tender_data)

        # 3. 关键词提取
        keywords = self.extract_keywords(tender_data)

        # 4. 生成摘要
        summary = self.generate_summary(tender_data)

        return {
            'ai_summary': summary,
            'ai_keywords': keywords,
            'ai_category': category,
            'entities': entities,
            'relevance_score': 0.0,  # 后续计算
        }

    def calculate_opportunity_score(
        self,
        tender: Dict,
        user_profile: Dict
    ) -> float:
        """计算商机评分"""
        return self.scoring_service.calculate(tender, user_profile)

    def classify_tender(self, tender_data: Dict) -> str:
        """招标分类"""
        # 基于规则和NLP的分类
        title = tender_data.get('title', '')

        industry_keywords = {
            '信息技术': ['信息化', '软件', '系统', 'IT', '智能', '平台'],
            '建筑工程': ['建筑', '工程', '施工', '建设'],
            '医疗设备': ['医疗', '医院', '设备', '器械'],
            '教育': ['学校', '教育', '教学', '校园'],
        }

        for industry, keywords in industry_keywords.items():
            if any(kw in title for kw in keywords):
                return industry

        return '其他'

    def extract_keywords(self, tender_data: Dict) -> List[str]:
        """提取关键词"""
        text = f"{tender_data.get('title', '')} {tender_data.get('description', '')}"
        # 使用TF-IDF或BERT提取关键词
        return self.nlp_service.extract_keywords(text, top_k=10)

    def generate_summary(self, tender_data: Dict) -> str:
        """生成摘要"""
        description = tender_data.get('description', '')
        if len(description) <= 200:
            return description

        # 使用LLM或抽取式摘要
        return self.nlp_service.summarize(description, max_length=200)


class OpportunityScoringService:
    """商机评分服务"""

    def calculate(self, tender: Dict, user_profile: Dict) -> Dict:
        """多因子商机评分"""

        # 1. 时效性评分 (0-100)
        time_score = self._calculate_time_urgency(tender)

        # 2. 匹配度评分 (0-100)
        match_score = self._calculate_match_score(tender, user_profile)

        # 3. 竞争度评分 (0-100)
        competition_score = self._calculate_competition_score(tender)

        # 4. 价值度评分 (0-100)
        value_score = self._calculate_value_score(tender)

        # 5. 历史胜率 (0-100)
        win_rate = self._get_historical_win_rate(tender, user_profile)

        # 加权计算
        weights = {
            'time': 0.15,
            'match': 0.30,
            'competition': 0.20,
            'value': 0.20,
            'win_rate': 0.15
        }

        total_score = (
            time_score * weights['time'] +
            match_score * weights['match'] +
            competition_score * weights['competition'] +
            value_score * weights['value'] +
            win_rate * weights['win_rate']
        )

        return {
            'opportunity_score': round(total_score, 2),
            'breakdown': {
                'time': round(time_score, 2),
                'match': round(match_score, 2),
                'competition': round(competition_score, 2),
                'value': round(value_score, 2),
                'win_rate': round(win_rate, 2)
            }
        }

    def _calculate_time_urgency(self, tender: Dict) -> float:
        """计算时效性评分"""
        from datetime import datetime, date

        publish_date = tender.get('publish_date')
        deadline_date = tender.get('deadline_date')

        if not deadline_date:
            return 50.0

        days_remaining = (deadline_date - date.today()).days

        if days_remaining <= 7:
            return 100.0
        elif days_remaining <= 30:
            return 80.0
        elif days_remaining <= 60:
            return 60.0
        else:
            return 40.0

    def _calculate_match_score(self, tender: Dict, user_profile: Dict) -> float:
        """计算匹配度评分"""
        # 使用语义相似度
        tender_text = f"{tender.get('title', '')} {tender.get('description', '')}"
        user_keywords = user_profile.get('keywords', [])

        if not user_keywords:
            return 50.0

        matches = sum(1 for kw in user_keywords if kw in tender_text)
        return min(100.0, matches * 20)

    def _calculate_competition_score(self, tender: Dict) -> float:
        """计算竞争度评分"""
        # 竞争度越高，评分越低
        competitor_count = tender.get('competitor_count', 0)
        return max(0, 100 - competitor_count * 10)

    def _calculate_value_score(self, tender: Dict) -> float:
        """计算价值度评分"""
        budget = tender.get('budget', 0)

        if budget >= 10000000:  # 1000万以上
            return 100.0
        elif budget >= 5000000:  # 500万以上
            return 80.0
        elif budget >= 1000000:  # 100万以上
            return 60.0
        else:
            return 40.0

    def _get_historical_win_rate(self, tender: Dict, user_profile: Dict) -> float:
        """获取历史胜率"""
        # 从用户历史数据计算
        return user_profile.get('historical_win_rate', 50.0)
```

#### Celery分析任务

```python
# apps/analysis/tasks.py
from celery import shared_task
from django.utils import timezone
from .services import AIService
from ..tenders.models import TenderNotice

@shared_task(bind=True, max_retries=2)
def analyze_tender_task(self, tender_id: int):
    """异步分析招标任务"""
    try:
        tender = TenderNotice.objects.get(id=tender_id)

        ai_service = AIService()

        # 准备数据
        tender_data = {
            'title': tender.title,
            'description': tender.description,
            'tenderer': tender.tenderer,
            'budget': tender.budget,
            'industry': tender.industry,
        }

        # 执行分析
        analysis_result = ai_service.analyze_tender(tender_data)

        # 更新招标记录
        tender.ai_summary = analysis_result['ai_summary']
        tender.ai_keywords = analysis_result['ai_keywords']
        tender.ai_category = analysis_result['ai_category']
        tender.status = TenderNotice.Status.ANALYZED
        tender.save()

        return {
            'status': 'success',
            'tender_id': tender_id,
            'analysis': analysis_result
        }

    except Exception as exc:
        self.retry(exc=exc, countdown=300)
```

---

## 接口设计

### REST API 规范

#### 招标信息接口

```yaml
# 获取招标列表
GET /api/v1/tenders
Parameters:
  - page: int (default: 1)
  - per_page: int (default: 20, max: 100)
  - keywords: string
  - regions: array<string>
  - industries: array<string>
  - start_date: date (YYYY-MM-DD)
  - end_date: date (YYYY-MM-DD)
  - min_budget: number
  - max_budget: number
  - ordering: string (default: "-publish_date")

Response:
  {
    "results": [Tender],
    "total": 1000,
    "page": 1,
    "per_page": 20,
    "total_pages": 50
  }

# 获取招标详情
GET /api/v1/tenders/{id}
Response:
  {
    "id": 1,
    "notice_id": "ZB202403001",
    "title": "...",
    "tenderer": "...",
    "related_tenders": [...],
    "tenderer_stats": {
      "total_count": 50,
      "total_budget": 50000000,
      "avg_budget": 1000000
    }
  }

# 高级搜索
POST /api/v1/tenders/search
Body:
  {
    "keywords": "云计算",
    "filters": {
      "regions": ["广东省"],
      "industries": ["信息技术"],
      "budget_range": [100000, 500000]
    },
    "sort": "-relevance_score",
    "page": 1,
    "per_page": 20
  }
```

#### 分析接口

```yaml
# 获取商机推荐
GET /api/v1/analysis/opportunities
Parameters:
  - limit: int (default: 10)
  - min_score: float (default: 60)

Response:
  {
    "opportunities": [
      {
        "tender": Tender,
        "opportunity_score": 85.5,
        "breakdown": {
          "time": 90,
          "match": 85,
          "competition": 80,
          "value": 90,
          "win_rate": 75
        }
      }
    ]
  }

# 获取趋势分析
GET /api/v1/analysis/trends
Parameters:
  - period: string ("month" | "quarter" | "year")
  - industry: string

Response:
  {
    "trends": [
      {
        "period": "2024-01",
        "count": 150,
        "total_budget": 150000000
      }
    ],
    "growth_rate": 15.5
  }

# 获取招标人画像
GET /api/v1/analysis/tenderers/{tenderer_name}
Response:
  {
    "name": "某市人民医院",
    "total_tenders": 50,
    "total_budget": 50000000,
    "avg_budget": 1000000,
    "favorite_industries": ["医疗设备", "信息化"],
    "top_suppliers": ["A公司", "B公司"],
    "trend": "up"
  }
```

#### 爬虫管理接口（Admin）

```yaml
# 获取爬虫任务列表
GET /api/v1/crawl/tasks
Response:
  {
    "tasks": [
      {
        "id": 1,
        "name": "政府采购网-20240323",
        "status": "completed",
        "items_crawled": 500,
        "started_at": "2024-03-23T02:00:00Z",
        "completed_at": "2024-03-23T05:30:00Z"
      }
    ]
  }

# 创建爬虫任务
POST /api/v1/crawl/tasks
Body:
  {
    "name": "新数据源",
    "source_url": "http://example.com/tenders",
    "source_site": "ExampleSite",
    "schedule": "0 2 * * *"  # cron表达式
  }

# 手动触发爬虫
POST /api/v1/crawl/tasks/{id}/run
Response:
  {
    "task_id": 1,
    "celery_task_id": "abc-123",
    "status": "queued"
  }
```

---

## 安全设计

### 认证与授权

```python
# JWT认证配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}
```

### 权限控制矩阵

| 角色 | 招标查看 | 搜索筛选 | 订阅管理 | 数据导出 | 爬虫配置 | 用户管理 |
|------|----------|----------|----------|----------|----------|----------|
| 销售/业务 | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| 数据分析师 | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| 管理层 | ✓ | ✓ | ✗ | ✓ | ✗ | ✗ |
| 系统管理员 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### 数据安全

1. **传输加密**: HTTPS/TLS 1.3
2. **存储加密**: 数据库敏感字段加密
3. **API限流**: 每分钟100请求
4. **SQL注入防护**: Django ORM参数化查询
5. **XSS防护**: 模板自动转义

### 爬虫安全

1. **请求频率控制**: 避免被封禁
2. **IP代理池**: 轮换代理避免单一IP请求过多
3. **User-Agent轮换**: 模拟真实浏览器
4. **请求间隔随机化**: jitter ±30%

---

*本文档基于 superpowers:brainstorming 技能生成*
