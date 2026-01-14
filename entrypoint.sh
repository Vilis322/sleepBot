#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."

# Wait for postgres to be reachable
until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-sleepbot_user}" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is ready!"

# Additional DNS resolution check
echo "Checking DNS resolution..."
getent hosts "${DB_HOST:-postgres}" || echo "Warning: DNS resolution issues"

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting bot..."
exec python main.py
