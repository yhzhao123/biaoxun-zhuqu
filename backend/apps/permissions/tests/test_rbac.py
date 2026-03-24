"""
RBAC Tests - Phase 9 Tasks 048-049
Tests for Role-Based Access Control
"""

import pytest
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

from apps.permissions.rbac import RBACService, Role
from apps.permissions.decorators import require_permission, require_role
from apps.permissions.middleware import PermissionMiddleware


User = get_user_model()


class TestRoleDefinitions(TestCase):
    """Test role definitions."""

    def test_role_constants(self):
        """Should have correct role constants."""
        assert Role.ADMIN == 'admin'
        assert Role.MANAGER == 'manager'
        assert Role.USER == 'user'
        assert Role.VIEWER == 'viewer'

    def test_role_permissions_mapping(self):
        """Should have correct permissions for each role."""
        rbac = RBACService()

        # Admin has all permissions
        admin_perms = rbac.get_role_permissions(Role.ADMIN)
        assert 'tenders.view_all' in admin_perms
        assert 'tenders.create' in admin_perms
        assert 'tenders.delete' in admin_perms
        assert 'subscriptions.manage_all' in admin_perms
        assert 'users.manage' in admin_perms

        # Manager has project management permissions
        manager_perms = rbac.get_role_permissions(Role.MANAGER)
        assert 'tenders.view_all' in manager_perms
        assert 'tenders.create' in manager_perms
        assert 'tenders.delete' not in manager_perms

        # User has limited permissions
        user_perms = rbac.get_role_permissions(Role.USER)
        assert 'tenders.view_own' in user_perms
        assert 'subscriptions.manage_own' in user_perms
        assert 'tenders.delete' not in user_perms

        # Viewer has read-only permissions
        viewer_perms = rbac.get_role_permissions(Role.VIEWER)
        assert 'tenders.view_public' in viewer_perms
        assert 'tenders.create' not in viewer_perms


class TestRBACService(TestCase):
    """Test RBACService."""

    def setUp(self):
        self.rbac = RBACService()
        # Clear cache to avoid test isolation issues
        from django.core.cache import cache
        cache.clear()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role=Role.ADMIN
        )
        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            role=Role.USER
        )
        self.viewer = User.objects.create_user(
            username='viewer',
            email='viewer@example.com',
            password='testpass123',
            role=Role.VIEWER
        )

    def test_has_permission_with_role(self):
        """Should check permission based on user role."""
        # Admin should have all permissions
        assert self.rbac.has_permission(self.admin_user, 'tenders.delete') is True
        assert self.rbac.has_permission(self.admin_user, 'users.manage') is True

        # User should have limited permissions
        assert self.rbac.has_permission(self.user, 'tenders.view_own') is True
        assert self.rbac.has_permission(self.user, 'tenders.delete') is False

        # Viewer should only have view permissions
        assert self.rbac.has_permission(self.viewer, 'tenders.view_public') is True
        assert self.rbac.has_permission(self.viewer, 'tenders.create') is False

    def test_has_permission_with_direct_assignment(self):
        """Should check directly assigned permissions."""
        # Assign specific permission to user
        self.rbac.assign_permission(self.user, 'tenders.delete')
        assert self.rbac.has_permission(self.user, 'tenders.delete') is True

    def test_has_role(self):
        """Should check if user has specific role."""
        assert self.rbac.has_role(self.admin_user, Role.ADMIN) is True
        assert self.rbac.has_role(self.admin_user, Role.USER) is False
        assert self.rbac.has_role(self.user, Role.USER) is True

    def test_assign_role(self):
        """Should assign role to user."""
        self.rbac.assign_role(self.viewer, Role.USER)
        assert self.rbac.has_role(self.viewer, Role.USER) is True

    def test_revoke_role(self):
        """Should revoke role from user."""
        self.rbac.revoke_role(self.user, Role.USER)
        assert self.rbac.has_role(self.user, Role.USER) is False

    def test_get_user_permissions(self):
        """Should get all permissions for user."""
        perms = self.rbac.get_user_permissions(self.user)
        assert 'tenders.view_own' in perms
        assert 'subscriptions.manage_own' in perms

    def test_check_access_allowed(self):
        """Should allow access when permission exists."""
        result = self.rbac.check_access(self.user, 'tenders', 'view_own')
        assert result is True

    def test_check_access_denied(self):
        """Should deny access when permission missing."""
        result = self.rbac.check_access(self.user, 'tenders', 'delete')
        assert result is False

    def test_super_admin_bypass(self):
        """Should allow super admin to bypass all checks."""
        self.admin_user.is_superuser = True
        self.admin_user.save()
        assert self.rbac.has_permission(self.admin_user, 'any.permission') is True


class TestPermissionDecorators(TestCase):
    """Test permission decorators."""

    def setUp(self):
        self.factory = RequestFactory()
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role=Role.ADMIN
        )
        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            role=Role.USER
        )

    def test_require_permission_decorator_allowed(self):
        """Should allow access when user has permission."""
        @require_permission('tenders.view_own')
        def view_func(request):
            return HttpResponse('Success')

        request = self.factory.get('/test/')
        request.user = self.user
        response = view_func(request)
        assert response.status_code == 200

    def test_require_permission_decorator_denied(self):
        """Should deny access when user lacks permission."""
        @require_permission('tenders.delete')
        def delete_func(request):
            return HttpResponse('Success')

        request = self.factory.get('/test/')
        request.user = self.user
        with pytest.raises(PermissionDenied):
            delete_func(request)

    def test_require_role_decorator_allowed(self):
        """Should allow access when user has role."""
        @require_role(Role.ADMIN)
        def admin_func(request):
            return HttpResponse('Success')

        request = self.factory.get('/test/')
        request.user = self.admin_user
        response = admin_func(request)
        assert response.status_code == 200

    def test_require_role_decorator_denied(self):
        """Should deny access when user lacks role."""
        @require_role(Role.ADMIN)
        def admin_func(request):
            return HttpResponse('Success')

        request = self.factory.get('/test/')
        request.user = self.user
        with pytest.raises(PermissionDenied):
            admin_func(request)


class TestPermissionMiddleware(TestCase):
    """Test permission middleware."""

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123',
            role=Role.USER
        )

    def test_middleware_adds_permission_checker(self):
        """Should add permission checker to request."""
        def get_response(request):
            return HttpResponse('OK')

        middleware = PermissionMiddleware(get_response)
        request = self.factory.get('/test/')
        request.user = self.user

        response = middleware(request)
        assert hasattr(request, 'permission_checker')
        assert response.status_code == 200


class TestPermissionEdgeCases(TestCase):
    """Test permission edge cases."""

    def setUp(self):
        self.rbac = RBACService()

    def test_invalid_role(self):
        """Should handle invalid role gracefully."""
        user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='testpass123'
        )
        user.role = 'invalid_role'
        user.save()

        # Should return empty permissions for invalid role
        perms = self.rbac.get_role_permissions('invalid_role')
        assert perms == []

    def test_permission_inheritance(self):
        """Should inherit permissions from parent roles."""
        # Manager should inherit user permissions
        manager_perms = self.rbac.get_role_permissions(Role.MANAGER)
        user_perms = self.rbac.get_role_permissions(Role.USER)

        # Manager has all user permissions plus more
        for perm in user_perms:
            assert perm in manager_perms

    def test_empty_permission_check(self):
        """Should deny when checking empty permission."""
        user = User.objects.create_user(
            username='test',
            email='test@example.com',
            password='testpass123',
            role=Role.USER
        )
        assert self.rbac.has_permission(user, '') is False

    def test_none_user(self):
        """Should handle None user gracefully."""
        assert self.rbac.has_permission(None, 'tenders.view') is False
