"""
LLM Serializers - 序列化器
"""
from rest_framework import serializers
from .models import LLMConfig, ChatConversation


class LLMConfigSerializer(serializers.ModelSerializer):
    """LLM配置序列化器"""

    class Meta:
        model = LLMConfig
        fields = [
            'id', 'provider', 'name', 'api_key', 'api_base_url',
            'model_name', 'temperature', 'max_tokens',
            'is_active', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'api_key': {'write_only': True},  # API密钥不返回给前端
        }


class LLMConfigListSerializer(serializers.ModelSerializer):
    """LLM配置列表序列化器（不返回API密钥）"""

    class Meta:
        model = LLMConfig
        fields = [
            'id', 'provider', 'name', 'api_base_url',
            'model_name', 'temperature', 'max_tokens',
            'is_active', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ChatMessageSerializer(serializers.Serializer):
    """聊天消息序列化器"""
    role = serializers.ChoiceField(
        choices=['user', 'assistant', 'system']
    )
    content = serializers.CharField()
    timestamp = serializers.DateTimeField(required=False)
    metadata = serializers.DictField(required=False, allow_null=True)


class ChatConversationSerializer(serializers.ModelSerializer):
    """对话记录序列化器"""
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatConversation
        fields = [
            'id', 'title', 'messages', 'tender_id',
            'llm_config', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class ChatRequestSerializer(serializers.Serializer):
    """聊天请求序列化器"""
    message = serializers.CharField(required=True)
    conversation_id = serializers.IntegerField(required=False, allow_null=True)
    tender_id = serializers.CharField(required=False, allow_null=True)
    llm_config_id = serializers.IntegerField(required=False, allow_null=True)


class ChatResponseSerializer(serializers.Serializer):
    """聊天响应序列化器"""
    message = serializers.CharField()
    conversation_id = serializers.IntegerField()
    extracted_entities = serializers.DictField(required=False)
