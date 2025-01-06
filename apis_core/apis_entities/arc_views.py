import pandas as pd
from django.views.generic import TemplateView
from django.http import JsonResponse
from apis_core.apis_entities.models import Person
from apis_core.apis_entities.list_view_person import PersonListFilter

from network.utils import iso_to_lat_long


class ArcsView(TemplateView):
    template_name = "apis_entities/arcs.html"


def get_arcs_data(request):
    values_list = ["id", "name", "first_name", "start_date", "end_date"]
    query_params = request.GET
    queryset = (
        Person.objects.filter()
        .exclude(start_date__isnull=True)
        .exclude(end_date__isnull=True)
    )
    qs = PersonListFilter(query_params, queryset=queryset).qs
    items = list(qs.values_list(*values_list))
    df = pd.DataFrame(list(items), columns=values_list)
    start_date = str(df["start_date"].min())
    end_date = str(df["end_date"].max())
    df["latitude_start"], df["longitude_start"] = zip(
        *df["start_date"].map(
            lambda date: iso_to_lat_long(date, start_date=start_date, end_date=end_date)
        )
    )
    df["latitude_end"], df["longitude_end"] = zip(
        *df["end_date"].map(
            lambda date: iso_to_lat_long(date, start_date=start_date, end_date=end_date)
        )
    )
    df = df.sort_values(by="start_date")
    items = df.apply(
        lambda row: {
            "id": row["id"],
            "label": f'{row["name"]}, {row["first_name"]} ({row["start_date"]}–{row["end_date"]})',
            "from": [row["latitude_start"], row["longitude_start"]],
            "to": [row["latitude_end"], row["longitude_end"]],
        },
        axis=1,
    ).tolist()
    data = {}
    data = {"metadata": {}, "items": items}
    data["metadata"] = {"number of objects": len(items)}
    data["metadata"]["query_params"] = [
        {key: value} for key, value in query_params.items()
    ]
    data["metadata"]["start_date"] = str(df["start_date"].min())
    data["metadata"]["end_date"] = str(df["start_date"].max())

    return JsonResponse(data, safe=False)
