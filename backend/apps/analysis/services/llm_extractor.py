"""
LLM-based Entity Extraction Service - Phase 4 Task 019

使用大模型进行招标信息实体提取。
支持本地模型(Ollama)和云端API(OpenAI/Claude)
"""

import os
import json
import re
from typing import Dict, List, Optional, Union
import requests
from decimal import Decimal


class LLMExtractor:
    """
    大模型实体提取器

    支持从招标文本中提取：
    - 招标人 (tenderer)
    - 预算金额 (amount)
    - 项目编号 (project_id)
    - 截止日期 (deadline)
    - 地区 (region)
    - 行业 (industry)
    """

    ENTITY_PROMPTS = {
        'tenderer': """从以下招标文本中提取招标人/采购单位信息。

文本内容：
{text}

请提取招标人/采购单位名称，并以JSON格式返回：
{{
    "entity": "提取的招标人名称",
    "confidence": 0.95,
    "evidence": "提取依据的原文片段",
    "reasoning": "解释为什么这是招标人"
}}

注意：
1. 优先识别"招标人"、"采购单位"、"采购人"后的内容
2. 如果没有明确标识，返回null
3. confidence取值0-1，越确定越高
4. 只返回JSON，不要其他内容""",

        'amount': """从以下招标文本中提取预算金额信息。

文本内容：
{text}

请提取预算金额/中标金额，并以JSON格式返回：
{{
    "entity": 提取的金额数字（单位：元）,
    "currency": "CNY",
    "confidence": 0.95,
    "evidence": "提取依据的原文片段",
    "reasoning": "解释提取过程和换算"
}}

注意：
1. 支持"万元"、"万"、"元"等单位，统一转换为元
2. 如果是美元，currency设为"USD"
3. 如果没有金额信息，entity设为null
4. 只返回JSON，不要其他内容""",

        'deadline': """从以下招标文本中提取截止日期信息。

文本内容：
{text}

请提取投标截止时间/报名截止时间，并以JSON格式返回：
{{
    "entity": "YYYY-MM-DD HH:MM:SS",
    "confidence": 0.95,
    "evidence": "提取依据的原文片段",
    "reasoning": "解释日期格式转换"
}}

注意：
1. 统一转换为YYYY-MM-DD HH:MM:SS格式
2. 如果没有明确时间，只保留日期
3. 如果没有截止日期，entity设为null
4. 只返回JSON，不要其他内容""",

        'region': """从以下招标文本中提取地区信息。

文本内容：
{text}

请提取项目所在地区/城市，并以JSON格式返回：
{{
    "entity": "省份/城市名称",
    "confidence": 0.95,
    "evidence": "提取依据的原文片段",
    "reasoning": "解释地区识别依据"
}}

注意：
1. 优先识别省级行政区，如"北京市"、"广东省"
2. 如果没有地区信息，返回null
3. 只返回JSON，不要其他内容""",

        'industry': """从以下招标文本中提取行业信息。

文本内容：
{text}

请提取项目所属行业，并以JSON格式返回：
{{
    "entity": "行业分类",
    "confidence": 0.85,
    "evidence": "提取依据的原文片段",
    "reasoning": "解释行业分类依据"
}}

注意：
1. 根据项目内容判断行业，如"IT"、"建筑"、"医疗"等
2. 如果没有明确行业，返回null
3. 只返回JSON，不要其他内容""",
    }

    def __init__(self, provider: str = None):
        """
        初始化LLM提取器

        Args:
            provider: LLM提供商 ('ollama', 'openai', 'claude')
                     默认从环境变量读取，否则使用'ollama'
        """
        self.provider = provider or os.environ.get('LLM_PROVIDER', 'ollama')
        self.api_key = os.environ.get('LLM_API_KEY')
        self.base_url = self._get_base_url()
        self.model = self._get_model()

    def _get_base_url(self) -> str:
        """获取API基础URL"""
        if self.provider == 'ollama':
            return os.environ.get('OLLAMA_URL', 'http://localhost:11434')
        elif self.provider == 'openai':
            return 'https://api.openai.com/v1'
        elif self.provider == 'claude':
            return 'https://api.anthropic.com/v1'
        else:
            return 'http://localhost:11434'

    def _get_model(self) -> str:
        """获取模型名称"""
        if self.provider == 'ollama':
            return os.environ.get('OLLAMA_MODEL', 'qwen2.5:7b')
        elif self.provider == 'openai':
            return os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo')
        elif self.provider == 'claude':
            return os.environ.get('CLAUDE_MODEL', 'claude-3-haiku-20240307')
        else:
            return 'qwen2.5:7b'

    def extract(self, text: str, entity_type: str) -> Dict:
        """
        从文本中提取指定类型的实体

        Args:
            text: 招标文本内容
            entity_type: 实体类型 ('tenderer', 'amount', 'deadline', 'region', 'industry')

        Returns:
            {
                'entity': 提取的值 (字符串、数字或None),
                'confidence': 置信度 (0-1),
                'evidence': 原文证据,
                'reasoning': 推理说明,
                'currency': 货币代码 (仅amount类型)
            }
        """
        if not text or not text.strip():
            return {
                'entity': None,
                'confidence': 0.0,
                'evidence': '',
                'reasoning': 'Empty text provided'
            }

        prompt = self.ENTITY_PROMPTS.get(entity_type, '').format(text=text[:2000])

        if not prompt:
            return {
                'entity': None,
                'confidence': 0.0,
                'evidence': '',
                'reasoning': f'Unknown entity type: {entity_type}'
            }

        try:
            response = self._call_llm(prompt)
            result = self._parse_response(response, entity_type)
            return result
        except Exception as e:
            return {
                'entity': None,
                'confidence': 0.0,
                'evidence': '',
                'reasoning': f'LLM call failed: {str(e)}'
            }

    def _call_llm(self, prompt: str) -> str:
        """调用LLM API"""
        if self.provider == 'ollama':
            return self._call_ollama(prompt)
        elif self.provider == 'openai':
            return self._call_openai(prompt)
        elif self.provider == 'claude':
            return self._call_claude(prompt)
        else:
            raise ValueError(f'Unknown provider: {self.provider}')

    def _call_ollama(self, prompt: str) -> str:
        """调用Ollama本地模型"""
        url = f"{self.base_url}/api/generate"
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 500
            }
        }

        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        return response.json().get('response', '')

    def _call_openai(self, prompt: str) -> str:
        """调用OpenAI API"""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that extracts structured data from text. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }

        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']

    def _call_claude(self, prompt: str) -> str:
        """调用Claude API"""
        url = f"{self.base_url}/messages"
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        data = {
            "model": self.model,
            "max_tokens": 500,
            "temperature": 0.1,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        return response.json()['content'][0]['text']

    def _parse_response(self, response: str, entity_type: str) -> Dict:
        """解析LLM响应"""
        # 尝试提取JSON
        try:
            # 查找JSON代码块
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析整个响应
                json_str = response.strip()

            result = json.loads(json_str)

            # 标准化结果
            parsed = {
                'entity': result.get('entity'),
                'confidence': float(result.get('confidence', 0.5)),
                'evidence': result.get('evidence', ''),
                'reasoning': result.get('reasoning', '')
            }

            # 金额类型特殊处理
            if entity_type == 'amount' and parsed['entity'] is not None:
                parsed['currency'] = result.get('currency', 'CNY')
                # 转换字符串金额为数字
                if isinstance(parsed['entity'], str):
                    parsed['entity'] = self._parse_amount(parsed['entity'])
            else:
                parsed['currency'] = None

            return parsed

        except json.JSONDecodeError:
            # 如果JSON解析失败，尝试正则提取
            return self._fallback_parse(response, entity_type)

    def _fallback_parse(self, response: str, entity_type: str) -> Dict:
        """当JSON解析失败时的备用解析"""
        # 尝试查找引号内的内容作为entity
        patterns = {
            'tenderer': r'[":\s]*([^"\n]{3,50}?)(?:"|$)',
            'amount': r'(\d[\d,\.]+)',
        }

        entity = None
        if entity_type in patterns:
            match = re.search(patterns[entity_type], response)
            if match:
                entity = match.group(1).strip()
                if entity_type == 'amount':
                    entity = self._parse_amount(entity)

        return {
            'entity': entity,
            'confidence': 0.5 if entity else 0.3,
            'evidence': response[:200],
            'reasoning': 'Fallback parsing used due to JSON parse failure',
            'currency': 'CNY' if entity_type == 'amount' and entity else None
        }

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """解析金额字符串为数字"""
        if amount_str is None:
            return None

        # 移除货币符号和空格
        amount_str = str(amount_str).strip()
        amount_str = re.sub(r'[¥$€,\s]', '', amount_str)

        try:
            amount = float(amount_str)
            return amount
        except ValueError:
            return None

    def batch_extract(self, texts: List[str], entity_types: List[str]) -> List[Dict]:
        """
        批量提取多个文本的多个实体

        Args:
            texts: 文本列表
            entity_types: 要提取的实体类型列表

        Returns:
            每个文本的提取结果列表
        """
        results = []
        for text in texts:
            result = {}
            for entity_type in entity_types:
                result[entity_type] = self.extract(text, entity_type)
            results.append(result)
        return results
