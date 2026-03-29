"""
FieldExtractorTool 测试

TDD 循环 5: 测试字段提取工具
重点测试招标人提取准确性
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any
from datetime import datetime

from apps.crawler.tools.field_extractor_tool import (
    FieldExtractorTool,
    FieldExtractionResult,
    field_extract_tool,
)
from apps.crawler.agents.schema import TenderNoticeSchema


class TestFieldExtractionResult:
    """FieldExtractionResult 测试"""

    def test_default_values(self):
        """测试默认值"""
        schema = Mock(spec=TenderNoticeSchema)
        result = FieldExtractionResult(
            schema=schema,
            success=True,
            extraction_method='llm',
            confidence=0.8,
        )

        assert result.success is True
        assert result.extraction_method == 'llm'
        assert result.confidence == 0.8
        assert result.missing_fields == []
        assert result.warnings == []
        assert result.error_message is None

    def test_to_dict(self):
        """测试转换为字典"""
        schema = Mock(spec=TenderNoticeSchema)
        schema.title = "招标公告"
        schema.tenderer = "测试公司"
        schema.budget_amount = 1000000

        result = FieldExtractionResult(
            schema=schema,
            success=True,
            extraction_method='llm+regex',
            confidence=0.85,
            field_confidences={'title': 0.9, 'tenderer': 0.8},
            missing_fields=['contact_phone'],
            warnings=['Missing contact_phone'],
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["success"] is True
        assert result_dict["extraction_method"] == 'llm+regex'
        assert result_dict["confidence"] == 0.85
        assert result_dict["field_confidences"]['title'] == 0.9
        assert 'data' in result_dict
        assert result_dict['data']['title'] == "招标公告"

    def test_quality_levels(self):
        """测试质量等级判断"""
        schema = Mock(spec=TenderNoticeSchema)

        # 高质量
        high = FieldExtractionResult(
            schema=schema, success=True, extraction_method='llm', confidence=0.85
        )
        assert high.is_high_quality() is True
        assert high.is_medium_quality() is False
        assert high.is_low_quality() is False

        # 中质量
        medium = FieldExtractionResult(
            schema=schema, success=True, extraction_method='llm', confidence=0.7
        )
        assert medium.is_high_quality() is False
        assert medium.is_medium_quality() is True
        assert medium.is_low_quality() is False

        # 低质量
        low = FieldExtractionResult(
            schema=schema, success=True, extraction_method='llm', confidence=0.5
        )
        assert low.is_high_quality() is False
        assert low.is_medium_quality() is False
        assert low.is_low_quality() is True


class TestFieldExtractorTool:
    """FieldExtractorTool 测试"""

    def test_initialization(self):
        """测试初始化"""
        tool = FieldExtractorTool()

        assert tool.agent is not None
        assert tool.config is not None
        assert len(tool.TENDERER_PATTERNS) > 0

    def test_clean_tenderer(self):
        """测试招标人名称清洗"""
        tool = FieldExtractorTool()

        # 测试去除多余空白
        assert tool._clean_tenderer("  测试  公司  ") == "测试 公司"

        # 测试去除后缀
        assert "联系人" not in tool._clean_tenderer("测试公司 联系人：张三")

        # 测试去除 HTML 标签
        assert tool._clean_tenderer("<b>测试公司</b>") == "测试公司"

    def test_is_valid_tenderer(self):
        """测试招标人名称验证"""
        tool = FieldExtractorTool()

        # 有效名称
        assert tool._is_valid_tenderer("北京市政府采购中心") is True
        assert tool._is_valid_tenderer("某某科技有限公司") is True

        # 无效名称 - 太短
        assert tool._is_valid_tenderer("无") is False

        # 无效名称 - 太长
        assert tool._is_valid_tenderer("A" * 101) is False

        # 无效名称 - 常见无效值
        assert tool._is_valid_tenderer("详见") is False

    def test_calculate_tenderer_confidence(self):
        """测试招标人置信度计算"""
        tool = FieldExtractorTool()
        content = "北京市政府采购中心联系人张三"

        # 测试包含关键词
        conf = tool._calculate_tenderer_confidence("北京市政府采购中心", content)
        assert conf > 0.6

        # 测试不含关键词
        conf = tool._calculate_tenderer_confidence("某某", content)
        assert conf < 0.6

    def test_extract_tenderer_enhanced(self):
        """测试增强的招标人提取"""
        tool = FieldExtractorTool()

        # 标准格式
        content1 = "采购人：北京市政府采购中心\n联系人：张三"
        assert "北京市政府采购中心" == tool._extract_tenderer_enhanced(content1)

        # 带空格格式
        content2 = "采 购 人：某某科技有限公司\n联系电话：12345678"
        assert "某某科技有限公司" == tool._extract_tenderer_enhanced(content2)

        # 招标人格式
        content3 = "招标人：中国电力研究院"
        assert "中国电力研究院" == tool._extract_tenderer_enhanced(content3)

        # 无匹配
        content4 = "这是一段无关内容"
        assert tool._extract_tenderer_enhanced(content4) is None

    def test_extract_contact_person_enhanced(self):
        """测试增强的联系人提取"""
        tool = FieldExtractorTool()

        content = "联系人：张三\n联系电话：010-12345678"
        assert tool._extract_contact_person_enhanced(content) == "张三"

    def test_extract_contact_phone_enhanced(self):
        """测试增强的电话提取"""
        tool = FieldExtractorTool()

        content = "联系电话：010-12345678"
        assert tool._extract_contact_phone_enhanced(content) == "010-12345678"

    def test_extract_project_number_enhanced(self):
        """测试增强的项目编号提取"""
        tool = FieldExtractorTool()

        content = "项目编号：BJZC-2024-001"
        assert tool._extract_project_number_enhanced(content) == "BJZC-2024-001"

    def test_calculate_overall_confidence(self):
        """测试整体置信度计算"""
        tool = FieldExtractorTool()

        field_confidences = {
            'title': 0.9,
            'tenderer': 0.8,
            'budget_amount': 0.7,
        }

        confidence = tool._calculate_overall_confidence(field_confidences)
        assert 0.0 < confidence <= 1.0

    def test_identify_missing_fields(self):
        """测试识别缺失字段"""
        tool = FieldExtractorTool()

        schema = Mock(spec=TenderNoticeSchema)
        schema.title = "招标公告"
        schema.tenderer = None
        schema.budget_amount = 1000
        schema.publish_date = None

        missing = tool._identify_missing_fields(schema)

        assert 'tenderer' in missing
        assert 'publish_date' in missing
        assert 'title' not in missing
        assert 'budget_amount' not in missing

    @pytest.mark.asyncio
    async def test_extract_success(self):
        """测试成功提取"""
        # 创建带属性的 Mock schema
        mock_schema = Mock(spec=TenderNoticeSchema)
        mock_schema.title = "招标公告"
        mock_schema.tenderer = "测试公司"
        mock_schema.budget_amount = 100000
        mock_schema.publish_date = None
        mock_schema.extraction_confidence = 0.75

        tool = FieldExtractorTool()

        with patch.object(
            tool.agent, "extract", new_callable=AsyncMock, return_value=mock_schema
        ):
            result = await tool.extract(
                html="<html>招标公告内容</html>",
                url="http://example.com/tender/1",
            )

            assert result.success is True
            assert result.extraction_method in ['llm', 'llm+regex', 'fallback']
            assert result.schema is not None

    @pytest.mark.asyncio
    async def test_extract_with_enhanced_tenderer(self):
        """测试增强招标人提取"""
        # 创建带属性的 Mock schema，tenderer 为 None
        mock_schema = Mock(spec=TenderNoticeSchema)
        mock_schema.title = "招标公告"
        mock_schema.tenderer = None  # LLM 没有提取到
        mock_schema.budget_amount = 100000
        mock_schema.publish_date = None
        mock_schema.extraction_confidence = 0.6

        html = "<html>采购人：北京市政府采购中心</html>"

        tool = FieldExtractorTool()

        with patch.object(
            tool.agent, "extract", new_callable=AsyncMock, return_value=mock_schema
        ):
            result = await tool.extract(
                html=html,
                url="http://example.com/tender/1",
                use_enhanced_tenderer=True,
            )

            # 验证招标人被补充提取
            assert result.schema is not None
            assert result.schema.tenderer == "北京市政府采购中心"
            assert result.extraction_method == 'llm+regex'

    @pytest.mark.asyncio
    async def test_extract_failure(self):
        """测试提取失败"""
        tool = FieldExtractorTool()

        with patch.object(
            tool.agent, "extract", new_callable=AsyncMock, side_effect=Exception("LLM error")
        ):
            with patch.object(
                tool.agent, "extract_from_text", new_callable=AsyncMock, side_effect=Exception("Fallback error")
            ):
                result = await tool.extract(
                    html="<html>内容</html>",
                    url="http://example.com/tender/1",
                )

                assert result.success is False
                assert result.error_message is not None

    @pytest.mark.asyncio
    async def test_extract_from_text_success(self):
        """测试从文本提取成功"""
        # 创建带属性的 Mock schema
        mock_schema = Mock(spec=TenderNoticeSchema)
        mock_schema.title = "PDF招标公告"
        mock_schema.tenderer = "测试公司"
        mock_schema.budget_amount = 100000
        mock_schema.publish_date = None
        mock_schema.extraction_confidence = 0.7

        tool = FieldExtractorTool()

        with patch.object(
            tool.agent, "extract_from_text", new_callable=AsyncMock, return_value=mock_schema
        ):
            result = await tool.extract_from_text(
                text="PDF文本内容",
                url="http://example.com/doc.pdf",
            )

            assert result.success is True
            assert result.extraction_method == 'llm_text+regex'


class TestFieldExtractToolFunction:
    """field_extract_tool 函数测试"""

    @pytest.mark.asyncio
    async def test_tool_function(self):
        """测试工具函数"""
        mock_schema = Mock(spec=TenderNoticeSchema)
        mock_schema.title = "招标公告"
        mock_schema.tenderer = "测试公司"
        mock_schema.budget_amount = 1000000

        with patch(
            "apps.crawler.tools.field_extractor_tool.FieldExtractorTool.extract",
            new_callable=AsyncMock,
        ) as mock_extract:
            mock_extract.return_value = FieldExtractionResult(
                schema=mock_schema,
                success=True,
                extraction_method='llm',
                confidence=0.85,
            )

            result = await field_extract_tool(
                html="<html>内容</html>",
                url="http://example.com/tender/1",
                use_enhanced=True,
            )

            assert isinstance(result, dict)
            assert result["success"] is True
            assert result["confidence"] == 0.85


class TestFieldExtractorToolIntegration:
    """FieldExtractorTool 集成测试"""

    def test_tenderer_accuracy_improvement(self):
        """测试招标人提取准确性提升"""
        tool = FieldExtractorTool()

        # 测试用例：各种格式的招标人
        test_cases = [
            ("采购人：北京市政府采购中心", "北京市政府采购中心"),
            ("招标人：中国科学院", "中国科学院"),
            ("采 购 人：某某医院", "某某医院"),
            ("采购单位：某某大学", "某某大学"),
            ("招标单位：某某公司", "某某公司"),
        ]

        for content, expected in test_cases:
            result = tool._extract_tenderer_enhanced(content)
            assert result == expected, f"Failed for: {content}"

    def test_confidence_calculation_accuracy(self):
        """测试置信度计算准确性"""
        tool = FieldExtractorTool()

        # 高质量字段
        high_confidences = {
            'title': 0.9,
            'tenderer': 0.85,
            'budget_amount': 0.8,
            'publish_date': 0.9,
        }
        high_overall = tool._calculate_overall_confidence(high_confidences)
        assert high_overall >= 0.8

        # 低质量字段
        low_confidences = {
            'title': 0.5,
            'tenderer': 0.4,
        }
        low_overall = tool._calculate_overall_confidence(low_confidences)
        assert low_overall < 0.6

    @pytest.mark.asyncio
    async def test_full_extraction_workflow(self):
        """测试完整提取流程"""
        # 创建带完整属性的 Mock
        mock_schema = Mock(spec=TenderNoticeSchema)
        mock_schema.title = "<h1>政府采购项目招标公告</h1>"
        mock_schema.tenderer = None  # 待补充
        mock_schema.budget_amount = 5000000
        mock_schema.publish_date = datetime.now()
        mock_schema.extraction_confidence = 0.6

        html = """
        <html>
        <h1>政府采购项目招标公告</h1>
        <p>采购人：北京市政府采购中心</p>
        <p>预算金额：500万元</p>
        <p>联系人：张三</p>
        <p>联系电话：010-12345678</p>
        </html>
        """

        tool = FieldExtractorTool()

        with patch.object(
            tool.agent, "extract", new_callable=AsyncMock, return_value=mock_schema
        ):
            result = await tool.extract(html, "http://example.com/tender/1")

            assert result.success is True
            # HTML title 包含标签，但 tenderer 应该被补充
            assert result.schema.tenderer == "北京市政府采购中心"

            # 验证置信度
            assert 'tenderer' in result.field_confidences
            assert result.field_confidences['tenderer'] > 0.6

            # 验证质量等级
            assert result.is_high_quality() or result.is_medium_quality()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
