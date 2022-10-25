#/bin/bash

docker build --no-cache -t pmb:latest .
docker run -it -p 8020:8020 --rm --name pmb --env-file .secret pmb