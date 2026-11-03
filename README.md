# PMB-SERVICE

[![flake8 Lint](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/lint.yml/badge.svg)](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/lint.yml)
[![Test](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/test.yml/badge.svg)](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/arthur-schnitzler/pmb-service/graph/badge.svg?token=P98WIT0K84)](https://codecov.io/gh/arthur-schnitzler/pmb-service)

lightweight APIS-PMB instance to generate TEI/XML dumps

maybe in future also with PMB CRUD included

## install

* clone the repo
* create a virtual env `python -m venv venv`
* activate it `source venv/bin/activate`
* install packages `pip install -r requirements_dev.txt`
* get a recent db-dump (`./dump_and_restore.sh`) (create a postgres-db `pmb` and run `./dump_and_restore.sh`, make sure you tunneled to production db first)
* set env variables
* run `python manage.py runserver`
* (create a superuser) `python manage.py creatsuperuser`

## jupyter notebook

* `pip install notebook` (1 time)
* set env varibles `./set_env_variables`
* `python manage.py shell_plus --lab`

## cheat-sheet

### process gnd-beacon

`python manage.py process_beacon --beacon=https://thun-korrespondenz.acdh.oeaw.ac.at/beacon.txt --domain=thun-korrespondenz`

`python manage.py process_beacon --beacon=https://raw.githubusercontent.com/Auden-Musulin-Papers/amp-entities/main/out/beacon.txt --domain=Auden-Musulin-Papers`

`python manage.py process_beacon --beacon=https://raw.githubusercontent.com/Hanslick-Online/hsl-entities/main/out/beacon.txt --domain=Hanslick`

### sync project uris

Projects tell the PMB where an entity is used by publishing a `pmb_uris-in-use.csv`:

```csv
pmb_id,entity_type,uri,domain
29819,bibl,https://schnitzler-briefe.acdh.oeaw.ac.at/pmb29819.html,schnitzler-briefe
```

* `entity_type` is one of `person`, `place`, `org`, `bibl`, `event`
* `domain` is constant per project and has to match its key in `PMB_URI_SOURCES` (`pmb/settings.py`)
* at most one row per `(entity_type, pmb_id)`

`sync_uris_in_use` compares each CSV with the PMB's uris **of that domain** and adds, updates or deletes them (uris of other domains are never touched):

```shell
python manage.py sync_uris_in_use --dry-run                           # all projects, writes nothing
python manage.py sync_uris_in_use --domain schnitzler-briefe          # a single project
python manage.py sync_uris_in_use --max-delete-ratio 0.1              # allow deleting up to 10% (default 5%)
```

* a project is skipped (and the command exits with an error) if the CSV can't be loaded or is invalid, or if more than `--max-delete-ratio` of its uris would be deleted
* rows pointing to an entity that doesn't exist (or has another type) are skipped and listed
* entities merged in the PMB already carry the uris of the merged entity, those rows are left as they are

To connect a new project:

1. copy [project_scripts/process_list_xml.py](project_scripts/process_list_xml.py) (python standard library only) and a `pmb-uris.json` based on [project_scripts/pmb-uris.example.json](project_scripts/pmb-uris.example.json) into the project's repo
2. run `python3 process_list_xml.py` after the data was fetched (it writes the CSV from the project's `list*.xml`, the diff is done by the PMB) and commit the CSV
3. add the project to `PMB_URI_SOURCES` and check it with `--dry-run` first

## set up new instance

in order to avoid errors on a new instance you'll need to set an environment variable `PMB_NEW=whatever`. After you run the inital `python manage.py migrate` you should `unset PMB_NEW`

## tests

Run all tests

```bash
uv run manage test -v 2
```

Run a single test

```bash
uv run manage.py test apis_core.apis_entities.tests.EntitiesTestCase.test_009_merge_view -v 2
```

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

## Docker

### building the image

* `docker build -t pmb:latest .`
* `docker build -t pmb:latest --no-cache .`

### running the image

To run the image you should provide an `.env` file to pass in needed environment variables; see `pmb/settings.py` for possible varibles:

```bash
docker run -it --network="host" --rm --env-file .env pmb:latest
```

## Refresh Collation

```shell
psql -U postgres -d pmb
REINDEX DATABASE pmb;
ALTER DATABASE pmb REFRESH COLLATION VERSION;
```
