import pandas as pd
from django.core.management.base import BaseCommand

from apis_core.apis_entities.models import Person
from apis_core.apis_vocabularies.models import ProfessionType


class Command(BaseCommand):
    help = "merged duplicated professions. keeps the entry with lowest id"

    def handle(self, *args, **kwargs):
        values_list = ["id", "name"]
        items = ProfessionType.objects.all().values_list(*values_list)
        df = pd.DataFrame(list(items), columns=values_list)
        df.to_csv("foo.csv", index=False)
        for g, ndf in df.groupby("name"):
            if len(ndf) > 1:
                ndf = ndf.sort_values("id")
                keep_profession = ProfessionType.objects.get(id=ndf.iloc[0]["id"])
                print(keep_profession, keep_profession.id)
                ids_to_remove = ndf["id"].iloc[1:].tolist()
                persons = Person.objects.filter(profession__in=ids_to_remove).distinct()
                # persons should have keep_profession as profession, but already set professions should be kept
                keep_profession.person_set.add(*persons)
                ProfessionType.objects.filter(id__in=ids_to_remove).delete()
                print(
                    f"merged {len(ids_to_remove)} duplicated professions into {keep_profession.id}"
                )

        print("done")
