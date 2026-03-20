from typing import Any

from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import TempEntityClass, to_iso_like


class Command(BaseCommand):
    help = "formats 'german dates' as iso dates"

    def handle(self, *args: Any, **options: Any) -> str | None:
        print("formats 'german dates' as iso dates")
        batch_size = 1000
        updates = []
        print("updating start_date_written")
        qs = TempEntityClass.objects.exclude(start_date_written=None)
        for obj in tqdm(qs.iterator(chunk_size=batch_size), total=batch_size):
            obj.start_date_written = to_iso_like(obj.start_date_written)
            updates.append(obj)

            if len(updates) >= batch_size:
                TempEntityClass.objects.bulk_update(updates, ["start_date_written"])
                updates = []

        if updates:
            TempEntityClass.objects.bulk_update(updates, ["start_date_written"])

        print("updating end_date_written")
        qs = TempEntityClass.objects.exclude(end_date_written=None)
        for obj in tqdm(qs.iterator(chunk_size=batch_size), total=batch_size):
            obj.end_date_written = to_iso_like(obj.end_date_written)
            updates.append(obj)

            if len(updates) >= batch_size:
                TempEntityClass.objects.bulk_update(updates, ["end_date_written"])
                updates = []

        if updates:
            TempEntityClass.objects.bulk_update(updates, ["end_date_written"])
