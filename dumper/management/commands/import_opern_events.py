import pandas as pd
from csae_pyutils import gsheet_to_df
from django.core.management.base import BaseCommand
from tqdm import tqdm

from apis_core.apis_entities.models import Event, Institution, Person, Place, Work
from apis_core.apis_metainfo.models import Collection, Uri
from apis_core.apis_relations.models import (
    EventWork,
    InstitutionEvent,
    PersonEvent,
    PlaceEvent,
)
from apis_core.apis_vocabularies.models import (
    EventType,
    EventWorkRelation,
    InstitutionEventRelation,
    PersonEventRelation,
    PlaceEventRelation,
)


class Command(BaseCommand):
    help = "imports opern"

    def add_arguments(self, parser):
        parser.add_argument(
            "--row",
            help="which row to start?",
        )

    def handle(self, *args, **kwargs):
        if kwargs["row"]:
            start_row = int(kwargs["row"])
        else:
            start_row = 0

        col = Collection.objects.get(id=122)
        domain = "spielplan-oper_1869–1945"
        df = gsheet_to_df("1S-bCy8M4a6_GKg3DQ6lw9C95zbKsW7_GgOmSZB-0BVU")
        event_kinds = {}

        persons = {}
        works = {}
        places = {}
        orgs = {}
        person_event_relation = PersonEventRelation.objects.get(id=1256)
        event_work_relation = EventWorkRelation.objects.get(id=1201)
        place_event_relation = PlaceEventRelation.objects.get(id=1202)
        institution_event_relation = InstitutionEventRelation.objects.get(id=1351)
        for i, row in tqdm(df.iloc[start_row:].iterrows(), total=len(df) - start_row):
            pmb_uri, _ = Uri.objects.get_or_create(uri=row["uri"], domain=domain)
            entity = pmb_uri.entity
            if entity:
                event = Event.objects.get(id=entity.id)
            else:
                try:
                    event_kind = event_kinds[row["event_type"]]
                except KeyError:
                    event_kind = EventType.objects.get_or_create(
                        name=row["event_type"]
                    )[0]
                    event_kinds[row["event_type"]] = event_kind
                item = {
                    "name": row["event_name"][:254]
                    if pd.notna(row["event_name"])
                    else "",
                    "start_date_written": row["date"],
                    "end_date_written": row["date"],
                    "kind": event_kind,
                }

                entity = Event.objects.create(**item)
                entity.save()
                event = Event.objects.get(id=entity.id)
                pmb_uri.entity = entity
                pmb_uri.save()
                entity.collection.add(col)
                if pd.notna(row["mitwirkend"]):
                    for x in row["mitwirkend"].split(" | "):
                        stub, person_id = x.split(":")
                        if stub == "opera":
                            uri = f"https://www.mdw.ac.at/imi/operapolitics/spielplan-wiener-oper/web/person/{person_id}"
                        else:
                            uri = f"https://pmb.acdh.oeaw.ac.at/entity/{person_id}/"
                        try:
                            person = persons[uri]
                        except KeyError:
                            person_id = Uri.objects.get(uri=uri).entity
                            person = Person.objects.get(id=person_id.id)
                            persons[uri] = person
                        PersonEvent.objects.get_or_create(
                            related_person=person,
                            related_event=event,
                            relation_type=person_event_relation,
                            start_date_written=row["date"],
                            end_date_written=row["date"],
                        )
                if pd.notna(row["work"]):
                    for x in row["work"].split(" | "):
                        stub, work_id = x.split(":")
                        if stub == "opera":
                            uri = f"https://www.mdw.ac.at/imi/operapolitics/spielplan-wiener-oper/web/opus/{work_id}"
                        else:
                            uri = f"https://pmb.acdh.oeaw.ac.at/entity/{work_id}/"
                        try:
                            work = works[uri]
                        except KeyError:
                            work_id = Uri.objects.get(uri=uri).entity
                            work = Work.objects.get(id=work_id.id)
                            works[uri] = work
                        EventWork.objects.get_or_create(
                            related_event=event,
                            related_work=work,
                            relation_type=event_work_relation,
                            start_date_written=row["date"],
                            end_date_written=row["date"],
                        )
                if pd.notna(row["place_pmb_id"]):
                    try:
                        place = places[row["place_pmb_id"]]
                    except KeyError:
                        place = Place.objects.get(id=row["place_pmb_id"])
                        places[uri] = place
                    PlaceEvent.objects.get_or_create(
                        related_place=place,
                        related_event=event,
                        relation_type=place_event_relation,
                        start_date_written=row["date"],
                        end_date_written=row["date"],
                    )
                if pd.notna(row["org_pmb_id"]):
                    try:
                        org = orgs[row["org_pmb_id"]]
                    except KeyError:
                        org = Institution.objects.get(id=row["org_pmb_id"])
                        orgs[uri] = org
                    InstitutionEvent.objects.get_or_create(
                        related_institution=org,
                        related_event=event,
                        relation_type=institution_event_relation,
                        start_date_written=row["date"],
                        end_date_written=row["date"],
                    )
