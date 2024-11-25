import django_filters
from django.core.exceptions import FieldDoesNotExist
from django.db.models import CharField, Q
import django_filters.widgets

from network.models import Edge


def safe_int_conversion(value):
    try:
        return int(value)
    except ValueError:
        pass


class EdgeListFilter(django_filters.FilterSet):

    node = django_filters.CharFilter(
        field_name="source_label",
        method="nodes_icontains_filter",
        label="Quell- oder Zielknoten",
        help_text="Sucht im Label des Ziel, oder des Quellknotens",
    )
    node_id = django_filters.BaseInFilter(
        field_name="source_id",
        method="nodes_id_filter",
        label="IDs eines oder mehrerer Quell- oder Zielknoten",
        help_text="IDs eines oder mehrerer Quell- oder Zielknoten, z.B. '2121,10815'",
        widget=django_filters.widgets.CSVWidget(),
    )
    edge_label = django_filters.AllValuesMultipleFilter()

    class Meta:
        model = Edge
        fields = "__all__"

    def nodes_icontains_filter(self, queryset, name, value):
        return queryset.filter(
            Q(source_label__icontains=value) | Q(target_label__icontains=value)
        )

    def nodes_id_filter(self, queryset, name, value):
        sane_values = [safe_int_conversion(x) for x in value]
        return queryset.filter(
            Q(source_id__in=sane_values) | Q(target_id__in=sane_values)
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, filter_obj in self.filters.items():
            try:
                model_field = self.Meta.model._meta.get_field(field_name)
                self.filters[field_name].label = model_field.verbose_name
                self.filters[field_name].help_text = model_field.help_text
            except FieldDoesNotExist:
                continue
            if isinstance(model_field, CharField) and not field_name == "edge_label":
                if (
                    model_field.choices
                ):  # Keep the default filter logic for choice fields
                    continue
                else:
                    self.filters[field_name] = django_filters.CharFilter(
                        field_name=field_name,
                        lookup_expr="icontains",
                        help_text=model_field.help_text,
                        label=model_field.verbose_name,
                    )
