echo "Waiting for redis..."
until redis-cli -u "$REDIS_URL" ping | grep -q PONG; do
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