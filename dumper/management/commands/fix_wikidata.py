import os
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from tqdm import tqdm
from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from apis_core.apis_metainfo.models import Uri
from dumper.utils import write_report


class Command(BaseCommand):
    help = "http for wikidata uris"

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        print("start fixing http for wikidata")
        to_fix = Uri.objects.filter(uri__startswith="https://www.wikidata")
        print(f"found {to_fix.count()} Uris with https")
        print("start fixing uris")
        failed = []
        for x in tqdm(to_fix, total=to_fix.count()):
            new_uri = get_normalized_uri(x.uri)
            x.uri = new_uri
            try:
                x.save()
            except IntegrityError:
                failed.append((x, x.entity))
        print("done fixing http")
        for x in failed:
            print(x)
        print(f"found {len(failed)} potential http/https duplicates")
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
