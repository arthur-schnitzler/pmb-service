import os
import pandas as pd
import recordlinkage

from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from icecream import ic
from tqdm import tqdm
from typing import Any
from apis_core.apis_relations.models import AbstractRelation
from dumper.utils import upload_files_to_owncloud, write_report


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
                    item = y.get_web_object()
                    item["relation_pk"] = y.id
                    data.append(item)
                except AttributeError:
                    issues.append(y)
        df = pd.DataFrame(data)
        print("lets find and delete duplicated relations")
        df.set_index("relation_pk", inplace=True, drop=False)
        save_path = os.path.join(settings.MEDIA_ROOT, "relations.csv")
        print(f"serialized {len(df)} relations")
        df.to_csv(save_path, index=False)

        df = pd.read_csv(save_path).fillna("nodate")
        df.set_index("relation_pk", inplace=True, drop=False)
        indexer = recordlinkage.Index()
        indexer.block(
            ["relation_type", "source_id", "target_id", "start_date", "end_date"]
        )
        duplicates = indexer.index(df)
        print(f"deleting {len(duplicates)} duplicated relations")

        deleted = []
        for double in duplicates:
            for x in AbstractRelation.get_all_relation_classes():
                try:
                    item = x.objects.get(id=double[1])
                except:  # noqa
                    continue
                deleted.append(item.id)
                item.delete()
                break
        print(deleted)
        df.drop(deleted)
        save_path = os.path.join(settings.MEDIA_ROOT, "relations.csv")
        df.to_csv(save_path, index=False)
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
        print(f"serialized {len(df)} relations")
        files = list()
        files.append(save_path)
        try:
            upload_files_to_owncloud(files)
        except Exception as e:
            ic(e)
        return "done"
