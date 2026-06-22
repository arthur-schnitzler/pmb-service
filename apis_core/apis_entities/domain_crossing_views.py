import django_tables2 as tables
from django.conf import settings
from django.db.models import Count
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

# Entitätstyp -> (Modell, Anzeigename, Icon)
ENTITY_TYPES = {
    "person": (Person, "Personen", "bi bi-people"),
    "place": (Place, "Orte", "bi bi-map"),
    "work": (Work, "Werke", "bi bi-book"),
    "event": (Event, "Ereignisse", "bi bi-calendar3"),
    "institution": (Institution, "Institutionen", "bi bi-building-gear"),
}

# Modus -> Anzeigename
MODES = {
    "intersection": "Schnittmenge",
    "union": "Vereinigung",
    "difference": "Differenz",
}

# Modus -> Erklärtext (als Tooltip angezeigt)
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

# Reihenfolge & Farben der Domains aus den Projekt-Einstellungen
DOMAIN_LABELS = [entry[1] for entry in settings.DOMAIN_MAPPING]
DOMAIN_COLORS = {entry[1]: entry[2] for entry in settings.DOMAIN_MAPPING}


# Gender-Filter: Wert -> Anzeigename (nur für Personen)
GENDER_OPTIONS = [
    ("female", "weiblich"),
    ("male", "männlich"),
    ("other", "anderes oder nicht ausgezeichnet"),
]


class DomainCrossingTable(tables.Table):
    """Generische Tabelle, die für jeden Entitätstyp funktioniert."""

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
    """Tabelle für Personen – zeigt zusätzlich den Vornamen."""

    first_name = tables.Column(verbose_name="Vorname", orderable=True)

    class Meta(DomainCrossingTable.Meta):
        sequence = (
            "id",
            "name",
            "first_name",
            "start_date_written",
            "end_date_written",
        )


class DomainCrossingView(TemplateView):
    """Findet Überschneidungen zwischen Daten-Domains (Schnittmenge,
    Vereinigung, Differenz) für einen wählbaren Entitätstyp."""

    template_name = "apis_entities/domain_crossing.html"
    export_name = "schnittmengen"

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        export_format = request.GET.get("_export", None)
        if TableExport.is_valid_format(export_format):
            exporter = TableExport(export_format, context["table"])
            return exporter.response(f"{self.export_name}.{export_format}")
        return self.render_to_response(context)

    def _querystring(self, **changes):
        """Aktuellen Querystring übernehmen, einzelne Parameter ändern und
        die Seitennummer zurücksetzen."""
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

        etype = request.GET.get("type", DEFAULT_TYPE)
        if etype not in ENTITY_TYPES:
            etype = DEFAULT_TYPE
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

        # Trefferzahl je Domain für diesen Entitätstyp
        counts = dict(
            model.objects.filter(uri__domain__in=DOMAIN_LABELS)
            .values_list("uri__domain")
            .annotate(c=Count("pk", distinct=True))
        )

        # Entitätstyp-Buttons
        entity_buttons = []
        for key, (_m, label, icon) in ENTITY_TYPES.items():
            entity_buttons.append(
                {
                    "key": key,
                    "label": label,
                    "icon": icon,
                    "active": key == etype,
                    "href": self._querystring(type=key),
                }
            )

        # Modus-Buttons
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

        # Domain-Buttons (nur Domains, die für diesen Typ vorkommen)
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

        # Gender-Buttons und -Filter (nur für Personen)
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
