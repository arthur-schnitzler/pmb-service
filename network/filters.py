import django_filters
from django.db.models import CharField

from network.models import Edge


class EdgeListFilter(django_filters.FilterSet):

    class Meta:
        model = Edge
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, filter_obj in self.filters.items():
            model_field = self.Meta.model._meta.get_field(field_name)
            self.filters[field_name].label = model_field.verbose_name
            self.filters[field_name].help_text = model_field.help_text

            if isinstance(model_field, CharField):
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
