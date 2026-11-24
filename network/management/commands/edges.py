import os
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from apis_core.apis_relations.models import AbstractRelation
from dumper.utils import write_report
from network.models import Edge

BATCH_SIZE = 1000


class Command(BaseCommand):
    help = "Updates Edges"

    def handle(self, *args, **kwargs):
        tz = ZoneInfo("Europe/Vienna")

        start_time = datetime.now(tz=tz).strftime(settings.PMB_TIME_PATTERN)
        with transaction.atomic():
            edges = Edge.objects.all()
            print(f"found {edges.count()} edges, going to delete those")
            edges._raw_delete(edges.db)
            print("finished deleting")
            created = 0
            for relation_class in AbstractRelation.get_all_relation_classes():
                print(f"####\n{relation_class.__name__}\n")
                edge_kind = relation_class.__name__.lower()
                source_kind = (
                    relation_class.get_related_entity_classa().__name__.lower()
                )
                target_kind = (
                    relation_class.get_related_entity_classb().__name__.lower()
                )
                relations = relation_class.objects.select_related(
                    relation_class.get_related_entity_field_namea(),
                    relation_class.get_related_entity_field_nameb(),
                    "relation_type",
                ).order_by("pk")
                last_pk = None
                with tqdm(total=relations.count()) as progress:
                    while True:
                        page = relations
                        if last_pk is not None:
                            page = page.filter(pk__gt=last_pk)
                        batch = list(page[:BATCH_SIZE])
                        if not batch:
                            break
                        new_edges = []
                        for relation in batch:
                            source_obj = relation.get_related_entity_instancea()
                            target_obj = relation.get_related_entity_instanceb()
                            item = {
                                "edge_id": relation.id,
                                "edge_kind": edge_kind,
                                "source_label": f"{source_obj}"[:249],
                                "source_kind": source_kind,
                                "source_id": source_obj.id,
                                "edge_label": f"{relation.relation_type}",
                                "target_label": f"{target_obj}"[:249],
                                "target_kind": target_kind,
                                "target_id": target_obj.id,
                                "start_date": relation.start_date,
                                "end_date": relation.end_date,
                            }
                            if source_kind == "place":
                                item["source_lat"] = source_obj.lat
                                item["source_lng"] = source_obj.lng
                            if target_kind == "place":
                                item["target_lat"] = target_obj.lat
                                item["target_lng"] = target_obj.lng
                            new_edges.append(Edge(**item))
                        Edge.objects.bulk_create(new_edges, batch_size=BATCH_SIZE)
                        created += len(new_edges)
                        progress.update(len(batch))
                        last_pk = batch[-1].pk
        print(f"created {created} Edges")
        end_time = datetime.now(tz=tz).strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
