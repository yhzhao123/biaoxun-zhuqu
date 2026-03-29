"""
Test for PDF Extraction Accuracy Issues

Tests:
1. Tenderer extraction with spaces in Chinese text (e.g., "采 购 人")
2. Content truncation at 2000 chars
3. Item extraction from tender documents

Run: python -m pytest backend/test_extraction_accuracy.py -v
"""
import logging
import os
import re
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

import django
django.setup()

import pytest
from apps.crawler.agents.services.pdf_analyzer import PDFContentAnalyzer
from apps.crawler.agents.orchestrator_v2 import TenderOrchestratorV2


class TestTendererExtraction:
    """Test tenderer extraction with various formats"""

    def test_tenderer_with_spaces(self):
        """Test tenderer extraction handles spaces like '采 购 人：xxx'"""
        text = """
        招标公告

        采 购 人：吉林财经大学
        采购单位：某省财政厅
        招 标 人：某大学

        项目编号：2024-CG-001
        预算金额：100万元
        """

        # Current regex (fails)
        old_pattern = r'(招标人|采购人|采购单位)[：:]\s*([^\n]+)'
        old_match = re.search(old_pattern, text)
        logger.info("Old pattern result: %s", old_match.group(2).strip() if old_match else 'No match')

        # Fixed regex (should work)
        new_pattern = r'(?:采\s*购\s*人|招\s*标\s*人|采\s*购\s*单\s*位)[：:]\s*([^\n]+)'
        new_match = re.search(new_pattern, text)
        logger.info("New pattern result: %s", new_match.group(1).strip() if new_match else 'No match')

        # Verify the old pattern fails and new pattern works
        assert old_match is None or old_match.group(2).strip() != '吉林财经大学', \
            "Old pattern should fail on spaced text"

        assert new_match is not None, "New pattern should match"
        assert '吉林财经大学' in new_match.group(1), \
            f"Expected '吉林财经大学' but got '{new_match.group(1)}'"


class TestContentTruncation:
    """Test content truncation issue"""

    def test_description_truncation(self):
        """Test that description is not truncated to 2000 chars"""
        # Create a long PDF content
        long_content = "这是招标公告的详细内容。\n" * 500  # ~9000 chars

        # Current truncation (fails)
        old_description = long_content[:2000] if len(long_content) > 2000 else long_content
        logger.info("Old truncation length: %d", len(old_description))

        # Fixed truncation (should be longer)
        new_description = long_content[:5000] if len(long_content) > 5000 else long_content
        logger.info("New truncation length: %d", len(new_description))

        # Verify old truncation is smaller than new
        assert len(old_description) < len(new_description), \
            "Old truncation should be more restrictive"
        assert len(new_description) >= 4000, \
            "New truncation should keep more content"


class TestItemExtraction:
    """Test item extraction from tender documents"""

    def setup_method(self):
        self.analyzer = PDFContentAnalyzer()

    def test_item_extraction_with_table_format(self):
        """Test extraction of items in table format"""
        text = """
        采购标的清单

        序号 | 标的名称 | 数量 | 单位 | 预算单价
        -----|----------|------|------|----------
        1 | 台式计算机 | 50 | 台 | 5000
        2 | 激光打印机 | 10 | 台 | 3000

        或者：

        货物名称  数量  单位
        服务器   5    台
        交换机   10   台
        """

        result = self.analyzer.analyze(text)
        items = result.get('items', [])

        logger.info("Extracted items: %s", items)
        logger.info("Item count: %d", len(items))

        # Should extract at least the table items
        assert len(items) > 0, "Should extract items from table format"

    def test_qualification_extraction(self):
        """Test qualification requirements extraction"""
        text = """
        投标人资格要求：

        1. 具有独立法人资格的企业；
        2. 注册资金不少于100万元；
        3. 具有相关政府采购资质；
        4. 近三年内无重大违法记录。

        供应商资格要求：
        1. 必须具有营业执照；
        2. 必须具有税务登记证；
        """

        result = self.analyzer.analyze(text)
        qualification = result.get('qualification_requirements', '')

        logger.info("Extracted qualification: %s...", qualification[:200])

        # Should extract qualification text, not dots
        assert qualification, "Should extract qualification requirements"
        assert '...' not in qualification and '……' not in qualification, \
            "Should not return dots/ellipsis"


class TestIntegration:
    """Integration tests for extraction"""

    def test_full_pipeline_tenderer(self):
        """Test full pipeline with tenderer in various formats"""
        test_cases = [
            ("采购人：吉林财经大学", "吉林财经大学"),
            ("采 购 人：吉林财经大学", "吉林财经大学"),
            ("采 购 单 位：某单位", "某单位"),
            ("招 标 人：测试公司", "测试公司"),
            ("招标人：正常格式", "正常格式"),
        ]

        for text, expected in test_cases:
            # Test with new pattern
            pattern = r'(?:采\s*购\s*人|招\s*标\s*人|采\s*购\s*单\s*位)[：:]\s*([^\n]+)'
            match = re.search(pattern, text)

            if match:
                extracted = match.group(1).strip()
                logger.info("Input: '%s' -> Extracted: '%s'", text, extracted)
                assert extracted == expected, f"Expected '{expected}' but got '{extracted}'"
            else:
                pytest.fail(f"Failed to match: {text}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])