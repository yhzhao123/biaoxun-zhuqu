"""
DetailFetcherTool 测试

TDD 循环 4: 测试详情页爬取工具
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from apps.crawler.tools.detail_fetcher_tool import (
    DetailFetcherTool,
    DetailFetchResult,
    detail_fetch_tool,
)
from apps.crawler.agents.schema import DetailResult, Attachment


class TestDetailFetchResult:
    """DetailFetchResult 测试"""

    def test_default_values(self):
        """测试默认值"""
        result = DetailFetchResult(
            url="http://example.com",
            html="<html></html>",
            success=True,
        )

        assert result.url == "http://example.com"
        assert result.html == "<html></html>"
        assert result.success is True
        assert result.attachments == []
        assert result.main_pdf_content is None
        assert result.error_message is None
        assert result.content_type == "html"

    def test_to_dict(self):
        """测试转换为字典"""
        result = DetailFetchResult(
            url="http://example.com",
            html="<html>content</html>" * 100,  # 长HTML
            success=True,
            attachments=[Mock(spec=Attachment, type='pdf')],
            main_pdf_content="PDF content",
            main_pdf_url="http://example.com/doc.pdf",
            content_type="pdf",
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["url"] == "http://example.com"
        assert result_dict["success"] is True
        assert result_dict["attachments_count"] == 1
        assert result_dict["has_pdf_content"] is True
        assert result_dict["main_pdf_url"] == "http://example.com/doc.pdf"
        assert result_dict["content_type"] == "pdf"
        # HTML应该被截断
        assert len(result_dict["html"]) <= 1000

    def test_get_full_text_with_pdf(self):
        """测试获取完整文本 - 有 PDF"""
        result = DetailFetchResult(
            url="http://example.com",
            html="<html>HTML content</html>",
            success=True,
            main_pdf_content="PDF extracted content",
        )

        # 优先返回 PDF 内容
        assert result.get_full_text() == "PDF extracted content"

    def test_get_full_text_without_pdf(self):
        """测试获取完整文本 - 无 PDF"""
        result = DetailFetchResult(
            url="http://example.com",
            html="<html>HTML content</html>",
            success=True,
        )

        # 返回 HTML 内容
        assert result.get_full_text() == "<html>HTML content</html>"

    def test_has_attachments(self):
        """测试检查附件"""
        # 无附件
        result_no_attachments = DetailFetchResult(
            url="http://example.com",
            html="<html></html>",
            success=True,
        )
        assert result_no_attachments.has_attachments() is False

        # 有附件
        result_with_attachments = DetailFetchResult(
            url="http://example.com",
            html="<html></html>",
            success=True,
            attachments=[Mock(spec=Attachment)],
        )
        assert result_with_attachments.has_attachments() is True

    def test_get_pdf_attachments(self):
        """测试获取 PDF 附件"""
        attachments = [
            Mock(spec=Attachment, type='pdf'),
            Mock(spec=Attachment, type='doc'),
            Mock(spec=Attachment, type='pdf'),
        ]

        result = DetailFetchResult(
            url="http://example.com",
            html="<html></html>",
            success=True,
            attachments=attachments,
        )

        pdf_attachments = result.get_pdf_attachments()
        assert len(pdf_attachments) == 2


class TestDetailFetcherTool:
    """DetailFetcherTool 测试"""

    def test_initialization(self):
        """测试初始化"""
        tool = DetailFetcherTool()

        assert tool.agent is not None
        assert tool.config is not None

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """测试成功爬取"""
        mock_detail_result = DetailResult(
            url="http://example.com/detail/1",
            html="<html>Detail content</html>",
            attachments=[],
            list_data={"title": "Test"},
        )

        list_item = {"url": "http://example.com/detail/1", "title": "Test"}

        tool = DetailFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=mock_detail_result
        ) as mock_fetch:
            result = await tool.fetch(list_item)

            assert result.success is True
            assert result.url == "http://example.com/detail/1"
            assert result.html == "<html>Detail content</html>"
            assert result.error_message is None

            mock_fetch.assert_called_once_with(list_item)

    @pytest.mark.asyncio
    async def test_fetch_success_with_pdf(self):
        """测试成功爬取（含 PDF）"""
        mock_detail_result = DetailResult(
            url="http://example.com/detail/1",
            html="<html>Detail content</html>",
            attachments=[],
            list_data={"title": "Test"},
            main_pdf_content="PDF extracted text content",
            main_pdf_url="http://example.com/doc.pdf",
            main_pdf_filename="document.pdf",
        )

        list_item = {"url": "http://example.com/detail/1", "title": "Test"}

        tool = DetailFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=mock_detail_result
        ):
            result = await tool.fetch(list_item, extract_pdf=True)

            assert result.success is True
            assert result.main_pdf_content == "PDF extracted text content"
            assert result.main_pdf_url == "http://example.com/doc.pdf"
            assert result.main_pdf_filename == "document.pdf"
            assert result.content_type == "pdf"

    @pytest.mark.asyncio
    async def test_fetch_skip_pdf(self):
        """测试跳过 PDF 提取"""
        mock_detail_result = DetailResult(
            url="http://example.com/detail/1",
            html="<html>Detail content</html>",
            attachments=[],
            list_data={"title": "Test"},
            main_pdf_content="PDF content",  # Agent 返回了 PDF
        )

        list_item = {"url": "http://example.com/detail/1", "title": "Test"}

        tool = DetailFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=mock_detail_result
        ):
            result = await tool.fetch(list_item, extract_pdf=False)

            # 即使 Agent 返回了 PDF，也应该是 None（因为我们设置了 extract_pdf=False）
            assert result.main_pdf_content is None

    @pytest.mark.asyncio
    async def test_fetch_failure(self):
        """测试爬取失败"""
        list_item = {"url": "http://example.com/detail/1", "title": "Test"}

        tool = DetailFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, side_effect=Exception("Network error")
        ):
            result = await tool.fetch(list_item)

            assert result.success is False
            assert result.html == ""
            assert "Network error" in result.error_message

    @pytest.mark.asyncio
    async def test_fetch_no_url(self):
        """测试缺少 URL"""
        list_item = {"title": "Test"}  # 缺少 url

        tool = DetailFetcherTool()
        result = await tool.fetch(list_item)

        assert result.success is False
        assert "No URL provided" in result.error_message

    @pytest.mark.asyncio
    async def test_fetch_empty_result(self):
        """测试空结果"""
        list_item = {"url": "http://example.com/detail/1", "title": "Test"}

        tool = DetailFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=None
        ):
            result = await tool.fetch(list_item)

            assert result.success is False
            assert "Failed to fetch" in result.error_message

    @pytest.mark.asyncio
    async def test_fetch_with_retry_success_on_first(self):
        """测试重试 - 第一次成功"""
        mock_detail_result = DetailResult(
            url="http://example.com/detail/1",
            html="<html>Content</html>",
            attachments=[],
            list_data={},
        )

        list_item = {"url": "http://example.com/detail/1"}

        tool = DetailFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=mock_detail_result
        ) as mock_fetch:
            result = await tool.fetch_with_retry(list_item, max_retries=3)

            assert result.success is True
            assert mock_fetch.call_count == 1

    @pytest.mark.asyncio
    async def test_fetch_with_retry_success_on_second(self):
        """测试重试 - 第二次成功"""
        mock_detail_result = DetailResult(
            url="http://example.com/detail/1",
            html="<html>Content</html>",
            attachments=[],
            list_data={},
        )

        list_item = {"url": "http://example.com/detail/1"}

        tool = DetailFetcherTool()

        with patch.object(
            tool.agent,
            "fetch",
            new_callable=AsyncMock,
            side_effect=[Exception("First fail"), mock_detail_result]
        ) as mock_fetch:
            result = await tool.fetch_with_retry(list_item, max_retries=3)

            assert result.success is True
            assert mock_fetch.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_with_retry_all_failed(self):
        """测试重试 - 全部失败"""
        list_item = {"url": "http://example.com/detail/1"}

        tool = DetailFetcherTool()

        with patch.object(
            tool.agent,
            "fetch",
            new_callable=AsyncMock,
            side_effect=Exception("Always fails")
        ):
            result = await tool.fetch_with_retry(list_item, max_retries=3)

            assert result.success is False
            assert "Failed after 3 attempts" in result.error_message

    def test_validate_list_item_valid(self):
        """测试有效列表项验证"""
        tool = DetailFetcherTool()

        valid_item = {
            "url": "http://example.com/detail/1",
            "title": "Test",
        }

        assert tool.validate_list_item(valid_item) is True

    def test_validate_list_item_no_url(self):
        """测试缺少 URL"""
        tool = DetailFetcherTool()

        invalid_item = {"title": "Test"}  # 缺少 url

        assert tool.validate_list_item(invalid_item) is False

    def test_validate_list_item_empty_url(self):
        """测试空 URL"""
        tool = DetailFetcherTool()

        invalid_item = {"url": "", "title": "Test"}

        assert tool.validate_list_item(invalid_item) is False

    def test_validate_list_item_invalid_url_format(self):
        """测试无效 URL 格式"""
        tool = DetailFetcherTool()

        invalid_item = {"url": "not-a-url", "title": "Test"}

        assert tool.validate_list_item(invalid_item) is False

    def test_validate_list_item_not_dict(self):
        """测试非字典类型"""
        tool = DetailFetcherTool()

        assert tool.validate_list_item("not a dict") is False
        assert tool.validate_list_item(None) is False
        assert tool.validate_list_item([1, 2, 3]) is False

    @pytest.mark.asyncio
    async def test_fetch_batch(self):
        """测试批量爬取"""
        list_items = [
            {"url": "http://example.com/1", "title": "Test 1"},
            {"url": "http://example.com/2", "title": "Test 2"},
            {"url": "http://example.com/3", "title": "Test 3"},
        ]

        async def mock_fetch(item, extract_pdf=True):
            return DetailFetchResult(
                url=item["url"],
                html=f"<html>Content for {item['title']}</html>",
                success=True,
            )

        tool = DetailFetcherTool()

        with patch.object(tool, "fetch", side_effect=mock_fetch):
            results = await tool.fetch_batch(list_items, max_concurrent=2)

            assert len(results) == 3
            assert all(r.success for r in results)
            assert results[0].url == "http://example.com/1"
            assert results[1].url == "http://example.com/2"
            assert results[2].url == "http://example.com/3"


class TestDetailFetchToolFunction:
    """detail_fetch_tool 函数测试"""

    @pytest.mark.asyncio
    async def test_tool_function(self):
        """测试工具函数"""
        with patch(
            "apps.crawler.tools.detail_fetcher_tool.DetailFetcherTool.fetch",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = DetailFetchResult(
                url="http://example.com/detail/1",
                html="<html>Content</html>",
                success=True,
            )

            result = await detail_fetch_tool(
                url="http://example.com/detail/1",
                title="Test",
                extract_pdf=True,
            )

            assert isinstance(result, dict)
            assert result["success"] is True
            assert result["url"] == "http://example.com/detail/1"


class TestDetailFetcherToolIntegration:
    """DetailFetcherTool 集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整流程"""
        # 创建模拟数据
        mock_detail_result = DetailResult(
            url="http://example.com/tender/1",
            html="<html>招标公告内容</html>",
            attachments=[
                Mock(spec=Attachment, type='pdf', url='http://example.com/attach.pdf'),
            ],
            list_data={"title": "招标公告", "publish_date": "2024-01-01"},
            main_pdf_content="PDF 正文内容",
            main_pdf_url="http://example.com/main.pdf",
        )

        list_item = {
            "url": "http://example.com/tender/1",
            "title": "招标公告",
            "publish_date": "2024-01-01",
        }

        tool = DetailFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=mock_detail_result
        ):
            # 验证列表项
            assert tool.validate_list_item(list_item) is True

            # 执行爬取
            result = await tool.fetch(list_item, extract_pdf=True)

            # 验证结果
            assert result.success is True
            assert result.url == "http://example.com/tender/1"
            assert result.main_pdf_content == "PDF 正文内容"
            assert result.has_attachments() is True
            assert len(result.get_pdf_attachments()) == 1

            # 获取完整文本
            full_text = result.get_full_text()
            assert full_text == "PDF 正文内容"  # 优先返回 PDF

            # 验证结果可序列化
            result_dict = result.to_dict()
            assert "url" in result_dict
            assert "has_pdf_content" in result_dict
            assert result_dict["has_pdf_content"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
