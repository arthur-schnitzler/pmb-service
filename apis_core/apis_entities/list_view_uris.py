import django_filters
import django_tables2 as tables
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import AccordionGroup
from crispy_bootstrap5.bootstrap5 import BS5Accordion

from browsing.browsing_utils import GenericListView

from apis_core.apis_metainfo.models import Uri


class UriTable(tables.Table):
    id = tables.LinkColumn(verbose_name="ID")
    uri = tables.columns.Column(verbose_name="URI")

    class Meta:
        model = Uri
        sequence = ("id", "uri", "domain")
        attrs = {"class": "table table-responsive table-hover"}


class UriFilterFormHelper(FormHelper):
    def __init__(self, *args, **kwargs):
        super(UriFilterFormHelper, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.form_class = "genericFilterForm"
        self.form_method = "GET"
        self.form_tag = False
        self.layout = Layout(
            BS5Accordion(
                AccordionGroup(
                    "Eigenschaften",
                    "uri",
                    "domain",
                    css_id="more",
                )
            )
        )


class UriListFilter(django_filters.FilterSet):
    uri = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Uri",
        help_text="eingegebene Zeichenkette muss in der URI enthalten sein",
    )
    domain = django_filters.CharFilter(
        lookup_expr="icontains",
        label="Domain",
        help_text="eingegebene Zeichenkette muss in der Domain enthalten sein",
    )

class UriListView(GenericListView):
    model = Uri
    filter_class = UriListFilter
    formhelper_class = UriFilterFormHelper
    table_class = UriTable
    init_columns = [
        "id",
        "uri",
        "domain",
    ]
    exclude_columns = []
    enable_merge = False
    template_name = "apis_entities/list_views/list.html"
    verbose_name = "Uris"
    help_text = "Uris help text"
    icon = "bi bi-link-45deg apis-uri big-icons"
