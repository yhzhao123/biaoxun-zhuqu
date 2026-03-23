"""
基础模型Mixin
"""
from django.db import models
from django.utils import timezone


class TimestampMixin(models.Model):
    """时间戳Mixin - 自动管理创建和更新时间"""
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """软删除Mixin - 逻辑删除而非物理删除"""
    is_deleted = models.BooleanField(default=False, verbose_name='已删除')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """软删除"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(using=using)

    def hard_delete(self):
        """物理删除"""
        super().delete()

    def restore(self):
        """恢复软删除"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()