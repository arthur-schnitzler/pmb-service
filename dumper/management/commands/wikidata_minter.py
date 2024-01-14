import os
import time
from datetime import datetime

from acdh_id_reconciler import gnd_to_wikidata, geonames_to_gnd
from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import Collection, TempEntityClass, Uri
from dumper.utils import write_report


class Command(BaseCommand):
    help = "mint WikiData IDs for GND-URIs"

    def handle(self, *args, **kwargs):
        LIMIT = 100
        USER_AGENT_PMB = "pmb (https://pmb.acdh.oeaw.ac.at)"
        col, _ = Collection.objects.get_or_create(name="No WikiData-ID found")
        types = ["d-nb.info", "geonames"]
        for uri_type in types:
            print(f"processing URIS with type: {uri_type}")
            start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
            ents = (
                TempEntityClass.objects.filter(uri__uri__icontains=uri_type)
                .exclude(uri__uri__icontains="wikidata")
                .exclude(collection=col)
            )
            uris_to_process = Uri.objects.filter(entity__in=ents).filter(
                uri__icontains=uri_type
            )

            print(
                f"All in all {uris_to_process.count()} {uri_type}-Entities without Wikidata"
            )
            for x in tqdm(uris_to_process.order_by("id")[:LIMIT], total=LIMIT):
                time.sleep(1)
                ent = x.entity
                try:
                    if uri_type == "d-nb.info":
                        results = gnd_to_wikidata(x.uri, USER_AGENT_PMB)
                    else:
                        results = geonames_to_gnd(x.uri, USER_AGENT_PMB)
                except Exception as e:
                    print(x, ent.id, e)
                    ent.collection.add(col)
                    continue
                wd_url = get_normalized_uri(results["wikidata"])
                wd_uri, _ = Uri.objects.get_or_create(uri=wd_url)
                wd_uri.entity = ent
                wd_uri.domain = "wikidata"
                wd_uri.save()
            ents = TempEntityClass.objects.filter(uri__uri__icontains=uri_type).exclude(
                uri__uri__icontains="wikidata"
            )
            uris_to_process = Uri.objects.filter(entity__in=ents).filter(
                uri__icontains=uri_type
            )
            mgs = f"{uris_to_process.count()} left"
            print(mgs)
            end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
            report = [os.path.basename(__file__), start_time, end_time]
            write_report(report)
