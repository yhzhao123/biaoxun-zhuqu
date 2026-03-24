"""
LLM-based NLP Extraction Tests - Phase 4 Task 018-023

使用大模型进行实体提取的测试。
支持本地模型(Ollama)和云端API(OpenAI/Claude)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestLLMEntityExtraction:
    """Test 1: 大模型实体提取基础功能"""

    def test_llm_extractor_class_exists(self):
        """LLMExtractor类应存在"""
        from apps.analysis.services.llm_extractor import LLMExtractor
        assert LLMExtractor is not None

    def test_llm_extractor_has_extract_method(self):
        """LLMExtractor应有extract方法"""
        from apps.analysis.services.llm_extractor import LLMExtractor
        assert hasattr(LLMExtractor, 'extract')


class TestTendererExtraction:
    """Test 2: 招标人提取测试"""

    @pytest.fixture
    def sample_tender_text(self):
        return """
        某市人民医院医疗设备采购项目招标公告
        招标人：某市人民医院
        招标代理机构：某招标代理有限公司
        项目预算：500万元
        """

    def test_extract_tenderer_from_standard_format(self, sample_tender_text):
        """从标准格式文本中提取招标人"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        # Mock LLM响应
        mock_response = '''
        {
            "entity": "某市人民医院",
            "confidence": 0.95,
            "evidence": "招标人：某市人民医院",
            "reasoning": "文本中明确标注'招标人'后跟随医院名称"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(sample_tender_text, entity_type='tenderer')

            assert result['entity'] == "某市人民医院"
            assert result['confidence'] > 0.85
            assert '招标人' in result['evidence']

    def test_extract_tenderer_from_procurement_format(self):
        """从'采购单位'格式中提取"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = "采购单位：某市教育局信息中心"

        mock_response = '''
        {
            "entity": "某市教育局信息中心",
            "confidence": 0.92,
            "evidence": "采购单位：某市教育局信息中心",
            "reasoning": "文本中明确标注'采购单位'"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='tenderer')

            assert result['entity'] == "某市教育局信息中心"
            assert result['confidence'] > 0.80

    def test_handle_ambiguous_tenderer(self):
        """处理招标人不明确的文本"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = "本项目欢迎各投标人参与"

        mock_response = '''
        {
            "entity": null,
            "confidence": 0.45,
            "evidence": "",
            "reasoning": "文本中未明确提及招标人"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='tenderer')

            assert result['entity'] is None or result['entity'] == ''
            assert result['confidence'] < 0.6

    def test_select_best_tenderer_candidate(self):
        """从多个候选中选择最佳招标人"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = """
        委托单位：某市政府
        采购单位：某市交通运输局
        代理机构：某招标代理公司
        """

        mock_response = '''
        {
            "entity": "某市交通运输局",
            "confidence": 0.88,
            "evidence": "采购单位：某市交通运输局",
            "reasoning": "采购单位是实际的招标执行方"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='tenderer')

            assert "交通运输局" in result['entity'] or "政府" in result['entity']
            assert result['confidence'] > 0.70


class TestAmountExtraction:
    """Test 3: 金额提取测试"""

    def test_extract_amount_with_wan(self):
        """提取'万元'格式金额"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = "预算金额：500万元"

        mock_response = '''
        {
            "entity": 5000000,
            "currency": "CNY",
            "confidence": 0.95,
            "evidence": "预算金额：500万元",
            "reasoning": "500万元 = 5000000元"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='amount')

            assert result['entity'] == 5000000
            assert result['currency'] == 'CNY'
            assert result['confidence'] > 0.85

    def test_extract_amount_with_yuan(self):
        """提取'元'格式金额"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = "中标金额：¥1,234,567.00元"

        mock_response = '''
        {
            "entity": 1234567.00,
            "currency": "CNY",
            "confidence": 0.95,
            "evidence": "中标金额：¥1,234,567.00元",
            "reasoning": "直接提取数字金额"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='amount')

            assert result['entity'] == 1234567.00
            assert result['confidence'] > 0.85

    def test_extract_amount_with_usd(self):
        """提取美元金额"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = "Budget: $100,000 USD"

        mock_response = '''
        {
            "entity": 100000,
            "currency": "USD",
            "confidence": 0.92,
            "evidence": "Budget: $100,000 USD",
            "reasoning": "识别到美元符号和USD标识"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='amount')

            assert result['entity'] == 100000
            assert result['currency'] == 'USD'

    def test_handle_missing_amount(self):
        """处理无金额文本"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = "本项目预算待确定"

        mock_response = '''
        {
            "entity": null,
            "currency": "CNY",
            "confidence": 0.3,
            "evidence": "",
            "reasoning": "文本中未提及具体金额"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='amount')

            assert result['entity'] is None
            assert result['confidence'] < 0.5


class TestConfidenceScoring:
    """Test 4: 置信度评分测试"""

    def test_high_confidence_for_clear_text(self):
        """清晰文本应返回高置信度"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = "招标人：某某公司，预算：100万元"

        mock_response = '''
        {
            "entity": "某某公司",
            "confidence": 0.95,
            "evidence": "招标人：某某公司",
            "reasoning": "文本明确标注招标人"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='tenderer')

            assert result['confidence'] > 0.85

    def test_low_confidence_for_ambiguous_text(self):
        """模糊文本应返回低置信度"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = "可能也许是某公司"

        mock_response = '''
        {
            "entity": "某公司",
            "confidence": 0.45,
            "evidence": "可能也许是某公司",
            "reasoning": "文本表述不确定"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='tenderer')

            assert result['confidence'] < 0.6

    def test_confidence_reasoning(self):
        """应提供置信度推理依据"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        text = "招标人：某某公司"

        mock_response = '''
        {
            "entity": "某某公司",
            "confidence": 0.95,
            "evidence": "招标人：某某公司",
            "reasoning": "明确标注了招标人"
        }
        '''

        with patch.object(LLMExtractor, '_call_ollama', return_value=mock_response):
            extractor = LLMExtractor()
            result = extractor.extract(text, entity_type='tenderer')

            assert 'reasoning' in result
            assert len(result['reasoning']) > 0


class TestLLMProviderConfig:
    """Test 5: LLM提供商配置测试"""

    def test_supports_openai(self):
        """支持OpenAI API"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        extractor = LLMExtractor(provider='openai')
        assert extractor.provider == 'openai'

    def test_supports_ollama(self):
        """支持Ollama本地模型"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        extractor = LLMExtractor(provider='ollama')
        assert extractor.provider == 'ollama'

    def test_supports_claude(self):
        """支持Claude API"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        extractor = LLMExtractor(provider='claude')
        assert extractor.provider == 'claude'

    def test_default_provider_is_ollama(self):
        """默认使用Ollama本地模型"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        extractor = LLMExtractor()
        assert extractor.provider == 'ollama'


class TestBatchExtraction:
    """Test 6: 批量提取测试"""

    def test_batch_extract_entities(self):
        """批量提取多个实体的多个字段"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        texts = [
            "招标人：公司A，预算：100万",
            "采购单位：公司B，金额：200万元",
        ]

        mock_responses = [
            '{"entity": "公司A", "confidence": 0.95, "evidence": "招标人：公司A", "reasoning": "明确标注"}',
            '{"entity": 1000000, "currency": "CNY", "confidence": 0.92, "evidence": "预算：100万", "reasoning": "100万=1000000"}',
            '{"entity": "公司B", "confidence": 0.93, "evidence": "采购单位：公司B", "reasoning": "明确标注"}',
            '{"entity": 2000000, "currency": "CNY", "confidence": 0.94, "evidence": "金额：200万元", "reasoning": "200万=2000000"}',
        ]

        with patch.object(LLMExtractor, '_call_ollama', side_effect=mock_responses):
            extractor = LLMExtractor()
            results = extractor.batch_extract(texts, entity_types=['tenderer', 'amount'])

            assert len(results) == 2
            assert all('tenderer' in r for r in results)
            assert all('amount' in r for r in results)

    def test_batch_with_empty_text(self):
        """批量处理包含空文本"""
        from apps.analysis.services.llm_extractor import LLMExtractor

        texts = ["", "招标人：公司A"]

        mock_responses = [
            '{"entity": null, "confidence": 0.0, "evidence": "", "reasoning": "Empty text"}',
            '{"entity": "公司A", "confidence": 0.95, "evidence": "招标人：公司A", "reasoning": "明确标注"}',
        ]

        with patch.object(LLMExtractor, '_call_ollama', side_effect=mock_responses):
            extractor = LLMExtractor()
            results = extractor.batch_extract(texts, entity_types=['tenderer'])

            assert len(results) == 2
            assert results[0]['tenderer']['entity'] is None
