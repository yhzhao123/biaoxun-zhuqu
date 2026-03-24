"""
RBAC Service - Phase 9 Tasks 048-049
Role-Based Access Control implementation
"""

from typing import List, Optional, Set, Any
from django.core.cache import cache


class Role:
    """Role constants."""
    ADMIN = 'admin'
    MANAGER = 'manager'
    USER = 'user'
    VIEWER = 'viewer'

    @classmethod
    def get_all_roles(cls) -> List[str]:
        """Get all available roles."""
        return [cls.ADMIN, cls.MANAGER, cls.USER, cls.VIEWER]


class RBACService:
    """
    Role-Based Access Control Service.

    Provides role and permission management functionality.
    """

    # Define permissions for each role
    ROLE_PERMISSIONS = {
        Role.ADMIN: [
            'tenders.view_all',
            'tenders.create',
            'tenders.update',
            'tenders.delete',
            'subscriptions.manage_all',
            'users.manage',
            'settings.manage',
            'reports.view_all',
            'analytics.view_all',
        ],
        Role.MANAGER: [
            'tenders.view_all',
            'tenders.create',
            'tenders.update',
            'subscriptions.manage_all',
            'reports.view_all',
            'analytics.view_all',
        ],
        Role.USER: [
            'tenders.view_own',
            'tenders.create',
            'tenders.update_own',
            'subscriptions.manage_own',
            'reports.view_own',
        ],
        Role.VIEWER: [
            'tenders.view_public',
            'reports.view_public',
        ],
    }

    def __init__(self):
        self._permission_cache = {}

    def get_role_permissions(self, role: str) -> List[str]:
        """
        Get all permissions for a role.

        Args:
            role: Role name

        Returns:
            List of permission strings
        """
        if role not in self.ROLE_PERMISSIONS:
            return []

        permissions = set(self.ROLE_PERMISSIONS[role])

        # Inheritance: MANAGER inherits from USER
        if role == Role.MANAGER:
            permissions.update(self.ROLE_PERMISSIONS.get(Role.USER, []))

        return list(permissions)

    def has_permission(self, user: Optional[Any], permission: str) -> bool:
        """
        Check if user has a specific permission.

        Args:
            user: User instance
            permission: Permission string

        Returns:
            True if user has permission
        """
        if not user:
            return False

        if not permission:
            return False

        # Superuser bypass
        if user.is_superuser:
            return True

        # Check cache
        cache_key = f'user_perms_{user.id}'
        cached_perms = cache.get(cache_key)

        if cached_perms is None:
            cached_perms = self.get_user_permissions(user)
            cache.set(cache_key, cached_perms, 300)  # 5 minutes

        return permission in cached_perms

    def has_role(self, user: Optional[Any], role: str) -> bool:
        """
        Check if user has a specific role.

        Args:
            user: User instance
            role: Role name

        Returns:
            True if user has role
        """
        if not user:
            return False

        return getattr(user, 'role', None) == role

    def assign_role(self, user: Any, role: str) -> bool:
        """
        Assign role to user.

        Args:
            user: User instance
            role: Role name

        Returns:
            True if successful
        """
        if role not in Role.get_all_roles():
            return False

        user.role = role
        user.save(update_fields=['role'])

        # Invalidate cache
        cache.delete(f'user_perms_{user.id}')
        return True

    def revoke_role(self, user: Any, role: str) -> bool:
        """
        Revoke role from user.

        Args:
            user: User instance
            role: Role name

        Returns:
            True if successful
        """
        if getattr(user, 'role', None) == role:
            user.role = ''
            user.save(update_fields=['role'])

            # Invalidate cache
            cache.delete(f'user_perms_{user.id}')
            return True
        return False

    def assign_permission(self, user: Any, permission: str) -> bool:
        """
        Assign specific permission to user.

        Args:
            user: User instance
            permission: Permission string

        Returns:
            True if successful
        """
        # Store in user's permissions field or separate table
        if not hasattr(user, 'extra_permissions'):
            user.extra_permissions = []

        if permission not in user.extra_permissions:
            user.extra_permissions.append(permission)
            user.save(update_fields=['extra_permissions'])

            # Invalidate cache
            cache.delete(f'user_perms_{user.id}')
        return True

    def get_user_permissions(self, user: Any) -> Set[str]:
        """
        Get all permissions for a user.

        Includes role-based permissions and directly assigned permissions.

        Args:
            user: User instance

        Returns:
            Set of permission strings
        """
        permissions = set()

        # Add role-based permissions
        user_role = getattr(user, 'role', None)
        if user_role:
            permissions.update(self.get_role_permissions(user_role))

        # Add directly assigned permissions
        extra_perms = getattr(user, 'extra_permissions', [])
        if extra_perms:
            permissions.update(extra_perms)

        return permissions

    def check_access(self, user: Any, resource: str, action: str) -> bool:
        """
        Check if user can perform action on resource.

        Args:
            user: User instance
            resource: Resource name (e.g., 'tenders')
            action: Action name (e.g., 'view', 'create')

        Returns:
            True if access is allowed
        """
        permission = f'{resource}.{action}'
        return self.has_permission(user, permission)

    def clear_cache(self, user_id: int):
        """Clear permission cache for user."""
        cache.delete(f'user_perms_{user_id}')
