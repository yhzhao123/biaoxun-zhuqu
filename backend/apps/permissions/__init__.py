"""
Permissions app for RBAC and data isolation.
"""

default_app_config = 'apps.permissions.apps.PermissionsConfig'

# Delay imports to avoid AppRegistryNotReady
__all__ = [
    # RBAC
    'RBACService',
    'Role',
    # Decorators
    'require_permission',
    'require_any_permission',
    'require_all_permissions',
    'require_role',
    'require_any_role',
    'object_permission_required',
    'PermissionChecker',
    # Middleware
    'PermissionMiddleware',
    'PermissionRequiredMiddleware',
    'RoleRequiredMiddleware',
    'PermissionExceptionMiddleware',
    # Isolation
    'DataIsolationService',
    'TenantIsolation',
    # QuerySets
    'IsolatedQuerySetMixin',
    'TenantQuerySetMixin',
    'OwnedModelManager',
    'TenantModelManager',
]
