#!/bin/bash
# =============================================================================
# Database Initialization Script
# Runs database setup and seed data
# =============================================================================

set -e

echo "=== Database Initialization ==="

# Wait for database to be ready
echo "Waiting for database connection..."
max_attempts=30
attempt=0

until python manage.py check --database default 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "ERROR: Database connection failed after $max_attempts attempts"
        exit 1
    fi
    echo "Attempt $attempt/$max_attempts - database not ready, sleeping..."
    sleep 2
done

echo "Database connection established!"

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create cache table if using database cache
echo "Setting up cache table..."
python manage.py createcachetable || true

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear 2>/dev/null || true

# Load initial data if available
if [ -f /app/data/seed.json ]; then
    echo "Loading seed data..."
    python manage.py loaddata /app/data/seed.json
fi

echo "=== Database Initialization Complete ==="