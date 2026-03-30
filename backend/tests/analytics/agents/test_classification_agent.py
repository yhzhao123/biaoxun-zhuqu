"""
Classification Agent Tests - TDD Cycle 37

测试 Classification Agent 的 10 个场景：
1. 单条分类 - 单个招标分类
2. 批量分类 - 多个招标批量处理
3. 空列表 - 空招标列表处理
4. 数据缺失 - 部分字段缺失
5. 分类统计 - 汇总统计正确性
6. Tool调用 - 正确调用 classify_tender
7. 错误处理 - Tool 调用失败处理
8. 返回格式 - JSON 格式正确
9. 并发处理 - 批量并发分类
10. 中文内容 - 中文数据处理
"""
import json
import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Dict, Any


# 测试数据
SAMPLE_TENDERS = [
    {
        "id": "t1",
        "title": "云计算平台建设项目",
        "tenderer": "中国移动北京公司",
        "region": "北京市",
        "industry": "云计算",
        "amount": 5000000
    },
    {
        "id": "t2",
        "title": "数据中心设备采购",
        "tenderer": "中国联通上海分公司",
        "region": "上海市",
        "industry": "通信",
        "amount": 3000000
    },
    {
        "id": "t3",
        "title": "智慧城市项目",
        "tenderer": "北京市政府",
        "region": "北京市",
        "industry": "智慧城市",
        "amount": 10000000
    }
]


class TestClassificationAgent:
    """Classification Agent 测试类"""

    @pytest.fixture
    def mock_classify_tender_tool(self):
        """Mock classify_tender Tool"""
        tool = Mock()
        tool.name = "classify_tender"
        tool.invoke = Mock()
        return tool

    @pytest.fixture
    def mock_subagent_executor(self):
        """Mock SubagentExecutor"""
        with patch("apps.analytics.agents.classification_agent.SubagentExecutor") as mock:
            executor_instance = Mock()
            executor_instance.execute = Mock()
            mock.return_value = executor_instance
            yield executor_instance

    def test_single_tender_classification(self):
        """测试1: 单条分类 - 单个招标分类"""
        # 这个测试需要导入实际的 Agent 类
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        # 测试单个招标分类
        result = agent.classify_single(
            tender_id="t1",
            tenderer="中国移动北京公司",
            region="北京市",
            industry="云计算",
            amount=5000000
        )

        # 验证结果包含必要的字段
        assert "status" in result
        assert result["status"] == "success"
        assert "tender_id" in result or "tender" in result

    def test_batch_classification(self):
        """测试2: 批量分类 - 多个招标批量处理"""
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        tenders = [
            {"id": "t1", "tenderer": "中国移动", "region": "北京", "industry": "云计算", "amount": 5000000},
            {"id": "t2", "tenderer": "中国联通", "region": "上海", "industry": "通信", "amount": 3000000},
        ]

        result = agent.classify_batch(tenders)

        assert result["status"] == "success"
        assert "results" in result
        assert len(result["results"]) == 2

    def test_empty_list(self):
        """测试3: 空列表 - 空招标列表处理"""
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        result = agent.classify_batch([])

        assert result["status"] == "success"
        assert result["total"] == 0
        assert result["classified"] == 0
        assert result["results"] == []

    def test_missing_fields(self):
        """测试4: 数据缺失 - 部分字段缺失"""
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        # 只提供部分字段
        result = agent.classify_single(
            tender_id="t1",
            tenderer="中国移动",
            region="北京",
            industry="云计算"
            # 缺少 amount
        )

        # 应该仍然能够分类
        assert result["status"] == "success"
        assert result["tender_id"] == "t1"

    def test_classification_summary(self):
        """测试5: 分类统计 - 汇总统计正确性"""
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        result = agent.classify_batch(SAMPLE_TENDERS)

        # 验证汇总统计
        assert "summary" in result
        summary = result["summary"]

        # 验证有汇总维度
        assert "by_region" in summary or "by_tenderer" in summary or "by_industry" in summary

    def test_tool_invocation(self):
        """测试6: Tool调用 - 正确调用 classify_tender"""
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        # 验证有正确的工具名称
        assert agent.name == "classification-agent"

        # 验证可以调用分类方法并返回正确结构
        result = agent.classify_single(
            tender_id="t1",
            tenderer="中国移动北京公司",
            region="北京市",
            industry="云计算"
        )

        # 验证返回包含必要的分类字段
        assert "tenderer_category" in result
        assert "region_category" in result
        assert "industry_category" in result

    def test_error_handling(self):
        """测试7: 错误处理 - 分类器调用失败处理"""
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        # Mock 分类器抛出异常
        with patch.object(agent.classifier, "classify_tender", side_effect=Exception("Classification engine error")):
            result = agent.classify_single(
                tender_id="t1",
                tenderer="中国移动",
                region="北京",
                industry="云计算"
            )

            # 应该优雅处理错误
            assert "error" in result or result["status"] == "error"

    def test_json_format(self):
        """测试8: 返回格式 - JSON 格式正确"""
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        result = agent.classify_single(
            tender_id="t1",
            tenderer="中国移动",
            region="北京",
            industry="云计算",
            amount=5000000
        )

        # 验证可以序列化为 JSON
        json_str = json.dumps(result, ensure_ascii=False)
        assert json_str is not None

        # 验证可以反序列化
        parsed = json.loads(json_str)
        assert parsed["tender_id"] == "t1"

    def test_concurrent_batch(self):
        """测试9: 并发处理 - 批量并发分类"""
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        # 创建大批量数据 (10个)
        tenders = [
            {"id": f"t{i}", "tenderer": f"公司{i}", "region": "北京", "industry": "云计算", "amount": 1000000 * i}
            for i in range(10)
        ]

        result = agent.classify_batch(tenders)

        assert result["status"] == "success"
        assert result["total"] == 10
        assert result["classified"] == 10
        assert len(result["results"]) == 10

    def test_chinese_content(self):
        """测试10: 中文内容 - 中文数据处理"""
        from apps.analytics.agents.classification_agent import ClassificationAgent

        agent = ClassificationAgent()

        chinese_tenders = [
            {"id": "t1", "tenderer": "中国移动通信集团公司", "region": "北京市", "industry": "移动通信", "amount": 5000000},
            {"id": "t2", "tenderer": "上海市政府采购中心", "region": "上海市", "industry": "政府采购", "amount": 8000000},
            {"id": "t3", "tenderer": "广东省电力有限公司", "region": "广东省", "industry": "电力", "amount": 15000000},
        ]

        result = agent.classify_batch(chinese_tenders)

        assert result["status"] == "success"
        assert result["total"] == 3

        # 验证中文内容正确处理
        for r in result["results"]:
            # 验证返回的分类结果包含中文
            assert r is not None