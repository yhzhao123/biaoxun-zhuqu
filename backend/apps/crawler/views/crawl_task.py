"""
爬虫任务API视图 - Phase 6
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from ..models import CrawlTask, CrawlSource


class CrawlTaskSerializer(ModelSerializer):
    """爬虫任务序列化器"""

    class Meta:
        model = CrawlTask
        fields = [
            'id', 'name', 'source_url', 'source_site', 'source',
            'status', 'items_crawled', 'error_message',
            'started_at', 'completed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CrawlTaskViewSet(viewsets.ViewSet):
    """
    爬虫任务API视图集
    """

    def list(self, request):
        """获取爬虫任务列表 - 从数据库查询"""
        tasks = CrawlTask.objects.all().order_by('-created_at')

        # 支持状态筛选
        status_filter = request.query_params.get('status')
        if status_filter:
            tasks = tasks.filter(status=status_filter)

        # 支持来源筛选
        source_filter = request.query_params.get('source_site')
        if source_filter:
            tasks = tasks.filter(source_site=source_filter)

        serializer = CrawlTaskSerializer(tasks, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """
        触发爬虫任务

        请求参数:
        - source_id: CrawlSource ID (推荐)
        - source: 爬虫源名称 (兼容旧版本)

        优先使用 source_id，如果未提供则尝试使用第一个活跃的爬虫源
        """
        from apps.crawler.tasks import run_crawl_task

        source_id = request.data.get('source_id')
        source_name = request.data.get('source')

        crawl_source = None

        # 优先使用 source_id 查找
        if source_id:
            try:
                crawl_source = CrawlSource.objects.get(
                    id=source_id,
                    status=CrawlSource.STATUS_ACTIVE
                )
            except CrawlSource.DoesNotExist:
                return Response(
                    {'error': f'爬虫源不存在或未启用: source_id={source_id}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        # 兼容旧版本：使用 source 名称查找
        elif source_name:
            crawl_source = CrawlSource.objects.filter(
                name=source_name,
                status=CrawlSource.STATUS_ACTIVE
            ).first()
        # 使用默认：第一个活跃的爬虫源
        else:
            crawl_source = CrawlSource.objects.filter(
                status=CrawlSource.STATUS_ACTIVE
            ).first()

        if not crawl_source:
            return Response(
                {'error': '未找到可用的爬虫源，请先配置爬虫源'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 创建任务记录，关联爬虫源
        task = CrawlTask.objects.create(
            name=f'爬取任务 - {crawl_source.name}',
            source_url=crawl_source.base_url,
            source_site=crawl_source.name,
            source=crawl_source,
            status='pending'
        )

        # 触发Celery任务
        celery_task = run_crawl_task.delay(task.id)

        return Response({
            'task_id': task.id,
            'celery_task_id': celery_task.id,
            'status': 'pending',
            'source': crawl_source.name,
            'message': f'爬虫任务已启动: {crawl_source.name}'
        }, status=status.HTTP_201_CREATED)
