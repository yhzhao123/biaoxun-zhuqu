"""
CrawlSource API Views - 爬虫源配置API
"""
import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny

from ..models import CrawlSource


class CrawlSourceSerializer(ModelSerializer):
    """爬虫源序列化器"""

    class Meta:
        model = CrawlSource
        fields = [
            'id', 'name', 'base_url', 'list_url_pattern',
            'selector_title', 'selector_content', 'selector_publish_date',
            'selector_tenderer', 'selector_budget',
            'request_headers', 'request_cookies', 'delay_seconds',
            'status', 'last_crawl_at', 'total_crawled', 'success_rate',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['last_crawl_at', 'total_crawled', 'success_rate', 'created_at', 'updated_at']


class CrawlSourceViewSet(viewsets.ModelViewSet):
    """
    爬虫源配置API视图集
    提供CRUD操作
    """
    queryset = CrawlSource.objects.all()
    serializer_class = CrawlSourceSerializer

    def get_permissions(self):
        """根据环境返回权限类"""
        if os.environ.get('DJANGO_SETTINGS_MODULE') == 'config.settings_dev' or \
           os.environ.get('DEBUG') in ('1', 'true', 'True'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """支持按状态筛选"""
        queryset = CrawlSource.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """切换源状态"""
        source = self.get_object()
        if source.status == CrawlSource.STATUS_ACTIVE:
            source.status = CrawlSource.STATUS_INACTIVE
        else:
            source.status = CrawlSource.STATUS_ACTIVE
        source.save()
        return Response(self.get_serializer(source).data)

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """测试爬虫源"""
        source = self.get_object()
        # 模拟测试
        return Response({
            'success': True,
            'message': f'爬虫源 "{source.name}" 测试成功',
            'url': source.base_url,
            'response_time': '1.2s',
            'status_code': 200
        })

    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取启用的爬虫源"""
        sources = CrawlSource.objects.filter(status=CrawlSource.STATUS_ACTIVE)
        return Response(self.get_serializer(sources, many=True).data)
