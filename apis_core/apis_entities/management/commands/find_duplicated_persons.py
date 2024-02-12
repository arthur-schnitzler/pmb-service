import os
import pandas as pd
import recordlinkage

from typing import Any
from django.conf import settings
from django.core.management.base import BaseCommand

from apis_core.apis_entities.models import Person


class Command(BaseCommand):
    help = "lists potential duplicated entities"

    def handle(self, *args: Any, **options: Any) -> str | None:
        print("searching for potential duplicates")

        props = [
            "id",
            "name",
            "first_name",
            "start_date__year",
            "end_date__year",
        ]
        df = pd.DataFrame(
            Person.objects.exclude(start_date__isnull=True).values_list(*props),
            columns=props,
        ).astype("str")
        df["custom_index"] = df["id"].astype(str) + " " + df["name"] + df["first_name"]
        df.set_index("custom_index", inplace=True)
        indexer = recordlinkage.Index()
        indexer.block(["name"])
        candidate_links = indexer.index(df)
        len(candidate_links)
        compare_cl = recordlinkage.Compare()
        compare_cl.exact("first_name", "first_name", label="first_name")
        compare_cl.exact(
            "start_date__year", "start_date__year", label="start_date__year"
        )
        compare_cl.exact("end_date__year", "end_date__year", label="end_date__year")
        features = compare_cl.compute(candidate_links, df)
        matches = features[features.sum(axis=1) > 2]
        save_path = os.path.join(settings.MEDIA_ROOT, "duplicated_persons.csv")
        matches.to_csv(save_path)
        print(f"found {len(matches)} potential duplicates")
