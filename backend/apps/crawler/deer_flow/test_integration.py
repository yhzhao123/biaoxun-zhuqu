"""
Integration Test: Tools Integration with deer-flow

测试 Tools 在 deer-flow 环境中的集成
验证 Tools 可以被 deer-flow Agent 正确调用
"""
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestToolsIntegration:
    """测试 Tools 集成"""

    def test_list_fetcher_tool_is_structured_tool(self):
        """验证 ListFetcherTool 是 StructuredTool 实例"""
        from langchain_core.tools import StructuredTool
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list

        assert isinstance(fetch_tender_list, StructuredTool)
        assert fetch_tender_list.name == "fetch_tender_list"

    def test_detail_fetcher_tool_is_structured_tool(self):
        """验证 DetailFetcherTool 是 StructuredTool 实例"""
        from langchain_core.tools import StructuredTool
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

        assert isinstance(fetch_tender_detail, StructuredTool)
        assert fetch_tender_detail.name == "fetch_tender_detail"

    def test_tools_have_required_attributes(self):
        """验证 Tools 有 deer-flow 必需的属性"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

        for tool in [fetch_tender_list, fetch_tender_detail]:
            assert hasattr(tool, "name")
            assert hasattr(tool, "description")
            assert hasattr(tool, "args_schema")
            assert tool.name
            assert tool.description

    def test_tool_args_schema_is_valid(self):
        """验证 Tool 参数模式有效"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

        # ListFetcherTool 参数
        list_schema = fetch_tender_list.args_schema
        assert "source_url" in list_schema.model_fields
        assert "site_type" in list_schema.model_fields
        assert "max_pages" in list_schema.model_fields
        assert "api_config" in list_schema.model_fields

        # DetailFetcherTool 参数
        detail_schema = fetch_tender_detail.args_schema
        assert "url" in detail_schema.model_fields
        assert "title" in detail_schema.model_fields
        assert "extract_pdf" in detail_schema.model_fields


class TestToolsInWorkflowContext:
    """测试 Tools 在 Workflow 上下文中的使用"""

    @pytest.mark.asyncio
    async def test_tools_called_by_workflow(self):
        """验证 Workflow 正确调用 Tools"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        from apps.crawler.tools.list_fetcher_tool import ListFetchResult

        mock_result = ListFetchResult(
            items=[{"title": "测试", "url": "http://example.com/1"}],
            total_count=1,
            pages_fetched=1,
            source_name="test",
            success=True
        )

        with patch("apps.crawler.deer_flow.workflow.ListFetcherTool.fetch") as mock_fetch:
            mock_fetch.return_value = mock_result

            workflow = TenderExtractionWorkflow()
            result = await workflow.extract(
                source_url="http://api.example.com/list",
                site_type="api"
            )

            assert result.success
            assert len(result.items) == 1
            assert mock_fetch.called

    @pytest.mark.asyncio
    async def test_tools_error_propagation(self):
        """验证 Tool 错误正确传播到 Workflow"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        from apps.crawler.tools.list_fetcher_tool import ListFetchResult

        mock_result = ListFetchResult(
            items=[],
            total_count=0,
            pages_fetched=0,
            source_name="test",
            success=False,
            error_message="Connection failed"
        )

        with patch("apps.crawler.deer_flow.workflow.ListFetcherTool.fetch") as mock_fetch:
            mock_fetch.return_value = mock_result

            workflow = TenderExtractionWorkflow()
            result = await workflow.extract(
                source_url="http://api.example.com/list",
                site_type="api"
            )

            assert not result.success
            assert "Connection failed" in result.error_message


class TestToolsOutputFormat:
    """测试 Tools 输出格式"""

    @pytest.mark.asyncio
    async def test_list_fetcher_returns_json(self):
        """验证 ListFetcherTool 返回有效 JSON"""
        from apps.crawler.tools.list_fetcher_tool import ListFetcherTool
        from apps.crawler.agents.schema import ExtractionStrategy

        mock_response = {
            "data": {
                "list": [
                    {"title": "项目1", "url": "http://example.com/1"}
                ]
            }
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )

            tool = ListFetcherTool()
            strategy = ExtractionStrategy(
                source_name="test",
                site_type="api",
                api_config={
                    "url": "http://api.example.com/list",
                    "response_path": "data.list"
                }
            )

            result = await tool.fetch(strategy)
            data = result.to_dict()

            assert isinstance(data, dict)
            assert "items" in data
            assert "success" in data

    @pytest.mark.asyncio
    async def test_detail_fetcher_returns_json(self):
        """验证 DetailFetcherTool 返回有效 JSON"""
        from apps.crawler.tools.detail_fetcher_tool import DetailFetcherTool

        mock_html = "<html><body>Test Content</body></html>"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.headers = {
                "Content-Type": "text/html"
            }
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_html
            )

            tool = DetailFetcherTool()
            result = await tool.fetch(
                list_item={"url": "http://example.com/1", "title": "Test"}
            )
            data = result.to_dict()

            assert isinstance(data, dict)
            assert "url" in data
            assert "success" in data


class TestToolsCompatibility:
    """测试 Tools 兼容性"""

    def test_tools_compatible_with_deer_flow_agent(self):
        """验证 Tools 兼容 deer-flow Agent 调用方式"""
        from langchain_core.tools import StructuredTool
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

        # 验证可以添加到工具列表
        tools = [fetch_tender_list, fetch_tender_detail]

        for tool in tools:
            # 验证是 StructuredTool 类型
            assert isinstance(tool, StructuredTool)
            # 验证有必需的方法
            assert callable(tool._run) or callable(tool._arun)
            # 验证参数模式可序列化
            schema = tool.args_schema
            assert schema is not None

    def test_tool_descriptions_for_agent(self):
        """验证 Tool 描述适合 Agent 理解"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

        for tool in [fetch_tender_list, fetch_tender_detail]:
            desc = tool.description
            assert len(desc) > 50  # 描述应该足够详细
            assert "fetch" in desc.lower() or "提取" in desc or "获取" in desc


class TestEndToEndIntegration:
    """端到端集成测试"""

    @pytest.mark.asyncio
    async def test_full_extraction_pipeline(self):
        """测试完整提取管道"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow
        from apps.crawler.tools.list_fetcher_tool import ListFetchResult
        from apps.crawler.tools.detail_fetcher_tool import DetailFetchResult

        # Mock 列表获取
        list_result = ListFetchResult(
            items=[
                {"title": "招标公告1", "url": "http://example.com/1"},
                {"title": "招标公告2", "url": "http://example.com/2"}
            ],
            total_count=2,
            pages_fetched=1,
            source_name="test",
            success=True
        )

        # Mock 详情获取
        detail_result = DetailFetchResult(
            url="http://example.com/1",
            html="<html>详情内容</html>",
            success=True
        )

        with patch("apps.crawler.deer_flow.workflow.ListFetcherTool.fetch") as mock_list, \
             patch("apps.crawler.deer_flow.workflow.DetailFetcherTool.fetch") as mock_detail:

            mock_list.return_value = list_result
            mock_detail.return_value = detail_result

            workflow = TenderExtractionWorkflow()
            result = await workflow.extract_with_details(
                source_url="http://api.example.com/list",
                site_type="api",
                max_items=2,
                concurrent_limit=2
            )

            assert result.success
            assert result.total_fetched == 2
            assert len(result.details) == 2
            assert mock_list.called
            assert mock_detail.call_count == 2

    def test_metrics_collection(self):
        """测试指标收集"""
        from apps.crawler.deer_flow.workflow import TenderExtractionWorkflow

        workflow = TenderExtractionWorkflow()

        # 验证初始指标
        metrics = workflow.get_metrics()
        assert metrics["list_calls"] == 0
        assert metrics["detail_calls"] == 0
        assert metrics["errors"] == 0

        # 验证重置功能
        workflow.reset_metrics()
        metrics = workflow.get_metrics()
        assert metrics["items_fetched"] == 0
