"""
数据验证和清洗系统测试

TDD Cycle 24: 招标数据验证和清洗系统
- 招标数据验证（标题、金额、日期、URL 等字段验证）
- 数据清洗（去除 HTML 标签、标准化格式、去重）
- 数据转换（货币格式统一、日期格式统一）
- 验证规则配置（可配置的验证规则）
- 批量验证和清洗
- 验证报告生成
"""
import pytest
import re
from decimal import Decimal
from datetime import datetime, date
from typing import Dict, Any, List

from apps.crawler.tools.data_validator import (
    ValidationResult,
    ValidationError,
    TenderValidator,
    TenderCleaner,
    TenderTransformer,
    ValidationConfig,
    BatchProcessor,
    ValidationReport,
)


class TestValidationResult:
    """测试验证结果类"""

    def test_validation_result_success(self):
        """测试成功的验证结果"""
        result = ValidationResult(is_valid=True, errors=[])
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.error_count == 0

    def test_validation_result_with_errors(self):
        """测试有错误的验证结果"""
        errors = [
            ValidationError(field="title", message="标题不能为空", code="REQUIRED"),
            ValidationError(field="budget_amount", message="金额不能为负", code="INVALID_RANGE"),
        ]
        result = ValidationResult(is_valid=False, errors=errors)
        assert result.is_valid is False
        assert result.error_count == 2

    def test_validation_result_to_dict(self):
        """测试验证结果转字典"""
        errors = [
            ValidationError(field="title", message="标题不能为空", code="REQUIRED"),
        ]
        result = ValidationResult(is_valid=False, errors=errors)
        result_dict = result.to_dict()
        assert result_dict["is_valid"] is False
        assert len(result_dict["errors"]) == 1
        assert result_dict["errors"][0]["field"] == "title"


class TestValidationError:
    """测试验证错误类"""

    def test_validation_error_creation(self):
        """测试验证错误创建"""
        error = ValidationError(
            field="title",
            message="标题不能为空",
            code="REQUIRED",
            value=None
        )
        assert error.field == "title"
        assert error.message == "标题不能为空"
        assert error.code == "REQUIRED"

    def test_validation_error_to_dict(self):
        """测试验证错误转字典"""
        error = ValidationError(
            field="title",
            message="标题不能为空",
            code="REQUIRED",
            value="test"
        )
        error_dict = error.to_dict()
        assert error_dict["field"] == "title"
        assert error_dict["message"] == "标题不能为空"
        assert error_dict["code"] == "REQUIRED"
        assert error_dict["value"] == "test"


class TestValidationConfig:
    """测试验证配置类"""

    def test_default_config(self):
        """测试默认配置"""
        config = ValidationConfig()
        assert config.title_min_length == 5
        assert config.title_max_length == 200
        assert config.budget_min == Decimal("0")
        assert config.budget_max == Decimal("999999999999")
        assert config.required_fields == ["title"]

    def test_custom_config(self):
        """测试自定义配置"""
        config = ValidationConfig(
            title_min_length=10,
            title_max_length=200,
            required_fields=["title", "tenderer", "budget_amount"],
            allow_html_tags=False
        )
        assert config.title_min_length == 10
        assert config.title_max_length == 200
        assert "budget_amount" in config.required_fields


class TestTenderValidator:
    """测试招标数据验证器"""

    def test_validate_valid_tender(self):
        """测试验证有效的数据"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目",
            "tenderer": "某省政府采购中心",
            "budget_amount": 1000000,
            "budget_unit": "元",
            "publish_date": "2024-01-15",
            "source_url": "https://example.com/tender/123",
        }
        result = validator.validate(tender_data)
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_validate_missing_title(self):
        """测试缺少标题验证"""
        validator = TenderValidator()
        tender_data = {
            "tenderer": "某省政府采购中心",
            "budget_amount": 1000000,
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.field == "title" for e in result.errors)

    def test_validate_title_too_short(self):
        """测试标题太短"""
        validator = TenderValidator()
        tender_data = {
            "title": "招标",
            "tenderer": "某省政府采购中心",
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "TITLE_TOO_SHORT" for e in result.errors)

    def test_validate_title_too_long(self):
        """测试标题太长"""
        validator = TenderValidator()
        tender_data = {
            "title": "项目" * 150,  # 300 字符，超过 200 限制
            "tenderer": "某省政府采购中心",
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "TITLE_TOO_LONG" for e in result.errors)

    def test_validate_negative_budget(self):
        """测试负金额验证"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目",
            "budget_amount": -1000,
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "BUDGET_NEGATIVE" for e in result.errors)

    def test_validate_budget_too_large(self):
        """测试金额过大验证"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目",
            "budget_amount": Decimal("99999999999999"),
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "BUDGET_TOO_LARGE" for e in result.errors)

    def test_validate_invalid_url(self):
        """测试无效 URL 验证"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目",
            "source_url": "not-a-valid-url",
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "INVALID_URL" for e in result.errors)

    def test_validate_valid_url(self):
        """测试有效 URL 验证"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目",
            "source_url": "https://www.example.com/tender/123",
        }
        result = validator.validate(tender_data)
        # URL 格式正确应该不报错
        assert not any(e.code == "INVALID_URL" for e in result.errors)

    def test_validate_invalid_date_format(self):
        """测试无效日期格式"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目",
            "publish_date": "not-a-date",
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "INVALID_DATE_FORMAT" for e in result.errors)

    def test_validate_future_date(self):
        """测试未来日期验证"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目",
            "publish_date": "2099-12-31",
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "DATE_TOO_FAR_FUTURE" for e in result.errors)

    def test_validate_invalid_phone(self):
        """测试无效电话验证"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目",
            "contact_phone": "123",
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "INVALID_PHONE" for e in result.errors)

    def test_validate_valid_phone(self):
        """测试有效电话验证"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目",
            "contact_phone": "010-12345678",
        }
        result = validator.validate(tender_data)
        assert not any(e.code == "INVALID_PHONE" for e in result.errors)

    def test_validate_custom_rules(self):
        """测试自定义验证规则"""
        config = ValidationConfig(
            title_min_length=10,
            required_fields=["title", "tenderer", "budget_amount"]
        )
        validator = TenderValidator(config)
        tender_data = {
            "title": "短标题",
            "tenderer": "测试单位",
            "budget_amount": 1000,
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "TITLE_TOO_SHORT" for e in result.errors)

    def test_validate_empty_data(self):
        """测试空数据验证"""
        validator = TenderValidator()
        result = validator.validate({})
        assert result.is_valid is False
        assert len(result.errors) > 0

    def test_validate_none_data(self):
        """测试 None 数据验证"""
        validator = TenderValidator()
        result = validator.validate(None)
        assert result.is_valid is False


class TestTenderCleaner:
    """测试招标数据清洗器"""

    def test_clean_html_tags(self):
        """测试去除 HTML 标签"""
        cleaner = TenderCleaner()
        dirty_text = "<p>这是<strong>招标</strong>公告</p>"
        clean_text = cleaner.clean_html_tags(dirty_text)
        assert clean_text == "这是招标公告"
        assert "<" not in clean_text
        assert ">" not in clean_text

    def test_clean_html_tags_with_entities(self):
        """测试去除 HTML 实体"""
        cleaner = TenderCleaner()
        dirty_text = "&lt;script&gt;alert('xss')&lt;/script&gt;"
        clean_text = cleaner.clean_html_tags(dirty_text)
        assert "&lt;" not in clean_text
        assert "&gt;" not in clean_text

    def test_clean_whitespace(self):
        """测试空白字符清洗"""
        cleaner = TenderCleaner()
        dirty_text = "招标    项目\n\n公告"
        clean_text = cleaner.clean_whitespace(dirty_text)
        assert "    " not in clean_text
        assert "\n\n" not in clean_text

    def test_clean_special_chars(self):
        """测试特殊字符清洗"""
        cleaner = TenderCleaner()
        dirty_text = "招标\u200b项目\u3000公告"
        clean_text = cleaner.clean_special_chars(dirty_text)
        assert "\u200b" not in clean_text
        assert "\u3000" not in clean_text

    def test_clean_tender_data(self):
        """测试清洗招标数据"""
        cleaner = TenderCleaner()
        dirty_data = {
            "title": "<p>某省政府<strong>招标</strong>采购项目</p>",
            "description": "项目描述\n\n包含多个   空格",
            "tenderer": "某省\u200b政府采购中心",
        }
        cleaned = cleaner.clean_tender_data(dirty_data)
        assert "<p>" not in cleaned["title"]
        assert "<strong>" not in cleaned["title"]
        assert "\n\n" not in cleaned["description"]
        assert "\u200b" not in cleaned["tenderer"]

    def test_clean_empty_strings(self):
        """测试空字符串处理"""
        cleaner = TenderCleaner()
        data = {
            "title": "  ",
            "description": None,
            "tenderer": "",
        }
        cleaned = cleaner.clean_tender_data(data)
        assert cleaned.get("title") is None or cleaned["title"] == ""
        assert cleaned.get("description") is None

    def test_normalize_company_name(self):
        """测试企业名称标准化"""
        cleaner = TenderCleaner()
        name = "  某省政府采购中心 "
        normalized = cleaner.normalize_company_name(name)
        assert normalized == "某省政府采购中心"

    def test_normalize_company_name_with_suffix(self):
        """测试带后缀的企业名称标准化"""
        cleaner = TenderCleaner()
        names = [
            "某省政府采购中心",
            "某省政府采购中心有限公司",
            "某省政府采购中心股份有限公司",
        ]
        for name in names:
            normalized = cleaner.normalize_company_name(name)
            assert normalized is not None


class TestTenderTransformer:
    """测试招标数据转换器"""

    def test_transform_budget_unit_yuan(self):
        """测试元单位转换"""
        transformer = TenderTransformer()
        result = transformer.transform_budget("10000", "元")
        assert result == Decimal("10000")
        assert result >= 0

    def test_transform_budget_unit_wan(self):
        """测试万元单位转换"""
        transformer = TenderTransformer()
        result = transformer.transform_budget("100", "万元")
        assert result == Decimal("1000000")

    def test_transform_budget_unit_yi(self):
        """测试亿元单位转换"""
        transformer = TenderTransformer()
        result = transformer.transform_budget("1", "亿元")
        assert result == Decimal("100000000")

    def test_transform_budget_invalid(self):
        """测试无效金额转换"""
        transformer = TenderTransformer()
        result = transformer.transform_budget("invalid", "元")
        assert result is None

    def test_transform_budget_with_symbols(self):
        """测试带符号金额转换"""
        transformer = TenderTransformer()
        result = transformer.transform_budget("￥100,000", "元")
        assert result == Decimal("100000")

    def test_transform_date_iso_format(self):
        """测试 ISO 格式日期转换"""
        transformer = TenderTransformer()
        result = transformer.transform_date("2024-01-15")
        assert isinstance(result, datetime)

    def test_transform_date_chinese_format(self):
        """测试中文格式日期转换"""
        transformer = TenderTransformer()
        result = transformer.transform_date("2024年01月15日")
        assert isinstance(result, datetime)
        assert result.year == 2024
        assert result.month == 1
        assert result.day == 15

    def test_transform_date_slash_format(self):
        """测试斜杠格式日期转换"""
        transformer = TenderTransformer()
        result = transformer.transform_date("2024/01/15")
        assert isinstance(result, datetime)
        assert result.year == 2024

    def test_transform_date_invalid(self):
        """测试无效日期转换"""
        transformer = TenderTransformer()
        result = transformer.transform_date("invalid-date")
        assert result is None

    def test_transform_full_tender_data(self):
        """测试完整数据转换"""
        transformer = TenderTransformer()
        data = {
            "title": "招标项目",
            "budget_amount": "100",
            "budget_unit": "万元",
            "publish_date": "2024年01月15日",
            "source_url": "https://example.com",
        }
        transformed = transformer.transform_tender_data(data)
        assert transformed["budget_amount"] == Decimal("1000000")
        assert isinstance(transformed["publish_date"], datetime)

    def test_normalize_url(self):
        """测试 URL 标准化"""
        transformer = TenderTransformer()
        url = "  https://example.com/tender  "
        normalized = transformer.normalize_url(url)
        assert normalized == "https://example.com/tender"

    def test_normalize_phone(self):
        """测试电话标准化"""
        transformer = TenderTransformer()
        phone = " 010-12345678 "
        normalized = transformer.normalize_phone(phone)
        assert normalized == "010-12345678"


class TestBatchProcessor:
    """测试批量处理器"""

    def test_batch_validate_multiple(self):
        """测试批量验证多个数据"""
        processor = BatchProcessor()
        tenders = [
            {"title": "有效招标1", "tenderer": "单位1"},
            {"title": "", "tenderer": "单位2"},  # 无效
            {"title": "有效招标3", "tenderer": "单位3"},
        ]
        results = processor.batch_validate(tenders)
        assert len(results) == 3
        assert results[0].is_valid is True
        assert results[1].is_valid is False
        assert results[2].is_valid is True

    def test_batch_clean_multiple(self):
        """测试批量清洗多个数据"""
        processor = BatchProcessor()
        tenders = [
            {"title": "<p>招标1</p>", "description": "  描述  "},
            {"title": "招标2", "description": "<b>描述</b>"},
        ]
        cleaned = processor.batch_clean(tenders)
        assert len(cleaned) == 2
        assert "<p>" not in cleaned[0]["title"]
        assert "  " not in cleaned[0]["description"]

    def test_batch_transform_multiple(self):
        """测试批量转换多个数据"""
        processor = BatchProcessor()
        tenders = [
            {"title": "招标1", "budget_amount": "100", "budget_unit": "万元"},
            {"title": "招标2", "budget_amount": "200", "budget_unit": "万元"},
        ]
        transformed = processor.batch_transform(tenders)
        assert len(transformed) == 2
        assert transformed[0]["budget_amount"] == Decimal("1000000")
        assert transformed[1]["budget_amount"] == Decimal("2000000")

    def test_batch_process_full_pipeline(self):
        """测试完整流水线处理"""
        processor = BatchProcessor()
        tenders = [
            {
                "title": "  <p>某省政府招标项目</p>  ",
                "budget_amount": "100",
                "budget_unit": "万元",
                "publish_date": "2024年01月15日",
                "source_url": "https://example.com/1",
            },
            {
                "title": "",  # 无效
                "budget_amount": "-100",  # 无效
            },
        ]
        processed = processor.process_batch(tenders)
        assert len(processed) == 2
        # 第一个应该有效
        assert processed[0]["validation_result"].is_valid is True
        # 第二个应该无效
        assert processed[1]["validation_result"].is_valid is False


class TestValidationReport:
    """测试验证报告生成"""

    def test_generate_report_empty(self):
        """测试生成空报告"""
        report = ValidationReport()
        results = []
        report_data = report.generate_report(results)
        assert report_data["total"] == 0
        assert report_data["valid_count"] == 0
        assert report_data["invalid_count"] == 0
        assert report_data["valid_rate"] == 0

    def test_generate_report_mixed(self):
        """测试生成混合结果报告"""
        report = ValidationReport()
        results = [
            ValidationResult(is_valid=True, errors=[]),
            ValidationResult(is_valid=False, errors=[
                ValidationError("title", "错误", "REQUIRED")
            ]),
            ValidationResult(is_valid=True, errors=[]),
        ]
        report_data = report.generate_report(results)
        assert report_data["total"] == 3
        assert report_data["valid_count"] == 2
        assert report_data["invalid_count"] == 1
        assert report_data["valid_rate"] == pytest.approx(2/3 * 100)

    def test_generate_report_error_summary(self):
        """测试生成错误摘要"""
        report = ValidationReport()
        results = [
            ValidationResult(is_valid=False, errors=[
                ValidationError("title", "标题不能为空", "REQUIRED"),
            ]),
            ValidationResult(is_valid=False, errors=[
                ValidationError("title", "标题太短", "TITLE_TOO_SHORT"),
                ValidationError("budget_amount", "金额无效", "INVALID"),
            ]),
        ]
        report_data = report.generate_report(results)
        assert "error_summary" in report_data
        assert report_data["error_summary"]["title"] == 2
        assert report_data["error_summary"]["budget_amount"] == 1


class TestEdgeCases:
    """测试边界情况"""

    def test_validate_unicode_title(self):
        """测试 Unicode 标题验证"""
        validator = TenderValidator()
        tender_data = {
            "title": "某省政府招标采购项目（中文）",
            "tenderer": "采购中心",
        }
        result = validator.validate(tender_data)
        assert result.is_valid is True

    def test_validate_emoji_in_title(self):
        """测试标题包含 Emoji"""
        validator = TenderValidator()
        tender_data = {
            "title": "招标项目🌟公告",
            "tenderer": "采购中心",
        }
        result = validator.validate(tender_data)
        # Emoji 应该被接受
        assert result.is_valid is True

    def test_clean_extreme_whitespace(self):
        """测试极端空白字符"""
        cleaner = TenderCleaner()
        text = "\n\t\r  \n\t\r  招标  \n\t\r  \n\t\r"
        cleaned = cleaner.clean_whitespace(text)
        assert cleaned == "招标"

    def test_transform_large_budget(self):
        """测试大额转换"""
        transformer = TenderTransformer()
        result = transformer.transform_budget("9999", "亿元")
        assert result == Decimal("999900000000")

    def test_validate_confidence_range(self):
        """测试置信度范围验证"""
        validator = TenderValidator()
        tender_data = {
            "title": "招标项目",
            "extraction_confidence": 1.5,  # 无效
        }
        result = validator.validate(tender_data)
        assert result.is_valid is False
        assert any(e.code == "INVALID_CONFIDENCE" for e in result.errors)

    def test_validate_confidence_valid(self):
        """测试有效置信度"""
        validator = TenderValidator()
        tender_data = {
            "title": "招标项目",
            "extraction_confidence": 0.85,
        }
        result = validator.validate(tender_data)
        assert not any(e.code == "INVALID_CONFIDENCE" for e in result.errors)