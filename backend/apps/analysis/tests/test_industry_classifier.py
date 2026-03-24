"""
Industry Classification Tests - Phase 5 Task 024
Tests for automatic industry classification based on tender content.
"""

import pytest
from unittest.mock import Mock, patch


class TestIndustryClassifierExists:
    """Test 1: IndustryClassifier class exists"""

    def test_industry_classifier_class_exists(self):
        """IndustryClassifier class should exist"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier
        assert IndustryClassifier is not None

    def test_industry_classifier_has_classify_method(self):
        """IndustryClassifier should have classify method"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier
        assert hasattr(IndustryClassifier, 'classify')


class TestHealthcareIndustryClassification:
    """Test 2: Healthcare industry recognition"""

    def test_classify_healthcare_industry(self):
        """Should identify healthcare industry from medical equipment tender"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = """
        某市人民医院CT设备采购项目招标公告
        采购内容：64排螺旋CT 1台，用于放射科诊断
        预算金额：800万元
        """

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "医疗健康"
        assert result['confidence'] > 0.80

    def test_classify_hospital_construction(self):
        """Should identify healthcare from hospital construction project"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某三甲医院新院区建设项目，包含住院楼、门诊楼建设"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "医疗健康"


class TestITIndustryClassification:
    """Test 3: IT/Technology industry recognition"""

    def test_classify_it_industry(self):
        """Should identify IT industry from software development tender"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = """
        某市政府智慧政务平台建设项目招标公告
        采购内容：政务云平台软件开发服务
        技术要求：云计算、大数据、微服务架构
        """

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "信息技术"
        assert result['confidence'] > 0.80

    def test_classify_cybersecurity(self):
        """Should identify IT industry from cybersecurity project"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某单位网络安全等级保护建设项目，包含防火墙、入侵检测系统"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "信息技术"


class TestConstructionIndustryClassification:
    """Test 4: Construction industry recognition"""

    def test_classify_construction_industry(self):
        """Should identify construction industry from building project"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = """
        某学校教学楼新建工程招标公告
        建设内容：教学楼土建、装修、机电安装
        建筑面积：15000平方米
        """

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "建筑工程"
        assert result['confidence'] > 0.80

    def test_classify_infrastructure(self):
        """Should identify construction from infrastructure project"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某市地铁3号线土建工程招标，包含隧道、站点建设"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "建筑工程"


class TestEnergyIndustryClassification:
    """Test 5: Energy and environmental industry"""

    def test_classify_energy_industry(self):
        """Should identify energy industry"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某风电场设备采购项目，包含风力发电机组、变压器"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "能源环保"

    def test_classify_environmental(self):
        """Should identify environmental industry"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某污水处理厂升级改造项目，日处理量10万吨"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "能源环保"


class TestTransportationIndustryClassification:
    """Test 6: Transportation and logistics industry"""

    def test_classify_transportation(self):
        """Should identify transportation industry"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某机场航站楼智能交通系统建设，包含航班信息显示、行李处理系统"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "交通物流"


class TestEducationIndustryClassification:
    """Test 7: Education and research industry"""

    def test_classify_education(self):
        """Should identify education industry"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某大学实验室设备采购项目，包含显微镜、离心机、PCR仪"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "教育科研"


class TestFinanceIndustryClassification:
    """Test 8: Finance and insurance industry"""

    def test_classify_finance(self):
        """Should identify finance industry"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某银行核心系统升级项目，包含服务器、存储设备、网络设备"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "金融保险"


class TestManufacturingIndustryClassification:
    """Test 9: Manufacturing industry"""

    def test_classify_manufacturing(self):
        """Should identify manufacturing industry"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某汽车厂自动化生产线改造项目，包含工业机器人、数控机床"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] == "制造业"


class TestAmbiguousContent:
    """Test 10: Handle ambiguous content"""

    def test_handle_ambiguous_industry(self):
        """Should handle industry-ambiguous text"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "本项目欢迎各供应商参与投标"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['industry'] is None
        assert result['confidence'] < 0.50

    def test_empty_text(self):
        """Should handle empty text"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        classifier = IndustryClassifier()
        result = classifier.classify("")

        assert result['industry'] is None
        assert result['confidence'] == 0.0


class TestMixedIndustryContent:
    """Test 11: Multi-industry content classification"""

    def test_classify_mixed_content(self):
        """Should classify mixed industry content"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = """
        智慧医院信息化建设项目
        包含：医疗设备采购、软件系统开发、网络基础设施建设
        """

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        # Should identify primary industry
        assert result['industry'] in ["医疗健康", "信息技术"]
        assert result['confidence'] > 0.60

    def test_secondary_industries(self):
        """Should return secondary industries"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "智慧医院信息化建设项目，医疗设备与软件开发"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert 'secondary_industries' in result
        assert isinstance(result['secondary_industries'], list)


class TestIndustryKeywordsMatched:
    """Test 12: Return matched keywords"""

    def test_return_matched_keywords(self):
        """Should return matched industry keywords"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某医院CT设备采购项目"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert 'keywords_matched' in result
        assert isinstance(result['keywords_matched'], list)
        assert len(result['keywords_matched']) > 0


class TestIndustryCode:
    """Test 13: Industry code mapping"""

    def test_industry_code_mapping(self):
        """Should return industry code"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某医院CT设备采购项目"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert 'industry_code' in result
        assert result['industry_code'] is not None


class TestIndustryConfidence:
    """Test 14: Confidence score calculation"""

    def test_confidence_range(self):
        """Confidence should be between 0 and 1"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某医院信息化建设项目"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert 0.0 <= result['confidence'] <= 1.0

    def test_high_confidence_for_clear_match(self):
        """High confidence for clear industry match"""
        from apps.analysis.classifiers.industry_classifier import IndustryClassifier

        text = "某市人民医院64排CT设备采购项目"

        classifier = IndustryClassifier()
        result = classifier.classify(text)

        assert result['confidence'] > 0.80
