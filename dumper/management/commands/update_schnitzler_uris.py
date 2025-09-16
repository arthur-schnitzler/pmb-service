import pandas as pd
from tqdm import tqdm
from django.core.management.base import BaseCommand

from apis_core.apis_metainfo.models import Uri, TempEntityClass


class Command(BaseCommand):
    help = "updates schnitzler uris"

    def handle(self, *args, **kwargs):
        print("start updating uris")
        df = pd.read_csv("https://raw.githubusercontent.com/arthur-schnitzler/schnitzler-briefe-data/refs/heads/main/csv/uris-in-use.csv")  # noqa
        to_delete = Uri.objects.filter(domain="schnitzler-briefe")
        delete = to_delete.delete()
        print(f"deleted: {delete}")
        errors = []
        created = 0
        for i, row in tqdm(df.iterrows(), total=len(df)):
            try:
                entity = TempEntityClass.objects.get(id=row["id"])
            except Exception as e:
                errors.append([row['id'], e])
                continue
            domain = row["domain"]
            uri = row["uri"]
            Uri.objects.create(uri=uri, domain=domain, entity=entity)
            created += 1
        print(f"created {created} uris")
        for x in errors:
            print(x)
