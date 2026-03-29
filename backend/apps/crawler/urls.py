"""
爬虫任务API路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CrawlTaskViewSet
from .views.crawl_source import CrawlSourceViewSet
from .views import deer_flow_views

router = DefaultRouter()
router.register(r'tasks', CrawlTaskViewSet, basename='crawltask')
router.register(r'sources', CrawlSourceViewSet, basename='crawlsource')

urlpatterns = [
    path('', include(router.urls)),
    path('trigger/', CrawlTaskViewSet.as_view({'post': 'trigger'}), name='crawl-trigger'),
    # Deer-Flow extraction endpoints
    path('deer-flow/extract', deer_flow_views.start_extraction, name='deer-flow-extract'),
    path('deer-flow/status/<str:task_id>', deer_flow_views.get_extraction_status, name='deer-flow-status'),
    path('deer-flow/results/<str:task_id>', deer_flow_views.get_extraction_results, name='deer-flow-results'),
    path('deer-flow/list', deer_flow_views.list_extractions, name='deer-flow-list'),
]
