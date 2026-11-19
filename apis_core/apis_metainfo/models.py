import json
import re
import time
import unicodedata
from datetime import date, datetime, timedelta
from urllib.parse import quote, urlsplit
from zoneinfo import ZoneInfo

import requests
from acdh_wikidata_pyutils import (
    DEFAULT_REQUEST_HEADERS,
    IMG_EP,
    JSON_API_STUB,
    URL_STUB,
)
from AcdhArcheAssets.uri_norm_rules import get_norm_id, get_normalized_uri
from django.apps import apps
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone
from django_jsonform.models.fields import ArrayField
from model_utils.managers import InheritanceManager
from next_prev import next_in_order, prev_in_order
from tinymce.models import HTMLField

from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.errors import MergeUndoError, StartDateAfterEndDateError
from apis_core.apis_vocabularies.models import CollectionType, LabelType, TextType
from apis_core.helper_functions import DateParser

DOMAIN_MAPPING = settings.DOMAIN_MAPPING
DEFAULT_COLOR = settings.DEFAULT_COLOR
DATE_ORDER_VALIDATION_MESSAGE = (
    "Das End-Datum muss gleich oder später als das Start-Datum sein."
)

QUOTES_PATTERN = re.compile(r'"([^"]+)"|“([^“”]+)”|„([^„“”]+)“')


APOSTROPHE_PATTERN = re.compile(r"'(?=s(?:\s|$))")


def convert_quotes(value):
    """Replaces quoted passages ("…", “…”, „…“) with »…« and
    the apostrophe in "Dreher's " with ’"""
    value = QUOTES_PATTERN.sub(
        lambda m: f"»{m.group(1) or m.group(2) or m.group(3)}«", value
    )
    return APOSTROPHE_PATTERN.sub("’", value)


WIKIMEDIA_ORIGINAL_PATTERN = re.compile(
    r"^/wikipedia/(?P<project>commons|[a-z-]+)/(?P<hash>[0-9a-f]/[0-9a-f]{2})/(?P<name>[^/]+)$"
)
WIKIMEDIA_THUMB_WIDTH = 250


def pick_wikidata_image_name(claims):
    """Returns the file name of the image to use from the P18 statements of a
    wikidata item: the first one with rank "preferred", otherwise the first one
    that is not "deprecated". Returns None if there is no such statement."""
    candidates = []
    for statement in claims:
        if statement.get("rank") == "deprecated":
            continue
        try:
            name = statement["mainsnak"]["datavalue"]["value"]
        except KeyError:
            continue
        candidates.append((statement.get("rank") != "preferred", name))
    if not candidates:
        return None
    return min(candidates, key=lambda x: x[0])[1]


def get_json_with_retry(url, attempts=3):
    """GETs a JSON document, waits and retries if Wikidata/Commons answer with
    "too many requests" or a server error, raises for any other bad status."""
    for attempt in range(attempts):
        r = requests.get(url, headers=DEFAULT_REQUEST_HEADERS, timeout=30)
        if r.status_code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
            time.sleep(min(int(r.headers.get("Retry-After", 2 ** (attempt + 1))), 30))
            continue
        r.raise_for_status()
        return r.json()


def fetch_image(wikidata_uri, thumb_width=WIKIMEDIA_THUMB_WIDTH):
    """Returns the URL of a thumbnail of the image (P18) of a wikidata item,
    respecting the rank of the statements, or an empty string."""
    wikidata_id = get_norm_id(wikidata_uri) if "/" in wikidata_uri else wikidata_uri
    claims = get_json_with_retry(IMG_EP.format(wikidata_id))
    img_name = pick_wikidata_image_name(claims.get("claims", {}).get("P18", []))
    if img_name is None:
        return ""
    img = URL_STUB.format(quote(img_name))
    api_url = JSON_API_STUB.format(img.split("file/")[-1], thumb_width)
    data = get_json_with_retry(api_url)
    try:
        return next(iter(data["query"]["pages"].values()))["imageinfo"][0]["thumburl"]
    except KeyError, IndexError:
        return img


def normalize_wikimedia_img_url(url):
    """Turns the URL of an original Wikimedia file
    (https://upload.wikimedia.org/wikipedia/commons/d/da/Otto_Brahm.jpg?utm_source=…)
    into the URL of a 250px thumbnail
    (https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/Otto_Brahm.jpg/250px-Otto_Brahm.jpg).
    Other URLs and URLs that already point to a thumbnail are returned (without
    query string for Wikimedia URLs) as they are."""
    if not url:
        return url
    parts = urlsplit(url.strip())
    if parts.netloc == "commons.wikimedia.org" and parts.path.startswith(
        "/wiki/Special:FilePath/"
    ):
        # FilePath redirects to the file; width makes it redirect to a thumbnail
        return (
            f"{parts.scheme}://{parts.netloc}{parts.path}?width={WIKIMEDIA_THUMB_WIDTH}"
        )
    if parts.netloc != "upload.wikimedia.org":
        return url
    base = f"{parts.scheme}://{parts.netloc}{parts.path}"
    match = WIKIMEDIA_ORIGINAL_PATTERN.match(parts.path)
    if not match:
        return base
    name = match.group("name")
    extension = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if extension == "svg":
        thumb_name = f"{WIKIMEDIA_THUMB_WIDTH}px-{name}.png"
    elif extension in ("jpg", "jpeg", "png", "gif", "webp"):
        thumb_name = f"{WIKIMEDIA_THUMB_WIDTH}px-{name}"
    else:
        return base
    return (
        f"{parts.scheme}://{parts.netloc}/wikipedia/{match.group('project')}/thumb/"
        f"{match.group('hash')}/{name}/{thumb_name}"
    )


tz = ZoneInfo("Europe/Vienna")


def to_iso_like(value: str) -> str:
    ISO_RE = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")
    DMY_RE = re.compile(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})$")
    MY_RE = re.compile(r"^(\d{1,2})\.(\d{4})$")
    try:
        s = value.strip()
    except ValueError:
        return value

    # Keep valid ISO-like strings as-is: yyyy, yyyy-mm, yyyy-mm-dd
    if ISO_RE.fullmatch(s):
        return s

    # d.m.yyyy or dd.mm.yyyy -> yyyy-mm-dd
    m = DMY_RE.fullmatch(s)
    if m:
        day, month, year = map(int, m.groups())
        try:
            date(year, month, day)  # validates real calendar date
            return f"{year:04d}-{month:02d}-{day:02d}"
        except ValueError:
            return value  # invalid date -> keep original

    # m.yyyy or mm.yyyy -> yyyy-mm
    m = MY_RE.fullmatch(s)
    if m:
        month, year = map(int, m.groups())
        if 1 <= month <= 12:
            return f"{year:04d}-{month:02d}"
        return value

    # all other formats stay unchanged
    return value


class TempEntityClass(models.Model):
    """Base class to bind common attributes to many classes.

    The common attributes are:
    written start and enddates
    recognized start and enddates which are derived by RegEx
    from the written dates.
    A review boolean field to mark an object as reviewed
    """

    name = models.CharField(max_length=500, blank=True)
    review = models.BooleanField(
        default=False,
        help_text="Should be set to True, if the data record holds up quality standards.",
    )
    start_date = models.DateField(blank=True, null=True)
    start_start_date = models.DateField(blank=True, null=True)
    start_end_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    end_start_date = models.DateField(blank=True, null=True)
    end_end_date = models.DateField(blank=True, null=True)
    start_date_written = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="Start",
    )
    end_date_written = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="End",
    )
    text = models.ManyToManyField("Text", blank=True)
    collection = models.ManyToManyField("Collection")
    status = models.CharField(max_length=100)
    source = models.ForeignKey(
        "Source", blank=True, null=True, on_delete=models.SET_NULL
    )
    references = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    published = models.BooleanField(default=False)
    objects = models.Manager()
    objects_inheritance = InheritanceManager()
    created = models.DateTimeField(auto_now_add=True, verbose_name="angelegt")
    updated = models.DateTimeField(auto_now=True, verbose_name="zuletzt geändert")
    img_url = models.URLField(
        blank=True,
        null=True,
        max_length=600,
        verbose_name="Bild URL",
        help_text="URL zu einem Bild der Entität",
    )
    img_last_checked = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Bild geprüft am",
        help_text="Datum an dem die Bild-URL eingetragen wurde.",
    )

    def __str__(self):
        if self.name != "" and hasattr(
            self, "first_name"
        ):  # relation usually don´t have names
            return f"{self.name}, {self.first_name} (ID: {self.id})"
        elif self.name != "":
            return f"{self.name} (ID: {self.id})"
        else:
            return f"(ID: {self.id})"

    def save(self, parse_dates=True, *args, **kwargs):
        """Adaption of the save() method of the class to automatically parse string-dates into date objects"""

        if parse_dates:
            # overwrite every field with None as default
            start_date = None
            start_start_date = None
            start_end_date = None
            end_date = None
            end_start_date = None
            end_end_date = None

            if self.start_date_written:
                # If some textual user input of a start date is there, then parse it
                self.start_date_written = to_iso_like(self.start_date_written)
                start_date, start_start_date, start_end_date = DateParser.parse_date(
                    self.start_date_written
                )

            if self.end_date_written:
                # If some textual user input of an end date is there, then parse it
                self.end_date_written = to_iso_like(self.end_date_written)
                end_date, end_start_date, end_end_date = DateParser.parse_date(
                    self.end_date_written
                )

            self.start_date = start_date
            self.start_start_date = start_start_date
            self.start_end_date = start_end_date
            self.end_date = end_date
            self.end_start_date = end_start_date
            self.end_end_date = end_end_date

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise StartDateAfterEndDateError(DATE_ORDER_VALIDATION_MESSAGE)

        if self.name:
            self.name = convert_quotes(unicodedata.normalize("NFC", self.name))

        if self.img_url:
            self.img_url = normalize_wikimedia_img_url(self.img_url)
        if self.img_url and not self.img_last_checked:
            self.img_last_checked = datetime.now(tz=tz)
        if self.img_url is None:
            self.img_last_checked = None

        super().save(*args, **kwargs)

        return self

    def get_child_entity(self):
        for x in [x for x in apps.all_models["apis_entities"].values()]:
            if x.__name__ in list(settings.APIS_ENTITIES.keys()):
                try:
                    my_ent = x.objects.get(id=self.id)
                    return my_ent
                    break
                except ObjectDoesNotExist:
                    pass
        return None

    def fetch_image(self, override=False):
        wikidata_uri = self.uri_set.filter(domain__icontains="wikidata").first()
        if override and wikidata_uri:
            img_url = fetch_image(wikidata_uri.uri)
            self.img_last_checked = datetime.now(tz=tz)
            if img_url:  # noqa: SIM102
                if len(img_url) < 601:
                    self.img_url = img_url
                    print(self.id, img_url)
            self.save()
        if wikidata_uri and self.img_url is None:
            checked = datetime.now(tz=tz)
            self.img_last_checked = checked
            img_url = fetch_image(wikidata_uri.uri)
            if img_url:  # noqa: SIM102
                if len(img_url) < 601:
                    self.img_url = img_url
            self.save()
            if not self.img_url:
                # save() resets img_last_checked if there is no image; keep the
                # check date so that the entity moves to the end of the queue
                # of the fetch_images command
                type(self).objects.filter(pk=self.pk).update(img_last_checked=checked)
        return self

    def img_credit(self):
        credit = None
        if self.img_url is not None:
            if "wikimedia" in self.img_url:
                img_name = self.img_url.split("/")[-1].split("px-")[-1]
                credit = f"https://commons.wikimedia.org/wiki/File:{img_name}"
            elif "AKON" in self.img_url:
                credit = self.img_url
        return credit

    def img_credit_label(self):
        credit = None
        if self.img_url is not None:
            if (
                "commons.wikimedia.org/w/index" in self.img_url
                or "thumb" in self.img_url
            ):
                return "Wikimedia Commons"
            elif "AKON" in self.img_url:
                credit = "AKON"
            else:
                credit = None
        return credit

    def clean_start_date_written(self):
        if self.start_date_written:
            clean_date = self.start_date_written
            if "<" in self.start_date_written:
                clean_date = self.start_date_written.split("<")[0]
            return clean_date.strip()
        else:
            return ""

    def clean_end_date_written(self):
        if self.end_date_written:
            clean_date = self.end_date_written
            if "<" in self.end_date_written:
                clean_date = self.end_date_written.split("<")[0]
            return clean_date.strip()
        else:
            return ""

    @classmethod
    def get_listview_url(self):
        entity = self.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(f"apis_core:apis_entities:{entity}_list_view")
        else:
            return "/"

    @classmethod
    def get_createview_url(self):
        entity = self.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_create_view",
                kwargs={"entity": entity},
            )
        else:
            return None

    def get_edit_url(self):
        entity = self.__class__.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_edit_view",
                kwargs={"entity": entity, "pk": self.id},
            )
        else:
            return None

    def get_child_class(self):
        child = self.get_child_entity()
        if child:
            return f"{child.__class__.__name__}"
        else:
            return f"{child.__class__.__name__}"

    def get_absolute_url(self):
        entity = self.__class__.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_detail_view",
                kwargs={"entity": entity, "pk": self.id},
            )
        elif entity == "tempentityclass":
            return self.get_child_entity().get_absolute_url()
        else:
            return reverse(
                "apis_core:apis_relations:generic_relations_detail_view",
                kwargs={"entity": entity, "pk": self.id},
            )

    def get_prev_url(self):
        entity = self.__class__.__name__.lower()
        prev = prev_in_order(self)
        if prev:
            if entity == "institution" or len(entity) < 10:
                return reverse(
                    "apis_core:apis_entities:generic_entities_detail_view",
                    kwargs={"entity": entity, "pk": prev.id},
                )
            else:
                return reverse(
                    "apis_core:apis_relations:generic_relations_detail_view",
                    kwargs={"entity": entity, "pk": prev.id},
                )
        else:
            return False

    def get_next_url(self):
        entity = self.__class__.__name__.lower()
        next = next_in_order(self)
        if next:
            if entity == "institution" or len(entity) < 10:
                return reverse(
                    "apis_core:apis_entities:generic_entities_detail_view",
                    kwargs={"entity": entity, "pk": next.id},
                )
            else:
                return reverse(
                    "apis_core:apis_relations:generic_relations_detail_view",
                    kwargs={"entity": entity, "pk": next.id},
                )
        else:
            return False

    def get_delete_url(self):
        entity = self.__class__.__name__.lower()
        if entity == "institution" or len(entity) < 10:
            return reverse(
                "apis_core:apis_entities:generic_entities_delete_view",
                kwargs={"entity": entity, "pk": self.id},
            )
        else:
            return None

    def merge_with(self, entities, user=None):
        """Merge ``entities`` into ``self`` and delete them.

        Every merged entity gets a ``MergeLog`` that records the state of the
        deleted entity and everything that was moved to ``self``, so the merge
        can be undone (see ``MergeLog.undo``).
        """
        e_a_pk = self.pk
        e_a = type(self).__name__
        self_model_class = ContentType.objects.get(
            app_label="apis_entities", model__iexact=e_a
        ).model_class()
        if isinstance(entities, int):
            entities = self_model_class.objects.get(pk=entities)
        if not isinstance(entities, list) and not isinstance(entities, QuerySet):
            entities = [entities]
            entities = [
                (self_model_class.objects.get(pk=ent) if type(ent) == int else ent)
                for ent in entities
            ]
        entities = [x for x in entities if x.id > self.pk]
        rels = ContentType.objects.filter(
            app_label="apis_relations", model__icontains=e_a
        )
        try:
            self_gender = self.gender
        except AttributeError:
            self_gender = False
        for ent in entities:
            notes = []
            references = []
            try:
                ent_gender = ent.gender
            except AttributeError:
                ent_gender = False
            if isinstance(ent.notes, str):
                notes.append(ent.notes)
            if isinstance(ent.references, str):
                references.append(ent.references)
            e_b = type(ent).__name__
            e_b_pk = ent.pk
            if e_b_pk == e_a_pk:
                raise ValueError("You can not merge an entity with itself")
            if e_a != e_b:
                continue
            log = {
                "source": serialize_entity_for_merge_log(ent),
                "target_before": merge_tracked_values(self),
                "target_added_m2m": {},
                "uris": list(
                    Uri.objects.filter(entity=ent).values_list("id", flat=True)
                ),
                "labels": list(
                    Label.objects.filter(temp_entity=ent).values_list("id", flat=True)
                ),
                "relations": [],
            }
            lt, _ = LabelType.objects.get_or_create(name="Legacy name (merge)")
            col_list = list(self.collection.all())
            for col2 in ent.collection.all():
                if col2 not in col_list:
                    self.collection.add(col2)
                    log["target_added_m2m"].setdefault("collection", []).append(col2.pk)
            for f in ent._meta.local_many_to_many:
                if not f.name.endswith("_set"):
                    sl = list(getattr(self, f.name).all())
                    for s in getattr(ent, f.name).all():
                        if s not in sl:
                            getattr(self, f.name).add(s)
                            log["target_added_m2m"].setdefault(f.name, []).append(s.pk)
            legacy_label = Label.objects.create(
                label=str(ent), label_type=lt, temp_entity=self
            )
            log["legacy_label"] = legacy_label.pk
            for u in Uri.objects.filter(entity=ent):
                u.entity = self
                u.save()
            for l in Label.objects.filter(temp_entity=ent):
                l.temp_entity = self
                l.save()
            for r in rels.filter(model__icontains=e_b):
                lst_ents_rel = str(r).split()
                if lst_ents_rel[-1] == lst_ents_rel[-2]:
                    q_d = {f"related_{e_b.lower()}a": ent}
                    k = r.model_class().objects.filter(**q_d)
                    for t in k:
                        setattr(t, f"related_{e_a.lower()}a", self)
                        t.save()
                        log["relations"].append(
                            [r.app_label, r.model, t.pk, f"related_{e_a.lower()}a"]
                        )
                    q_d = {f"related_{e_b.lower()}b": ent}
                    k = r.model_class().objects.filter(**q_d)
                    for t in k:
                        setattr(t, f"related_{e_a.lower()}b", self)
                        t.save()
                        log["relations"].append(
                            [r.app_label, r.model, t.pk, f"related_{e_a.lower()}b"]
                        )
                else:
                    q_d = {f"related_{e_b.lower()}": ent}
                    k = r.model_class().objects.filter(**q_d)
                    for t in k:
                        setattr(t, f"related_{e_a.lower()}", self)
                        t.save()
                        log["relations"].append(
                            [r.app_label, r.model, t.pk, f"related_{e_a.lower()}"]
                        )
            ent_name = str(ent)[:500]
            ent.delete()
            save_target = False
            if self_gender:
                pass
            elif ent_gender:
                self.gender = ent_gender
                save_target = True
            else:
                pass
            # Only inherit the lifespan when the target has none at all, and
            # copy both dates together: the merged entity is internally
            # consistent, so this can never produce an invalid date range.
            if (
                not self.start_date_written
                and not self.end_date_written
                and (ent.start_date_written or ent.end_date_written)
            ):
                self.start_date_written = ent.start_date_written
                self.end_date_written = ent.end_date_written
                save_target = True
            # Inherit coordinates (Place) when the target has none. lat and lng
            # always go together (see Place.save), so copy both as a pair.
            if (
                hasattr(self, "lat")
                and self.lat is None
                and self.lng is None
                and (
                    getattr(ent, "lat", None) is not None
                    or getattr(ent, "lng", None) is not None
                )
            ):
                self.lat = ent.lat
                self.lng = ent.lng
                save_target = True
            if len(notes) > 0:
                additional_notes = " ".join(notes)
                self.notes = f"{self.notes} {additional_notes}"
                save_target = True
            if len(references) > 0:
                additional_references = " ".join(references)
                self.references = f"{self.references} {additional_references}"
                save_target = True
            if save_target:
                self.save()
            log["target_after"] = merge_tracked_values(self)
            MergeLog.objects.create(
                target=self,
                target_pk=self.pk,
                source_pk=e_b_pk,
                source_model=e_b.lower(),
                source_name=ent_name,
                data=log,
                user=user if user is not None and user.is_authenticated else None,
            )


# Fields of the merge target that ``merge_with`` may change; ``MergeLog`` stores
# their values before and after the merge so ``undo`` can restore them.
MERGE_TRACKED_FIELDS = [
    "notes",
    "references",
    "gender",
    "start_date_written",
    "end_date_written",
    "lat",
    "lng",
]


def merge_tracked_values(entity):
    return {f: getattr(entity, f) for f in MERGE_TRACKED_FIELDS if hasattr(entity, f)}


def serialize_entity_for_merge_log(entity):
    """Serialize an entity (its TempEntityClass row first, then the concrete
    row) including its many-to-many values, fresh from the database."""
    model = type(entity)
    objects = [TempEntityClass.objects.get(pk=entity.pk)]
    if model is not TempEntityClass:
        objects.append(model.objects.get(pk=entity.pk))
    return json.loads(serializers.serialize("json", objects))


def get_merge_undo_days():
    return getattr(settings, "MERGE_UNDO_DAYS", 14)


class MergeLog(models.Model):
    """Protocol of one merge (``source`` merged into ``target``).

    ``data`` holds a serialized copy of the deleted source entity and the ids
    of everything that was moved to the target, so the merge can be undone
    within ``settings.MERGE_UNDO_DAYS`` days.
    """

    target = models.ForeignKey(
        TempEntityClass,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="merge_logs",
        verbose_name="Ziel",
    )
    target_pk = models.PositiveIntegerField(verbose_name="ID des Ziels")
    source_pk = models.PositiveIntegerField(
        db_index=True, verbose_name="ID der gemergten Entität"
    )
    source_model = models.CharField(max_length=100, verbose_name="Entitätstyp")
    source_name = models.CharField(
        max_length=500, blank=True, verbose_name="Name der gemergten Entität"
    )
    data = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True, verbose_name="gemergt am")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="gemergt von",
    )
    undone_at = models.DateTimeField(
        blank=True, null=True, verbose_name="rückgängig gemacht am"
    )
    undone_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="rückgängig gemacht von",
    )

    class Meta:
        ordering = ["-created"]
        verbose_name = "Merge-Protokoll"
        verbose_name_plural = "Merge-Protokolle"

    def __str__(self):
        return f"{self.source_name} ({self.source_pk}) -> {self.target_pk}"

    @property
    def undo_deadline(self):
        return self.created + timedelta(days=get_merge_undo_days())

    def undo_blocker(self):
        """Reason why this merge can not be undone, or None."""
        if self.undone_at:
            return "Diese Zusammenführung wurde bereits rückgängig gemacht."
        if timezone.now() > self.undo_deadline:
            return (
                f"Zusammenführungen können nur {get_merge_undo_days()} Tage "
                "lang rückgängig gemacht werden."
            )
        if not TempEntityClass.objects.filter(pk=self.target_pk).exists():
            return "Die Ziel-Entität existiert nicht mehr."
        if TempEntityClass.objects.filter(pk=self.source_pk).exists():
            return f"Die ID {self.source_pk} ist bereits wieder vergeben."
        return None

    @property
    def can_undo(self):
        return self.undo_blocker() is None

    def undo(self, user=None):
        """Recreate the merged entity under its old id and move everything
        that was moved by the merge back to it.

        Returns a list of warnings (things that could not be restored because
        they changed after the merge).
        """
        with transaction.atomic():
            # lock the row so the same merge can not be undone twice at once
            log = MergeLog.objects.select_for_update().get(pk=self.pk)
            blocker = log.undo_blocker()
            if blocker:
                raise MergeUndoError(blocker)
            warnings = []
            data = log.data
            source_pk = log.source_pk
            target_pk = log.target_pk

            # 1. recreate the entity (raw save: no signals, no default uri)
            for obj in serializers.deserialize("json", json.dumps(data["source"])):
                obj.save()

            # 2. move uris and labels back
            moved = Uri.objects.filter(id__in=data["uris"], entity_id=target_pk)
            if moved.count() != len(data["uris"]):
                warnings.append(
                    f"{len(data['uris']) - moved.count()} URI(s) waren nicht mehr "
                    "beim Ziel und wurden nicht zurückverschoben."
                )
            moved.update(entity_id=source_pk)
            moved = Label.objects.filter(
                id__in=data["labels"], temp_entity_id=target_pk
            )
            if moved.count() != len(data["labels"]):
                warnings.append(
                    f"{len(data['labels']) - moved.count()} Label waren nicht mehr "
                    "beim Ziel und wurden nicht zurückverschoben."
                )
            moved.update(temp_entity_id=source_pk)
            if data.get("legacy_label"):
                Label.objects.filter(
                    id=data["legacy_label"], temp_entity_id=target_pk
                ).delete()

            # 3. move relations back
            missing = 0
            for app_label, model_name, rel_pk, field in data["relations"]:
                model_class = ContentType.objects.get(
                    app_label=app_label, model=model_name
                ).model_class()
                updated = model_class.objects.filter(
                    pk=rel_pk, **{f"{field}_id": target_pk}
                ).update(**{f"{field}_id": source_pk})
                if not updated:
                    missing += 1
            if missing:
                warnings.append(
                    f"{missing} Beziehung(en) wurden seit der Zusammenführung "
                    "gelöscht oder geändert und nicht zurückverschoben."
                )

            # 4. remove what the merge added to the target
            target_model = ContentType.objects.get(
                app_label="apis_entities", model=log.source_model
            ).model_class()
            target = target_model.objects.get(pk=target_pk)
            for field_name, pks in data["target_added_m2m"].items():
                getattr(target, field_name).remove(*pks)

            # 5. restore target fields, but only those unchanged since the merge
            changed = False
            for field, before in data["target_before"].items():
                after = data["target_after"].get(field)
                current = getattr(target, field)
                if current == after:
                    if current != before:
                        setattr(target, field, before)
                        changed = True
                elif before != after:
                    warnings.append(
                        f"Das Feld '{field}' der Ziel-Entität wurde seit der "
                        "Zusammenführung geändert und nicht zurückgesetzt."
                    )
            if changed:
                target.save()

            log.undone_at = timezone.now()
            log.undone_by = user if user is not None and user.is_authenticated else None
            log.save()
        return warnings


class Source(models.Model):
    """Holds information about entities and their relations"""

    orig_filename = models.CharField(max_length=500, blank=True)
    indexed = models.BooleanField(default=False)
    pubinfo = models.CharField(max_length=400, blank=True)
    author = models.CharField(max_length=500, blank=True)
    orig_id = models.PositiveIntegerField(blank=True, null=True)

    def __str__(self):
        if self.author != "" and self.orig_filename != "":
            return f"{self.orig_filename}, stored by {self.author}"
        else:
            return f"(ID: {self.id})"


class Text(models.Model):
    """Holds unstructured text associeted with
    one ore many entities/relations."""

    kind = models.ForeignKey(TextType, blank=True, null=True, on_delete=models.SET_NULL)
    text = models.TextField(blank=True)
    source = models.ForeignKey(Source, blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        if self.text != "":
            return f"ID: {self.id} - {self.text[:25]}"
        else:
            return f"ID: {self.id}"


class Uri(models.Model):
    uri = models.URLField(
        blank=True,
        null=True,
        unique=True,
        max_length=500,
        verbose_name="URI",
        help_text="Eindeutiger Identifier",
    )
    domain = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Domain",
        help_text="Domain der Normdatenquelle, z.B. gnd, wikidata, geonames, ...",
    )
    rdf_link = models.URLField(blank=True)
    entity = models.ForeignKey(
        TempEntityClass,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        verbose_name="Entität",
        help_text="Entität die mit dieser URI verbunden ist",
    )
    loaded = models.BooleanField(default=False)
    loaded_time = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return str(self.uri)

    def get_color(self):
        color = DEFAULT_COLOR
        for x in DOMAIN_MAPPING:
            if x[1] == self.domain:
                color = x[2]
                break
        return color

    def get_web_object(self):
        result = {
            "relation_pk": self.pk,
            "relation_type": "uri",
            "related_entity": self.entity.name,
            "related_entity_url": self.entity.get_absolute_url(),
            "related_entity_class_name": self.entity.__class__.__name__.lower(),
            "uri": self.uri,
        }
        return result

    def save(self, *args, **kwargs):
        self.uri = get_normalized_uri(self.uri)
        super().save(*args, **kwargs)

    @classmethod
    def get_listview_url(self):
        return reverse("apis_core:apis_metainfo:uri_browse")

    @classmethod
    def get_createview_url(self):
        return reverse("apis_core:apis_metainfo:uri_create")

    def get_absolute_url(self):
        return reverse("apis_core:apis_metainfo:uri_detail", kwargs={"pk": self.id})

    def get_delete_url(self):
        return reverse("apis_core:apis_metainfo:uri_delete", kwargs={"pk": self.id})

    def get_edit_url(self):
        return reverse("apis_core:apis_metainfo:uri_edit", kwargs={"pk": self.id})

    @classmethod
    def get_icon(self):
        return "bi bi-link-45deg apis-uri"


class Collection(models.Model):
    """Allows to group entities and relation."""

    name = models.CharField(
        verbose_name="Name",
        help_text="Name des Projektes, der Sammlung",
        max_length=500,
    )
    description = HTMLField(
        blank=True,
        verbose_name="Beschreibung",
        help_text="Kurze Beschreibung des Projektes, der Sammlung",
    )
    related_domain = ArrayField(
        models.CharField(blank=True, max_length=250, null=True),
        blank=True,
        default=list,
        verbose_name="Verknüpfte URI-Domains",
        help_text="URIs bzw. Domains, die mit diesem Projekt verbunden sind.",
    )
    collection_type = models.ForeignKey(
        CollectionType,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name="Typ des Projektes",
        help_text="Setze 'Projekt' damit das Projekt unter '/projects' aufscheint",
    )
    published = models.BooleanField(
        default=False,
        verbose_name="veröffentlicht",
        help_text="Auf 'True' setzen damit das Projekt unter 'projects' aufscheint.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "apis_core:apis_metainfo:collection_detail", kwargs={"pk": self.id}
        )

    @classmethod
    def get_icon(self):
        return "bi bi-collection apis-collection"

    def get_related_uris(self):
        uris = Uri.objects.filter(domain__in=self.related_domain)
        return uris

    def get_related_entities(self):
        uris = self.get_related_uris()
        entities = TempEntityClass.objects.filter(uri__in=uris).distinct()
        return entities

    def get_related_entities_count(self):
        return self.get_related_entities().count()
