import os
import time
import warnings
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import F, Q
from tqdm import tqdm

from apis_core.apis_metainfo.models import TempEntityClass
from dumper.utils import write_report

warnings.filterwarnings("ignore")

RECHECK_DAYS = 30


class Command(BaseCommand):
    help = "fetches images for all entities with a wikidata URI"

    def handle(self, *args, **kwargs):
        tz = ZoneInfo("Europe/Vienna")
        start_time = datetime.now(tz=tz).strftime(settings.PMB_TIME_PATTERN)
        # never checked, or checked without result more than RECHECK_DAYS ago;
        # the least recently checked come first so that entities without an
        # image do not starve the others
        cutoff = datetime.now(tz=tz) - timedelta(days=RECHECK_DAYS)
        items = (
            TempEntityClass.objects.filter(uri__domain__icontains="wikidata")
            .filter(
                Q(img_last_checked__isnull=True)
                | Q(img_url__isnull=True, img_last_checked__lt=cutoff)
            )
            .distinct()
            .order_by(F("img_last_checked").asc(nulls_first=True), "id")
        )
        print(
            f"start fetching images for {items.count()} TempEntityClasss without images"
        )
        for x in tqdm(items[:200]):
            try:
                x.fetch_image()
            except Exception as e:
                print(x.id, e)
                continue
            time.sleep(0.5)
        end_time = datetime.now(tz=tz).strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
