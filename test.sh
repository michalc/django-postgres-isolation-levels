#!/bin/bash -xe

RETRIES=10

until PGPASSWORD=password psql -h localhost -U postgres -d postgres -c "select 1" > /dev/null 2>&1 || [ $RETRIES -eq 0 ]; do
  echo "Waiting for postgres server, $((RETRIES--)) remaining attempts..."
  sleep 1
done

./manage.py migrate
DJANGO_SETTINGS_MODULE=app.settings pytest
