import pandas as pd

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import TempEntityClass


def get_id(row, col):
    return int(row[col].split(" ")[0])


def is_greater(row, col_a, col_b):
    if row[col_a] > row[col_b]:
        return True
    else:
        return False


class Command(BaseCommand):
    help = """merges duplicated entities\
        e.g. python manage.py merge_duplicated_entities --csv https://pmb.acdh.oeaw.ac.at/media/duplicated_places.csv
        """

    def add_arguments(self, parser):
        parser.add_argument("--csv")

    def handle(self, *args, **kwargs):
        csv_url = kwargs["csv"]
        print(f"reading duplicated objects from csv: {csv_url}")
        df = pd.read_csv(csv_url)
        df["id_a"] = df.apply(lambda row: get_id(row, "custom_index_1"), axis=1)
        df["id_b"] = df.apply(lambda row: get_id(row, "custom_index_2"), axis=1)
        df = df[["id_a", "id_b"]]
        df["b_smaller_a"] = df.apply(
            lambda row: is_greater(row, "id_a", "id_b"), axis=1
        )

        keep_not_found = set()
        merge_did_not_work = []
        print(f"start merging of {len(df)} duplicated objects")
        for i, row in tqdm(df.iterrows(), total=len(df)):
            if row["b_smaller_a"]:
                try:
                    keep = TempEntityClass.objects.get(
                        id=row["id_b"]
                    ).get_child_entity()
                except ObjectDoesNotExist:
                    keep_not_found.add(row["id_b"])
                try:
                    keep.merge_with(row["id_a"])
                except Exception as e:
                    merge_did_not_work.append([row, e])
        if len(keep_not_found) > 0:
            print("following potential to keep objects could not be found")
            for x in keep_not_found:
                print(x)
        if len(merge_did_not_work) > 0:
            print("for following objects the merge did not work")
            for x in merge_did_not_work:
                print(x)
        print("done")
