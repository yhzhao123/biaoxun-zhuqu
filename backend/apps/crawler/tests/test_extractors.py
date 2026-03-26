"""
Tests for Intelligent Extractor and Extraction Pipeline
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

from apps.crawler.extractors.intelligent_extractor import IntelligentExtractor
from apps.crawler.extractors.pipeline import ExtractionPipeline, ExtractionResult


class TestIntelligentExtractor:
    """Tests for IntelligentExtractor"""

    @pytest.fixture
    def extractor(self):
        return IntelligentExtractor()

    def test_extract_title_from_h1(self, extractor):
        """Should extract title from h1 tag"""
        html = """
        <html>
            <head><title>Page Title</title></head>
            <body>
                <h1>招标公告：某项目采购</h1>
                <div class="content">Content here</div>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['title'] == '招标公告：某项目采购'

    def test_extract_title_with_keywords(self, extractor):
        """Should extract title with tender keywords"""
        html = """
        <html>
            <body>
                <h1>中标公告：某某项目采购</h1>
                <div class="content">内容</div>
            </body>
        </html>
        """
        result = extractor.extract(html)
        # Title extraction should find the h1
        assert result['title'] == '中标公告：某某项目采购'

    def test_extract_publish_date_chinese_format(self, extractor):
        """Should parse Chinese date format"""
        html = """
        <html>
            <body>
                <h1>招标公告</h1>
                <div class="date">发布时间：2024年01月15日</div>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['publish_date'] is not None
        assert result['publish_date'].year == 2024
        assert result['publish_date'].month == 1
        assert result['publish_date'].day == 15

    def test_extract_publish_date_iso_format(self, extractor):
        """Should parse ISO date format"""
        html = """
        <html>
            <body>
                <time datetime="2024-02-20">2024-02-20</time>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['publish_date'] is not None
        assert result['publish_date'].year == 2024
        assert result['publish_date'].month == 2

    def test_extract_budget_with_unit(self, extractor):
        """Should extract budget with unit conversion"""
        html = """
        <html>
            <body>
                <h1>招标公告</h1>
                <div class="budget">预算金额：100万元</div>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['budget'] is not None
        assert result['budget'] == Decimal('1000000')

    def test_extract_budget_yuan(self, extractor):
        """Should extract budget in yuan"""
        html = """
        <html>
            <body>
                <h1>招标公告</h1>
                <p>项目预算：¥500,000元</p>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['budget'] is not None
        assert result['budget'] == Decimal('500000')

    def test_extract_tenderer(self, extractor):
        """Should extract tenderer/purchaser"""
        html = """
        <html>
            <body>
                <h1>招标公告</h1>
                <p>采购人：某某市教育局</p>
                <p>联系人：张三</p>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['tenderer'] is not None
        assert '教育局' in result['tenderer']

    def test_extract_description(self, extractor):
        """Should extract content description"""
        html = """
        <html>
            <body>
                <article>
                    <h1>招标公告</h1>
                    <p>本项目为某某设备采购项目，预算金额为100万元。</p>
                    <p>详细需求如下...</p>
                </article>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['description'] is not None
        assert len(result['description']) > 10

    def test_empty_html(self, extractor):
        """Should handle empty HTML"""
        result = extractor.extract("")
        assert result == {}

    def test_analyze_page_structure(self, extractor):
        """Should analyze page structure"""
        html = """
        <html>
            <body>
                <article id="main-content" class="article">
                    <h1>Title</h1>
                    <time>2024-01-01</time>
                </article>
            </body>
        </html>
        """
        structure = extractor.analyze_page_structure(html)
        assert structure['has_article'] is True
        assert 'potential_selectors' in structure


class TestExtractionResult:
    """Tests for ExtractionResult"""

    def test_calculate_confidence_full(self):
        """Should calculate high confidence for full data"""
        data = {
            'title': '招标公告',
            'publish_date': datetime(2024, 1, 1),
            'budget': Decimal('100000'),
            'tenderer': '测试单位',
            'description': '测试描述',
            'extraction_method': 'intelligent'
        }
        result = ExtractionResult(data)
        assert result.confidence == 1.0
        assert result.is_valid()

    def test_calculate_confidence_partial(self):
        """Should calculate partial confidence"""
        data = {
            'title': '招标公告',
            'description': '测试描述',
            'extraction_method': 'intelligent'
        }
        result = ExtractionResult(data)
        assert 0 < result.confidence < 1
        assert result.is_valid()  # Still valid with title

    def test_calculate_confidence_no_title(self):
        """Should have low confidence without title"""
        data = {
            'description': '测试描述',
            'extraction_method': 'intelligent'
        }
        result = ExtractionResult(data)
        assert result.confidence < 0.3
        assert not result.is_valid()

    def test_properties(self):
        """Should expose data as properties"""
        data = {
            'title': '测试标题',
            'publish_date': datetime(2024, 1, 1),
            'budget': Decimal('100000'),
            'tenderer': '测试单位',
            'description': '测试描述',
            'extraction_method': 'intelligent'
        }
        result = ExtractionResult(data)
        assert result.title == '测试标题'
        assert result.publish_date == datetime(2024, 1, 1)
        assert result.budget == Decimal('100000')
        assert result.tenderer == '测试单位'
        assert result.description == '测试描述'


class TestExtractionPipeline:
    """Tests for ExtractionPipeline"""

    def test_pipeline_intelligent_extraction(self):
        """Should use intelligent extraction by default"""
        pipeline = ExtractionPipeline(use_llm=False, use_intelligent=True)

        html = """
        <html>
            <body>
                <h1>招标公告：某项目</h1>
                <time>2024-01-15</time>
            </body>
        </html>
        """

        result = pipeline.extract(html, source_url='http://example.com/test')
        assert result.extraction_method == 'intelligent'
        assert result.title == '招标公告：某项目'

    def test_pipeline_selector_fallback(self):
        """Should fallback to selectors when intelligent fails"""
        pipeline = ExtractionPipeline(use_llm=False, use_intelligent=False)

        html = """
        <html>
            <body>
                <h1 class="title">招标公告</h1>
                <div class="content">内容</div>
            </body>
        </html>
        """

        selectors = {
            'title': 'h1.title',
            'content': 'div.content'
        }

        result = pipeline.extract(html, selectors=selectors, source_url='http://example.com/test')
        assert result.extraction_method == 'selector'
        assert result.title == '招标公告'

    def test_pipeline_empty_html(self):
        """Should handle empty HTML gracefully"""
        pipeline = ExtractionPipeline(use_llm=False, use_intelligent=True)

        result = pipeline.extract("", source_url='http://example.com/test')
        assert result is not None
        assert result.confidence < 0.3

    @patch('apps.crawler.extractors.pipeline.get_llm_extractor')
    def test_pipeline_llm_extraction(self, mock_get_llm):
        """Should use LLM extraction when configured"""
        mock_llm = Mock()
        mock_llm.extract.return_value = {
            'title': 'LLM提取的标题',
            'tenderer': '采购单位',
            'budget': Decimal('100000'),
            'extraction_method': 'llm'
        }
        mock_get_llm.return_value = mock_llm

        pipeline = ExtractionPipeline(use_llm=True, use_intelligent=False)

        html = """
        <html>
            <body>
                <div>Some content</div>
            </body>
        </html>
        """

        result = pipeline.extract(html, source_url='http://example.com/test')
        assert result.extraction_method == 'llm'
        assert result.title == 'LLM提取的标题'


class TestIntelligentExtractorEdgeCases:
    """Edge case tests for IntelligentExtractor"""

    @pytest.fixture
    def extractor(self):
        return IntelligentExtractor()

    def test_multiple_dates_picks_first(self, extractor):
        """Should pick the first valid date when multiple found"""
        html = """
        <html>
            <body>
                <div>发布时间：2024年01月10日</div>
                <div>截止时间：2024年02月20日</div>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['publish_date'] is not None
        assert result['publish_date'].day == 10

    def test_budget_with_billion(self, extractor):
        """Should handle billion unit"""
        html = """
        <html>
            <body>
                <p>项目预算：1.5亿元</p>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['budget'] == Decimal('150000000')

    def test_no_main_content(self, extractor):
        """Should handle pages without clear main content"""
        html = """
        <html>
            <head><title>Test</title></head>
        </html>
        """
        result = extractor.extract(html)
        # Should not crash, may return empty or minimal data
        assert result is not None

    def test_nested_structure(self, extractor):
        """Should handle deeply nested HTML"""
        html = """
        <html>
            <body>
                <div>
                    <div>
                        <div>
                            <article>
                                <h1>深层嵌套的标题</h1>
                            </article>
                        </div>
                    </div>
                </div>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['title'] == '深层嵌套的标题'

    def test_tenderer_with_colon_variations(self, extractor):
        """Should handle different colon styles"""
        html = """
        <html>
            <body>
                <p>采购人: 某某单位</p>
            </body>
        </html>
        """
        result = extractor.extract(html)
        assert result['tenderer'] is not None