from django.urls import path
from django.conf import settings

from dumper.views import HomePageView

app_name = "dumper"

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
]

if settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
