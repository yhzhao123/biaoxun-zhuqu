"""
爬虫任务API路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CrawlTaskViewSet

router = DefaultRouter()
router.register(r'tasks', CrawlTaskViewSet, basename='crawltask')

urlpatterns = [
    path('', include(router.urls)),
    path('trigger/', CrawlTaskViewSet.as_view({'post': 'trigger'}), name='crawl-trigger'),
]
