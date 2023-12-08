import os
import time

from datetime import datetime
from acdh_id_reconciler import wikidata_to_wikipedia
from tqdm import tqdm

from django.conf import settings
from django.core.management.base import BaseCommand
from apis_core.apis_metainfo.models import TempEntityClass, Uri, Collection
from dumper.utils import write_report


class Command(BaseCommand):
    help = "mint WikiData IDs for GND-URIs"

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        LIMIT = 250
        USER_AGENT_PMB = "pmb (https://pmb.acdh.oeaw.ac.at)"
        col, _ = Collection.objects.get_or_create(name="No german Wikipedia-Site found")

        ents = (
            TempEntityClass.objects.filter(uri__domain="wikidata")
            .exclude(uri__uri__icontains="wikipedia")
            .exclude(collection=col)
        )
        uris_to_process = Uri.objects.filter(entity__in=ents).filter(domain="wikidata")

        print(
            f"All in all {uris_to_process.count()} WIKIDATA-Entities without Wikipedia"
        )
        for x in tqdm(uris_to_process.order_by("id")[:LIMIT], total=LIMIT):
            time.sleep(1)
            ent = x.entity
            try:
                wikipedia_uri = wikidata_to_wikipedia(x.uri, user_agent=USER_AGENT_PMB)
            except Exception as e:  # noqa: F841
                ent.collection.add(col)
                continue
            wd_uri, _ = Uri.objects.get_or_create(uri=wikipedia_uri)
            wd_uri.entity = ent
            wd_uri.domain = "wikipedia"
            wd_uri.save()
        ents = (
            TempEntityClass.objects.filter(uri__domain="wikidata")
            .exclude(uri__uri__icontains="wikipedia")
            .exclude(collection=col)
        )
        uris_to_process = Uri.objects.filter(entity__in=ents).filter(domain="wikidata")
        mgs = f"{uris_to_process.count()} left"
        print(mgs)
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
