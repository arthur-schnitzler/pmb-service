from django.conf.urls import url

from .tei_ac import TeiEntAc, TeiCompleterAc

from apis_core.apis_tei import views

app_name = 'apis_tei'

urlpatterns = [
    url(
        r'^autocomplete/(?P<entity>[a-zA-Z0-9-]+)/$',
        TeiEntAc.as_view(),
        name='generic_entities_autocomplete'
    ),
    url(
        r'^tei-completer/(?P<entity>[a-zA-Z0-9-]+)/$',
        TeiCompleterAc.as_view(),
        name='tei_completer_autocomplete'
    ),
    url(
         r'^person/<int:pk>$',
        views.person_as_tei,
        name='person_as_tei'
    ),
    url(
        r'^place/<int:pk>$',
        views.place_as_tei,
        name='place_as_tei'
    ),
    url(
        r'^org/<int:pk>$',
        views.org_as_tei,
        name='org_as_tei'
    ),
    url(
        r'^institution/<int:pk>$',
        views.org_as_tei,
        name='org_as_tei'
    ),
    
    url(
        r'^work/<int:pk>$',
        views.work_as_tei,
        name='work_as_tei'
    ),
    url(
        r'^uri-to-tei',
        views.uri_to_tei,
        name='uri_to_tei'
    ),
]
