from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import (
    TempEntityClass,
    normalize_wikimedia_img_url,
)


class Command(BaseCommand):
    help = "converts Wikimedia original image URLs of all entities to thumbnail URLs"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="only lists the changes, does not save anything",
        )

    def handle(self, *args, **options):
        items = TempEntityClass.objects.filter(
            img_url__icontains="upload.wikimedia.org"
        )
        print(f"{items.count()} entities with a Wikimedia image URL")
        changed = 0
        for x in tqdm(items, total=items.count()):
            new_url = normalize_wikimedia_img_url(x.img_url)
            if new_url == x.img_url:
                continue
            if len(new_url) > x._meta.get_field("img_url").max_length:
                print(f"{x.id}: new URL too long, skipped")
                continue
            changed += 1
            if options["dry_run"]:
                print(f"{x.id}: {x.img_url} -> {new_url}")
            else:
                x.img_url = new_url
                try:
                    x.save()
                except Exception as e:
                    print(x.id, e)
        print(
            f"{changed} image URLs {'would be ' if options['dry_run'] else ''}changed"
        )
