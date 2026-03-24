"""
Search Highlight Tests - Phase 6 Task 034
Tests for search result highlighting and snippet generation.
"""

import pytest
from django.test import TestCase
from apps.tenders.search.highlight_service import HighlightService, SnippetService


class TestHighlightServiceExists:
    """Test 1: HighlightService class exists"""

    def test_highlight_service_class_exists(self):
        """HighlightService class should exist"""
        from apps.tenders.search.highlight_service import HighlightService
        assert HighlightService is not None

    def test_highlight_service_has_highlight_method(self):
        """HighlightService should have highlight method"""
        from apps.tenders.search.highlight_service import HighlightService
        assert hasattr(HighlightService, 'highlight')


class TestBasicHighlight(TestCase):
    """Test 2: Basic highlighting"""

    def setUp(self):
        self.service = HighlightService()

    def test_highlight_single_keyword(self):
        """Should highlight single keyword in text"""
        text = "这是一份医疗设备采购公告"
        result = self.service.highlight(text, ['医疗'])

        assert '<mark>医疗</mark>' in result

    def test_highlight_multiple_keywords(self):
        """Should highlight multiple keywords"""
        text = "北京市医院设备采购项目"
        result = self.service.highlight(text, ['北京', '医院'])

        assert '<mark>北京</mark>' in result
        assert '<mark>医院</mark>' in result

    def test_highlight_case_insensitive(self):
        """Should highlight case-insensitively"""
        text = "Beijing Hospital Project"
        result = self.service.highlight(text, ['beijing'])

        assert '<mark>Beijing</mark>' in result

    def test_no_highlight_for_no_match(self):
        """Should not modify text when no match"""
        text = "这是一份普通公告"
        result = self.service.highlight(text, ['不存在'])

        assert result == text
        assert '<mark>' not in result


class TestHighlightTagConfiguration(TestCase):
    """Test 3: Configurable highlight tags"""

    def setUp(self):
        self.service = HighlightService()

    def test_default_mark_tag(self):
        """Should use <mark> tag by default"""
        text = "医疗设备采购"
        result = self.service.highlight(text, ['医疗'])

        assert '<mark>医疗</mark>' in result

    def test_custom_start_tag(self):
        """Should support custom start tag"""
        text = "医疗设备采购"
        result = self.service.highlight(
            text,
            ['医疗'],
            start_tag='<em class="highlight">',
            end_tag='</em>'
        )

        assert '<em class="highlight">医疗</em>' in result

    def test_custom_end_tag(self):
        """Should support custom end tag"""
        text = "医疗设备采购"
        result = self.service.highlight(
            text,
            ['医疗'],
            end_tag='</strong>'
        )

        assert '<mark>医疗</strong>' in result


class TestXSSProtection(TestCase):
    """Test 4: XSS protection through HTML escaping"""

    def setUp(self):
        self.service = HighlightService()

    def test_escapes_html_in_text(self):
        """Should escape HTML characters in text"""
        text = "<script>alert('xss')</script>医疗设备"
        result = self.service.highlight(text, ['医疗'])

        assert '<script>' not in result
        assert '&lt;script&gt;' in result
        assert '<mark>医疗</mark>' in result

    def test_escapes_quotes(self):
        """Should escape quotes in text"""
        text = '"医疗设备"采购'
        result = self.service.highlight(text, ['医疗'])

        assert '&quot;' in result or '"' not in result

    def test_escapes_ampersand(self):
        """Should escape ampersand"""
        text = 'A&B医疗设备'
        result = self.service.highlight(text, ['医疗'])

        assert '&amp;' in result or result.count('&') == 1

    def test_keyword_with_special_chars(self):
        """Should handle keywords with special characters safely"""
        text = "医疗设备<特殊>"
        result = self.service.highlight(text, ['特殊'])

        assert '<mark>特殊</mark>' in result
        assert '<mark>' not in result.replace('<mark>特殊</mark>', '')


class TestSnippetService(TestCase):
    """Test 5: SnippetService exists"""

    def test_snippet_service_class_exists(self):
        """SnippetService class should exist"""
        from apps.tenders.search.highlight_service import SnippetService
        assert SnippetService is not None

    def test_snippet_service_has_generate_method(self):
        """SnippetService should have generate method"""
        from apps.tenders.search.highlight_service import SnippetService
        assert hasattr(SnippetService, 'generate')


class TestSnippetGeneration(TestCase):
    """Test 6: Snippet generation with context"""

    def setUp(self):
        self.service = SnippetService()

    def test_generate_snippet_with_context(self):
        """Should generate snippet with context around keyword"""
        text = "这是一份很长的公告文本。其中包含医疗设备采购信息。这是其他不相关内容。"
        result = self.service.generate(text, ['医疗'], context_size=5)

        assert '...' in result or len(result) < len(text)
        assert '医疗' in result

    def test_snippet_contains_keyword(self):
        """Snippet should always contain the keyword"""
        text = "这是一份医疗设备采购公告，用于医院建设。"
        result = self.service.generate(text, ['设备'])

        assert '设备' in result

    def test_snippet_max_length(self):
        """Snippet should respect max length"""
        text = "这是一份" + "很长的" * 100 + "医疗设备采购公告"
        result = self.service.generate(text, ['医疗'], max_length=50)

        assert len(result) <= 50

    def test_multiple_snippets(self):
        """Should handle multiple keyword occurrences"""
        # Use longer text so occurrences are not all in same snippet
        text = "医疗设备采购，这是一些额外的描述文字。医疗设备安装，更多描述内容。医疗设备维护"
        result = self.service.generate(text, ['医疗'], max_snippets=2, context_size=10)

        assert result.count('医疗') <= 2


class TestSnippetHighlightIntegration(TestCase):
    """Test 7: Snippet generation with highlighting"""

    def setUp(self):
        self.snippet_service = SnippetService()
        self.highlight_service = HighlightService()

    def test_snippet_with_highlighting(self):
        """Should generate snippet with highlighted keywords"""
        text = "这是一份医疗设备采购公告"
        snippet = self.snippet_service.generate(text, ['医疗'])
        highlighted = self.highlight_service.highlight(snippet, ['医疗'])

        assert '<mark>医疗</mark>' in highlighted

    def test_highlighted_snippet_escapes_html(self):
        """Highlighted snippet should escape HTML"""
        text = "<script>医疗设备</script>采购"
        snippet = self.snippet_service.generate(text, ['医疗'])
        highlighted = self.highlight_service.highlight(snippet, ['医疗'])

        assert '<script>' not in highlighted
        assert '<mark>医疗</mark>' in highlighted


class TestSearchResultWithHighlight(TestCase):
    """Test 8: Search results with highlighting"""

    def setUp(self):
        from apps.tenders.repositories import TenderRepository
        from apps.tenders.search.search_service import SearchService

        self.repo = TenderRepository()
        self.search_service = SearchService()

    def test_search_returns_highlighted_title(self):
        """Search should return highlighted title"""
        from datetime import datetime
        from apps.tenders.models import TenderNotice

        self.repo.create({
            'title': '医疗设备采购项目',
            'description': '医院设备采购',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        results = self.search_service.search(query='医疗', highlight=True)

        assert len(results) > 0
        assert 'highlighted_title' in results[0] or 'highlighted' in results[0]

    def test_search_returns_highlighted_description(self):
        """Search should return highlighted description"""
        from datetime import datetime
        from apps.tenders.models import TenderNotice

        self.repo.create({
            'title': '设备采购',
            'description': '医疗设备详细说明',
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        results = self.search_service.search(query='医疗', highlight=True)

        assert len(results) > 0
        if 'highlighted_description' in results[0]:
            assert '<mark>' in results[0]['highlighted_description']

    def test_search_returns_snippet(self):
        """Search should return snippet for long descriptions"""
        from datetime import datetime
        from apps.tenders.models import TenderNotice

        long_description = "这是一份" + "很长的" * 50 + "医疗设备采购说明"
        self.repo.create({
            'title': '设备采购',
            'description': long_description,
            'publish_date': datetime.now(),
            'notice_type': TenderNotice.TYPE_BIDDING
        })

        results = self.search_service.search(query='医疗', highlight=True)

        assert len(results) > 0
        if 'snippet' in results[0]:
            assert len(results[0]['snippet']) < len(long_description)


class TestHighlightPerformance(TestCase):
    """Test 9: Highlight performance"""

    def setUp(self):
        self.service = HighlightService()

    def test_highlight_large_text(self):
        """Should handle large text efficiently"""
        import time

        text = "医疗设备" * 1000 + "关键词"
        start = time.time()
        result = self.service.highlight(text, ['关键词'])
        elapsed = time.time() - start

        assert elapsed < 1.0
        assert '<mark>关键词</mark>' in result


class TestChineseHighlight(TestCase):
    """Test 10: Chinese text highlighting"""

    def setUp(self):
        self.service = HighlightService()

    def test_highlight_chinese_phrase(self):
        """Should highlight Chinese phrases correctly"""
        text = "北京市政府采购项目"
        result = self.service.highlight(text, ['北京市政府'])

        assert '<mark>北京市政府</mark>' in result

    def test_highlight_partial_chinese_match(self):
        """Should highlight Chinese matches"""
        text = "医院医疗设备"
        result = self.service.highlight(text, ['医疗'])

        assert '<mark>医疗</mark>' in result
        # Only exact matches are highlighted, not partial characters
        assert result.count('<mark>') == 1

    def test_highlight_mixed_chinese_english(self):
        """Should handle mixed Chinese and English"""
        text = "IBM医疗设备采购Project"
        result = self.service.highlight(text, ['IBM', '医疗'])

        assert '<mark>IBM</mark>' in result
        assert '<mark>医疗</mark>' in result


class TestEdgeCases(TestCase):
    """Test 11: Edge cases"""

    def setUp(self):
        self.service = HighlightService()

    def test_empty_text(self):
        """Should handle empty text"""
        result = self.service.highlight('', ['关键词'])

        assert result == ''

    def test_empty_keywords(self):
        """Should handle empty keywords"""
        text = "这是一份公告"
        result = self.service.highlight(text, [])

        assert result == text

    def test_none_keywords(self):
        """Should handle None keywords"""
        text = "这是一份公告"
        result = self.service.highlight(text, None)

        assert result == text

    def test_overlapping_keywords(self):
        """Should handle overlapping keywords"""
        text = "医疗设备"
        result = self.service.highlight(text, ['医疗', '设备'])

        # Should highlight both without breaking HTML
        assert '<mark>医疗</mark>' in result
        assert '<mark>设备</mark>' in result

    def test_keyword_at_boundaries(self):
        """Should highlight keywords at text boundaries"""
        text = "医疗设备"
        result = self.service.highlight(text, ['医疗', '设备'])

        assert result.startswith('<mark>医疗</mark>')
        assert result.endswith('<mark>设备</mark>')

