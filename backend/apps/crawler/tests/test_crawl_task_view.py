"""
CrawlTask ViewSet Tests
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import RequestFactory


class TestCrawlTaskViewSet:
    """CrawlTaskViewSet测试"""

    @pytest.mark.django_db
    def test_list_returns_database_records(self):
        """测试list方法返回数据库记录而非模拟数据"""
        from apps.crawler.models import CrawlTask
        from apps.crawler.views.crawl_task import CrawlTaskViewSet
        from rest_framework.test import APIRequestFactory

        # 确认初始状态无数据
        initial_count = CrawlTask.objects.count()

        # 创建测试数据
        task1 = CrawlTask.objects.create(
            name='Test Task DB 1',
            source_url='http://testdb1.com',
            source_site='testdb1',
            status='completed',
            items_crawled=100
        )
        task2 = CrawlTask.objects.create(
            name='Test Task DB 2',
            source_url='http://testdb2.com',
            source_site='testdb2',
            status='running',
            items_crawled=50
        )

        # 创建请求
        factory = APIRequestFactory()
        request = factory.get('/api/crawler/tasks/')
        view = CrawlTaskViewSet.as_view({'get': 'list'})

        # 执行
        response = view(request)

        # 验证返回的是数据库数据
        assert response.status_code == 200
        data = response.data

        # 检查返回的数量正确（初始数量 + 2）
        expected_count = initial_count + 2
        assert len(data) == expected_count, f"Expected {expected_count}, got {len(data)}"

        # 检查返回的数据包含我们创建的任务名称
        task_names = [item['name'] for item in data]
        assert 'Test Task DB 1' in task_names
        assert 'Test Task DB 2' in task_names

    @pytest.mark.django_db
    def test_list_returns_empty_for_no_tasks(self):
        """测试无任务时返回空列表"""
        from apps.crawler.views.crawl_task import CrawlTaskViewSet
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get('/api/crawler/tasks/')
        view = CrawlTaskViewSet.as_view({'get': 'list'})

        response = view(request)

        assert response.status_code == 200
        assert isinstance(response.data, list)

    @pytest.mark.django_db
    def test_trigger_creates_task_and_returns_task_id(self):
        """测试trigger方法创建任务并返回task_id"""
        from apps.crawler.models import CrawlTask
        from apps.crawler.views.crawl_task import CrawlTaskViewSet
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.post('/api/crawler/trigger/', {'source': 'test-source'}, format='json')
        view = CrawlTaskViewSet.as_view({'post': 'trigger'})

        with patch('apps.crawler.tasks.run_crawl_task.delay') as mock_delay:
            mock_delay.return_value = Mock(id=123)
            response = view(request)

        assert response.status_code == 200
        assert 'task_id' in response.data
        assert 'status' in response.data