import os
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_relations.models import AbstractRelation
from dumper.utils import write_report

from network.models import Edge


class Command(BaseCommand):
    help = "Updates Edges"

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        edges = Edge.objects.all()
        print(f"found {edges.count()} edges, going to delete those")
        edges._raw_delete(edges.db)
        print("finished deleting")
        for y in AbstractRelation.get_all_relation_classes():
            print(f"####\n{y.__name__}\n")
            edge_kind = y.__name__.lower()
            source_kind = y.get_related_entity_classa().__name__.lower()
            target_kind = y.get_related_entity_classb().__name__.lower()
            for x in tqdm(y.objects.all(), total=y.objects.all().count()):
                source_obj = x.get_related_entity_instancea()
                target_obj = x.get_related_entity_instanceb()
                item = {
                    "edge_id": x.id,
                    "edge_kind": edge_kind,
                    "source_label": f"{source_obj}"[:249],
                    "source_kind": source_kind,
                    "source_id": source_obj.id,
                    "edge_label": f"{x.relation_type}",
                    "target_label": f"{target_obj}"[:249],
                    "target_kind": target_kind,
                    "target_id": target_obj.id,
                    "start_date": x.start_date,
                    "end_date": x.end_date,
                }
                if source_kind == "place":
                    item["source_lat"] = source_obj.lat
                    item["source_lng"] = source_obj.lng
                if target_kind == "place":
                    item["target_lat"] = target_obj.lat
                    item["target_lng"] = target_obj.lng
                try:
                    Edge.objects.create(**item)
                except Exception as e:
                    print(x, x.id, edge_kind, e)
        print(f"created {Edge.objects.all().count()} Edges")
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
