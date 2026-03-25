"""
Test settings - use SQLite for testing
"""
import os

# Set environment variables before importing settings
os.environ['SECRET_KEY'] = 'test-secret-key-not-for-production-use-only-in-tests'
os.environ['POSTGRES_PASSWORD'] = 'test-password'

from .settings import *

# Override with test-specific settings
SECRET_KEY = 'test-secret-key-not-for-production-use-only-in-tests'

# Remove PostgreSQL-specific apps
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django.contrib.postgres']

# Ensure monitoring app is in INSTALLED_APPS (avoid duplicates)
if 'apps.monitoring' not in INSTALLED_APPS:
    INSTALLED_APPS = INSTALLED_APPS + ['apps.monitoring']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable caching during tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Use mock for Celery during tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Allow any permissions for API testing
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}