#!/bin/bash

pg_dump -d pmb -h localhost -p 5433 -U  pmb -c -f pmb_dump.sql
psql -U postgres -d pmb < pmb_dump.sql
