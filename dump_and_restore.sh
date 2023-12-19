#!/bin/bash

pg_dump -d pmb -h localhost -p 5432 -U  postgres -c -f pmb_dump.sql
# psql -U postgres --dbname=pmb


# python manage.py migrate --fake apis_entities zero
# python manage.py migrate --fake apis_labels zero
# python manage.py migrate --fake apis_metainfo zero
# python manage.py migrate --fake apis_relations zero
# python manage.py migrate --fake apis_vocabularies zero