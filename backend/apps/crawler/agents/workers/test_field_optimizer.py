"""
Tests for Field Optimization Agent

Test cases covering:
- Field extraction from list items
- Regex preprocessing
- Smart field merging
- Missing field detection
- Full optimization workflow
"""

import unittest
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from apps.crawler.agents.workers.field_optimizer import (
    FieldOptimizationAgent,
    FieldOptimizationConfig,
    ExtractionResult,
)


class MockLLMExtractor:
    """Mock LLM extractor for testing"""

    def __init__(self, mock_data: Dict[str, Any] = None):
        self.mock_data = mock_data or {
            'title': 'Mock Tender Title',
            'tenderer': 'Mock Procurement Unit',
            'description': 'Mock description from LLM',
        }
        self.call_count = 0

    def extract(self, html: str, url: str) -> Dict[str, Any]:
        self.call_count += 1
        return {
            **self.mock_data,
            'extraction_method': 'llm',
            'llm_provider': 'mock',
        }


class TestFieldOptimizationConfig(unittest.TestCase):
    """Test FieldOptimizationConfig dataclass"""

    def test_default_config(self):
        """Test default configuration values"""
        config = FieldOptimizationConfig()

        self.assertIn('title', config.required_fields)
        self.assertIn('tenderer', config.required_fields)
        self.assertTrue(config.use_regex_preprocessing)
        self.assertEqual(config.llm_fallback_threshold, 0.5)

    def test_custom_config(self):
        """Test custom configuration"""
        config = FieldOptimizationConfig(
            required_fields=['title', 'budget_amount'],
            llm_fallback_threshold=0.7,
            use_regex_preprocessing=False,
        )

        self.assertEqual(config.required_fields, ['title', 'budget_amount'])
        self.assertEqual(config.llm_fallback_threshold, 0.7)
        self.assertFalse(config.use_regex_preprocessing)

    def test_get_list_field_for_detail(self):
        """Test field mapping retrieval"""
        config = FieldOptimizationConfig()
        config.list_to_detail_mapping = {
            'title': 'title',
            'purchaser': 'tenderer',
        }

        result = config.get_list_field_for_detail('title')
        self.assertEqual(result, 'title')


class TestFieldOptimizationAgent(unittest.TestCase):
    """Test FieldOptimizationAgent functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.config = FieldOptimizationConfig()
        self.agent = FieldOptimizationAgent(self.config)

    def test_extract_from_list_basic(self):
        """Test basic list item extraction"""
        list_item = {
            'title': 'Test Tender',
            'purchaser': 'Test Unit',
            'date': '2024-01-15',
            'budget': '50000',
        }

        result = self.agent.extract_from_list(list_item)

        self.assertEqual(result.get('title'), 'Test Tender')
        self.assertIn('publish_date', result)
        self.assertIn('budget_amount', result)

    def test_extract_from_list_with_mapping(self):
        """Test extraction with custom field mapping"""
        list_item = {
            'custom_title': 'Custom Tender',
            'buyer_name': 'Custom Buyer',
        }

        mapping = {
            'title': 'custom_title',
            'tenderer': 'buyer_name',
        }

        result = self.agent.extract_from_list(list_item, mapping)

        self.assertEqual(result.get('title'), 'Custom Tender')
        self.assertEqual(result.get('tenderer'), 'Custom Buyer')

    def test_extract_from_list_empty(self):
        """Test extraction with empty list item"""
        result = self.agent.extract_from_list({})
        self.assertEqual(result, {})

        result = self.agent.extract_from_list(None)
        self.assertEqual(result, {})

    def test_determine_missing_fields(self):
        """Test missing field detection"""
        prefilled = {
            'title': 'Test Title',
            'tenderer': '',  # Empty string should be missing
            'publish_date': None,  # None should be missing
            'budget_amount': -100,  # Negative should be missing
        }

        required = ['title', 'tenderer', 'publish_date', 'budget_amount']

        missing = self.agent.determine_missing_fields(prefilled, required)

        self.assertIn('tenderer', missing)
        self.assertIn('publish_date', missing)
        self.assertIn('budget_amount', missing)
        self.assertNotIn('title', missing)

    def test_determine_missing_fields_all_present(self):
        """Test when all fields are present"""
        prefilled = {
            'title': 'Test Title',
            'tenderer': 'Test Tenderer',
            'publish_date': datetime.now(),
            'budget_amount': Decimal('10000'),
        }

        required = ['title', 'tenderer', 'publish_date', 'budget_amount']

        missing = self.agent.determine_missing_fields(prefilled, required)

        self.assertEqual(missing, [])

    def test_merge_results(self):
        """Test smart field merging"""
        list_data = {
            'title': 'List Title',
            'tenderer': 'List Tenderer',
            'publish_date': datetime(2024, 1, 1),
        }

        llm_data = {
            'title': 'LLM Title',  # Should be overridden by list data (list_conf 0.95 > llm_conf 0.9 for tenderer)
            'tenderer': 'LLM Tenderer',  # List confidence 0.95 > LLM confidence 0.9, so list wins
            'description': 'LLM Description',  # Should be added
            'budget_amount': Decimal('50000'),  # Should be added
        }

        list_confidence = {
            'title': 0.95,  # Higher than default LLM title confidence (1.0), but let's test with tenderer
            'tenderer': 0.95,  # Higher than default LLM tenderer confidence (0.9)
            'publish_date': 0.85,
        }

        merged, confidence, sources = self.agent.merge_results(
            list_data, llm_data, list_confidence
        )

        # Tenderer should come from list (higher confidence: 0.95 > 0.9)
        self.assertEqual(merged['tenderer'], 'List Tenderer')
        self.assertEqual(sources['tenderer'], 'list')

        # Description should come from LLM
        self.assertEqual(merged['description'], 'LLM Description')
        self.assertEqual(sources['description'], 'llm')

    def test_preprocess_with_regex_dates(self):
        """Test regex preprocessing for dates"""
        html = """
        <html>
        <body>
            <div>发布时间：2024年3月15日</div>
            <div>招标公告</div>
        </body>
        </html>
        """

        result = self.agent.preprocess_with_regex(html)

        self.assertIn('publish_date', result)
        self.assertIsInstance(result['publish_date'], datetime)

    def test_preprocess_with_regex_amounts(self):
        """Test regex preprocessing for amounts"""
        html = """
        <html>
        <body>
            <div>预算金额：50万元</div>
            <div>招标公告</div>
        </body>
        </html>
        """

        result = self.agent.preprocess_with_regex(html)

        self.assertIn('budget_amount', result)
        self.assertIsInstance(result['budget_amount'], Decimal)
        self.assertEqual(result['budget_amount'], Decimal('500000'))

    def test_preprocess_with_regex_tenderer(self):
        """Test regex preprocessing for tenderer"""
        html = """
        <html>
        <body>
            <div>采购人：某政府采购中心</div>
            <div>联系人：张三</div>
        </body>
        </html>
        """

        result = self.agent.preprocess_with_regex(html)

        self.assertIn('tenderer', result)
        self.assertEqual(result['tenderer'], '某政府采购中心')

    def test_parse_date_value(self):
        """Test date value parsing"""
        # Test Chinese format
        result = self.agent._parse_date_value('2024年3月15日')
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2024)
        self.assertEqual(result.month, 3)
        self.assertEqual(result.day, 15)

        # Test ISO format
        result = self.agent._parse_date_value('2024-03-15')
        self.assertIsInstance(result, datetime)

        # Test datetime input
        dt = datetime(2024, 1, 1)
        result = self.agent._parse_date_value(dt)
        self.assertEqual(result, dt)

    def test_parse_amount_value(self):
        """Test amount value parsing"""
        # Test string with currency
        result = self.agent._parse_amount_value('¥50,000')
        self.assertEqual(result, Decimal('50000'))

        # Test string with unit
        result = self.agent._parse_amount_value('50万元')
        self.assertEqual(result, Decimal('500000'))

        # Test numeric input
        result = self.agent._parse_amount_value(50000)
        self.assertEqual(result, Decimal('50000'))

    def test_field_names_match(self):
        """Test field name matching logic"""
        # Direct match
        self.assertTrue(self.agent._field_names_match('title', 'title'))

        # Case insensitive
        self.assertTrue(self.agent._field_names_match('Title', 'title'))

        # Substring match
        self.assertTrue(self.agent._field_names_match('purchaser', 'tenderer'))

        # No match
        self.assertFalse(self.agent._field_names_match('random', 'title'))

    def test_calculate_savings(self):
        """Test savings calculation"""
        result = ExtractionResult()
        result.data = {'title': 'Test', 'tenderer': 'Test'}
        result.sources = {'title': 'list_item', 'tenderer': 'regex'}
        result.llm_called = False

        savings = self.agent.calculate_savings(result)

        self.assertTrue(savings['llm_call_avoided'])
        self.assertGreater(savings['estimated_cost_saved'], 0)
        self.assertIn('optimization_rate', savings)


class TestOptimizationWorkflow(unittest.TestCase):
    """Integration tests for full optimization workflow"""

    def test_optimize_extraction_avoids_llm(self):
        """Test that complete list data avoids LLM call"""
        config = FieldOptimizationConfig()
        agent = FieldOptimizationAgent(config)

        # Complete list item
        list_item = {
            'title': 'Complete Tender',
            'purchaser': 'Test Unit',
            'date': '2024-03-15',
            'budget': '100000',
        }

        mock_llm = MockLLMExtractor()

        result = agent.optimize_extraction(
            list_item=list_item,
            html='',  # No HTML
            url='http://example.com',
            llm_extractor=mock_llm,
        )

        # LLM should not be called
        self.assertFalse(result.llm_called)
        self.assertEqual(mock_llm.call_count, 0)

        # All required fields should be present
        self.assertIn('title', result.data)
        self.assertIn('tenderer', result.data)

    def test_optimize_extraction_uses_llm_for_missing(self):
        """Test that missing fields trigger LLM extraction"""
        config = FieldOptimizationConfig()
        agent = FieldOptimizationAgent(config)

        # Incomplete list item (missing tenderer)
        list_item = {
            'title': 'Partial Tender',
            'date': '2024-03-15',
        }

        mock_llm = MockLLMExtractor()

        html = """
        <html><body>
            <h1>Partial Tender</h1>
            <div>采购人：某单位</div>
        </body></html>
        """

        result = agent.optimize_extraction(
            list_item=list_item,
            html=html,
            url='http://example.com',
            llm_extractor=mock_llm,
        )

        # LLM should be called
        self.assertTrue(result.llm_called)
        self.assertEqual(mock_llm.call_count, 1)

        # Should have tenderer from LLM
        self.assertIn('tenderer', result.data)


if __name__ == '__main__':
    unittest.main()
