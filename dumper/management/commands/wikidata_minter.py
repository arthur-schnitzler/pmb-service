import time
from acdh_id_reconciler import gnd_to_wikidata
from tqdm import tqdm

from django.core.management.base import BaseCommand
from apis_core.apis_metainfo.models import TempEntityClass, Uri, Collection


class Command(BaseCommand):
    help = 'mint WikiData IDs for GND-URIs'

    def handle(self, *args, **kwargs):
        LIMIT = 100
        USER_AGENT_PMB = "pmb (https://pmb.acdh.oeaw.ac.at)"
        col, _ = Collection.objects.get_or_create(
            name="No WikiData-ID found"
        )

        ents = TempEntityClass.objects.filter(uri__uri__icontains="d-nb.info").\
            exclude(uri__uri__icontains="wikidata").exclude(collection=col)
        uris_to_process = Uri.objects.filter(entity__in=ents).filter(uri__icontains="d-nb.info")

        print(f"All in all {uris_to_process.count()} GND-Entities without Wikidata")
        for x in tqdm(uris_to_process.order_by('id')[:LIMIT], total=LIMIT):
            time.sleep(1)
            ent = x.entity
            try:
                results = gnd_to_wikidata(x.uri, USER_AGENT_PMB)
            except Exception as e:
                print(x, ent.id, e)
                ent.collection.add(col)
                continue
            wd_url = results['wikidata'].replace('http://', 'https://')
            wd_uri, _ = Uri.objects.get_or_create(uri=wd_url)
            wd_uri.entity = ent
            wd_uri.domain = 'wikidata'
            wd_uri.save()
        ents = TempEntityClass.objects.filter(uri__uri__icontains="d-nb.info").exclude(uri__uri__icontains="wikidata")
        uris_to_process = Uri.objects.filter(entity__in=ents).filter(uri__icontains="d-nb.info")
        print(f"{uris_to_process.count()} GND-Entities without Wikidata left")
