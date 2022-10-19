import os
from datetime import datetime
from django.conf import settings
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import Uri
from dumper.utils import DOMAIN_MAPPING, write_report


class Command(BaseCommand):
    help = 'Command to harmonize URL-Domains'

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        print("start fixing domains")
        domains = [x[1] for x in DOMAIN_MAPPING]
        wrong_domain = Uri.objects.exclude(domain__in=domains)
        print(f"found {wrong_domain.count()} with wrong or without domains")
        print("start fixing domains")
        for x in DOMAIN_MAPPING:
            to_fix = wrong_domain.filter(uri__icontains=x[0])
            print(x[1])
            for uri in tqdm(to_fix, total=to_fix.count()):
                uri.domain = x[1]
                uri.save()
        print("done fixing domains")

        wrong_domain = Uri.objects.exclude(domain__in=domains)
        print(f"now I found {wrong_domain.count()} with wrong or without domains")
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [
            os.path.basename(__file__),
            start_time,
            end_time
        ]
        write_report(report)
