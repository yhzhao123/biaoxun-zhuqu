"""
Test models
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model


@pytest.mark.django_db
class TestUserModel(TestCase):
    """Test User model."""

    def test_create_user(self):
        """Test creating a regular user."""
        User = get_user_model()
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        assert user.username == 'testuser'
        assert user.email == 'test@example.com'
        assert not user.is_superuser
        assert user.is_active

    def test_create_superuser(self):
        """Test creating a superuser."""
        User = get_user_model()
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        assert user.is_superuser
        assert user.is_staff

    def test_user_str(self):
        """Test user string representation."""
        User = get_user_model()
        user = User(username='testuser', email='test@example.com')
        assert str(user) == 'testuser'

    def test_soft_delete(self):
        """Test soft delete functionality."""
        from apps.users.mixins import SoftDeleteMixin

        # Test that SoftDeleteMixin has delete method
        assert hasattr(SoftDeleteMixin, 'delete')
        assert hasattr(SoftDeleteMixin, 'hard_delete')
        assert hasattr(SoftDeleteMixin, 'restore')

    def test_timestamp_mixin(self):
        """Test timestamp mixin fields."""
        from apps.users.mixins import TimestampMixin

        # Test that TimestampMixin has required fields
        assert hasattr(TimestampMixin, 'created_at')
        assert hasattr(TimestampMixin, 'updated_at')