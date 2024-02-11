import os
import pandas as pd
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand

from tqdm import tqdm
from typing import Any
from apis_core.apis_relations.models import AbstractRelation
from dumper.utils import write_report


class Command(BaseCommand):
    help = "Dumps all relations into a csv"

    def handle(self, *args: Any, **options: Any) -> str | None:
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        print("dumping all relations into a csv")

        data = []
        issues = []
        for x in AbstractRelation.get_all_relation_classes():
            print(x.__name__)
            for y in tqdm(x.objects.all()):
                try:
                    data.append(y.get_web_object())
                except AttributeError:
                    issues.append(y)
        df = pd.DataFrame(data)
        save_path = os.path.join(settings.MEDIA_ROOT, "relations.csv")
        df.to_csv(save_path, index=False)
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
        print(f"serialized {len(df)} relations")
        return "done"
