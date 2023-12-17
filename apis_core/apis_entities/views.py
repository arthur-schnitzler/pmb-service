from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.template.loader import select_template
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import DeleteView
from django_tables2 import RequestConfig
import importlib

from apis_core.apis_entities.models import AbstractEntity
from apis_core.apis_labels.models import Label
from apis_core.apis_relations.models import AbstractRelation
from apis_core.apis_relations.tables import get_generic_relations_table, LabelTableEdit
from .forms import get_entities_form, FullTextForm


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
        form_text = FullTextForm(request.POST, entity=entity.title())
        if form.is_valid() and form_text.is_valid():
            entity_2 = form.save()
            form_text.save(entity_2)
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
                "form_text": form_text,
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
class GenericEntitiesCreateStanbolView(View):
    def post(self, request, *args, **kwargs):
        entity = kwargs["entity"]
        ent_merge_pk = kwargs.get("ent_merge_pk", False)
        if ent_merge_pk:
            form = GenericEntitiesStanbolForm(
                entity, request.POST, ent_merge_pk=ent_merge_pk
            )
        else:
            form = GenericEntitiesStanbolForm(entity, request.POST)
        # form = form(request.POST)
        if form.is_valid():
            entity_2 = form.save()
            if ent_merge_pk:
                entity_2.merge_with(int(ent_merge_pk))
            return redirect(
                reverse(
                    "apis:apis_entities:generic_entities_edit_view",
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
                    request=request, context={"permissions": permissions, "form": form}
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
        self.success_url = reverse(
            "apis_core:apis_entities:generic_entities_list", kwargs={"entity": entity}
        )
        return super(GenericEntitiesDeleteView, self).dispatch(request, *args, **kwargs)
