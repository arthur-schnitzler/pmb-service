import pandas as pd
from django.http import HttpResponseNotFound

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse


@login_required
def dl_vocabs_as_csv(request, model_name):
    kwargs = {"app_label": "apis_vocabularies", "entity": model_name}
    try:
        model = ContentType.objects.get(
            app_label=kwargs.get("app_label"), model=kwargs.get("entity").lower()
        ).model_class()
    except ObjectDoesNotExist:
        return HttpResponseNotFound(
            f"<h1>Error</h1><p>Es konnte keine Klasse mit dem Name <strong>{model_name}</strong> gefunden werden</p>"
        )
    data = [[x.id, x.name, x.parent_class] for x in model.objects.all()]
    columns = ["id", "name", "parent_class"]
    df = pd.DataFrame(data, columns=columns)
    filename = f"{kwargs.get('entity').lower()}.csv"
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f"attachment; filename='{filename}'"
    df.to_csv(response, index=False)

    return response


# Create your views here.
