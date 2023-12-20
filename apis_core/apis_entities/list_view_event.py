import django_filters
import django_tables2 as tables
from apis_core.apis_entities.models import Event
from apis_core.apis_vocabularies.models import (EventEventRelation, EventType,
                                                EventWorkRelation,
                                                InstitutionEventRelation,
                                                PersonEventRelation,
                                                PlaceEventRelation)
from apis_core.helper_functions.utils import get_child_classes
from browsing.browsing_utils import GenericListView
from crispy_bootstrap5.bootstrap5 import BS5Accordion
from crispy_forms.bootstrap import AccordionGroup
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from dal import autocomplete

excluded_cols = [
    "start_start_date",
    "start_end_date",
    "end_start_date",
    "end_end_date",
    "status",
    "source",
    "references",
    "published",
    "tempentityclass_ptr",
    "review",
]


EVENT_PERSON_RELATION_CHOICES = [
    (f"{x.id}", f"{x.label_reverse} (ID: {x.id})")
    for x in PersonEventRelation.objects.all()
]
EVENT_PLACE_RELATION_CHOICES = [
    (f"{x.id}", f"{x.label_reverse} (ID: {x.id})")
    for x in PlaceEventRelation.objects.all()
]
EVENT_EVENT_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in EventEventRelation.objects.all()
]
EVENT_INSTITUTION_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in InstitutionEventRelation.objects.all()
]
EVENT_WORK_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in EventWorkRelation.objects.all()
]


class EventListFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Name des Ereignisses",
        help_text="eingegebene Zeichenkette muss im Titel enthalten sein",
    )
    year_of_creation = django_filters.NumberFilter(
        field_name="start_date__year", label="Schöpfungsdatum", help_text="z.B. 1880"
    )
    related_with_person = django_filters.LookupChoiceFilter(
        lookup_choices=EVENT_PERSON_RELATION_CHOICES,
        label="Bezugsperson",
        help_text="Name einer Bezugsperson und die Art des Beziehung, z.B. 'hat als Arbeitskraft' und 'Haindl'",
        method="related_person_filter",
    )
    related_with_place = django_filters.LookupChoiceFilter(
        lookup_choices=EVENT_PLACE_RELATION_CHOICES,
        label="Bezugsort",
        help_text="Names eines Bezugsort und die Art des Beziehung, z.B. 'veranstaltet in' und 'Volkstheater'",
        method="related_place_filter",
    )
    related_with_work = django_filters.LookupChoiceFilter(
        lookup_choices=EVENT_WORK_RELATION_CHOICES,
        label="Werk",
        help_text="Name einer Werkes und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geschaffen von'",
        method="related_work_filter",
    )
    kind = django_filters.ModelMultipleChoiceFilter(
        queryset=EventType.objects.all(),
        help_text="Art/Typ des Ereignisses, z.B. 'Premiere'",
        label="Art des Ereignisses",
        widget=autocomplete.Select2Multiple(
            url="/apis/vocabularies/autocomplete/eventtype/normal/",
        ),
    )

    def related_work_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            EventWorkRelation,
        )
        qs = qs.filter(
            eventwork_set__related_work__name__icontains=value.value,
            eventwork_set__relation_type__in=rels,
        )
        return qs

    def related_person_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            EventWorkRelation,
        )
        qs = qs.filter(
            personevent_set__related_person__name__icontains=value.value,
            personevent_set__relation_type__in=rels,
        )
        return qs

    def related_place_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PlaceEventRelation,
        )
        qs = qs.filter(
            placeevent_set__related_place__name__icontains=value.value,
            placeevent_set__relation_type__in=rels,
        )
        return qs


class EventFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(EventFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.form_tag = False
        self.layout = Layout(
            BS5Accordion(
                AccordionGroup(
                    "Eigenschaften",
                    "name",
                    "kind",
                    "year_of_creation",
                    css_id="more",
                ),
                AccordionGroup(
                    "Beziehungen",
                    "related_with_person",
                    "related_with_place",
                    "related_with_work",
                    css_id="admin_search",
                ),
            )
        )


class EventTable(tables.Table):
    id = tables.LinkColumn(verbose_name="ID")
    name = tables.columns.Column(verbose_name="Titel")
    label_set = tables.ManyToManyColumn(verbose_name="Labels")
    placeevent_set = tables.ManyToManyColumn(
        verbose_name="veranstaltet in",
        transform=lambda x: x.related_place,
        filter=lambda qs: qs.filter(
            relation_type__in=get_child_classes(
                [1202, 1369],
                PlaceEventRelation,
            )
        ),  # ToDo: don't hardcode the realtion type id here
    )

    class Meta:
        model = Event
        sequence = ("id", "name", "start_date", "placeevent_set")
        attrs = {"class": "table table-responsive table-hover"}


class EventListView(GenericListView):
    model = Event
    filter_class = EventListFilter
    formhelper_class = EventFilterFormHelper
    table_class = EventTable
    init_columns = ["id", "name", "start_date", "kind", "placeevent_set"]
    exclude_columns = excluded_cols
    enable_merge = False
    template_name = "apis_entities/list_view.html"
    verbose_name = "Ereignisse"
    help_text = "Ereignisse help text"
    icon = "bi bi-calendar3 apis-event big-icons"
