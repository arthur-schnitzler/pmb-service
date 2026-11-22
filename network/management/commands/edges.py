import os
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_relations.models import AbstractRelation
from dumper.utils import write_report
from network.models import Edge


class Command(BaseCommand):
    help = "Updates Edges"

    def handle(self, *args, **kwargs):
        tz = ZoneInfo("Europe/Vienna")

        start_time = datetime.now(tz=tz).strftime(settings.PMB_TIME_PATTERN)
        edges = Edge.objects.all()
        print(f"found {edges.count()} edges, going to delete those")
        edges._raw_delete(edges.db)
        print("finished deleting")
        for y in AbstractRelation.get_all_relation_classes():
            print(f"####\n{y.__name__}\n")
            for x in tqdm(y.objects.all(), total=y.objects.all().count()):
                try:
                    Edge.objects.create(
                        edge_id=x.id,
                        edge_kind=y.__name__.lower(),
                        **Edge.values_from_relation(x),
                    )
                except Exception as e:
                    print(x, x.id, y.__name__.lower(), e)
        print(f"created {Edge.objects.all().count()} Edges")
        end_time = datetime.now(tz=tz).strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
