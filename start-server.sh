#!/usr/bin/env bash
# start-server.sh
echo "Hello from Project PMB"
echo "starting rabbitmq"
rabbitmq-server > rabbit_mq.log 1>&1 &

echo "starting celery server"
celery -A pmb worker --concurrency=4 -l INFO  > celery.log 2>&1 &
celery -A pmb beat -l INFO > beat.log 2>&1  &

python manage.py collectstatic --no-input
gunicorn pmb.wsgi --user www-data --bind 0.0.0.0:8010 --workers 3 --timeout 600 & nginx -g "daemon off;"