# Task 002: 配置PostgreSQL和Redis

**Task ID:** 002
**Task Name:** 配置PostgreSQL和Redis
**Type:** setup
**Depends-on:** [001]
**Status:** pending

---

## Description

Configure PostgreSQL as the primary database and Redis as the cache layer for the Django project. Set up connection pooling and proper environment-based configuration.

---

## Files to Create

| File | Purpose |
|------|---------|
| `.env.example` | Environment variable template |
| `.env` | Local development environment variables (gitignored) |
| `config/settings/database.py` | Database configuration module |
| `config/settings/cache.py` | Cache configuration module |
| `requirements/db.txt` | Database-related dependencies |

## Files to Modify

| File | Changes |
|------|---------|
| `config/settings/base.py` | Import database and cache settings |
| `.gitignore` | Add `.env` to ignore list |
| `requirements/base.txt` | Add psycopg2-binary and redis |

---

## Implementation Steps

### 1. Environment Configuration

Create `.env.example`:
```bash
# Database
POSTGRES_DB=bidding_system
POSTGRES_USER=bidding_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_POOL_SIZE=10
POSTGRES_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=50

# Environment
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 2. Database Configuration Module

Create `config/settings/database.py`:
```python
import os
from pathlib import Path

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent.parent

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'bidding_system'),
        'USER': os.getenv('POSTGRES_USER', 'bidding_user'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', ''),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',
        },
        'CONN_MAX_AGE': 600,  # Connection persistence (10 minutes)
        'CONN_HEALTH_CHECKS': True,
    }
}

# Connection pool settings
DATABASE_POOL_SIZE = int(os.getenv('POSTGRES_POOL_SIZE', '10'))
DATABASE_MAX_OVERFLOW = int(os.getenv('POSTGRES_MAX_OVERFLOW', '20'))

# Test database configuration
if 'test' in os.sys.argv:
    DATABASES['default']['NAME'] = f"test_{DATABASES['default']['NAME']}"
    DATABASES['default']['CONN_MAX_AGE'] = 0
```

### 3. Cache Configuration Module

Create `config/settings/cache.py`:
```python
import os

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_CLASS': 'redis.connection.ConnectionPool',
            'CONNECTION_POOL_CLASS_KWARGS': {
                'max_connections': int(os.getenv('REDIS_POOL_SIZE', '50')),
                'retry_on_timeout': True,
            },
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        },
        'KEY_PREFIX': 'bidding',
        'TIMEOUT': 300,  # 5 minutes default
    },
    'session': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'session',
        'TIMEOUT': 3600,  # 1 hour
    }
}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'session'

# Cache time-to-live settings
CACHE_TTL = {
    'TENDER_LIST': 300,      # 5 minutes
    'TENDER_DETAIL': 600,    # 10 minutes
    'USER_PROFILE': 1800,    # 30 minutes
    'SEARCH_RESULTS': 60,    # 1 minute
}
```

### 4. Update Base Settings

Modify `config/settings/base.py` to import database and cache settings:
```python
from .database import *  # noqa
from .cache import *  # noqa
```

### 5. Update Dependencies

Add to `requirements/base.txt`:
```
psycopg2-binary>=2.9.9
redis>=5.0.0
django-redis>=5.4.0
python-dotenv>=1.0.0
```

### 6. Update .gitignore

Add to `.gitignore`:
```
.env
*.dump
postgres_data/
redis_data/
```

### 7. Create Local Environment File

Copy `.env.example` to `.env` and configure for local development.

---

## Verification Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements/base.txt
   ```

2. **Test database connection:**
   ```bash
   python manage.py check --database default
   ```

3. **Test cache connection:**
   ```bash
   python -c "
   from django.core.cache import cache
   cache.set('test_key', 'test_value', 30)
   value = cache.get('test_key')
   assert value == 'test_value', 'Cache test failed'
   print('Cache connection: OK')
   "
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Verify connection pooling:**
   ```bash
   python -c "
   from django.db import connection
   print(f'Database: {connection.vendor}')
   print(f'Settings: {connection.settings_dict[\"NAME\"]}')
   "
   ```

---

## Git Commit Message

```
chore: configure PostgreSQL and Redis

- Add PostgreSQL database configuration with connection pooling
- Add Redis cache configuration with django-redis
- Set up environment-based configuration with python-dotenv
- Configure session storage in Redis
- Add connection health checks and timeouts
```
