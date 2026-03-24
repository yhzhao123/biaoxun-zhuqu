"""
Data Isolation Tests - Phase 9 Tasks 050-051
Tests for user data isolation and multi-tenancy
"""

import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.permissions.isolation import DataIsolationService, TenantIsolation
from apps.permissions.querysets import IsolatedQuerySetMixin
from apps.tenders.models import TenderNotice
from apps.subscriptions.models import Subscription


User = get_user_model()


class TestDataIsolationService(TestCase):
    """Test DataIsolationService."""

    def setUp(self):
        self.isolation = DataIsolationService()
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            is_staff=True
        )

    def test_filter_by_owner(self):
        """Should filter queryset by owner."""
        # Create tenders for different users
        tender1 = TenderNotice.objects.create(
            title='User1 Tender',
            notice_id='T001',
            created_by=self.user1
        )
        tender2 = TenderNotice.objects.create(
            title='User2 Tender',
            notice_id='T002',
            created_by=self.user2
        )

        # Filter for user1
        queryset = TenderNotice.objects.all()
        filtered = self.isolation.filter_by_owner(queryset, self.user1)

        assert tender1 in filtered
        assert tender2 not in filtered

    def test_admin_can_view_all(self):
        """Should allow admin to view all data."""
        tender1 = TenderNotice.objects.create(
            title='User1 Tender',
            notice_id='T001',
            created_by=self.user1
        )
        tender2 = TenderNotice.objects.create(
            title='User2 Tender',
            notice_id='T002',
            created_by=self.user2
        )

        queryset = TenderNotice.objects.all()
        filtered = self.isolation.filter_by_owner(queryset, self.admin)

        # Admin should see all
        assert tender1 in filtered
        assert tender2 in filtered

    def test_check_ownership(self):
        """Should check if user owns object."""
        tender = TenderNotice.objects.create(
            title='Test Tender',
            notice_id='T001',
            created_by=self.user1
        )

        assert self.isolation.check_ownership(tender, self.user1) is True
        assert self.isolation.check_ownership(tender, self.user2) is False

    def test_get_user_data_stats(self):
        """Should get data statistics for user."""
        TenderNotice.objects.create(
            title='Tender 1',
            notice_id='T001',
            created_by=self.user1
        )
        TenderNotice.objects.create(
            title='Tender 2',
            notice_id='T002',
            created_by=self.user1
        )
        Subscription.objects.create(
            user=self.user1,
            name='Sub 1',
            frequency=Subscription.FREQUENCY_DAILY
        )

        stats = self.isolation.get_user_data_stats(self.user1)
        assert stats['tenders'] == 2
        assert stats['subscriptions'] == 1

    def test_isolate_subscription_data(self):
        """Should isolate subscription data."""
        sub1 = Subscription.objects.create(
            user=self.user1,
            name='User1 Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )
        sub2 = Subscription.objects.create(
            user=self.user2,
            name='User2 Sub',
            frequency=Subscription.FREQUENCY_DAILY
        )

        queryset = Subscription.objects.all()
        filtered = self.isolation.filter_by_owner(queryset, self.user1)

        assert sub1 in filtered
        assert sub2 not in filtered


class TestTenantIsolation(TestCase):
    """Test TenantIsolation for multi-tenancy."""

    def setUp(self):
        self.tenant1 = User.objects.create_user(
            username='tenant1',
            email='tenant1@example.com',
            password='testpass123'
        )
        self.tenant1.tenant_id = 'tenant_1'
        self.tenant1.save()

        self.tenant2 = User.objects.create_user(
            username='tenant2',
            email='tenant2@example.com',
            password='testpass123'
        )
        self.tenant2.tenant_id = 'tenant_2'
        self.tenant2.save()

    def test_tenant_data_isolation(self):
        """Should isolate data between tenants."""
        isolation = TenantIsolation()

        # Create data for tenant1
        tender1 = TenderNotice.objects.create(
            title='Tenant1 Tender',
            notice_id='T001',
            tenant_id='tenant_1'
        )
        tender2 = TenderNotice.objects.create(
            title='Tenant2 Tender',
            notice_id='T002',
            tenant_id='tenant_2'
        )

        queryset = TenderNotice.objects.all()
        filtered = isolation.filter_by_tenant(queryset, 'tenant_1')

        assert tender1 in filtered
        assert tender2 not in filtered

    def test_cross_tenant_access_denied(self):
        """Should deny cross-tenant access."""
        isolation = TenantIsolation()

        tender = TenderNotice.objects.create(
            title='Tenant1 Tender',
            notice_id='T001',
            tenant_id='tenant_1'
        )

        # Tenant2 trying to access tenant1's data
        assert isolation.can_access(self.tenant2, tender) is False
        assert isolation.can_access(self.tenant1, tender) is True


class TestIsolatedQuerySetMixin(TestCase):
    """Test IsolatedQuerySetMixin."""

    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

    def test_isolated_queryset_filters_by_user(self):
        """Should automatically filter by user."""
        # This tests that the mixin properly isolates data
        tender1 = TenderNotice.objects.create(
            title='User1 Tender',
            notice_id='T001',
            created_by=self.user1
        )
        tender2 = TenderNotice.objects.create(
            title='User2 Tender',
            notice_id='T002',
            created_by=self.user2
        )

        # Simulate isolated queryset using Django Manager pattern
        from django.db import models
        from apps.permissions.querysets import IsolatedQuerySetMixin

        class IsolatedTenderManager(IsolatedQuerySetMixin, models.Manager):
            pass

        # Create manager instance properly
        manager = IsolatedTenderManager()
        manager.model = TenderNotice
        manager._db = 'default'

        user1_tenders = manager.for_user(self.user1)

        assert tender1 in user1_tenders
        assert tender2 not in user1_tenders


class TestDataIsolationEdgeCases(TestCase):
    """Test data isolation edge cases."""

    def setUp(self):
        self.isolation = DataIsolationService()
        self.user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123'
        )

    def test_object_without_owner_field(self):
        """Should handle objects without owner field gracefully."""
        # Create a tender without created_by
        tender = TenderNotice.objects.create(
            title='No Owner Tender',
            notice_id='T001'
        )

        # Should not crash
        result = self.isolation.check_ownership(tender, self.user)
        # If no owner, anyone can access (or based on policy)
        assert result is True  # Public access for unowned data

    def test_none_user_filter(self):
        """Should handle None user in filter."""
        queryset = TenderNotice.objects.all()
        # Should return empty queryset for None user
        filtered = self.isolation.filter_by_owner(queryset, None)
        assert filtered.count() == 0

    def test_superuser_bypass_isolation(self):
        """Should allow superuser to bypass isolation."""
        superuser = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='testpass123'
        )

        tender = TenderNotice.objects.create(
            title='Test Tender',
            notice_id='T001',
            created_by=self.user
        )

        # Superuser should be able to access
        queryset = TenderNotice.objects.all()
        filtered = self.isolation.filter_by_owner(queryset, superuser)
        assert tender in filtered

    def test_shared_data_access(self):
        """Should handle shared/public data."""
        # Create a public/shared tender
        tender = TenderNotice.objects.create(
            title='Public Tender',
            notice_id='T001',
            is_public=True
        )

        # Any user should be able to access public data
        user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='testpass123'
        )

        queryset = TenderNotice.objects.all()
        filtered = self.isolation.filter_by_owner(queryset, user2)

        # Public data should be accessible
        assert tender in filtered
