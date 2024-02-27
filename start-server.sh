#!/usr/bin/env bash
# start-server.sh
echo "Hello from Project PMB"
printenv >> /etc/environment
touch /var/log/cron.log
cron &&\
python manage.py migrate
python manage.py collectstatic --no-input
./download_files.sh
python manage.py find_duplicated_persons
python manage.py find_duplicated_places
gunicorn pmb.wsgi --user www-data --bind 0.0.0.0:8010 --workers 3 --timeout 600 & nginx -g "daemon off;"