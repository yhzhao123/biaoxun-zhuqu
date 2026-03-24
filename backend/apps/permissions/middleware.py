"""
Permission Middleware - Phase 9 Tasks 048-049
Middleware for permission checking
"""

from typing import Optional
from django.http import HttpResponseForbidden, JsonResponse
from django.core.exceptions import PermissionDenied

from .rbac import RBACService


class PermissionMiddleware:
    """
    Middleware to add permission checking to requests.

    Adds a permission_checker attribute to the request object.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.rbac = RBACService()

    def __call__(self, request):
        # Add permission checker to request
        request.permission_checker = self.rbac

        response = self.get_response(request)
        return response


class PermissionRequiredMiddleware:
    """
    Middleware to enforce permissions on specific paths.

    Configuration in settings:
        PERMISSION_REQUIRED_PATHS = {
            '/api/admin/': 'users.manage',
            '/api/reports/': 'reports.view',
        }
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.rbac = RBACService()

    def __call__(self, request):
        from django.conf import settings

        path_permissions = getattr(settings, 'PERMISSION_REQUIRED_PATHS', {})
        path = request.path

        for prefix, permission in path_permissions.items():
            if path.startswith(prefix):
                if not self.rbac.has_permission(request.user, permission):
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse(
                            {'error': 'Permission denied', 'permission': permission},
                            status=403
                        )
                    return HttpResponseForbidden('Permission denied')

        response = self.get_response(request)
        return response


class RoleRequiredMiddleware:
    """
    Middleware to enforce roles on specific paths.

    Configuration in settings:
        ROLE_REQUIRED_PATHS = {
            '/api/admin/': ['admin', 'manager'],
        }
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.rbac = RBACService()

    def __call__(self, request):
        from django.conf import settings

        path_roles = getattr(settings, 'ROLE_REQUIRED_PATHS', {})
        path = request.path

        for prefix, roles in path_roles.items():
            if path.startswith(prefix):
                user_role = getattr(request.user, 'role', None)
                if user_role not in roles:
                    if request.headers.get('Accept') == 'application/json':
                        return JsonResponse(
                            {'error': 'Role required', 'required_roles': roles},
                            status=403
                        )
                    return HttpResponseForbidden('Role required')

        response = self.get_response(request)
        return response


class PermissionExceptionMiddleware:
    """
    Middleware to handle PermissionDenied exceptions.

    Returns JSON response for API requests, HTML for others.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, PermissionDenied):
            message = str(exception) or 'Permission denied'

            if request.headers.get('Accept') == 'application/json':
                return JsonResponse(
                    {'error': message},
                    status=403
                )
            return HttpResponseForbidden(message)
        return None
