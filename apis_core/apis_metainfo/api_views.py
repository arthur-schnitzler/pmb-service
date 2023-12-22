from rest_framework import viewsets

from .models import Collection, Source, TempEntityClass, Text, Uri
from .serializers import (
    CollectionSerializer,
    SourceSerializer,
    TempEntityClassSerializer,
    TextSerializer,
    UriSerializer,
)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


class TextViewSet(viewsets.ModelViewSet):
    queryset = Text.objects.all()
    serializer_class = TextSerializer


class SourceSerializerViewSet(viewsets.ModelViewSet):
    queryset = Source.objects.all()
    serializer_class = SourceSerializer


class UriSerializerViewSet(viewsets.ModelViewSet):
    queryset = Uri.objects.all()
    serializer_class = UriSerializer


class TempEntityClassViewSet(viewsets.ModelViewSet):
    queryset = TempEntityClass.objects.all()
    serializer_class = TempEntityClassSerializer

    def destroy(self, request, pk=None):
        pass
