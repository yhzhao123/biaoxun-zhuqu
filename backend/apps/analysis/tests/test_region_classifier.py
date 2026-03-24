"""
Region Classification Tests - Phase 5 Task 026
Tests for automatic region classification based on tender content.
"""

import pytest
from unittest.mock import Mock, patch


class TestRegionClassifierExists:
    """Test 1: RegionClassifier class exists"""

    def test_region_classifier_class_exists(self):
        """RegionClassifier class should exist"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier
        assert RegionClassifier is not None

    def test_region_classifier_has_classify_method(self):
        """RegionClassifier should have classify method"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier
        assert hasattr(RegionClassifier, 'classify')


class TestProvinceRegionClassification:
    """Test 2: Province-level region recognition"""

    def test_classify_province_region(self):
        """Should identify province from tender text"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = """
        广东省交通基础设施建设项目招标公告
        采购单位：广东省交通运输厅
        """

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "广东省"
        assert result['province_code'] == "440000"
        assert result['confidence'] > 0.85

    def test_classify_multiple_provinces(self):
        """Should identify province from various texts"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        test_cases = [
            ("北京市政务服务平台建设", "北京市"),
            ("江苏省人民医院设备采购", "江苏省"),
            ("浙江省杭州市智慧交通项目", "浙江省"),
            ("四川省成都市地铁建设", "四川省"),
        ]

        classifier = RegionClassifier()
        for text, expected_province in test_cases:
            result = classifier.classify(text)
            assert result['province'] == expected_province


class TestCityRegionClassification:
    """Test 3: City-level region recognition"""

    def test_classify_city_region(self):
        """Should identify city from tender text"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = """
        深圳市政务云平台建设项目
        采购单位：深圳市政务服务数据管理局
        """

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "广东省"
        assert result['city'] == "深圳市"
        assert result['city_code'] == "440300"
        assert result['confidence'] > 0.85

    def test_classify_major_cities(self):
        """Should identify major cities"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        test_cases = [
            ("上海市浦东新区项目", "上海市", "浦东新区"),
            ("广州市地铁建设", "广东省", "广州市"),
            ("武汉市医院采购", "湖北省", "武汉市"),
            ("西安市信息化项目", "陕西省", "西安市"),
        ]

        classifier = RegionClassifier()
        for text, expected_province, expected_city in test_cases:
            result = classifier.classify(text)
            assert result['province'] == expected_province
            assert result['city'] == expected_city


class TestDistrictRegionClassification:
    """Test 4: District-level region recognition"""

    def test_classify_district_region(self):
        """Should identify district from tender text"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = """
        杭州市西湖区智慧校园建设项目
        采购单位：杭州市西湖区教育局
        项目地点：西湖区文三路
        """

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "浙江省"
        assert result['city'] == "杭州市"
        assert result['district'] == "西湖区"
        assert result['district_code'] == "330106"
        assert result['confidence'] > 0.85


class TestAddressExtraction:
    """Test 5: Extract address from text"""

    def test_extract_address_from_text(self):
        """Should extract full address from text"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = """
        项目地点：江苏省南京市鼓楼区中山路1号
        交货地点：上海浦东新区张江高科技园区
        """

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "江苏省"
        assert result['city'] == "南京市"
        assert result['district'] == "鼓楼区"


class TestMultipleRegionsResolution:
    """Test 6: Handle multiple regions in text"""

    def test_resolve_multiple_regions(self):
        """Should resolve conflicts when multiple regions mentioned"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = """
        采购单位：北京市财政局
        项目地点：河北省石家庄市
        交货地点：天津市滨海新区
        """

        classifier = RegionClassifier()
        result = classifier.classify(text)

        # Should prioritize purchaser's region
        assert result['province'] == "北京市"
        assert 'mentioned_regions' in result


class TestRegionAliases:
    """Test 7: Region alias recognition"""

    def test_recognize_region_aliases(self):
        """Should recognize region aliases like 沪 for Shanghai"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = """
        沪上某医院医疗设备采购项目
        采购单位：申城医疗集团
        """

        classifier = RegionClassifier()
        result = classifier.classify(text)

        # "沪" and "申城" are aliases for Shanghai
        assert result['province'] == "上海市"

    def test_recognize_guangdong_alias(self):
        """Should recognize 粤 as Guangdong"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "粤北某市教育信息化项目"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "广东省"


class TestMunicipalities:
    """Test 8: Direct-controlled municipalities"""

    def test_beijing_municipality(self):
        """Should handle Beijing as municipality"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "北京市海淀区智慧城市建设项目"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "北京市"
        assert result['city'] == "北京市"  # Municipality
        assert result['district'] == "海淀区"

    def test_shanghai_municipality(self):
        """Should handle Shanghai as municipality"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "上海市浦东新区金融中心建设"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "上海市"
        assert result['city'] == "上海市"

    def test_tianjin_municipality(self):
        """Should handle Tianjin as municipality"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "天津市滨海新区港口建设"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "天津市"
        assert result['city'] == "天津市"

    def test_chongqing_municipality(self):
        """Should handle Chongqing as municipality"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "重庆市渝中区智慧交通项目"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "重庆市"
        assert result['city'] == "重庆市"


class TestAutonomousRegions:
    """Test 9: Autonomous regions"""

    def test_guangxi_autonomous_region(self):
        """Should handle Guangxi Zhuang Autonomous Region"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "广西南宁市轨道交通建设"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "广西壮族自治区"
        assert result['city'] == "南宁市"

    def test_inner_mongolia_autonomous_region(self):
        """Should handle Inner Mongolia Autonomous Region"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "内蒙古呼和浩特市数据中心建设"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] == "内蒙古自治区"


class TestConfidenceCalculation:
    """Test 10: Confidence score calculation"""

    def test_confidence_range(self):
        """Confidence should be between 0 and 1"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "某市信息化项目"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert 0.0 <= result['confidence'] <= 1.0

    def test_high_confidence_with_full_address(self):
        """Higher confidence with full address info"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "北京市海淀区中关村大街1号办公楼"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['confidence'] > 0.85


class TestEmptyAndInvalid:
    """Test 11: Handle empty and invalid text"""

    def test_empty_text(self):
        """Should handle empty text"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        classifier = RegionClassifier()
        result = classifier.classify("")

        assert result['province'] is None
        assert result['confidence'] == 0.0

    def test_no_region_text(self):
        """Should handle text with no region info"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "本项目欢迎各供应商参与投标"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert result['province'] is None
        assert result['confidence'] < 0.50


class TestRegionExtractionSource:
    """Test 12: Track extraction source"""

    def test_track_extraction_source(self):
        """Should track where region info was extracted from"""
        from apps.analysis.classifiers.region_classifier import RegionClassifier

        text = "北京市政府采购项目"

        classifier = RegionClassifier()
        result = classifier.classify(text)

        assert 'source' in result
        assert result['source'] in ['title', 'tenderer', 'address', 'keywords']
