from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('arche/', include('archemd.urls')),
    path('', include('dumper.urls')),
]
