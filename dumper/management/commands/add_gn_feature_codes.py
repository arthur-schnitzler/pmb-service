import os
from tqdm import tqdm

from datetime import datetime

from acdh_geonames_utils.gn_client import gn_as_object
from django.conf import settings
from django.core.management.base import BaseCommand

from apis_core.apis_entities.models import Place
from apis_core.apis_vocabularies.models import PlaceType
from dumper.utils import write_report


class Command(BaseCommand):
    help = "adds geonames feature codes to places with geoname uris"

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        print("start adding geoname feature codes")
        cols = ["id", "uri__domain", "uri__uri", "kind__description"]
        places = (
            Place.objects.filter(uri__domain__icontains="geonames")
            .exclude(kind__description__icontains="geonames")
            .values_list(*cols)
        )
        places.count()
        for x in tqdm(places[:250]):
            place = Place.objects.get(id=x[0])
            gn_uri = x[2]
            try:
                gn_obj = gn_as_object(gn_uri)
            except:  # noqa
                gn_obj = {}
                gn_obj["feature code"] = "kein passender Code gefunden"
            code = gn_obj["feature code"]
            try:
                place_type, _ = PlaceType.objects.get_or_create(name=code)
            except:  # noqa
                place_type = (
                    PlaceType.objects.filter(name=code)
                    .exclude(description=None)
                    .first()
                )
            place.kind = place_type
            place.save()
        places = (
            Place.objects.filter(uri__domain__icontains="geonames")
            .exclude(kind__description__icontains="geonames")
            .values_list(*cols)
        )
        places.count()
        print(place.id)
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
