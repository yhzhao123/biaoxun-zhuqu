"""
LLM Services Tests - 使用官方SDK的测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List


# 模拟LLMConfig
class MockLLMConfig:
    def __init__(self, provider='ollama', api_key='test-key', api_base_url=None,
                 model_name='test-model', temperature=0.7, max_tokens=2000,
                 timeout_seconds=120):
        self.provider = provider
        self.api_key = api_key
        self.api_base_url = api_base_url
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds


class TestOpenAIService:
    """OpenAI服务测试 - 使用官方SDK"""

    @patch('apps.llm.services.openai.OpenAI')
    def test_chat_openai_with_sdk(self, mock_openai_class):
        """测试使用openai官方SDK调用chat completion"""
        from apps.llm.services import LLMService

        # Setup mock - 使用完整的对象模拟而不是dict
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # 模拟完整的使用量对象
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        # Execute
        config = MockLLMConfig(
            provider='openai',
            api_key='sk-test-key',
            model_name='gpt-4'
        )
        service = LLMService(config)

        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant'},
            {'role': 'user', 'content': 'Hello'}
        ]
        result = service._chat_openai(messages)

        # Verify
        assert result['message'] == "Test response"
        assert result['metadata']['provider'] == 'openai'
        assert result['metadata']['model'] == 'gpt-4'
        mock_client.chat.completions.create.assert_called_once()

    @patch('apps.llm.services.openai.OpenAI')
    def test_chat_openai_api_error(self, mock_openai_class):
        """测试OpenAI API错误时的错误处理"""
        from apps.llm.services import LLMService

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # 直接抛出异常
        mock_client.chat.completions.create.side_effect = Exception("API Error: 401 Invalid API key")

        config = MockLLMConfig(provider='openai', api_key='invalid-key')
        service = LLMService(config)

        messages = [{'role': 'user', 'content': 'Hello'}]

        with pytest.raises(Exception, match="API Error"):
            service._chat_openai(messages)

    @patch('apps.llm.services.openai.OpenAI')
    def test_chat_openai_timeout_error(self, mock_openai_class):
        """测试OpenAI超时错误处理"""
        from apps.llm.services import LLMService
        import openai

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = openai.APITimeoutError(
            "Request timed out"
        )

        config = MockLLMConfig(provider='openai', api_key='sk-test-key')
        service = LLMService(config)

        messages = [{'role': 'user', 'content': 'Hello'}]

        with pytest.raises(openai.APITimeoutError):
            service._chat_openai(messages)


class TestClaudeService:
    """Claude服务测试 - 使用官方SDK"""

    @patch('apps.llm.services.anthropic.Anthropic')
    def test_chat_claude_with_sdk(self, mock_anthropic_class):
        """测试使用anthropic官方SDK调用messages API"""
        from apps.llm.services import LLMService

        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # 模拟完整的使用量对象
        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 20

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Claude response"
        mock_response.usage = mock_usage
        mock_client.messages.create.return_value = mock_response

        # Execute
        config = MockLLMConfig(
            provider='claude',
            api_key='sk-ant-test-key',
            model_name='claude-3-opus-20240229'
        )
        service = LLMService(config)

        messages = [
            {'role': 'system', 'content': 'You are a helpful assistant'},
            {'role': 'user', 'content': 'Hello'}
        ]
        result = service._chat_claude(messages)

        # Verify
        assert result['message'] == "Claude response"
        assert result['metadata']['provider'] == 'claude'
        assert result['metadata']['model'] == 'claude-3-opus-20240229'
        mock_client.messages.create.assert_called_once()

    @patch('apps.llm.services.anthropic.Anthropic')
    def test_chat_claude_api_error(self, mock_anthropic_class):
        """测试Claude API错误时的错误处理"""
        from apps.llm.services import LLMService

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        # 直接抛出异常
        mock_client.messages.create.side_effect = Exception("API Error: Invalid API key")

        config = MockLLMConfig(provider='claude', api_key='invalid-key')
        service = LLMService(config)

        messages = [{'role': 'user', 'content': 'Hello'}]

        with pytest.raises(Exception, match="API Error"):
            service._chat_claude(messages)


class TestOllamaService:
    """Ollama服务测试 - 继续使用requests"""

    @patch('apps.llm.services.requests.post')
    @patch('apps.llm.services.requests.get')
    def test_chat_ollama(self, mock_get, mock_post):
        """测试Ollama聊天功能"""
        from apps.llm.services import LLMService

        # Setup mock responses
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'message': {'content': 'Ollama response'}
        }
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        config = MockLLMConfig(
            provider='ollama',
            api_base_url='http://localhost:11434',
            model_name='qwen2.5:7b'
        )
        service = LLMService(config)

        messages = [{'role': 'user', 'content': 'Hello'}]
        result = service._chat_ollama(messages)

        assert result['message'] == 'Ollama response'
        assert result['metadata']['provider'] == 'ollama'
        mock_post.assert_called_once()

    @patch('apps.llm.services.requests.get')
    def test_test_connection_ollama(self, mock_get):
        """测试Ollama连接测试"""
        from apps.llm.services import LLMService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'models': [{'name': 'qwen2.5:7b'}, {'name': 'llama2:7b'}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        config = MockLLMConfig(
            provider='ollama',
            api_base_url='http://localhost:11434',
            model_name='qwen2.5:7b'
        )
        service = LLMService(config)

        result = service._test_ollama()

        assert result['success'] is True
        assert 'qwen2.5:7b' in result['message']


class TestLLMServiceFactory:
    """LLMService工厂方法测试"""

    def test_service_creation_by_provider(self):
        """测试根据provider类型创建正确的服务"""
        from apps.llm.services import LLMService

        # Test Ollama
        config = MockLLMConfig(provider='ollama', model_name='qwen2.5:7b')
        service = LLMService(config)
        assert service.provider == 'ollama'

        # Test OpenAI
        config = MockLLMConfig(provider='openai', api_key='sk-test', model_name='gpt-4')
        service = LLMService(config)
        assert service.provider == 'openai'

        # Test Claude
        config = MockLLMConfig(provider='claude', api_key='sk-ant-test', model_name='claude-3-opus')
        service = LLMService(config)
        assert service.provider == 'claude'

    def test_chat_dispatch_by_provider(self):
        """测试chat方法根据provider分发到正确的实现"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(provider='ollama')
        service = LLMService(config)

        with patch.object(service, '_chat_ollama') as mock_ollama:
            mock_ollama.return_value = {'message': 'test'}
            service.chat([], 'hello')
            mock_ollama.assert_called_once()


class TestConfigValidation:
    """配置验证测试"""

    def test_openai_requires_api_key(self):
        """测试OpenAI需要API密钥"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(provider='openai', api_key='')
        service = LLMService(config)

        with pytest.raises(ValueError, match='API密钥未配置'):
            service._chat_openai([{'role': 'user', 'content': 'hello'}])

    def test_claude_requires_api_key(self):
        """测试Claude需要API密钥"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(provider='claude', api_key='')
        service = LLMService(config)

        with pytest.raises(ValueError, match='API密钥未配置'):
            service._chat_claude([{'role': 'user', 'content': 'hello'}])

    def test_unknown_provider_raises_error(self):
        """测试未知provider抛出错误"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(provider='unknown')
        service = LLMService(config)

        with pytest.raises(ValueError, match='未知的提供商'):
            service.chat([], 'hello')


class TestBackwardCompatibility:
    """向后兼容性测试"""

    @patch('apps.llm.services.openai.OpenAI')
    @patch('apps.llm.services.anthropic.Anthropic')
    def test_chat_interface_compatibility(self, mock_anthropic, mock_openai):
        """测试chat接口保持向后兼容"""
        from apps.llm.services import LLMService

        # Setup OpenAI mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        config = MockLLMConfig(
            provider='openai',
            api_key='sk-test',
            model_name='gpt-4'
        )
        service = LLMService(config)

        # Test that the public interface works
        context = [{'role': 'system', 'content': 'You are helpful'}]
        message = 'What is the weather?'

        result = service.chat(context, message)

        assert 'message' in result
        assert isinstance(result['message'], str)

    def test_analyze_tender_works(self):
        """测试analyze_tender方法正常工作"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(provider='ollama', model_name='qwen2.5:7b')
        service = LLMService(config)

        with patch.object(service, '_chat_ollama') as mock_chat:
            mock_chat.return_value = {
                'message': '{"entities": {"tenderer": "Test"}, "analysis": "Test analysis", "suggestions": []}'
            }

            result = service.analyze_tender("Test tender content")

            assert 'analysis' in result
            assert 'entities' in result
            assert 'suggestions' in result


class TestSDKClientInitialization:
    """SDK客户端初始化测试"""

    @patch('apps.llm.services.openai.OpenAI')
    def test_openai_client_lazy_initialization(self, mock_openai_class):
        """测试OpenAI客户端延迟初始化"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(
            provider='openai',
            api_key='sk-test',
            model_name='gpt-4'
        )
        service = LLMService(config)

        # 客户端不应该在初始化时创建
        assert service._openai_client is None

        # 第一次调用时创建
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test"
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        service._chat_openai([{'role': 'user', 'content': 'Hello'}])

        # 验证客户端已创建
        assert service._openai_client is not None
        mock_openai_class.assert_called_once()

    @patch('apps.llm.services.anthropic.Anthropic')
    def test_anthropic_client_lazy_initialization(self, mock_anthropic_class):
        """测试Anthropic客户端延迟初始化"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(
            provider='claude',
            api_key='sk-ant-test',
            model_name='claude-3-opus'
        )
        service = LLMService(config)

        # 客户端不应该在初始化时创建
        assert service._anthropic_client is None

        # 第一次调用时创建
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 20
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test"
        mock_response.usage = mock_usage
        mock_client.messages.create.return_value = mock_response

        service._chat_claude([{'role': 'user', 'content': 'Hello'}])

        # 验证客户端已创建
        assert service._anthropic_client is not None
        mock_anthropic_class.assert_called_once()


class TestEdgeCases:
    """边界情况测试"""

    @patch('apps.llm.services.openai.OpenAI')
    def test_openai_empty_messages(self, mock_openai_class):
        """测试OpenAI处理空消息列表"""
        from apps.llm.services import LLMService

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 0
        mock_usage.completion_tokens = 10
        mock_usage.total_tokens = 10
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        config = MockLLMConfig(provider='openai', api_key='sk-test')
        service = LLMService(config)

        result = service._chat_openai([])

        assert result['message'] == "Response"

    @patch('apps.llm.services.anthropic.Anthropic')
    def test_claude_empty_messages(self, mock_anthropic_class):
        """测试Claude处理空消息列表"""
        from apps.llm.services import LLMService

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.input_tokens = 0
        mock_usage.output_tokens = 10
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage = mock_usage
        mock_client.messages.create.return_value = mock_response

        config = MockLLMConfig(provider='claude', api_key='sk-ant-test')
        service = LLMService(config)

        result = service._chat_claude([])

        assert result['message'] == "Response"

    def test_ollama_with_custom_base_url(self):
        """测试Ollama使用自定义base_url"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(
            provider='ollama',
            api_base_url='http://custom:11434',
            model_name='llama2'
        )
        service = LLMService(config)

        with patch('apps.llm.services.requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {'message': {'content': 'Test'}}
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response

            service._chat_ollama([{'role': 'user', 'content': 'Hi'}])

            # 验证使用了自定义URL
            call_url = mock_post.call_args[1]['json']['model']
            assert call_url == 'llama2'


class TestConnectionTesting:
    """连接测试方法测试"""

    @patch('apps.llm.services.openai.OpenAI')
    def test_test_connection_openai_success(self, mock_openai_class):
        """测试OpenAI连接成功"""
        from apps.llm.services import LLMService

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        config = MockLLMConfig(provider='openai', api_key='sk-test')
        service = LLMService(config)

        result = service._test_openai()

        assert result['success'] is True
        assert '成功' in result['message']

    @patch('apps.llm.services.openai.OpenAI')
    def test_test_connection_openai_no_api_key(self, mock_openai_class):
        """测试OpenAI无API密钥"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(provider='openai', api_key='')
        service = LLMService(config)

        result = service._test_openai()

        assert result['success'] is False
        assert 'API密钥' in result['message']

    @patch('apps.llm.services.openai.OpenAI')
    def test_test_connection_openai_auth_error(self, mock_openai_class):
        """测试OpenAI认证错误处理"""
        from apps.llm.services import LLMService
        import openai

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        # 使用简单的异常
        mock_client.models.list.side_effect = Exception("AuthenticationError: Invalid API key")

        config = MockLLMConfig(provider='openai', api_key='invalid')
        service = LLMService(config)

        result = service._test_openai()

        assert result['success'] is False

    @patch('apps.llm.services.anthropic.Anthropic')
    def test_test_connection_claude_success(self, mock_anthropic_class):
        """测试Claude连接成功"""
        from apps.llm.services import LLMService

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        config = MockLLMConfig(provider='claude', api_key='sk-ant-test', model_name='claude-3-opus')
        service = LLMService(config)

        result = service._test_claude()

        assert result['success'] is True

    @patch('apps.llm.services.anthropic.Anthropic')
    def test_test_connection_claude_no_api_key(self, mock_anthropic_class):
        """测试Claude无API密钥"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(provider='claude', api_key='')
        service = LLMService(config)

        result = service._test_claude()

        assert result['success'] is False

    @patch('apps.llm.services.anthropic.Anthropic')
    def test_test_connection_claude_auth_error(self, mock_anthropic_class):
        """测试Claude认证错误处理"""
        from apps.llm.services import LLMService
        import anthropic

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        # 使用简单的异常
        mock_client.messages.create.side_effect = Exception("AuthenticationError: Invalid API key")

        config = MockLLMConfig(provider='claude', api_key='invalid')
        service = LLMService(config)

        result = service._test_claude()

        assert result['success'] is False

    @patch('apps.llm.services.requests.get')
    def test_test_connection_ollama_model_not_found(self, mock_get):
        """测试Ollama模型未找到"""
        from apps.llm.services import LLMService

        mock_response = MagicMock()
        mock_response.json.return_value = {
            'models': [{'name': 'llama2:7b'}, {'name': 'mistral:7b'}]
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        config = MockLLMConfig(
            provider='ollama',
            model_name='nonexistent-model'
        )
        service = LLMService(config)

        result = service._test_ollama()

        assert result['success'] is True
        assert '未找到模型' in result['message']

    def test_test_connection_unknown_provider(self):
        """测试未知provider"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(provider='unknown')
        service = LLMService(config)

        result = service.test_connection()

        assert result['success'] is False
        assert '未知' in result['message']

    def test_test_connection_exception_handling(self):
        """测试连接异常处理"""
        from apps.llm.services import LLMService

        config = MockLLMConfig(provider='ollama', api_base_url='http://invalid:9999')
        service = LLMService(config)

        with patch('apps.llm.services.requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection refused")

            result = service.test_connection()

            assert result['success'] is False
            assert 'Connection refused' in result['message']


class TestTimeoutConfiguration:
    """超时配置测试"""

    @patch('apps.llm.services.openai.OpenAI')
    def test_openai_client_uses_httpx_timeout(self, mock_openai_class):
        """测试OpenAI客户端使用httpx.Timeout而非requests.Timeout"""
        from apps.llm.services import LLMService
        from httpx import Timeout

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test"
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        config = MockLLMConfig(
            provider='openai',
            api_key='sk-test',
            model_name='gpt-4',
            timeout_seconds=60
        )
        service = LLMService(config)

        # 调用以触发客户端创建
        service._chat_openai([{'role': 'user', 'content': 'Hello'}])

        # 验证使用了httpx.Timeout
        call_kwargs = mock_openai_class.call_args[1]
        assert 'timeout' in call_kwargs
        assert isinstance(call_kwargs['timeout'], Timeout), \
            f"Expected httpx.Timeout, got {type(call_kwargs['timeout'])}"

    @patch('apps.llm.services.anthropic.Anthropic')
    def test_anthropic_client_uses_httpx_timeout(self, mock_anthropic_class):
        """测试Anthropic客户端使用httpx.Timeout而非整数"""
        from apps.llm.services import LLMService
        from httpx import Timeout

        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.input_tokens = 10
        mock_usage.output_tokens = 20
        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Test"
        mock_response.usage = mock_usage
        mock_client.messages.create.return_value = mock_response

        config = MockLLMConfig(
            provider='claude',
            api_key='sk-ant-test',
            model_name='claude-3-opus',
            timeout_seconds=90
        )
        service = LLMService(config)

        # 调用以触发客户端创建
        service._chat_claude([{'role': 'user', 'content': 'Hello'}])

        # 验证使用了httpx.Timeout
        call_kwargs = mock_anthropic_class.call_args[1]
        assert 'timeout' in call_kwargs
        assert isinstance(call_kwargs['timeout'], Timeout), \
            f"Expected httpx.Timeout, got {type(call_kwargs['timeout'])}"

    @patch('apps.llm.services.openai.OpenAI')
    def test_openai_client_default_timeout(self, mock_openai_class):
        """测试OpenAI客户端默认超时值"""
        from apps.llm.services import LLMService
        from httpx import Timeout

        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20
        mock_usage.total_tokens = 30
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test"
        mock_response.usage = mock_usage
        mock_client.chat.completions.create.return_value = mock_response

        # 不设置timeout_seconds，使用默认值120
        config = MockLLMConfig(
            provider='openai',
            api_key='sk-test',
            model_name='gpt-4'
        )
        service = LLMService(config)
        service._chat_openai([{'role': 'user', 'content': 'Hello'}])

        # 验证使用了默认超时值120
        call_kwargs = mock_openai_class.call_args[1]
        assert call_kwargs['timeout'].connect == 120