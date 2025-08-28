#!/bin/bash
set -e

echo "Esperando que la base de datos esté lista..."
while ! python -c "
import psycopg2
try:
    psycopg2.connect(host='db', database='caritas_db', user='caritas_user', password='caritas_password')
except:
    exit(1)
"; do
    sleep 2
done

echo "Ejecutando makemigrations..."
python manage.py makemigrations --noinput

echo "Ejecutando migraciones..."
python manage.py migrate --noinput

exec "$@"