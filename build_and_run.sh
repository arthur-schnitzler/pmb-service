#/bin/bash

docker build -t pmb:latest .
docker run -it -p 8020:8020 --rm --name pmb --env-file .docker pmb