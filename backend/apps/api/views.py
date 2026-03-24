"""
API views - Phase 6 Task 036-045
API端点实现
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from django.utils.dateparse import parse_date

from apps.tenders.models import TenderNotice
from apps.tenders.repositories import TenderRepository
from apps.analytics.services import (
    StatisticsService,
    OpportunityAnalyzer,
    ReportGenerator,
)


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TenderViewSet(viewsets.ModelViewSet):
    """
    Tender API - Task 036-037

    招标公告 CRUD 操作
    """
    queryset = TenderNotice.objects.filter(is_deleted=False)
    serializer_class = None  # Will be defined below
    pagination_class = StandardResultsSetPagination
    repository = TenderRepository()

    def get_serializer_class(self):
        from .serializers import TenderSerializer
        return TenderSerializer

    def get_queryset(self):
        """支持过滤的查询集"""
        queryset = self.queryset

        # 状态过滤
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # 地区过滤
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__icontains=region)

        # 行业过滤
        industry = self.request.query_params.get('industry')
        if industry:
            queryset = queryset.filter(industry__icontains=industry)

        # 来源过滤
        source = self.request.query_params.get('source_site')
        if source:
            queryset = queryset.filter(source_site__icontains=source)

        # 日期范围
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(publish_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(publish_date__lte=end_date)

        # 预算范围
        min_budget = self.request.query_params.get('min_budget')
        max_budget = self.request.query_params.get('max_budget')
        if min_budget:
            queryset = queryset.filter(budget__gte=min_budget)
        if max_budget:
            queryset = queryset.filter(budget__lte=max_budget)

        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        搜索API - Task 038-039

        全文搜索招标公告
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response(
                {'error': 'Search query is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 使用 repository 的搜索方法
        results = self.repository.search(query)

        # 分页
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def filter_options(self, request):
        """
        筛选选项API - Task 040-041

        返回可用的筛选选项
        """
        # 获取所有地区
        regions = list(
            self.queryset.exclude(region='')
            .values_list('region', flat=True)
            .distinct()
        )

        # 获取所有行业
        industries = list(
            self.queryset.exclude(industry='')
            .values_list('industry', flat=True)
            .distinct()
        )

        # 获取所有来源
        sources = list(
            self.queryset.exclude(source_site='')
            .values_list('source_site', flat=True)
            .distinct()
        )

        return Response({
            'regions': regions,
            'industries': industries,
            'sources': sources,
            'statuses': [
                {'value': 'active', 'label': 'Active'},
                {'value': 'pending', 'label': 'Pending'},
                {'value': 'closed', 'label': 'Closed'},
                {'value': 'expired', 'label': 'Expired'},
            ]
        })

    @action(detail=True, methods=['post'])
    def mark_status(self, request, pk=None):
        """标记状态"""
        tender = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(TenderNotice.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )

        tender.status = new_status
        tender.save()

        serializer = self.get_serializer(tender)
        return Response(serializer.data)


class StatisticsViewSet(viewsets.ViewSet):
    """
    统计API - Task 042-043

    数据分析统计接口
    """

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """总览统计"""
        service = StatisticsService()
        data = service.get_overview()
        return Response(data)

    @action(detail=False, methods=['get'])
    def trend(self, request):
        """趋势数据"""
        days = int(request.query_params.get('days', 30))
        service = StatisticsService()
        data = service.get_trend(days)
        return Response(data)

    @action(detail=False, methods=['get'])
    def budget_distribution(self, request):
        """预算分布"""
        service = StatisticsService()
        data = service.get_budget_distribution()
        return Response(data)

    @action(detail=False, methods=['get'])
    def top_tenderers(self, request):
        """活跃招标人排行"""
        limit = int(request.query_params.get('limit', 10))
        service = StatisticsService()
        data = service.get_top_tenderers(limit)
        return Response(data)


class OpportunityViewSet(viewsets.ViewSet):
    """
    商机API - Task 044

    商机识别和分析接口
    """

    @action(detail=False, methods=['get'])
    def opportunities(self, request):
        """获取商机列表"""
        analyzer = OpportunityAnalyzer()
        data = analyzer.analyze_opportunities()
        return Response(data)

    @action(detail=False, methods=['get'])
    def high_value(self, request):
        """高价值招标"""
        limit = int(request.query_params.get('limit', 20))
        analyzer = OpportunityAnalyzer()
        data = analyzer._find_high_value(limit)
        return Response(data)

    @action(detail=False, methods=['get'])
    def urgent(self, request):
        """紧急招标"""
        limit = int(request.query_params.get('limit', 10))
        analyzer = OpportunityAnalyzer()
        data = analyzer._find_urgent(limit)
        return Response(data)


class ReportViewSet(viewsets.ViewSet):
    """
    报告API - Task 045

    报告生成接口
    """

    @action(detail=False, methods=['get'])
    def daily(self, request):
        """日报"""
        generator = ReportGenerator()
        data = generator.generate_daily_report()
        return Response(data)

    @action(detail=False, methods=['get'])
    def weekly(self, request):
        """周报"""
        generator = ReportGenerator()
        data = generator.generate_weekly_report()
        return Response(data)


class CrawlerTaskViewSet(viewsets.ViewSet):
    """
    爬虫任务API

    爬虫任务管理和触发
    """

    @action(detail=False, methods=['get'])
    def tasks(self, request):
        """获取爬虫任务列表"""
        from apps.crawler.models import CrawlTask

        tasks = CrawlTask.objects.all().order_by('-created_at')[:50]
        data = [
            {
                'id': t.id,
                'name': t.name,
                'source_url': t.source_url,
                'source_site': t.source_site,
                'status': t.status,
                'items_crawled': t.items_crawled,
                'error_message': t.error_message,
                'started_at': t.started_at.isoformat() if t.started_at else None,
                'completed_at': t.completed_at.isoformat() if t.completed_at else None,
                'created_at': t.created_at.isoformat(),
            }
            for t in tasks
        ]
        return Response(data)

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """触发爬虫"""
        from apps.crawler.tasks import scheduled_daily_crawl

        # 异步触发爬虫任务
        result = scheduled_daily_crawl.delay()

        return Response({
            'task_id': result.id,
            'status': 'triggered',
            'message': 'Crawl task has been scheduled'
        })
