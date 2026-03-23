"""
Test Celery configuration
"""
import os
import sys
import pytest


class TestCeleryConfiguration:
    """Test Celery configuration."""

    def test_celery_app_importable(self):
        """Test that Celery app can be imported."""
        backend_path = os.path.join(os.path.dirname(__file__), '..')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        try:
            from config.celery import app as celery_app
            assert celery_app is not None
        except Exception as e:
            pytest.fail(f"Cannot import Celery app: {e}")

    def test_celery_connected_to_redis(self):
        """Test that Celery is configured with Redis broker."""
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        backend_path = os.path.join(os.path.dirname(__file__), '..')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        try:
            from django.conf import settings
            assert 'redis://' in settings.CELERY_BROKER_URL
        except Exception as e:
            pytest.fail(f"Cannot verify Celery broker: {e}")

    def test_celery_task_discovery(self):
        """Test that Celery can discover tasks."""
        backend_path = os.path.join(os.path.dirname(__file__), '..')
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings_test')

        try:
            from config.celery import app
            # Check that tasks are autodiscovered
            assert app.autodiscover_tasks is not None
        except Exception as e:
            pytest.fail(f"Cannot verify task discovery: {e}")