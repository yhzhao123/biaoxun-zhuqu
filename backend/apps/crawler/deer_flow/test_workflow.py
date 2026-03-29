"""
TDD Test: Tender Extraction Workflow for deer-flow

测试招标信息提取 Workflow 编排
"""
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestTenderExtractionWorkflow:
    """测试招标信息提取 Workflow"""

    def test_workflow_import(self):
        """测试 Workflow 可以正确导入"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        assert TenderExtractionWorkflow is not None

    def test_workflow_initialization(self):
        """测试 Workflow 初始化"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()
        assert workflow is not None
        assert hasattr(workflow, "extract")

    @pytest.mark.asyncio
    async def test_extract_single_source(self):
        """测试从单一源提取招标信息"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        from apps.crawler.tools.list_fetcher_tool import ListFetchResult

        # Mock ListFetcherTool.fetch
        mock_result = ListFetchResult(
            items=[
                {
                    "title": "测试招标项目1",
                    "url": "http://example.com/detail/1",
                    "publish_date": "2024-01-01"
                }
            ],
            total_count=1,
            pages_fetched=1,
            source_name="test",
            success=True
        )

        with patch("apps.crawler.tools.list_fetcher_tool.ListFetcherTool.fetch") as mock_fetch:
            mock_fetch.return_value = mock_result

            workflow = TenderExtractionWorkflow()
            result = await workflow.extract(
                source_url="http://api.example.com/list",
                site_type="api",
                max_items=1
            )

            assert result is not None
            assert hasattr(result, "items")
            assert len(result.items) == 1

    @pytest.mark.asyncio
    async def test_extract_with_detail_fetching(self):
        """测试提取并获取详情"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        from apps.crawler.tools.list_fetcher_tool import ListFetchResult
        from apps.crawler.tools.detail_fetcher_tool import DetailFetchResult

        mock_list = ListFetchResult(
            items=[
                {"title": "项目1", "url": "http://example.com/1"},
                {"title": "项目2", "url": "http://example.com/2"}
            ],
            total_count=2,
            pages_fetched=1,
            source_name="test",
            success=True
        )

        mock_detail = DetailFetchResult(
            url="http://example.com/1",
            html="<html>详情内容</html>",
            success=True
        )

        with patch("apps.crawler.tools.list_fetcher_tool.ListFetcherTool.fetch") as mock_list_tool, \
             patch("apps.crawler.tools.detail_fetcher_tool.DetailFetcherTool.fetch") as mock_detail_tool:

            mock_list_tool.return_value = mock_list
            mock_detail_tool.return_value = mock_detail

            workflow = TenderExtractionWorkflow()
            result = await workflow.extract_with_details(
                source_url="http://api.example.com/list",
                site_type="api",
                max_items=2
            )

            assert result is not None
            assert hasattr(result, "details")
            # 验证详情被获取
            assert mock_detail_tool.called

    @pytest.mark.asyncio
    async def test_extract_batch_processing(self):
        """测试批量处理多个源"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        from apps.crawler.tools.list_fetcher_tool import ListFetchResult

        sources = [
            {"url": "http://source1.com/api", "type": "api"},
            {"url": "http://source2.com/api", "type": "api"}
        ]

        mock_result = ListFetchResult(
            items=[{"title": "项目", "url": "http://example.com/1"}],
            total_count=1,
            pages_fetched=1,
            source_name="test",
            success=True
        )

        with patch("apps.crawler.tools.list_fetcher_tool.ListFetcherTool.fetch") as mock_tool:
            mock_tool.return_value = mock_result

            workflow = TenderExtractionWorkflow()
            results = await workflow.extract_batch(sources, max_items_per_source=1)

            assert len(results) == len(sources)

    @pytest.mark.asyncio
    async def test_error_handling_and_continue(self):
        """测试错误处理和继续"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        from apps.crawler.tools.list_fetcher_tool import ListFetchResult
        from apps.crawler.tools.detail_fetcher_tool import DetailFetchResult

        mock_list = ListFetchResult(
            items=[{"title": "项目1", "url": "http://example.com/1"}],
            total_count=1,
            pages_fetched=1,
            source_name="test",
            success=True
        )

        mock_error = DetailFetchResult(
            url="",
            html="",
            success=False,
            error_message="Failed to fetch"
        )

        with patch("apps.crawler.tools.list_fetcher_tool.ListFetcherTool.fetch") as mock_list_tool, \
             patch("apps.crawler.tools.detail_fetcher_tool.DetailFetcherTool.fetch") as mock_detail_tool:

            mock_list_tool.return_value = mock_list
            mock_detail_tool.return_value = mock_error

            workflow = TenderExtractionWorkflow()
            result = await workflow.extract_with_details(
                source_url="http://api.example.com/list",
                site_type="api",
                max_items=1
            )

            # 即使详情获取失败，也应该返回列表结果
            assert result is not None
            assert hasattr(result, "items")

    @pytest.mark.asyncio
    async def test_concurrent_detail_fetching(self):
        """测试并发获取详情"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        from apps.crawler.tools.list_fetcher_tool import ListFetchResult
        from apps.crawler.tools.detail_fetcher_tool import DetailFetchResult

        mock_list = ListFetchResult(
            items=[
                {"title": f"项目{i}", "url": f"http://example.com/{i}"}
                for i in range(5)
            ],
            total_count=5,
            pages_fetched=1,
            source_name="test",
            success=True
        )

        mock_detail = DetailFetchResult(
            url="http://example.com/1",
            html="<html>详情</html>",
            success=True
        )

        with patch("apps.crawler.tools.list_fetcher_tool.ListFetcherTool.fetch") as mock_list_tool, \
             patch("apps.crawler.tools.detail_fetcher_tool.DetailFetcherTool.fetch") as mock_detail_tool:

            mock_list_tool.return_value = mock_list
            mock_detail_tool.return_value = mock_detail

            workflow = TenderExtractionWorkflow()
            result = await workflow.extract_with_details(
                source_url="http://api.example.com/list",
                site_type="api",
                max_items=5,
                concurrent_limit=3
            )

            assert result is not None
            assert hasattr(result, "details")
            # 验证并发调用
            assert mock_detail_tool.call_count == 5

    def test_workflow_configuration(self):
        """测试 Workflow 配置"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow, WorkflowConfig

        config = WorkflowConfig(
            max_concurrent_requests=5,
            max_retries=3,
            request_delay=1.0
        )

        workflow = TenderExtractionWorkflow(config=config)
        assert workflow.config is not None
        assert workflow.config.max_concurrent_requests == 5


class TestWorkflowIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_end_to_end_extraction(self):
        """测试端到端提取流程"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        from apps.crawler.tools.list_fetcher_tool import ListFetchResult
        from apps.crawler.tools.detail_fetcher_tool import DetailFetchResult

        # 模拟完整的提取流程
        mock_list_result = ListFetchResult(
            items=[
                {
                    "title": "办公设备采购招标公告",
                    "url": "http://example.com/tender/123",
                    "publish_date": "2024-01-15",
                    "budget": "500000"
                }
            ],
            total_count=1,
            pages_fetched=1,
            source_name="test",
            success=True
        )

        mock_detail_result = DetailFetchResult(
            url="http://example.com/tender/123",
            html="<html><body>采购人：XX市政府<br>联系人：张三<br>电话：13800138000</body></html>",
            success=True,
            attachments=[]
        )

        with patch("apps.crawler.tools.list_fetcher_tool.ListFetcherTool.fetch") as mock_list, \
             patch("apps.crawler.tools.detail_fetcher_tool.DetailFetcherTool.fetch") as mock_detail:

            mock_list.return_value = mock_list_result
            mock_detail.return_value = mock_detail_result

            workflow = TenderExtractionWorkflow()
            result = await workflow.extract_with_details(
                source_url="http://api.example.com/tender/list",
                site_type="api",
                api_config=json.dumps({
                    "url": "http://api.example.com/tender/list",
                    "method": "GET",
                    "response_path": "data.list"
                }),
                max_items=1
            )

            assert result is not None
            assert hasattr(result, "items")
            assert hasattr(result, "details")

    def test_workflow_metrics(self):
        """测试 Workflow 指标收集"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()
        assert hasattr(workflow, "get_metrics")

        metrics = workflow.get_metrics()
        assert isinstance(metrics, dict)
        assert "list_calls" in metrics
