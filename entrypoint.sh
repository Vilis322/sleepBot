#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."

# Wait for postgres to be reachable
until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-sleepbot_user}" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is ready!"

# Additional DNS resolution check and fix for asyncio
echo "Checking DNS resolution..."
POSTGRES_IP=$(getent hosts "${DB_HOST:-postgres}" | awk '{ print $1 }')
if [ -n "$POSTGRES_IP" ]; then
  echo "$POSTGRES_IP ${DB_HOST:-postgres}" >> /etc/hosts
  echo "Added $POSTGRES_IP ${DB_HOST:-postgres} to /etc/hosts"
else
  echo "Warning: Could not resolve ${DB_HOST:-postgres}"
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting bot..."
exec python main.py
