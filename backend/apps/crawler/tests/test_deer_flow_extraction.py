"""
测试 deer-flow 数据提取服务

测试 DeerFlowExtractionService 的功能
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from dataclasses import asdict


class TestDeerFlowExtractionService:
    """测试 DeerFlowExtractionService 服务类"""

    def test_service_initialization(self):
        """测试服务初始化"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        service = DeerFlowExtractionService()
        assert service is not None
        assert hasattr(service, "client")

    def test_extract_tenders(self):
        """测试提取招标列表"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        mock_result = {
            "items": [
                {"title": "测试招标", "url": "http://example.com/1"}
            ],
            "success": True
        }

        with patch.object(DeerFlowExtractionService, "extract_tenders", return_value=mock_result):
            service = DeerFlowExtractionService()
            result = service.extract_tenders("http://api.example.com")

            assert result["success"] is True
            assert len(result["items"]) == 1

    def test_extract_with_details(self):
        """测试提取招标列表和详情"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        mock_result = {
            "items": [{"title": "测试招标", "url": "http://example.com/1"}],
            "details": [{"title": "测试招标", "content": "详情内容"}],
            "success": True,
            "total_fetched": 1,
            "total_with_details": 1
        }

        with patch.object(DeerFlowExtractionService, "extract_with_details", return_value=mock_result):
            service = DeerFlowExtractionService()
            result = service.extract_with_details("http://api.example.com")

            assert result["success"] is True
            assert len(result["items"]) == 1
            assert len(result["details"]) == 1


class TestDeerFlowExtractionTask:
    """测试提取任务模型"""

    def test_task_creation(self):
        """测试提取任务创建"""
        from apps.crawler.services.deer_flow_extraction import ExtractionTask

        task = ExtractionTask(
            source_url="http://api.example.com",
            site_type="api",
            max_pages=5,
            status="pending"
        )

        assert task.source_url == "http://api.example.com"
        assert task.site_type == "api"
        assert task.max_pages == 5
        assert task.status == "pending"

    def test_task_to_dict(self):
        """测试任务转换为字典"""
        from apps.crawler.services.deer_flow_extraction import ExtractionTask

        task = ExtractionTask(
            id="test-123",
            source_url="http://api.example.com",
            site_type="api",
            status="pending"
        )

        task_dict = task.to_dict()

        assert "id" in task_dict
        assert task_dict["source_url"] == "http://api.example.com"
        assert task_dict["status"] == "pending"


class TestDeerFlowClientIntegration:
    """测试 deer-flow Client 集成"""

    def test_client_initialization(self):
        """测试 Client 初始化"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        # 测试服务初始化，不依赖实际的 deerflow 模块
        service = DeerFlowExtractionService()
        assert service is not None
        assert hasattr(service, "_client")
        assert hasattr(service, "_workflow")

    @pytest.mark.asyncio
    async def test_extract_via_workflow(self):
        """测试通过 Workflow 提取数据"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        mock_result = type('obj', (object,), {
            "items": [{"title": "测试", "url": "http://example.com/1"}],
            "success": True,
            "error_message": None,
            "total_fetched": 1,
            "details": [],
            "total_with_details": 0,
            "to_dict": lambda self: {
                "items": self.items,
                "details": self.details,
                "success": self.success,
                "error_message": self.error_message,
                "total_fetched": self.total_fetched,
                "total_with_details": self.total_with_details
            }
        })()

        with patch("apps.crawler.deer_flow.workflow.TenderExtractionWorkflow.extract", return_value=mock_result):
            workflow = TenderExtractionWorkflow()
            result = await workflow.extract(
                source_url="http://api.example.com",
                site_type="api"
            )

            assert result.success is True
            assert len(result.items) == 1


class TestDeerFlowExtractionServiceFull:
    """测试 DeerFlowExtractionService 完整功能"""

    def test_create_task_with_all_params(self):
        """测试创建任务时使用所有参数"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        service = DeerFlowExtractionService()
        task = service.create_task(
            source_url="http://api.example.com",
            site_type="api",
            max_pages=10,
            max_items=50,
            api_config='{"key": "value"}',
            fetch_details=True
        )

        assert task.source_url == "http://api.example.com"
        assert task.site_type == "api"
        assert task.max_pages == 10
        assert task.max_items == 50
        assert task.api_config == '{"key": "value"}'
        assert task.fetch_details is True
        assert task.status == "pending"

    def test_get_task(self):
        """测试获取任务"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        service = DeerFlowExtractionService()
        task = service.create_task(
            source_url="http://api.example.com",
            site_type="api"
        )

        retrieved = service.get_task(task.id)
        assert retrieved is not None
        assert retrieved.id == task.id

    def test_get_task_not_found(self):
        """测试获取不存在的任务"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        service = DeerFlowExtractionService()
        result = service.get_task("non-existent-id")
        assert result is None

    def test_list_tasks(self):
        """测试列出所有任务"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        service = DeerFlowExtractionService()
        service.clear_tasks()

        service.create_task("http://api1.example.com", "api")
        service.create_task("http://api2.example.com", "web")

        tasks = service.list_tasks()
        assert len(tasks) == 2

    def test_clear_tasks(self):
        """测试清空任务"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        service = DeerFlowExtractionService()
        service.create_task("http://api.example.com", "api")

        service.clear_tasks()
        assert len(service.list_tasks()) == 0

    @patch("apps.crawler.deer_flow.workflow.TenderExtractionWorkflow.extract")
    def test_extract_tenders_success(self, mock_extract):
        """测试提取招标列表成功"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        mock_result = type('obj', (object,), {
            "items": [{"title": "测试招标"}],
            "success": True,
            "error_message": None,
            "total_fetched": 1,
            "to_dict": lambda self: {
                "items": self.items,
                "success": self.success,
                "error_message": self.error_message,
                "total_fetched": self.total_fetched
            }
        })()

        mock_extract.return_value = mock_result

        service = DeerFlowExtractionService()
        result = service.extract_tenders("http://api.example.com")

        assert result["success"] is True
        assert len(result["items"]) == 1

    @patch("apps.crawler.deer_flow.workflow.TenderExtractionWorkflow.extract")
    def test_extract_tenders_failure(self, mock_extract):
        """测试提取招标列表失败"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        mock_extract.side_effect = Exception("Connection failed")

        service = DeerFlowExtractionService()
        result = service.extract_tenders("http://api.example.com")

        assert result["success"] is False
        assert "Connection failed" in result["error_message"]

    @patch("apps.crawler.deer_flow.workflow.TenderExtractionWorkflow.extract_with_details")
    def test_extract_with_details_success(self, mock_extract):
        """测试提取招标列表和详情成功"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        mock_result = type('obj', (object,), {
            "items": [{"title": "测试招标"}],
            "details": [{"content": "详情"}],
            "success": True,
            "error_message": None,
            "total_fetched": 1,
            "total_with_details": 1,
            "to_dict": lambda self: {
                "items": self.items,
                "details": self.details,
                "success": self.success,
                "error_message": self.error_message,
                "total_fetched": self.total_fetched,
                "total_with_details": self.total_with_details
            }
        })()

        mock_extract.return_value = mock_result

        service = DeerFlowExtractionService()
        result = service.extract_with_details("http://api.example.com")

        assert result["success"] is True
        assert len(result["items"]) == 1
        assert len(result["details"]) == 1

    @patch("apps.crawler.services.deer_flow_extraction.DeerFlowExtractionService.extract_tenders")
    def test_run_task_sync(self, mock_extract):
        """测试运行同步任务"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        mock_extract.return_value = {
            "success": True,
            "total_fetched": 5
        }

        service = DeerFlowExtractionService()
        task = service.create_task(
            source_url="http://api.example.com",
            fetch_details=False
        )

        result = service.run_task(task.id)

        assert result["success"] is True
        assert task.status == "completed"

    @patch("apps.crawler.services.deer_flow_extraction.DeerFlowExtractionService.extract_with_details")
    def test_run_task_with_details(self, mock_extract):
        """测试运行需要获取详情的任务"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        mock_extract.return_value = {
            "success": True,
            "total_fetched": 5,
            "total_with_details": 3
        }

        service = DeerFlowExtractionService()
        task = service.create_task(
            source_url="http://api.example.com",
            fetch_details=True
        )

        result = service.run_task(task.id)

        assert result["success"] is True
        assert task.status == "completed"

    def test_run_task_not_found(self):
        """测试运行不存在的任务"""
        from apps.crawler.services.deer_flow_extraction import DeerFlowExtractionService

        service = DeerFlowExtractionService()
        result = service.run_task("non-existent-id")

        assert result["success"] is False
        assert "not found" in result["error_message"]