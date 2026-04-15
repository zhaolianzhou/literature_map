#!/bin/sh
set -e

echo "=== DATABASE_URL check ==="
if [ -z "$DATABASE_URL" ]; then
  echo "ERROR: DATABASE_URL is not set. Aborting."
  exit 1
fi
echo "DATABASE_URL is set (host: $(echo $DATABASE_URL | sed 's|.*@||' | cut -d/ -f1))"

echo "=== Running Alembic migrations ==="
alembic -c /app/alembic.ini upgrade head

echo "=== Running seed script ==="
python /app/seed.py

echo "=== Starting uvicorn ==="
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
