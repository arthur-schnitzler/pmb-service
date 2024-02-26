import os
import pandas as pd
import networkx as nx
import recordlinkage
from tqdm import tqdm

from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from icecream import ic
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
            [
                "relation_type",
                "source_id",
                "target_id",
                "relation_start_date_written",
                "relation_end_date_written",
            ]
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
        print(f"serialized {len(df)} relations")
        files = list()
        files.append(save_path)
        try:
            upload_files_to_owncloud(files)
            print(f"uploading {save_path} to owncloud")
        except Exception as e:
            ic(e)
        print("and now serialize relations as network graph")
        G = nx.Graph()
        for i, row in tqdm(df.iterrows(), total=len(df)):
            G.add_nodes_from(
                [
                    (
                        row["source_id"],
                        {
                            "label": row["source"],
                            "type": row["source_type"],
                            "color": row["source_color"],
                        },
                    )
                ]
            )
            G.add_nodes_from(
                [
                    (
                        row["target_id"],
                        {
                            "label": row["target"],
                            "type": row["target_type"],
                            "color": row["target_color"],
                        },
                    )
                ]
            )
            G.add_edges_from(
                [
                    (
                        row["source_id"],
                        row["target_id"],
                        {"label": row["relation_type"], "id": row["relation_pk"]},
                    )
                ]
            )
        save_path = os.path.join(settings.MEDIA_ROOT, "relations.gexf")
        nx.write_gexf(G, save_path)
        print(f"serialized {len(df)} relations")
        files = list()
        files.append(save_path)
        try:
            upload_files_to_owncloud(files)
            print(f"uploading {save_path} to owncloud")
        except Exception as e:
            ic(e)
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
        return "done"
