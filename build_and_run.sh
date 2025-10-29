#/bin/bash

docker build -t pmb:latest .
docker run -it --network="host" --rm --env-file .env pmb:latest