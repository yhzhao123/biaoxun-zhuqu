"""
Test: Crawl task trigger with CrawlSource association

TDD approach: Write failing tests first, then implement fixes.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import TestCase, Client
from apps.crawler.models import CrawlSource, CrawlTask


class CrawlTaskTriggerTest(TestCase):
    """测试爬虫任务触发逻辑"""

    def setUp(self):
        """创建测试数据"""
        self.source = CrawlSource.objects.create(
            name='Test Source',
            base_url='http://test.example.com',
            list_url_pattern='/list?page={page}',
            selector_title='h1',
            selector_content='.content',
            status='active'
        )

    def test_trigger_with_source_id_creates_task_with_source(self):
        """
        测试：使用 source_id 触发任务，任务应该关联到正确的 CrawlSource

        RED: 当前实现没有 source 字段，测试会失败
        """
        client = Client()

        response = client.post(
            '/api/v1/crawler/trigger/',
            {'source_id': self.source.id},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        # 验证任务创建
        data = response.json()
        self.assertIn('task_id', data)

        task = CrawlTask.objects.get(id=data['task_id'])

        # 验证任务关联了正确的爬虫源
        # RED: 当前 CrawlTask 没有 source 字段
        self.assertEqual(task.source_id, self.source.id)
        self.assertEqual(task.source_site, self.source.name)

    def test_trigger_with_invalid_source_id_returns_error(self):
        """
        测试：使用无效的 source_id 应该返回错误
        """
        client = Client()

        response = client.post(
            '/api/v1/crawler/trigger/',
            {'source_id': 99999},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_trigger_without_source_id_uses_default(self):
        """
        测试：不提供 source_id 时，应该使用第一个活跃的爬虫源
        """
        client = Client()

        response = client.post(
            '/api/v1/crawler/trigger/',
            {},
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()
        task = CrawlTask.objects.get(id=data['task_id'])

        # 应该使用第一个活跃的爬虫源
        self.assertEqual(task.source_site, self.source.name)


if __name__ == '__main__':
    import unittest
    unittest.main()