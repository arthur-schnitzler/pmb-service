from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import Uri
from apis_core.apis_labels.models import Label


class Command(BaseCommand):
    help = "Normalizes Wikidata Uris"

    def handle(self, *args, **kwargs):
        labels = Label.objects.filter(label_type__name="Wien-Geschichte-Wiki")
        print(f"fixing {labels.count()} labes Wien-Geschichte-Wiki")
        for x in tqdm(labels):
            ent = x.temp_entity.get_child_entity()
            uri_val = x.label
            try:
                Uri.objects.create(uri=uri_val, domain="wiengeschichtewiki", entity=ent)
            except Exception as e:  # noqa
                # x.delete()
                continue
            # x.delete()

        labels = Label.objects.filter(label_type__name="Anno")
        print(f"fixing {labels.count()} labes Anno")
        for x in tqdm(labels):
            ent = x.temp_entity.get_child_entity()
            uri_val = x.label
            try:
                Uri.objects.create(uri=uri_val, domain="anno", entity=ent)
            except Exception as e:  # noqa
                # x.delete()
                continue
            # x.delete()
        print("done")
