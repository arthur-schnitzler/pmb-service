import pandas as pd
import json
from django.http import HttpResponse, JsonResponse


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


def network_data(request):
    values_list = [x.name for x in Edge._meta.get_fields()]
    qs = EdgeListFilter(request.GET, queryset=Edge.objects.all()).qs
    items = list(qs.values_list(*values_list))
    df = pd.DataFrame(items, columns=values_list)
    response = HttpResponse(
        content_type="text/csv",
    )
    format = request.GET.get("format", "csv")
    if format not in ["csv", "json"]:
        format = "csv"
    if format == "csv":
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="relations.csv"'},
        )
        df.to_csv(response, index=False)
    else:
        df = df.set_index("edge_id")
        df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
        df["start_date"] = df["start_date"].dt.strftime("%Y-%m-%d").fillna("")
        df["end_date"] = df["end_date"].dt.strftime("%Y-%m-%d").fillna("")
        out = df.to_json(orient="index", force_ascii=False)
        response = JsonResponse(json.loads(out))
    return response
