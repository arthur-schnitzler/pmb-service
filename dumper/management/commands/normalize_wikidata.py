import os
from datetime import datetime

from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import Uri
from dumper.utils import write_report


class Command(BaseCommand):
    help = "Normalizes Wikidata Uris"

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        uris_to_fix = Uri.objects.filter(uri__icontains="wikidata.org/wiki/")
        print(f"found {uris_to_fix.count()} to fix Wikidata Uris")
        for x in tqdm(uris_to_fix, total=uris_to_fix.count()):
            new_uri = get_normalized_uri(x.uri)
            x.uri = new_uri
            x.save()
        uris_to_fix = Uri.objects.filter(uri__icontains="wikidata.org/wiki/")
        print(f"now I found {uris_to_fix.count()} to fix Wikidata Uris")
        print(uris_to_fix)
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
