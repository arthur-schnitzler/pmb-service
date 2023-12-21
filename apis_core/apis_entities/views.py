import importlib

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import select_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView
from django_tables2 import RequestConfig
from icecream import ic

from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import Uri
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_relations.tables import LabelTableEdit, get_generic_relations_table

from .forms import MergeForm, get_entities_form


@method_decorator(login_required, name="dispatch")
class GenericEntitiesEditView(View):
    def get(self, request, *args, **kwargs):
        entity = kwargs["entity"]
        pk = kwargs["pk"]
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
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
                relation_class=rel, entity_instance=instance, detail=False
            )
            title_card = ""
            if match[0] == match[1]:
                title_card = entity.title()
                dict_1 = {"related_" + entity.lower() + "a": instance}
                dict_2 = {"related_" + entity.lower() + "b": instance}
                objects = rel.objects.filter(Q(**dict_1) | Q(**dict_2))
            else:
                if match[0].lower() == entity.lower():
                    title_card = match[1].title()
                else:
                    title_card = match[0].title()
                dict_1 = {"related_" + entity.lower(): instance}
                objects = rel.objects.filter(**dict_1)
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
        form = get_entities_form(entity.title())
        form = form(instance=instance)
        form_merge_with = MergeForm(entity, ent_merge_pk=pk)
        object_labels = Label.objects.filter(temp_entity=instance)
        tb_label = LabelTableEdit(data=object_labels, prefix=entity.title()[:2] + "L-")
        tb_label_open = request.GET.get("PL-page", None)
        side_bar.append(("Label", tb_label, "PersonLabel", tb_label_open))
        RequestConfig(request, paginate={"per_page": 10}).configure(tb_label)
        template = select_template(
            [
                "apis_entities/edit_view.html",
            ]
        )
        context = {
            "entity_type": entity,
            "form": form,
            "form_merge_with": form_merge_with,
            "instance": instance,
            "right_card": side_bar,
        }
        return HttpResponse(template.render(request=request, context=context))

    def post(self, request, *args, **kwargs):
        entity = kwargs["entity"]
        pk = kwargs["pk"]
        entity_model = AbstractEntity.get_entity_class_of_name(entity)
        instance = get_object_or_404(entity_model, pk=pk)
        form = get_entities_form(entity.title())
        form = form(request.POST, instance=instance)
        if form.is_valid():
            entity_2 = form.save()
            return redirect(
                reverse(
                    "apis:apis_entities:generic_entities_edit_view",
                    kwargs={"pk": pk, "entity": entity},
                )
            )
        else:
            template = select_template(
                [
                    "apis_entities/{}_create_generic.html".format(entity),
                    "apis_entities/create_view.html",
                ]
            )
            context = {
                "form": form,
                "entity_type": entity,
                "instance": instance,
            }
            if entity.lower() != "place":
                return TemplateResponse(request, template, context=context)
            return HttpResponse(template.render(request=request, context=context))


@method_decorator(login_required, name="dispatch")
class GenericEntitiesCreateView(View):
    def get(self, request, *args, **kwargs):
        entity = kwargs["entity"]
        form = get_entities_form(entity.title())
        form = form()
        template = select_template(
            [
                "apis_entities/{}_create_generic.html".format(entity),
                "apis_entities/create_view.html",
            ]
        )
        return HttpResponse(
            template.render(
                request=request,
                context={
                    "entity_type": entity,
                    "form": form,
                },
            )
        )

    def post(self, request, *args, **kwargs):
        entity = kwargs["entity"]
        form = get_entities_form(entity.title())
        form = form(request.POST)
        if form.is_valid():
            entity_2 = form.save()
            return redirect(
                reverse(
                    "apis:apis_entities:generic_entities_detail_view",
                    kwargs={"pk": entity_2.pk, "entity": entity},
                )
            )
        else:
            permissions = {
                "create": request.user.has_perm("apis_entities.add_{}".format(entity))
            }
            template = select_template(
                [
                    "apis_entities/{}_create_generic.html".format(entity),
                    "apis_entities/create_view.html",
                ]
            )
            return HttpResponse(
                template.render(
                    request=request,
                    context={
                        "permissions": permissions,
                        "form": form,
                    },
                )
            )


@method_decorator(login_required, name="dispatch")
class GenericEntitiesDeleteView(DeleteView):
    model = importlib.import_module("apis_core.apis_metainfo.models").TempEntityClass
    template_name = getattr(
        settings, "APIS_DELETE_VIEW_TEMPLATE", "apis_entities/confirm_delete.html"
    )

    def dispatch(self, request, *args, **kwargs):
        entity = kwargs["entity"]
        self.success_url = reverse(f"apis_core:apis_entities:{entity}_list_view")
        return super(GenericEntitiesDeleteView, self).dispatch(request, *args, **kwargs)


@method_decorator(login_required, name="dispatch")
class MergeEntitiesView(View):
    def post(self, request, *args, **kwargs):
        entity = kwargs["entity"]
        ent_merge_pk = kwargs.get("ent_merge_pk", False)
        form = MergeForm(entity, request.POST, ent_merge_pk=ent_merge_pk)
        if form.is_valid():
            uri = form.data["entity"]
            if ent_merge_pk:
                uri_obj = Uri.objects.get(uri=uri)
                target = uri_obj.entity
                entity_model_class = ContentType.objects.get(
                    app_label="apis_entities", model__iexact=entity
                ).model_class()
                target_obj = entity_model_class.objects.get(id=target.id)
                target_obj.merge_with(int(ent_merge_pk))
            return redirect(
                reverse(
                    "apis:apis_entities:generic_entities_detail_view",
                    kwargs={"pk": target.pk, "entity": entity},
                )
            )
        else:
            return redirect(
                reverse(
                    "apis:apis_entities:generic_entities_edit_view",
                    kwargs={"pk": ent_merge_pk, "entity": entity},
                )
            )
