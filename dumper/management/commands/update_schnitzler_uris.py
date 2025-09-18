import pandas as pd
from tqdm import tqdm
from django.core.management.base import BaseCommand

from apis_core.apis_metainfo.models import Uri, TempEntityClass


class Command(BaseCommand):
    help = "updates schnitzler uris"

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default="https://raw.githubusercontent.com/arthur-schnitzler/schnitzler-briefe-data/refs/heads/main/csv/uris-in-use.csv",  # noqa: E501
            help="CSV URL to use"
        )

    def handle(self, *args, **kwargs):
        print("start updating uris")
        url = kwargs['url']
        print(f"Using URL: {url}")
        df = pd.read_csv(url)
        domains = df["domain"].unique().tolist()
        print(f"Found domains: {domains}")
        to_delete = Uri.objects.filter(domain__in=domains)
        print(f"found {to_delete.count()} in {" ".join([x for x in domains])} to delete")
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
