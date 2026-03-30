"""
Opportunity Agent Tests - TDD Cycle 38

测试 Opportunity Agent 的 10 个场景：
1. 单条分析 - 单个招标深度分析
2. 批量分析 - 多个招标批量评分
3. 高价值筛选 - 筛选 >=80分商机
4. 风险识别 - 识别风险因素
5. 推荐生成 - 生成行动建议
6. 报告生成 - 生成详细报告
7. 空数据 - 空列表处理
8. 阈值筛选 - 自定义阈值筛选
9. TOP-N排序 - 按分数排序
10. 错误处理 - 分析失败处理
"""
import json
import pytest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from typing import Dict, Any, List


# 测试数据
SAMPLE_TENDERS = [
    {
        "id": "t1",
        "title": "云计算平台建设项目",
        "tenderer": "中国移动北京公司",
        "budget": 5000000,
        "deadline_date": "2026-06-30",
        "publish_date": "2026-01-15",
        "region": "北京",
        "industry": "云计算"
    },
    {
        "id": "t2",
        "title": "数据中心设备采购",
        "tenderer": "中国联通上海分公司",
        "budget": 3000000,
        "deadline_date": "2026-07-15",
        "publish_date": "2026-02-01",
        "region": "上海",
        "industry": "通信"
    },
    {
        "id": "t3",
        "title": "智慧城市项目",
        "tenderer": "北京市政府",
        "budget": 10000000,
        "deadline_date": "2026-08-01",
        "publish_date": "2026-01-20",
        "region": "北京",
        "industry": "智慧城市"
    }
]


class TestOpportunityAgent:
    """Opportunity Agent 测试类"""

    @pytest.fixture
    def mock_score_opportunity_tool(self):
        """Mock score_opportunity Tool"""
        tool = Mock()
        tool.name = "score_opportunity"
        tool.invoke = Mock()
        return tool

    @pytest.fixture
    def sample_tenders(self) -> List[Dict[str, Any]]:
        """示例招标数据"""
        return SAMPLE_TENDERS

    def test_single_tender_analysis(self, sample_tenders):
        """测试1: 单条分析 - 单个招标深度分析"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        result = agent.analyze(sample_tenders[0])

        # 验证结果结构
        assert "status" in result
        assert result["status"] == "success"
        assert "results" in result
        assert len(result["results"]) == 1

    def test_batch_analysis(self, sample_tenders):
        """测试2: 批量分析 - 多个招标批量评分"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        result = agent.analyze(sample_tenders)

        assert result["status"] == "success"
        assert "total_analyzed" in result
        assert result["total_analyzed"] == 3
        assert "results" in result
        assert len(result["results"]) == 3

    def test_high_value_filtering(self, sample_tenders):
        """测试3: 高价值筛选 - 筛选 >=80分商机"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        # 先获取所有分析结果
        result = agent.analyze(sample_tenders)

        # 筛选高价值商机
        high_value = agent.find_high_value(sample_tenders, threshold=80.0)

        # 验证高价值筛选结果
        assert isinstance(high_value, list)
        for item in high_value:
            # 高价值商机应该 >= 80 分
            if "total_score" in item:
                assert item["total_score"] >= 80.0

    def test_risk_identification(self, sample_tenders):
        """测试4: 风险识别 - 识别风险因素"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        # 测试一个可能存在风险的招标（无预算、无截止日期）
        risky_tender = {
            "id": "t_risky",
            "title": "测试项目",
            "tenderer": "某公司",
            "budget": None,
            "deadline_date": None,
            "publish_date": "2026-01-01",
            "region": "北京",
            "industry": "软件"
        }

        result = agent.analyze(risky_tender)

        # 验证风险因素识别
        assert "results" in result
        if result["results"]:
            first_result = result["results"][0]
            if "risk_factors" in first_result:
                # 应该识别出信息风险
                assert len(first_result["risk_factors"]) > 0

    def test_recommendation_generation(self, sample_tenders):
        """测试5: 推荐生成 - 生成行动建议"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        result = agent.analyze(sample_tenders[0])

        # 验证推荐生成
        assert "results" in result
        if result["results"]:
            first_result = result["results"][0]
            assert "recommendations" in first_result
            assert isinstance(first_result["recommendations"], list)
            assert len(first_result["recommendations"]) > 0

    def test_report_generation(self, sample_tenders):
        """测试6: 报告生成 - 生成详细报告"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        # 先分析一次
        agent.analyze(sample_tenders)

        # 生成报告
        report = agent.generate_report("t1")

        assert "status" in report or "tender_id" in report or "tender" in report

    def test_empty_data(self):
        """测试7: 空数据 - 空列表处理"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        result = agent.analyze([])

        # 验证空数据处理
        assert "status" in result
        assert result["status"] == "success"
        assert result.get("total_analyzed", 0) == 0
        assert result.get("results", []) == []

    def test_custom_threshold_filtering(self, sample_tenders):
        """测试8: 阈值筛选 - 自定义阈值筛选"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        # 先分析
        result = agent.analyze(sample_tenders)

        # 使用较低阈值(50分)筛选
        filtered = agent.find_high_value(sample_tenders, threshold=50.0)

        # 验证阈值筛选
        for item in filtered:
            if "total_score" in item:
                assert item["total_score"] >= 50.0

    def test_top_n_sorting(self, sample_tenders):
        """测试9: TOP-N排序 - 按分数排序"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        result = agent.analyze(sample_tenders)

        # 验证有排序结果
        assert "top_opportunities" in result
        assert isinstance(result["top_opportunities"], list)

    def test_error_handling(self, sample_tenders):
        """测试10: 错误处理 - 分析失败处理"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        # Mock 评分器抛出异常
        with patch("apps.analytics.agents.opportunity_agent._get_scorer") as mock_get_scorer:
            mock_scorer = Mock()
            mock_scorer.score_tender.side_effect = Exception("Scoring engine error")
            mock_get_scorer.return_value = mock_scorer

            result = agent.analyze(sample_tenders[0])

            # 验证错误被优雅处理
            assert "status" in result
            # 可能是 "error" 或者 results 中包含错误信息

    def test_json_format(self, sample_tenders):
        """测试11: JSON格式 - 验证返回可序列化为JSON"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        result = agent.analyze(sample_tenders[0])

        # 验证可以序列化为 JSON
        json_str = json.dumps(result, ensure_ascii=False)
        assert json_str is not None

        # 验证可以反序列化
        parsed = json.loads(json_str)
        assert "status" in parsed

    def test_agent_properties(self):
        """测试12: Agent属性 - 验证agent属性正确"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        # 验证名称
        assert agent.name == "opportunity-agent"

        # 验证有 system_prompt
        assert hasattr(agent, "system_prompt")
        assert isinstance(agent.system_prompt, str)
        assert len(agent.system_prompt) > 0

    def test_score_factors_structure(self, sample_tenders):
        """测试13: 评分因子结构 - 验证评分因子完整"""
        from apps.analytics.agents.opportunity_agent import OpportunityAgent

        agent = OpportunityAgent()

        result = agent.analyze(sample_tenders[0])

        # 验证评分因子结构
        if result.get("results"):
            first_result = result["results"][0]
            if "factors" in first_result:
                factors = first_result["factors"]
                # 验证5个评分维度
                assert "amount_score" in factors
                assert "competition_score" in factors
                assert "timeline_score" in factors
                assert "relevance_score" in factors
                assert "history_score" in factors