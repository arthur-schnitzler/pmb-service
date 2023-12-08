from django.views.generic.base import TemplateView
from apis_core.apis_entities.models import Person, Place, Event, Work, Institution
from apis_core.apis_metainfo.models import Uri


class HomePageView(TemplateView):

    template_name = "dumper/index.html"

    def get_context_data(self, *args, **kwargs):
        context = super(HomePageView, self).get_context_data(*args, **kwargs)
        context["person_count"] = Person.objects.all().count()
        context["place_count"] = Place.objects.all().count()
        context["event_count"] = Event.objects.all().count()
        context["work_count"] = Work.objects.all().count()
        context["institution_count"] = Institution.objects.all().count()
        context["uri_count"] = Uri.objects.all().count()
        return context
