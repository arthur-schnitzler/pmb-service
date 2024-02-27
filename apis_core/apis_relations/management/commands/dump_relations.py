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
        relations_csv = os.path.join(settings.MEDIA_ROOT, "relations.csv")
        df.to_csv(relations_csv, index=False)
        print(f"serialized {len(df)} relations")
        files = list()
        files.append(relations_csv)

        print("and now serialize relations as network graph")
        G = nx.Graph()
        nodes = {}
        edges = []
        edges_labels = ["source", "target", "type", "label", "date"]
        for i, row in tqdm(df.iterrows(), total=len(df)):
            source_node = {
                "id": row["source_id"],
                "label": row["source"],
                "type": row["source_type"],
                "color": row["source_color"],
                "start_date": row["source_start_date"],
                "start_date_written": row["source_start_date_written"],
            }
            nodes[row["source_id"]] = source_node
            G.add_nodes_from([(row["source_id"], source_node)])
            target_node = {
                "id": row["target_id"],
                "label": row["target"],
                "type": row["target_type"],
                "color": row["target_color"],
                "date": row["target_start_date"],
                "start_date_written": row["target_start_date_written"],
            }
            nodes[row["target_id"]] = target_node
            G.add_nodes_from([(row["target_id"], target_node)])
            G.add_edges_from(
                [
                    (
                        row["source_id"],
                        row["target_id"],
                        {
                            "relation_class": row["relation_class"],
                            "label": row["relation_type"],
                            "id": row["relation_pk"],
                            "start_date": row["relation_start_date"],
                            "start_date_written": row["relation_start_date_written"],
                            "end_date": row["relation_end_date"],
                            "end_date_written": row["relation_end_date_written"],
                        },
                    )
                ]
            )
            edges.append(
                [
                    row["source_id"],
                    row["target_id"],
                    row["relation_class"],
                    row["relation_type"],
                    row["relation_start_date"],
                ]
            )
        gexf_file = os.path.join(settings.MEDIA_ROOT, "relations.gexf")
        nx.write_gexf(G, gexf_file)
        print(f"serialized {len(df)} relations")
        files.append(gexf_file)

        ndf = pd.DataFrame(edges, columns=edges_labels)
        edges_file = os.path.join(settings.MEDIA_ROOT, "edges.csv")
        ndf.to_csv(edges_file, index=False)
        files.append(edges_file)

        data = []
        for key, value in nodes.items():
            data.append(value)

        df = pd.DataFrame(data)
        nodes_file = os.path.join(settings.MEDIA_ROOT, "nodes.csv")
        df.to_csv(nodes_file, index=False)
        files.append(nodes_file)
        ic(files)

        try:
            upload_files_to_owncloud(files)
            for x in files:
                print(f"uploading {x} to owncloud")
        except Exception as e:
            ic(e)

        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
        return "done"
