"""
Analyze Trends Tool 测试 - TDD Cycle 35

测试 analyze_trends Tool 的所有功能
15个测试场景
"""
import pytest
import json
from datetime import datetime
from typing import List, Dict, Any


def create_tender_data(
    id: str,
    title: str,
    publish_date: str,
    amount: float,
    tenderer: str,
    region: str,
    industry: str
) -> Dict[str, Any]:
    """创建测试用招标数据"""
    return {
        "id": id,
        "title": title,
        "publish_date": publish_date,
        "amount": amount,
        "tenderer": tenderer,
        "region": region,
        "industry": industry
    }


class TestAnalyzeTrendsTool:
    """analyze_trends Tool 测试类"""

    def test_full_analysis_all_types(self):
        """测试1: 全部分析 - analysis_type='all'"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2024-01-20", 800000, "联通", "上海", "IT"),
            create_tender_data("t3", "项目C", "2024-02-10", 300000, "电信", "北京", "建筑"),
            create_tender_data("t4", "项目D", "2024-02-15", 1200000, "移动", "广东", "IT"),
            create_tender_data("t5", "项目E", "2024-03-05", 600000, "联通", "浙江", "医疗"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "all"
        })

        assert result is not None
        data = json.loads(result)

        # 验证所有分析维度都存在
        assert "time_series" in data
        assert "region_distribution" in data
        assert "industry_heat" in data
        assert "amount_distribution" in data
        assert "tenderer_activity" in data
        assert "analyzed_at" in data

    def test_time_series_analysis_only(self):
        """测试2: 时间序列分析 - analysis_type='time_series'"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2024-02-20", 800000, "联通", "上海", "IT"),
            create_tender_data("t3", "项目C", "2024-03-10", 300000, "电信", "北京", "建筑"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "time_series"
        })

        data = json.loads(result)
        assert "time_series" in data
        ts = data["time_series"]

        # 验证月度统计
        assert "monthly_counts" in ts
        assert "2024-01" in ts["monthly_counts"]
        assert "2024-02" in ts["monthly_counts"]
        assert "2024-03" in ts["monthly_counts"]

        # 验证季度统计
        assert "quarterly_counts" in ts
        assert "2024-Q1" in ts["quarterly_counts"]

        # 验证年度统计
        assert "yearly_counts" in ts
        assert "2024" in ts["yearly_counts"]

        # 验证月度金额
        assert "monthly_amounts" in ts

    def test_region_distribution_only(self):
        """测试3: 地区分布分析 - analysis_type='region'"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2024-01-20", 800000, "联通", "北京", "IT"),
            create_tender_data("t3", "项目C", "2024-02-10", 300000, "电信", "上海", "建筑"),
            create_tender_data("t4", "项目D", "2024-02-15", 1200000, "移动", "广东", "IT"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "region"
        })

        data = json.loads(result)
        assert "region_distribution" in data
        region = data["region_distribution"]

        # 验证 counts
        assert "counts" in region
        assert region["counts"]["北京"] == 2
        assert region["counts"]["上海"] == 1
        assert region["counts"]["广东"] == 1

        # 验证 heat_ranking - 现在返回对象列表
        assert "heat_ranking" in region
        assert region["heat_ranking"][0]["region"] == "北京"

    def test_industry_heat_only(self):
        """测试4: 行业热度分析 - analysis_type='industry'"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2024-01-20", 800000, "联通", "上海", "IT"),
            create_tender_data("t3", "项目C", "2024-02-10", 300000, "电信", "北京", "建筑"),
            create_tender_data("t4", "项目D", "2024-02-15", 1200000, "移动", "广东", "IT"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "industry"
        })

        data = json.loads(result)
        assert "industry_heat" in data
        industry = data["industry_heat"]

        # 验证 counts
        assert "counts" in industry
        assert industry["counts"]["IT"] == 3
        assert industry["counts"]["建筑"] == 1

        # 验证 heat_ranking - 现在返回对象列表
        assert "heat_ranking" in industry
        assert industry["heat_ranking"][0]["industry"] == "IT"

    def test_amount_distribution_only(self):
        """测试5: 金额区间分析 - analysis_type='amount'"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 50000, "移动", "北京", "IT"),       # 10-50万
            create_tender_data("t2", "项目B", "2024-01-20", 800000, "联通", "上海", "IT"),      # 50-100万
            create_tender_data("t3", "项目C", "2024-02-10", 3000000, "电信", "北京", "建筑"),  # 100-500万
            create_tender_data("t4", "项目D", "2024-02-15", 8000000, "移动", "广东", "IT"),    # 500-1000万
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "amount"
        })

        data = json.loads(result)
        assert "amount_distribution" in data
        amount = data["amount_distribution"]

        # 验证 counts
        assert "counts" in amount
        # 检查金额区间数量
        counts = amount["counts"]
        assert sum(counts.values()) == 4  # 总共4条数据

    def test_tenderer_activity_only(self):
        """测试6: 招标人活跃度 - analysis_type='tenderer'"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2024-01-20", 800000, "移动", "上海", "IT"),
            create_tender_data("t3", "项目C", "2024-02-10", 300000, "电信", "北京", "建筑"),
            create_tender_data("t4", "项目D", "2024-02-15", 1200000, "联通", "广东", "IT"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "tenderer"
        })

        data = json.loads(result)
        assert "tenderer_activity" in data
        tenderer = data["tenderer_activity"]

        # 验证 frequency_ranking - 现在返回对象列表
        assert "frequency_ranking" in tenderer
        assert tenderer["frequency_ranking"][0]["tenderer"] == "移动"  # 2次

    def test_empty_data(self):
        """测试7: 空数据 - 空列表处理"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders_json = json.dumps([])

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "all"
        })

        data = json.loads(result)

        # 空数据应该返回空分析结果
        assert "time_series" in data
        assert data["time_series"]["monthly_counts"] == {}

    def test_single_tender(self):
        """测试8: 单条数据 - 最小数据集"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 500000, "移动", "北京", "IT"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "all"
        })

        data = json.loads(result)

        # 单条数据也能正常分析
        assert data["time_series"]["monthly_counts"]["2024-01"] == 1
        assert data["region_distribution"]["counts"]["北京"] == 1
        assert data["industry_heat"]["counts"]["IT"] == 1

    def test_large_dataset(self):
        """测试9: 大数据量 - 1000条数据处理"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        # 生成1000条测试数据
        import random
        regions = ["北京", "上海", "广东", "浙江", "江苏", "四川", "湖北", "湖南"]
        industries = ["IT", "建筑", "医疗", "教育", "金融"]
        tenderers = ["移动", "联通", "电信", "华为", "阿里"]

        tenders = []
        for i in range(1000):
            tenders.append(create_tender_data(
                id=f"t{i}",
                title=f"项目{i}",
                publish_date=f"2024-{(i % 12) + 1:02d}-15",
                amount=random.randint(10000, 10000000),
                tenderer=random.choice(tenderers),
                region=random.choice(regions),
                industry=random.choice(industries)
            ))

        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "all"
        })

        data = json.loads(result)

        # 验证大数据量处理正常
        assert data["time_series"]["yearly_counts"]["2024"] == 1000
        assert data["tenderer_activity"]["total_unique_tenderers"] <= 5

    def test_monthly_statistics(self):
        """测试10: 月份统计 - 月度数量统计"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-05", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2024-01-15", 800000, "联通", "上海", "IT"),
            create_tender_data("t3", "项目C", "2024-01-25", 300000, "电信", "北京", "建筑"),
            create_tender_data("t4", "项目D", "2024-02-10", 1200000, "移动", "广东", "IT"),
            create_tender_data("t5", "项目E", "2024-03-20", 600000, "联通", "浙江", "医疗"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "time_series"
        })

        data = json.loads(result)
        ts = data["time_series"]

        # 验证月度数量
        assert ts["monthly_counts"]["2024-01"] == 3
        assert ts["monthly_counts"]["2024-02"] == 1
        assert ts["monthly_counts"]["2024-03"] == 1

    def test_quarterly_statistics(self):
        """测试11: 季度统计 - 季度数量统计"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2024-02-20", 800000, "联通", "上海", "IT"),
            create_tender_data("t3", "项目C", "2024-03-10", 300000, "电信", "北京", "建筑"),
            create_tender_data("t4", "项目D", "2024-04-15", 1200000, "移动", "广东", "IT"),
            create_tender_data("t5", "项目E", "2024-05-20", 600000, "联通", "浙江", "医疗"),
            create_tender_data("t6", "项目F", "2024-06-10", 900000, "电信", "江苏", "建筑"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "time_series"
        })

        data = json.loads(result)
        ts = data["time_series"]

        # 验证季度数量
        assert ts["quarterly_counts"]["2024-Q1"] == 3
        assert ts["quarterly_counts"]["2024-Q2"] == 3

    def test_yearly_statistics(self):
        """测试12: 年度统计 - 年度数量统计"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2023-01-15", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2023-06-20", 800000, "联通", "上海", "IT"),
            create_tender_data("t3", "项目C", "2024-01-10", 300000, "电信", "北京", "建筑"),
            create_tender_data("t4", "项目D", "2024-03-15", 1200000, "移动", "广东", "IT"),
            create_tender_data("t5", "项目E", "2024-06-20", 600000, "联通", "浙江", "医疗"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "time_series"
        })

        data = json.loads(result)
        ts = data["time_series"]

        # 验证年度数量
        assert ts["yearly_counts"]["2023"] == 2
        assert ts["yearly_counts"]["2024"] == 3

    def test_region_heat_ranking(self):
        """测试13: 地区排名 - 热度排名正确性"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2024-01-20", 800000, "联通", "北京", "IT"),
            create_tender_data("t3", "项目C", "2024-02-10", 300000, "电信", "北京", "建筑"),
            create_tender_data("t4", "项目D", "2024-02-15", 1200000, "移动", "上海", "IT"),
            create_tender_data("t5", "项目E", "2024-03-05", 600000, "联通", "广东", "医疗"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "region"
        })

        data = json.loads(result)
        region = data["region_distribution"]

        # 验证 heat_ranking 正确性 - 北京3次排第一，现在返回对象列表
        assert region["heat_ranking"][0]["region"] == "北京"
        assert region["counts"]["北京"] == 3

    def test_industry_heat_ranking(self):
        """测试14: 行业排名 - 热度排名正确性"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        tenders = [
            create_tender_data("t1", "项目A", "2024-01-15", 500000, "移动", "北京", "IT"),
            create_tender_data("t2", "项目B", "2024-01-20", 800000, "联通", "上海", "IT"),
            create_tender_data("t3", "项目C", "2024-02-10", 300000, "电信", "北京", "IT"),
            create_tender_data("t4", "项目D", "2024-02-15", 1200000, "移动", "广东", "建筑"),
            create_tender_data("t5", "项目E", "2024-03-05", 600000, "联通", "浙江", "建筑"),
        ]
        tenders_json = json.dumps(tenders)

        result = analyze_trends.invoke({
            "tenders_json": tenders_json,
            "analysis_type": "industry"
        })

        data = json.loads(result)
        industry = data["industry_heat"]

        # 验证 heat_ranking 正确性 - IT 3次排第一，现在返回对象列表
        assert industry["heat_ranking"][0]["industry"] == "IT"
        assert industry["counts"]["IT"] == 3

    def test_invalid_json_format(self):
        """测试15: JSON解析 - 输入JSON格式错误处理"""
        from apps.analytics.tools.analyze_trends import analyze_trends

        # 传入无效的 JSON 字符串
        invalid_json = "{ invalid json }"

        result = analyze_trends.invoke({
            "tenders_json": invalid_json,
            "analysis_type": "all"
        })

        data = json.loads(result)

        # 应该返回错误信息
        assert "error" in data or "success" in data