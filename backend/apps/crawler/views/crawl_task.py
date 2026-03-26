"""
爬虫任务API视图 - Phase 6
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from ..models import CrawlTask


class CrawlTaskSerializer(ModelSerializer):
    """爬虫任务序列化器"""

    class Meta:
        model = CrawlTask
        fields = [
            'id', 'name', 'source_url', 'source_site',
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
        """触发爬虫任务"""
        from apps.crawler.tasks import run_crawl_task

        source = request.data.get('source', 'default')

        # 创建任务记录
        task = CrawlTask.objects.create(
            name=f'爬取任务 - {source}',
            source_url=f'http://{source}.com',
            source_site=source,
            status='pending'
        )

        # 触发Celery任务
        celery_task = run_crawl_task.delay(task.id)

        return Response({
            'task_id': task.id,
            'celery_task_id': celery_task.id,
            'status': 'pending',
            'message': f'爬虫任务已启动: {source}'
        })
