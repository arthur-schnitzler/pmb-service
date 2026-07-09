import warnings

import requests
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import Collection, Uri
from normdata.utils import import_from_normdata

warnings.filterwarnings("ignore")


class Command(BaseCommand):
    help = "Updates Hanslick Data"

    def handle(self, *args, **kwargs):
        limit = False
        iteration_limit = 25
        col, _ = Collection.objects.get_or_create(name="Hanslick-Online")
        domain = "hanslick-online"
        failed = []
        orig_data = requests.get(
            "https://raw.githubusercontent.com/Hanslick-Online/hsl-entities/refs/heads/main/json_dumps/Personen.json"
        ).json()
        for index, (key, value) in enumerate(
            tqdm(orig_data.items(), total=len(orig_data)), start=1
        ):
            if limit and index > iteration_limit:
                break
            gnd = value["gnd"]
            url = f"https://hanslick.acdh.oeaw.ac.at/{value['hsl_id']}.html"
            if gnd:
                try:
                    entity = import_from_normdata(gnd, "person")
                except Exception as e:
                    failed.append([gnd, url, e])
                    continue
                if entity:
                    entity.collection.add(col)
                    try:
                        uri, _ = Uri.objects.get_or_create(
                            uri=url, domain=domain, entity=entity
                        )
                    except Exception as e:
                        failed.append([gnd, url, e])

        print("########")
        print("and now, lets process works")
        print("########")

        orig_data = requests.get(
            "https://raw.githubusercontent.com/Hanslick-Online/hsl-entities/refs/heads/main/json_dumps/Werke.json"
        ).json()
        for index, (key, value) in enumerate(
            tqdm(orig_data.items(), total=len(orig_data)), start=1
        ):
            if limit and index > iteration_limit:
                break
            gnd = value["gnd"]
            url = f"https://hanslick.acdh.oeaw.ac.at/{value['hsl_id']}.html"
            if gnd:
                try:
                    entity = import_from_normdata(gnd, "work")
                except Exception as e:
                    failed.append([gnd, url, e])
                    continue
                if entity:
                    entity.collection.add(col)
                    try:
                        uri, _ = Uri.objects.get_or_create(
                            uri=url, domain=domain, entity=entity
                        )
                    except Exception as e:
                        failed.append([gnd, url, e])

        print("done")
        print("printing failed uris")
        for x in failed:
            print(x)
