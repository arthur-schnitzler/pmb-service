import django_filters
import django_tables2 as tables
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import AccordionGroup
from crispy_bootstrap5.bootstrap5 import BS5Accordion

from dal import autocomplete

from browsing.browsing_utils import GenericListView

from apis_core.apis_entities.models import Event

from apis_core.apis_vocabularies.models import (
    PlaceEventRelation,
    InstitutionEventRelation,
    PersonEventRelation,
    EventEventRelation,
    EventType,
)
from apis_core.helper_functions.utils import get_child_classes

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
    (f"{x.id}", f"{x} (ID: {x.id})") for x in PlaceEventRelation.objects.all()
]
EVENT_EVENT_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in EventEventRelation.objects.all()
]
EVENT_INSTITUTION_RELATION_CHOICES = [
    (f"{x.id}", f"{x} (ID: {x.id})") for x in InstitutionEventRelation.objects.all()
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
        help_text="Name einer Bezugsperson und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geschaffen von'",
        method="related_person_filter",
    )
    related_with_work = django_filters.LookupChoiceFilter(
        lookup_choices=EVENT_EVENT_RELATION_CHOICES,
        label="Werk",
        help_text="Name einer Werkes und die Art des Beziehung, z.B. 'Schnitzler' und 'wurde geschaffen von'",
        method="related_work_filter",
    )
    kind = django_filters.ModelMultipleChoiceFilter(
        queryset=EventType.objects.all(),
        help_text="Art/Typ des Werkes, z.B. 'Roman'",
        label="Werktype",
        widget=autocomplete.Select2Multiple(
            url="/apis/vocabularies/autocomplete/worktype/normal/",
        ),
    )

    def related_work_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            EventEventRelation,
        )
        qs = qs.filter(
            workb_set__name__icontains=value.value, workb_relationtype_set__in=rels
        )
        return qs

    def related_person_filter(self, qs, name, value):
        rels = get_child_classes(
            [
                value.lookup_expr,
            ],
            PersonEventRelation,
        )
        qs = qs.filter(
            personwork_set__related_person__name__icontains=value.value,
            personwork_set__relation_type__in=rels,
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
                    "related_with_work",
                    css_id="admin_search",
                ),
            )
        )


class EventTable(tables.Table):
    id = tables.LinkColumn(verbose_name="ID")
    name = tables.columns.Column(verbose_name="Titel")
    label_set = tables.ManyToManyColumn(verbose_name="Labels")
    personwork_set = tables.ManyToManyColumn(
        verbose_name="AutorIn",
        transform=lambda x: x.related_person,
        filter=lambda qs: qs.filter(
            relation_type__in=get_child_classes(
                [
                    1049,
                ],
                PersonEventRelation,
            )
        ),  # ToDo: don't hardcode the realtion type id here
    )

    class Meta:
        model = Event
        sequence = ("id", "name", "personwork_set", "start_date")
        attrs = {"class": "table table-responsive table-hover"}


class EventListView(GenericListView):
    model = Event
    filter_class = EventListFilter
    formhelper_class = EventFilterFormHelper
    table_class = EventTable
    init_columns = [
        "id",
        "name",
        "start_date",
        "personwork_set",
        "kind",
    ]
    exclude_columns = excluded_cols
    enable_merge = False
    template_name = "apis_entities/list_views/list.html"
    verbose_name = "Werke"
    help_text = "Werke help text"
    icon = "bi bi-book apis-work big-icons"
