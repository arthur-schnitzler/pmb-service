import os
import lxml.etree as ET
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_entities.models import (
    Person,
    Place,
    Institution,
    Work
)
from apis_core.apis_tei.tei_utils import get_node_from_template, tei_header
from dumper.utils import upload_files_to_owncloud

ENTITY_MAP = {
    "person": {
        "model": Person,
        "template": "person"
    },
    "place": {
        "model": Place,
        "template": "place"
    },
    "bibl": {
        "model": Work,
        "template": "work"
    },
    "org": {
        "model": Institution,
        "template": "org"
    }
}


class Command(BaseCommand):
    help = 'Command to serialize APIS Entities to XML/TEI Entities'

    def add_arguments(self, parser):
        parser.add_argument(
            '-l',
            '--limit',
            action='store_true',
            help='number of entities should be limited',
        )
        parser.add_argument(
            '-f',
            '--full',
            action='store_true',
            help='should related entities e.g. birth-places be fully serialized',
        )
        parser.add_argument(
            '--collection',
            help='which collection?',
        )

    def handle(self, *args, **kwargs):
        for key, value in ENTITY_MAP.items():
            save_path = os.path.join(settings.MEDIA_ROOT, f'list{key}.xml')
            tei_doc = tei_header(
                title=f"List{key.capitalize()}",
                ent_type=f"<list{key.capitalize()}/>",
            )
            item_list = tei_doc.xpath(f"//*[local-name() = 'list{key.capitalize()}']")[0]

            if kwargs['full']:
                print("full is set")
                full = True
            else:
                print("simple")
                full = False

            if kwargs['collection']:
                try:
                    col_id = int(kwargs['collection'])
                except ValueError:
                    print(f"collection needs to be an integer and not: {kwargs['collection']}")
                    return False

                items = value['model'].objects.filter(collection=col_id)
            else:
                items = value['model'].objects.all()
            if kwargs['limit']:
                items = items[:20]
            print(f"serialize {items.count()} {key.capitalize()}s")
            for res in tqdm(items, total=len(items)):
                item_node = get_node_from_template(
                    f"apis_tei/{value['template']}.xml", res, full=full
                )
                item_list.append(item_node)

            with open(save_path, 'w') as f:
                mystr = ET.tostring(tei_doc).decode('utf-8')
                data = "".join([s for s in mystr.splitlines(True) if s.strip()])
                print(data, file=f)
            print(f"done serializing {items.count()} {key.capitalize()}s to {save_path}")
            files = list()
            files.append(save_path)
            upload_files_to_owncloud(files)

        print("finally done")
