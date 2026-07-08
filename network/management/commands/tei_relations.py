import os
from datetime import datetime

import pandas as pd
from acdh_tei_pyutils.tei import TeiReader
from django.conf import settings
from django.core.management.base import BaseCommand

from dumper.utils import write_report
from network.models import Edge
from network.utils import relation_row_to_tei
from network.views import tei_template


class Command(BaseCommand):
    help = "Dumps relations as TEI/XML"

    def handle(self, *args, **kwargs):

        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        save_path = os.path.join(settings.MEDIA_ROOT, "relations.xml")

        values_list = [x.name for x in Edge._meta.get_fields()]
        qs = Edge.objects.all()
        items = qs.values_list(*values_list)
        df = pd.DataFrame(list(items), columns=values_list)
        relations = df.apply(relation_row_to_tei, axis=1).tolist()
        doc = TeiReader(tei_template)
        root = doc.any_xpath(".//tei:listRelation")[0]
        root.extend(relations)
        doc.tree_to_file(save_path)
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [f"{os.path.basename(__file__)}: {save_path}", start_time, end_time]
        write_report(report)

        print("finally done")
