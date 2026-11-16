"""Rewrites relations stored with a deprecated inverse relation type (see #553).

For relations between entities of the same class (e.g. PersonPerson) one edge
can be expressed by two types: "A ist Kind von B" and "B ist Elternteil von A".
A relation type whose `canonical_inverse` is set is considered deprecated; this
command rewrites its relations to the canonical type with source and target
swapped. If the mirrored relation already exists, both are merged.

Examples:

    # list candidate pairs (name == other.name_reverse) with counts
    python manage.py normalize_inverse_relations --report

    # dry run: what would happen if 1120 ("ist Kind von") was replaced by 1109
    python manage.py normalize_inverse_relations --mark 1120:1109 --csv out.csv

    # write the marks and rewrite the relations
    python manage.py normalize_inverse_relations --mark 1120:1109 --apply --csv out.csv
"""

import csv
import re

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_vocabularies.models import RelationBaseClass

DATE_FIELDS = ["start_date_written", "end_date_written"]
TEXT_FIELDS = ["references", "notes"]
MERGE_FIELDS = DATE_FIELDS + TEXT_FIELDS
CSV_FIELDS = [
    "action",
    "relation_class",
    "relation_id",
    "old_type_id",
    "old_type",
    "new_type_id",
    "new_type",
    "source_id",
    "source",
    "target_id",
    "target",
    "counterpart_id",
    "details",
]


def same_class_relation_classes():
    return [
        relation_class
        for relation_class in AbstractRelation.get_all_relation_classes()
        if relation_class.get_related_entity_classa()
        == relation_class.get_related_entity_classb()
    ]


def relation_type_class(relation_class):
    return relation_class._meta.get_field("relation_type").related_model


def is_empty(value):
    return value is None or f"{value}".strip() == ""


def find_conflicts(relation, counterpart, fields):
    """Fields where both relations have different, non-empty values."""
    return [
        field
        for field in fields
        if not is_empty(getattr(relation, field))
        and not is_empty(getattr(counterpart, field))
        and f"{getattr(relation, field)}".strip()
        != f"{getattr(counterpart, field)}".strip()
    ]


def find_duplicate(relation, counterparts):
    """The first mirrored relation covering the same period.

    Relations with different periods are distinct relations, not duplicates
    (e.g. two separate employments). Periods count as the same if the dates
    are equal or missing on one side.
    """
    for counterpart in counterparts:
        if not find_conflicts(relation, counterpart, DATE_FIELDS):
            return counterpart
    return None


class Command(BaseCommand):
    help = (
        "Rewrites relations with a deprecated inverse relation type to its canonical "
        "inverse (source and target swapped). Dry run unless --apply is given."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--report",
            action="store_true",
            help="List candidate inverse pairs of relation types and exit.",
        )
        parser.add_argument(
            "--mark",
            action="append",
            default=[],
            metavar="DEPRECATED_ID:CANONICAL_ID",
            help="Mark a relation type as replaced by its canonical inverse. Repeatable.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Write changes. Without it, nothing is changed in the database.",
        )
        parser.add_argument("--csv", help="Write a log of all (planned) changes.")

    def handle(self, *args, **options):
        if options["report"]:
            self.report()
            return
        marks = self.parse_marks(options["mark"])
        apply = options["apply"]
        rows = []
        with transaction.atomic():
            mapping = self.current_marks()
            mapping.update(self.apply_marks(marks, save=apply))
            if not mapping:
                raise CommandError(
                    "No relation type is marked as deprecated; use --mark or --report."
                )
            for relation_class in same_class_relation_classes():
                rows += self.normalize(relation_class, mapping, apply)
        self.write_csv(options.get("csv"), rows)
        summary = {}
        for row in rows:
            summary[row["action"]] = summary.get(row["action"], 0) + 1
        mode = "applied" if apply else "dry run, nothing changed"
        self.stdout.write(f"{mode}: {summary or 'no relations to rewrite'}")

    def parse_marks(self, raw_marks):
        marks = []
        for raw in raw_marks:
            match = re.fullmatch(r"\s*(\d+)\s*:\s*(\d+)\s*", raw)
            if not match:
                raise CommandError(f"Invalid --mark '{raw}', expected 1120:1109")
            marks.append((int(match.group(1)), int(match.group(2))))
        return marks

    def apply_marks(self, marks, save):
        """Validates the marks and, if save is True, stores them in the database."""
        type_classes = [relation_type_class(rc) for rc in same_class_relation_classes()]
        mapping = {}
        for deprecated_id, canonical_id in marks:
            deprecated = None
            for type_class in type_classes:
                deprecated = type_class.objects.filter(pk=deprecated_id).first()
                if deprecated is not None:
                    break
            if deprecated is None:
                raise CommandError(
                    f"{deprecated_id} is not a relation type between entities of the same class"
                )
            canonical = RelationBaseClass.objects.filter(pk=canonical_id).first()
            if canonical is None:
                raise CommandError(f"Unknown relation type {canonical_id}")
            deprecated.canonical_inverse = canonical
            try:
                deprecated.clean()
            except ValidationError as exc:
                raise CommandError(f"{deprecated_id}:{canonical_id}: {exc}") from exc
            if deprecated.name != canonical.name_reverse:
                self.stderr.write(
                    f"warning: {deprecated.name!r} ({deprecated_id}) differs from the reverse "
                    f"name of {canonical_id}, {canonical.name_reverse!r}"
                )
            if save:
                deprecated.save()
            mapping[deprecated.pk] = canonical
        return mapping

    def current_marks(self):
        return {
            rt.pk: rt.canonical_inverse
            for rt in RelationBaseClass.objects.filter(
                canonical_inverse__isnull=False
            ).select_related("canonical_inverse")
        }

    def normalize(self, relation_class, mapping, apply):
        field_a = relation_class.get_related_entity_field_namea()
        field_b = relation_class.get_related_entity_field_nameb()
        type_ids = set(relation_type_class(relation_class).objects.values_list("pk", flat=True))
        rows = []
        for deprecated_id, canonical in mapping.items():
            if deprecated_id not in type_ids:
                continue
            relations = relation_class.objects.filter(
                relation_type_id=deprecated_id
            ).select_related(field_a, field_b, "relation_type")
            for relation in relations.iterator():
                source = getattr(relation, field_a)
                target = getattr(relation, field_b)
                row = {
                    "relation_class": relation_class.__name__,
                    "relation_id": relation.pk,
                    "old_type_id": deprecated_id,
                    "old_type": relation.relation_type.name,
                    "new_type_id": canonical.pk,
                    "new_type": canonical.name,
                    # after the rewrite, the old target becomes the source
                    "source_id": target.pk,
                    "source": f"{target}",
                    "target_id": source.pk,
                    "target": f"{source}",
                    "counterpart_id": "",
                    "details": "",
                }
                counterpart = find_duplicate(
                    relation,
                    relation_class.objects.filter(
                        **{field_a: target, field_b: source},
                        relation_type_id=canonical.pk,
                    ).exclude(pk=relation.pk),
                )
                if counterpart is None:
                    row["action"] = "flip"
                    if apply:
                        setattr(relation, field_a, target)
                        setattr(relation, field_b, source)
                        relation.relation_type_id = canonical.pk
                        relation.save()
                elif conflicts := find_conflicts(relation, counterpart, TEXT_FIELDS):
                    row["action"] = "conflict"
                    row["counterpart_id"] = counterpart.pk
                    row["details"] = "; ".join(
                        f"{field}: {getattr(relation, field)!r} ≠ {getattr(counterpart, field)!r}"
                        for field in conflicts
                    )
                else:
                    row["action"] = "merge"
                    row["counterpart_id"] = counterpart.pk
                    if apply:
                        self.merge(relation, counterpart)
                if source.pk == target.pk:
                    row["details"] = (row["details"] + " self-relation").strip()
                rows.append(row)
        return rows

    def merge(self, relation, counterpart):
        """Copies everything the counterpart lacks from relation, then deletes relation."""
        for field in MERGE_FIELDS:
            if is_empty(getattr(counterpart, field)) and not is_empty(
                getattr(relation, field)
            ):
                setattr(counterpart, field, getattr(relation, field))
        if counterpart.source_id is None and relation.source_id is not None:
            counterpart.source_id = relation.source_id
        counterpart.save()
        counterpart.collection.add(*relation.collection.all())
        counterpart.text.add(*relation.text.all())
        relation.delete()

    def report(self):
        for relation_class in same_class_relation_classes():
            type_class = relation_type_class(relation_class)
            types = list(type_class.objects.all())
            counts = {
                rt.pk: relation_class.objects.filter(relation_type=rt).count()
                for rt in types
            }
            pairs = [
                (a, b)
                for a in types
                for b in types
                if a.pk < b.pk
                and a.name != a.name_reverse
                and a.name == b.name_reverse
                and a.name_reverse == b.name
            ]
            marked = [rt for rt in types if rt.canonical_inverse_id]
            if not pairs and not marked:
                continue
            self.stdout.write(f"== {relation_class.__name__}")
            for a, b in pairs:
                self.stdout.write(
                    f"  {a.pk} {a.name!r} ({counts[a.pk]})"
                    f"  <->  {b.pk} {b.name!r} ({counts[b.pk]})"
                )
            for rt in marked:
                self.stdout.write(
                    f"  marked: {rt.pk} {rt.name!r} ({counts[rt.pk]})"
                    f" -> {rt.canonical_inverse_id} {rt.canonical_inverse.name!r}"
                )

    def write_csv(self, path, rows):
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        self.stdout.write(f"log written to {path}")
