"""
Test Aggregate Data Tool - TDD Cycle 36

测试 aggregate_data Tool 的 15 个测试场景
"""
import json
import pytest
from datetime import datetime, timedelta
from typing import List, Optional

from apps.analytics.tools.aggregate_data import (
    aggregate_data,
    AggregateDataInput,
    _parse_tenders_json,
    _parse_filters_json,
    _convert_to_tender_data,
    _serialize_result,
)
from apps.analytics.api.aggregator import AnalyticsAPI, TenderData, FilterParams


# ==================== 辅助函数测试 ====================

class TestParseTendersJson:
    """测试 tenders_json 解析"""

    def test_valid_json_array(self):
        """测试有效 JSON 数组解析"""
        data = '[{"id": "t1", "title": "项目A"}]'
        result = _parse_tenders_json(data)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "t1"

    def test_empty_json_array(self):
        """测试空数组解析"""
        data = '[]'
        result = _parse_tenders_json(data)
        assert result == []

    def test_invalid_json(self):
        """测试无效 JSON 处理"""
        data = 'invalid json'
        result = _parse_tenders_json(data)
        assert result == []

    def test_malformed_json(self):
        """测试畸形 JSON 处理"""
        data = '{"id": "t1", "title": "项目A"'  # 缺少 }
        result = _parse_tenders_json(data)
        assert result == []

    def test_empty_string(self):
        """测试空字符串"""
        result = _parse_tenders_json("")
        assert result == []


class TestParseFiltersJson:
    """测试 filters_json 解析"""

    def test_valid_filters_json(self):
        """测试有效筛选条件解析"""
        data = '{"regions": ["北京", "上海"], "start_date": "2024-01-01"}'
        result = _parse_filters_json(data)
        assert result is not None
        assert "regions" in result
        assert result["regions"] == ["北京", "上海"]

    def test_none_input(self):
        """测试 None 输入"""
        result = _parse_filters_json(None)
        assert result == {}

    def test_empty_string(self):
        """测试空字符串"""
        result = _parse_filters_json("")
        assert result == {}

    def test_invalid_filters_json(self):
        """测试无效筛选条件"""
        result = _parse_filters_json("not json")
        assert result == {}


class TestConvertToTenderData:
    """测试 TenderData 转换"""

    def test_valid_conversion(self):
        """测试有效数据转换"""
        raw = {
            "id": "t1",
            "title": "测试项目",
            "publish_date": "2024-01-15",
            "amount": 100000,
            "tenderer": "某单位",
            "region": "北京",
            "industry": "IT",
            "status": "招标中"
        }
        result = _convert_to_tender_data(raw)
        assert result.id == "t1"
        assert result.title == "测试项目"
        assert result.amount == 100000.0

    def test_missing_optional_fields(self):
        """测试可选字段缺失"""
        raw = {
            "id": "t1",
            "title": "测试项目",
            "publish_date": "2024-01-15",
            "tenderer": "某单位",
            "region": "北京",
            "industry": "IT"
        }
        result = _convert_to_tender_data(raw)
        assert result.amount is None
        assert result.status == "招标中"

    def test_invalid_date_format(self):
        """测试无效日期格式"""
        raw = {
            "id": "t1",
            "title": "测试项目",
            "publish_date": "invalid-date",
            "tenderer": "某单位",
            "region": "北京",
            "industry": "IT"
        }
        result = _convert_to_tender_data(raw)
        # 使用当前日期作为默认值
        assert result.publish_date is not None


# ==================== Tool 功能测试 ====================

@pytest.fixture
def sample_tenders() -> List[dict]:
    """样本招标数据"""
    now = datetime.now()
    return [
        {
            "id": "t1",
            "title": "智慧城市项目",
            "publish_date": (now - timedelta(days=1)).strftime("%Y-%m-%d"),
            "amount": 5000000,
            "tenderer": "北京市政府",
            "region": "北京",
            "industry": "IT",
            "status": "招标中"
        },
        {
            "id": "t2",
            "title": "医院建设",
            "publish_date": now.strftime("%Y-%m-%d"),
            "amount": 20000000,
            "tenderer": "上海市医院",
            "region": "上海",
            "industry": "医疗",
            "status": "招标中"
        },
        {
            "id": "t3",
            "title": "学校网络改造",
            "publish_date": (now - timedelta(days=5)).strftime("%Y-%m-%d"),
            "amount": 800000,
            "tenderer": "北京市教育局",
            "region": "北京",
            "industry": "教育",
            "status": "招标中"
        },
        {
            "id": "t4",
            "title": "工业园区建设",
            "publish_date": (now - timedelta(days=30)).strftime("%Y-%m-%d"),
            "amount": 50000000,
            "tenderer": "深圳产业园",
            "region": "深圳",
            "industry": "建筑",
            "status": "招标中"
        },
        {
            "id": "t5",
            "title": "软件采购",
            "publish_date": now.strftime("%Y-%m-%d"),
            "amount": 300000,
            "tenderer": "某科技公司",
            "region": "北京",
            "industry": "IT",
            "status": "招标中"
        },
    ]


@pytest.mark.unit
class TestAggregateDataOverview:
    """测试概览查询"""

    def test_overview_query(self, sample_tenders):
        """测试 query_type='overview'"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "overview"
        })

        result_data = json.loads(result)
        assert "overview" in result_data
        assert result_data["overview"]["total_count"] == 5
        assert result_data["overview"]["total_amount"] > 0


@pytest.mark.unit
class TestAggregateDataClassification:
    """测试分类统计"""

    def test_classification_query(self, sample_tenders):
        """测试 query_type='classification'"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "classification"
        })

        result_data = json.loads(result)
        assert "classification" in result_data
        assert "by_region" in result_data["classification"]
        assert result_data["classification"]["by_region"]["北京"] == 3


@pytest.mark.unit
class TestAggregateDataOpportunities:
    """测试商机列表"""

    def test_opportunities_query(self, sample_tenders):
        """测试 query_type='opportunities'"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "opportunities"
        })

        result_data = json.loads(result)
        assert "opportunities" in result_data
        assert "items" in result_data["opportunities"]
        # 分页信息在顶层
        assert "page" in result_data["opportunities"]
        assert "page_size" in result_data["opportunities"]


@pytest.mark.unit
class TestAggregateDataTrends:
    """测试趋势分析"""

    def test_trends_query(self, sample_tenders):
        """测试 query_type='trends'"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "trends"
        })

        result_data = json.loads(result)
        assert "trends" in result_data
        assert "time_series" in result_data["trends"]


@pytest.mark.unit
class TestAggregateDataDashboard:
    """测试完整仪表板"""

    def test_dashboard_query(self, sample_tenders):
        """测试 query_type='dashboard'"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "dashboard"
        })

        result_data = json.loads(result)
        assert "overview" in result_data
        assert "classification" in result_data
        assert "opportunities" in result_data
        assert "trends" in result_data


@pytest.mark.unit
class TestAggregateDataFilters:
    """测试筛选功能"""

    def test_region_filter(self, sample_tenders):
        """测试地区筛选"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        filters_json = json.dumps({"regions": ["北京"]})
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "overview",
            "filters_json": filters_json
        })

        result_data = json.loads(result)
        # 北京地区有 3 条: t1, t3, t5
        assert result_data["overview"]["total_count"] == 3

    def test_industry_filter(self, sample_tenders):
        """测试行业筛选"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        filters_json = json.dumps({"industries": ["IT"]})
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "overview",
            "filters_json": filters_json
        })

        result_data = json.loads(result)
        # IT 行业有 2 条: t1, t5
        assert result_data["overview"]["total_count"] == 2

    def test_date_range_filter(self, sample_tenders):
        """测试时间范围筛选"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        now = datetime.now()
        filters_json = json.dumps({
            "start_date": (now - timedelta(days=2)).strftime("%Y-%m-%d"),
            "end_date": now.strftime("%Y-%m-%d")
        })
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "overview",
            "filters_json": filters_json
        })

        result_data = json.loads(result)
        # 今天、昨天、前天的记录: t1(t2-1), t2, t5 = 3条
        assert result_data["overview"]["total_count"] == 3

    def test_amount_range_filter(self, sample_tenders):
        """测试金额区间筛选"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        filters_json = json.dumps({"amount_range": [100000, 1000000]})
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "overview",
            "filters_json": filters_json
        })

        result_data = json.loads(result)
        # 10万-100万: t3(80万), t5(30万)
        assert result_data["overview"]["total_count"] == 2


@pytest.mark.unit
class TestAggregateDataPagination:
    """测试分页功能"""

    def test_pagination(self, sample_tenders):
        """测试分页参数"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "opportunities",
            "page": 2,
            "page_size": 2
        })

        result_data = json.loads(result)
        # 分页信息在顶层
        assert "page" in result_data["opportunities"]
        assert "page_size" in result_data["opportunities"]


@pytest.mark.unit
class TestAggregateDataOpportunityScoreFilter:
    """测试商机评分筛选"""

    def test_opportunity_score_min_filter(self, sample_tenders):
        """测试商机评分筛选"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        filters_json = json.dumps({"opportunity_score_min": 80})
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "opportunities",
            "filters_json": filters_json
        })

        result_data = json.loads(result)
        assert "opportunities" in result_data
        # 检查所有返回的商机评分都 >= 80
        if result_data["opportunities"]["items"]:
            for item in result_data["opportunities"]["items"]:
                assert item["total_score"] >= 80


@pytest.mark.unit
class TestAggregateDataCombinedFilters:
    """测试组合筛选"""

    def test_combined_filters(self, sample_tenders):
        """测试多条件组合筛选"""
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        filters_json = json.dumps({
            "regions": ["北京"],
            "industries": ["IT"],
            "start_date": "2024-01-01"
        })
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "dashboard",
            "filters_json": filters_json
        })

        result_data = json.loads(result)
        assert "overview" in result_data
        # 北京 + IT 行业 = 2 条 (t1, t5)


@pytest.mark.unit
class TestAggregateDataEdgeCases:
    """测试边界情况"""

    def test_empty_tenders_list(self):
        """测试空数据列表"""
        result = aggregate_data.invoke({
            "tenders_json": "[]",
            "query_type": "overview"
        })

        result_data = json.loads(result)
        assert result_data["overview"]["total_count"] == 0

    def test_invalid_tenders_json(self):
        """测试无效 JSON 格式"""
        result = aggregate_data.invoke({
            "tenders_json": "not valid json",
            "query_type": "overview"
        })

        result_data = json.loads(result)
        # 应该返回空结果，不抛出异常
        assert "overview" in result_data

    def test_unknown_query_type(self):
        """测试未知 query_type"""
        sample_tenders = [
            {
                "id": "t1",
                "title": "测试",
                "publish_date": "2024-01-01",
                "tenderer": "单位",
                "region": "北京",
                "industry": "IT"
            }
        ]
        tenders_json = json.dumps(sample_tenders, ensure_ascii=False)
        result = aggregate_data.invoke({
            "tenders_json": tenders_json,
            "query_type": "unknown_type"
        })

        result_data = json.loads(result)
        # 未知类型应该回退到 overview
        assert "overview" in result_data


@pytest.mark.unit
class TestAggregateDataInputModel:
    """测试输入模型验证"""

    def test_valid_input(self):
        """测试有效输入"""
        input_data = AggregateDataInput(
            tenders_json='[{"id": "t1"}]',
            query_type="overview",
            filters_json='{"regions": ["北京"]}',
            page=1,
            page_size=20
        )
        assert input_data.query_type == "overview"
        assert input_data.page == 1

    def test_default_values(self):
        """测试默认值"""
        input_data = AggregateDataInput(
            tenders_json='[{"id": "t1"}]'
        )
        assert input_data.query_type == "overview"
        assert input_data.filters_json is None
        assert input_data.page == 1
        assert input_data.page_size == 20


@pytest.mark.unit
class TestSerializeResult:
    """测试结果序列化"""

    def test_serialize_overview_result(self):
        """测试概览结果序列化"""
        from apps.analytics.api.aggregator import OverviewResult

        result = OverviewResult(
            total_count=100,
            total_amount=5000000,
            active_tenderers=10,
            avg_amount=50000,
            today_count=5,
            week_count=20,
            month_count=80
        )
        serialized = _serialize_result(result)
        assert serialized["total_count"] == 100
        assert serialized["total_amount"] == 5000000

    def test_serialize_classification_stats(self):
        """测试分类统计序列化"""
        from apps.analytics.api.aggregator import ClassificationStats

        result = ClassificationStats(
            by_tenderer={"单位A": 10, "单位B": 5},
            by_region={"北京": 8, "上海": 7},
            by_industry={"IT": 10, "建筑": 5},
            by_amount_range={"0-10万": 3, "1000万以上": 2}
        )
        serialized = _serialize_result(result)
        assert serialized["by_region"]["北京"] == 8
        assert serialized["by_industry"]["IT"] == 10