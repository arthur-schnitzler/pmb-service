from django.conf import settings
from django.urls import path

from dumper import views

app_name = "dumper"

urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("imprint/", views.ImprintView.as_view(), name="imprint"),
    path("login/", views.user_login, name="user_login"),
    path("logout/", views.user_logout, name="user_logout"),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
