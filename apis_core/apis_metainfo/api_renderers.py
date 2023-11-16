from django.template.loader import render_to_string
from rest_framework import renderers


class TEIBaseRenderer(renderers.BaseRenderer):
    media_type = 'application/xml+tei'
    format = 'xml'

    def render(self, data, media_type=None, renderer_context=None):
        data = render_to_string("apis_metainfo/TEI_renderer.xml", {'data': data, 'renderer_context': renderer_context})

        return data

