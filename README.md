[![flake8 Lint](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/lint.yml/badge.svg)](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/lint.yml)
[![Test](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/test.yml/badge.svg)](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/arthur-schnitzler/pmb-service/graph/badge.svg?token=P98WIT0K84)](https://codecov.io/gh/arthur-schnitzler/pmb-service)

# PMB-SERVICE

lightweight APIS-PMB instance to generate TEI/XML dumps

maybe in future also with PMB CRUD included


## cheat-sheet

### process gnd-beacon

`python manage.py process_beacon --beacon=https://thun-korrespondenz.acdh.oeaw.ac.at/beacon.txt --domain=thun-korrespondenz`

`python manage.py process_beacon --beacon=https://raw.githubusercontent.com/Auden-Musulin-Papers/amp-entities/main/out/beacon.txt --domain=Auden-Musulin-Papers`

`python manage.py process_beacon --beacon=https://raw.githubusercontent.com/Hanslick-Online/hsl-entities/main/out/beacon.txt --domain=Hanslick`


## set up new instance

in order to avoid errors on a new instance you'll need to set an environment variable `PMB_NEW=whatever`. After you run the inital `python manage.py migrate` you should `unset PMB_NEW`


## vite

* bundling js-code (used for network-vis) is not part of the docker-setup
* for development make sure the vite-dev-server is running `pnpm run vite`
* for building new bundle, run `pn run build`


## reset sequence 
```SQL
BEGIN; 
SELECT setval(pg_get_serial_sequence('"django_migrations"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "django_migrations";
COMMIT;
```