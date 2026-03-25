#!/bin/bash
# =============================================================================
# Backend Entry Point Script
# Handles database migrations, static file collection, and starts Gunicorn
# =============================================================================

set -e

echo "=== Starting Backend Application ==="

# Wait for database to be ready
echo "Waiting for database..."
until python manage.py check --database default 2>/dev/null; do
    echo "Database is unavailable - sleeping"
    sleep 2
done
echo "Database is ready!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if needed (only in development)
if [ "${DEBUG:-0}" = "1" ]; then
    echo "Creating superuser if needed..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
import os
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    admin_password = os.environ.get('ADMIN_PASSWORD')
    if admin_password:
        User.objects.create_superuser('admin', 'admin@example.com', admin_password)
        print('Superuser created: admin (password from ADMIN_PASSWORD env)')
    else:
        print('Warning: ADMIN_PASSWORD not set, skipping superuser creation')
else:
    print('Superuser already exists')
EOF
fi

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn config.asgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class=uvicorn.workers.UvicornWorker \
    --worker-tmp-dir /dev/shm \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    --timeout 120