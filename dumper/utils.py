import os

import owncloud
import pandas as pd
import requests
from io import BytesIO
from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from tqdm import tqdm

from apis_core.apis_metainfo.models import Uri


PMB_ENTITIES = "pmb_entities"


def upload_files_to_owncloud(
    file_list, user=settings.OWNCLOUD_USER, pw=settings.OWNCLOUD_PW, folder=PMB_ENTITIES
):  # pragma: no cover
    collection = folder
    oc = owncloud.Client("https://oeawcloud.oeaw.ac.at")
    oc.login(user, pw)

    try:
        oc.mkdir(collection)
    except:  # noqa: E722
        pass

    files = file_list
    for x in files:
        _, tail = os.path.split(x)
        owncloud_name = f"{collection}/{tail}"
        print(f"uploading {tail} to {owncloud_name}")
        oc.put_file(owncloud_name, x)


def write_report(report, report_file=settings.PMB_LOG_FILE):  # pragma: no cover
    with open(report_file, "a") as f:
        f.write(f'{",".join(report)}\n')
        return "done"


def process_beacon(beacon_url, domain):
    """takes an URL to a beacon.txt file and a string to populate an APIS-URL domain field"""
    r = requests.get(beacon_url)
    lines = r.content.decode("utf-8").split("\n")
    created = 0
    for x in tqdm(lines, total=len(lines)):
        if "|" in x and not x.startswith("#"):
            gnd, beacon_uri = get_normalized_uri(x.split("|")[0]), x.split("|")[-1]
            try:
                item = Uri.objects.get(uri=gnd)
            except ObjectDoesNotExist:
                continue
            entity = item.entity
            try:
                Uri.objects.get(uri=beacon_uri)
                continue
            except ObjectDoesNotExist:
                new_uri = Uri.objects.create(uri=beacon_uri, entity=entity)
                new_uri.domain = domain
                new_uri.save()
                created += 1
    return created


def gsheet_to_df(sheet_id):
    GDRIVE_BASE_URL = "https://docs.google.com/spreadsheet/ccc?key="
    url = f"{GDRIVE_BASE_URL}{sheet_id}&output=csv"
    r = requests.get(url)
    print(r.status_code)
    data = r.content
    df = pd.read_csv(BytesIO(data))
    return df
