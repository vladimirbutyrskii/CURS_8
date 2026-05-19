# docker/entrypoint.sh
set -e

# Ждем готовности PostgreSQL
echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.5
done
echo "PostgreSQL is ready!"

# Ждем готовности Redis
echo "Waiting for Redis..."
while ! nc -z $REDIS_HOST $REDIS_PORT; do
  sleep 0.5
done
echo "Redis is ready!"

# Применяем миграции
echo "Applying migrations..."
python manage.py migrate --noinput

# Собираем статику
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Выполняем переданную команду
exec "$@"

