"""
LLM Services - 大模型服务封装
使用官方SDK: OpenAI (openai), Anthropic (anthropic), Ollama (requests)
"""
import json
import requests
from typing import Dict, List, Optional
from httpx import Timeout

# 官方SDK导入
import openai
import anthropic

from .models import LLMConfig


class LLMService:
    """
    大模型服务封装
    支持Ollama、OpenAI、Claude
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = config.provider
        self.api_key = config.api_key
        self.base_url = config.api_base_url
        self.model = config.model_name

        # 初始化SDK客户端
        self._openai_client = None
        self._anthropic_client = None

    def _get_openai_client(self) -> openai.OpenAI:
        """获取或创建OpenAI客户端"""
        if self._openai_client is None:
            self._openai_client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url or None,
                timeout=Timeout(getattr(self.config, 'timeout_seconds', 120))
            )
        return self._openai_client

    def _get_anthropic_client(self) -> anthropic.Anthropic:
        """获取或创建Anthropic客户端"""
        if self._anthropic_client is None:
            self._anthropic_client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.base_url or None,
                timeout=Timeout(getattr(self.config, 'timeout_seconds', 120))
            )
        return self._anthropic_client

    def test_connection(self) -> Dict:
        """测试LLM连接"""
        try:
            if self.provider == 'ollama':
                return self._test_ollama()
            elif self.provider == 'openai':
                return self._test_openai()
            elif self.provider == 'claude':
                return self._test_claude()
            else:
                return {'success': False, 'message': '未知的提供商'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def chat(self, context: List[Dict], message: str) -> Dict:
        """
        发送聊天消息

        Args:
            context: 对话上下文
            message: 用户消息

        Returns:
            {
                'message': 'LLM响应内容',
                'extracted_entities': {}  # 提取的实体
            }
        """
        # 构建完整消息
        messages = context + [{'role': 'user', 'content': message}]

        if self.provider == 'ollama':
            return self._chat_ollama(messages)
        elif self.provider == 'openai':
            return self._chat_openai(messages)
        elif self.provider == 'claude':
            return self._chat_claude(messages)
        else:
            raise ValueError(f'未知的提供商: {self.provider}')

    def analyze_tender(self, content: str, question: str = '') -> Dict:
        """
        分析招标信息

        Args:
            content: 招标文档内容
            question: 用户问题（可选）

        Returns:
            {
                'analysis': '分析结果',
                'entities': {},
                'suggestions': []
            }
        """
        # 构建分析提示
        if question:
            prompt = f"""请分析以下招标信息并回答问题。

招标内容：
{content[:3000]}

用户问题：{question}

请提供详细分析和建议。"""
        else:
            prompt = f"""请分析以下招标信息，提取关键实体并提供洞察。

招标内容：
{content[:3000]}

请提取以下信息并以JSON格式返回：
{{
    "entities": {{
        "tenderer": "招标人",
        "budget": "预算金额",
        "region": "地区",
        "industry": "行业",
        "deadline": "截止日期"
    }},
    "analysis": "详细分析",
    "suggestions": ["建议1", "建议2"]
}}"""

        messages = [
            {'role': 'system', 'content': '你是招标信息分析专家，擅长提取关键信息和提供商业洞察。'},
            {'role': 'user', 'content': prompt}
        ]

        # 调用LLM
        if self.provider == 'ollama':
            response = self._chat_ollama(messages)
        elif self.provider == 'openai':
            response = self._chat_openai(messages)
        elif self.provider == 'claude':
            response = self._chat_claude(messages)
        else:
            raise ValueError(f'未知的提供商: {self.provider}')

        # 解析响应
        content = response['message']

        # 尝试提取JSON
        try:
            # 查找JSON代码块
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = content

            data = json.loads(json_str)
            return {
                'analysis': data.get('analysis', content),
                'entities': data.get('entities', {}),
                'suggestions': data.get('suggestions', [])
            }
        except json.JSONDecodeError:
            return {
                'analysis': content,
                'entities': {},
                'suggestions': []
            }

    def _test_ollama(self) -> Dict:
        """测试Ollama连接"""
        url = f"{self.base_url or 'http://localhost:11434'}/api/tags"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        models = response.json().get('models', [])
        model_names = [m['name'] for m in models]

        if self.model in model_names:
            return {'success': True, 'message': f'连接成功，找到模型: {self.model}'}
        else:
            return {
                'success': True,
                'message': f'连接成功，但未找到模型 {self.model}，可用模型: {", ".join(model_names[:5])}'
            }

    def _test_openai(self) -> Dict:
        """测试OpenAI连接"""
        if not self.api_key:
            return {'success': False, 'message': '未配置API密钥'}

        try:
            client = self._get_openai_client()
            # 列出可用模型来验证连接
            client.models.list()
            return {'success': True, 'message': 'OpenAI API连接成功'}
        except openai.AuthenticationError:
            return {'success': False, 'message': 'API密钥无效'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def _test_claude(self) -> Dict:
        """测试Claude连接"""
        if not self.api_key:
            return {'success': False, 'message': '未配置API密钥'}

        try:
            client = self._get_anthropic_client()
            # 发送一个最小的请求来验证连接
            client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{'role': 'user', 'content': 'Hi'}]
            )
            return {'success': True, 'message': 'Claude API连接成功'}
        except anthropic.AuthenticationError:
            return {'success': False, 'message': 'API密钥无效'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def _chat_ollama(self, messages: List[Dict]) -> Dict:
        """调用Ollama聊天"""
        url = f"{self.base_url or 'http://localhost:11434'}/api/chat"

        # 构建prompt
        prompt = self._messages_to_prompt(messages)

        data = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens
            }
        }

        # 使用可配置的超时时间
        timeout = getattr(self.config, 'timeout_seconds', 120)
        response = requests.post(url, json=data, timeout=timeout)
        response.raise_for_status()

        result = response.json()
        return {
            'message': result.get('message', {}).get('content', ''),
            'metadata': {'provider': 'ollama', 'model': self.model}
        }

    def _chat_openai(self, messages: List[Dict]) -> Dict:
        """调用OpenAI聊天 - 使用官方SDK"""
        if not self.api_key:
            raise ValueError('OpenAI API密钥未配置')

        client = self._get_openai_client()

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        return {
            'message': response.choices[0].message.content,
            'metadata': {
                'provider': 'openai',
                'model': self.model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens if response.usage else 0,
                    'completion_tokens': response.usage.completion_tokens if response.usage else 0,
                    'total_tokens': response.usage.total_tokens if response.usage else 0
                }
            }
        }

    def _chat_claude(self, messages: List[Dict]) -> Dict:
        """调用Claude聊天 - 使用官方SDK"""
        if not self.api_key:
            raise ValueError('Claude API密钥未配置')

        client = self._get_anthropic_client()

        # 提取system message
        system_message = None
        chat_messages = []
        for msg in messages:
            if msg['role'] == 'system':
                system_message = msg['content']
            else:
                chat_messages.append(msg)

        # 构建请求参数
        request_params = {
            "model": self.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": chat_messages
        }

        if system_message:
            request_params["system"] = system_message

        response = client.messages.create(**request_params)

        return {
            'message': response.content[0].text,
            'metadata': {
                'provider': 'claude',
                'model': self.model,
                'usage': {
                    'input_tokens': response.usage.input_tokens if response.usage else 0,
                    'output_tokens': response.usage.output_tokens if response.usage else 0
                }
            }
        }

    def _messages_to_prompt(self, messages: List[Dict]) -> str:
        """将消息列表转换为Ollama提示"""
        prompt = ""
        for msg in messages:
            if msg['role'] == 'system':
                prompt += f"System: {msg['content']}\n\n"
            elif msg['role'] == 'user':
                prompt += f"User: {msg['content']}\n\n"
            elif msg['role'] == 'assistant':
                prompt += f"Assistant: {msg['content']}\n\n"
        prompt += "Assistant: "
        return prompt