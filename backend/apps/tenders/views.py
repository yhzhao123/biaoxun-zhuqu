"""
招标公告API视图 - Phase 6 Task 026-027
提供RESTful API接口
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta

from .models import TenderNotice
from .repositories import TenderRepository


class StandardResultsSetPagination(PageNumberPagination):
    """标准分页器"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class TenderViewSet(viewsets.ViewSet):
    """
    招标公告API视图集
    """
    pagination_class = StandardResultsSetPagination
    repository = TenderRepository()

    def list(self, request):
        """获取招标列表"""
        # 获取查询参数
        status_filter = request.query_params.get('status')
        region = request.query_params.get('region')
        industry = request.query_params.get('industry')
        search = request.query_params.get('search')

        # 构建查询
        queryset = TenderNotice.objects.all()

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if region:
            queryset = queryset.filter(region=region)
        if industry:
            queryset = queryset.filter(industry=industry)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(tenderer__icontains=search)
            )

        # 分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [self._serialize_tender(t) for t in page]
            return self.get_paginated_response(data)

        # 手动序列化
        data = [self._serialize_tender(t) for t in queryset]
        return Response({
            'count': len(data),
            'results': data,
            'page': 1,
            'page_size': len(data)
        })

    def retrieve(self, request, pk=None):
        """获取单个招标详情"""
        try:
            tender = TenderNotice.objects.get(id=pk)
            return Response(self._serialize_tender(tender))
        except TenderNotice.DoesNotExist:
            return Response(
                {'error': '招标公告不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def search(self, request):
        """搜索招标"""
        query = request.query_params.get('search', '')
        if not query:
            return Response({'results': [], 'count': 0})

        queryset = TenderNotice.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tenderer__icontains=query)
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            data = [self._serialize_tender(t) for t in page]
            return self.get_paginated_response(data)

        data = [self._serialize_tender(t) for t in queryset]
        return Response({
            'count': len(data),
            'results': data,
            'page': 1,
            'page_size': len(data)
        })

    @action(detail=False, methods=['get'])
    def export(self, request):
        """导出招标数据"""
        format_type = request.query_params.get('format', 'excel')
        queryset = TenderNotice.objects.all()
        data = [self._serialize_tender(t) for t in queryset]
        return Response({
            'data': data,
            'format': format_type,
            'count': len(data)
        })

    def _serialize_tender(self, tender):
        """序列化招标对象"""
        return {
            'id': str(tender.id),
            'notice_id': tender.notice_id,
            'title': tender.title,
            'description': tender.description,
            'tenderer': tender.tenderer,
            'budget': float(tender.budget) if tender.budget else None,
            'currency': tender.currency,
            'publish_date': tender.publish_date.isoformat() if tender.publish_date else None,
            'deadline_date': tender.deadline_date.isoformat() if tender.deadline_date else None,
            'region': tender.region,
            'industry': tender.industry,
            'source_url': tender.source_url,
            'source_site': tender.source_site,
            'status': tender.status,
            'created_at': tender.created_at.isoformat(),
            'updated_at': tender.updated_at.isoformat(),
        }

    def get_serializer(self, queryset, many=False):
        """兼容方法"""
        return None

    def paginate_queryset(self, queryset):
        """分页查询"""
        page_size = int(self.request.query_params.get('page_size', 20))
        page = int(self.request.query_params.get('page', 1))

        start = (page - 1) * page_size
        end = start + page_size
        return queryset[start:end]

    def get_paginated_response(self, data):
        """返回分页响应"""
        return Response({
            'count': len(data),
            'results': data,
            'page': int(self.request.query_params.get('page', 1)),
            'page_size': int(self.request.query_params.get('page_size', 20))
        })


class StatisticsViewSet(viewsets.ViewSet):
    """
    统计API视图集
    """

    def list(self, request):
        """获取统计数据"""
        total_tenders = TenderNotice.objects.count()
        active_tenders = TenderNotice.objects.filter(
            status=TenderNotice.STATUS_ACTIVE
        ).count()
        total_budget = TenderNotice.objects.aggregate(
            total=Sum('budget')
        )['total'] or 0

        # 按地区统计
        by_region = list(TenderNotice.objects.values('region').annotate(
            count=Count('id')
        ).order_by('-count')[:10])

        # 按行业统计
        by_industry = list(TenderNotice.objects.values('industry').annotate(
            count=Count('id')
        ).order_by('-count')[:10])

        # 按状态统计
        by_status = list(TenderNotice.objects.values('status').annotate(
            count=Count('id')
        ))

        return Response({
            'total_tenders': total_tenders,
            'active_tenders': active_tenders,
            'total_budget': float(total_budget),
            'by_region': by_region,
            'by_industry': by_industry,
            'by_status': by_status,
            'daily_trend': []
        })

    @action(detail=False, methods=['get'])
    def regions(self, request):
        """获取地区分布统计"""
        by_region = list(TenderNotice.objects.values('region').annotate(
            count=Count('id')
        ).order_by('-count'))
        return Response(by_region)

    @action(detail=False, methods=['get'])
    def industries(self, request):
        """获取行业分布统计"""
        by_industry = list(TenderNotice.objects.values('industry').annotate(
            count=Count('id')
        ).order_by('-count'))
        return Response(by_industry)

    @action(detail=False, methods=['get'])
    def trend(self, request):
        """获取趋势数据"""
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # 按日期统计
        queryset = TenderNotice.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).extra(
            select={'date': "DATE(created_at)"}
        ).values('date').annotate(count=Count('id')).order_by('date')

        data = [{'date': item['date'], 'count': item['count']} for item in queryset]
        return Response(data)
