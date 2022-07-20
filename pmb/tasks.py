import os
import lxml.etree as ET
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from tqdm import tqdm

# from apis_core.apis_entities.models import Person
# from apis_core.apis_tei.tei_utils import get_node_from_template, tei_header


logger = get_task_logger(__name__)


@shared_task
def sample_task():
    logger.info("The sample task just ran.")


# @shared_task(name="listperson")
# def dump_persons():
#     tei_doc = tei_header()
#     entity_list = tei_doc.xpath("//*[local-name() = 'listPerson']")[0]
#     items = Person.objects.all()[:20]
#     print(f"serialize {items.count()} Persons")
#     for res in tqdm(items, total=len(items)):
#         item_node = get_node_from_template(
#             'apis_tei/person.xml', res, full=full
#         )
#         listperson.append(item_node)
    
#     with open('listperson.xml', 'w') as f:
#         print(ET.tostring(tei_doc).decode('utf-8'), file=f)
#     print("done")