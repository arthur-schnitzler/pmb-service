[![flake8 Lint](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/lint.yml/badge.svg)](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/lint.yml)
<!-- [![Build and publish Docker image](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/build-deploy.yml/badge.svg)](https://github.com/arthur-schnitzler/pmb-service/actions/workflows/build-deploy.yml) -->

# PMB-SERVICE

lightweight APIS-PMB instance to generate TEI/XML dumps

maybe in future also with PMB CRUD included


## cheat-sheet

### process gnd-beacon

`python manage.py process_beacon --beacon=https://thun-korrespondenz.acdh.oeaw.ac.at/beacon.txt --domain=thun-korrespondenz`


## set up new instance

in order to avoid errors on a new instance you'll need to set an environment variable `PMB_NEW=whatever`. After you run the inital `python manage.py migrate` you should `unset PMB_NEW`