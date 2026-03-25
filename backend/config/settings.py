"""
Django settings for config project.
"""
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY and os.environ.get('DJANGO_SETTINGS_MODULE') != 'config.settings_dev':
    raise ValueError('SECRET_KEY environment variable is required')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # For PostgreSQL-specific features
    # Third party
    'rest_framework',
    'corsheaders',
    # Local apps
    'apps.users',
    'apps.tenders',
    'apps.crawler',
    'apps.analysis',
    'apps.subscriptions',
    'apps.permissions',
    'apps.monitoring',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.permissions.middleware.PermissionMiddleware',
    'apps.permissions.middleware.PermissionExceptionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('POSTGRES_DB', 'bidding_db'),
        'USER': os.environ.get('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD'),
        'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
        'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        # Connection pool settings for high-concurrency bidding scenarios
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '600')),  # 10 minutes
        'CONN_HEALTH_CHECKS': True,
        'OPTIONS': {
            # Connection timeout settings
            'connect_timeout': int(os.environ.get('DB_CONNECT_TIMEOUT', '30')),
            # Additional connection options for performance
            'options': '-c statement_timeout=60000 -c idle_in_transaction_session_timeout=300000',
        },
    }
}

# Database connection pool settings (for production)
DB_POOL_SETTINGS = {
    'min_connections': int(os.environ.get('DB_POOL_MIN', '10')),
    'max_connections': int(os.environ.get('DB_POOL_MAX', '50')),
    'max_overflow': int(os.environ.get('DB_POOL_OVERFLOW', '10')),
    'pool_timeout': int(os.environ.get('DB_POOL_TIMEOUT', '30')),
    'pool_recycle': int(os.environ.get('DB_POOL_RECYCLE', '3600')),
}

# Query timeout settings
DB_QUERY_TIMEOUT = {
    'default': int(os.environ.get('DB_QUERY_TIMEOUT', '30000')),  # 30 seconds
    'slow': int(os.environ.get('DB_SLOW_QUERY_TIMEOUT', '60000')),  # 60 seconds
}

# Validate database password (skip for dev settings)
if os.environ.get('DJANGO_SETTINGS_MODULE') != 'config.settings_dev':
    if not DATABASES['default']['PASSWORD']:
        raise ValueError('POSTGRES_PASSWORD environment variable is required')


# Cache
# https://docs.djangoproject.com/en/4.2/topics/cache/

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Django REST Framework
# https://www.django-rest-framework.org/

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# CORS
# https://github.com/adamchainz/django-cors-headers/

CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://localhost:3000'
).split(',')

CORS_ALLOW_CREDENTIALS = True


# Celery Configuration
# https://docs.celeryq.dev/

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Shanghai'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60