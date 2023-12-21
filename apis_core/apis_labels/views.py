from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

from .models import Label


@login_required
def delete_label(request, label_id):
    instance = Label.objects.get(id=label_id)
    label = f"{instance}"
    instance.delete()
    return HttpResponse(f"<small>gelöschtes Label: {label}</small> ")
