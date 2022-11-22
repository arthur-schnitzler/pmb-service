import os
import owncloud
from django.conf import settings


DOMAIN_MAPPING = [
    ("d-nb.info/gnd", "gnd"),
    ("geonames", "geonames"),
    ("wikidata", "wikidata"),
    ("wikipedia", "wikipedia"),
    ("fackel.oeaw.ac.at", "fackel"),
    ("schnitzler-tagebuch", "schnitzler-tagebuch"),
    ("schnitzler-bahr", "schnitzler-bahr"),
    ("schnitzler-briefe", "schnitzler-briefe"),
    ("schnitzler-lektueren", "schnitzler-lektueren"),
    ("doi.org/10.1553", "oebl"),
    ("kraus.wienbibliothek.at", "legalkraus"),
    ("kraus1933", "dritte-walpurgisnacht"),
    ("pmb.acdh.oeaw.ac.at", "pmb"),
]


PMB_ENTITIES = "pmb_entities"


def upload_files_to_owncloud(
        file_list,
        user=settings.OWNCLOUD_USER,
        pw=settings.OWNCLOUD_PW,
        folder=PMB_ENTITIES
):
    collection = folder
    oc = owncloud.Client('https://oeawcloud.oeaw.ac.at')
    oc.login(user, pw)

    try:
        oc.mkdir(collection)
    except:  # noqa: E722
        pass

    files = file_list
    for x in files:
        _, tail = os.path.split(x)
        owncloud_name = f'{collection}/{tail}'
        print(f"uploading {tail} to {owncloud_name}")
        oc.put_file(owncloud_name, x)


def write_report(report, report_file=settings.PMB_LOG_FILE):
    with open(report_file, 'a') as f:
        f.write(f'{",".join(report)}\n')
        return "done"
