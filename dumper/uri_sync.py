import csv
import io
import re
from collections import defaultdict
from dataclasses import dataclass, field

import requests
from AcdhArcheAssets.uri_norm_rules import get_normalized_uri
from django.db import transaction

from apis_core.apis_entities.models import Event, Institution, Person, Place, Work
from apis_core.apis_metainfo.models import TempEntityClass, Uri

CSV_COLUMNS = ["pmb_id", "entity_type", "uri", "domain"]
ENTITY_MODELS = {
    "person": Person,
    "place": Place,
    "org": Institution,
    "bibl": Work,
    "event": Event,
}
CHUNK_SIZE = 5000


class UriSyncError(Exception):
    """The sync of a single project had to be aborted, nothing was written."""


@dataclass
class Plan:
    domain: str
    existing_count: int = 0
    to_add: list = field(default_factory=list)  # (entity_id, uri)
    to_change: list = field(default_factory=list)  # (Uri, new_uri)
    to_delete: list = field(default_factory=list)  # Uri
    merged: list = field(default_factory=list)  # (pmb_id, uri, entity_id)
    skipped: list = field(default_factory=list)  # (entity_type, pmb_id, uri, reason)
    conflicts: list = field(default_factory=list)  # (entity_id, uri, holder)

    @property
    def has_changes(self):
        return bool(self.to_add or self.to_change or self.to_delete)


def chunked(items, size=CHUNK_SIZE):
    items = list(items)
    for i in range(0, len(items), size):
        yield items[i : i + size]


def load_csv(url, domain):
    """Downloads and validates a `pmb_uris-in-use.csv`.

    Returns a list of `(entity_type, pmb_id, normalized_uri)`. Raises `UriSyncError`
    if the file can't be fetched or breaks the contract in any way.
    """
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        text = r.content.decode("utf-8-sig")
    except (requests.RequestException, UnicodeDecodeError) as e:
        raise UriSyncError(f"could not load {url}: {e}") from e
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise UriSyncError(f"{url} is empty")
    missing = [c for c in CSV_COLUMNS if c not in reader.fieldnames]
    if missing:
        raise UriSyncError(f"{url} has no column(s) {', '.join(missing)}")

    rows, problems = [], []
    seen_keys, seen_uris = set(), set()
    for line_no, row in enumerate(reader, start=2):
        pmb_id, entity_type, uri, row_domain = (
            (row.get(c) or "").strip() for c in CSV_COLUMNS
        )
        if row_domain != domain:
            problems.append(f"line {line_no}: foreign domain {row_domain!r}")
        elif entity_type not in ENTITY_MODELS:
            problems.append(f"line {line_no}: invalid entity_type {entity_type!r}")
        elif not re.fullmatch(r"[0-9]+", pmb_id):
            problems.append(f"line {line_no}: invalid pmb_id {pmb_id!r}")
        elif not uri:
            problems.append(f"line {line_no}: empty uri")
        else:
            key, uri = (entity_type, int(pmb_id)), get_normalized_uri(uri)
            if key in seen_keys:
                problems.append(f"line {line_no}: duplicate {entity_type} {pmb_id}")
            elif uri in seen_uris:
                problems.append(f"line {line_no}: duplicate uri {uri}")
            else:
                seen_keys.add(key)
                seen_uris.add(uri)
                rows.append((entity_type, int(pmb_id), uri))
    if problems:
        examples = "; ".join(problems[:5])
        raise UriSyncError(f"{url} has {len(problems)} invalid rows, e.g. {examples}")
    if not rows:
        raise UriSyncError(f"{url} contains no rows")
    return rows


def _live_keys(rows):
    """Returns the `(entity_type, pmb_id)` of all rows pointing to an entity of that type."""
    live = set()
    for entity_type, model in ENTITY_MODELS.items():
        ids = [pmb_id for t, pmb_id, _ in rows if t == entity_type]
        for chunk in chunked(ids):
            found = model.objects.filter(pk__in=chunk).values_list("pk", flat=True)
            live.update((entity_type, pk) for pk in found)
    return live


def _existing_ids(ids):
    found = set()
    for chunk in chunked(ids):
        found.update(
            TempEntityClass.objects.filter(pk__in=chunk).values_list("pk", flat=True)
        )
    return found


def _uris_by_value(uris):
    found = {}
    for chunk in chunked(uris):
        found.update({u.uri: u for u in Uri.objects.filter(uri__in=chunk)})
    return found


def build_plan(domain, rows):
    """Compares the rows of the csv (soll) with the PMB's uris of `domain` (ist)."""
    plan = Plan(domain=domain)
    ist = defaultdict(list)
    for uri in Uri.objects.filter(domain=domain, entity__isnull=False).order_by("pk"):
        ist[uri.entity_id].append(uri)
    plan.existing_count = sum(len(v) for v in ist.values())

    by_value = _uris_by_value(uri for _, _, uri in rows)
    live = _live_keys(rows)
    not_live_ids = [pmb_id for t, pmb_id, _ in rows if (t, pmb_id) not in live]
    exists_with_other_type = _existing_ids(not_live_ids)

    soll = defaultdict(set)
    for entity_type, pmb_id, uri in rows:
        if (entity_type, pmb_id) in live:
            soll[pmb_id].add(uri)
            continue
        known = by_value.get(uri)
        if pmb_id in exists_with_other_type:
            plan.skipped.append((entity_type, pmb_id, uri, "entity has another type"))
        elif known and known.domain == domain and known.entity_id:
            # PMB doesn't remember merge targets, but merging moves the uris of the
            # merged entity to the target, so the uri is already where it belongs
            soll[known.entity_id].add(uri)
            plan.merged.append((pmb_id, uri, known.entity_id))
        else:
            plan.skipped.append((entity_type, pmb_id, uri, "entity doesn't exist"))

    for entity_id in sorted(soll.keys() | ist.keys()):
        wanted = soll.get(entity_id, set())
        have = {u.uri: u for u in ist.get(entity_id, [])}
        to_create = sorted(wanted - have.keys())
        surplus = [have[k] for k in sorted(have.keys() - wanted)]
        # an entity with a new uri instead of an old one gets its uri updated
        for new_uri, old in zip(to_create, surplus):
            plan.to_change.append((old, new_uri))
        for new_uri in to_create[len(surplus) :]:
            plan.to_add.append((entity_id, new_uri))
        plan.to_delete.extend(surplus[len(to_create) :])

    # uris are unique, so one that is held by something we don't delete can't be written
    deleted = {u.pk for u in plan.to_delete}

    def holder(uri):
        other = by_value.get(uri)
        return other if other and other.pk not in deleted else None

    plan.conflicts = [(e, u, holder(u)) for e, u in plan.to_add if holder(u)]
    plan.conflicts += [
        (o.entity_id, u, holder(u)) for o, u in plan.to_change if holder(u)
    ]
    blocked = {u for _, u, _ in plan.conflicts}
    plan.to_add = [(e, u) for e, u in plan.to_add if u not in blocked]
    plan.to_change = [(o, u) for o, u in plan.to_change if u not in blocked]
    return plan


def check_delete_ratio(plan, max_delete_ratio):
    if (
        plan.existing_count
        and len(plan.to_delete) > max_delete_ratio * plan.existing_count
    ):
        raise UriSyncError(
            f"emergency brake: would delete {len(plan.to_delete)} of "
            f"{plan.existing_count} uris (max. {max_delete_ratio:.0%}), nothing written"
        )


def apply_plan(plan):
    with transaction.atomic():
        for chunk in chunked(u.pk for u in plan.to_delete):
            Uri.objects.filter(pk__in=chunk).delete()
        changed = []
        for uri_obj, new_uri in plan.to_change:
            uri_obj.uri = new_uri
            changed.append(uri_obj)
        Uri.objects.bulk_update(changed, ["uri"], batch_size=CHUNK_SIZE)
        Uri.objects.bulk_create(
            [Uri(uri=u, domain=plan.domain, entity_id=e) for e, u in plan.to_add],
            batch_size=CHUNK_SIZE,
        )
