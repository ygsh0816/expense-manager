#!/bin/bash
set -e

# Load .env vars if file exists
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput 

echo "Creating superuser if needed..."
if [ -z "$DJANGO_SUPERUSER_USERNAME" ] || [ -z "$DJANGO_SUPERUSER_EMAIL" ]; then
  echo "Superuser username/email not set, skipping creation."
else
  if python manage.py createsuperuser --username "$DJANGO_SUPERUSER_USERNAME" --email "$DJANGO_SUPERUSER_EMAIL" --noinput 2>&1 | grep -q 'already exists'; then
    echo "Superuser '$DJANGO_SUPERUSER_USERNAME' already exists."
  else
    echo "Superuser '$DJANGO_SUPERUSER_USERNAME' created."
  fi
fi

echo "Starting app: $@"
exec "$@"
