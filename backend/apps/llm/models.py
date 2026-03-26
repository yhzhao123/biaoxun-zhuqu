"""
LLM Models - 大模型配置和对话记录
"""
from django.db import models
from django.conf import settings


class LLMProvider(models.TextChoices):
    """LLM提供商选项"""
    OLLAMA = 'ollama', 'Ollama (本地)'
    OPENAI = 'openai', 'OpenAI'
    CLAUDE = 'claude', 'Claude (Anthropic)'


class LLMConfig(models.Model):
    """
    大模型配置模型
    支持Ollama、OpenAI、Claude等多种提供商
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='llm_configs',
        verbose_name='用户'
    )
    provider = models.CharField(
        max_length=20,
        choices=LLMProvider.choices,
        default=LLMProvider.OLLAMA,
        verbose_name='提供商'
    )
    name = models.CharField(max_length=100, verbose_name='配置名称')
    api_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='API密钥'
    )
    api_base_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name='API基础URL'
    )
    model_name = models.CharField(
        max_length=100,
        default='qwen2.5:7b',
        verbose_name='模型名称'
    )
    temperature = models.FloatField(default=0.7, verbose_name='温度参数')
    max_tokens = models.IntegerField(default=2000, verbose_name='最大Token数')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    is_default = models.BooleanField(default=False, verbose_name='默认配置')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'llm_configs'
        verbose_name = 'LLM配置'
        verbose_name_plural = 'LLM配置'
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.name} ({self.provider})"


class ChatConversation(models.Model):
    """
    对话记录模型
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chat_conversations',
        verbose_name='用户'
    )
    title = models.CharField(max_length=200, verbose_name='对话标题')
    messages = models.JSONField(default=list, verbose_name='消息记录')
    tender_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name='关联招标ID'
    )
    llm_config = models.ForeignKey(
        LLMConfig,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='使用的LLM配置'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'llm_conversations'
        verbose_name = '对话记录'
        verbose_name_plural = '对话记录'
        ordering = ['-updated_at']

    def __str__(self):
        return self.title

    def add_message(self, role: str, content: str, metadata: dict = None):
        """添加消息到对话"""
        message = {
            'role': role,
            'content': content,
            'timestamp': self.updated_at.isoformat() if self.updated_at else None
        }
        if metadata:
            message['metadata'] = metadata
        self.messages.append(message)
        self.save()
