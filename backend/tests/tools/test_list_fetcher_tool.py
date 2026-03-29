"""
ListFetcherTool 测试

TDD 循环 2: 测试列表爬取工具
"""
import json
import os
import sys

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '../..')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from apps.crawler.tools.list_fetcher_tool import (
    ListFetcherTool,
    ListFetchResult,
    fetch_tender_list,
)
from apps.crawler.agents.schema import ExtractionStrategy


class TestListFetchResult:
    """ListFetchResult 测试"""

    def test_default_values(self):
        """测试默认值"""
        result = ListFetchResult(
            items=[],
            total_count=0,
            pages_fetched=0,
            source_name="test",
            success=True,
        )

        assert result.items == []
        assert result.total_count == 0
        assert result.success is True
        assert result.error_message is None
        assert result.cache_hit is False

    def test_to_dict(self):
        """测试转换为字典"""
        result = ListFetchResult(
            items=[{"title": "Test"}],
            total_count=1,
            pages_fetched=1,
            source_name="test_source",
            success=True,
            cache_hit=True,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["total_count"] == 1
        assert result_dict["source_name"] == "test_source"
        assert result_dict["success"] is True
        assert result_dict["cache_hit"] is True


class TestListFetcherTool:
    """ListFetcherTool 测试"""

    def test_initialization(self):
        """测试初始化"""
        tool = ListFetcherTool()

        assert tool.agent is not None
        assert hasattr(tool, 'logger')

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """测试成功爬取"""
        # Mock agent.fetch 返回值
        mock_items = [
            {"title": "招标公告1", "url": "http://example.com/1"},
            {"title": "招标公告2", "url": "http://example.com/2"},
        ]

        strategy = Mock(spec=ExtractionStrategy)
        strategy.source_name = "test_source"
        strategy.max_pages = 5
        strategy.pagination = {"items_per_page": 10}

        tool = ListFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=mock_items
        ) as mock_fetch:
            result = await tool.fetch(strategy, max_pages=3)

            assert result.success is True
            assert result.total_count == 2
            assert len(result.items) == 2
            assert result.source_name == "test_source"
            assert result.error_message is None

            # 验证 agent.fetch 被调用
            mock_fetch.assert_called_once_with(strategy)
            # 验证页数被修改
            assert strategy.max_pages == 3

    @pytest.mark.asyncio
    async def test_fetch_failure(self):
        """测试爬取失败"""
        strategy = Mock(spec=ExtractionStrategy)
        strategy.source_name = "test_source"
        strategy.max_pages = 5

        tool = ListFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, side_effect=Exception("Network error")
        ) as mock_fetch:
            result = await tool.fetch(strategy)

            assert result.success is False
            assert result.total_count == 0
            assert result.items == []
            assert "Network error" in result.error_message

    @pytest.mark.asyncio
    async def test_fetch_empty_result(self):
        """测试空结果"""
        strategy = Mock(spec=ExtractionStrategy)
        strategy.source_name = "test_source"
        strategy.max_pages = 5
        strategy.pagination = {"items_per_page": 10}

        tool = ListFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=[]
        ):
            result = await tool.fetch(strategy)

            assert result.success is True
            assert result.total_count == 0
            assert result.pages_fetched == 0

    def test_estimate_pages_fetched(self):
        """测试页数估算"""
        tool = ListFetcherTool()

        strategy = Mock(spec=ExtractionStrategy)
        strategy.pagination = {"items_per_page": 10}

        # 测试不同数量的 items
        assert tool._estimate_pages_fetched([], strategy) == 0
        assert tool._estimate_pages_fetched([{}] * 5, strategy) == 1
        assert tool._estimate_pages_fetched([{}] * 10, strategy) == 1
        assert tool._estimate_pages_fetched([{}] * 15, strategy) == 2
        assert tool._estimate_pages_fetched([{}] * 100, strategy) == 10

    def test_fetch_single_page_removed(self):
        """测试单页爬取功能已移除（deer-flow Tool 简化）"""
        # deer-flow Tool 版本已简化，fetch_single_page 方法已移除
        # 使用 fetch 方法并设置 max_pages=1 替代
        tool = ListFetcherTool()
        assert not hasattr(tool, 'fetch_single_page')

    def test_validate_strategy_removed(self):
        """测试策略验证已移除（deer-flow Tool 简化）"""
        # deer-flow Tool 版本已简化，validate_strategy 方法已移除
        tool = ListFetcherTool()
        assert not hasattr(tool, 'validate_strategy')


class TestListFetchToolFunction:
    """fetch_tender_list 函数测试"""

    @pytest.mark.asyncio
    async def test_tool_function(self):
        """测试工具函数"""
        with patch(
            "apps.crawler.tools.list_fetcher_tool.ListFetcherTool.fetch",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = ListFetchResult(
                items=[{"title": "Test"}],
                total_count=1,
                pages_fetched=1,
                source_name="test",
                success=True,
            )

            # 使用 fetch_tender_list.ainvoke (deer-flow Tool 装饰器版本)
            # StructuredTool 需要使用 ainvoke 而不是直接调用
            result = await fetch_tender_list.ainvoke({
                "source_url": "http://api.example.com",
                "site_type": "api",
                "max_pages": 3,
                "api_config": '{"url": "http://api.example.com"}',
            })

            # 结果应为 JSON 字符串
            assert isinstance(result, str)
            result_dict = json.loads(result)
            assert result_dict["success"] is True
            assert result_dict["total_count"] == 1


class TestListFetcherToolIntegration:
    """ListFetcherTool 集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整流程"""
        # 创建模拟数据
        mock_items = [
            {
                "title": "政府采购项目",
                "url": "http://example.com/tender/1",
                "publish_date": "2024-01-01",
            },
            {
                "title": "招标公告",
                "url": "http://example.com/tender/2",
                "publish_date": "2024-01-02",
            },
        ]

        strategy = Mock(spec=ExtractionStrategy)
        strategy.source_name = "集成测试源"
        strategy.max_pages = 5
        strategy.pagination = {"items_per_page": 10}

        tool = ListFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=mock_items
        ):
            # 执行爬取
            result = await tool.fetch(strategy)

            # 验证结果
            assert result.success is True
            assert result.total_count == 2
            assert result.source_name == "集成测试源"

            # 验证数据完整性
            assert len(result.items) == 2
            assert result.items[0]["title"] == "政府采购项目"
            assert result.items[1]["title"] == "招标公告"

            # 验证结果可序列化
            result_dict = result.to_dict()
            assert "items" in result_dict
            assert "total_count" in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
