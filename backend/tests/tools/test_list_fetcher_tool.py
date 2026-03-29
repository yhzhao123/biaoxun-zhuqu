"""
ListFetcherTool 测试

TDD 循环 2: 测试列表爬取工具
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from apps.crawler.tools.list_fetcher_tool import (
    ListFetcherTool,
    ListFetchResult,
    list_fetch_tool,
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
        assert tool.config is not None

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

    @pytest.mark.asyncio
    async def test_fetch_single_page(self):
        """测试单页爬取"""
        mock_items = [{"title": "Test"}]

        strategy = Mock(spec=ExtractionStrategy)
        strategy.source_name = "test_source"
        strategy.max_pages = 10  # 原始值
        strategy.pagination = {"items_per_page": 10}

        tool = ListFetcherTool()

        with patch.object(
            tool.agent, "fetch", new_callable=AsyncMock, return_value=mock_items
        ):
            result = await tool.fetch_single_page(strategy, page=2)

            assert result.success is True
            # 验证临时修改了 max_pages
            assert strategy.max_pages == 10  # 恢复原值

    def test_validate_strategy_valid(self):
        """测试有效策略验证"""
        tool = ListFetcherTool()

        strategy = Mock(spec=ExtractionStrategy)
        strategy.source_name = "test"
        strategy.site_type = "api"
        strategy.api_config = {"url": "http://api.example.com"}

        assert tool.validate_strategy(strategy) is True

    def test_validate_strategy_missing_source_name(self):
        """测试缺少 source_name"""
        tool = ListFetcherTool()

        strategy = Mock(spec=ExtractionStrategy)
        strategy.source_name = ""

        assert tool.validate_strategy(strategy) is False

    def test_validate_strategy_api_without_config(self):
        """测试 API 类型缺少配置"""
        tool = ListFetcherTool()

        strategy = Mock(spec=ExtractionStrategy)
        strategy.source_name = "test"
        strategy.site_type = "api"
        strategy.api_config = None

        assert tool.validate_strategy(strategy) is False


class TestListFetchToolFunction:
    """list_fetch_tool 函数测试"""

    @pytest.mark.asyncio
    async def test_tool_function(self):
        """测试工具函数"""
        source_config = {
            "source_name": "test",
            "site_type": "api",
            "api_config": {"url": "http://api.example.com"},
            "list_strategy": {},
            "detail_strategy": {},
            "pagination": {},
            "anti_detection": {},
            "max_pages": 5,
        }

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

            result = await list_fetch_tool(source_config, max_pages=3)

            assert isinstance(result, dict)
            assert result["success"] is True
            assert result["total_count"] == 1


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
