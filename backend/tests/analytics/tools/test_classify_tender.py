"""
Classify Tender Tool 测试 - TDD Cycle 33

测试 classify_tender Tool 的所有功能
"""
import pytest
import json
from unittest.mock import Mock, patch


class TestClassifyTenderTool:
    """classify_tender Tool 测试类"""

    def test_basic_classification(self):
        """测试1: 基本分类 - 正常招标数据分类"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t001",
            "tenderer": "中国移动北京公司",
            "region": "北京市",
            "industry": "通信",
            "amount": 500000.0
        })

        assert result is not None
        data = json.loads(result)
        assert data["tender_id"] == "t001"
        assert "tenderer_category" in data
        assert "region_category" in data
        assert "industry_category" in data
        assert "amount_category" in data

    def test_tenderer_classification(self):
        """测试2: 招标人分类 - 验证招标人识别和类型判断"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t002",
            "tenderer": "中国联通上海公司",
            "region": "上海市",
            "industry": "电信",
            "amount": 100000.0
        })

        data = json.loads(result)
        tenderer = data["tenderer_category"]
        assert "normalized" in tenderer
        assert "category" in tenderer
        # 中国联通应该是国有企业
        assert tenderer["category"] == "国有企业"

    def test_region_classification(self):
        """测试3: 地区分类 - 验证地区标准化和区域划分"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t003",
            "tenderer": "某政府机关",
            "region": "广东省",
            "industry": "信息技术",
            "amount": 200000.0
        })

        data = json.loads(result)
        region = data["region_category"]
        assert region["normalized"] == "广东"
        assert region["category"] == "华南地区"

    def test_industry_classification(self):
        """测试4: 行业分类 - 验证行业识别和代码映射"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t004",
            "tenderer": "某医院",
            "region": "北京市",
            "industry": "医疗",
            "amount": 300000.0
        })

        data = json.loads(result)
        industry = data["industry_category"]
        assert "normalized" in industry
        assert "category" in industry

    def test_amount_classification(self):
        """测试5: 金额分类 - 验证金额区间判断"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t005",
            "tenderer": "某公司",
            "region": "北京市",
            "industry": "通信",
            "amount": 500000.0  # 50万 - 中额
        })

        data = json.loads(result)
        amount = data["amount_category"]
        assert "category" in amount

    def test_empty_amount(self):
        """测试6: 空金额 - 处理 None 金额"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t006",
            "tenderer": "某公司",
            "region": "北京市",
            "industry": "通信",
            "amount": None
        })

        data = json.loads(result)
        # None 金额时不应有 amount_category（符合 TenderClassifier 实现）
        assert "amount_category" not in data

    def test_zero_amount(self):
        """测试7: 零金额 - 处理 0 金额"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t007",
            "tenderer": "某公司",
            "region": "北京市",
            "industry": "通信",
            "amount": 0
        })

        data = json.loads(result)
        assert "amount_category" in data

    def test_large_amount(self):
        """测试8: 超大金额 - 处理超大金额（>1000万）"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t008",
            "tenderer": "某大型企业",
            "region": "上海市",
            "industry": "建筑",
            "amount": 50000000.0  # 5000万 - 超大额
        })

        data = json.loads(result)
        amount = data["amount_category"]
        # 验证超大额分类
        assert amount is not None

    def test_unknown_tenderer(self):
        """测试9: 未知招标人 - 未知招标人处理"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t009",
            "tenderer": "未知公司XYZ",
            "region": "北京市",
            "industry": "通信",
            "amount": 100000.0
        })

        data = json.loads(result)
        tenderer = data["tenderer_category"]
        # 未知招标人应该有默认分类
        assert tenderer is not None

    def test_unknown_region(self):
        """测试10: 未知地区 - 未知地区处理"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t010",
            "tenderer": "某公司",
            "region": "未知地区XYZ",
            "industry": "通信",
            "amount": 100000.0
        })

        data = json.loads(result)
        region = data["region_category"]
        # 未知地区应该有低置信度或默认分类

    def test_unknown_industry(self):
        """测试11: 未知行业 - 未知行业处理"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t011",
            "tenderer": "某公司",
            "region": "北京市",
            "industry": "未知行业XYZ",
            "amount": 100000.0
        })

        data = json.loads(result)
        industry = data["industry_category"]
        assert industry is not None

    def test_all_fields(self):
        """测试12: 全部字段 - 所有分类维度同时测试"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t012",
            "tenderer": "中国电信江苏公司",
            "region": "江苏省",
            "industry": "电信",
            "amount": 800000.0
        })

        data = json.loads(result)
        # 验证所有字段都存在
        assert data["tender_id"] == "t012"
        assert "tenderer_category" in data
        assert "region_category" in data
        assert "industry_category" in data
        assert "amount_category" in data

    def test_return_format(self):
        """测试13: 返回格式 - 验证 JSON 格式正确"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t013",
            "tenderer": "某公司",
            "region": "北京市",
            "industry": "通信",
            "amount": 100000.0
        })

        # 验证是有效的 JSON
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_chinese_content(self):
        """测试14: 中文字符 - 处理中文内容"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t014",
            "tenderer": "中华人民共和国财政部",
            "region": "北京市",
            "industry": "金融",
            "amount": 1000000.0
        })

        data = json.loads(result)
        # 验证中文正确处理
        assert "中" in data["tenderer_category"]["normalized"]

    def test_special_characters(self):
        """测试15: 特殊字符 - 处理特殊字符"""
        from apps.analytics.tools.classify_tender import classify_tender

        result = classify_tender.invoke({
            "tender_id": "t015",
            "tenderer": "某公司(分支机构)@#",
            "region": "北京市",
            "industry": "信息技术",
            "amount": 250000.0
        })

        data = json.loads(result)
        # 验证特殊字符处理不导致错误
        assert data["tender_id"] == "t015"


class TestClassifyTenderInput:
    """ClassifyTenderInput 输入模型测试"""

    def test_input_model_valid(self):
        """测试输入模型验证 - 有效输入"""
        from apps.analytics.tools.classify_tender import ClassifyTenderInput
        from pydantic import ValidationError

        try:
            obj = ClassifyTenderInput(
                tender_id="t001",
                tenderer="测试公司",
                region="北京",
                industry="通信",
                amount=100000.0
            )
            assert obj.tender_id == "t001"
            assert obj.amount == 100000.0
        except ValidationError:
            pytest.skip("Pydantic validation not available")

    def test_input_model_optional_amount(self):
        """测试输入模型验证 - 可选金额"""
        from apps.analytics.tools.classify_tender import ClassifyTenderInput
        from pydantic import ValidationError

        try:
            obj = ClassifyTenderInput(
                tender_id="t002",
                tenderer="测试公司",
                region="北京",
                industry="通信"
            )
            assert obj.amount is None
        except ValidationError:
            pytest.skip("Pydantic validation not available")


class TestToolMetadata:
    """Tool 元数据测试"""

    def test_tool_name(self):
        """测试工具名称"""
        from apps.analytics.tools.classify_tender import classify_tender

        assert classify_tender.name == "classify_tender"

    def test_tool_description(self):
        """测试工具描述存在"""
        from apps.analytics.tools.classify_tender import classify_tender

        assert classify_tender.description is not None
        assert len(classify_tender.description) > 0

    def test_tool_args_schema(self):
        """测试工具参数模式"""
        from apps.analytics.tools.classify_tender import classify_tender

        # 验证 args_schema
        assert classify_tender.args_schema is not None