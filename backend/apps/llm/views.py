"""
LLM API Views - 大模型配置和对话API
"""
import os
import requests
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import LLMConfig, ChatConversation
from .serializers import (
    LLMConfigSerializer, LLMConfigListSerializer,
    ChatConversationSerializer, ChatRequestSerializer, ChatResponseSerializer
)


class LLMConfigViewSet(viewsets.ModelViewSet):
    """
    LLM配置API视图集
    支持CRUD操作和连接测试
    """
    queryset = LLMConfig.objects.all()

    def get_permissions(self):
        """根据action返回不同的权限类"""
        if self.action == 'health':
            return [AllowAny()]
        # 在DEBUG模式下允许无认证访问
        if os.environ.get('DJANGO_SETTINGS_MODULE') == 'config.settings_dev' or \
           os.environ.get('DEBUG') in ('1', 'true', 'True'):
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'list':
            return LLMConfigListSerializer
        return LLMConfigSerializer

    def get_queryset(self):
        """返回配置列表"""
        # 开发模式或未认证用户返回所有配置
        if self.request.user.is_anonymous:
            return LLMConfig.objects.all()
        return LLMConfig.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """创建时关联用户，如果是第一个配置则自动设为默认"""
        user = self.request.user if self.request.user.is_authenticated else None

        # 检查是否已有配置
        existing_configs = LLMConfig.objects.filter(user=user) if user else LLMConfig.objects.all()
        is_first_config = not existing_configs.exists()

        serializer.save(
            user=user,
            is_default=is_first_config  # 第一个配置自动设为默认
        )

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def health(self, request):
        """
        LLM服务健康检查 (无需认证)
        GET /api/v1/llm/configs/health/

        检查各LLM提供商的连接状态，帮助用户诊断问题。
        """
        results = {}

        # 检查Ollama
        ollama_url = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
        try:
            response = requests.get(f'{ollama_url}/api/tags', timeout=5)
            if response.status_code == 200:
                models = [m['name'] for m in response.json().get('models', [])]
                results['ollama'] = {
                    'available': True,
                    'models': models,
                    'url': ollama_url
                }
            else:
                results['ollama'] = {
                    'available': False,
                    'error': f'HTTP {response.status_code}',
                    'url': ollama_url
                }
        except requests.exceptions.ConnectionError:
            results['ollama'] = {
                'available': False,
                'error': '无法连接 - 请确认Ollama服务是否运行',
                'url': ollama_url,
                'solution': '运行 "ollama serve" 启动服务'
            }
        except requests.exceptions.Timeout:
            results['ollama'] = {
                'available': False,
                'error': '连接超时',
                'url': ollama_url
            }
        except Exception as e:
            results['ollama'] = {
                'available': False,
                'error': str(e),
                'url': ollama_url
            }

        # 检查OpenAI
        openai_key = os.environ.get('OPENAI_API_KEY')
        if openai_key:
            try:
                response = requests.get(
                    'https://api.openai.com/v1/models',
                    headers={'Authorization': f'Bearer {openai_key}'},
                    timeout=10
                )
                if response.status_code == 200:
                    results['openai'] = {'available': True, 'configured': True}
                elif response.status_code == 401:
                    results['openai'] = {
                        'available': False,
                        'configured': True,
                        'error': 'API密钥无效'
                    }
                else:
                    results['openai'] = {
                        'available': False,
                        'configured': True,
                        'error': f'HTTP {response.status_code}'
                    }
            except Exception as e:
                results['openai'] = {
                    'available': False,
                    'configured': True,
                    'error': str(e)
                }
        else:
            results['openai'] = {
                'available': False,
                'configured': False,
                'solution': '设置环境变量 OPENAI_API_KEY'
            }

        # 检查Claude
        claude_key = os.environ.get('ANTHROPIC_API_KEY')
        if claude_key:
            try:
                response = requests.get(
                    'https://api.anthropic.com/v1/models',
                    headers={
                        'x-api-key': claude_key,
                        'anthropic-version': '2023-06-01'
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    results['claude'] = {'available': True, 'configured': True}
                elif response.status_code == 401:
                    results['claude'] = {
                        'available': False,
                        'configured': True,
                        'error': 'API密钥无效'
                    }
                else:
                    results['claude'] = {
                        'available': False,
                        'configured': True,
                        'error': f'HTTP {response.status_code}'
                    }
            except Exception as e:
                results['claude'] = {
                    'available': False,
                    'configured': True,
                    'error': str(e)
                }
        else:
            results['claude'] = {
                'available': False,
                'configured': False,
                'solution': '设置环境变量 ANTHROPIC_API_KEY'
            }

        # 生成建议
        recommendations = []
        if not results['ollama'].get('available'):
            recommendations.append({
                'provider': 'ollama',
                'action': '启动Ollama服务',
                'command': 'ollama serve'
            })
        if not results['openai'].get('configured'):
            recommendations.append({
                'provider': 'openai',
                'action': '配置OpenAI API密钥',
                'env_var': 'OPENAI_API_KEY'
            })
        if not results['claude'].get('configured'):
            recommendations.append({
                'provider': 'claude',
                'action': '配置Anthropic API密钥',
                'env_var': 'ANTHROPIC_API_KEY'
            })

        return Response({
            'status': 'ok',
            'providers': results,
            'recommendations': recommendations
        })

    @action(detail=True, methods=['post'])
    def test(self, request, pk=None):
        """
        测试LLM连接
        POST /api/v1/llm/configs/{id}/test/
        """
        config = self.get_object()

        try:
            # 导入服务模块
            from .services import LLMService

            service = LLMService(config)
            result = service.test_connection()

            return Response({
                'success': result['success'],
                'message': result['message'],
                'provider': config.provider,
                'model': config.model_name,
                'details': result.get('details', {})
            })
        except requests.exceptions.ConnectionError as e:
            error_msg = '无法连接到服务'
            solution = None

            if config.provider == 'ollama':
                error_msg = 'Ollama服务未运行'
                solution = '请运行 "ollama serve" 启动服务'

            return Response({
                'success': False,
                'message': error_msg,
                'provider': config.provider,
                'error_type': 'connection_error',
                'solution': solution
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'message': '连接超时',
                'provider': config.provider,
                'error_type': 'timeout',
                'solution': '请检查网络连接或增加超时时间'
            }, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.exceptions.HTTPError as e:
            error_msg = f'HTTP错误: {e.response.status_code}'
            solution = None

            if e.response.status_code == 401:
                error_msg = 'API密钥无效或未配置'
                solution = '请检查API密钥是否正确'
            elif e.response.status_code == 403:
                error_msg = 'API访问被拒绝'
                solution = '请检查API密钥权限或账户状态'
            elif e.response.status_code == 404:
                error_msg = 'API端点不存在或模型不可用'
                solution = '请检查模型名称是否正确'

            return Response({
                'success': False,
                'message': error_msg,
                'provider': config.provider,
                'error_type': 'http_error',
                'status_code': e.response.status_code,
                'solution': solution
            }, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'测试失败: {str(e)}',
                'provider': config.provider,
                'error_type': 'unknown',
                'error_detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        设置为默认配置
        POST /api/v1/llm/configs/{id}/activate/
        """
        config = self.get_object()

        # 取消其他默认配置
        if request.user.is_authenticated:
            LLMConfig.objects.filter(user=request.user).update(is_default=False)
        else:
            LLMConfig.objects.all().update(is_default=False)

        # 设置当前为默认
        config.is_default = True
        config.save()

        return Response({
            'success': True,
            'message': '已设置为默认配置',
            'config_id': config.id
        })

    @action(detail=False, methods=['get'])
    def default(self, request):
        """
        获取默认配置
        GET /api/v1/llm/configs/default/
        """
        try:
            if request.user.is_authenticated:
                config = LLMConfig.objects.get(user=request.user, is_default=True)
            else:
                config = LLMConfig.objects.get(is_default=True)
            serializer = self.get_serializer(config)
            return Response(serializer.data)
        except LLMConfig.DoesNotExist:
            return Response({
                'detail': '未找到默认配置'
            }, status=status.HTTP_404_NOT_FOUND)


class ChatViewSet(viewsets.ViewSet):
    """
    对话API视图集
    """

    def get_permissions(self):
        """根据环境返回权限类"""
        if os.environ.get('DJANGO_SETTINGS_MODULE') == 'config.settings_dev' or \
           os.environ.get('DEBUG', '').lower() == 'true':
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request):
        """获取对话列表"""
        if request.user.is_anonymous:
            conversations = ChatConversation.objects.all()
        else:
            conversations = ChatConversation.objects.filter(user=request.user)
        serializer = ChatConversationSerializer(conversations, many=True)
        return Response(serializer.data)

    def create(self, request):
        """创建新对话"""
        title = request.data.get('title', '新对话')
        tender_id = request.data.get('tender_id')

        # 获取默认配置
        if request.user.is_anonymous:
            llm_config = LLMConfig.objects.filter(is_default=True, is_active=True).first()
        else:
            llm_config = LLMConfig.objects.filter(
                user=request.user, is_default=True, is_active=True
            ).first()

        conversation = ChatConversation.objects.create(
            user=request.user if request.user.is_authenticated else None,
            title=title,
            tender_id=tender_id,
            llm_config=llm_config
        )

        serializer = ChatConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        """获取单个对话"""
        try:
            if request.user.is_anonymous:
                conversation = ChatConversation.objects.get(id=pk)
            else:
                conversation = ChatConversation.objects.get(id=pk, user=request.user)
            serializer = ChatConversationSerializer(conversation)
            return Response(serializer.data)
        except ChatConversation.DoesNotExist:
            return Response(
                {'detail': '对话不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, pk=None):
        """删除对话"""
        try:
            if request.user.is_anonymous:
                conversation = ChatConversation.objects.get(id=pk)
            else:
                conversation = ChatConversation.objects.get(id=pk, user=request.user)
            conversation.delete()
            return Response({'success': True})
        except ChatConversation.DoesNotExist:
            return Response(
                {'detail': '对话不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """
        发送消息
        POST /api/v1/llm/chat/{id}/send/
        """
        try:
            if request.user.is_anonymous:
                conversation = ChatConversation.objects.get(id=pk)
            else:
                conversation = ChatConversation.objects.get(id=pk, user=request.user)
        except ChatConversation.DoesNotExist:
            return Response(
                {'detail': '对话不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        message = request.data.get('message', '').strip()
        if not message:
            return Response(
                {'detail': '消息不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 添加用户消息
        conversation.add_message('user', message)

        # 获取LLM响应
        try:
            from .services import LLMService

            llm_config = conversation.llm_config
            if not llm_config:
                return Response({
                    'detail': '未配置LLM，请先设置默认配置'
                }, status=status.HTTP_400_BAD_REQUEST)

            service = LLMService(llm_config)

            # 构建上下文
            context = self._build_context(conversation)

            # 调用LLM
            response = service.chat(context, message)

            # 添加助手消息
            conversation.add_message(
                'assistant',
                response['message'],
                metadata=response.get('metadata')
            )

            return Response({
                'message': response['message'],
                'conversation_id': conversation.id,
                'extracted_entities': response.get('extracted_entities', {})
            })

        except Exception as e:
            return Response({
                'detail': f'LLM调用失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='analyze-tender')
    def analyze_tender(self, request):
        """
        分析招标信息
        POST /api/v1/llm/chat/analyze-tender/
        """
        tender_id = request.data.get('tender_id')
        tender_content = request.data.get('content', '')
        question = request.data.get('question', '')

        if not tender_content:
            return Response({
                'detail': '请提供招标内容'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 获取默认配置
        if request.user.is_anonymous:
            llm_config = LLMConfig.objects.filter(is_default=True, is_active=True).first()
        else:
            llm_config = LLMConfig.objects.filter(
                user=request.user, is_default=True, is_active=True
            ).first()

        if not llm_config:
            return Response({
                'detail': '未配置LLM，请先设置默认配置'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            from .services import LLMService

            service = LLMService(llm_config)
            result = service.analyze_tender(tender_content, question)

            return Response({
                'analysis': result['analysis'],
                'extracted_entities': result.get('entities', {}),
                'suggestions': result.get('suggestions', [])
            })

        except Exception as e:
            return Response({
                'detail': f'分析失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _build_context(self, conversation):
        """构建对话上下文"""
        context = []

        # 添加系统提示
        context.append({
            'role': 'system',
            'content': '你是一个招标信息分析助手，擅长从招标文档中提取关键信息并回答相关问题。'
        })

        # 添加历史消息（最近20条）
        messages = conversation.messages[-20:] if len(conversation.messages) > 20 else conversation.messages
        for msg in messages:
            context.append({
                'role': msg['role'],
                'content': msg['content']
            })

        return context
