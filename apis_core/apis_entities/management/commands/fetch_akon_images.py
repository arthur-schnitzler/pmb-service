import os
import urllib.request as urllib2
import warnings

import pandas as pd

from zipfile import ZipFile
from io import BytesIO

from datetime import datetime
from tqdm import tqdm

from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.conf import settings
from django.core.management.base import BaseCommand

from apis_core.apis_entities.models import Place
from dumper.utils import write_report

warnings.filterwarnings("ignore")


class Command(BaseCommand):
    help = "fetches images for places from AKON"

    def handle(self, *args, **kwargs):
        start_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        print("loading akon data into dataframe")
        POSTKARTEN_DUMP = "https://labs.onb.ac.at/gitlab/labs-team/raw-metadata/raw/master/akon_postcards_public_domain.zip?inline=false"

        print(f"downloading AKON Data from {POSTKARTEN_DUMP}")
        r = urllib2.urlopen(POSTKARTEN_DUMP).read()
        file = ZipFile(BytesIO(r))
        cards_csv = file.open("akon_postcards_public_domain.csv")
        cards_df = pd.read_csv(cards_csv, low_memory=False)
        cards_df = cards_df[["geoname_id", "download_link"]].dropna().astype("str")
        cards_df["geonames"] = cards_df["geoname_id"].apply(
            lambda x: get_normalized_uri(
                "https://sws.geonames.org/{}/".format(str(x).replace(".0", ""))
            )
        )
        cards_df = cards_df.drop_duplicates(subset="geoname_id", keep="first")
        items = Place.objects.filter(uri__domain__icontains="geonames").filter(
            img_last_checked__isnull=True
        )
        print(f"start fetching images for {items.count()} places without images")
        for x in tqdm(items, total=items.count()):
            geonames_uri = x.uri_set.filter(domain__icontains="geonames").first()
            if geonames_uri and x.img_url is None and not x.img_last_checked:
                try:
                    akon = cards_df.loc[cards_df["geonames"] == geonames_uri.uri][
                        "download_link"
                    ].values[0]
                except IndexError:
                    continue
                x.img_url = akon.replace(
                    "full/full/0/native.jpg", "full/,600/0/native.jpg"
                )
            x.img_last_checked = datetime.now()
            x.save()
        end_time = datetime.now().strftime(settings.PMB_TIME_PATTERN)
        report = [os.path.basename(__file__), start_time, end_time]
        write_report(report)
