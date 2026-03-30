"""
Trend Analysis Agent Tests - TDD Cycle 39

测试趋势分析 Agent 的功能
"""
import json
import pytest
from datetime import datetime, timedelta
from typing import List, Dict, Any

from apps.analytics.agents.trend_analysis_agent import (
    TrendAnalysisAgent,
    create_trend_analysis_agent,
    generate_insights,
    generate_recommendations,
)


# ==================== 测试数据 ====================

def get_sample_tenders() -> List[Dict[str, Any]]:
    """获取样例招标数据"""
    base_date = datetime(2024, 1, 1)
    return [
        {
            "id": "t1",
            "title": "北京IT系统建设项目",
            "publish_date": (base_date).strftime("%Y-%m-%d"),
            "amount": 500000,
            "tenderer": "北京市政府",
            "region": "北京",
            "industry": "IT"
        },
        {
            "id": "t2",
            "title": "上海智慧城市项目",
            "publish_date": (base_date + timedelta(days=15)).strftime("%Y-%m-%d"),
            "amount": 800000,
            "tenderer": "上海市政府",
            "region": "上海",
            "industry": "智慧城市"
        },
        {
            "id": "t3",
            "title": "广东基础设施建设",
            "publish_date": (base_date + timedelta(days=30)).strftime("%Y-%m-%d"),
            "amount": 1200000,
            "tenderer": "广东省政府",
            "region": "广东",
            "industry": "建筑"
        },
        {
            "id": "t4",
            "title": "浙江数字化改革项目",
            "publish_date": (base_date + timedelta(days=45)).strftime("%Y-%m-%d"),
            "amount": 600000,
            "tenderer": "浙江省政府",
            "region": "浙江",
            "industry": "IT"
        },
        {
            "id": "t5",
            "title": "江苏智能制造项目",
            "publish_date": (base_date + timedelta(days=60)).strftime("%Y-%m-%d"),
            "amount": 900000,
            "tenderer": "江苏省政府",
            "region": "江苏",
            "industry": "制造"
        },
    ]


def get_monthly_tenders() -> List[Dict[str, Any]]:
    """获取按月分布的招标数据"""
    base_date = datetime(2024, 1, 1)
    tenders = []
    # 1月: 10个 (Jan 1-10)
    for i in range(10):
        tenders.append({
            "id": f"m1_{i}",
            "title": f"项目1_{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 500000 + i * 10000,
            "tenderer": f"招标人{i}",
            "region": "北京",
            "industry": "IT"
        })
    # 2月: 15个 (Feb 1-15)
    for i in range(15):
        tenders.append({
            "id": f"m2_{i}",
            "title": f"项目2_{i}",
            # 2024 是闰年，2月有29天，Feb 1 = day 31
            "publish_date": (base_date + timedelta(days=31 + i)).strftime("%Y-%m-%d"),
            "amount": 600000 + i * 10000,
            "tenderer": f"招标人{i}",
            "region": "上海",
            "industry": "建筑"
        })
    # 3月: 20个 (Mar 1-20)
    for i in range(20):
        # 2024年2月29天，Mar 1 = day 60
        tenders.append({
            "id": f"m3_{i}",
            "title": f"项目3_{i}",
            "publish_date": (base_date + timedelta(days=60 + i)).strftime("%Y-%m-%d"),
            "amount": 700000 + i * 10000,
            "tenderer": f"招标人{i}",
            "region": "广东",
            "industry": "IT"
        })
    return tenders


def get_regional_tenders() -> List[Dict[str, Any]]:
    """获取地区分布数据"""
    base_date = datetime(2024, 1, 1)
    tenders = []
    # 北京 40个
    for i in range(40):
        tenders.append({
            "id": f"bj_{i}",
            "title": f"北京项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 500000,
            "tenderer": f"北京招标人{i}",
            "region": "北京",
            "industry": "IT"
        })
    # 上海 30个
    for i in range(30):
        tenders.append({
            "id": f"sh_{i}",
            "title": f"上海项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 400000,
            "tenderer": f"上海招标人{i}",
            "region": "上海",
            "industry": "建筑"
        })
    # 广东 20个
    for i in range(20):
        tenders.append({
            "id": f"gd_{i}",
            "title": f"广东项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 300000,
            "tenderer": f"广东招标人{i}",
            "region": "广东",
            "industry": "制造"
        })
    # 浙江 10个
    for i in range(10):
        tenders.append({
            "id": f"zj_{i}",
            "title": f"浙江项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 200000,
            "tenderer": f"浙江招标人{i}",
            "region": "浙江",
            "industry": "IT"
        })
    return tenders


def get_industry_tenders() -> List[Dict[str, Any]]:
    """获取行业分布数据"""
    base_date = datetime(2024, 1, 1)
    tenders = []
    # IT 50个
    for i in range(50):
        tenders.append({
            "id": f"it_{i}",
            "title": f"IT项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 500000,
            "tenderer": f"招标人{i}",
            "region": "北京",
            "industry": "IT"
        })
    # 建筑 30个
    for i in range(30):
        tenders.append({
            "id": f"jz_{i}",
            "title": f"建筑项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 800000,
            "tenderer": f"招标人{i}",
            "region": "上海",
            "industry": "建筑"
        })
    # 制造 15个
    for i in range(15):
        tenders.append({
            "id": f"zz_{i}",
            "title": f"制造项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 600000,
            "tenderer": f"招标人{i}",
            "region": "广东",
            "industry": "制造"
        })
    # 医疗 5个
    for i in range(5):
        tenders.append({
            "id": f"yl_{i}",
            "title": f"医疗项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 300000,
            "tenderer": f"招标人{i}",
            "region": "浙江",
            "industry": "医疗"
        })
    return tenders


def get_amount_distribution_tenders() -> List[Dict[str, Any]]:
    """获取金额区间分布数据"""
    base_date = datetime(2024, 1, 1)
    tenders = []
    # 0-10万: 10个
    for i in range(10):
        tenders.append({
            "id": f"a1_{i}",
            "title": f"小额项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 50000 + i * 5000,
            "tenderer": f"招标人{i}",
            "region": "北京",
            "industry": "IT"
        })
    # 100-500万: 30个
    for i in range(30):
        tenders.append({
            "id": f"a2_{i}",
            "title": f"中额项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 1500000 + i * 10000,
            "tenderer": f"招标人{i}",
            "region": "上海",
            "industry": "建筑"
        })
    # 1000万以上: 10个
    for i in range(10):
        tenders.append({
            "id": f"a3_{i}",
            "title": f"大额项目{i}",
            "publish_date": (base_date + timedelta(days=i)).strftime("%Y-%m-%d"),
            "amount": 11000000 + i * 100000,
            "tenderer": f"招标人{i}",
            "region": "广东",
            "industry": "IT"
        })
    return tenders


def get_large_dataset() -> List[Dict[str, Any]]:
    """获取大数据集（1000条）"""
    base_date = datetime(2023, 1, 1)
    tenders = []
    regions = ["北京", "上海", "广东", "浙江", "江苏", "四川", "湖北", "山东"]
    industries = ["IT", "建筑", "制造", "医疗", "教育", "交通"]
    tenderers = [f"招标人{i}" for i in range(100)]

    for i in range(1000):
        tenders.append({
            "id": f"large_{i}",
            "title": f"大型项目{i}",
            "publish_date": (base_date + timedelta(days=i % 365)).strftime("%Y-%m-%d"),
            "amount": 100000 + (i % 50) * 100000,
            "tenderer": tenderers[i % 100],
            "region": regions[i % len(regions)],
            "industry": industries[i % len(industries)]
        })
    return tenders


# ==================== 测试用例 ====================

class TestTrendAnalysisAgent:
    """趋势分析 Agent 测试类"""

    def test_create_agent(self):
        """测试创建 Agent 实例"""
        agent = TrendAnalysisAgent()
        assert agent is not None
        assert agent.name == "trend-analysis-agent"
        assert hasattr(agent, "analyze")

    def test_create_agent_function(self):
        """测试便捷创建函数"""
        agent = create_trend_analysis_agent()
        assert agent is not None
        assert isinstance(agent, TrendAnalysisAgent)

    def test_analyze_empty_list(self):
        """测试空列表处理"""
        agent = TrendAnalysisAgent()
        result = agent.analyze([])

        assert result["status"] == "success"
        assert result["total_tenders"] == 0
        assert "data_summary" in result

    def test_analyze_comprehensive_report(self):
        """测试综合报告生成"""
        agent = TrendAnalysisAgent()
        tenders = get_sample_tenders()
        result = agent.analyze(tenders)

        assert result["status"] == "success"
        assert result["total_tenders"] == 5

        # 验证各维度分析结果存在
        assert "time_series_analysis" in result
        assert "regional_analysis" in result
        assert "industry_analysis" in result
        assert "amount_analysis" in result

    def test_time_series_analysis(self):
        """测试时间序列分析"""
        agent = TrendAnalysisAgent()
        tenders = get_monthly_tenders()
        result = agent.analyze_time_series(tenders)

        assert "monthly_counts" in result
        assert "2024-01" in result["monthly_counts"]
        assert result["monthly_counts"]["2024-01"] == 10
        assert result["monthly_counts"]["2024-02"] == 15
        assert result["monthly_counts"]["2024-03"] == 20

    def test_regional_distribution(self):
        """测试地区分布分析"""
        agent = TrendAnalysisAgent()
        tenders = get_regional_tenders()
        result = agent.analyze_regional_distribution(tenders)

        assert "top_regions" in result
        assert len(result["top_regions"]) > 0

        # 验证排名前列
        top = result["top_regions"]
        assert top[0]["region"] == "北京"
        assert top[0]["count"] == 40

    def test_industry_heat_analysis(self):
        """测试行业热度分析"""
        agent = TrendAnalysisAgent()
        tenders = get_industry_tenders()
        result = agent.analyze_industry_heat(tenders)

        assert "top_industries" in result
        assert len(result["top_industries"]) > 0

        # 验证排名第一
        top = result["top_industries"]
        assert top[0]["industry"] == "IT"
        assert top[0]["count"] == 50

    def test_amount_distribution(self):
        """测试金额区间分析"""
        agent = TrendAnalysisAgent()
        tenders = get_amount_distribution_tenders()
        result = agent.analyze_amount_distribution(tenders)

        assert "distribution" in result
        assert "total_amount" in result

    def test_growth_trend_detection(self):
        """测试增长趋势识别"""
        agent = TrendAnalysisAgent()
        tenders = get_monthly_tenders()
        result = agent.analyze(tenders)

        time_series = result.get("time_series_analysis", {})
        assert "trend" in time_series
        # 验证趋势识别（增长）
        assert time_series["trend"] in ["increasing", "stable", "decreasing"]

    def test_insights_generation(self):
        """测试市场洞察生成"""
        tenders = get_regional_tenders()
        agent = TrendAnalysisAgent()
        result = agent.analyze(tenders)

        assert "insights" in result
        assert isinstance(result["insights"], list)

    def test_recommendations_generation(self):
        """测试建议生成"""
        tenders = get_sample_tenders()
        agent = TrendAnalysisAgent()
        result = agent.analyze(tenders)

        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

    def test_large_dataset_processing(self):
        """测试大数据量处理"""
        agent = TrendAnalysisAgent()
        tenders = get_large_dataset()
        result = agent.analyze(tenders)

        assert result["status"] == "success"
        assert result["total_tenders"] == 1000
        assert "time_series_analysis" in result
        assert "regional_analysis" in result


class TestGenerateInsights:
    """洞察生成函数测试"""

    def test_generate_insights_from_time_series(self):
        """测试从时间序列生成洞察"""
        time_series = {
            "monthly_counts": {"2024-01": 10, "2024-02": 15, "2024-03": 20},
            "trend": "increasing"
        }
        insights = generate_insights(time_series, None, None, None)

        assert isinstance(insights, list)
        assert len(insights) > 0

    def test_generate_insights_from_regions(self):
        """测试从地区分布生成洞察"""
        regions = {
            "top_regions": [
                {"region": "北京", "count": 40, "percentage": 40},
                {"region": "上海", "count": 30, "percentage": 30}
            ]
        }
        insights = generate_insights(None, regions, None, None)

        assert isinstance(insights, list)
        assert len(insights) > 0

    def test_generate_insights_from_industry(self):
        """测试从行业分布生成洞察"""
        industry = {
            "top_industries": [
                {"industry": "IT", "count": 50, "percentage": 50},
                {"industry": "建筑", "count": 30, "percentage": 30}
            ]
        }
        insights = generate_insights(None, None, industry, None)

        assert isinstance(insights, list)
        assert len(insights) > 0

    def test_generate_insights_empty(self):
        """测试空数据生成洞察"""
        insights = generate_insights(None, None, None, None)

        assert isinstance(insights, list)


class TestGenerateRecommendations:
    """建议生成函数测试"""

    def test_generate_recommendations_from_analysis(self):
        """测试基于分析结果生成建议"""
        analysis_result = {
            "regional_analysis": {
                "top_regions": [
                    {"region": "北京", "count": 40, "percentage": 40}
                ]
            },
            "industry_analysis": {
                "top_industries": [
                    {"industry": "IT", "count": 50, "percentage": 50}
                ]
            }
        }
        recommendations = generate_recommendations(analysis_result)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

    def test_generate_recommendations_empty(self):
        """测试空数据生成建议"""
        recommendations = generate_recommendations({})

        assert isinstance(recommendations, list)


class TestAsyncInterface:
    """异步接口测试"""

    @pytest.mark.asyncio
    async def test_run_method(self):
        """测试异步 run 方法"""
        agent = TrendAnalysisAgent()
        tenders = get_sample_tenders()
        context = {"tenders": tenders}

        result = await agent.run("分析招标趋势", context)

        assert result["status"] == "success"
        assert result["total_tenders"] == 5


class TestEdgeCases:
    """边界情况测试"""

    def test_missing_fields(self):
        """测试缺失字段"""
        agent = TrendAnalysisAgent()
        tenders = [
            {"id": "t1"},  # 只有 id
            {"title": "test"},  # 只有 title
        ]
        result = agent.analyze(tenders)

        assert result["status"] == "success"

    def test_null_values(self):
        """测试空值处理"""
        agent = TrendAnalysisAgent()
        tenders = [
            {
                "id": "t1",
                "title": "test",
                "publish_date": None,
                "amount": None,
                "tenderer": None,
                "region": None,
                "industry": None
            }
        ]
        result = agent.analyze(tenders)

        assert result["status"] == "success"

    def test_invalid_date_format(self):
        """测试无效日期格式"""
        agent = TrendAnalysisAgent()
        tenders = [
            {
                "id": "t1",
                "title": "test",
                "publish_date": "invalid-date",
                "amount": 500000,
                "tenderer": "test",
                "region": "北京",
                "industry": "IT"
            }
        ]
        result = agent.analyze(tenders)

        assert result["status"] == "success"