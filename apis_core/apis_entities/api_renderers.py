from apis_core.apis_tei.tei import TeiEntCreator
from django.conf import settings
from rest_framework import renderers

base_uri = getattr(settings, "APIS_BASE_URI", "http://apis.info")
if base_uri.endswith("/"):
    base_uri = base_uri[:-1]
lang = getattr(settings, "LANGUAGE_CODE", "de")


class EntityToTEI(renderers.BaseRenderer):
    media_type = "text/xml"
    format = "tei"

    def render(self, data, media_type=None, renderer_context=None):
        tei_doc = TeiEntCreator(data)
        return tei_doc.serialize_full_doc()
