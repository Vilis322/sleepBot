#!/bin/sh
set -e

echo "Waiting for PostgreSQL to be ready..."

# Wait for postgres to be reachable
until pg_isready -h "${DB_HOST:-postgres}" -p "${DB_PORT:-5432}" -U "${DB_USER:-sleepbot_user}" > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is ready!"

# Resolve postgres hostname to IP and use it directly
echo "Resolving postgres IP address..."
POSTGRES_IP=$(getent hosts "${DB_HOST:-postgres}" | awk '{ print $1 }')
if [ -n "$POSTGRES_IP" ]; then
  echo "Resolved ${DB_HOST:-postgres} to $POSTGRES_IP"
  export DB_HOST="$POSTGRES_IP"
  echo "Using DB_HOST=$DB_HOST for connections"
else
  echo "Warning: Could not resolve ${DB_HOST:-postgres}, using hostname"
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting bot..."
exec python main.py
