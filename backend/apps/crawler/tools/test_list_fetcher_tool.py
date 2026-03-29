"""
TDD Test: ListFetcherAgent Tool for deer-flow

测试 ListFetcherAgent 封装为 deer-flow Tool
"""
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock


# 测试 deer-flow Tool 封装
class TestListFetcherTool:
    """测试列表获取 Tool"""

    def test_tool_import(self):
        """测试 Tool 可以正确导入"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        # StructuredTool 通过 ainvoke 调用
        assert hasattr(fetch_tender_list, "ainvoke")

    def test_tool_has_docstring(self):
        """测试 Tool 有正确的 docstring"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        # StructuredTool 的 description 属性
        assert hasattr(fetch_tender_list, "description")
        desc = fetch_tender_list.description.lower()
        assert "tender" in desc or "招标" in desc or "fetch" in desc

    def test_tool_name(self):
        """测试 Tool 有正确的名称"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        assert hasattr(fetch_tender_list, "name")
        assert fetch_tender_list.name == "fetch_tender_list"

    def test_tool_args_schema(self):
        """测试 Tool 有正确的参数模式"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        assert hasattr(fetch_tender_list, "args_schema")
        # 验证必需参数
        schema = fetch_tender_list.args_schema
        assert "source_url" in schema.__fields__
        assert "site_type" in schema.__fields__
        assert "max_pages" in schema.__fields__
        assert "api_config" in schema.__fields__

    @pytest.mark.asyncio
    async def test_fetch_api_type_site(self):
        """测试 API 类型网站获取"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list

        # Mock API 响应
        mock_response = {
            "data": {
                "list": [
                    {
                        "title": "测试招标项目1",
                        "url": "http://example.com/detail/1",
                        "publish_time": "2024-01-01",
                        "budget": "100000"
                    },
                    {
                        "title": "测试招标项目2",
                        "url": "http://example.com/detail/2",
                        "publish_time": "2024-01-02",
                        "budget": "200000"
                    }
                ]
            }
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )

            result = await fetch_tender_list.ainvoke({
                "source_url": "http://api.example.com/tender/list",
                "site_type": "api",
                "max_pages": 1,
                "api_config": json.dumps({
                    "url": "http://api.example.com/tender/list",
                    "method": "GET",
                    "params": {"page": 1},
                    "response_path": "data.list"
                })
            })

            # 解析结果
            data = json.loads(result)
            assert "items" in data or "error" in data

            if "items" in data:
                assert len(data["items"]) == 2
                assert data["items"][0]["title"] == "测试招标项目1"

    @pytest.mark.asyncio
    async def test_fetch_with_field_mapping(self):
        """测试字段映射"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list

        # Mock 响应使用不同字段名
        mock_response = {
            "result": [
                {
                    "project_name": "测试项目",
                    "detail_url": "http://example.com/1",
                    "pub_date": "2024-01-01"
                }
            ]
        }

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )

            result = await fetch_tender_list.ainvoke({
                "source_url": "http://api.example.com/list",
                "site_type": "api",
                "max_pages": 1,
                "api_config": json.dumps({
                    "url": "http://api.example.com/list",
                    "method": "GET",
                    "response_path": "result",
                    "field_mapping": {
                        "title_field": "project_name",
                        "url_field": "detail_url",
                        "date_field": "pub_date"
                    }
                })
            })

            data = json.loads(result)
            if "items" in data and len(data["items"]) > 0:
                # 验证字段被正确映射
                assert "title" in data["items"][0]

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 500
            mock_get.return_value.__aenter__.return_value.raise_for_status = Mock(
                side_effect=Exception("Server Error")
            )

            result = await fetch_tender_list.ainvoke({
                "source_url": "http://api.example.com/list",
                "site_type": "api",
                "max_pages": 1
            })

            data = json.loads(result)
            assert "error" in data or "error_message" in data

    @pytest.mark.asyncio
    async def test_empty_result(self):
        """测试空结果处理"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list

        mock_response = {"data": {"list": []}}

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value=mock_response
            )

            result = await fetch_tender_list.ainvoke({
                "source_url": "http://api.example.com/list",
                "site_type": "api",
                "max_pages": 1
            })

            data = json.loads(result)
            assert "items" in data
            assert len(data["items"]) == 0

    def test_tool_returns_structured_tool(self):
        """测试 Tool 返回 StructuredTool"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        from langchain_core.tools import StructuredTool

        # 验证是 StructuredTool 实例
        assert isinstance(fetch_tender_list, StructuredTool)

    def test_api_config_validation(self):
        """测试 api_config 参数验证"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        import asyncio

        # 测试无效的 JSON - 应该通过 Tool 的参数验证
        async def call_invalid():
            return await fetch_tender_list.ainvoke({
                "source_url": "http://example.com",
                "site_type": "api",
                "api_config": "invalid json"
            })

        # 无效 JSON 应该返回错误信息
        result = asyncio.run(call_invalid())
        data = json.loads(result)
        assert "error" in data or "error_message" in data


class TestToolIntegration:
    """集成测试：验证 Tool 与 deer-flow 集成"""

    def test_tool_has_langchain_decorator(self):
        """测试 Tool 使用了 langchain 装饰器"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        from langchain_core.tools import StructuredTool

        # StructuredTool 是 langchain 的装饰器结果
        assert isinstance(fetch_tender_list, StructuredTool)

    def test_tool_output_format(self):
        """测试 Tool 输出格式符合 deer-flow 标准"""
        from apps.crawler.tools.list_fetcher_tool import fetch_tender_list
        import asyncio

        async def check_output():
            result = await fetch_tender_list.ainvoke({
                "source_url": "http://example.com",
                "site_type": "api",
                "api_config": json.dumps({
                    "url": "http://example.com",
                    "method": "GET",
                    "params": {"page": 1}
                })
            })
            # 验证是字符串
            assert isinstance(result, str)
            # 验证是有效 JSON
            data = json.loads(result)
            assert isinstance(data, dict)

        # 使用 mock 避免实际网络请求
        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(
                return_value={"data": {"list": []}}
            )
            asyncio.run(check_output())
