from django.views.generic.base import TemplateView


class FooBarView(TemplateView):

    template_name = "apis_entities/htmx/test.html"

    def get_context_data(self, *args, **kwargs):
        context = super(FooBarView, self).get_context_data(*args, **kwargs)
        request = self.request
        instance_id = request.GET.get("instance_id", None)
        context["object"] = {
            "request": self.request,
            "instance_id": instance_id,
            "relation_type": request.GET.get("relation_type", None),
        }
        return context
