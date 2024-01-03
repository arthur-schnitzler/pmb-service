from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.loader import select_template
from django.views import View
from django_tables2 import RequestConfig

from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Uri
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_relations.tables import LabelTableBase, get_generic_relations_table
from apis_core.utils import get_object_from_pk_or_uri


class GenericEntitiesDetailView(View):
    # login_url = '/accounts/login/'

    def get(self, request, *args, **kwargs):
        entity = kwargs["entity"].lower()
        pk = kwargs["pk"]
        instance = get_object_from_pk_or_uri(pk)
        if f"{instance.id}" == f"{pk}":
            pass
        else:
            return redirect(instance)
        relations = AbstractRelation.get_relation_classes_of_entity_name(
            entity_name=entity
        )
        side_bar = []
        for rel in relations:
            match = [
                rel.get_related_entity_classa().__name__.lower(),
                rel.get_related_entity_classb().__name__.lower(),
            ]
            prefix = "{}{}-".format(match[0].title()[:2], match[1].title()[:2])
            table = get_generic_relations_table(
                relation_class=rel, entity_instance=instance, detail=True
            )
            if match[0] == match[1]:
                title_card = entity.title()
                dict_1 = {"related_" + entity.lower() + "a": instance}
                dict_2 = {"related_" + entity.lower() + "b": instance}
                objects = rel.objects.filter(Q(**dict_1) | Q(**dict_2))
                if callable(getattr(objects, "filter_for_user", None)):
                    objects = objects.filter_for_user()
            else:
                if match[0].lower() == entity.lower():
                    title_card = match[1].title()
                else:
                    title_card = match[0].title()
                dict_1 = {"related_" + entity.lower(): instance}
                if "apis_highlighter" in settings.INSTALLED_APPS:
                    objects = (
                        rel.objects.filter_ann_proj(request=request)
                        .filter_for_user()
                        .filter(**dict_1)
                    )
                else:
                    objects = rel.objects.filter(**dict_1)
                    if callable(getattr(objects, "filter_for_user", None)):
                        objects = objects.filter_for_user()
            tb_object = table(data=objects, prefix=prefix)
            tb_object_open = request.GET.get(prefix + "page", None)
            RequestConfig(request, paginate={"per_page": 10}).configure(tb_object)
            side_bar.append(
                (
                    title_card,
                    tb_object,
                    "".join([x.title() for x in match]),
                    tb_object_open,
                )
            )
        object_lod = Uri.objects.filter(entity=instance)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = LabelTableBase(data=object_labels, prefix=entity.title()[:2] + "L-")
        tb_label_open = request.GET.get("PL-page", None)
        side_bar.append(("Label", tb_label, "PersonLabel", tb_label_open))
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        template = select_template(
            [
                "apis_entities/detail_views/{}_detail_generic.html".format(entity),
                "apis_entities/detail_views/entity_detail_generic.html",
            ]
        )
        try:
            no_merge_labels = [
                x for x in object_labels if not x.label_type.name.startswith("Legacy")
            ]
        except AttributeError:
            no_merge_labels = []
        context = {
            "entity_type": entity,
            "object": instance,
            "right_card": side_bar,
            "no_merge_labels": no_merge_labels,
            "object_lables": object_labels,
            "object_lod": object_lod,
        }
        return HttpResponse(template.render(request=request, context=context))
