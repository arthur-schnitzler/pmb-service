from django.core.management.base import BaseCommand

from dumper.utils import process_beacon


class Command(BaseCommand):
    help = "parses a gnd-beacon file and adds new uris to matching entities"

    def add_arguments(self, parser):
        parser.add_argument("--beacon")
        parser.add_argument("--domain")

    def handle(self, *args, **kwargs):
        beacon_url = kwargs["beacon"]
        domain = kwargs["domain"]
        new_uris = process_beacon(beacon_url, domain)
        print(f"added {new_uris} new uris")
        return "done"
