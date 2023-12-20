#!/bin/bash

pg_dump -d pmb -h localhost -p 5432 -U  postgres -c -f pmb_dump.sql
pg_dump -d pmb_play -h localhost -p 5432 -U  postgres -c -f pmb_play_dump.sql

