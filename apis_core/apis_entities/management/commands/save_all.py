import os
import warnings

from datetime import datetime
from tqdm import tqdm
from django.conf import settings
from django.core.management.base import BaseCommand

from apis_core.apis_metainfo.models import TempEntityClass
from dumper.utils import write_report

warnings.filterwarnings("ignore")


class Command(BaseCommand):
    help = "saves all TempEntity objects"

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        items = TempEntityClass.objects.all()
        print(f"{items.count()} objects to save")
        for x in tqdm(items, total=items.count()):
            x.save()
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
