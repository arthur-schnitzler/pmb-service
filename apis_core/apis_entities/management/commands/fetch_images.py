import os
import time
import warnings

from datetime import datetime
from tqdm import tqdm
from django.conf import settings
from django.core.management.base import BaseCommand

from apis_core.apis_entities.models import Person
from dumper.utils import write_report

warnings.filterwarnings('ignore')


class Command(BaseCommand):
    help = "fetches images for persons"

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        items = Person.objects.filter(uri__domain__icontains="wikidata").filter(
            img_last_checked__isnull=True
        )
        print(f"start fetching images for {items.count()} persons without images")
        for x in tqdm(items[:200]):
            x.fetch_image()
            time.sleep(0.5)
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
