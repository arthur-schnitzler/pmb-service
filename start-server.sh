#!/usr/bin/env bash
# start-server.sh
echo "Hello from Project PMB"
printenv >> /etc/environment
touch /var/log/cron.log
cron &&\
uv run manage.py migrate
uv run manage.py collectstatic --no-input
./download_files.sh
uv run manage.py find_duplicated_persons
uv run manage.py find_duplicated_places
uv run gunicorn pmb.wsgi --user www-data --bind 0.0.0.0:8010 --workers 12 --timeout 30 & nginx -g "daemon off;"