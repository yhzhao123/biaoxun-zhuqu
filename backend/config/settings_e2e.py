"""
Django settings for E2E testing
Uses SQLite for simplified testing
"""
import os

# Set required env vars before importing base settings
os.environ.setdefault('SECRET_KEY', 'django-insecure-e2e-test-key-not-for-production')
os.environ.setdefault('POSTGRES_PASSWORD', 'testpassword')

from .settings import *

# Database - Use SQLite for E2E tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.e2e.sqlite3',
    }
}

# Security settings for E2E
SECRET_KEY = 'django-insecure-e2e-test-key-not-for-production'
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3004',
    'http://localhost:5173',
    'http://localhost:5174',
    'http://localhost:5175',
]
CORS_ALLOW_ALL_ORIGINS = True

# Disable some middleware for testing
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
