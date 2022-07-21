from celery import shared_task
from celery.utils.log import get_task_logger
from django.core.management import call_command

# from apis_core.apis_entities.models import Person
# from apis_core.apis_tei.tei_utils import get_node_from_template, tei_header


logger = get_task_logger(__name__)


@shared_task
def sample_task():
    logger.info("The sample task just ran.")


@shared_task()
def dump_to_tei():
    call_command("dump_entities")
