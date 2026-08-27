from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_metainfo.models import Collection

DOMAIN_MAPPING = [
    {
        "collection_title": "Braadsfhms Online",
        "domains": ["brahms-online"],
    },
    {
        "collection_title": "Arthur Schnitzler – Briefwechsel mit Autorinnen und Autoren",
        "domains": ["schnitzler-briefe"],
    },
    {
        "collection_title": "Arthur Schnitzler – Kulturveranstaltungen",
        "domains": ["schnitzler-kultur"],
    },
    {
        "collection_title": "Arthur Schnitzler – Lektüren",
        "domains": ["schnitzler-lektueren"],
    },
    {
        "collection_title": "Arthur Schnitzler – Tagebuch",
        "domains": ["schnitzler-tagebuch"],
    },
    {
        "collection_title": "Brahms Online",
        "domains": ["brahms-online"],
    },
    {
        "collection_title": "Briefedition Wedekind",
        "domains": ["wedekind-korrespondenz"],
    },
    {
        "collection_title": "Burgtheater",
        "domains": [""],
    },
    {
        "collection_title": "Conrad Ansorge",
        "domains": [""],
    },
    {
        "collection_title": "Die Fackel",
        "domains": ["fackel"],
    },
    {
        "collection_title": "Die Schaubühne",
        "domains": [""],
    },
    {
        "collection_title": "DLA-Schnitzler",
        "domains": ["dla-marbach"],
    },
    {
        "collection_title": "Hanslick-Online",
        "domains": ["hanslick-online"],
    },
    # {
    #     "collection_title": "Hermann Bahr – Arthur Schnitzler",
    #     "domains": [""],
    # },
    # {
    #     "collection_title": "Hermann Bahr: Tagebücher, Skizzenbücher, Notizhefte",
    #     "domains": [""],
    # },
    # {
    #     "collection_title": "Hermann Bahr – Textverzeichnis",
    #     "domains": [""],
    # },
    # {
    #     "collection_title": "Kalbeck Tagebücher",
    #     "domains": [""],
    # },
    # {
    #     "collection_title": "Karl Kraus 1933: Dritte Walpurgisnacht",
    #     "domains": [""],
    # },
    {
        "collection_title": "Karl Kraus: Rechtsakten",
        "domains": ["legalkraus"],
    },
    # {
    #     "collection_title": "Schnitzler-Veranstaltungen",
    #     "domains": [""],
    # },
    {
        "collection_title": "Schönberg-Briefe: Universal-Edition und Dreililien",
        "domains": ["schoenberg-ue"],
    },
    {
        "collection_title": "Schubert Digital",
        "domains": ["schubert-digital"],
    },
    {
        "collection_title": "SemanticKraus",
        "domains": ["semantickraus"],
    },
    {
        "collection_title": "S-Fischer",
        "domains": ["schnitzler-fischer"],
    },
    {
        "collection_title": "Stefan Zweig digital",
        "domains": ["zweig-digital"],
    },
    {
        "collection_title": "Schnitzler-Kino",
        "domains": ["schnitzler-kino"],
    },
    {
        "collection_title": "Wiener Schnitzler – Schnitzlers Wien",
        "domains": ["wienerschnitzler"],
    },
]


class Command(BaseCommand):
    help = "fetches images for places from AKON"

    def handle(self, *args, **kwargs):
        for x in tqdm(DOMAIN_MAPPING, total=len(DOMAIN_MAPPING)):
            try:
                col = Collection.objects.get(name=x["collection_title"])
            except ObjectDoesNotExist:
                continue
            col.related_domain = x["domains"]
            col.save()
