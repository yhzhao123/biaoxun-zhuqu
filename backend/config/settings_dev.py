"""
Development settings with SQLite
"""
from .settings import *

# Use SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Disable Redis cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# Celery in eager mode
CELERY_TASK_ALWAYS_EAGER = True

# Allow all hosts
ALLOWED_HOSTS = ['*']

# Debug mode
DEBUG = True

# Test secret key
SECRET_KEY = 'dev-secret-key-not-for-production'

# REST Framework - allow any for dev
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
