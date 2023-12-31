from acdh_geonames_utils.gn_client import gn_as_object
from acdh_id_reconciler import geonames_to_wikidata, gnd_to_wikidata
from acdh_wikidata_pyutils import WikiDataPerson, WikiDataPlace
from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from icecream import ic

from apis_core.apis_entities.models import Person, Place
from apis_core.apis_metainfo.models import Uri
from apis_core.apis_relations.models import PersonPlace
from apis_core.apis_vocabularies.models import PersonPlaceRelation
from dumper.utils import DOMAIN_MAPPING

BIRTH_REL = getattr(settings, "BIRTH_REL")
DEATH_REL = getattr(settings, "DEATH_REL")


def get_uri_domain(uri):
    for x in DOMAIN_MAPPING:
        if x[0] in uri:
            return x[1]


def get_or_create_place_from_geonames(uri):
    uri = get_normalized_uri(uri)
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Place.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        geonames_obj = gn_as_object(uri)
        apis_entity = {
            "name": geonames_obj["name"],
            "lat": geonames_obj["latitude"],
            "lng": geonames_obj["longitude"],
        }
        entity = Place.objects.create(**apis_entity)
        Uri.objects.create(
            uri=uri,
            domain="geonames",
            entity=entity,
        )
        return entity


def get_or_create_place_from_wikidata(uri):
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Place.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        wd_entity = WikiDataPlace(uri)
        try:
            entity = Uri.objects.get(uri=wd_entity.geonames_uri).entity
            entity = Place.objects.get(id=entity.id)
            return entity
        except ObjectDoesNotExist:
            try:
                entity = Uri.objects.get(uri=wd_entity.gnd_uri).entity
                entity = Place.objects.get(id=entity.id)
                return entity
            except ObjectDoesNotExist:
                apis_entity = wd_entity.get_apis_entity()
                entity = Place.objects.create(**apis_entity)
                Uri.objects.create(
                    uri=get_normalized_uri(uri),
                    domain="wikidata",
                    entity=entity,
                )
                try:
                    if wd_entity.gnd_uri:
                        Uri.objects.create(
                            uri=get_normalized_uri(wd_entity.gnd_uri),
                            domain="gnd",
                            entity=entity,
                        )
                except IntegrityError:
                    pass
                try:
                    if wd_entity.geonames_uri:
                        Uri.objects.create(
                            uri=get_normalized_uri(wd_entity.geonames_uri),
                            domain="geonames",
                            entity=entity,
                        )
                except IntegrityError:
                    pass
        return entity


def get_or_create_person_from_wikidata(uri):
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Person.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        wd_entity = WikiDataPerson(uri)
        try:
            entity = Uri.objects.get(uri=wd_entity.gnd_uri).entity
            entity = Person.objects.get(id=entity.id)
            return entity
        except ObjectDoesNotExist:
            apis_entity = wd_entity.get_apis_entity()
            entity = Person.objects.create(**apis_entity)
            Uri.objects.create(
                uri=get_normalized_uri(uri),
                domain="wikidata",
                entity=entity,
            )
            if wd_entity.gnd_uri:
                try:
                    Uri.objects.create(
                        uri=get_normalized_uri(wd_entity.gnd_uri),
                        domain="gnd",
                        entity=entity,
                    )
                except IntegrityError:
                    pass
            if wd_entity.place_of_birth:
                relation_type = PersonPlaceRelation.objects.get(id=BIRTH_REL[0])
                place = get_or_create_place_from_wikidata(wd_entity.place_of_birth)
                rel, _ = PersonPlace.objects.get_or_create(
                    related_person=entity,
                    related_place=place,
                    relation_type=relation_type,
                    start_date_written=apis_entity["start_date_written"],
                )
            if wd_entity.place_of_death:
                relation_type = PersonPlaceRelation.objects.get(id=DEATH_REL[0])
                place = get_or_create_place_from_wikidata(wd_entity.place_of_death)
                rel, _ = PersonPlace.objects.get_or_create(
                    related_person=entity,
                    related_place=place,
                    relation_type=relation_type,
                    start_date_written=apis_entity["end_date_written"],
                )
        return entity


def import_from_normdata(raw_url, entity_type):
    normalized_url = get_normalized_uri(raw_url.strip())
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
            try:
                entity = get_or_create_place_from_geonames(normalized_url)
                return entity
            except Exception as e:
                ic(e)
                wikidata_url = False
    elif domain == "wikidata":
        wikidata_url = normalized_url
    else:
        wikidata_url = False
    if wikidata_url:
        try:
            entity = Uri.objects.get(uri=normalized_url).entity
            return entity
        except ObjectDoesNotExist:
            if entity_type == "place":
                entity = get_or_create_place_from_wikidata(wikidata_url)
            else:
                entity = get_or_create_person_from_wikidata(wikidata_url)
    else:
        entity = None
    return entity
