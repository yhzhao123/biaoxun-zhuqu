"""
测试 deer-flow API 视图

测试 REST API 端点
"""
import pytest
from unittest.mock import patch, Mock
from django.test import Client
import json


class TestDeerFlowAPIEndpoints:
    """测试 Deer-Flow API 端点"""

    def setup_method(self):
        """设置测试客户端"""
        self.client = Client()
        self.base_url = '/api/v1/crawler/deer-flow'

    def test_start_extraction_missing_source_url(self):
        """测试缺少 source_url 的请求"""
        response = self.client.post(
            f'{self.base_url}/extract',
            data=json.dumps({}),
            content_type='application/json'
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_start_extraction_invalid_source_url(self):
        """测试无效的 source_url 请求"""
        response = self.client.post(
            f'{self.base_url}/extract',
            data=json.dumps({"source_url": ""}),
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_get_status_not_found(self):
        """测试获取不存在的任务状态"""
        response = self.client.get(f'{self.base_url}/status/invalid-task-id')

        assert response.status_code == 404

    def test_get_results_not_found(self):
        """测试获取不存在的任务结果"""
        response = self.client.get(f'{self.base_url}/results/invalid-task-id')

        assert response.status_code == 404

    def test_list_extractions(self):
        """测试列出所有任务"""
        response = self.client.get(f'{self.base_url}/list')

        assert response.status_code == 200
        data = response.json()
        assert "tasks" in data

    @patch('apps.crawler.services.deer_flow_extraction.get_extraction_service')
    def test_start_extraction_sync_success(self, mock_get_service):
        """测试同步提取成功"""
        mock_service = Mock()
        mock_service.extract_tenders.return_value = {
            "success": True,
            "items": [{"title": "测试", "url": "http://example.com/1"}],
            "total_fetched": 1
        }
        mock_get_service.return_value = mock_service

        response = self.client.post(
            f'{self.base_url}/extract',
            data=json.dumps({
                "source_url": "http://api.example.com",
                "max_pages": 2
            }),
            content_type='application/json'
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "result" in data

    @patch('apps.crawler.services.deer_flow_extraction.get_extraction_service')
    def test_get_extraction_status_success(self, mock_get_service):
        """测试获取任务状态成功"""
        from apps.crawler.services.deer_flow_extraction import ExtractionTask

        mock_task = ExtractionTask(
            id="test-123",
            source_url="http://api.example.com",
            status="completed",
            error_message=None
        )

        mock_service = Mock()
        mock_service.get_task.return_value = mock_task
        mock_get_service.return_value = mock_service

        response = self.client.get(f'{self.base_url}/status/test-123')

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-123"
        assert data["status"] == "completed"

    @patch('apps.crawler.services.deer_flow_extraction.get_extraction_service')
    def test_get_extraction_results_success(self, mock_get_service):
        """测试获取任务结果成功"""
        from apps.crawler.services.deer_flow_extraction import ExtractionTask

        mock_task = ExtractionTask(
            id="test-123",
            source_url="http://api.example.com",
            status="completed",
            result={
                "success": True,
                "items": [{"title": "测试"}],
                "total_fetched": 1
            }
        )

        mock_service = Mock()
        mock_service.get_task.return_value = mock_task
        mock_get_service.return_value = mock_service

        response = self.client.get(f'{self.base_url}/results/test-123')

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "result" in data


class TestDeerFlowTasks:
    """测试 Celery 任务"""

    @patch('apps.crawler.services.deer_flow_extraction.get_extraction_service')
    def test_run_deer_flow_extraction_task(self, mock_get_service):
        """测试执行提取任务"""
        from apps.crawler.services.deer_flow_extraction import ExtractionTask

        mock_task = ExtractionTask(
            id="test-123",
            source_url="http://api.example.com",
            status="completed",
            result={"success": True, "total_fetched": 1}
        )

        mock_service = Mock()
        mock_service.get_task.return_value = mock_task
        mock_service.run_task.return_value = {
            "success": True,
            "total_fetched": 1
        }
        mock_get_service.return_value = mock_service

        from apps.crawler.tasks import run_deer_flow_extraction

        result = run_deer_flow_extraction("test-123")

        assert result["status"] == "completed"
        assert result["success"] is True

    def test_run_batch_extraction_task(self):
        """测试批量提取任务"""
        from apps.crawler.tasks import run_batch_extraction

        sources = [
            {"url": "http://api1.example.com", "type": "api"},
            {"url": "http://api2.example.com", "type": "api"},
        ]

        # 使用 mock 避免实际执行
        with patch('apps.crawler.deer_flow.workflow.TenderExtractionWorkflow') as MockWorkflow:
            mock_workflow = Mock()
            mock_result = Mock()
            mock_result.to_dict.return_value = {"success": True, "items": []}
            mock_workflow.extract = Mock(return_value=mock_result)

            with patch('asyncio.new_event_loop') as mock_loop:
                mock_loop_instance = Mock()
                mock_loop_instance.run_until_complete.return_value = [
                    {"url": "http://api1.example.com", "success": True}
                ]
                mock_loop.return_value = mock_loop_instance

                result = run_batch_extraction(sources)

                assert "status" in result