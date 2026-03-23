# Task 063: Tender API实现

## 任务信息

- **任务ID**: 063
- **任务名称**: Tender API实现
- **任务类型**: impl
- **依赖任务**: 062 (Tender API测试)

## BDD Scenario

```gherkin
Scenario: Tender API正常工作
  Given 所有Tender API测试已定义
  When 实现Django REST Framework视图和序列化器
  Then 所有API测试应通过
  And API应支持分页、搜索、筛选功能
  And API应返回标准化的JSON响应格式
```

## 实现目标

实现完整的Tender REST API，包括序列化器、视图集、过滤器和路由配置，使所有测试通过。

## 修改的文件

- `apps/tenders/serializers.py` - DRF序列化器(新建)
- `apps/tenders/views.py` - API视图集
- `apps/tenders/filters.py` - 过滤器类(新建)
- `apps/tenders/urls.py` - API路由
- `config/urls.py` - 根路由配置
- `config/settings/base.py` - DRF配置

## 实施步骤

### 1. 安装依赖

```bash
pip install djangorestframework djangorestframework-simplejwt django-filter
```

### 2. 配置Django REST Framework

```python
# config/settings/base.py

INSTALLED_APPS = [
    # ...
    'rest_framework',
    'rest_framework_simplejwt',
    'django_filters',
    # ...
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardResultsSetPagination',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}
```

### 3. 创建自定义分页类

```python
# apps/core/pagination.py

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data,
        })
```

### 4. 创建序列化器

```python
# apps/tenders/serializers.py

from rest_framework import serializers
from .models import TenderNotice


class TenderListSerializer(serializers.ModelSerializer):
    """招标列表序列化器 - 精简字段"""

    class Meta:
        model = TenderNotice
        fields = [
            'id', 'notice_id', 'title', 'tenderer',
            'budget', 'currency', 'publish_date', 'deadline_date',
            'region', 'industry', 'relevance_score', 'status',
            'created_at', 'updated_at',
        ]


class TenderDetailSerializer(serializers.ModelSerializer):
    """招标详情序列化器 - 完整字段"""
    ai_keywords = serializers.ListField(read_only=True)

    class Meta:
        model = TenderNotice
        fields = [
            'id', 'notice_id', 'title', 'description', 'tenderer',
            'budget', 'currency', 'publish_date', 'deadline_date',
            'region', 'industry', 'source_url', 'source_site',
            'ai_summary', 'ai_keywords', 'ai_category',
            'relevance_score', 'status', 'crawl_batch_id',
            'created_at', 'updated_at',
        ]


class TenderSearchSerializer(serializers.ModelSerializer):
    """招标搜索序列化器 - 包含高亮"""
    highlighted_title = serializers.SerializerMethodField()
    highlighted_description = serializers.SerializerMethodField()

    class Meta:
        model = TenderNotice
        fields = [
            'id', 'notice_id', 'title', 'description', 'tenderer',
            'budget', 'publish_date', 'region', 'industry',
            'highlighted_title', 'highlighted_description',
        ]

    def get_highlighted_title(self, obj):
        """获取高亮标题"""
        highlight = getattr(obj, 'highlighted_title', None)
        return highlight or obj.title

    def get_highlighted_description(self, obj):
        """获取高亮描述"""
        highlight = getattr(obj, 'highlighted_description', None)
        return highlight or obj.description[:200]
```

### 5. 创建过滤器

```python
# apps/tenders/filters.py

import django_filters
from django.db.models import Q
from .models import TenderNotice


class TenderFilter(django_filters.FilterSet):
    """招标信息过滤器"""

    budget_min = django_filters.NumberFilter(
        field_name='budget', lookup_expr='gte'
    )
    budget_max = django_filters.NumberFilter(
        field_name='budget', lookup_expr='lte'
    )
    publish_date_from = django_filters.DateFilter(
        field_name='publish_date', lookup_expr='gte'
    )
    publish_date_to = django_filters.DateFilter(
        field_name='publish_date', lookup_expr='lte'
    )
    deadline_date_from = django_filters.DateFilter(
        field_name='deadline_date', lookup_expr='gte'
    )
    deadline_date_to = django_filters.DateFilter(
        field_name='deadline_date', lookup_expr='lte'
    )
    region = django_filters.CharFilter(lookup_expr='iexact')
    industry = django_filters.CharFilter(lookup_expr='iexact')
    status = django_filters.CharFilter(lookup_expr='exact')
    tenderer = django_filters.CharFilter(lookup_expr='icontains')

    # 自定义搜索过滤器
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = TenderNotice
        fields = [
            'region', 'industry', 'status',
            'budget_min', 'budget_max',
            'publish_date_from', 'publish_date_to',
            'deadline_date_from', 'deadline_date_to',
        ]

    def filter_search(self, queryset, name, value):
        """多字段搜索"""
        if not value:
            return queryset
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(tenderer__icontains=value)
        )
```

### 6. 创建视图集

```python
# apps/tenders/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import TenderNotice
from .serializers import (
    TenderListSerializer,
    TenderDetailSerializer,
    TenderSearchSerializer,
)
from .filters import TenderFilter
from apps.core.pagination import StandardResultsSetPagination


class TenderViewSet(viewsets.ReadOnlyModelViewSet):
    """招标信息API视图集"""

    queryset = TenderNotice.objects.all()
    serializer_class = TenderListSerializer
    pagination_class = StandardResultsSetPagination
    filterset_class = TenderFilter
    search_fields = ['title', 'description', 'tenderer']
    ordering_fields = ['publish_date', 'budget', 'relevance_score', 'created_at']
    ordering = ['-publish_date']

    def get_serializer_class(self):
        """根据action返回不同的序列化器"""
        if self.action == 'retrieve':
            return TenderDetailSerializer
        elif self.action == 'search':
            return TenderSearchSerializer
        return TenderListSerializer

    def get_queryset(self):
        """获取查询集，支持高亮"""
        queryset = TenderNotice.objects.all()

        # 检查是否需要高亮
        highlight = self.request.query_params.get('highlight', 'false').lower() == 'true'
        search_query = self.request.query_params.get('search', '')

        if highlight and search_query:
            from django.contrib.postgres.search import SearchQuery, SearchHeadline
            search_vector = SearchQuery(search_query)
            queryset = queryset.annotate(
                highlighted_title=SearchHeadline(
                    'title', search_vector,
                    start_sel='<mark>', stop_sel='</mark>'
                ),
                highlighted_description=SearchHeadline(
                    'description', search_vector,
                    start_sel='<mark>', stop_sel='</mark>',
                    max_words=50, min_words=30
                )
            )

        return queryset.select_related().prefetch_related()

    @action(detail=False, methods=['get'])
    def search(self, request):
        """高级搜索接口"""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """统计信息接口"""
        from django.db.models import Count, Avg

        queryset = self.filter_queryset(self.get_queryset())
        stats = {
            'total_count': queryset.count(),
            'region_distribution': list(
                queryset.values('region').annotate(count=Count('id')).order_by('-count')[:10]
            ),
            'industry_distribution': list(
                queryset.values('industry').annotate(count=Count('id')).order_by('-count')[:10]
            ),
            'monthly_trend': list(
                queryset.extra(select={'month': "DATE_TRUNC('month', publish_date)"})
                .values('month')
                .annotate(count=Count('id'))
                .order_by('month')[:12]
            ),
        }
        return Response(stats)
```

### 7. 配置URL路由

```python
# apps/tenders/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenderViewSet

router = DefaultRouter()
router.register(r'tenders', TenderViewSet, basename='tender')

urlpatterns = [
    path('', include(router.urls)),
]
```

```python
# config/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.tenders.urls')),
    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
```

### 8. 创建API文档

```python
# apps/tenders/views.py (添加文档字符串)

class TenderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    招标信息API

    提供招标信息的查询、搜索、筛选功能。

    ## 认证
    - 需要JWT令牌认证

    ## 功能
    - 列表查询: GET /api/v1/tenders/
    - 详情查询: GET /api/v1/tenders/{id}/
    - 搜索: GET /api/v1/tenders/?search=关键词
    - 筛选: GET /api/v1/tenders/?region=北京&industry=IT
    - 排序: GET /api/v1/tenders/?ordering=-publish_date

    ## 分页
    - 默认每页20条
    - 可通过page_size参数调整(最大100)

    ## 高亮
    - 添加highlight=true启用搜索高亮
    """
    # ... 实现代码
```

## 验证步骤

```bash
# 1. 运行数据库迁移
python manage.py migrate

# 2. 运行API测试
pytest apps/tenders/tests/test_api.py -v

# 3. 测试API端点(开发服务器)
python manage.py runserver

# 4. 手动测试API
curl -X POST http://localhost:8000/api/v1/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "test", "password": "test"}'

curl http://localhost:8000/api/v1/tenders/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 预期结果

- 所有API测试通过(GREEN状态)
- API响应符合RESTful规范
- 分页、搜索、筛选功能正常工作
- 认证机制正常工作

## 提交信息

```
feat: implement Tender REST API

- Add DRF serializers for tender list/detail/search
- Add TenderFilter with multi-field filtering support
- Add TenderViewSet with pagination and search
- Configure JWT authentication with simplejwt
- Add API routes and URL configuration
- Add search highlight support
- Add statistics endpoint for data visualization
- All API tests passing (GREEN state)
```
