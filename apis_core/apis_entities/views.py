# -*- coding: utf-8 -*-
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.urls import reverse_lazy
from apis_core.apis_metainfo.models import Uri, UriCandidate, Text
from apis_core.apis_relations.models import AbstractRelation
from apis_core.helper_functions.RDFParser import RDFParser
from apis_core.helper_functions.stanbolQueries import retrieve_obj
from apis_core.helper_functions.utils import (
    access_for_all_function,
)

from .forms import (
    NetworkVizFilterForm,
    PersonResolveUriForm,
)
from .models import Place


###########################################################################
############################################################################
#
#   Helper Functions
#
############################################################################
############################################################################


@user_passes_test(access_for_all_function)
def set_session_variables(request):
    ann_proj_pk = request.GET.get("project", None)
    types = request.GET.getlist("types", None)
    users_show = request.GET.getlist("users_show", None)
    edit_views = request.GET.get("edit_views", False)
    if types:
        request.session["entity_types_highlighter"] = types
    if users_show:
        request.session["users_show_highlighter"] = users_show
    if ann_proj_pk:
        request.session["annotation_project"] = ann_proj_pk
    if edit_views:
        if edit_views != "false":
            request.session["edit_views"] = True
    return request


@user_passes_test(access_for_all_function)
def get_highlighted_texts(request, instance):
    if "apis_highlighter" in settings.INSTALLED_APPS:
        set_ann_proj = request.session.get("annotation_project", 1)
        entity_types_highlighter = request.session.get("entity_types_highlighter", None)
        users_show = request.session.get("users_show_highlighter", None)
        object_texts = [
            {
                "text": highlight_text_new(
                    x,
                    set_ann_proj=set_ann_proj,
                    types=entity_types_highlighter,
                    users_show=users_show,
                )[0].strip(),
                "id": x.pk,
                "kind": x.kind,
            }
            for x in Text.objects.filter(tempentityclass=instance)
        ]
        ann_proj_form = SelectAnnotationProject(
            set_ann_proj=set_ann_proj,
            entity_types_highlighter=entity_types_highlighter,
            users_show_highlighter=users_show,
        )
        return object_texts, ann_proj_form
    else:
        object_texts = [
            {"text": x.text, "id": x.pk, "kind": x.kind}
            for x in Text.objects.filter(tempentityclass=instance)
        ]
        return object_texts, False


############################################################################
############################################################################
#
#   OtherViews
#
############################################################################
############################################################################


@user_passes_test(access_for_all_function)
def getGeoJson(request):
    """Used to retrieve GeoJsons for single objects"""
    # if request.is_ajax():
    pk_obj = request.GET.get("object_id")
    instance = get_object_or_404(Place, pk=pk_obj)
    uria = Uri.objects.filter(entity=instance)
    urib = UriCandidate.objects.filter(entity=instance)
    if urib.count() > 0:
        uric = urib
    elif uria.count() > 0:
        uric = uria
        add_info = ""
    lst_json = []
    if uric.count() > 0 and not instance.status.startswith("distinct"):
        for x in uric:
            o = retrieve_obj(x.uri)
            if o:
                url_r = reverse_lazy(
                    "apis:apis_entities:resolve_ambigue_place",
                    kwargs={
                        "pk": str(instance.pk),
                        "uri": o["representation"]["id"][7:],
                    },
                )
                select_text = "<a href='{}'>Select this URI</a>".format(url_r)
                try:
                    add_info = "<b>Confidence:</b> {}<br/><b>Feature:</b> <a href='{}'>{}</a>".format(
                        x.confidence, x.uri, x.uri
                    )
                except:
                    add_info = "<b>Confidence:</b>no value provided <br/><b>Feature:</b> <a href='{}'>{}</a>".format(
                        x.uri, x.uri
                    )
                r = {
                    "geometry": {
                        "type": "Point",
                        "coordinates": [
                            float(
                                o["representation"][
                                    "http://www.w3.org/2003/01/geo/wgs84_pos#long"
                                ][0]["value"]
                            ),
                            float(
                                o["representation"][
                                    "http://www.w3.org/2003/01/geo/wgs84_pos#lat"
                                ][0]["value"]
                            ),
                        ],
                    },
                    "type": "Feature",
                    "properties": {
                        "popupContent": "<b>ÖBL name:</b> %s<br/><b>Geonames:</b> %s<br/>%s<br/>%s"
                        % (
                            instance.name,
                            o["representation"][
                                "http://www.geonames.org/ontology#name"
                            ][0]["value"],
                            select_text,
                            add_info,
                        )
                    },
                    "id": x.pk,
                }
                lst_json.append(r)
    elif instance.lat is not None and instance.lng is not None:
        r = {
            "geometry": {"type": "Point", "coordinates": [instance.lng, instance.lat]},
            "type": "Feature",
            "properties": {"popupContent": "<b>Name:</b> %s<br/>" % (instance.name)},
            "id": instance.pk,
        }
        lst_json.append(r)

    return HttpResponse(json.dumps(lst_json), content_type="application/json")


@user_passes_test(access_for_all_function)
def getGeoJsonList(request):
    """Used to retrieve a list of GeoJsons. To generate the list the kind of connection
    and the connected entity is needed"""
    relation = AbstractRelation.get_relation_class_of_name(request.GET.get("relation"))
    # relation_type = request.GET.get("relation_type")
    objects = relation.objects.filter(related_place__status="distinct").select_related(
        "related_person", "related_place", "relation_type"
    )
    lst_json = []
    for x in objects:
        pers_url = x.related_person.get_absolute_url()
        place_url = x.related_place.get_absolute_url()
        r = {
            "geometry": {
                "type": "Point",
                "coordinates": [x.related_place.lng, x.related_place.lat],
            },
            "type": "Feature",
            "relation_type": x.relation_type.name,
            "properties": {
                "popupContent": "<b>Person:</b> <a href='%s'>%s</a><br/><b>Connection:</b> %s<br/><b>Place:</b> <a href='%s'>%s</a>"
                % (
                    pers_url,
                    x.related_person,
                    x.relation_type,
                    place_url,
                    x.related_place,
                )
            },
            "id": x.pk,
        }
        lst_json.append(r)
    return HttpResponse(json.dumps(lst_json), content_type="application/json")


@user_passes_test(access_for_all_function)
def getNetJsonList(request):
    """Used to retrieve a Json to draw a network"""
    relation = AbstractRelation.get_relation_class_of_name("PersonPlace")
    objects = relation.objects.filter(related_place__status="distinct")
    nodes = dict()
    edges = []

    for x in objects:
        if x.related_place.pk not in nodes.keys():
            place_url = reverse_lazy(
                "apis:apis_entities:place_edit", kwargs={"pk": str(x.related_place.pk)}
            )
            tt = (
                "<div class='arrow'></div>\
            <div class='sigma-tooltip-header'>%s</div>\
            <div class='sigma-tooltip-body'>\
            <table>\
                <tr><th>Type</th> <td>%s</td></tr>\
                <tr><th>Entity</th> <td><a href='%s'>Link</a></td></tr>\
            </table>\
            </div>"
                % (x.related_place.name, "place", place_url)
            )
            nodes[x.related_place.pk] = {
                "type": "place",
                "label": x.related_place.name,
                "id": str(x.related_place.pk),
                "tooltip": tt,
            }
        if x.related_person.pk not in nodes.keys():
            pers_url = reverse_lazy(
                "apis:apis_entities:person_edit",
                kwargs={"pk": str(x.related_person.pk)},
            )
            tt = (
                "<div class='arrow'></div>\
            <div class='sigma-tooltip-header'>%s</div>\
            <div class='sigma-tooltip-body'>\
            <table>\
                <tr><th>Type</th> <td>%s</td></tr>\
                <tr><th>Entity</th> <td><a href='%s'>Link</a></td></tr>\
            </table>\
            </div>"
                % (str(x.related_person), "person", pers_url)
            )
            nodes[x.related_person.pk] = {
                "type": "person",
                "label": str(x.related_person),
                "id": str(x.related_person.pk),
                "tooltip": tt,
            }
        edges.append(
            {
                "source": x.related_person.pk,
                "target": x.related_place.pk,
                "kind": x.relation_type.name,
                "id": str(x.pk),
            }
        )
    lst_json = {"edges": edges, "nodes": [nodes[x] for x in nodes.keys()]}

    return HttpResponse(json.dumps(lst_json), content_type="application/json")


@user_passes_test(access_for_all_function)
def getNetJsonListInstitution(request):
    """Used to retrieve a Json to draw a network"""
    relation = AbstractRelation.get_relation_class_of_name("PersonInstitution")
    objects = relation.objects.all()
    nodes = dict()
    edges = []

    for x in objects:
        if x.related_institution.pk not in nodes.keys():
            inst_url = reverse_lazy(
                "apis:apis_entities:institution_edit",
                kwargs={"pk": str(x.related_institution.pk)},
            )
            tt = (
                "<div class='arrow'></div>\
            <div class='sigma-tooltip-header'>%s</div>\
            <div class='sigma-tooltip-body'>\
            <table>\
                <tr><th>Type</th> <td>%s</td></tr>\
                <tr><th>Entity</th> <td><a href='%s'>Link</a></td></tr>\
            </table>\
            </div>"
                % (x.related_institution.name, "institution", inst_url)
            )
            nodes[x.related_institution.pk] = {
                "type": "institution",
                "label": x.related_institution.name,
                "id": str(x.related_institution.pk),
                "tooltip": tt,
            }
        if x.related_person.pk not in nodes.keys():
            pers_url = reverse_lazy(
                "apis:apis_entities:person_edit",
                kwargs={"pk": str(x.related_person.pk)},
            )
            tt = (
                "<div class='arrow'></div>\
            <div class='sigma-tooltip-header'>%s</div>\
            <div class='sigma-tooltip-body'>\
            <table>\
                <tr><th>Type</th> <td>%s</td></tr>\
                <tr><th>Entity</th> <td><a href='%s'>Link</a></td></tr>\
            </table>\
            </div>"
                % (str(x.related_person), "person", pers_url)
            )
            nodes[x.related_person.pk] = {
                "type": "person",
                "label": str(x.related_person),
                "id": str(x.related_person.pk),
                "tooltip": tt,
            }
        edges.append(
            {
                "source": x.related_person.pk,
                "target": x.related_institution.pk,
                "kind": x.relation_type.name,
                "id": str(x.pk),
            }
        )
    lst_json = {"edges": edges, "nodes": [nodes[x] for x in nodes.keys()]}

    return HttpResponse(json.dumps(lst_json), content_type="application/json")


@login_required
def resolve_ambigue_place(request, pk, uri):
    """Only used to resolve place names."""
    uri = "http://" + uri
    entity = Place.objects.get(pk=pk)
    pl_n = RDFParser(uri, kind="Place")
    pl_n.create_objct()
    pl_n_1 = pl_n.save()
    pl_n_1 = pl_n.merge(entity)
    url = pl_n_1.get_absolute_url()
    if pl_n.created:
        pl_n_1.status = "distinct (manually resolved)"
        pl_n_1.save()
    UriCandidate.objects.filter(entity=entity).delete()

    return HttpResponseRedirect(url)


@login_required
def resolve_ambigue_person(request):
    if request.method == "POST":
        form = PersonResolveUriForm(request.POST)
    if form.is_valid():
        pers = form.save()
        return redirect(
            reverse("apis:apis_entities:person_edit", kwargs={"pk": pers.pk})
        )


############################################################################
############################################################################
#
#   VisualizationViews
#
############################################################################
############################################################################


@user_passes_test(access_for_all_function)
def birth_death_map(request):
    return render(request, "apis:apis_entities/map_list.html")


@user_passes_test(access_for_all_function)
def pers_place_netw(request):
    return render(request, "apis:apis_entities/network.html")


@user_passes_test(access_for_all_function)
def pers_inst_netw(request):
    return render(request, "apis:apis_entities/network_institution.html")


@user_passes_test(access_for_all_function)
def generic_network_viz(request):
    if request.method == "GET":
        form = NetworkVizFilterForm()
        return render(
            request,
            "apis:apis_entities/generic_network_visualization.html",
            {"form": form},
        )
