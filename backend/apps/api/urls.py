"""
API URLs - Phase 6
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    TenderViewSet,
    StatisticsViewSet,
    OpportunityViewSet,
    ReportViewSet,
    CrawlerTaskViewSet,
)

router = DefaultRouter()
router.register(r'tenders', TenderViewSet, basename='tender')

urlpatterns = [
    path('', include(router.urls)),

    # Statistics API
    path('statistics/', StatisticsViewSet.as_view({'get': 'overview'}), name='statistics-overview'),
    path('statistics/trend/', StatisticsViewSet.as_view({'get': 'trend'}), name='statistics-trend'),
    path('statistics/budget/', StatisticsViewSet.as_view({'get': 'budget_distribution'}), name='statistics-budget'),
    path('statistics/top-tenderers/', StatisticsViewSet.as_view({'get': 'top_tenderers'}), name='statistics-top-tenderers'),

    # Opportunities API
    path('opportunities/', OpportunityViewSet.as_view({'get': 'opportunities'}), name='opportunities'),
    path('opportunities/high-value/', OpportunityViewSet.as_view({'get': 'high_value'}), name='opportunities-high-value'),
    path('opportunities/urgent/', OpportunityViewSet.as_view({'get': 'urgent'}), name='opportunities-urgent'),

    # Reports API
    path('reports/daily/', ReportViewSet.as_view({'get': 'daily'}), name='report-daily'),
    path('reports/weekly/', ReportViewSet.as_view({'get': 'weekly'}), name='report-weekly'),

    # Crawler API
    path('crawler/tasks/', CrawlerTaskViewSet.as_view({'get': 'tasks'}), name='crawler-tasks'),
    path('crawler/trigger/', CrawlerTaskViewSet.as_view({'post': 'trigger'}), name='crawler-trigger'),
]
