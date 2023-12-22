import inspect
import re

from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.http import Http404, HttpResponse
from django.template import loader

from apis_core.apis_entities.models import (
    AbstractEntity,
    Event,
    Institution,
    Person,
    Place,
    Work,
)
from apis_core.apis_labels.models import Label
from apis_core.apis_metainfo.models import TempEntityClass, Uri
from apis_core.apis_relations import forms as relation_form_module

from .forms2 import GenericRelationForm
from .models import (
    EventEvent,
    EventWork,
    InstitutionEvent,
    InstitutionInstitution,
    InstitutionPlace,
    InstitutionWork,
    PersonEvent,
    PersonInstitution,
    PersonPerson,
    PersonPlace,
    PersonWork,
    PlaceEvent,
    PlacePlace,
    PlaceWork,
    WorkWork,
)
from .tables import LabelTableEdit

form_module_list = [relation_form_module]


def turn_form_modules_into_dict(form_module_list):
    """
    Since form classes are loaded dynamically from the respective modules and it's settings-dependent which modules
    are imported and which not, it's better to differentiate here which modules are imported close to their imports
    and then providing a dict for later extraction of the required form class.
    """

    form_class_dict = {}
    for m in form_module_list:
        for name, cls in inspect.getmembers(m, inspect.isclass):
            form_class_dict[name] = cls

    return form_class_dict


form_class_dict = turn_form_modules_into_dict(form_module_list)


############################################################################
############################################################################
#
#   Generic views for AjaxForms
#
############################################################################
############################################################################

######################################################
# test for class-ignoring _ajax_form-functions
######################################################


# Model-classes must be registered together with their ModelForm-classes
registered_forms = {
    "WorkWorkForm": [WorkWork, Work, Work],
    "EventEventForm": [EventEvent, Event, Event],
    "PersonPlaceForm": [PersonPlace, Person, Place],
    "PersonPlaceHighlighterForm": [PersonPlace, Person, Place],
    "PersonPersonForm": [PersonPerson, Person, Person],
    "PersonPersonHighlighterForm": [PersonPerson, Person, Person],
    "PersonInstitutionForm": [PersonInstitution, Person, Institution],
    "PersonEventForm": [PersonEvent, Person, Event],
    "PersonWorkForm": [PersonWork, Person, Work],
    "PersonInstitutionHighlighterForm": [PersonInstitution, Person, Institution],
    "PersonWorkHighlighterForm": [PersonWork, Person, Work],
    "PlaceWorkHighlighterForm": [PlaceWork, Place, Work],
    "InstitutionWorkHighlighterForm": [InstitutionWork, Institution, Work],
    "InstitutionPlaceForm": [InstitutionPlace, Institution, Place],
    "InstitutionInstitutionForm": [InstitutionInstitution, Institution, Institution],
    "InstitutionPersonForm": [PersonInstitution, Institution, Person],
    "InstitutionEventForm": [InstitutionEvent, Institution, Event],
    "InstitutionWorkForm": [InstitutionWork, Institution, Work],
    "PlaceEventForm": [PlaceEvent, Place, Event],
    "PlaceWorkForm": [PlaceWork, Place, Work],
    "PlacePlaceForm": [PlacePlace, Place, Place],
    "EventWorkForm": [EventWork, Event, Work],
    "InstitutionLabelForm": [Label, Institution, Label],
    "PersonLabelForm": [Label, Person, Label],
    "EventLabelForm": [Label, Event, Label],
    "PersonResolveUriForm": [Uri, Person, Uri],
    "SundayHighlighterForm": [],
    "AddRelationHighlighterPersonForm": [],
    #'PlaceHighlighterForm': [Annotation, ],
    #'PersonHighlighterForm': [Annotation, ]
}


@login_required
def get_form_ajax(request):
    """Returns forms rendered in html"""

    FormName = request.POST.get("FormName")
    SiteID = request.POST.get("SiteID")
    print(SiteID)
    ButtonText = request.POST.get("ButtonText")
    ObjectID = request.POST.get("ObjectID")
    entity_type_str = request.POST.get("entity_type")
    relation_name = FormName.replace("Form", "")
    form_match = re.match(r"([A-Z][a-z]+)([A-Z][a-z]+)(Highlighter)?Form", FormName)
    form_match2 = re.match(r"([A-Z][a-z]+)(Highlighter)?Form", FormName)
    if FormName and form_match:
        entity_type_v1 = ContentType.objects.filter(
            model="{}{}".format(
                form_match.group(1).lower(), form_match.group(2)
            ).lower(),
            app_label="apis_relations",
        )
        entity_type_v2 = ContentType.objects.none()
    elif FormName and form_match2:
        entity_type_v2 = ContentType.objects.filter(
            model="{}".format(form_match.group(1).lower(), app_label="apis_entities")
        )
        entity_type_v1 = ContentType.objects.none()
    else:
        entity_type_v1 = ContentType.objects.none()
        entity_type_v2 = ContentType.objects.none()
    if ObjectID == "false" or ObjectID is None or ObjectID == "None":
        ObjectID = False
        form_dict = {"entity_type": entity_type_str}
    elif entity_type_v1.count() > 0:
        d = entity_type_v1[0].model_class().objects.get(pk=ObjectID)
        form_dict = {"instance": d, "siteID": SiteID, "entity_type": entity_type_str}
    elif entity_type_v2.count() > 0:
        d = entity_type_v2[0].model_class().objects.get(pk=ObjectID)
        form_dict = {"instance": d, "siteID": SiteID, "entity_type": entity_type_str}
    else:
        if FormName not in registered_forms.keys():
            raise Http404
        d = registered_forms[FormName][0].objects.get(pk=ObjectID)
        form_dict = {"instance": d, "siteID": SiteID, "entity_type": entity_type_str}
    if entity_type_v1.count() > 0:
        form_dict["relation_form"] = "{}{}".format(
            form_match.group(1), form_match.group(2)
        )
        form = GenericRelationForm(**form_dict)
    else:
        form_class = form_class_dict[FormName]
        form = form_class(**form_dict)
    template = loader.get_template("apis_relations/_ajax_form.html")
    form_context = {
        "entity_type": entity_type_str,
        "form": form,
        "form_name": FormName,
        "relation_name": relation_name,
        "url2": "save_ajax_" + FormName,
        "button_text": ButtonText,
        "ObjectID": ObjectID,
        "SiteID": SiteID,
    }

    return HttpResponse(template.render(form_context, request))


@login_required
def save_ajax_form(request, entity_type, kind_form, SiteID, ObjectID=False):
    """Tests validity and saves AjaxForms, returns them when validity test fails"""
    if kind_form not in registered_forms.keys():
        raise Http404
    entity_type_str = entity_type
    entity_type = AbstractEntity.get_entity_class_of_name(entity_type)
    object_id = ObjectID
    form_match = re.match(r"([A-Z][a-z]+)([A-Z][a-z]+)?(Highlighter)?Form", kind_form)
    form_dict = {"data": request.POST, "entity_type": entity_type, "request": request}

    test_form_relations = ContentType.objects.filter(
        model="{}{}".format(form_match.group(1).lower(), form_match.group(2)).lower(),
        app_label="apis_relations",
    )
    tab = re.match(r"(.*)Form", kind_form).group(1)
    if test_form_relations.count() > 0:
        relation_form = test_form_relations[0].model_class()
        form_dict["relation_form"] = relation_form
        form = GenericRelationForm(**form_dict)
    else:
        form_class = form_class_dict[kind_form]
        form = form_class(**form_dict)
    if form.is_valid():
        site_instance = entity_type.objects.get(pk=SiteID)

        if object_id:
            form.save(instance=object_id, site_instance=site_instance)
        else:
            form.save(site_instance=site_instance)
        if test_form_relations.count() > 0:
            table_html = form.get_html_table(
                entity_type_str, request, site_instance, form_match
            )
        if tab == "PersonLabel":
            table_html = LabelTableEdit(
                data=site_instance.label_set.all(), prefix="PL-"
            )
        elif tab == "InstitutionLabel":
            table_html = LabelTableEdit(
                data=site_instance.label_set.all(), prefix="IL-"
            )
        if table_html:
            table_html2 = table_html.as_html(request)
        else:
            table_html2 = None
        return HttpResponse(table_html2)
    else:
        template = loader.get_template("apis_relations/_ajax_form.html")
        return HttpResponse(template.render({"form": form}, request))


@login_required
def delete_relation_view(request, relation_id):
    instance = TempEntityClass.objects.get(id=relation_id)
    instance.delete()
    return HttpResponse(f"<small>gelöschte Verbindung: {relation_id}</small> ")
