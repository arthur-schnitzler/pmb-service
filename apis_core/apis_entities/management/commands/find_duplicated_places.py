import os
import pandas as pd
import recordlinkage
from recordlinkage.compare import Geographic

from typing import Any
from django.conf import settings
from django.core.management.base import BaseCommand

from apis_core.apis_entities.models import Place


class Command(BaseCommand):
    help = "lists potential duplicated entities"

    def handle(self, *args: Any, **options: Any) -> str | None:
        print("searching for potential duplicates")

        props = [
            "id",
            "name",
            "lat",
            "lng"
        ]
        df = pd.DataFrame(
            Place.objects.values_list(*props),
            columns=props,
        ).astype("str").fillna("nix")
        df["custom_index"] = df["id"].astype(str) + " " + df["name"]
        df.set_index("custom_index", inplace=True)
        indexer = recordlinkage.Index()
        indexer.block(["name"])
        candidate_links = indexer.index(df)
        len(candidate_links)
        compare_cl = recordlinkage.Compare()
        compare_cl.exact("name", "name", label="name")
        compare_cl.exact("lat", "lat", label="lat")
        compare_cl.exact("lng", "lng", label="lng")
        features = compare_cl.compute(candidate_links, df)
        matches = features[features.sum(axis=1) > 2]
        save_path = os.path.join(settings.MEDIA_ROOT, "duplicated_places.csv")
        matches.to_csv(save_path)
        print(f"found {len(matches)} potential duplicates")
