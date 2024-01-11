from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic.base import TemplateView

from apis_core.apis_entities.models import Event, Institution, Person, Place, Work
from django.conf import settings
from apis_core.apis_metainfo.models import Uri
import requests


from .forms import form_user_login


def get_imprint_url():
    base_url = "https://imprint.acdh.oeaw.ac.at/"
    redmine_id = getattr(settings, "REDMINE_ID", "go-register-a-redmine-service-issue")
    return f"{base_url}{redmine_id}"


class AboutView(TemplateView):
    template_name = "dumper/about.html"


class ImprintView(TemplateView):
    template_name = "dumper/imprint.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        r = requests.get(get_imprint_url())

        if r.status_code == 200:
            context["imprint_body"] = f"{r.text}"
        else:
            context[
                "imprint_body"
            ] = """
            On of our services is currently not available. Please try it later or write
            an email to acdh@oeaw.ac.at; if you are service provide, make sure that you
            provided ACDH_IMPRINT_URL and REDMINE_ID
            """
        return context


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


def user_login(request):
    if request.method == "POST":
        form = form_user_login(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd["username"], password=cd["password"])
            if user and user.is_active:
                login(request, user)
                return HttpResponseRedirect(request.GET.get("next", "/"))
            return HttpResponse("user does not exist")
    else:
        form = form_user_login()
        return render(request, "dumper/user_login.html", {"form": form})


def user_logout(request):
    logout(request)
    return render(request, "dumper/user_logout.html")
