import django_tables2 as tables
import pandas as pd
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django_tables2 import RequestConfig
from django_tables2.export import TableExport

from apis_core.apis_entities.models import (
    Event,
    Institution,
    Person,
    Place,
    Work,
)

# Entity type -> (model, display name, icon)
ENTITY_TYPES = {
    "person": (Person, "Personen", "bi bi-people"),
    "place": (Place, "Orte", "bi bi-map"),
    "work": (Work, "Werke", "bi bi-book"),
    "event": (Event, "Ereignisse", "bi bi-calendar3"),
    "institution": (Institution, "Institutionen", "bi bi-building-gear"),
}

# Mode -> display name
MODES = {
    "intersection": "Schnittmenge",
    "union": "Vereinigung",
    "difference": "Differenz",
}

# Mode -> explanatory text (shown as a tooltip)
MODE_DESCRIPTIONS = {
    "intersection": (
        "Entitäten, die in allen gewählten Domains vorkommen. "
        "Beispiel: Personen, die sowohl in »schnitzler-briefe« als auch "
        "in »gnd« vorhanden sind."
    ),
    "union": (
        "Entitäten, die in mindestens einer der gewählten Domains vorkommen. "
        "Beispiel: alle Personen, die in »schnitzler-briefe« oder »gnd« "
        "(oder in beiden) vorkommen."
    ),
    "difference": (
        "Entitäten, die in der Basis-Domain vorkommen, aber in keiner der "
        "ausgeschlossenen Domains. Beispiel: Personen in »schnitzler-briefe«, "
        "die keinen »gnd«-Eintrag haben."
    ),
}

DEFAULT_TYPE = "person"
DEFAULT_MODE = "intersection"

# Order & colors of the domains from the project settings
DOMAIN_LABELS = [entry[1] for entry in settings.DOMAIN_MAPPING]
DOMAIN_COLORS = {entry[1]: entry[2] for entry in settings.DOMAIN_MAPPING}


# Gender filter: value -> display name (persons only)
GENDER_OPTIONS = [
    ("female", "weiblich"),
    ("male", "männlich"),
    ("other", "anderes oder nicht ausgezeichnet"),
]


class DomainCrossingTable(tables.Table):
    """Generic table that works for any entity type."""

    id = tables.Column(verbose_name="ID", orderable=True, linkify=True)
    name = tables.Column(
        verbose_name="Name", orderable=True, linkify=True, default="ohne Name"
    )
    start_date_written = tables.Column(verbose_name="von", orderable=True)
    end_date_written = tables.Column(verbose_name="bis", orderable=True)

    class Meta:
        attrs = {"class": "table table-responsive table-hover"}
        sequence = ("id", "name", "start_date_written", "end_date_written")


class PersonCrossingTable(DomainCrossingTable):
    """Table for persons – also shows the first name."""

    first_name = tables.Column(verbose_name="Vorname", orderable=True)

    class Meta(DomainCrossingTable.Meta):
        sequence = (
            "id",
            "name",
            "first_name",
            "start_date_written",
            "end_date_written",
        )


class EntityCrossingViewMixin:
    """Shared logic for views that offer a selectable entity type."""

    def _querystring(self, **changes):
        """Take over the current querystring, change individual parameters
        and reset the page number."""
        params = self.request.GET.copy()
        params.pop("page", None)
        for key, value in changes.items():
            if value is None or value == []:
                params.pop(key, None)
            elif isinstance(value, list):
                params.setlist(key, value)
            else:
                params[key] = value
        return f"?{params.urlencode()}"

    def _get_entity_type(self):
        etype = self.request.GET.get("type", DEFAULT_TYPE)
        return etype if etype in ENTITY_TYPES else DEFAULT_TYPE

    def _entity_buttons(self, etype):
        return [
            {
                "key": key,
                "label": label,
                "icon": icon,
                "active": key == etype,
                "href": self._querystring(type=key),
            }
            for key, (_m, label, icon) in ENTITY_TYPES.items()
        ]


@method_decorator(login_required, name="dispatch")
class MostValuableEntityView(EntityCrossingViewMixin, TemplateView):
    """ranks entities by domains"""

    template_name = "apis_entities/most_valuable_entity.html"
    export_name = "haeufig_verwendete_entitaeten"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        export_format = request.GET.get("_export")
        if export_format in ("csv", "json"):
            return self._export(context["rows"], export_format)
        return self.render_to_response(context)

    def _export(self, rows, export_format):
        export_rows = []
        for row in rows:
            entry = {
                "id": row["entity"],
                "name": row.get("entity__name") or "ohne Name",
            }
            if "first_name" in row:
                entry["first_name"] = row.get("first_name")
            entry["count"] = row["count"]
            entry["uris"] = "; ".join(uri for uri, _domain in row["uris"])
            export_rows.append(entry)
        df = pd.DataFrame(export_rows)
        filename = f"{self.export_name}.{export_format}"
        if export_format == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            df.to_csv(response, index=False)
        else:
            response = HttpResponse(content_type="application/json")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            df.to_json(response, orient="records", force_ascii=False)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        etype = self._get_entity_type()
        if etype in ["person", "place", "work"]:
            threshold = 14
        else:
            threshold = 2
        items = ENTITY_TYPES[etype][0].objects.all()
        values_list = ["uri__uri", "uri__domain", "name", "id"]
        if etype == "person":
            values_list.append("first_name")
        qs = items.values_list(*values_list)
        df = pd.DataFrame(list(qs), columns=values_list)
        df = df.rename(
            columns={
                "uri__uri": "uri",
                "uri__domain": "domain",
                "name": "entity__name",
                "id": "entity",
            }
        )
        df["host"] = df["uri"].str.extract(r"https?://([^/]+)")
        df = df.drop_duplicates(subset=["host", "domain", "entity"], keep="first")
        group_cols = ["entity", "entity__name"]
        if etype == "person":
            group_cols.append("first_name")
        biggest_groups = (
            df.assign(uri_domain=list(zip(df["uri"], df["domain"])))
            .groupby(group_cols)
            .agg(
                count=("entity", "size"),
                uris=("uri_domain", list),
            )
            .sort_values("count", ascending=False)
            .reset_index()
            .query(f"count >= {threshold}")
        )

        context["entity_buttons"] = self._entity_buttons(etype)
        context["entity"] = etype
        context["rows"] = biggest_groups.to_dict(orient="records")
        context["uri_count"] = items.count()
        return context


@method_decorator(login_required, name="dispatch")
class DomainCrossingView(EntityCrossingViewMixin, TemplateView):
    """Finds overlaps between data domains (intersection, union,
    difference) for a selectable entity type."""

    template_name = "apis_entities/domain_crossing.html"
    export_name = "schnittmengen"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        export_format = request.GET.get("_export", None)
        if TableExport.is_valid_format(export_format):
            exporter = TableExport(export_format, context["table"])
            return exporter.response(f"{self.export_name}.{export_format}")
        return self.render_to_response(context)

    def _build_queryset(self, model, mode, selected, base):
        qs = model.objects.all()
        if mode == "union":
            if not selected:
                return qs.none()
            qs = qs.filter(uri__domain__in=selected)
        elif mode == "difference":
            if base not in DOMAIN_LABELS:
                return qs.none()
            qs = qs.filter(uri__domain=base)
            excluded = [d for d in selected if d != base]
            if excluded:
                qs = qs.exclude(uri__domain__in=excluded)
        else:  # intersection
            if not selected:
                return qs.none()
            for domain in selected:
                qs = qs.filter(uri__domain=domain)
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        request = self.request

        etype = self._get_entity_type()
        mode = request.GET.get("mode", DEFAULT_MODE)
        if mode not in MODES:
            mode = DEFAULT_MODE
        selected = [d for d in request.GET.getlist("d") if d in DOMAIN_LABELS]
        base = request.GET.get("base")
        if base not in DOMAIN_LABELS:
            base = None
        gender = request.GET.get("gender")
        if gender not in dict(GENDER_OPTIONS):
            gender = None

        model, verbose_name, _icon = ENTITY_TYPES[etype]

        # Number of hits per domain for this entity type
        counts = dict(
            model.objects.filter(uri__domain__in=DOMAIN_LABELS)
            .values_list("uri__domain")
            .annotate(c=Count("pk", distinct=True))
        )

        # Entity type buttons
        entity_buttons = self._entity_buttons(etype)

        # Mode buttons
        mode_buttons = [
            {
                "key": key,
                "label": label,
                "description": MODE_DESCRIPTIONS[key],
                "active": key == mode,
                "href": self._querystring(mode=key),
            }
            for key, label in MODES.items()
        ]

        # Domain buttons (only domains that occur for this type)
        domain_buttons = []
        base_buttons = []
        for domain in DOMAIN_LABELS:
            count = counts.get(domain, 0)
            if not count:
                continue
            color = DOMAIN_COLORS.get(domain, settings.DEFAULT_COLOR)
            is_selected = domain in selected
            toggled = (
                [d for d in selected if d != domain]
                if is_selected
                else selected + [domain]
            )
            domain_buttons.append(
                {
                    "label": domain,
                    "color": color,
                    "count": count,
                    "selected": is_selected,
                    "href": self._querystring(d=toggled),
                }
            )
            base_buttons.append(
                {
                    "label": domain,
                    "color": color,
                    "count": count,
                    "selected": domain == base,
                    "href": self._querystring(base=None if domain == base else domain),
                }
            )

        # Gender buttons and filter (persons only)
        gender_buttons = []
        if etype == "person":
            for value, label in GENDER_OPTIONS:
                gender_buttons.append(
                    {
                        "value": value,
                        "label": label,
                        "active": value == gender,
                        "href": self._querystring(
                            gender=None if value == gender else value
                        ),
                    }
                )

        queryset = self._build_queryset(model, mode, selected, base)
        if etype == "person" and gender:
            if gender == "other":
                queryset = queryset.exclude(gender__in=["female", "male"])
            else:
                queryset = queryset.filter(gender=gender)
        queryset = queryset.order_by("name")

        table_class = PersonCrossingTable if etype == "person" else DomainCrossingTable
        table = table_class(queryset)
        RequestConfig(request, paginate={"per_page": 25}).configure(table)

        context.update(
            {
                "table": table,
                "entity": etype,
                "verbose_name": verbose_name,
                "mode": mode,
                "mode_label": MODES[mode],
                "selected": selected,
                "base": base,
                "gender": gender,
                "entity_buttons": entity_buttons,
                "mode_buttons": mode_buttons,
                "domain_buttons": domain_buttons,
                "base_buttons": base_buttons,
                "gender_buttons": gender_buttons,
                "total": table.paginator.count,
                "enable_merge": False,
                "app_name": "apis_entities",
            }
        )
        return context
