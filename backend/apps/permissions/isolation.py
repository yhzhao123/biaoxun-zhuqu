"""
Data Isolation Service - Phase 9 Tasks 050-051
User data isolation and multi-tenancy implementation
"""

from typing import Optional, Dict, Any, Type
from django.db import models
from django.db.models import Q, QuerySet


class DataIsolationService:
    """
    Service for data isolation between users.

    Ensures users can only access their own data unless they have
    special permissions (admin, superuser).
    """

    def filter_by_owner(
        self,
        queryset: QuerySet,
        user: Optional[Any],
        owner_field: str = 'created_by'
    ) -> QuerySet:
        """
        Filter queryset to only show user's own data.

        Args:
            queryset: Base queryset
            user: User to filter for
            owner_field: Field name for ownership (default: 'created_by')

        Returns:
            Filtered queryset
        """
        if not user:
            return queryset.none()

        # Superusers and staff can see all
        if user.is_superuser or user.is_staff:
            return queryset

        model = queryset.model
        filters = Q()

        # Check if model has owner field - include user's own data
        if hasattr(model, owner_field):
            filters |= Q(**{owner_field: user})

        # Check for user field (e.g., Subscription.user) - include user's own data
        if hasattr(model, 'user'):
            filters |= Q(user=user)

        # Include public data that has no owner (truly public/shared data)
        if hasattr(model, 'is_public'):
            public_filter = Q(is_public=True)
            if hasattr(model, owner_field):
                public_filter &= Q(**{f"{owner_field}__isnull": True})
            filters |= public_filter

        # If no filters applied, return empty (secure by default)
        if not filters:
            return queryset.none()

        return queryset.filter(filters)

    def check_ownership(
        self,
        obj: models.Model,
        user: Any,
        owner_field: str = 'created_by'
    ) -> bool:
        """
        Check if user owns an object.

        Args:
            obj: Object to check
            user: User to check ownership for
            owner_field: Field name for ownership

        Returns:
            True if user owns the object
        """
        if not user:
            return False

        # Superusers own everything
        if user.is_superuser or user.is_staff:
            return True

        # Get owner from object
        owner = getattr(obj, owner_field, None)
        if owner is None:
            # Check for user field
            owner = getattr(obj, 'user', None)

        if owner is None:
            # No owner - consider it public/shared
            return True

        return owner == user

    def get_user_data_stats(self, user: Any) -> Dict[str, int]:
        """
        Get data statistics for a user.

        Args:
            user: User to get stats for

        Returns:
            Dict with counts per model
        """
        from apps.tenders.models import TenderNotice
        from apps.subscriptions.models import Subscription

        stats = {
            'tenders': TenderNotice.objects.filter(created_by=user).count(),
            'subscriptions': Subscription.objects.filter(user=user).count(),
        }

        return stats

    def isolate_queryset(
        self,
        queryset: QuerySet,
        user: Any,
        tenant_field: Optional[str] = None
    ) -> QuerySet:
        """
        Apply full isolation to queryset.

        Args:
            queryset: Base queryset
            user: User to isolate for
            tenant_field: Optional tenant field for multi-tenancy

        Returns:
            Isolated queryset
        """
        if not user:
            return queryset.none()

        # Admin bypass
        if user.is_superuser or user.is_staff:
            return queryset

        filters = Q()

        # Owner filter
        model = queryset.model
        if hasattr(model, 'created_by'):
            filters |= Q(created_by=user)
        if hasattr(model, 'user'):
            filters |= Q(user=user)

        # Tenant filter
        if tenant_field and hasattr(model, tenant_field):
            tenant_id = getattr(user, 'tenant_id', None)
            if tenant_id:
                filters |= Q(**{tenant_field: tenant_id})

        # Public data filter
        if hasattr(model, 'is_public'):
            filters |= Q(is_public=True)

        return queryset.filter(filters)


class TenantIsolation:
    """
    Multi-tenancy isolation service.

    Provides data isolation between tenants in a multi-tenant system.
    """

    def filter_by_tenant(
        self,
        queryset: QuerySet,
        tenant_id: str,
        tenant_field: str = 'tenant_id'
    ) -> QuerySet:
        """
        Filter queryset by tenant.

        Args:
            queryset: Base queryset
            tenant_id: Tenant ID to filter by
            tenant_field: Field name for tenant

        Returns:
            Filtered queryset
        """
        if not tenant_id:
            return queryset.none()

        return queryset.filter(**{tenant_field: tenant_id})

    def can_access(self, user: Any, obj: models.Model, tenant_field: str = 'tenant_id') -> bool:
        """
        Check if user can access object in multi-tenant context.

        Args:
            user: User attempting access
            obj: Object being accessed
            tenant_field: Field name for tenant

        Returns:
            True if access is allowed
        """
        if not user or not obj:
            return False

        # Superusers can access all
        if user.is_superuser:
            return True

        # Check tenant match
        user_tenant = getattr(user, 'tenant_id', None)
        obj_tenant = getattr(obj, tenant_field, None)

        if user_tenant and obj_tenant:
            return user_tenant == obj_tenant

        # No tenant isolation for objects without tenant
        return True

    def get_tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """
        Get statistics for a tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            Dict with tenant statistics
        """
        from apps.tenders.models import TenderNotice
        from apps.subscriptions.models import Subscription

        return {
            'tenant_id': tenant_id,
            'tenders_count': TenderNotice.objects.filter(tenant_id=tenant_id).count(),
            'subscriptions_count': Subscription.objects.filter(tenant_id=tenant_id).count(),
        }


class IsolatedQuerySetMixin:
    """
    Mixin for isolated queryset management.

    Usage:
        class TenderManager(IsolatedQuerySetMixin, models.Manager):
            pass
    """

    def get_queryset(self, user: Optional[Any] = None) -> QuerySet:
        """
        Get queryset with isolation applied.

        Args:
            user: User to isolate for

        Returns:
            Isolated queryset
        """
        queryset = super().get_queryset()

        if user:
            isolation = DataIsolationService()
            return isolation.isolate_queryset(queryset, user)

        return queryset

    def for_user(self, user: Any) -> QuerySet:
        """Get queryset filtered for specific user."""
        return self.get_queryset(user)
