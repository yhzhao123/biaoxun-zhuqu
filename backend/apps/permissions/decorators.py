"""
Permission Decorators - Phase 9 Tasks 048-049
Decorators for permission checking
"""

from functools import wraps
from typing import Optional, List
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from .rbac import RBACService, Role


def require_permission(permission: str):
    """
    Decorator to require specific permission.

    Args:
        permission: Required permission string

    Usage:
        @require_permission('tenders.create')
        def create_tender(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            rbac = RBACService()
            if not rbac.has_permission(request.user, permission):
                raise PermissionDenied(f'Requires permission: {permission}')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(*permissions: str):
    """
    Decorator to require any of the specified permissions.

    Args:
        *permissions: Permission strings (at least one required)

    Usage:
        @require_any_permission('tenders.view_all', 'tenders.view_own')
        def view_tenders(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            rbac = RBACService()
            for permission in permissions:
                if rbac.has_permission(request.user, permission):
                    return view_func(request, *args, **kwargs)
            raise PermissionDenied(f'Requires one of permissions: {permissions}')
        return wrapper
    return decorator


def require_all_permissions(*permissions: str):
    """
    Decorator to require all specified permissions.

    Args:
        *permissions: Permission strings (all required)

    Usage:
        @require_all_permissions('tenders.view', 'tenders.create')
        def create_and_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            rbac = RBACService()
            for permission in permissions:
                if not rbac.has_permission(request.user, permission):
                    raise PermissionDenied(f'Requires permission: {permission}')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_role(role: str):
    """
    Decorator to require specific role.

    Args:
        role: Required role name

    Usage:
        @require_role(Role.ADMIN)
        def admin_panel(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            rbac = RBACService()
            if not rbac.has_role(request.user, role):
                raise PermissionDenied(f'Requires role: {role}')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_any_role(*roles: str):
    """
    Decorator to require any of the specified roles.

    Args:
        *roles: Role names (at least one required)

    Usage:
        @require_any_role(Role.ADMIN, Role.MANAGER)
        def management_panel(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            rbac = RBACService()
            for role in roles:
                if rbac.has_role(request.user, role):
                    return view_func(request, *args, **kwargs)
            raise PermissionDenied(f'Requires one of roles: {roles}')
        return wrapper
    return decorator


def object_permission_required(
    model,
    permission: str,
    lookup_field: str = 'pk',
    owner_field: str = 'created_by'
):
    """
    Decorator to check object-level permissions.

    Args:
        model: Django model class
        permission: Base permission string
        lookup_field: Field to lookup object (default: 'pk')
        owner_field: Field for ownership check (default: 'created_by')

    Usage:
        @object_permission_required(TenderNotice, 'tenders.update')
        def update_tender(request, pk):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            rbac = RBACService()
            obj_id = kwargs.get(lookup_field)

            if not obj_id:
                raise PermissionDenied('Object ID required')

            obj = get_object_or_404(model, pk=obj_id)

            # Check if user has general permission
            if rbac.has_permission(request.user, permission):
                return view_func(request, *args, **kwargs)

            # Check ownership permission
            own_perm = f'{permission}_own'
            if rbac.has_permission(request.user, own_perm):
                owner = getattr(obj, owner_field, None)
                if owner == request.user:
                    return view_func(request, *args, **kwargs)

            raise PermissionDenied(f'Cannot {permission} this object')
        return wrapper
    return decorator


class PermissionChecker:
    """
    Class-based permission checker for views.

    Usage in CBV:
        class MyView(PermissionChecker, View):
            required_permission = 'tenders.view'
    """
    required_permission: Optional[str] = None
    required_role: Optional[str] = None

    def dispatch(self, request, *args, **kwargs):
        rbac = RBACService()

        if self.required_permission:
            if not rbac.has_permission(request.user, self.required_permission):
                raise PermissionDenied(f'Requires permission: {self.required_permission}')

        if self.required_role:
            if not rbac.has_role(request.user, self.required_role):
                raise PermissionDenied(f'Requires role: {self.required_role}')

        return super().dispatch(request, *args, **kwargs)
