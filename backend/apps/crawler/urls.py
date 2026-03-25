"""
爬虫任务API路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CrawlTaskViewSet
from .views.crawl_source import CrawlSourceViewSet

router = DefaultRouter()
router.register(r'tasks', CrawlTaskViewSet, basename='crawltask')
router.register(r'sources', CrawlSourceViewSet, basename='crawlsource')

urlpatterns = [
    path('', include(router.urls)),
    path('trigger/', CrawlTaskViewSet.as_view({'post': 'trigger'}), name='crawl-trigger'),
]
