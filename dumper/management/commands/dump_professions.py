import os
import pandas as pd
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from apis_core.apis_vocabularies.models import ProfessionType
from dumper.utils import write_report

SAVE_PATH = os.path.join(settings.MEDIA_ROOT, 'professions.csv')


class Command(BaseCommand):
    help = 'Dump Profession Types as csv'

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        items = ProfessionType.objects.all()
        data = []
        for x in items:
            item = {
                "id": f"{x.id}",
                "name": x.name,
                "parent_id": None,
                "parent_name": None
            }
            if x.parent_class:
                item['parent_id'] = f"{x.parent_class.id}"
                item['parent_name'] = x.parent_class.name
            data.append(item)
        df = pd.DataFrame(data)
        df.to_csv(SAVE_PATH, index=False)
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [
            os.path.basename(__file__),
            start_time,
            end_time
        ]
        write_report(report)
