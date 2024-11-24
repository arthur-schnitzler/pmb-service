from browsing.browsing_utils import (
    GenericListView,
)

from network.filters import EdgeListFilter
from network.forms import EdgeFilterFormHelper
from network.models import Edge
from network.tables import EdgeTable


class EdgeListViews(GenericListView):
    model = Edge
    filter_class = EdgeListFilter
    formhelper_class = EdgeFilterFormHelper
    table_class = EdgeTable
    init_columns = [
        "source_label",
        "edge_label",
        "target_label",
        "start_date",
    ]
    enable_merge = False
    template_name = "network/list_view.html"
