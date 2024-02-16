from dal import autocomplete

from .models import TempEntityClass, Collection


class CollectionAC(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = Collection.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)
        return qs


class TempEntityClassAC(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        qs = TempEntityClass.objects.all()

        if self.q:
            qs = qs.filter(name__icontains=self.q)

        return qs
