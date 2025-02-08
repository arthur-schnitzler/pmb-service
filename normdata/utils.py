from acdh_geonames_utils.gn_client import gn_as_object
from acdh_id_reconciler import geonames_to_wikidata, gnd_to_wikidata
from acdh_wikidata_pyutils import (
    WikiDataPerson,
    WikiDataPlace,
    WikiDataOrg,
    WikiDataEntity,
)
from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from icecream import ic
from pylobid.pylobid import PyLobidPerson, PyLobidPlace, PyLobidOrg, PyLobidWork

from apis_core.apis_entities.models import Person, Place, Institution, Work
from apis_core.apis_metainfo.models import Uri
from apis_core.apis_relations.models import PersonPlace, InstitutionPlace, PersonWork
from apis_core.apis_vocabularies.models import (
    PersonPlaceRelation,
    InstitutionPlaceRelation,
    PersonWorkRelation,
    PlaceType
)

DOMAIN_MAPPING = settings.DOMAIN_MAPPING
BIRTH_REL = getattr(settings, "BIRTH_REL")
DEATH_REL = getattr(settings, "DEATH_REL")
LOCATED_REL = getattr(settings, "ORG_LOCATED_IN")
CREATED_REL = getattr(settings, "AUTHOR_RELS")


def get_uri_domain(uri):
    for x in DOMAIN_MAPPING:
        if x[0] in uri:
            return x[1]


def get_gender_from_pylobid(fetched_item):
    ent_dict = fetched_item.get_entity_json()
    try:
        gender = ent_dict["gender"][0]["id"]
    except (KeyError, IndexError):
        return None
    if "female" in gender:
        return "female"
    else:
        return "male"


def get_or_create_place_from_gnd(uri):
    uri = get_normalized_uri(uri)
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Place.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        fetched_item = PyLobidPlace(uri)
        apis_entity = {"name": fetched_item.pref_name}
        try:
            lng, lat = fetched_item.coords
        except ValueError:
            lng = False
        if lng:
            apis_entity["lat"] = lat
            apis_entity["lng"] = lng
        entity = Place.objects.create(**apis_entity)
        Uri.objects.create(
            uri=uri,
            domain="gnd",
            entity=entity,
        )
        return entity


def get_or_create_place_from_geonames(uri):
    uri = get_normalized_uri(uri)
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Place.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        fetched_item = gn_as_object(uri)
        apis_entity = {
            "name": fetched_item["name"],
            "lat": fetched_item["latitude"],
            "lng": fetched_item["longitude"],
        }
        entity = Place.objects.create(**apis_entity)
        Uri.objects.create(
            uri=uri,
            domain="geonames",
            entity=entity,
        )
        place_type, _ = PlaceType.objects.get_or_create(name=fetched_item["feature code"])
        entity.kind = place_type
        entity.save()
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


def get_or_create_person_from_gnd(uri):
    uri = get_normalized_uri(uri)
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Person.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        fetched_item = PyLobidPerson(uri)
        pref_name = fetched_item.pref_name
        if ", " in pref_name:
            name, first_name = pref_name.split(", ")
        else:
            name, first_name = pref_name, None
        apis_entity = {
            "name": name,
            "first_name": first_name,
            "gender": get_gender_from_pylobid(fetched_item),
        }
        life_dates = fetched_item.get_life_dates()
        apis_entity["start_date_written"] = life_dates.get("birth_date_str", None)
        apis_entity["end_date_written"] = life_dates.get("death_date_str", None)
        entity = Person.objects.create(**apis_entity)
        Uri.objects.create(
            uri=uri,
            domain="gnd",
            entity=entity,
        )
        return entity


def get_or_create_org_from_gnd(uri):
    uri = get_normalized_uri(uri.strip())
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Institution.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        fetched_item = PyLobidOrg(uri)
        pref_name = fetched_item.pref_name
        apis_entity = {
            "name": pref_name,
        }
        entity = Institution.objects.create(**apis_entity)
        Uri.objects.create(
            uri=uri,
            domain="gnd",
            entity=entity,
        )
        return entity


def get_or_create_person_from_wikidata(uri):
    uri = get_normalized_uri(uri)
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
                try:
                    relation_type = PersonPlaceRelation.objects.get(id=BIRTH_REL[0])
                except ObjectDoesNotExist:
                    relation_type, _ = PersonPlaceRelation.objects.get_or_create(
                        name="geboren in"
                    )
                place = get_or_create_place_from_wikidata(wd_entity.place_of_birth)
                rel, _ = PersonPlace.objects.get_or_create(
                    related_person=entity,
                    related_place=place,
                    relation_type=relation_type,
                    start_date_written=apis_entity["start_date_written"],
                )
            if wd_entity.place_of_death:
                try:
                    relation_type = PersonPlaceRelation.objects.get(id=DEATH_REL[0])
                except ObjectDoesNotExist:
                    relation_type, _ = PersonPlaceRelation.objects.get_or_create(
                        name="gestorben in"
                    )
                place = get_or_create_place_from_wikidata(wd_entity.place_of_death)
                rel, _ = PersonPlace.objects.get_or_create(
                    related_person=entity,
                    related_place=place,
                    relation_type=relation_type,
                    start_date_written=apis_entity["end_date_written"],
                )
        return entity


def get_or_create_work_from_gnd(uri):
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Work.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        fetched_item = PyLobidWork(uri)
        try:
            start_date_written, end_date_written = fetched_item.date_of_creation.split(
                "-"
            )
        except ValueError:
            start_date_written, end_date_written = fetched_item.date_of_creation, ""
        apis_entity = {
            "name": fetched_item.pref_name,
            "start_date_written": start_date_written,
            "end_date_written": end_date_written,
        }
        entity = Work.objects.create(**apis_entity)
        Uri.objects.create(
            uri=uri,
            domain="gnd",
            entity=entity,
        )
        try:
            start_date_written, end_date_written = (
                fetched_item.date_of_production.split("-")
            )
        except ValueError:
            pass
        for x in fetched_item.creators:
            if x["role"] in ["firstAuthor", "author", "firstComposer"]:
                try:
                    wikidata_url = gnd_to_wikidata(x["id"])["wikidata"]
                    creator = get_or_create_person_from_wikidata(wikidata_url)
                except IndexError:
                    creator = get_or_create_person_from_gnd(x["id"])
                try:
                    relation_type = PersonWorkRelation.objects.get(id=CREATED_REL[0])
                except ObjectDoesNotExist:
                    relation_type, _ = PersonWorkRelation.objects.get_or_create(
                        name="hat geschaffen"
                    )
                PersonWork.objects.get_or_create(
                    related_person=creator,
                    related_work=entity,
                    relation_type=relation_type,
                    start_date_written=start_date_written,
                    end_date_written=end_date_written,
                )
        return entity


def get_or_create_work_from_wikidata(uri):
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Work.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        wd_entity = WikiDataEntity(uri)
        if wd_entity.gnd_uri:
            try:
                entity = Uri.objects.get(uri=wd_entity.gnd_uri).entity
                entity = Work.objects.get(id=entity.id)
                return entity
            except ObjectDoesNotExist:
                entity = get_or_create_work_from_gnd(wd_entity.gnd_uri)
                Uri.objects.create(
                    uri=get_normalized_uri(uri),
                    domain="wikidata",
                    entity=entity,
                )
                return entity
        else:
            apis_entity = wd_entity.get_apis_entity()
            entity = Work.objects.create(**apis_entity)
            Uri.objects.create(
                uri=get_normalized_uri(uri),
                domain="wikidata",
                entity=entity,
            )
            return entity


def get_or_create_org_from_wikidata(uri):
    try:
        entity = Uri.objects.get(uri=uri).entity
        entity = Institution.objects.get(id=entity.id)
        return entity
    except ObjectDoesNotExist:
        wd_entity = WikiDataOrg(uri)
        try:
            entity = Uri.objects.get(uri=wd_entity.gnd_uri).entity
            entity = Institution.objects.get(id=entity.id)
            return entity
        except ObjectDoesNotExist:
            apis_entity = wd_entity.get_apis_entity()
            entity = Institution.objects.create(**apis_entity)
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
            if wd_entity.location:
                try:
                    relation_type = InstitutionPlaceRelation.objects.get(
                        id=LOCATED_REL[0]
                    )
                except ObjectDoesNotExist:
                    relation_type, _ = InstitutionPlaceRelation.objects.get_or_create(
                        name="angesiedelt in"
                    )
                place = get_or_create_place_from_wikidata(wd_entity.location)
                rel, _ = InstitutionPlace.objects.get_or_create(
                    related_institution=entity,
                    related_place=place,
                    relation_type=relation_type,
                    start_date_written=apis_entity["start_date_written"],
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
            if entity_type == "work":
                try:
                    entity = get_or_create_work_from_gnd(normalized_url)
                    return entity
                except Exception as e:
                    ic(e)
                    wikidata_url = False
            if entity_type == "place":
                try:
                    entity = get_or_create_place_from_gnd(normalized_url)
                    return entity
                except Exception as e:
                    ic(e)
                    wikidata_url = False
            elif entity_type == "person":
                try:
                    entity = get_or_create_person_from_gnd(normalized_url)
                    return entity
                except Exception as e:
                    ic(e)
                    wikidata_url = False
            elif entity_type == "institution":
                try:
                    entity = get_or_create_org_from_gnd(normalized_url)
                    return entity
                except Exception as e:
                    ic(e)
                    wikidata_url = False
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
            elif entity_type == "person":
                entity = get_or_create_person_from_wikidata(wikidata_url)
            elif entity_type == "work":
                entity = get_or_create_work_from_wikidata(wikidata_url)
            else:
                entity = get_or_create_org_from_wikidata(wikidata_url)
    else:
        entity = None
    return entity
