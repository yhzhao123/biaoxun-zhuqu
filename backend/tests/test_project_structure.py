"""
Test Django project structure and configuration.
"""
import os
import sys
import pytest


class TestDjangoProjectStructure:
    """Test that Django project structure is properly initialized."""

    def test_config_module_exists(self):
        """Test that config module can be imported."""
        # Add backend to path
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        # Try to import config
        try:
            import config
        except ImportError as e:
            pytest.fail(f"Cannot import config module: {e}")

    def test_django_settings_module(self):
        """Test that Django settings can be configured."""
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        try:
            import django
            django.setup()
            from django.conf import settings
            assert settings is not None
        except Exception as e:
            pytest.fail(f"Cannot configure Django settings: {e}")

    def test_project_apps_exist(self):
        """Test that core apps are defined."""
        backend_path = os.path.join(os.path.dirname(__file__), 'backend')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

        try:
            import django
            django.setup()
            from django.conf import settings
            # Check that INSTALLED_APPS contains our apps
            installed_apps = settings.INSTALLED_APPS
            assert 'apps.users' in installed_apps or 'users' in installed_apps
        except Exception as e:
            pytest.fail(f"Cannot verify apps configuration: {e}")


class TestDjangoDependencies:
    """Test that required Django packages are available."""

    def test_django_installed(self):
        """Test Django is installed."""
        import django
        assert django.get_version().startswith('4.2')

    def test_drf_installed(self):
        """Test Django REST Framework is installed."""
        import rest_framework
        assert rest_framework is not None

    def test_psycopg2_installed(self):
        """Test psycopg2 is installed."""
        import psycopg2
        assert psycopg2 is not None

    def test_redis_installed(self):
        """Test redis client is installed."""
        import redis
        assert redis is not None

    def test_celery_installed(self):
        """Test Celery is installed."""
        import celery
        assert celery is not None

    def test_pytest_django_installed(self):
        """Test pytest-django is installed."""
        import pytest_django
        assert pytest_django is not None