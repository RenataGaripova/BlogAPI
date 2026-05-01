#!/bin/sh
set -e

echo "Waiting for redis..."
until python -c "import redis; redis.Redis.from_url('$REDIS_URL').ping()" 2>/dev/null; do
  sleep 2
done
echo "Redis is available!"

echo "Run migrations."
python manage.py migrate --no-input

echo "Collect static files."
python manage.py collectstatic --no-input

echo "Compile translation messages."
python manage.py compilemessages

echo "Starting..."
exec "$@"