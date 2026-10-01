import warnings

from acdh_tei_pyutils.tei import TeiReader
from acdh_tei_pyutils.utils import any_xpath, get_xmlid
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import Collection, Uri
from normdata.utils import import_from_normdata

warnings.filterwarnings("ignore")


class Command(BaseCommand):
    help = "Imports/updates Tillich Persons"

    uris = {}

    def handle(self, *args, **kwargs):

        col, _ = Collection.objects.get_or_create(name="Tillich-Briefe")
        domain = "tillich-briefe"
        col.related_domain = [domain]
        col.published = True
        col.save()

        tei_file = "https://tillich-briefe.acdh.oeaw.ac.at/listperson.xml"
        doc = TeiReader(tei_file)
        for x in tqdm(
            doc.any_xpath(".//tei:person[./tei:idno[@type='gnd'] and ./tei:noteGrp]")
        ):
            gnd = any_xpath(x, "./tei:idno[@type='gnd']/text()")[0]
            xml_id = get_xmlid(x)
            url = f"https://tillich-briefe.acdh.oeaw.ac.at/{xml_id}.html"
            try:
                entity = import_from_normdata(gnd, "person")
            except Exception as e:
                print([gnd, url, e])
                continue
            if entity:
                entity.collection.add(col)
                try:
                    Uri.objects.get_or_create(uri=url, domain=domain, entity=entity)
                except Exception as e:
                    print([gnd, url, e])
