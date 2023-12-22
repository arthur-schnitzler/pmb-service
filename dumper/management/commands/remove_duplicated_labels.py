import os
from datetime import datetime

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

from apis_core.apis_metainfo.models import Label
from dumper.utils import write_report


class Command(BaseCommand):
    help = "Removes duplicated labels"

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        print("start removing duplicated labels")
        cols = [
            "temp_entity_id",
            "label",
            "label_type__name",
            "id",
            "start_date",
            "end_date",
        ]
        items = Label.objects.values_list(*cols)
        start_count = Label.objects.all().count()
        df = pd.DataFrame(items, columns=cols)
        print(f"{start_count} labels found")
        for _, gdf in df.groupby(["temp_entity_id", "label", "label_type__name"]):
            if len(gdf) > 1:
                for _, row in gdf.iloc[1:].iterrows():
                    if row["start_date"] or row["end_date"]:
                        continue
                    else:
                        lab = Label.objects.get(id=row["id"])
                        print(f"deleting {lab}")
                        lab.delete()
        end_count = Label.objects.all().count()
        print(f"{end_count} labels left")
        print(f"{start_count - end_count} labels deleted")
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
