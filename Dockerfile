FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update -y && apt-get upgrade -y && apt-get install postgresql-common libpq-dev nginx g++ gcc vim cron tzdata wget -y
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log
ENV TZ="Europe/Vienna"
COPY nginx.default /etc/nginx/sites-available/default
COPY nginx.conf /etc/nginx/nginx.conf

RUN mkdir -p /opt/app
COPY . /opt/app
WORKDIR /opt/app
RUN uv sync --no-install-project
RUN ./download_files.sh
RUN chown -R www-data:www-data /opt/app && chmod -R 755 /opt/app/media
ADD crontab /etc/cron.d/container_cronjob
RUN chmod 0644 /etc/cron.d/container_cronjob

# start server
EXPOSE 80
STOPSIGNAL SIGTERM
CMD ["/opt/app/start-server.sh"]
