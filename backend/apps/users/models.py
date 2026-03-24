"""
用户模型
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from .mixins import TimestampMixin, SoftDeleteMixin


class User(AbstractUser, TimestampMixin, SoftDeleteMixin):
    """自定义用户模型"""
    username = models.CharField(max_length=150, unique=True, verbose_name='用户名')
    email = models.EmailField(unique=True, verbose_name='邮箱')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, verbose_name='头像')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')

    # RBAC fields
    role = models.CharField(
        max_length=20,
        choices=[
            ('admin', '管理员'),
            ('manager', '经理'),
            ('user', '普通用户'),
            ('viewer', '访客'),
        ],
        default='user',
        verbose_name='角色'
    )
    extra_permissions = models.JSONField(default=list, blank=True, verbose_name='额外权限')
    tenant_id = models.CharField(max_length=100, blank=True, verbose_name='租户ID')

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username