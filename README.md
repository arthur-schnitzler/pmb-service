[![flake8 Lint](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/lint.yml/badge.svg)](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/lint.yml)
[![Test](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/test.yml/badge.svg)](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/arthur-schnitzler/pmb-service/graph/badge.svg?token=P98WIT0K84)](https://codecov.io/gh/arthur-schnitzler/pmb-service)

# PMB-SERVICE

lightweight APIS-PMB instance to generate TEI/XML dumps

maybe in future also with PMB CRUD included


## cheat-sheet

### process gnd-beacon

`python manage.py process_beacon --beacon=https://thun-korrespondenz.acdh.oeaw.ac.at/beacon.txt --domain=thun-korrespondenz`


## set up new instance

in order to avoid errors on a new instance you'll need to set an environment variable `PMB_NEW=whatever`. After you run the inital `python manage.py migrate` you should `unset PMB_NEW`