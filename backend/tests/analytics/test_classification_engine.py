"""
TDD Cycle 27: 智能分类引擎测试
"""
import pytest
from apps.analytics.classification.engine import (
    TenderClassifier,
    ClassificationType,
    ClassificationResult,
    TenderClassification,
)


class TestClassificationResult:
    """测试分类结果数据类"""

    def test_classification_result_creation(self):
        """测试分类结果创建"""
        result = ClassificationResult(
            original_value="北京市",
            normalized_value="北京",
            category="华北地区",
            confidence=0.95,
            classification_type=ClassificationType.REGION
        )
        assert result.original_value == "北京市"
        assert result.normalized_value == "北京"
        assert result.category == "华北地区"
        assert result.confidence == 0.95
        assert result.classification_type == ClassificationType.REGION

    def test_classification_result_with_metadata(self):
        """测试带元数据的分类结果"""
        result = ClassificationResult(
            original_value="XX公司",
            normalized_value="XX公司",
            category="国有企业",
            confidence=0.88,
            classification_type=ClassificationType.TENDERER,
            metadata={"alias": ["XX集团", "XX股份"]}
        )
        assert result.metadata["alias"] == ["XX集团", "XX股份"]


class TestTenderClassification:
    """测试招标信息分类数据类"""

    def test_tender_classification_creation(self):
        """测试招标分类创建"""
        classification = TenderClassification(tender_id="T001")
        assert classification.tender_id == "T001"
        assert classification.tenderer_category is None
        assert classification.region_category is None

    def test_tender_classification_with_categories(self):
        """测试带分类结果的招标分类"""
        region_result = ClassificationResult(
            original_value="上海市",
            normalized_value="上海",
            category="华东地区",
            confidence=0.98,
            classification_type=ClassificationType.REGION
        )
        classification = TenderClassification(
            tender_id="T002",
            region_category=region_result
        )
        assert classification.region_category.category == "华东地区"


class TestTenderClassifierInitialization:
    """测试分类器初始化"""

    def test_classifier_initialization(self):
        """测试分类器可以初始化"""
        classifier = TenderClassifier()
        assert classifier is not None
        assert classifier.tenderer_rules is not None
        assert classifier.region_rules is not None
        assert classifier.industry_rules is not None


class TestTendererClassification:
    """测试招标人分类"""

    def test_classify_tenderer_returns_result(self):
        """测试招标人分类返回结果"""
        classifier = TenderClassifier()
        result = classifier.classify_tenderer("中国移动通信集团公司")
        assert isinstance(result, ClassificationResult)

    def test_classify_tenderer_normalizes_name(self):
        """测试招标人名称规范化"""
        classifier = TenderClassifier()
        result = classifier.classify_tenderer("中国移动通信集团公司")
        assert result.normalized_value == "中国移动"
        assert result.category == "国有企业"

    def test_classify_tenderer_handles_variations(self):
        """测试处理招标人名称变体"""
        classifier = TenderClassifier()
        result1 = classifier.classify_tenderer("XX股份有限公司")
        result2 = classifier.classify_tenderer("XX股份公司")
        assert result1.normalized_value == result2.normalized_value


class TestRegionClassification:
    """测试地区分类"""

    def test_classify_region_returns_result(self):
        """测试地区分类返回结果"""
        classifier = TenderClassifier()
        result = classifier.classify_region("北京市")
        assert isinstance(result, ClassificationResult)

    def test_classify_region_normalizes_city(self):
        """测试城市名称规范化"""
        classifier = TenderClassifier()
        result = classifier.classify_region("北京市")
        assert result.normalized_value == "北京"
        assert result.category == "华北地区"

    def test_classify_region_handles_province(self):
        """测试处理省份名称"""
        classifier = TenderClassifier()
        result = classifier.classify_region("广东省")
        assert result.normalized_value == "广东"
        assert result.category == "华南地区"

    def test_classify_region_handles_unknown(self):
        """测试处理未知地区"""
        classifier = TenderClassifier()
        result = classifier.classify_region("未知地区")
        assert result.category == "未知"
        assert result.confidence < 0.5


class TestIndustryClassification:
    """测试行业分类"""

    def test_classify_industry_returns_result(self):
        """测试行业分类返回结果"""
        classifier = TenderClassifier()
        result = classifier.classify_industry("信息技术")
        assert isinstance(result, ClassificationResult)

    def test_classify_industry_maps_to_standard(self):
        """测试行业映射到标准分类"""
        classifier = TenderClassifier()
        result = classifier.classify_industry("软件开发")
        assert result.category == "信息传输、软件和信息技术服务业"


class TestTenderClassificationIntegration:
    """测试完整分类流程"""

    def test_classify_tender_returns_complete_classification(self):
        """测试完整招标分类"""
        classifier = TenderClassifier()
        classification = classifier.classify_tender(
            tender_id="T001",
            tenderer="中国移动通信集团公司",
            region="北京市",
            industry="信息技术",
            amount=5000000.0
        )
        assert isinstance(classification, TenderClassification)
        assert classification.tender_id == "T001"
        assert classification.tenderer_category is not None
        assert classification.region_category is not None
        assert classification.industry_category is not None

    def test_classify_tender_handles_empty_values(self):
        """测试处理空值"""
        classifier = TenderClassifier()
        classification = classifier.classify_tender(
            tender_id="T002",
            tenderer="",
            region="",
            industry=""
        )
        assert classification.tender_id == "T002"
        # 空值应该返回默认分类
        assert classification.tenderer_category is not None


class TestAmountClassification:
    """测试金额分类"""

    def test_classify_small_amount(self):
        """测试小额分类"""
        classifier = TenderClassifier()
        result = classifier.amount_rules.classify(50000)
        assert result.category == "小额 (<10万)"
        assert result.confidence == 0.95

    def test_classify_medium_amount(self):
        """测试中额分类"""
        classifier = TenderClassifier()
        result = classifier.amount_rules.classify(500000)
        assert result.category == "中额 (10-100万)"

    def test_classify_large_amount(self):
        """测试大额分类"""
        classifier = TenderClassifier()
        result = classifier.amount_rules.classify(5000000)
        assert result.category == "大额 (100-1000万)"

    def test_classify_extra_large_amount(self):
        """测试超大额分类"""
        classifier = TenderClassifier()
        result = classifier.amount_rules.classify(50000000)
        assert result.category == "超大额 (>=1000万)"


class TestClassificationEdgeCases:
    """测试边界情况"""

    def test_empty_string_classification(self):
        """测试空字符串分类"""
        classifier = TenderClassifier()

        tenderer_result = classifier.classify_tenderer("")
        assert tenderer_result.category == "未知"

        region_result = classifier.classify_region("")
        assert region_result.category == "未知"

        industry_result = classifier.classify_industry("")
        assert industry_result.category == "未知"

    def test_none_amount_classification(self):
        """测试 None 金额不触发分类"""
        classifier = TenderClassifier()
        classification = classifier.classify_tender(
            tender_id="T003",
            tenderer="测试公司",
            region="北京",
            industry="IT",
            amount=None
        )
        assert classification.amount_category is None

    def test_classification_types(self):
        """测试分类类型枚举"""
        assert ClassificationType.TENDERER.value == "tenderer"
        assert ClassificationType.REGION.value == "region"
        assert ClassificationType.INDUSTRY.value == "industry"
        assert ClassificationType.AMOUNT.value == "amount"


class TestClassificationMetadata:
    """测试分类元数据"""

    def test_metadata_defaults_to_empty_dict(self):
        """测试元数据默认为空字典"""
        result = ClassificationResult(
            original_value="测试",
            normalized_value="测试",
            category="测试",
            confidence=0.8,
            classification_type=ClassificationType.TENDERER
        )
        assert result.metadata == {}

    def test_metadata_stores_additional_info(self):
        """测试元数据存储额外信息"""
        result = ClassificationResult(
            original_value="测试",
            normalized_value="测试",
            category="测试",
            confidence=0.8,
            classification_type=ClassificationType.TENDERER,
            metadata={"source": "manual", "version": "1.0"}
        )
        assert result.metadata["source"] == "manual"
        assert result.metadata["version"] == "1.0"
