"""
爬虫任务API视图 - Phase 6
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response


class CrawlTaskViewSet(viewsets.ViewSet):
    """
    爬虫任务API视图集
    """

    def list(self, request):
        """获取爬虫任务列表"""
        # 返回模拟数据，实际应该查询数据库
        tasks = [
            {
                'id': 1,
                'name': '中国政府采购网',
                'source_url': 'http://www.ccgp.gov.cn',
                'source_site': 'ccgp',
                'status': 'completed',
                'items_crawled': 150,
                'started_at': '2024-01-15T10:00:00Z',
                'completed_at': '2024-01-15T10:30:00Z',
                'created_at': '2024-01-15T09:00:00Z',
            },
            {
                'id': 2,
                'name': '中国招标投标公共服务平台',
                'source_url': 'http://www.cebpubservice.com',
                'source_site': 'cebpubservice',
                'status': 'running',
                'items_crawled': 45,
                'started_at': '2024-01-15T11:00:00Z',
                'completed_at': None,
                'created_at': '2024-01-15T11:00:00Z',
            }
        ]
        return Response(tasks)

    @action(detail=False, methods=['post'])
    def trigger(self, request):
        """触发爬虫任务"""
        source = request.data.get('source', 'default')
        # 实际应该调用 Celery 任务
        return Response({
            'task_id': 1,
            'status': 'pending',
            'message': f'爬虫任务已启动: {source}'
        })
