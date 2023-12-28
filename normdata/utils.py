from acdh_id_reconciler import geonames_to_wikidata, gnd_to_wikidata
from acdh_wikidata_pyutils import WikiDataPerson, WikiDataPlace
from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.core.exceptions import ObjectDoesNotExist
from icecream import ic

from apis_core.apis_entities.models import Person, Place
from apis_core.apis_metainfo.models import Uri
from dumper.utils import DOMAIN_MAPPING


def get_uri_domain(uri):
    for x in DOMAIN_MAPPING:
        if x[0] in uri:
            return x[1]


def import_from_wikidata(wikidata_url, entity_type):
    if entity_type == "person":
        wd_entity = WikiDataPerson(wikidata_url)
        apis_entity = wd_entity.get_apis_entity()
        entity = Person.objects.create(**apis_entity)
        Uri.objects.create(
            uri=get_normalized_uri(wikidata_url),
            domain="wikidata",
            entity=entity,
        )
        if wd_entity.gnd_uri:
            Uri.objects.create(
                uri=get_normalized_uri(wd_entity.gnd_uri),
                domain="gnd",
                entity=entity,
            )
    else:
        wd_entity = WikiDataPlace(wikidata_url)
        apis_entity = wd_entity.get_apis_entity()
        entity = Place.objects.create(**apis_entity)
        Uri.objects.create(
            uri=get_normalized_uri(wikidata_url),
            domain="wikidata",
            entity=entity,
        )
        if wd_entity.gnd_uri:
            Uri.objects.create(
                uri=get_normalized_uri(wd_entity.gnd_uri),
                domain="gnd",
                entity=entity,
            )
        if wd_entity.geonames_uri:
            Uri.objects.create(
                uri=get_normalized_uri(wd_entity.geonames_uri),
                domain="geonames",
                entity=entity,
            )
    return entity


def import_from_normdata(raw_url, entity_type):
    normalized_url = get_normalized_uri(raw_url)
    try:
        entity = Uri.objects.get(uri=normalized_url).entity
        return entity
    except ObjectDoesNotExist:
        pass
    domain = get_uri_domain(normalized_url)
    if domain == "gnd":
        try:
            wikidata_url = gnd_to_wikidata(normalized_url)["wikidata"]
        except (IndexError, KeyError):
            wikidata_url = False
    elif domain == "geonames":
        try:
            wikidata_url = geonames_to_wikidata(normalized_url)["wikidata"]
        except (IndexError, KeyError):
            wikidata_url = False
    elif domain == "wikidata":
        wikidata_url = normalized_url
    else:
        wikidata_url = False
    ic(domain, wikidata_url)
    if wikidata_url:
        try:
            entity = Uri.objects.get(uri=normalized_url).entity
            return entity
        except ObjectDoesNotExist:
            entity = import_from_wikidata(wikidata_url, entity_type)
    else:
        entity = None
    return entity
