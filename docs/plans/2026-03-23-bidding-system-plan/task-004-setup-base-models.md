# Task 004: 创建基础模型和Admin

**Task ID:** 004
**Task Name:** 创建基础模型和Admin
**Type:** setup
**Depends-on:** [002]
**Status:** pending

---

## Description

Create base model classes with timestamp mixin, soft delete functionality, and admin base configuration. This provides the foundation for all domain models in the bidding system.

---

## Files to Create

| File | Purpose |
|------|---------|
| `apps/core/models/__init__.py` | Core models package |
| `apps/core/models/base.py` | Base model classes and mixins |
| `apps/core/models/fields.py` | Custom model fields |
| `apps/core/admin/__init__.py` | Core admin package |
| `apps/core/admin/base.py` | Base admin classes |
| `apps/core/managers.py` | Custom queryset managers |
| `apps/core/querysets.py` | Custom queryset classes |

## Files to Modify

| File | Changes |
|------|---------|
| `apps/core/apps.py` | Ensure AppConfig is properly set |
| `config/settings/base.py` | Update INSTALLED_APPS ordering |

---

## Implementation Steps

### 1. Create Base Model Module

Create `apps/core/models/__init__.py`:
```python
from .base import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    UUIDMixin,
    BaseManager,
    BaseQuerySet,
)

__all__ = [
    'BaseModel',
    'TimestampMixin',
    'SoftDeleteMixin',
    'UUIDMixin',
    'BaseManager',
    'BaseQuerySet',
]
```

Create `apps/core/models/base.py`:
```python
import uuid
from datetime import datetime
from typing import Optional

from django.db import models
from django.db.models import QuerySet, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class BaseQuerySet(QuerySet):
    """Custom queryset with common filtering methods."""

    def active(self) -> 'BaseQuerySet':
        """Return only active (not soft-deleted) records."""
        return self.filter(is_deleted=False)

    def deleted(self) -> 'BaseQuerySet':
        """Return only soft-deleted records."""
        return self.filter(is_deleted=True)

    def with_deleted(self) -> 'BaseQuerySet':
        """Return all records including soft-deleted."""
        return self

    def created_after(self, date: datetime) -> 'BaseQuerySet':
        """Filter records created after given date."""
        return self.filter(created_at__gt=date)

    def created_before(self, date: datetime) -> 'BaseQuerySet':
        """Filter records created before given date."""
        return self.filter(created_at__lt=date)

    def updated_recently(self, days: int = 7) -> 'BaseQuerySet':
        """Filter records updated within the last N days."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(updated_at__gte=cutoff)


class BaseManager(models.Manager):
    """Custom manager using BaseQuerySet."""

    def get_queryset(self) -> BaseQuerySet:
        return BaseQuerySet(self.model, using=self._db)

    def active(self) -> BaseQuerySet:
        """Return only active records."""
        return self.get_queryset().active()

    def deleted(self) -> BaseQuerySet:
        """Return only deleted records."""
        return self.get_queryset().deleted()

    def with_deleted(self) -> BaseQuerySet:
        """Return all records including deleted."""
        return self.get_queryset().with_deleted()


class TimestampMixin(models.Model):
    """Mixin adding created_at and updated_at timestamps."""

    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        db_index=True,
        help_text=_('Record creation timestamp')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        db_index=True,
        help_text=_('Record last update timestamp')
    )

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Mixin adding soft delete functionality."""

    is_deleted = models.BooleanField(
        _('is deleted'),
        default=False,
        db_index=True,
        help_text=_('Soft delete flag')
    )
    deleted_at = models.DateTimeField(
        _('deleted at'),
        null=True,
        blank=True,
        help_text=_('Soft deletion timestamp')
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, soft=True):
        """
        Override delete to support soft delete.

        Args:
            soft: If True, perform soft delete. If False, hard delete.
        """
        if soft:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            self.save(update_fields=['is_deleted', 'deleted_at'])
        else:
            super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted record."""
        if self.is_deleted:
            self.is_deleted = False
            self.deleted_at = None
            self.save(update_fields=['is_deleted', 'deleted_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the record."""
        super().delete(using=using, keep_parents=keep_parents)


class UUIDMixin(models.Model):
    """Mixin adding UUID primary key."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text=_('Unique identifier')
    )

    class Meta:
        abstract = True


class BaseModel(TimestampMixin, SoftDeleteMixin, models.Model):
    """
    Abstract base model with timestamps and soft delete.

    All domain models should inherit from this class.
    """

    objects = BaseManager()
    objects_with_deleted = BaseManager()  # Alias for clarity

    class Meta:
        abstract = True
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_deleted', 'created_at']),
            models.Index(fields=['is_deleted', 'updated_at']),
        ]

    def __str__(self) -> str:
        """Default string representation."""
        if hasattr(self, 'name'):
            return str(self.name)
        if hasattr(self, 'title'):
            return str(self.title)
        return f'{self.__class__.__name__}({self.pk})'

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f'<{self.__class__.__name__}: {self.pk}>'


class BaseUUIDModel(UUIDMixin, BaseModel):
    """
    Abstract base model with UUID primary key, timestamps, and soft delete.

    Use this for models that need UUID as primary key.
    """

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self) -> str:
        """Default string representation with truncated UUID."""
        if hasattr(self, 'name'):
            return str(self.name)
        if hasattr(self, 'title'):
            return str(self.title)
        return f'{self.__class__.__name__}({str(self.pk)[:8]})'
```

### 2. Create Custom Fields Module

Create `apps/core/models/fields.py`:
```python
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _


class PhoneNumberField(models.CharField):
    """Custom field for phone numbers with validation."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 20)
        kwargs.setdefault('validators', [RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message=_('Phone number must be in format: +999999999 or 999999999')
        )])
        super().__init__(*args, **kwargs)


class ColorField(models.CharField):
    """Custom field for hex color codes."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('max_length', 7)
        kwargs.setdefault('validators', [RegexValidator(
            regex=r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$',
            message=_('Enter a valid hex color code (e.g., #FF5733)')
        )])
        super().__init__(*args, **kwargs)


class JSONFieldWrapper(models.JSONField):
    """Wrapper around JSONField with default empty dict."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', dict)
        kwargs.setdefault('blank', True)
        super().__init__(*args, **kwargs)
```

### 3. Create Admin Base Classes

Create `apps/core/admin/__init__.py`:
```python
from .base import BaseAdmin, BaseModelAdmin, SoftDeleteAdminMixin

__all__ = ['BaseAdmin', 'BaseModelAdmin', 'SoftDeleteAdminMixin']
```

Create `apps/core/admin/base.py`:
```python
from typing import Any, Optional

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html


class SoftDeleteAdminMixin:
    """Mixin adding soft delete support to admin."""

    def get_queryset(self, request):
        """Include soft-deleted records if explicitly requested."""
        qs = self.model.objects_with_deleted.get_queryset()
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs

    def delete_model(self, request, obj):
        """Perform soft delete by default."""
        obj.delete(soft=True)

    def delete_queryset(self, request, queryset):
        """Perform soft delete on queryset."""
        for obj in queryset:
            obj.delete(soft=True)

    actions = ['restore_selected', 'hard_delete_selected']

    @admin.action(description=_('Restore selected records'))
    def restore_selected(self, request, queryset):
        """Admin action to restore soft-deleted records."""
        count = 0
        for obj in queryset:
            if obj.is_deleted:
                obj.restore()
                count += 1
        self.message_user(request, f'{count} records restored.')

    @admin.action(description=_('Permanently delete selected records'))
    def hard_delete_selected(self, request, queryset):
        """Admin action to permanently delete records."""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} records permanently deleted.')


class BaseModelAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    """
    Base admin class with common configurations.

    Includes soft delete support and timestamp display.
    """

    list_display = ['__str__', 'created_at', 'updated_at', 'is_deleted']
    list_filter = ['is_deleted', 'created_at', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at', 'deleted_at']
    date_hierarchy = 'created_at'
    save_on_top = True

    def get_list_display(self, request):
        """Customize list display based on permissions."""
        display = list(super().get_list_display(request))
        if 'is_deleted' not in display:
            display.append('is_deleted')
        return display

    def is_deleted_display(self, obj):
        """Display soft delete status with color."""
        if obj.is_deleted:
            return format_html(
                '<span style="color: red;">{}</span>',
                _('Deleted')
            )
        return format_html(
            '<span style="color: green;">{}</span>',
            _('Active')
        )
    is_deleted_display.short_description = _('Status')  # type: ignore


class BaseAdmin(BaseModelAdmin):
    """
    Simplified base admin for simple models.

    Extends BaseModelAdmin with search and ordering defaults.
    """

    search_fields = ['name', 'title', 'description']
    ordering = ['-created_at']
```

### 4. Update App Configuration

Update `apps/core/apps.py`:
```python
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = _('Core')
    verbose_name_plural = _('Core')

    def ready(self):
        """Import signals when app is ready."""
        import apps.core.signals  # noqa
```

### 5. Create Signals Module

Create `apps/core/signals.py`:
```python
"""
Django model signals for core functionality.
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import BaseModel


@receiver(pre_save)
def update_timestamps(sender, instance, **kwargs):
    """
    Ensure updated_at is set before save.
    This is a fallback in case auto_now doesn't work.
    """
    if isinstance(instance, BaseModel) and not kwargs.get('raw', False):
        if instance.pk:
            instance.updated_at = timezone.now()
```

### 6. Create Initial Migration

```bash
python manage.py makemigrations core
```

---

## Verification Steps

1. **Check model imports:**
   ```bash
   python -c "
   from apps.core.models import BaseModel, TimestampMixin, SoftDeleteMixin
   print('Base model imports: OK')
   "
   ```

2. **Check admin imports:**
   ```bash
   python -c "
   from apps.core.admin import BaseAdmin, BaseModelAdmin
   print('Admin imports: OK')
   "
   ```

3. **Test base model creation:**
   ```bash
   python -c "
   from apps.core.models import BaseModel
   print(f'BaseModel abstract: {BaseModel._meta.abstract}')
   print(f'BaseModel fields: {[f.name for f in BaseModel._meta.fields]}')
   "
   ```

4. **Run migrations:**
   ```bash
   python manage.py makemigrations --check
   python manage.py migrate
   ```

5. **Verify admin site loads:**
   ```bash
   python manage.py check
   ```

---

## Git Commit Message

```
feat: create base model classes and admin configuration

- Add TimestampMixin with created_at and updated_at
- Add SoftDeleteMixin with is_deleted and deleted_at
- Add UUIDMixin for UUID primary keys
- Create BaseQuerySet with common filtering methods
- Create BaseManager with active/deleted queryset methods
- Add BaseModel combining all mixins
- Create BaseModelAdmin with soft delete support
- Add custom fields: PhoneNumberField, ColorField
- Implement admin actions for restore and hard delete
```
