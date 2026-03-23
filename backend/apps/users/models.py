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

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'

    def __str__(self):
        return self.username