"""
Isolated QuerySets - Phase 9 Tasks 050-051
QuerySet mixins for data isolation
"""

from typing import Optional, Any
from django.db import models
from django.db.models import QuerySet


class IsolatedQuerySetMixin:
    """
    Mixin to provide isolated querysets based on user.

    Automatically filters queryset to show only data the user can access.
    """

    def get_queryset(self, user: Optional[Any] = None) -> QuerySet:
        """
        Get queryset with isolation applied.

        Args:
            user: User to filter for

        Returns:
            Filtered queryset
        """
        queryset = super().get_queryset()

        if user and not (user.is_superuser or user.is_staff):
            # Apply ownership filter
            if hasattr(self.model, 'created_by'):
                queryset = queryset.filter(created_by=user)
            elif hasattr(self.model, 'user'):
                queryset = queryset.filter(user=user)

            # Include public data
            if hasattr(self.model, 'is_public'):
                queryset = queryset.filter(is_public=True) | queryset.filter(created_by=user)

        return queryset

    def for_user(self, user: Any) -> QuerySet:
        """Get queryset for specific user."""
        return self.get_queryset(user)

    def owned_by(self, user: Any) -> QuerySet:
        """Get objects owned by user."""
        queryset = super().get_queryset()

        if hasattr(self.model, 'created_by'):
            return queryset.filter(created_by=user)
        elif hasattr(self.model, 'user'):
            return queryset.filter(user=user)

        return queryset.none()


class TenantQuerySetMixin:
    """
    Mixin for multi-tenant queryset filtering.
    """

    def get_queryset(self, tenant_id: Optional[str] = None) -> QuerySet:
        """
        Get queryset filtered by tenant.

        Args:
            tenant_id: Tenant ID to filter by

        Returns:
            Filtered queryset
        """
        queryset = super().get_queryset()

        if tenant_id and hasattr(self.model, 'tenant_id'):
            queryset = queryset.filter(tenant_id=tenant_id)

        return queryset

    def for_tenant(self, tenant_id: str) -> QuerySet:
        """Get queryset for specific tenant."""
        return self.get_queryset(tenant_id)


class OwnedModelManager(IsolatedQuerySetMixin, models.Manager):
    """
    Manager for owned models.

    Automatically filters to user's own data.
    """
    pass


class TenantModelManager(TenantQuerySetMixin, models.Manager):
    """
    Manager for tenant models.

    Automatically filters to tenant data.
    """
    pass
