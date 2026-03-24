"""
招标公告API路由 - Phase 6 Task 026
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenderViewSet, StatisticsViewSet

router = DefaultRouter()
router.register(r'tenders', TenderViewSet, basename='tender')
router.register(r'statistics', StatisticsViewSet, basename='statistics')

urlpatterns = [
    path('', include(router.urls)),
]
