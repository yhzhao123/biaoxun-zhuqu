"""
TDD Test: DetailFetcherAgent Tool for deer-flow

测试 DetailFetcherAgent 封装为 deer-flow Tool
"""
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock


class TestDetailFetcherTool:
    """测试详情页获取 Tool"""

    def test_tool_import(self):
        """测试 Tool 可以正确导入"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail
        assert hasattr(fetch_tender_detail, "ainvoke")

    def test_tool_has_docstring(self):
        """测试 Tool 有正确的描述"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail
        assert hasattr(fetch_tender_detail, "description")
        desc = fetch_tender_detail.description.lower()
        assert "detail" in desc or "detail" in desc or "page" in desc

    def test_tool_name(self):
        """测试 Tool 有正确的名称"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail
        assert hasattr(fetch_tender_detail, "name")
        assert fetch_tender_detail.name == "fetch_tender_detail"

    def test_tool_args_schema(self):
        """测试 Tool 有正确的参数模式"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail
        assert hasattr(fetch_tender_detail, "args_schema")
        schema = fetch_tender_detail.args_schema
        assert "url" in schema.__fields__
        assert "title" in schema.__fields__
        assert "extract_pdf" in schema.__fields__

    @pytest.mark.asyncio
    async def test_fetch_html_detail(self):
        """测试 HTML 详情页获取"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

        mock_html = """
        <html>
        <body>
            <h1>招标公告标题</h1>
            <div class="content">
                <p>采购人：测试采购单位</p>
                <p>联系人：张三</p>
                <p>联系电话：13800138000</p>
                <p>预算金额：100万元</p>
            </div>
        </body>
        </html>
        """

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.headers = {
                "Content-Type": "text/html"
            }
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value=mock_html
            )

            result = await fetch_tender_detail.ainvoke({
                "url": "http://example.com/detail/1",
                "title": "测试招标公告",
                "extract_pdf": True
            })

            data = json.loads(result)
            assert "success" in data

            if data.get("success"):
                assert "html" in data or "has_pdf_content" in data

    @pytest.mark.asyncio
    async def test_fetch_pdf_detail(self):
        """测试 PDF 详情页获取"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

        # Mock PDF 内容
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n"

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.headers = {
                "Content-Type": "application/pdf"
            }
            mock_get.return_value.__aenter__.return_value.read = AsyncMock(
                return_value=pdf_content
            )

            result = await fetch_tender_detail.ainvoke({
                "url": "http://example.com/detail/1.pdf",
                "title": "测试PDF公告",
                "extract_pdf": True
            })

            data = json.loads(result)
            assert "success" in data

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 404
            mock_get.return_value.__aenter__.return_value.raise_for_status = Mock(
                side_effect=Exception("Not Found")
            )

            result = await fetch_tender_detail.ainvoke({
                "url": "http://example.com/not-found",
                "title": "",
                "extract_pdf": True
            })

            data = json.loads(result)
            assert "error" in data or "error_message" in data

    @pytest.mark.asyncio
    async def test_invalid_url(self):
        """测试无效 URL 处理"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail

        result = await fetch_tender_detail.ainvoke({
            "url": "",
            "title": "",
            "extract_pdf": True
        })

        data = json.loads(result)
        assert "error" in data or "error_message" in data

    def test_tool_returns_structured_tool(self):
        """测试 Tool 返回 StructuredTool"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail
        from langchain_core.tools import StructuredTool

        assert isinstance(fetch_tender_detail, StructuredTool)


class TestToolIntegration:
    """集成测试"""

    def test_tool_has_langchain_decorator(self):
        """测试 Tool 使用了 langchain 装饰器"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail
        from langchain_core.tools import StructuredTool

        assert isinstance(fetch_tender_detail, StructuredTool)

    def test_tool_output_format(self):
        """测试 Tool 输出格式"""
        from apps.crawler.tools.detail_fetcher_tool import fetch_tender_detail
        import asyncio

        async def check_output():
            result = await fetch_tender_detail.ainvoke({
                "url": "http://example.com/detail/1",
                "title": "测试",
                "extract_pdf": False
            })
            assert isinstance(result, str)
            data = json.loads(result)
            assert isinstance(data, dict)

        with patch("aiohttp.ClientSession.get") as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.headers = {
                "Content-Type": "text/html"
            }
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value="<html><body>Test</body></html>"
            )
            asyncio.run(check_output())
