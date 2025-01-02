import csv
import json
import pandas as pd
from django.apps import apps
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView


from browsing.browsing_utils import (
    GenericListView,
)

from network.filters import EdgeListFilter
from network.forms import EdgeFilterFormHelper
from network.models import Edge
from network.tables import EdgeTable
from network.utils import get_coords, df_to_geojson_vect


class NetworkView(TemplateView):
    template_name = "network/network.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        MODELS = list(apps.all_models["apis_entities"].values())
        model_list = []
        for x in MODELS:
            try:
                item = {
                    "color": x.get_color(),
                    "icon": x.get_icon(),
                    "name": x._meta.verbose_name,
                }
            except AttributeError:
                continue
            model_list.append(item)
        context["model_list"] = model_list
        return context


class MapView(TemplateView):
    template_name = "network/map.html"


class CalenderView(TemplateView):
    template_name = "network/calender.html"


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


def edges_as_calender(request):
    query_params = request.GET
    queryset = Edge.objects.filter().exclude(start_date__isnull=True)
    values_list = [x.name for x in Edge._meta.get_fields()]
    qs = EdgeListFilter(request.GET, queryset=queryset).qs
    items = list(qs.values_list(*values_list))
    df = pd.DataFrame(list(items), columns=values_list)

    def map_date_to_lat_lng(date_str):
        try:
            date = pd.to_datetime(date_str)
            year = date.year
            day_of_year = date.dayofyear
            # Map year to latitude (-90 to 90)
            latitude = (year % 180) - 90
            # Map day of year to longitude (-180 to 180)
            longitude = (day_of_year % 360) - 180
            return latitude, longitude
        except Exception as e: # noqa
            return None, None

    df["latitude"], df["longitude"] = zip(*df["start_date"].map(map_date_to_lat_lng))
    df["label"] = df[["source_label", "edge_label", "target_label"]].agg(
        " ".join, axis=1
    )
    items = df.apply(
        lambda row: {
            "date": str(row["start_date"]),
            # "label": row["label"],
            "edge_label": row["edge_label"],
            "kind": row["edge_kind"],
            "latitude": row["latitude"],
            "longitude": row["longitude"],
            "id": row["edge_id"],
        },
        axis=1,
    ).tolist()
    data = {}
    data = {"metadata": {}, "events": items}
    data["metadata"] = {"number of objects": len(items)}
    data["metadata"]["query_params"] = [
        {key: value} for key, value in query_params.items()
    ]
    data["metadata"]["start_date"] = str(df["start_date"].min())
    data["metadata"]["end_date"] = str(df["start_date"].max())
    return JsonResponse(data=data)


def edges_as_geojson(request):
    query_params = request.GET
    values_list = [x.name for x in Edge._meta.get_fields()]
    qs = (
        Edge.objects.filter(edge_kind__icontains="place")
        .exclude(source_lat__isnull=True, target_lat__isnull=True)
        .exclude(edge_kind="placeplace")
    )
    items = EdgeListFilter(request.GET, queryset=qs).qs.values_list(*values_list)
    df = pd.DataFrame(list(items), columns=values_list)
    try:
        df["label"] = df[["source_label", "edge_label", "target_label"]].agg(
            " ".join, axis=1
        )
    except ValueError:
        return JsonResponse(data={})
    df[["latitude", "longitude"]] = df.apply(
        lambda row: pd.Series(get_coords(row)), axis=1
    )
    data = df_to_geojson_vect(df, ["label", "edge_id"])
    data["metadata"] = {"number of objects": len(df)}
    data["metadata"]["query_params"] = [
        {key: value} for key, value in query_params.items()
    ]
    return JsonResponse(data=data)


def network_data(request):
    query_params = request.GET
    values_list = [x.name for x in Edge._meta.get_fields()]
    qs = EdgeListFilter(request.GET, queryset=Edge.objects.all()).qs
    items = list(qs.values_list(*values_list))
    df = pd.DataFrame(items, columns=values_list)
    response = HttpResponse(
        content_type="text/csv",
    )
    format = request.GET.get("format", "csv")
    if format not in ["csv", "json", "cosmograph"]:
        format = "csv"
    if format == "csv":
        response = HttpResponse(
            content_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="relations.csv"'},
        )
        df.to_csv(response, index=False, quoting=csv.QUOTE_ALL, quotechar='"')
        return response
    elif format == "json":
        df = df.set_index("edge_id")
        df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
        df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")
        df["start_date"] = df["start_date"].dt.strftime("%Y-%m-%d").fillna("")
        df["end_date"] = df["end_date"].dt.strftime("%Y-%m-%d").fillna("")
        out = df.to_json(orient="index", force_ascii=False)
        response = JsonResponse(json.loads(out))
        return response
    elif format == "cosmograph":
        data = {}
        edge_data = df.apply(
            lambda row: {
                "id": row["edge_id"],
                "s": row["source_id"],
                "t": row["target_id"],
                "start": str(row["start_date"]),
                "end": str(row["end_date"]),
            },
            axis=1,
        ).tolist()
        data["edges"] = edge_data
        source_nodes = df[["source_label", "source_kind", "source_id"]].rename(
            columns={
                "source_label": "node_label",
                "source_kind": "node_kind",
                "source_id": "node_id",
            }
        )
        target_nodes = df[["target_label", "target_kind", "target_id"]].rename(
            columns={
                "target_label": "node_label",
                "target_kind": "node_kind",
                "target_id": "node_id",
            }
        )
        nodes = (
            pd.concat([source_nodes, target_nodes])
            .drop_duplicates()
            .reset_index(drop=True)
        )
        data["nodes"] = nodes.apply(
            lambda row: {
                "id": row["node_id"],
                "k": row["node_kind"],
                "l": row["node_label"],
            },
            axis=1,
        ).tolist()
        data["metadata"] = {
            "query_params": [{key: value} for key, value in query_params.items()]
        }
        response = JsonResponse(data)
        return response
