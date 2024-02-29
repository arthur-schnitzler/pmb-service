from django.urls import path

from dumper import views

app_name = "dumper"

urlpatterns = [
    path("", views.HomePageView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("export/", views.ExportView.as_view(), name="export"),
    path("imprint/", views.ImprintView.as_view(), name="imprint"),
    path("login/", views.user_login, name="user_login"),
    path("logout/", views.user_logout, name="user_logout"),
]
